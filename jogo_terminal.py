"""Versão de terminal do jogo: usa exatamente a mesma lógica e o mesmo banco do pygame.

Útil para testar regras e saves sem abrir janela:  python jogo_terminal.py
"""
import constantes
import torneio
from times import forcas_dos_times, nomes_dos_times
from src.systems import banco_dados as banco
from src.systems import sistema_decisao as sd

ROTULOS = {"relacionamento": "Relacionamento", "estabilidade": "Estabilidade",
           "reputacao": "Reputação"}


def ler_inteiro(mensagem, minimo, maximo):
    while True:
        texto = input(mensagem).strip()
        if texto.isdigit() and minimo <= int(texto) <= maximo:
            return int(texto)
        print(f"Digite um número entre {minimo} e {maximo}.")


def mostrar_medidores(tecnico):
    print("Medidores: " + " | ".join(f"{ROTULOS[m]} {tecnico[m]}" for m in sd.MEDIDORES))


def mostrar_classificacao(conn, tid, time_usuario):
    print(f"\n{'#':>2} {'Time':<14}{'P':>3}{'J':>3}{'V':>3}{'E':>3}{'D':>3}{'SG':>4}")
    for i, l in enumerate(banco.classificacao(conn, tid), 1):
        marca = "<- você" if l["time"] == time_usuario else ""
        saldo = l["gols_pro"] - l["gols_contra"]
        print(f"{i:>2} {l['time']:<14}{l['pontos']:>3}{l['jogos']:>3}{l['vitorias']:>3}"
              f"{l['empates']:>3}{l['derrotas']:>3}{saldo:>4} {marca}")


def novo_torneio_terminal(conn):
    nomes = nomes_dos_times()
    print("\nEscolha seu time:")
    for i, nome in enumerate(nomes, 1):
        print(f"  {i}) {nome}")
    time = nomes[ler_inteiro("Time: ", 1, len(nomes)) - 1]
    return banco.novo_torneio(conn, f"{time} (terminal)", time, dict(constantes.TECNICO_INICIAL))


def escolher_torneio(conn):
    torneios = banco.listar_torneios(conn)
    if not torneios:
        print("\nNenhum torneio salvo.")
        return None
    print("\nTorneios salvos:")
    for i, t in enumerate(torneios, 1):
        print(f"  {i}) {t['nome']} - rodada {t['rodada_atual']} - {t['status']}")
    return torneios[ler_inteiro("Torneio: ", 1, len(torneios)) - 1]["id"]


def voltar_save(conn, tid):
    dados, _ = banco.carregar_torneio(conn, tid)
    anteriores = [c for c in banco.listar_checkpoints(conn, tid) if c["rodada"] < dados["rodada_atual"]]
    if not anteriores:
        print("\nNão há rodada anterior para voltar.")
        return False
    print("\nVoltar para o início de qual rodada?")
    for c in anteriores:
        print(f"  {c['rodada']}) medidores {c['relacionamento']}/{c['estabilidade']}/{c['reputacao']}")
    rodada = ler_inteiro("Rodada: ", anteriores[0]["rodada"], anteriores[-1]["rodada"])
    if input("Isso apaga o progresso posterior. Confirma? (s/n) ").strip().lower() != "s":
        return False
    banco.voltar_checkpoint(conn, tid, rodada)
    return True


def jogar(conn, tid, decisoes, calendario, forcas):
    dados, tecnico = banco.carregar_torneio(conn, tid)
    time_usuario = dados["time_usuario"]
    total = len(calendario)

    for rodada in range(dados["rodada_atual"], total + 1):
        jogos = calendario[rodada - 1]
        print(f"\n=== Rodada {rodada}/{total} ({time_usuario}) ===")
        mostrar_medidores(tecnico)

        tomadas = []
        numero = torneio.numero_do_jogo_do_usuario(calendario, rodada, time_usuario)
        for decisao in (sd.buscar_decisoes(decisoes, numero) if numero else []):
            print(f"\n{decisao['texto']}")
            for i, opcao in enumerate(decisao["opcoes"], 1):
                print(f"  {i}) {opcao['texto']}")
            indice = ler_inteiro("Sua escolha: ", 1, len(decisao["opcoes"])) - 1
            sd.aplicar_efeito(tecnico, decisao, indice)
            tomadas.append((decisao["id"], indice, dict(tecnico)))
            mostrar_medidores(tecnico)

        resultados = torneio.simular_rodada(jogos, forcas, time_usuario, tecnico)
        banco.fechar_rodada(conn, tid, rodada, resultados, tomadas, tecnico,
                            finalizado=(rodada == total))
        print("\nResultados:")
        for mandante, visitante, gm, gv in resultados:
            print(f"  {mandante} {gm} x {gv} {visitante}")
        mostrar_classificacao(conn, tid, time_usuario)

        if rodada < total:
            if input("\nEnter para a próxima rodada (ou 's' para sair): ").strip().lower() == "s":
                return
    campeao = banco.classificacao(conn, tid)[0]
    print(f"\nFim do torneio! Campeão: {campeao['time']} com {campeao['pontos']} pontos.")


def main():
    conn = banco.conectar()
    decisoes = sd.carregar_decisoes()
    calendario = torneio.gerar_calendario(nomes_dos_times())
    forcas = forcas_dos_times()

    while True:
        print("\n=== Simulador de Técnico (terminal) ===")
        print("1) Novo torneio\n2) Continuar torneio\n3) Voltar a um save\n0) Sair")
        opcao = ler_inteiro("Opção: ", 0, 3)
        if opcao == 0:
            break
        if opcao == 1:
            jogar(conn, novo_torneio_terminal(conn), decisoes, calendario, forcas)
        else:
            tid = escolher_torneio(conn)
            if tid is None:
                continue
            if opcao == 3 and not voltar_save(conn, tid):
                continue
            jogar(conn, tid, decisoes, calendario, forcas)
    conn.close()


if __name__ == "__main__":
    main()
