"""Persistência do jogo com SQLite.

Tabelas:
  torneios     -> um save/jogo por linha (time do usuário, rodada atual, medidores atuais)
  partidas     -> todas as partidas simuladas do torneio (mandante, visitante, gols)
  decisoes     -> decisões tomadas pelo usuário e os medidores resultantes
  checkpoints  -> foto dos medidores ao fim de cada rodada (permite "voltar no save")
"""
import os
import sqlite3
from datetime import datetime

import constantes

MEDIDORES = ("relacionamento", "estabilidade", "reputacao")

ESQUEMA = """
CREATE TABLE IF NOT EXISTS torneios (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nome            TEXT NOT NULL,
    time_usuario    TEXT NOT NULL,
    rodada_atual    INTEGER NOT NULL DEFAULT 1,
    status          TEXT NOT NULL DEFAULT 'em_andamento',
    relacionamento  INTEGER NOT NULL,
    estabilidade    INTEGER NOT NULL,
    reputacao       INTEGER NOT NULL,
    criado_em       TEXT NOT NULL,
    atualizado_em   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS partidas (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    torneio_id   INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
    rodada       INTEGER NOT NULL,
    mandante     TEXT NOT NULL,
    visitante    TEXT NOT NULL,
    gols_mandante  INTEGER NOT NULL,
    gols_visitante INTEGER NOT NULL,
    forca_casa     INTEGER,
    forca_fora     INTEGER,
    acertos        INTEGER
);

CREATE TABLE IF NOT EXISTS decisoes (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    torneio_id      INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
    rodada          INTEGER NOT NULL,
    decisao_id      TEXT NOT NULL,
    indice_escolha  INTEGER NOT NULL,
    relacionamento  INTEGER NOT NULL,
    estabilidade    INTEGER NOT NULL,
    reputacao       INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS checkpoints (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    torneio_id      INTEGER NOT NULL REFERENCES torneios(id) ON DELETE CASCADE,
    rodada          INTEGER NOT NULL,
    relacionamento  INTEGER NOT NULL,
    estabilidade    INTEGER NOT NULL,
    reputacao       INTEGER NOT NULL,
    criado_em       TEXT NOT NULL,
    UNIQUE (torneio_id, rodada)
);
"""


def _agora():
    return datetime.now().isoformat(timespec="seconds")


def conectar(caminho=None):
    """Abre (e cria, se preciso) o banco. Use ":memory:" nos testes."""
    caminho = caminho or constantes.CAMINHO_BANCO
    pasta = os.path.dirname(os.fspath(caminho))
    if pasta:
        os.makedirs(pasta, exist_ok=True)
    conn = sqlite3.connect(caminho)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(ESQUEMA)
    _migrar_partidas(conn)
    return conn


def _migrar_partidas(conn):
    """Adiciona os metadados de força a bancos criados por versões anteriores."""
    colunas = {linha["name"] for linha in conn.execute("PRAGMA table_info(partidas)")}
    for nome in ("forca_casa", "forca_fora", "acertos"):
        if nome not in colunas:
            conn.execute(f"ALTER TABLE partidas ADD COLUMN {nome} INTEGER")


# ---------- torneio / save ----------

def novo_torneio(conn, nome, time_usuario, tecnico):
    """Cria um torneio novo e já grava o checkpoint da rodada 1."""
    with conn:
        cur = conn.execute(
            "INSERT INTO torneios (nome, time_usuario, relacionamento, estabilidade,"
            " reputacao, criado_em, atualizado_em) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (nome, time_usuario, tecnico["relacionamento"], tecnico["estabilidade"],
             tecnico["reputacao"], _agora(), _agora()),
        )
        torneio_id = cur.lastrowid
        _gravar_checkpoint(conn, torneio_id, 1, tecnico)
    return torneio_id


def listar_torneios(conn):
    return conn.execute(
        "SELECT id, nome, time_usuario, rodada_atual, status, atualizado_em"
        " FROM torneios ORDER BY atualizado_em DESC, id DESC"
    ).fetchall()


def carregar_torneio(conn, torneio_id):
    """Retorna (torneio, tecnico) para retomar o jogo de onde parou."""
    t = conn.execute("SELECT * FROM torneios WHERE id = ?", (torneio_id,)).fetchone()
    if t is None:
        return None, None
    tecnico = {m: t[m] for m in MEDIDORES}
    return dict(t), tecnico


