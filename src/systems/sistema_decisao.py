import json

MEDIDORES = ("relacionamento", "estabilidade", "reputacao")

def carregar_decisoes(caminho="data/decisoes.json"):
    with open(caminho, encoding="utf-8") as arquivo:
        return json.load(arquivo)

def buscar_decisao(decisoes, numero_partida):
    for decisao in decisoes:
        if decisao["id_partida"] == numero_partida:
            return decisao
    return None

def limitar(valor, minimo=0, maximo=100):
    return max(minimo, min(maximo, valor))

def aplicar_efeito(tecnico, decisao, indice_escolha):
    efeitos = decisao["opcoes"][indice_escolha]["efeitos"]
    for medidor in MEDIDORES:
        tecnico[medidor] = limitar(tecnico[medidor] + efeitos[medidor])