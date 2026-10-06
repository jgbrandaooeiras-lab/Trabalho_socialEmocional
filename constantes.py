from pathlib import Path

# Caminhos (sempre relativos à pasta do projeto, não à pasta onde o comando é executado)
RAIZ = Path(__file__).resolve().parent
CAMINHO_DECISOES = RAIZ / "data" / "decisoes.json"
CAMINHO_BANCO = RAIZ / "data" / "jogo.db"
PASTA_ESCUDOS = RAIZ / "assets" / "escudos"

# Janela
LARGURA = 1280
ALTURA = 740
TITULO = "Simulador de Técnico de Futebol"
FPS = 30

# Medidores do técnico no início de um torneio novo
TECNICO_INICIAL = {"relacionamento": 50, "estabilidade": 50, "reputacao": 50}

# Cores
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
FUNDO = (18, 32, 24)
CINZA = (170, 170, 170)
CINZA_ESCURO = (70, 70, 70)
VERDE = (60, 180, 90)
VERDE_ESCURO = (30, 130, 70)
AMARELO = (230, 190, 60)
VERMELHO = (210, 70, 70)
AZUL = (40, 90, 160)
AZUL_CLARO = (70, 130, 210)
DESTAQUE = (45, 75, 55)

FORCA_MIN = 0
FORCA_MAX = 100
BONUS_POR_ACERTO = 8
CHANCE_EMPATE = 0.15
