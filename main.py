import pygame
from sys import exit
from pygame.locals import *
import constantes


class Game:
    def __init__(self):
        # CRIADA TELA DO JOGO
        pygame.init()
        pygame.mixer.init()
        self.tela = pygame.display.set_mode((constantes.LARGURA, constantes.ALTURA))
        pygame.display.set_caption((constantes.TITULO))
        self.clock = pygame.time.Clock()
        self.esta_rodando = True

    def novo_jogo(self):
        self.todas_sprites = pygame.sprite.Group()
        self.rodar()

    def rodar(self):
        # loop do jogo
        self.jogando = True
        while self.jogando:
            self.clock.tick(constantes.FPS)
            self.eventos()
            self.atualizar_sprites()
            self.desenhar_sprites()

    def eventos(self):
        # isso define os eventos que ocorrem durante o jogo
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                if self.jogando:
                    self.jogando = False
                self.esta_rodando = False

    def atualizar_sprites(self):
        # Atualizar sprites do jogo
        self.todas_sprites.update()

    def desenhar_sprites(self):
        self.tela.fill(constantes.PRETO)
        self.todas_sprites.draw(self.tela)
        pygame.display.flip()

    def tela_de_start(self):
        pass


g = Game()
g.tela_de_start()

while g.esta_rodando:
    g.novo_jogo()
