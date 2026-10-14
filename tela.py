import sys

import pygame

import constantes
import torneio
from times import TIMES, forcas_dos_times, nomes_dos_times
from src.systems import sistema_decisao as sd

LARGURA, ALTURA = constantes.LARGURA, constantes.ALTURA
PASTA_IMAGENS = constantes.RAIZ / "imagens"
PASTA_ESCUDOS = constantes.RAIZ / "escudos.png"

FUNDOS = {"campo": "CAMPO.png", "vestiario": "vestiário.jpeg", "coletiva": "coletiva.jfif"}
NOMES_CENARIO = {"campo": "CAMPO", "vestiario": "VESTIÁRIO", "coletiva": "COLETIVA"}
ROTULOS = {"relacionamento": "RELACIONAMENTO", "estabilidade": "ESTABILIDADE",
           "reputacao": "REPUTAÇÃO"}

COR_CAIXA = (24, 28, 48)
COR_BORDA = (245, 245, 235)
COR_SOMBRA = (6, 8, 16)
COR_HOVER = (52, 92, 160)
COR_DESTAQUE = (250, 210, 70)
COR_VAZIO = (60, 64, 80)
COR_LINHA_USUARIO = (40, 80, 60)


# ---------------------------------------------------------------- utilidades de desenho
def carregar_imagem(nome_arquivo, pasta=PASTA_IMAGENS):
    try:
        return pygame.image.load(str(pasta / nome_arquivo)).convert_alpha()
    except (pygame.error, FileNotFoundError):
        return None


def cobrir_tela(img, suave):
    """Escala a imagem para cobrir a tela inteira, cortando o excesso no centro."""
    escala = max(LARGURA / img.get_width(), ALTURA / img.get_height())
    tamanho = (int(img.get_width() * escala) + 1, int(img.get_height() * escala) + 1)
    img = pygame.transform.smoothscale(img, tamanho) if suave else pygame.transform.scale(img, tamanho)
    corte = pygame.Rect(0, 0, LARGURA, ALTURA)
    corte.center = img.get_rect().center
    return img.subsurface(corte).copy()


def caber(img, lado):
    escala = lado / max(img.get_width(), img.get_height())
    return pygame.transform.smoothscale(
        img, (max(1, int(img.get_width() * escala)), max(1, int(img.get_height() * escala))))


def clarear(cor, q=30):
    return tuple(min(255, c + q) for c in cor)


def _forma_pixel(tela, r, cor, p):
    pygame.draw.rect(tela, cor, (r.x + p, r.y, r.w - 2 * p, r.h))
    pygame.draw.rect(tela, cor, (r.x, r.y + p, r.w, r.h - 2 * p))


def caixa_pixel(tela, rect, fundo=COR_CAIXA, borda=COR_BORDA, p=4, sombra=True):
    """Bloco quadrado com cantos 'serrilhados' no estilo pixel art."""
    r = pygame.Rect(rect)
    if sombra:
        _forma_pixel(tela, r.move(p + 2, p + 2), COR_SOMBRA, p)
    _forma_pixel(tela, r, borda, p)
    interno = r.inflate(-2 * p, -2 * p)
    _forma_pixel(tela, interno, fundo, p)
    pygame.draw.rect(tela, clarear(fundo), (interno.x + p, interno.y, interno.w - 2 * p, p))
    pygame.draw.rect(tela, clarear(fundo, -12) if min(fundo) >= 12 else fundo,
                     (interno.x + p, interno.bottom - p, interno.w - 2 * p, p))


def texto(tela, s, fonte, cor, pos, ancora="topleft", sombra=True):
    img = fonte.render(s, True, cor)
    r = img.get_rect(**{ancora: pos})
    if sombra:
        tela.blit(fonte.render(s, True, COR_SOMBRA), r.move(2, 2))
    tela.blit(img, r)
    return r


def quebrar(s, fonte, largura):
    linhas, atual = [], ""
    for palavra in s.split():
        teste = f"{atual} {palavra}".strip()
        if fonte.size(teste)[0] <= largura:
            atual = teste
        else:
            if atual:
                linhas.append(atual)
            atual = palavra
    if atual:
        linhas.append(atual)
    return linhas


