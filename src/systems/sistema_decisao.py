import json

import constantes

MEDIDORES = ("relacionamento", "estabilidade", "reputacao")


def carregar_decisoes(caminho=None):
    caminho = caminho or constantes.CAMINHO_DECISOES
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)


def buscar_decisao(decisoes, numero_partida):
    """Primeira decisão da partida (ou None)."""
    for decisao in decisoes:
        if decisao["id_partida"] == numero_partida:
            return decisao
    return None


def buscar_decisoes(decisoes, numero_partida):
    """Todas as decisões da partida, na ordem do JSON (uma partida pode ter mais de uma)."""
    return [d for d in decisoes if d["id_partida"] == numero_partida]


def limitar(valor, minimo=0, maximo=100):
    return max(minimo, min(maximo, valor))


def aplicar_efeito(tecnico, decisao, indice_escolha):
    efeitos = decisao["opcoes"][indice_escolha]["efeitos"]
    for medidor in MEDIDORES:
        tecnico[medidor] = limitar(tecnico[medidor] + efeitos[medidor])
