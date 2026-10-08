from doctest import script_from_examples

import pygame

x = 1280
y = 720

screen = pygame.display.set_mode((x,y))
pygame.display.set_caption("Jogo")
jogotelafundo = pygame.image.load('imagens_/telacampo.jpg').convert_alpha()
jogotelafundo = pygame.transform.scale(jogotelafundo,(x,y))

rodando = True

while rodando:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            rodando = False
    screen.blit( jogotelafundo,(0,0))

    pygame.display.update()