class Botao:
    def __init__(self, rect, rotulo, acao, fonte, letra=None, imagem=None, legenda=None,
                 fonte_legenda=None, cor=COR_CAIXA):
        self.rect = pygame.Rect(rect)
        self.rotulo = rotulo
        self.acao = acao
        self.fonte = fonte
        self.letra = letra
        self.imagem = imagem
        self.legenda = legenda
        self.fonte_legenda = fonte_legenda or fonte
        self.cor = cor

    def foi_clicado(self, evento):
        return (evento.type == pygame.MOUSEBUTTONDOWN and evento.button == 1
                and self.rect.collidepoint(evento.pos))

    def desenhar(self, tela, mouse):
        hover = self.rect.collidepoint(mouse)
        r = self.rect.move(0, -3) if hover else self.rect
        caixa_pixel(tela, r, COR_HOVER if hover else self.cor, COR_DESTAQUE if hover else COR_BORDA)

        if self.imagem:
            img_r = self.imagem.get_rect(midtop=(r.centerx, r.y + 18))
            tela.blit(self.imagem, img_r)
            y = texto(tela, self.rotulo, self.fonte, COR_BORDA, (r.centerx, img_r.bottom + 10), "midtop").bottom
            if self.legenda:
                texto(tela, self.legenda, self.fonte_legenda, COR_DESTAQUE, (r.centerx, y + 4), "midtop")
            return

        x0 = r.x + 20
        if self.letra:
            tag = pygame.Rect(r.x + 14, r.centery - 20, 40, 40)
            caixa_pixel(tela, tag, COR_DESTAQUE, COR_BORDA, p=3, sombra=False)
            texto(tela, self.letra, self.fonte, COR_CAIXA, tag.center, "center", sombra=False)
            x0 = tag.right + 16
        linhas = quebrar(self.rotulo, self.fonte, r.right - 20 - x0)
        lh = self.fonte.get_linesize()
        y = r.centery - len(linhas) * lh // 2
        for linha in linhas:
            if self.letra:
                texto(tela, linha, self.fonte, COR_BORDA, (x0, y))
            else:
                texto(tela, linha, self.fonte, COR_BORDA, (r.centerx, y), "midtop")
            y += lh