def excluir_torneio(conn, torneio_id):
    with conn:
        conn.execute("DELETE FROM torneios WHERE id = ?", (torneio_id,))


# ---------- registro durante o jogo ----------

def registrar_partida(conn, torneio_id, rodada, mandante, visitante, gols_m, gols_v,
                      forca_casa=None, forca_fora=None, acertos=None):
    with conn:
        conn.execute(
            "INSERT INTO partidas (torneio_id, rodada, mandante, visitante,"
            " gols_mandante, gols_visitante, forca_casa, forca_fora, acertos)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (torneio_id, rodada, mandante, visitante, gols_m, gols_v,
             forca_casa, forca_fora, acertos),
        )


def registrar_decisao(conn, torneio_id, rodada, decisao_id, indice_escolha, tecnico):
    """Chame depois de aplicar_efeito(), passando o técnico já atualizado."""
    with conn:
        conn.execute(
            "INSERT INTO decisoes (torneio_id, rodada, decisao_id, indice_escolha,"
            " relacionamento, estabilidade, reputacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (torneio_id, rodada, decisao_id, indice_escolha,
             tecnico["relacionamento"], tecnico["estabilidade"], tecnico["reputacao"]),
        )


def _gravar_checkpoint(conn, torneio_id, rodada, tecnico):
    conn.execute(
        "INSERT OR REPLACE INTO checkpoints (torneio_id, rodada, relacionamento,"
        " estabilidade, reputacao, criado_em) VALUES (?, ?, ?, ?, ?, ?)",
        (torneio_id, rodada, tecnico["relacionamento"], tecnico["estabilidade"],
         tecnico["reputacao"], _agora()),
    )


def salvar_progresso(conn, torneio_id, proxima_rodada, tecnico, finalizado=False):
    """Atualiza o torneio e cria o checkpoint da próxima rodada."""
    with conn:
        conn.execute(
            "UPDATE torneios SET rodada_atual = ?, status = ?, relacionamento = ?,"
            " estabilidade = ?, reputacao = ?, atualizado_em = ? WHERE id = ?",
            (proxima_rodada, "finalizado" if finalizado else "em_andamento",
             tecnico["relacionamento"], tecnico["estabilidade"], tecnico["reputacao"],
             _agora(), torneio_id),
        )
        _gravar_checkpoint(conn, torneio_id, proxima_rodada, tecnico)


def fechar_rodada(conn, torneio_id, rodada, partidas, decisoes_tomadas, tecnico,
                  finalizado=False):
    """Grava uma rodada inteira em UMA transação (ou grava tudo, ou nada).

    partidas:         lista de (mandante, visitante, gols_mandante, gols_visitante)
    decisoes_tomadas: lista de (decisao_id, indice_escolha, medidores_depois_da_escolha)
    tecnico:          medidores ao fim da rodada
    Depois de gravar, o torneio avança para rodada + 1 e ganha um checkpoint.
    """
    with conn:
        for partida in partidas:
            mandante, visitante, gols_m, gols_v = partida[:4]
            forca_casa, forca_fora, acertos = (*partida[4:7], None, None, None)[:3]
            conn.execute(
                "INSERT INTO partidas (torneio_id, rodada, mandante, visitante,"
                " gols_mandante, gols_visitante, forca_casa, forca_fora, acertos)"
                " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (torneio_id, rodada, mandante, visitante, gols_m, gols_v,
                 forca_casa, forca_fora, acertos),
            )
        for decisao_id, indice, medidores in decisoes_tomadas:
            conn.execute(
                "INSERT INTO decisoes (torneio_id, rodada, decisao_id, indice_escolha,"
                " relacionamento, estabilidade, reputacao) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (torneio_id, rodada, decisao_id, indice, medidores["relacionamento"],
                 medidores["estabilidade"], medidores["reputacao"]),
            )
        conn.execute(
            "UPDATE torneios SET rodada_atual = ?, status = ?, relacionamento = ?,"
            " estabilidade = ?, reputacao = ?, atualizado_em = ? WHERE id = ?",
            (rodada + 1, "finalizado" if finalizado else "em_andamento",
             tecnico["relacionamento"], tecnico["estabilidade"], tecnico["reputacao"],
             _agora(), torneio_id),
        )
        _gravar_checkpoint(conn, torneio_id, rodada + 1, tecnico)


