import json
import random
import sqlite3
from pathlib import Path

import torneio
from constantes import TECNICO_INICIAL
from src.systems import banco_dados as banco
from src.systems import sistema_decisao as sd


def testar_decisoes_assertivas():
    decisoes = json.loads(Path("data/decisoes.json").read_text(encoding="utf-8"))
    assert all("assertiva" in opcao for decisao in decisoes
               for opcao in decisao["opcoes"])
    assert sd.contar_acertos(decisoes, [("d01", 0, {})]) == 1
    assert sd.contar_acertos(decisoes, [("d01", 1, {})]) == 0
    assert sd.forca_efetiva(90, 2) == 100


def testar_forca_sorteada_e_bonus():
    bases = {"Time A": 60, "Time B": 50}
    rng = random.Random(10)
    forcas = torneio.simular_rodada(
        [("Time A", "Time B")], bases, "Time A", dict(TECNICO_INICIAL),
        rng=random.Random(10), acertos=0,
    )[0]
    forca_com_acerto = torneio.simular_rodada(
        [("Time A", "Time B")], bases, "Time A", dict(TECNICO_INICIAL),
        rng=random.Random(10), acertos=1,
    )[0]
    assert bases["Time A"] - 15 <= forcas[4] <= bases["Time A"] + 15
    assert forcas[5] == forca_com_acerto[5]
    assert forca_com_acerto[4] == forcas[4] + 8
    assert forca_com_acerto[6] == 1


def testar_migracao_e_persistencia():
    legado = sqlite3.connect(":memory:")
    legado.row_factory = sqlite3.Row
    legado.execute(
        "CREATE TABLE partidas (id INTEGER PRIMARY KEY, rodada INTEGER, mandante TEXT,"
        " visitante TEXT, gols_mandante INTEGER, gols_visitante INTEGER)"
    )
    legado.execute(
        "INSERT INTO partidas VALUES (?, ?, ?, ?, ?, ?)", (1, 1, "A", "B", 2, 1)
    )
    banco._migrar_partidas(legado)
    colunas = {linha["name"] for linha in legado.execute("PRAGMA table_info(partidas)")}
    assert {"forca_casa", "forca_fora", "acertos"} <= colunas
    assert legado.execute("SELECT gols_mandante FROM partidas").fetchone()[0] == 2

    conn = banco.conectar(":memory:")
    tecnico = dict(TECNICO_INICIAL)
    torneio_id = banco.novo_torneio(conn, "Teste", "Time A", tecnico)
    banco.fechar_rodada(
        conn, torneio_id, 1,
        [("Time A", "Time B", 2, 1, 75, 60, 1)], [], tecnico,
    )
    partida = banco.historico_partidas(conn, torneio_id)[0]
    assert (partida["forca_casa"], partida["forca_fora"], partida["acertos"]) == (75, 60, 1)


if __name__ == "__main__":
    testар_decisoes_assertivas = testar_decisoes_assertivas
    testар_decisoes_assertivas()
    testar_forca_sorteada_e_bonus()
    testar_migracao_e_persistencia()
    print("TESTES PASSARAM")