# ---------------------------------------------------------------- jogo
class Game:
    """Máquina de estados: menu -> escolher_time -> etapas da rodada -> ... -> fim.

    Cada rodada é uma lista de etapas (anuncio, coletiva, decisao, resultado, tabela)
    definida pelo campo "fluxo" da decisão no decisoes.json. A tela de configurações
    (ESC ou botão CONFIG) abre por cima de qualquer estado.
    """

    def __init__(self):
        pygame.init()
        # SCALED: em tela cheia a imagem é ampliada mantendo a proporção (e o mouse continua certo)
        self.tela = pygame.display.set_mode((LARGURA, ALTURA), pygame.SCALED)
        pygame.display.set_caption(constantes.TITULO)
        self.clock = pygame.time.Clock()
        self.esta_rodando = True

        fonte = "consolas,couriernew,monospace"
        self.fonte_titulo = pygame.font.SysFont(fonte, 56, bold=True)
        self.fonte_h2 = pygame.font.SysFont(fonte, 32, bold=True)
        self.fonte = pygame.font.SysFont(fonte, 22, bold=True)
        self.fonte_pequena = pygame.font.SysFont(fonte, 17, bold=True)
        self.fonte_placar = pygame.font.SysFont(fonte, 72, bold=True)

        self.carregar_assets()
        self.iniciar_musica()
        self.decisoes = sd.carregar_decisoes()
        self.calendario = torneio.gerar_calendario(nomes_dos_times())
        self.forcas = forcas_dos_times()

        self.botoes = []
        self.config_aberta = False
        self.botoes_config = []
        self.ir_para("menu")

    def carregar_assets(self):
        self.fundos = {}
        for cenario, arquivo in FUNDOS.items():
            img = carregar_imagem(arquivo)
            if img is None:
                img = pygame.Surface((LARGURA, ALTURA))
                img.fill(constantes.FUNDO)
            self.fundos[cenario] = cobrir_tela(img, suave=cenario != "campo")

        self.escurecer = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.escurecer.fill((0, 0, 0, 120))
        self.escurecer_forte = pygame.Surface((LARGURA, ALTURA), pygame.SRCALPHA)
        self.escurecer_forte.fill((0, 0, 0, 170))

        tecnico = carregar_imagem("TÉCNICO(UM POUCO INSPIRADO).png")
        jogador = carregar_imagem("JOGADORBARATO.png")
        self.img_tecnico = pygame.transform.scale(tecnico, (256, 256)) if tecnico else None
        self.img_jogador = pygame.transform.scale(jogador, (256, 256)) if jogador else None
        self.icone_tecnico = pygame.transform.scale(tecnico, (128, 128)) if tecnico else None
        if tecnico:
            pygame.display.set_icon(tecnico)
        logo = carregar_imagem("KASEL.png")
        self.img_logo = pygame.transform.scale(logo, (96, 96)) if logo else None
        reporter = carregar_imagem("sem_fundo/vorcaro.png")
        self.img_reporter = caber(reporter, 256) if reporter else None
        self.img_reporter_grande = caber(reporter, 400) if reporter else None

        self.escudos_grandes, self.escudos_medios, self.escudos_pequenos, self.escudos_mini = {}, {}, {}, {}
        for time in TIMES:
            img = carregar_imagem(time["escudo"], PASTA_ESCUDOS)
            if img is None:
                img = self.escudo_generico(time["nome"])
            self.escudos_grandes[time["nome"]] = caber(img, 160)
            self.escudos_medios[time["nome"]] = caber(img, 96)
            self.escudos_pequenos[time["nome"]] = caber(img, 36)
            self.escudos_mini[time["nome"]] = caber(img, 26)

    def escudo_generico(self, nome):
        img = pygame.Surface((160, 160), pygame.SRCALPHA)
        caixa_pixel(img, (6, 6, 144, 144), (90, 40, 40), COR_BORDA, p=8, sombra=False)
        texto(img, nome[:3].upper(), self.fonte_h2, COR_BORDA, (78, 78), "center")
        return img

    def iniciar_musica(self):
        """Toca audio/audiojogo.* em loop até o jogo fechar (se houver som disponível)."""
        self.volume = constantes.VOLUME_INICIAL
        self.tem_musica = False
        arquivo = next(iter(sorted(constantes.PASTA_AUDIO.glob("audiojogo.*"))), None)
        if arquivo is None:
            return
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            pygame.mixer.music.load(str(arquivo))
            pygame.mixer.music.set_volume(self.volume)
            pygame.mixer.music.play(-1)
            self.tem_musica = True
        except pygame.error:
            pass

    # ------------------------------------------------------------ infraestrutura
    def ir_para(self, estado):
        self.estado = estado
        self.botoes = []
        getattr(self, f"montar_{estado}")()
        if estado != "menu":
            self.botoes.append(Botao((LARGURA - 164, 20, 140, 48), "CONFIG", ("abrir_config",), self.fonte))

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.esta_rodando = False
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_F11:
                self.acao_tela_cheia()
                continue
            if evento.type == pygame.KEYDOWN and evento.key == pygame.K_ESCAPE:
                if self.config_aberta:
                    self.acao_fechar_config()
                else:
                    self.acao_abrir_config()
                continue
            for botao in (self.botoes_config if self.config_aberta else self.botoes):
                if botao.foi_clicado(evento):
                    nome, *args = botao.acao
                    getattr(self, f"acao_{nome}")(*args)
                    break

    def desenhar(self):
        getattr(self, f"desenhar_{self.estado}")()
        mouse = pygame.mouse.get_pos()
        for botao in self.botoes:
            botao.desenhar(self.tela, (-1, -1) if self.config_aberta else mouse)
        if self.config_aberta:
            self.desenhar_config()
            for botao in self.botoes_config:
                botao.desenhar(self.tela, mouse)
        pygame.display.flip()

    def rodar(self):
        while self.esta_rodando:
            self.clock.tick(constantes.FPS)
            self.eventos()
            if self.esta_rodando:
                self.desenhar()
        pygame.quit()

    def fundo(self, cenario="campo", escuro=True):
        self.tela.blit(self.fundos[cenario], (0, 0))
        if escuro:
            self.tela.blit(self.escurecer, (0, 0))

    def caixa_titulo(self, s, y=20):
        largura = self.fonte_h2.size(s)[0] + 60
        r = pygame.Rect(0, y, largura, 56)
        r.centerx = LARGURA // 2
        caixa_pixel(self.tela, r)
        texto(self.tela, s, self.fonte_h2, COR_DESTAQUE, r.center, "center")

    def desenhar_medidores(self, x, y, largura):
        gap = 24
        w = (largura - 2 * gap) // 3
        for i, medidor in enumerate(sd.MEDIDORES):
            valor = self.tecnico[medidor]
            bx = x + i * (w + gap)
            texto(self.tela, f"{ROTULOS[medidor]} {valor}", self.fonte_pequena, COR_BORDA, (bx, y))
            cor = constantes.VERDE if valor >= 60 else constantes.AMARELO if valor >= 35 else constantes.VERMELHO
            bw = (w - 9 * 3) // 10
            cheios = round(valor / 10)
            for b in range(10):
                bloco = pygame.Rect(bx + b * (bw + 3), y + 24, bw, 16)
                pygame.draw.rect(self.tela, COR_SOMBRA, bloco.move(2, 2))
                pygame.draw.rect(self.tela, cor if b < cheios else COR_VAZIO, bloco)

    def desenhar_personagens(self, cenario="campo"):
        """Técnico à esquerda; à direita o jogador, ou o repórter na coletiva."""
        y = ALTURA - 330
        direita = (self.img_reporter, "REPÓRTER") if cenario == "coletiva" else (self.img_jogador, "JOGADOR")
        for img, rotulo, x in ((self.img_tecnico, "TÉCNICO", 24), (*direita, LARGURA - 280)):
            if img:
                self.tela.blit(img, img.get_rect(midbottom=(x + 128, y + 256)))
            placa = pygame.Rect(x + 38, y + 262, 180, 40)
            caixa_pixel(self.tela, placa, COR_CAIXA, COR_DESTAQUE, p=3)
            texto(self.tela, rotulo, self.fonte, COR_DESTAQUE, placa.center, "center")

    # ------------------------------------------------------------ configurações
    def painel_config(self):
        painel = pygame.Rect(0, 0, 560, 500)
        painel.center = (LARGURA // 2, ALTURA // 2)
        return painel

    def acao_abrir_config(self):
        self.config_aberta = True
        painel = self.painel_config()
        cx = painel.centerx
        self.botoes_config = [
            Botao((painel.x + 40, painel.y + 116, 64, 56), "-", ("volume", -0.1), self.fonte_h2),
            Botao((painel.right - 104, painel.y + 116, 64, 56), "+", ("volume", 0.1), self.fonte_h2),
            Botao((cx - 180, painel.y + 204, 360, 56), "CONTINUAR", ("fechar_config",), self.fonte),
            Botao((cx - 180, painel.y + 272, 360, 56), "TELA CHEIA (F11)", ("tela_cheia",), self.fonte),
        ]
        if self.estado != "menu":
            self.botoes_config.append(
                Botao((cx - 180, painel.y + 340, 360, 56), "MENU INICIAL", ("menu_inicial",), self.fonte))
        self.botoes_config.append(
            Botao((cx - 180, painel.y + 408, 360, 56), "SAIR DO JOGO", ("sair",), self.fonte))

    def desenhar_config(self):
        self.tela.blit(self.escurecer_forte, (0, 0))
        painel = self.painel_config()
        caixa_pixel(self.tela, painel, p=6)
        texto(self.tela, "CONFIGURAÇÕES", self.fonte_h2, COR_DESTAQUE, (painel.centerx, painel.y + 24), "midtop")
        rotulo = f"VOLUME {round(self.volume * 100)}%" if self.tem_musica else "MÚSICA INDISPONÍVEL"
        texto(self.tela, rotulo, self.fonte, COR_BORDA, (painel.centerx, painel.y + 80), "midtop")
        x0, largura = painel.x + 124, painel.w - 248
        bw = (largura - 9 * 4) // 10
        cheios = round(self.volume * 10)
        for b in range(10):
            bloco = pygame.Rect(x0 + b * (bw + 4), painel.y + 126, bw, 36)
            pygame.draw.rect(self.tela, COR_SOMBRA, bloco.move(2, 2))
            pygame.draw.rect(self.tela, COR_DESTAQUE if b < cheios else COR_VAZIO, bloco)

    def acao_volume(self, delta):
        self.volume = round(max(0.0, min(1.0, self.volume + delta)), 1)
        if self.tem_musica:
            pygame.mixer.music.set_volume(self.volume)

    def acao_tela_cheia(self):
        pygame.display.toggle_fullscreen()

    def acao_fechar_config(self):
        self.config_aberta = False
        self.botoes_config = []

    def acao_menu_inicial(self):
        self.acao_fechar_config()
        self.ir_para("menu")

    # ------------------------------------------------------------ menu
    def montar_menu(self):
        cx = LARGURA // 2
        self.botoes = [
            Botao((cx - 170, 390, 340, 66), "NOVO JOGO", ("ir", "escolher_time"), self.fonte_h2),
            Botao((cx - 170, 470, 340, 66), "CONFIGURAÇÕES", ("abrir_config",), self.fonte_h2),
            Botao((cx - 170, 550, 340, 66), "SAIR", ("sair",), self.fonte_h2),
        ]

    def desenhar_menu(self):
        self.fundo("campo", escuro=False)
        r = pygame.Rect(0, 150, 900, 190)
        r.centerx = LARGURA // 2
        caixa_pixel(self.tela, r, p=6)
        texto(self.tela, "SIMULADOR DE TÉCNICO", self.fonte_titulo, COR_DESTAQUE, (r.centerx, r.y + 30), "midtop")
        texto(self.tela, "SOCIOEMOCIONAL", self.fonte_h2, COR_BORDA, (r.centerx, r.y + 100), "midtop")
        texto(self.tela, "Suas decisões mudam o destino do time", self.fonte_pequena, COR_BORDA,
              (r.centerx, r.y + 146), "midtop")
        if self.img_tecnico:
            self.tela.blit(self.img_tecnico, (40, ALTURA - 280))
        if self.img_jogador:
            self.tela.blit(self.img_jogador, (LARGURA - 296, ALTURA - 280))
        if self.img_logo:
            self.tela.blit(self.img_logo, (LARGURA - 112, 16))

    def acao_ir(self, estado):
        self.ir_para(estado)

    def acao_sair(self):
        self.esta_rodando = False

    # ------------------------------------------------------------ escolha do time
    def montar_escolher_time(self):
        por_linha, w, h, gap = 5, 210, 250, 24
        for i, time in enumerate(TIMES):
            linha, col = divmod(i, por_linha)
            n_linha = min(por_linha, len(TIMES) - linha * por_linha)
            x0 = (LARGURA - (n_linha * w + (n_linha - 1) * gap)) // 2
            rect = (x0 + col * (w + gap), 100 + linha * (h + gap), w, h)
            self.botoes.append(Botao(rect, time["nome"], ("escolher_time", time["nome"]), self.fonte,
                                     imagem=self.escudos_grandes[time["nome"]],
                                     legenda=f"FORÇA {time['forca']}", fonte_legenda=self.fonte_pequena))
        self.botoes.append(Botao((24, ALTURA - 80, 180, 56), "VOLTAR", ("ir", "menu"), self.fonte))

    def desenhar_escolher_time(self):
        self.fundo("campo")
        self.caixa_titulo("ESCOLHA SEU TIME")

    def acao_escolher_time(self, nome):
        self.time_usuario = nome
        self.tecnico = dict(constantes.TECNICO_INICIAL)
        self.tabela = {n: {"pts": 0, "j": 0, "v": 0, "e": 0, "d": 0, "gp": 0, "gc": 0}
                       for n in nomes_dos_times()}
        self.rodada = 1
        self.total_decisoes = 0
        self.total_assertivas = 0
        self.sequencia = 0  # decisões assertivas seguidas
        self.iniciar_rodada()

    # ------------------------------------------------------------ rodada (etapas)
    def iniciar_rodada(self):
        if self.rodada > len(self.calendario):
            self.ir_para("fim")
            return
        self.jogos = self.calendario[self.rodada - 1]
        self.jogo_usuario = torneio.jogo_do_usuario(self.jogos, self.time_usuario)
        mandante, visitante = self.jogo_usuario
        self.adversario = visitante if mandante == self.time_usuario else mandante
        self.numero_partida = torneio.numero_do_jogo_do_usuario(self.calendario, self.rodada, self.time_usuario)
        situacao = {"derrotas": self.tabela[self.time_usuario]["d"], "posicao": self.posicao_usuario()}
        self.decisao_rodada = sd.escolher_decisao(self.decisoes, self.numero_partida, situacao)
        self.etapas = sd.fluxo_da_rodada(self.decisao_rodada)
        self.resultados = None
        self.avancar()

    def avancar(self):
        """Vai para a próxima etapa da rodada; sem etapas, começa a próxima rodada."""
        if not self.etapas:
            self.rodada += 1
            self.iniciar_rodada()
            return
        etapa = self.etapas.pop(0)
        if etapa == "decisao":
            self.decisao_atual = self.decisao_rodada
            self.ir_para("decisao")
        elif etapa == "resultado":
            self.simular()
        else:  # anuncio, coletiva, tabela
            self.ir_para(etapa)

    def acao_avancar(self):
        self.avancar()

    def botao_avancar(self, rect=(LARGURA - 344, ALTURA - 84, 320, 64)):
        """Botão que leva à próxima etapa, com o rótulo de acordo com ela."""
        rotulos = {"resultado": "JOGAR PARTIDA", "tabela": "VER TABELA"}
        if self.etapas:
            rotulo = rotulos.get(self.etapas[0], "CONTINUAR")
        else:
            rotulo = "RESULTADO FINAL" if self.rodada >= len(self.calendario) else "PRÓXIMA RODADA"
        self.botoes.append(Botao(rect, rotulo, ("avancar",), self.fonte_h2))

    # ------------------------------------------------------------ anúncio da partida
    def montar_anuncio(self):
        self.botao_avancar((LARGURA // 2 - 180, ALTURA - 100, 360, 64))

    def desenhar_anuncio(self):
        self.fundo("campo")
        self.caixa_titulo(f"RODADA {self.rodada} DE {len(self.calendario)}")
        caixa = pygame.Rect(0, 110, 860, 400)
        caixa.centerx = LARGURA // 2
        caixa_pixel(self.tela, caixa, p=6)

        mandante, visitante = self.jogo_usuario
        for nome, cx in ((mandante, caixa.x + 200), (visitante, caixa.right - 200)):
            esc = self.escudos_grandes[nome]
            self.tela.blit(esc, esc.get_rect(center=(cx, caixa.y + 150)))
            cor = COR_DESTAQUE if nome == self.time_usuario else COR_BORDA
            texto(self.tela, nome.upper(), self.fonte_h2, cor, (cx, caixa.y + 250), "midtop")
        texto(self.tela, "VS", self.fonte_placar, COR_DESTAQUE, (caixa.centerx, caixa.y + 150), "center")
        texto(self.tela, f"Seu adversário: {self.adversario}", self.fonte, COR_BORDA,
              (caixa.centerx, caixa.y + 310), "midtop")
        cor = constantes.VERDE if self.sequencia >= constantes.SEQUENCIA_MINIMA else constantes.AMARELO
        texto(self.tela, f"Sequência de decisões assertivas: {self.sequencia}", self.fonte_pequena, cor,
              (caixa.centerx, caixa.y + 346), "midtop")
        self.desenhar_medidores(caixa.x + 40, caixa.bottom + 20, caixa.w - 80)

    # ------------------------------------------------------------ coletiva de imprensa
    def montar_coletiva(self):
        self.botao_avancar()

    def desenhar_coletiva(self):
        self.fundo("coletiva")
        self.caixa_titulo("COLETIVA DE IMPRENSA")
        if self.img_reporter_grande:
            img_r = self.img_reporter_grande.get_rect(bottomleft=(60, ALTURA - 80))
            self.tela.blit(self.img_reporter_grande, img_r)
            placa = pygame.Rect(0, 0, 200, 40)
            placa.midtop = (img_r.centerx, img_r.bottom + 10)
            caixa_pixel(self.tela, placa, COR_CAIXA, COR_DESTAQUE, p=3)
            texto(self.tela, "REPÓRTER", self.fonte, COR_DESTAQUE, placa.center, "center")

        fala = pygame.Rect(500, 120, LARGURA - 540, 400)
        caixa_pixel(self.tela, fala, p=6)
        texto(self.tela, "AO VIVO DA SALA DE IMPRENSA", self.fonte, COR_DESTAQUE,
              (fala.centerx, fala.y + 24), "midtop")
        discurso = (f"Boa tarde a todos! Estamos ao vivo do centro de treinamento do {self.time_usuario}. "
                    f"Antes do confronto contra o {self.adversario}, o técnico vai encarar as perguntas "
                    "da imprensa. A pressão é grande e cada palavra pode mudar o clima no clube. "
                    "Vamos à primeira pergunta!")
        y = fala.y + 70
        for linha in quebrar(discurso, self.fonte, fala.w - 60):
            texto(self.tela, linha, self.fonte, COR_BORDA, (fala.x + 30, y))
            y += self.fonte.get_linesize() + 4
        esc_meu, esc_adv = self.escudos_medios[self.time_usuario], self.escudos_medios[self.adversario]
        self.tela.blit(esc_meu, esc_meu.get_rect(center=(fala.centerx - 120, fala.bottom - 70)))
        self.tela.blit(esc_adv, esc_adv.get_rect(center=(fala.centerx + 120, fala.bottom - 70)))
        texto(self.tela, "VS", self.fonte_h2, COR_DESTAQUE, (fala.centerx, fala.bottom - 70), "center")

    # ------------------------------------------------------------ decisão
    def area_central(self):
        return pygame.Rect(300, 0, LARGURA - 600, ALTURA)

    def montar_decisao(self):
        centro = self.area_central()
        linhas = quebrar(self.decisao_atual["texto"], self.fonte_h2, centro.w - 60)
        self.linhas_pergunta = linhas
        self.rect_pergunta = pygame.Rect(centro.x, 84, centro.w, len(linhas) * self.fonte_h2.get_linesize() + 70)

        y = self.rect_pergunta.bottom + 24
        lh = self.fonte.get_linesize()
        for i, opcao in enumerate(self.decisao_atual["opcoes"]):
            n = len(quebrar(opcao["texto"], self.fonte, centro.w - 90))
            h = max(66, n * lh + 30)
            self.botoes.append(Botao((centro.x, y, centro.w, h), opcao["texto"], ("escolher", i),
                                     self.fonte, letra="ABCDEFGH"[i]))
            y += h + 16

    def desenhar_cena(self):
        cenario = self.decisao_atual.get("cenario", "campo")
        self.fundo(cenario)
        tag = pygame.Rect(24, 20, 250, 48)
        caixa_pixel(self.tela, tag, COR_CAIXA, COR_DESTAQUE, p=3)
        texto(self.tela, NOMES_CENARIO.get(cenario, cenario.upper()), self.fonte, COR_DESTAQUE, tag.center, "center")

        mandante, visitante = self.jogo_usuario
        placa = pygame.Rect(LARGURA - 434, 20, 250, 48)
        caixa_pixel(self.tela, placa, COR_CAIXA, COR_BORDA, p=3)
        self.tela.blit(self.escudos_pequenos[mandante], (placa.x + 14, placa.y + 6))
        self.tela.blit(self.escudos_pequenos[visitante], (placa.right - 50, placa.y + 6))
        texto(self.tela, "VS", self.fonte, COR_DESTAQUE, placa.center, "center")

        self.desenhar_personagens(cenario)
        centro = self.area_central()
        self.desenhar_medidores(centro.x, ALTURA - 64, centro.w)

    def desenhar_decisao(self):
        self.desenhar_cena()
        caixa_pixel(self.tela, self.rect_pergunta, p=6)
        texto(self.tela, f"DECISÃO {self.numero_partida}", self.fonte_pequena, COR_DESTAQUE,
              (self.rect_pergunta.centerx, self.rect_pergunta.y + 14), "midtop")
        y = self.rect_pergunta.y + 42
        for linha in self.linhas_pergunta:
            texto(self.tela, linha, self.fonte_h2, COR_BORDA, (self.rect_pergunta.centerx, y), "midtop")
            y += self.fonte_h2.get_linesize()

    def acao_escolher(self, indice):
        opcao = self.decisao_atual["opcoes"][indice]
        antes = dict(self.tecnico)
        sd.aplicar_efeito(self.tecnico, self.decisao_atual, indice)
        self.variacao = {m: self.tecnico[m] - antes[m] for m in sd.MEDIDORES}
        self.opcao_escolhida = opcao
        self.total_decisoes += 1
        if opcao.get("assertiva"):
            self.total_assertivas += 1
            self.sequencia += 1
        else:
            self.sequencia = 0
        self.ir_para("feedback")

    def montar_feedback(self):
        centro = self.area_central()
        self.botao_avancar((centro.centerx - 160, 412, 320, 64))

    def desenhar_feedback(self):
        self.desenhar_cena()
        centro = self.area_central()
        caixa = pygame.Rect(centro.x, 84, centro.w, 300)
        assertiva = self.opcao_escolhida.get("assertiva")
        caixa_pixel(self.tela, caixa, borda=constantes.VERDE if assertiva else constantes.VERMELHO, p=6)

        titulo = "DECISÃO ASSERTIVA!" if assertiva else "DECISÃO ARRISCADA..."
        texto(self.tela, titulo, self.fonte_h2, constantes.VERDE if assertiva else constantes.VERMELHO,
              (caixa.centerx, caixa.y + 24), "midtop")
        y = caixa.y + 80
        for linha in quebrar(f"Você escolheu: {self.opcao_escolhida['texto']}", self.fonte, caixa.w - 60):
            texto(self.tela, linha, self.fonte, COR_BORDA, (caixa.centerx, y), "midtop")
            y += self.fonte.get_linesize()
        y += 20
        for medidor in sd.MEDIDORES:
            d = self.variacao[medidor]
            cor = constantes.VERDE if d > 0 else constantes.VERMELHO if d < 0 else COR_BORDA
            texto(self.tela, f"{ROTULOS[medidor]}: {d:+d}", self.fonte, cor, (caixa.centerx, y), "midtop")
            y += self.fonte.get_linesize() + 4
        texto(self.tela, f"Sequência de decisões assertivas: {self.sequencia}",
              self.fonte_pequena, COR_DESTAQUE, (caixa.centerx, y + 8), "midtop")

    # ------------------------------------------------------------ simulação e resultado
    def simular(self):
        """Medidores baixos, sem sequência de 2+ acertos ou derrota roteirizada (campo
        "resultado" do JSON) -> o time perde. Senão a sequência dá bônus de força."""
        forcar_derrota = ((self.decisao_rodada or {}).get("resultado") == "derrota"
                          or torneio.time_em_ma_fase(self.tecnico, self.sequencia))
        self.resultados = torneio.simular_rodada(
            self.jogos, self.forcas, self.time_usuario, self.tecnico,
            acertos=min(self.sequencia, constantes.SEQUENCIA_MAXIMA), forcar_derrota=forcar_derrota)
        for mandante, visitante, gm, gv, *_ in self.resultados:
            for nome, gp, gc in ((mandante, gm, gv), (visitante, gv, gm)):
                t = self.tabela[nome]
                t["j"] += 1
                t["gp"] += gp
                t["gc"] += gc
                if gp > gc:
                    t["v"] += 1
                    t["pts"] += 3
                elif gp == gc:
                    t["e"] += 1
                    t["pts"] += 1
                else:
                    t["d"] += 1
        self.ir_para("resultado")

    def classificacao(self):
        return sorted(self.tabela.items(),
                      key=lambda kv: (kv[1]["pts"], kv[1]["gp"] - kv[1]["gc"], kv[1]["gp"]), reverse=True)

    def posicao_usuario(self):
        return [nome for nome, _ in self.classificacao()].index(self.time_usuario) + 1

    def montar_resultado(self):
        self.botao_avancar()

    def desenhar_resultado(self):
        self.fundo("campo")
        self.caixa_titulo(f"RODADA {self.rodada} - RESULTADO", y=12)

        topo = pygame.Rect(0, 82, 760, 170)
        topo.centerx = LARGURA // 2
        caixa_pixel(self.tela, topo, p=6)
        m, v, gm, gv = next(r for r in self.resultados if self.time_usuario in r[:2])[:4]
        self.tela.blit(self.escudos_medios[m], self.escudos_medios[m].get_rect(center=(topo.x + 110, topo.y + 70)))
        self.tela.blit(self.escudos_medios[v], self.escudos_medios[v].get_rect(center=(topo.right - 110, topo.y + 70)))
        texto(self.tela, m, self.fonte_pequena, COR_BORDA, (topo.x + 110, topo.y + 126), "midtop")
        texto(self.tela, v, self.fonte_pequena, COR_BORDA, (topo.right - 110, topo.y + 126), "midtop")
        texto(self.tela, f"{gm} x {gv}", self.fonte_placar, COR_BORDA, (topo.centerx, topo.y + 62), "center")
        meus, deles = (gm, gv) if m == self.time_usuario else (gv, gm)
        if meus > deles:
            rotulo, cor = "VITÓRIA!", constantes.VERDE
        elif meus == deles:
            rotulo, cor = "EMPATE", constantes.AMARELO
        else:
            rotulo, cor = "DERROTA", constantes.VERMELHO
        texto(self.tela, rotulo, self.fonte_h2, cor, (topo.centerx, topo.y + 118), "midtop")

        outros = pygame.Rect(0, 272, 760, 300)
        outros.centerx = LARGURA // 2
        caixa_pixel(self.tela, outros)
        texto(self.tela, "OUTROS JOGOS DA RODADA", self.fonte, COR_DESTAQUE, (outros.centerx, outros.y + 20), "midtop")
        y = outros.y + 74
        for m, v, gm, gv, *_ in self.resultados:
            if self.time_usuario in (m, v):
                continue
            self.tela.blit(self.escudos_pequenos[m], (outros.x + 30, y - 6))
            texto(self.tela, m, self.fonte, COR_BORDA, (outros.x + 80, y))
            texto(self.tela, f"{gm} x {gv}", self.fonte, COR_DESTAQUE, (outros.centerx, y), "midtop")
            texto(self.tela, v, self.fonte, COR_BORDA, (outros.right - 80, y), "topright")
            self.tela.blit(self.escudos_pequenos[v], (outros.right - 66, y - 6))
            y += 52

        self.desenhar_medidores(24, ALTURA - 74, 860)

    # ------------------------------------------------------------ tabela da liga
    def montar_tabela(self):
        self.botao_avancar()

    def desenhar_tabela(self):
        self.fundo("campo")
        self.caixa_titulo(f"CLASSIFICAÇÃO - RODADA {self.rodada}", y=12)
        caixa = pygame.Rect(0, 82, 820, 410)
        caixa.centerx = LARGURA // 2
        self.desenhar_classificacao(caixa)
        self.desenhar_medidores(caixa.x + 20, caixa.bottom + 24, caixa.w - 40)

    def desenhar_classificacao(self, caixa):
        caixa_pixel(self.tela, caixa)
        direita = caixa.w - 50
        colunas = [("#", 22), ("", 58), ("TIME", 96), ("P", direita - 300), ("J", direita - 240),
                   ("V", direita - 180), ("E", direita - 120), ("D", direita - 60), ("SG", direita)]
        for rotulo, dx in colunas:
            texto(self.tela, rotulo, self.fonte_pequena, COR_DESTAQUE, (caixa.x + dx, caixa.y + 16))
        y = caixa.y + 48
        for pos, (nome, t) in enumerate(self.classificacao(), 1):
            if nome == self.time_usuario:
                pygame.draw.rect(self.tela, COR_LINHA_USUARIO, (caixa.x + 10, y - 4, caixa.w - 20, 34))
            esc = self.escudos_mini[nome]
            self.tela.blit(esc, esc.get_rect(center=(caixa.x + 70, y + 12)))
            valores = [pos, "", nome, t["pts"], t["j"], t["v"], t["e"], t["d"], t["gp"] - t["gc"]]
            for (_, dx), valor in zip(colunas, valores):
                texto(self.tela, str(valor), self.fonte_pequena, COR_BORDA, (caixa.x + dx, y + 2), sombra=False)
            y += 35

    # ------------------------------------------------------------ fim
    def montar_fim(self):
        cx = LARGURA // 2
        self.botoes = [
            Botao((cx - 360, ALTURA - 96, 340, 64), "JOGAR NOVAMENTE", ("ir", "escolher_time"), self.fonte_h2),
            Botao((cx + 20, ALTURA - 96, 340, 64), "MENU", ("ir", "menu"), self.fonte_h2),
        ]

    def desfecho(self, posicao):
        ultimo = len(self.tabela)
        if posicao == 1:
            return "CAMPEÃO!", COR_DESTAQUE
        if posicao <= 4:
            return "CLASSIFICADO PARA A LIBERTADORES", constantes.VERDE
        if posicao <= 6:
            return "CLASSIFICADO PARA A SUL-AMERICANA", constantes.AZUL_CLARO
        if posicao >= ultimo - 1:
            return "REBAIXADO", constantes.VERMELHO
        return "PERMANECEU NA SÉRIE A", COR_BORDA

    def desenhar_fim(self):
        self.fundo("campo")
        posicao = self.posicao_usuario()
        pts = self.tabela[self.time_usuario]["pts"]
        rotulo, cor = self.desfecho(posicao)

        caixa = pygame.Rect(0, 40, 900, 520)
        caixa.centerx = LARGURA // 2
        caixa_pixel(self.tela, caixa, borda=cor, p=6)
        texto(self.tela, "FIM DE TEMPORADA", self.fonte_h2, COR_BORDA, (caixa.centerx, caixa.y + 24), "midtop")
        self.tela.blit(self.escudos_grandes[self.time_usuario],
                       self.escudos_grandes[self.time_usuario].get_rect(center=(caixa.centerx, caixa.y + 160)))
        texto(self.tela, rotulo, self.fonte_titulo if len(rotulo) < 16 else self.fonte_h2, cor,
              (caixa.centerx, caixa.y + 260), "midtop")
        texto(self.tela, f"{self.time_usuario} terminou em {posicao}º lugar com {pts} pontos",
              self.fonte, COR_BORDA, (caixa.centerx, caixa.y + 340), "midtop")
        texto(self.tela, f"Decisões assertivas: {self.total_assertivas} de {self.total_decisoes}",
              self.fonte, COR_DESTAQUE, (caixa.centerx, caixa.y + 378), "midtop")
        self.desenhar_medidores(caixa.x + 50, caixa.y + 430, caixa.w - 100)
        if self.icone_tecnico:
            self.tela.blit(self.icone_tecnico, (caixa.x + 30, caixa.y + 90))
        if self.img_jogador:
            jog = pygame.transform.scale(self.img_jogador, (128, 128))
            self.tela.blit(jog, (caixa.right - 158, caixa.y + 90))


if __name__ == "__main__":
    Game().rodar()
    sys.exit()
