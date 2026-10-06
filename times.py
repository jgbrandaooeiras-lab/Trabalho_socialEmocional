import random
from constantes import FORCA_MIN, FORCA_MAX
# Dados dos times do campeonato.
# - nome:   aparece nas telas, na classificação e no banco de dados
# - escudo: arquivo dentro de assets/escudos/
# - forca:  usada na simulação das partidas (quanto maior, mais chances de vencer)
#
# ATENÇÃO: a ordem desta lista define o calendário do torneio. Evite reordenar
# ou remover times depois que já existirem saves.
TIMES = [
    {"nome": "Atlético-MG",  "escudo": "AtleticoMineiro.png",    "forca": 75},
    {"nome": "Athletico-PR", "escudo": "AtleticoParanaense.png", "forca": 70},
    {"nome": "Bahia",        "escudo": "Bahia.png",              "forca": 68},
    {"nome": "Coritiba",     "escudo": "Coritiba.png",           "forca": 60},
    {"nome": "Flamengo",     "escudo": "flamengo.png",           "forca": 82},
    {"nome": "Grêmio",       "escudo": "Gremio.png",             "forca": 72},
    {"nome": "Palmeiras",    "escudo": "Palmeiras.jpg",          "forca": 80},
    {"nome": "São Paulo",    "escudo": "SaoPaulo.png",           "forca": 71},
    {"nome": "Vasco",        "escudo": "Vasco.png",              "forca": 65}
    # 9º time: adicione aqui (e o escudo em assets/escudos/). Com 9 times o torneio
    # passa a ter 9 rodadas e cada time joga 8 partidas (uma rodada de folga cada).
]


def nomes_dos_times():
    return [t["nome"] for t in TIMES]


def forcas_dos_times():
    return {t["nome"]: t["forca"] for t in TIMES}


def buscar_time(nome):
    return next((t for t in TIMES if t["nome"] == nome), None)


def sortear_forca():
    """Força aleatória de 0 a 100 para um time em uma partida."""
    return random.randint(FORCA_MIN, FORCA_MAX)

def sortear_forcas_da_rodada():
    """Sorteia a força dos 9 times de uma vez: {'Flamengo': 57, ...}"""
    return {t["nome"]: sortear_forca() for t in TIMES}