# ---------- voltar no save ----------

def listar_checkpoints(conn, torneio_id):
    return conn.execute(
        "SELECT rodada, relacionamento, estabilidade, reputacao, criado_em"
        " FROM checkpoints WHERE torneio_id = ? ORDER BY rodada",
        (torneio_id,),
    ).fetchall()


def voltar_checkpoint(conn, torneio_id, rodada):
    """Volta o torneio ao início da `rodada`: apaga partidas, decisões e
    checkpoints posteriores e restaura os medidores. Retorna o técnico."""
    cp = conn.execute(
        "SELECT * FROM checkpoints WHERE torneio_id = ? AND rodada = ?",
        (torneio_id, rodada),
    ).fetchone()
    if cp is None:
        return None
    tecnico = {m: cp[m] for m in MEDIDORES}
    with conn:
        conn.execute("DELETE FROM partidas WHERE torneio_id = ? AND rodada >= ?",
                     (torneio_id, rodada))
        conn.execute("DELETE FROM decisoes WHERE torneio_id = ? AND rodada >= ?",
                     (torneio_id, rodada))
        conn.execute("DELETE FROM checkpoints WHERE torneio_id = ? AND rodada > ?",
                     (torneio_id, rodada))
        conn.execute(
            "UPDATE torneios SET rodada_atual = ?, status = 'em_andamento',"
            " relacionamento = ?, estabilidade = ?, reputacao = ?, atualizado_em = ?"
            " WHERE id = ?",
            (rodada, tecnico["relacionamento"], tecnico["estabilidade"],
             tecnico["reputacao"], _agora(), torneio_id),
        )
    return tecnico


# ---------- histórico e consultas ----------

def historico_partidas(conn, torneio_id):
    return conn.execute(
        "SELECT rodada, mandante, visitante, gols_mandante, gols_visitante,"
        " forca_casa, forca_fora, acertos"
        " FROM partidas WHERE torneio_id = ? ORDER BY rodada, id",
        (torneio_id,),
    ).fetchall()


def historico_decisoes(conn, torneio_id):
    return conn.execute(
        "SELECT rodada, decisao_id, indice_escolha, relacionamento, estabilidade,"
        " reputacao FROM decisoes WHERE torneio_id = ? ORDER BY rodada, id",
        (torneio_id,),
    ).fetchall()


def classificacao(conn, torneio_id):
    """Tabela do campeonato calculada direto das partidas (3 pts vitória, 1 empate)."""
    return conn.execute(
        """
        WITH jogos AS (
            SELECT mandante AS time, gols_mandante AS gp, gols_visitante AS gc
              FROM partidas WHERE torneio_id = :t
            UNION ALL
            SELECT visitante, gols_visitante, gols_mandante
              FROM partidas WHERE torneio_id = :t
        )
        SELECT time,
               COUNT(*)                                          AS jogos,
               SUM(gp > gc)                                      AS vitorias,
               SUM(gp = gc)                                      AS empates,
               SUM(gp < gc)                                      AS derrotas,
               SUM(gp)                                           AS gols_pro,
               SUM(gc)                                           AS gols_contra,
               SUM(CASE WHEN gp > gc THEN 3 WHEN gp = gc THEN 1 ELSE 0 END) AS pontos
          FROM jogos
         GROUP BY time
         ORDER BY pontos DESC, (SUM(gp) - SUM(gc)) DESC, SUM(gp) DESC, time
        """,
        {"t": torneio_id},
    ).fetchall()


def decisoes_com_medidor_abaixo(conn, torneio_id, medidor, limite):
    """Exemplo do professor: decisões em que um medidor ficou abaixo de `limite`."""
    if medidor not in MEDIDORES:  # evita injeção, já que o nome da coluna é interpolado
        raise ValueError(f"medidor inválido: {medidor}")
    return conn.execute(
        f"SELECT rodada, decisao_id, {medidor} FROM decisoes"
        f" WHERE torneio_id = ? AND {medidor} < ? ORDER BY rodada",
        (torneio_id, limite),
    ).fetchall()
