"""Lógica do campeonato: calendário, simulação das partidas e efeito do técnico."""
import math
import random


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


def simular_rodada(jogos, forcas, time_usuario, tecnico, rng=random):
    """Simula todos os jogos da rodada. O time do usuário recebe o bônus do técnico.

    Retorna lista de (mandante, visitante, gols_mandante, gols_visitante).
    """
    bonus = bonus_tecnico(tecnico)
    resultados = []
    for mandante, visitante in jogos:
        forca_m, forca_v = forcas[mandante], forcas[visitante]
        if mandante == time_usuario:
            forca_m += bonus
        if visitante == time_usuario:
            forca_v += bonus
        gols_m, gols_v = simular_partida(forca_m, forca_v, rng)
        resultados.append((mandante, visitante, gols_m, gols_v))
    return resultados
