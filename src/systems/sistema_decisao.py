import json
import random
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

def sortear_forca_perto_base(forca_base, variacao=15):
    """Sorteia uma força próxima da base, com variação de até ±variacao."""
    minimo = max(constantes.FORCA_MIN, forca_base - variacao)
    maximo = min(constantes.FORCA_MAX, forca_base + variacao)
    return random.randint(minimo, maximo)


BONUS_POR_ACERTO = 8   # ajuste no teste de jogo

def forca_efetiva(forca_sorteada, acertos):
    return min(constantes.FORCA_MAX, forca_sorteada + acertos * constantes.BONUS_POR_ACERTO)


def contar_acertos(decisoes, decisoes_tomadas):
    """Conta escolhas marcadas como assertivas no arquivo de decisões."""
    por_id = {decisao["id"]: decisao for decisao in decisoes}
    acertos = 0
    for decisao_id, indice_escolha, *_ in decisoes_tomadas:
        decisao = por_id.get(decisao_id)
        if decisao and decisao["opcoes"][indice_escolha].get("assertiva", False):
            acertos += 1
    return acertos
