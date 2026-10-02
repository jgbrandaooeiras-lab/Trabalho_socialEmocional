from src.systems.sistema_decisao import carregar_decisoes, aplicar_efeito

tecnico = {"relacionamento": 50, "estabilidade": 50, "reputacao": 50}
decisoes = carregar_decisoes()

aplicar_efeito(tecnico, decisoes[0], 0)
assert tecnico["relacionamento"] == 60

# limites: nunca passa de 100 nem fica abaixo de 0
tecnico = {"relacionamento": 95, "estabilidade": 50, "reputacao": 50}
aplicar_efeito(tecnico, decisoes[0], 0)
assert tecnico["relacionamento"] == 100

print("TESTE PASSOU")