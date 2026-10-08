import pygame
from sys import exit
from pygame.locals import *
import constantes
import json
import os

# Definição de cores de segurança (fallback caso falhe no constantes.py)
COR_BRANCO = getattr(constantes, 'BRANCO', (255, 255, 255))
COR_PRETO = getattr(constantes, 'PRETO', (0, 0, 0))
LARGURA_TELA = getattr(constantes, 'LARGURA', 800)
ALTURA_TELA = getattr(constantes, 'ALTURA', 600)
TITULO_JOGO = getattr(constantes, 'TITULO', "Trabalho Social Emocional")
FPS_JOGO = getattr(constantes, 'FPS', 60)


class Game:
    def __init__(self):
        # Inicialização do Pygame
        pygame.init()
        pygame.mixer.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        self.clock = pygame.time.Clock()
        self.esta_rodando = True

        # Configuração de Fontes
        self.fonte_titulo = pygame.font.SysFont('Arial', 32, bold=True)
        self.fonte_texto = pygame.font.SysFont('Arial', 20)
        self.fonte_botao = pygame.font.SysFont('Arial', 18, bold=True)

        # Carregar escudos e dilemas
        self.escudos = self.carregar_escudos()
        self.perguntas = self.carregar_decisoes()
        self.indice_pergunta = 0
        self.pontuacao_socioemocional = 0

    def carregar_escudos(self):
        escudos_dict = {}
        pasta_escudos = os.path.join('data', 'escudos')
        if os.path.exists(pasta_escudos):
            for ficheiro in os.listdir(pasta_escudos):
                if ficheiro.endswith(('.png', '.jpg', '.jpeg')):
                    nome_time = os.path.splitext(ficheiro)[0].lower()
                    caminho = os.path.join(pasta_escudos, ficheiro)
                    try:
                        imagem = pygame.image.load(caminho).convert_alpha()
                        imagem = pygame.transform.scale(imagem, (80, 80))
                        escudos_dict[nome_time] = imagem
                    except Exception as e:
                        print(f"Erro ao carregar escudo {ficheiro}: {e}")
        return escudos_dict

    def carregar_decisoes(self):
        caminho_json = os.path.join('data', 'decisoes.json')
        if os.path.exists(caminho_json):
            try:
                with open(caminho_json, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Erro ao carregar decisoes.json: {e}")
        return [
            {
                "situacao": "Seu atacante perdeu um pênalti decisivo no último minuto da partida.",
                "opcao_a": "Apoiar o jogador e trabalhar a resiliência no vestiário.",
                "pontos_a": 10,
                "opcao_b": "Criticar publicamente a cobrança na coletiva de imprensa.",
                "pontos_b": -5,
                "time": "flamengo"
            }
        ]

    def novo_jogo(self):
        self.todas_sprites = pygame.sprite.Group()
        self.indice_pergunta = 0
        self.pontuacao_socioemocional = 0
        self.rodar()

    def rodar(self):
        self.jogando = True
        while self.jogando:
            self.clock.tick(FPS_JOGO)
            self.eventos()
            self.atualizar_sprites()
            self.desenhar_sprites()

    def eventos(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.jogando:
                    self.jogando = False
                self.esta_rodando = False

            if event.type == MOUSEBUTTONDOWN:
                pos_mouse = event.pos

                # Clique na Opção A
                if hasattr(self, 'rect_opcao_a') and self.rect_opcao_a.collidepoint(pos_mouse):
                    if self.indice_pergunta < len(self.perguntas):
                        self.pontuacao_socioemocional += self.perguntas[self.indice_pergunta].get("pontos_a", 10)
                        self.proxima_pergunta()

                # Clique na Opção B
                elif hasattr(self, 'rect_opcao_b') and self.rect_opcao_b.collidepoint(pos_mouse):
                    if self.indice_pergunta < len(self.perguntas):
                        self.pontuacao_socioemocional += self.perguntas[self.indice_pergunta].get("pontos_b", -5)
                        self.proxima_pergunta()

    def proxima_pergunta(self):
        self.indice_pergunta += 1
        if self.indice_pergunta >= len(self.perguntas):
            self.tela_de_game_over()

    def atualizar_sprites(self):
        self.todas_sprites.update()

    def desenhar_sprites(self):
        self.tela.fill(COR_PRETO)

        if self.indice_pergunta < len(self.perguntas):
            pergunta_atual = self.perguntas[self.indice_pergunta]

            # 1. Placar Socioemocional
            txt_placar = self.fonte_titulo.render(f"Pontos Socioemocionais: {self.pontuacao_socioemocional}", True,
                                                  COR_BRANCO)
            self.tela.blit(txt_placar, (50, 30))

            # 2. Desenhar Escudo
            nome_time = pergunta_atual.get("time", "").lower()
            if nome_time in self.escudos:
                escudo_img = self.escudos[nome_time]
                self.tela.blit(escudo_img, (LARGURA_TELA - 130, 20))
            elif self.escudos:
                primeiro_escudo = list(self.escudos.values())[0]
                self.tela.blit(primeiro_escudo, (LARGURA_TELA - 130, 20))

            # 3. Dilema/Situação
            txt_sit = self.fonte_texto.render(pergunta_atual["situacao"], True, COR_BRANCO)
            self.tela.blit(txt_sit, (50, 130))

            # 4. Botão Opção A
            self.rect_opcao_a = pygame.Rect(50, 220, LARGURA_TELA - 100, 60)
            pygame.draw.rect(self.tela, (40, 140, 60), self.rect_opcao_a, border_radius=10)
            txt_a = self.fonte_botao.render(f"A) {pergunta_atual['opcao_a']}", True, COR_BRANCO)
            self.tela.blit(txt_a, (self.rect_opcao_a.x + 20, self.rect_opcao_a.y + 18))

            # 5. Botão Opção B
            self.rect_opcao_b = pygame.Rect(50, 310, LARGURA_TELA - 100, 60)
            pygame.draw.rect(self.tela, (180, 50, 50), self.rect_opcao_b, border_radius=10)
            txt_b = self.fonte_botao.render(f"B) {pergunta_atual['opcao_b']}", True, COR_BRANCO)
            self.tela.blit(txt_b, (self.rect_opcao_b.x + 20, self.rect_opcao_b.y + 18))

        self.todas_sprites.draw(self.tela)
        pygame.display.flip()

    def tela_de_start(self):
        aguardando = True
        while aguardando:
            self.clock.tick(FPS_JOGO)
            self.tela.fill(COR_PRETO)

            txt_titulo = self.fonte_titulo.render(TITULO_JOGO, True, COR_BRANCO)
            txt_sub = self.fonte_texto.render("Pressione qualquer tecla para começar...", True, (200, 200, 200))

            self.tela.blit(txt_titulo, (LARGURA_TELA // 2 - txt_titulo.get_width() // 2, 180))
            self.tela.blit(txt_sub, (LARGURA_TELA // 2 - txt_sub.get_width() // 2, 280))

            # Exibe escudos decorativos no menu inicial
            x_pos = 50
            for imagem in list(self.escudos.values())[:5]:
                self.tela.blit(imagem, (x_pos, 380))
                x_pos += 110

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    aguardando = False
                    self.esta_rodando = False
                if event.type == pygame.KEYUP or event.type == MOUSEBUTTONDOWN:
                    aguardando = False

    def tela_de_game_over(self):
        self.jogando = False
        aguardando = True
        while aguardando:
            self.clock.tick(FPS_JOGO)
            self.tela.fill(COR_PRETO)

            txt_fim = self.fonte_titulo.render("Fim da Jornada!", True, COR_BRANCO)
            txt_pontos = self.fonte_texto.render(f"Pontuação Final: {self.pontuacao_socioemocional}", True, COR_BRANCO)
            txt_reiniciar = self.fonte_texto.render("Pressione R para Jogar Novamente ou Q para Sair", True,
                                                    (180, 180, 180))

            self.tela.blit(txt_fim, (LARGURA_TELA // 2 - txt_fim.get_width() // 2, 150))
            self.tela.blit(txt_pontos, (LARGURA_TELA // 2 - txt_pontos.get_width() // 2, 220))
            self.tela.blit(txt_reiniciar, (LARGURA_TELA // 2 - txt_reiniciar.get_width() // 2, 320))

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    aguardando = False
                    self.esta_rodando = False
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        aguardando = False
                        self.novo_jogo()
                    elif event.key == pygame.K_q:
                        aguardando = False
                        self.esta_rodando = False


g = Game()
g.tela_de_start()

while g.esta_rodando:
    g.novo_jogo()

pygame.quit()
exit()