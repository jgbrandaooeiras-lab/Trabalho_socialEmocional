import random
from constantes import FORCA_MIN, FORCA_MAX
# Dados dos times do campeonato.
# - nome:   aparece nas telas, na classificação e no banco de dados
# - escudo: arquivo dentro de escudos.png/ (sem_fundo/ = gerado pelo remover_fundo.py)
# - forca:  usada na simulação das partidas (quanto maior, mais chances de vencer)
#
# ATENÇÃO: a ordem desta lista define o calendário do torneio. Evite reordenar
# ou remover times depois que já existirem saves.
TIMES = [
    {"nome": "Atlético-MG",  "escudo": "sem_fundo/AtleticoMineiro.png", "forca": 75},
    {"nome": "Athletico-PR", "escudo": "sem_fundo/AtleticoParanaense.png", "forca": 70},
    {"nome": "Bahia",        "escudo": "sem_fundo/Bahia.png", "forca": 68},
    {"nome": "Coritiba",     "escudo": "sem_fundo/Coritiba.png", "forca": 60},
    {"nome": "Flamengo",     "escudo": "sem_fundo/flamengo.png", "forca": 82},
    {"nome": "Grêmio",       "escudo": "sem_fundo/Gremio.png", "forca": 72},
    {"nome": "Palmeiras",    "escudo": "sem_fundo/Palmeiras.png", "forca": 80},
    {"nome": "São Paulo",    "escudo": "sem_fundo/SaoPaulo.png", "forca": 71},
    {"nome": "Vasco",        "escudo": "sem_fundo/vasco.png", "forca": 65},
    {"nome": "Corinthians",  "escudo": "sem_fundo/corinthians.png", "forca": 74},
    # Com 10 times (número par) ninguém folga: são 9 rodadas e o usuário joga todas.
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


def sortear_forca_perto_base(forca_base, variacao=15, rng=random):
    """Sorteia uma força dentro da variação permitida em torno da força base."""
    minimo = max(FORCA_MIN, forca_base - variacao)
    maximo = min(FORCA_MAX, forca_base + variacao)
    return rng.randint(minimo, maximo)


def sortear_forcas_da_rodada(variacao=15, rng=random, forcas_base=None):
    """Sorteia a força de cada time para uma rodada, preservando sua força base."""
    bases = forcas_base or {t["nome"]: t["forca"] for t in TIMES}
    return {nome: sortear_forca_perto_base(base, variacao, rng)
            for nome, base in bases.items()}
