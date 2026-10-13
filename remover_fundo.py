"""Gera versões sem fundo (PNG transparente) dos escudos e do repórter.

Uso: python remover_fundo.py

Como funciona: a cor de fundo é a cor mais comum na borda da imagem. A partir da
borda, "pinta" de transparente todos os pixels parecidos com ela que estão ligados
à borda (como o balde de tinta do Paint). O que fica dentro do desenho, mesmo que
tenha a mesma cor (ex.: o branco dentro de um escudo), é preservado.

Ajustes por imagem (veja ESCUDOS e PERSONAGENS):
- tolerancia: quanto a cor pode variar e ainda contar como fundo
- fundo:      cor do fundo, quando a cor mais comum da borda não é o fundo
- areas:      retângulos (em frações do desenho já recortado: x0, y0, x1, y1) onde TODA cor
              parecida com o fundo é apagada, mesmo sem encostar na borda
- manter_cercado_de_preto: nas áreas, preserva as manchas de cor de fundo totalmente
              cercadas de preto (ex.: as bolinhas brancas do anel do Corinthians)
- contorno:   devolve as faixas apagadas com até 2x esse número de pixels de
              largura; preserva contornos escuros internos que tocam um fundo escuro

Os originais não são alterados; os resultados vão para escudos.png/sem_fundo/ e
imagens/sem_fundo/.
"""
from collections import Counter, deque
from pathlib import Path

from PIL import Image

RAIZ = Path(__file__).resolve().parent
LADO_MAXIMO = 512  # o jogo nunca mostra maior que isso

ESCUDOS = {
    "AtleticoMineiro.png": {"tolerancia": 60},
    "AtleticoParanaense.png": {"tolerancia": 60, "areas": [(0, 0, 0.45, 0.36)]},  # branco das letras CAP
    "Bahia.png": {"tolerancia": 60},
    "Coritiba.png": {"tolerancia": 60},
    "Gremio.png": {"tolerancia": 60},
    "Palmeiras.jpg": {"tolerancia": 45},
    "SaoPaulo.png": {"tolerancia": 60, "fundo": (255, 255, 255)},
    "corinthians.png": {"tolerancia": 60,
                        "areas": [(0.04, 0.07, 0.29, 0.30), (0.71, 0.07, 0.96, 0.30),  # branco dos remos
                                  # âncora, cruzamento dos remos e braços laterais da âncora
                                  (0, 0.70, 1, 1), (0, 0.55, 0.12, 0.70), (0.88, 0.55, 1, 0.70)],
                        "manter_cercado_de_preto": True},
    "flamengo.png": {"tolerancia": 60},
    "vasco.jfif": {"tolerancia": 40},
}
PERSONAGENS = {"vorcaro.jfif": {"tolerancia": 10, "contorno": 6}}


def parecido(a, b, tolerancia):
    return max(abs(a[0] - b[0]), abs(a[1] - b[1]), abs(a[2] - b[2])) <= tolerancia


def _filtro(mascara, w, h, raio, func):
    """Mínimo (erosão) ou máximo (dilatação) num quadrado de lado 2*raio+1."""
    linhas = [[func(mascara[y][max(0, x - raio):x + raio + 1]) for x in range(w)] for y in range(h)]
    return [[func(linhas[yy][x] for yy in range(max(0, y - raio), min(h, y + raio + 1)))
             for x in range(w)] for y in range(h)]


def _manchas(px, w, h, pixels):
    """Separa os pixels em manchas conectadas (vizinhos de cima/baixo/lados)."""
    restantes, manchas = set(pixels), []
    while restantes:
        fila = deque([restantes.pop()])
        mancha = set(fila)
        while fila:
            x, y = fila.popleft()
            for viz in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if viz in restantes:
                    restantes.discard(viz)
                    mancha.add(viz)
                    fila.append(viz)
        manchas.append(mancha)
    return manchas


def _cercada_de_preto(mancha, px, w, h, apagar):
    for x, y in mancha:
        for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if (vx, vy) in mancha:
                continue
            if not (0 <= vx < w and 0 <= vy < h) or apagar[vy][vx] or max(px[vx, vy][:3]) > 90:
                return False
    return True


def remover_fundo(origem, destino, tolerancia, fundo=None, areas=(), contorno=0,
                  manter_cercado_de_preto=False):
    img = Image.open(origem).convert("RGBA")
    if max(img.size) > LADO_MAXIMO:
        img.thumbnail((LADO_MAXIMO, LADO_MAXIMO), Image.LANCZOS)
    w, h = img.size
    px = img.load()

    borda = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    fundo = fundo or Counter(px[p][:3] for p in borda).most_common(1)[0][0]

    # 1) balde de tinta a partir da borda
    apagar = [[False] * w for _ in range(h)]
    fila = deque(p for p in borda if parecido(px[p], fundo, tolerancia))
    for x, y in fila:
        apagar[y][x] = True
    while fila:
        x, y = fila.popleft()
        for vx, vy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= vx < w and 0 <= vy < h and not apagar[vy][vx] and parecido(px[vx, vy], fundo, tolerancia):
                apagar[vy][vx] = True
                fila.append((vx, vy))

    # 2) faixas finas voltam a ser desenho (contornos internos)
    if contorno:
        apagar = _filtro(_filtro(apagar, w, h, contorno, min), w, h, contorno, max)

    # 3) áreas onde toda cor de fundo sai, mesmo presa dentro do desenho
    #    (frações medidas no desenho recortado, igual ao PNG gerado)
    xs = [x for y in range(h) for x in range(w) if not apagar[y][x]]
    ys = [y for y in range(h) if not all(apagar[y])]
    bx, by, bw, bh = min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1
    nas_areas = {(x, y) for fx0, fy0, fx1, fy1 in areas
                 for y in range(by + int(fy0 * bh), by + int(fy1 * bh))
                 for x in range(bx + int(fx0 * bw), bx + int(fx1 * bw))
                 if not apagar[y][x] and parecido(px[x, y], fundo, tolerancia)}
    if manter_cercado_de_preto and nas_areas:
        # avalia a mancha inteira (mesmo a parte fora da área) para não cortar bolinhas ao meio
        cor_fundo = {(x, y) for y in range(h) for x in range(w)
                     if not apagar[y][x] and parecido(px[x, y], fundo, tolerancia)}
        nas_areas = {p for mancha in _manchas(px, w, h, cor_fundo) if mancha & nas_areas
                     and not _cercada_de_preto(mancha, px, w, h, apagar) for p in mancha}
    for x, y in nas_areas:
        apagar[y][x] = True

    for y in range(h):
        for x in range(w):
            if apagar[y][x]:
                px[x, y] = (0, 0, 0, 0)

    img = img.crop(img.getbbox())  # tira a sobra transparente em volta
    destino.parent.mkdir(parents=True, exist_ok=True)
    img.save(destino)
    print(f"{origem.name:28} fundo {fundo} -> {destino.relative_to(RAIZ)}")


if __name__ == "__main__":
    for nome, ajustes in ESCUDOS.items():
        remover_fundo(RAIZ / "escudos.png" / nome,
                      RAIZ / "escudos.png" / "sem_fundo" / f"{Path(nome).stem}.png", **ajustes)
    for nome, ajustes in PERSONAGENS.items():
        remover_fundo(RAIZ / "imagens" / nome,
                      RAIZ / "imagens" / "sem_fundo" / f"{Path(nome).stem}.png", **ajustes)
