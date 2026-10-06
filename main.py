import sys
from datetime import datetime

import pygame

import constantes
import torneio
from times import TIMES, buscar_time, forcas_dos_times, nomes_dos_times
from src.systems import banco_dados as banco
from src.systems import sistema_decisao as sd
from src.ui.componentes import (
    Botao, desenhar_barra, desenhar_escudo, desenhar_paragrafo, desenhar_texto,
)

ROTULOS = {"relacionamento": "Relacionamento", "estabilidade": "Estabilidade",
           "reputacao": "Reputação"}
MAX_SAVES_NA_TELA = 6
MAX_RODADAS_NA_TELA = 8


class Game:
    """Controla a janela e as telas do jogo.

    Cada tela é um "estado" (menu, novo, saves, rodadas, confirmar, prejogo, decisao,
    feedback, resultado, classificacao, historico, fim). Para cada estado existem:
      montar_<estado>()    cria os botões da tela
      desenhar_<estado>()  desenha o conteúdo da tela
    Os cliques nos botões chamam os métodos acao_<nome>().
    """

    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((constantes.LARGURA, constantes.ALTURA))
        pygame.display.set_caption(constantes.TITULO)
        self.clock = pygame.time.Clock()
        self.esta_rodando = True

        self.fonte_titulo = pygame.font.Font(None, 72)
        self.fonte_h2 = pygame.font.Font(None, 46)
        self.fonte = pygame.font.Font(None, 34)
        self.fonte_pequena = pygame.font.Font(None, 26)

        self.conn = banco.conectar()
        self.decisoes = sd.carregar_decisoes()
        self.calendario = torneio.gerar_calendario(nomes_dos_times())
        self.total_rodadas = len(self.calendario)

        # estado do torneio em andamento
        self.tid = None
        self.dados_torneio = None
        self.time_usuario = None
        self.tecnico = None
        self.rodada = 1
        self.jogos = []
        self.decisoes_pendentes = []
        self.decisoes_tomadas = []
        self.decisao_atual = None
        self.ultima_escolha = None
        self.resultados = []

        self.mensagem = ""
        self.botoes = []
        self.ir_para("menu")

    # ------------------------------------------------------------------ infraestrutura
    def ir_para(self, estado):
        self.estado = estado
        self.botoes = []
        getattr(self, f"montar_{estado}")()

    def ao_clicar(self, acao):
        nome, *argumentos = acao
        getattr(self, f"acao_{nome}")(*argumentos)

    def eventos(self):
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                self.esta_rodando = False
            for botao in self.botoes:
                if botao.foi_clicado(evento):
                    self.ao_clicar(botao.acao)
                    break  # a lista de botões pode ter mudado

    def desenhar(self):
        self.tela.fill(constantes.FUNDO)
        getattr(self, f"desenhar_{self.estado}")()
        mouse = pygame.mouse.get_pos()
        for botao in self.botoes:
            botao.desenhar(self.tela, self.fonte, mouse)
        sobrepor = getattr(self, f"sobrepor_{self.estado}", None)
        if sobrepor:
            sobrepor()
        pygame.display.flip()

    def rodar(self):
        while self.esta_rodando:
            self.clock.tick(constantes.FPS)
            self.eventos()
            self.desenhar()
        self.conn.close()
        pygame.quit()

    # ------------------------------------------------------------------ utilidades
    @property
    def cx(self):
        return constantes.LARGURA // 2

    def titulo_tela(self, texto):
        desenhar_texto(self.tela, texto, self.fonte_h2, constantes.BRANCO, (self.cx, 30),
                       centralizado=True)

    def time_por_nome(self, nome):
        return buscar_time(nome) or {"nome": nome, "escudo": None}

    def desenhar_medidores(self, y, valores=None):
        valores = valores or self.tecnico
        for i, medidor in enumerate(("relacionamento", "estabilidade", "reputacao")):
            desenhar_barra(self.tela, self.fonte_pequena, ROTULOS[medidor], valores[medidor],
                           (70 + i * 390, y), 360)

    def texto_status(self, torneio_salvo):
        if torneio_salvo["status"] == "finalizado":
            return "Finalizado"
        return f"Rodada {torneio_salvo['rodada_atual']}/{self.total_rodadas}"

    def tabela_classificacao(self):
        linhas = [dict(l) for l in banco.classificacao(self.conn, self.tid)]
        jogaram = {l["time"] for l in linhas}
        for nome in nomes_dos_times():
            if nome not in jogaram:
                linhas.append({"time": nome, "jogos": 0, "vitorias": 0, "empates": 0,
                               "derrotas": 0, "gols_pro": 0, "gols_contra": 0, "pontos": 0})
        return linhas

    # ------------------------------------------------------------------ fluxo do torneio
    def carregar_jogo(self, tid):
        dados, tecnico = banco.carregar_torneio(self.conn, tid)
        if dados is None or dados["time_usuario"] not in nomes_dos_times():
            self.mensagem = "Não foi possível abrir esse save (o time não existe mais)."
            self.ir_para("menu")
            return
        self.tid = tid
        self.dados_torneio = dados
        self.tecnico = tecnico
        self.time_usuario = dados["time_usuario"]
        self.mensagem = ""
        self.iniciar_rodada()

    def iniciar_rodada(self):
        self.rodada = self.dados_torneio["rodada_atual"]
        if self.rodada > self.total_rodadas:
            self.ir_para("fim")
            return
        self.jogos = self.calendario[self.rodada - 1]
        numero = torneio.numero_do_jogo_do_usuario(self.calendario, self.rodada,
                                                   self.time_usuario)
        self.decisoes_pendentes = sd.buscar_decisoes(self.decisoes, numero) if numero else []
        self.decisoes_tomadas = []
        self.ir_para("prejogo")

    def proxima_decisao(self):
        if self.decisoes_pendentes:
            self.decisao_atual = self.decisoes_pendentes.pop(0)
            self.ir_para("decisao")
        else:
            self.jogar_rodada()

    def jogar_rodada(self):
        finalizado = self.rodada == self.total_rodadas
        self.resultados = torneio.simular_rodada(self.jogos, forcas_dos_times(),
                                                 self.time_usuario, self.tecnico,
                                                 acertos=sd.contar_acertos(
                                                     self.decisoes, self.decisoes_tomadas))
        # tudo é gravado de uma vez: se fechar o jogo no meio da rodada, nada fica pela metade
        banco.fechar_rodada(self.conn, self.tid, self.rodada, self.resultados,
                            self.decisoes_tomadas, self.tecnico, finalizado)
        self.dados_torneio["rodada_atual"] = self.rodada + 1
        self.dados_torneio["status"] = "finalizado" if finalizado else "em_andamento"
        self.ir_para("resultado")

    # ------------------------------------------------------------------ MENU
    def montar_menu(self):
        x = (constantes.LARGURA - 460) // 2
        tem_saves = bool(banco.listar_torneios(self.conn))
        self.botoes = [
            Botao((x, 290, 460, 70), "Novo jogo", ("novo",), destaque=True),
            Botao((x, 380, 460, 70), "Continuar / carregar save", ("saves",), ativo=tem_saves),
            Botao((x, 470, 460, 70), "Sair", ("sair",)),
        ]

    def desenhar_menu(self):
        desenhar_texto(self.tela, constantes.TITULO, self.fonte_titulo, constantes.BRANCO,
                       (self.cx, 100), centralizado=True)
        desenhar_texto(self.tela, "Tome boas decisões e leve seu time ao título",
                       self.fonte, constantes.CINZA, (self.cx, 185), centralizado=True)
        if self.mensagem:
            desenhar_texto(self.tela, self.mensagem, self.fonte_pequena, constantes.VERMELHO,
                           (self.cx, 590), centralizado=True)

    def acao_menu(self):
        self.mensagem = ""
        self.ir_para("menu")

    def acao_sair(self):
        self.esta_rodando = False

    # ------------------------------------------------------------------ NOVO JOGO
    def montar_novo(self):
        colunas, largura, altura, espaco = 4, 270, 150, 20
        x0 = (constantes.LARGURA - (colunas * largura + (colunas - 1) * espaco)) // 2
        self.cartas_times = []
        for i, time in enumerate(TIMES):
            rect = pygame.Rect(x0 + (i % colunas) * (largura + espaco),
                               130 + (i // colunas) * (altura + espaco), largura, altura)
            self.cartas_times.append((rect, time))
            self.botoes.append(Botao(rect, time["nome"], ("escolher_time", time["nome"]),
                                     texto_embaixo=True))
        self.botoes.append(Botao((40, 670, 200, 50), "Voltar", ("menu",)))

    def desenhar_novo(self):
        self.titulo_tela("Escolha o time que você vai treinar")

    def sobrepor_novo(self):
        for rect, time in self.cartas_times:
            desenhar_escudo(self.tela, time, (rect.centerx, rect.y + 45), 70)
            desenhar_texto(self.tela, f"Força {time['forca']}", self.fonte_pequena,
                           constantes.CINZA, (rect.centerx, rect.bottom - 30),
                           centralizado=True)

    def acao_novo(self):
        self.ir_para("novo")

    def acao_escolher_time(self, nome):
        nome_torneio = f"{nome} - {datetime.now():%d/%m/%Y %H:%M}"
        tid = banco.novo_torneio(self.conn, nome_torneio, nome, dict(constantes.TECNICO_INICIAL))
        self.carregar_jogo(tid)

    # ------------------------------------------------------------------ SAVES
    def montar_saves(self):
        self.lista_saves = banco.listar_torneios(self.conn)[:MAX_SAVES_NA_TELA]
        for i, t in enumerate(self.lista_saves):
            y = 150 + i * 80
            self.botoes.append(Botao((820, y, 200, 64), "Continuar", ("continuar", t["id"])))
            self.botoes.append(Botao((1040, y, 200, 64), "Voltar rodada", ("rodadas", t["id"])))
        self.botoes.append(Botao((40, 670, 200, 50), "Voltar", ("menu",)))

    def desenhar_saves(self):
        self.titulo_tela("Seus torneios")
        if not self.lista_saves:
            desenhar_texto(self.tela, "Nenhum torneio salvo ainda.", self.fonte,
                           constantes.CINZA, (self.cx, 300), centralizado=True)
        for i, t in enumerate(self.lista_saves):
            y = 150 + i * 80
            pygame.draw.rect(self.tela, constantes.DESTAQUE, (40, y, 1200, 64), border_radius=10)
            desenhar_texto(self.tela, t["nome"], self.fonte, constantes.BRANCO, (60, y + 6))
            sub = f"{self.texto_status(t)}  |  atualizado em {t['atualizado_em'].replace('T', ' ')}"
            desenhar_texto(self.tela, sub, self.fonte_pequena, constantes.CINZA, (60, y + 37))

    def acao_saves(self):
        self.ir_para("saves")

    def acao_continuar(self, tid):
        self.carregar_jogo(tid)

    # ------------------------------------------------------------------ VOLTAR RODADA
    def montar_rodadas(self):
        dados, _ = banco.carregar_torneio(self.conn, self.tid_voltar)
        anteriores = [c for c in banco.listar_checkpoints(self.conn, self.tid_voltar)
                      if c["rodada"] < dados["rodada_atual"]]
        self.checkpoints_tela = anteriores[-MAX_RODADAS_NA_TELA:]
        for i, c in enumerate(self.checkpoints_tela):
            self.botoes.append(Botao((900, 150 + i * 60, 340, 50),
                                     f"Voltar para a rodada {c['rodada']}",
                                     ("confirmar_voltar", c["rodada"])))
        self.botoes.append(Botao((40, 670, 200, 50), "Voltar", ("saves",)))

    def desenhar_rodadas(self):
        self.titulo_tela("Voltar para uma rodada anterior")
        desenhar_texto(self.tela, "O progresso a partir da rodada escolhida será apagado.",
                       self.fonte_pequena, constantes.CINZA, (self.cx, 92), centralizado=True)
        if not self.checkpoints_tela:
            desenhar_texto(self.tela, "Nenhuma rodada anterior para voltar.", self.fonte,
                           constantes.CINZA, (self.cx, 300), centralizado=True)
        for i, c in enumerate(self.checkpoints_tela):
            y = 150 + i * 60
            desenhar_texto(self.tela, f"Início da rodada {c['rodada']}", self.fonte,
                           constantes.BRANCO, (60, y + 2))
            medidores = "  |  ".join(f"{ROTULOS[m]} {c[m]}" for m in
                                     ("relacionamento", "estabilidade", "reputacao"))
            desenhar_texto(self.tela, medidores, self.fonte_pequena, constantes.CINZA,
                           (60, y + 28))

    def acao_rodadas(self, tid):
        self.tid_voltar = tid
        self.ir_para("rodadas")

    def montar_confirmar(self):
        self.botoes = [
            Botao((330, 400, 280, 70), "Sim, voltar", ("voltar_checkpoint",), destaque=True),
            Botao((670, 400, 280, 70), "Cancelar", ("rodadas", self.tid_voltar)),
        ]

    def desenhar_confirmar(self):
        self.titulo_tela("Tem certeza?")
        desenhar_paragrafo(
            self.tela,
            f"Voltar para o início da rodada {self.rodada_destino}? As partidas, as decisões "
            "e os saves posteriores a ela serão apagados e não poderão ser recuperados.",
            self.fonte_h2, constantes.BRANCO, (self.cx, 160), 900, centralizado=True)

    def acao_confirmar_voltar(self, rodada):
        self.rodada_destino = rodada
        self.ir_para("confirmar")

    def acao_voltar_checkpoint(self):
        banco.voltar_checkpoint(self.conn, self.tid_voltar, self.rodada_destino)
        self.carregar_jogo(self.tid_voltar)

    # ------------------------------------------------------------------ ANTES DO JOGO
    def montar_prejogo(self):
        self.botoes = [
            Botao((490, 570, 300, 70), "Começar rodada", ("seguir",), destaque=True),
            Botao((40, 670, 200, 50), "Menu", ("menu",)),
        ]

    def desenhar_prejogo(self):
        self.titulo_tela(f"Rodada {self.rodada} de {self.total_rodadas}")
        desenhar_texto(self.tela, f"Você treina: {self.time_usuario}", self.fonte,
                       constantes.CINZA, (self.cx, 90), centralizado=True)
        jogo = torneio.jogo_do_usuario(self.jogos, self.time_usuario)
        if jogo:
            for lado, nome in ((-1, jogo[0]), (1, jogo[1])):
                centro_x = self.cx + lado * 260
                desenhar_escudo(self.tela, self.time_por_nome(nome), (centro_x, 220), 120)
                desenhar_texto(self.tela, nome, self.fonte_h2, constantes.BRANCO,
                               (centro_x, 300), centralizado=True)
            desenhar_texto(self.tela, "x", self.fonte_titulo, constantes.BRANCO,
                           (self.cx, 190), centralizado=True)
        else:
            desenhar_texto(self.tela, "Seu time folga nesta rodada.", self.fonte_h2,
                           constantes.BRANCO, (self.cx, 240), centralizado=True)
        desenhar_texto(self.tela, "Seus medidores", self.fonte, constantes.CINZA,
                       (self.cx, 390), centralizado=True)
        self.desenhar_medidores(440)

    def acao_seguir(self):
        self.proxima_decisao()

    # ------------------------------------------------------------------ DECISÃO
    def montar_decisao(self):
        for i, opcao in enumerate(self.decisao_atual["opcoes"]):
            self.botoes.append(Botao((140, 330 + i * 100, 1000, 84), opcao["texto"],
                                     ("escolher_opcao", i)))

    def desenhar_decisao(self):
        self.titulo_tela(f"Rodada {self.rodada} - Decisão do técnico")
        self.desenhar_medidores(85)
        desenhar_paragrafo(self.tela, self.decisao_atual["texto"], self.fonte_h2,
                           constantes.BRANCO, (140, 190), 1000, espacamento=8)

    def acao_escolher_opcao(self, indice):
        decisao = self.decisao_atual
        antes = dict(self.tecnico)
        sd.aplicar_efeito(self.tecnico, decisao, indice)
        self.decisoes_tomadas.append((decisao["id"], indice, dict(self.tecnico)))
        variacao = {m: self.tecnico[m] - antes[m] for m in sd.MEDIDORES}
        self.ultima_escolha = (decisao["opcoes"][indice]["texto"], variacao)
        self.ir_para("feedback")

    # ------------------------------------------------------------------ RESULTADO DA DECISÃO
    def montar_feedback(self):
        self.botoes = [Botao((490, 610, 300, 70), "Continuar", ("apos_feedback",),
                             destaque=True)]

    def desenhar_feedback(self):
        texto, variacao = self.ultima_escolha
        self.titulo_tela("Sua decisão")
        desenhar_paragrafo(self.tela, f"Você escolheu: {texto}", self.fonte_h2,
                           constantes.BRANCO, (140, 110), 1000, espacamento=8)
        y = 260
        for medidor in sd.MEDIDORES:
            delta = variacao[medidor]
            cor = (constantes.VERDE if delta > 0 else
                   constantes.VERMELHO if delta < 0 else constantes.CINZA)
            desenhar_texto(self.tela, f"{ROTULOS[medidor]}: {delta:+d}", self.fonte_h2, cor,
                           (self.cx, y), centralizado=True)
            y += 55
        desenhar_texto(self.tela, "Medidores agora", self.fonte, constantes.CINZA,
                       (self.cx, 450), centralizado=True)
        self.desenhar_medidores(495)

    def acao_apos_feedback(self):
        self.proxima_decisao()

    # ------------------------------------------------------------------ RESULTADO DA RODADA
    def montar_resultado(self):
        self.botoes = [Botao((490, 620, 300, 70), "Classificação", ("classificacao",),
                             destaque=True)]

    def desenhar_resultado(self):
        self.titulo_tela(f"Resultados da rodada {self.rodada}")
        for i, (mandante, visitante, gm, gv, _, _, _) in enumerate(self.resultados):
            y = 110 + i * 70
            if self.time_usuario in (mandante, visitante):
                pygame.draw.rect(self.tela, constantes.DESTAQUE, (300, y - 6, 680, 64),
                                 border_radius=10)
            desenhar_texto(self.tela, mandante, self.fonte, constantes.BRANCO, (510, y + 12),
                           direita=True)
            desenhar_escudo(self.tela, self.time_por_nome(mandante), (560, y + 25), 52)
            desenhar_texto(self.tela, f"{gm}  x  {gv}", self.fonte_h2, constantes.BRANCO,
                           (self.cx, y + 6), centralizado=True)
            desenhar_escudo(self.tela, self.time_por_nome(visitante), (720, y + 25), 52)
            desenhar_texto(self.tela, visitante, self.fonte, constantes.BRANCO, (770, y + 12))

        jogo = torneio.jogo_do_usuario(self.jogos, self.time_usuario)
        if jogo is None:
            texto, cor = "Seu time folgou nesta rodada.", constantes.CINZA
        else:
            _, _, gm, gv, *_ = next(r for r in self.resultados
                                    if self.time_usuario in r[:2])
            meus, deles = (gm, gv) if jogo[0] == self.time_usuario else (gv, gm)
            if meus > deles:
                texto, cor = "Vitória! +3 pontos", constantes.VERDE
            elif meus == deles:
                texto, cor = "Empate. +1 ponto", constantes.AMARELO
            else:
                texto, cor = "Derrota. +0 pontos", constantes.VERMELHO
        desenhar_texto(self.tela, texto, self.fonte_h2, cor, (self.cx, 540), centralizado=True)

    def acao_classificacao(self):
        self.ir_para("classificacao")

    # ------------------------------------------------------------------ CLASSIFICAÇÃO
    def montar_classificacao(self):
        self.tabela = self.tabela_classificacao()
        terminou = self.dados_torneio["rodada_atual"] > self.total_rodadas
        self.botoes = [
            Botao((960, 650, 280, 60), "Resultado final" if terminou else "Próxima rodada",
                  ("fim",) if terminou else ("proxima_rodada",), destaque=True),
            Botao((660, 650, 280, 60), "Histórico", ("historico",)),
            Botao((40, 650, 200, 60), "Menu", ("menu",)),
        ]

    def desenhar_classificacao(self):
        self.titulo_tela("Classificação")
        colunas = [("P", 600), ("J", 670), ("V", 740), ("E", 810), ("D", 880),
                   ("GP", 960), ("GC", 1040), ("SG", 1120)]
        desenhar_texto(self.tela, "Time", self.fonte_pequena, constantes.CINZA, (210, 100))
        for rotulo, x in colunas:
            desenhar_texto(self.tela, rotulo, self.fonte_pequena, constantes.CINZA, (x, 100),
                           direita=True)
        for i, linha in enumerate(self.tabela):
            y = 135 + i * 46
            if linha["time"] == self.time_usuario:
                pygame.draw.rect(self.tela, constantes.DESTAQUE, (100, y - 6, 1080, 42),
                                 border_radius=8)
            valores = [linha["pontos"], linha["jogos"], linha["vitorias"], linha["empates"],
                       linha["derrotas"], linha["gols_pro"], linha["gols_contra"],
                       linha["gols_pro"] - linha["gols_contra"]]
            desenhar_texto(self.tela, f"{i + 1}", self.fonte, constantes.BRANCO, (120, y + 2))
            desenhar_escudo(self.tela, self.time_por_nome(linha["time"]), (178, y + 14), 32)
            desenhar_texto(self.tela, linha["time"], self.fonte, constantes.BRANCO, (210, y + 2))
            for (rotulo, x), valor in zip(colunas, valores):
                cor = constantes.BRANCO if rotulo != "P" else constantes.AMARELO
                desenhar_texto(self.tela, str(valor), self.fonte, cor, (x, y + 2), direita=True)

    def acao_proxima_rodada(self):
        self.iniciar_rodada()

    def acao_fim(self):
        self.ir_para("fim")

    # ------------------------------------------------------------------ HISTÓRICO
    def montar_historico(self):
        self.botoes = [Botao((40, 670, 200, 50), "Voltar", ("classificacao",))]

    def desenhar_historico(self):
        self.titulo_tela("Histórico do seu técnico")
        meus_jogos = [p for p in banco.historico_partidas(self.conn, self.tid)
                      if self.time_usuario in (p["mandante"], p["visitante"])]
        por_id = {d["id"]: d for d in self.decisoes}

        desenhar_texto(self.tela, "Seus jogos", self.fonte, constantes.AMARELO, (60, 95))
        y = 135
        for p in meus_jogos:
            linha = (f"R{p['rodada']}: {p['mandante']} {p['gols_mandante']} x "
                     f"{p['gols_visitante']} {p['visitante']}")
            desenhar_texto(self.tela, linha, self.fonte_pequena, constantes.BRANCO, (60, y))
            if p["forca_casa"] is not None:
                detalhe = (f"Força {p['forca_casa']} x {p['forca_fora']}  |  "
                           f"Acertos: {p['acertos']}")
                desenhar_texto(self.tela, detalhe, self.fonte_pequena, constantes.CINZA,
                               (60, y + 22))
                y += 50
            else:
                y += 30
        if not meus_jogos:
            desenhar_texto(self.tela, "Nenhum jogo disputado ainda.", self.fonte_pequena,
                           constantes.CINZA, (60, y))

        desenhar_texto(self.tela, "Suas decisões", self.fonte, constantes.AMARELO, (560, 95))
        y = 135
        decisoes_feitas = banco.historico_decisoes(self.conn, self.tid)
        for d in decisoes_feitas:
            texto = por_id[d["decisao_id"]]["opcoes"][d["indice_escolha"]]["texto"]
            y = desenhar_paragrafo(self.tela, f"R{d['rodada']}: {texto}", self.fonte_pequena,
                                   constantes.BRANCO, (560, y), 680, espacamento=2) + 6
        if not decisoes_feitas:
            desenhar_texto(self.tela, "Nenhuma decisão tomada ainda.", self.fonte_pequena,
                           constantes.CINZA, (560, y))
        self.desenhar_medidores(600)

    def acao_historico(self):
        self.ir_para("historico")

    # ------------------------------------------------------------------ FIM DO TORNEIO
    def montar_fim(self):
        self.tabela = self.tabela_classificacao()
        self.botoes = [
            Botao((330, 620, 280, 70), "Ver classificação", ("classificacao",)),
            Botao((670, 620, 280, 70), "Menu principal", ("menu",), destaque=True),
        ]

    def desenhar_fim(self):
        self.titulo_tela("Fim do torneio")
        campeao = self.tabela[0]
        desenhar_escudo(self.tela, self.time_por_nome(campeao["time"]), (self.cx, 190), 150)
        desenhar_texto(self.tela, f"Campeão: {campeao['time']}", self.fonte_titulo,
                       constantes.AMARELO, (self.cx, 290), centralizado=True)
        desenhar_texto(self.tela, f"{campeao['pontos']} pontos", self.fonte_h2,
                       constantes.BRANCO, (self.cx, 355), centralizado=True)

        posicao = next(i for i, l in enumerate(self.tabela, 1) if l["time"] == self.time_usuario)
        minha = self.tabela[posicao - 1]
        if posicao == 1:
            texto, cor = "Parabéns, técnico! Você é campeão!", constantes.VERDE
        else:
            texto, cor = (f"{self.time_usuario} terminou em {posicao}º lugar "
                          f"com {minha['pontos']} pontos."), constantes.BRANCO
        desenhar_texto(self.tela, texto, self.fonte_h2, cor, (self.cx, 440), centralizado=True)
        desenhar_texto(self.tela, "Medidores finais", self.fonte, constantes.CINZA,
                       (self.cx, 500), centralizado=True)
        self.desenhar_medidores(540)


if __name__ == "__main__":
    Game().rodar()
    sys.exit()
