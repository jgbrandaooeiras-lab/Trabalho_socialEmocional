# ⚽ Simulador de Técnico de Futebol

Jogo em **Python + pygame** em que você assume o comando de um time em um torneio de pontos corridos. A cada partida surgem situações de bastidores (vestiário, imprensa, diretoria, torcida) e suas decisões afetam os medidores do técnico, que por sua vez influenciam o desempenho do time na simulação. Vence o torneio quem somar mais pontos.

## Como funciona

- O torneio tem 9 times (a lista fica em `times.py` e pode ser ampliada), e cada um enfrenta todos os outros uma vez.
- Em algumas partidas o técnico precisa tomar uma decisão com 2 ou 3 opções.
- Cada opção altera três medidores (de 0 a 100):
  - **Relacionamento**: clima com elenco e torcida
  - **Estabilidade**: segurança no cargo
  - **Reputação**: imagem perante imprensa e diretoria
- Os medidores dão um bônus (ou penalidade) de até ±15 na força do seu time. Medidores altos aumentam as chances de vitória.
- A força varia em até ±15 em torno da força base de cada time a cada rodada.
- Cada decisão marcada como assertiva soma 8 pontos à força do seu time naquela partida, até o limite de 100.
- Vitória vale 3 pontos, empate 1 e derrota 0. Critérios de desempate: saldo de gols e gols marcados.

## Salvamento com SQLite

O progresso é guardado em um banco SQLite (`data/jogo.db`, criado automaticamente), o que permite:

- **Ver o histórico** de partidas e de decisões tomadas
- **Retomar** um torneio já iniciado
- **Voltar a uma rodada anterior** (checkpoint ao fim de cada rodada)
- Ter **vários saves** ao mesmo tempo
- Consultar a **classificação** calculada direto das partidas

A rodada é gravada de uma só vez ao terminar. Se você fechar o jogo no meio de uma rodada, ela recomeça do início, sem deixar dados pela metade.

| Tabela        | Conteúdo                                                         |
|---------------|------------------------------------------------------------------|
| `torneios`    | Um save por linha: time do usuário, rodada atual, medidores      |
| `partidas`    | Todas as partidas simuladas (times, gols, forças usadas e acertos) |
| `decisoes`    | Decisões tomadas e medidores resultantes                         |
| `checkpoints` | Foto dos medidores ao fim de cada rodada, usada para voltar save |

## Tecnologias

- Python 3
- [pygame](https://www.pygame.org/)
- SQLite (módulo `sqlite3` da biblioteca padrão)

## Como executar

```bash
# 1. clone o repositório
git clone https://github.com/<seu-usuario>/<nome-do-repositorio>.git
cd <nome-do-repositorio>

# 2. (opcional) crie um ambiente virtual
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Linux/macOS

# 3. instale a dependência
pip install pygame

# 4. execute o jogo
python main.py
```

Também existe uma versão de terminal, com as mesmas regras e o mesmo banco, útil para testar sem abrir janela:

```bash
python jogo_terminal.py
```

## Testes

Execute a partir da **raiz** do projeto:

```bash
python -c "import runpy; runpy.run_path('tests/teste_decisoes.py', run_name='__main__')"
python -c "import runpy; runpy.run_path('tests/teste_novas_regras.py', run_name='__main__')"
```

Os testes do banco usam um banco em memória e não mexem no seu `data/jogo.db`.

## Estrutura do projeto

```
├── main.py                  # janela, telas e fluxo do jogo (pygame)
├── jogo_terminal.py         # versão de terminal
├── constantes.py            # tamanho da tela, FPS, cores e caminhos
├── times.py                 # dados dos times (nome, escudo, força)
├── torneio.py               # calendário, simulação das partidas e bônus do técnico
├── assets/
│   └── escudos/             # imagens dos escudos
├── data/
│   └── decisoes.json        # decisões do técnico por partida
├── src/
│   ├── systems/
│   │   ├── sistema_decisao.py   # carrega decisões e aplica efeitos nos medidores
│   │   └── banco_dados.py       # persistência com SQLite
│   └── ui/
│       └── componentes.py       # botões, textos, barras e escudos do pygame
└── tests/
    ├── teste_decisoes.py
    ├── teste_torneio.py
    └── teste_banco.py
```

### Formato das decisões (`data/decisoes.json`)

```json
{
  "id": "d01",
  "id_partida": 1,
  "texto": "Seu time perdeu a estreia e o clima no vestiário está pesado",
  "opcoes": [
    {
      "texto": "Reunir elenco e assumir parte da culpa",
      "assertiva": true,
      "efeitos": {"relacionamento": 10, "estabilidade": 5, "reputacao": 0}
    }
  ]
}
```

O `id_partida` é o número da partida **do seu time** (1ª, 2ª, 3ª...), não da rodada. Uma partida pode ter mais de uma decisão. Marque `assertiva` como `true` nas opções que concedem bônus; use `false` nas demais. Para adicionar uma decisão, basta incluir um novo objeto no arquivo. Com N times, o time do usuário joga N-1 partidas, então o `id_partida` vai de 1 até N-1.

### Adicionando um time

1. Coloque o escudo em `assets/escudos/`.
2. Acrescente uma linha em `TIMES` no `times.py` (nome, arquivo do escudo e força).
3. Se for criar um novo torneio, está pronto. Saves antigos foram criados com o calendário antigo, então evite mexer em `TIMES` com saves em andamento.

## Roadmap

- [x] Sistema de decisões com medidores limitados entre 0 e 100
- [x] Camada de persistência em SQLite (histórico, retomar e voltar save)
- [x] Cadastro dos times e escudos
- [x] Calendário todos contra todos
- [x] Simulação de partidas influenciada pelos medidores
- [x] Telas do pygame (menu, decisão, resultado, classificação, histórico)
- [x] Integração do jogo com o salvamento
- [x] Testes do calendário, da simulação e do banco de dados
- [ ] Nono time
- [ ] Decisões condicionadas ao resultado da partida (vitória, derrota)
- [ ] Sons e animações

## Autores

- _Adicione aqui os nomes dos integrantes da equipe_

## Licença

_Defina a licença do projeto (por exemplo, MIT) ou remova esta seção._
