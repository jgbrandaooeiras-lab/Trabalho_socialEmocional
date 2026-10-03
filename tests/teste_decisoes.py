from systems.banco_dados import conectar, novo_torneio, carregar_checkpoint
from src.systems.sistema_decisao import carregar_decisoes, aplicar_efeito

tecnico = {"relacionamento": 50, "estabilidade": 50, "reputacao": 50}
decisoes = carregar_decisoes()

aplicar_efeito(tecnico, decisoes[0], 0)
assert tecnico["relacionamento"] == 60

# limites: nunca passa de 100 nem fica abaixo de 0
tecnico = {"relacionamento": 95, "estabilidade": 50, "reputacao": 50}
aplicar_efeito(tecnico, decisoes[0], 0)
assert tecnico["relacionamento"] == 100


def test_novo_torneio_cria_checkpoint(tmp_path):
    conn = conectar(str(tmp_path / "save.db"))
    tecnico = {"relacionamento": 42, "estabilidade": 55, "reputacao": 60}

    torneio_id = novo_torneio(conn, "Teste", "Flamengo", tecnico)
    checkpoint = carregar_checkpoint(conn, torneio_id, 1)

    assert checkpoint == tecnico

print("TESTE PASSOU")