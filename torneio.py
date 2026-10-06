"""Lógica do campeonato: calendário, simulação das partidas e efeito do técnico."""
import math
import random

import constantes
from times import sortear_forcas_da_rodada
from src.systems import sistema_decisao as sd


def gerar_calendario(nomes):
    """Todos contra todos em turno único (método do círculo).

    Retorna uma lista de rodadas; cada rodada é uma lista de (mandante, visitante).
    Com número ímpar de times, um time folga em cada rodada.
    """
    times = list(nomes)
    if len(times) % 2:
        times.append(None)  # None = folga
    n = len(times)
    rodadas = []
    for r in range(n - 1):
        jogos = []
        for i in range(n // 2):
            a, b = times[i], times[n - 1 - i]
            if a is None or b is None:
                continue
            if i == 0 and r % 2 == 1:  # alterna o mando do primeiro confronto
                a, b = b, a
            jogos.append((a, b))
        rodadas.append(jogos)
        times.insert(1, times.pop())  # gira todos, menos o primeiro
    return rodadas


def _poisson(media, rng):
    limite = math.exp(-media)
    gols, p = 0, rng.random()
    while p > limite:
        gols += 1
        p *= rng.random()
    return gols


def simular_partida(forca_a, forca_b, rng=random):
    """Sorteia o placar. Time mais forte tende a fazer mais gols."""
    dif = (forca_a - forca_b) / 100
    gols_a = _poisson(max(0.2, 1.3 + dif * 2), rng)
    gols_b = _poisson(max(0.2, 1.3 - dif * 2), rng)
    return gols_a, gols_b


def bonus_tecnico(tecnico):
    """Bônus (ou penalidade) na força do time do usuário, vindo dos medidores.

    Média dos medidores = 50 -> 0. Média 100 -> +15. Média 0 -> -15.
    """
    media = sum(tecnico.values()) / len(tecnico)
    return (media - 50) * 0.3


def jogo_do_usuario(jogos, time_usuario):
    """Retorna (mandante, visitante) do time do usuário na rodada, ou None se folgar."""
    for jogo in jogos:
        if time_usuario in jogo:
            return jogo
    return None


def numero_do_jogo_do_usuario(calendario, rodada, time_usuario):
    """Qual partida do usuário é essa (1ª, 2ª...)? None se ele folga na rodada.

    É esse número que casa com o campo id_partida do decisoes.json.
    """
    if jogo_do_usuario(calendario[rodada - 1], time_usuario) is None:
        return None
    return sum(1 for jogos in calendario[:rodada] if jogo_do_usuario(jogos, time_usuario))


def simular_rodada(jogos, forcas, time_usuario, tecnico, rng=random, acertos=0):
    """Simula os jogos com força sorteada; decisões assertivas favorecem o usuário.

    Retorna (mandante, visitante, gols_mandante, gols_visitante, forca_casa,
    forca_fora, acertos) para cada partida.
    """
    forcas_sorteadas = sortear_forcas_da_rodada(rng=rng, forcas_base=forcas)
    bonus = bonus_tecnico(tecnico)
    resultados = []
    for mandante, visitante in jogos:
        forca_m, forca_v = forcas_sorteadas[mandante], forcas_sorteadas[visitante]
        acertos_partida = 0
        if mandante == time_usuario:
            forca_m = max(constantes.FORCA_MIN, min(
                constantes.FORCA_MAX, sd.forca_efetiva(forca_m, acertos) + bonus))
            acertos_partida = acertos
        if visitante == time_usuario:
            forca_v = max(constantes.FORCA_MIN, min(
                constantes.FORCA_MAX, sd.forca_efetiva(forca_v, acertos) + bonus))
            acertos_partida = acertos
        gols_m, gols_v = simular_partida(forca_m, forca_v, rng)
        resultados.append((mandante, visitante, gols_m, gols_v, forca_m, forca_v,
                           acertos_partida))
    return resultados
