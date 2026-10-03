# ⚽ Simulador de Técnico de Futebol

Jogo em **Python + pygame** em que você assume o comando de um time em um torneio de pontos corridos. A cada partida surgem situações de bastidores (vestiário, imprensa, diretoria, torcida) e suas decisões afetam os medidores do técnico, que por sua vez influenciam o desempenho do time na simulação. Vence o torneio quem somar mais pontos.

> 🚧 **Status: em desenvolvimento.** A lógica de decisões e a camada de persistência (SQLite) já existem; calendário, simulação e telas estão em construção. Veja o [Roadmap](#roadmap).

## Como funciona

- O torneio tem cerca de 9 times, e cada um enfrenta todos os outros.
- Antes de algumas partidas, o técnico precisa tomar uma decisão com 2 ou 3 opções.
- Cada opção altera três medidores (de 0 a 100):
  - **Relacionamento**: clima com elenco e torcida
  - **Estabilidade**: segurança no cargo
  - **Reputação**: imagem perante imprensa e diretoria
- Decisões assertivas elevam os medidores e aumentam as chances de vitória do seu time.
- Vitória vale 3 pontos, empate 1 e derrota 0.

## Salvamento com SQLite

O progresso é guardado em um banco SQLite (`data/jogo.db`), o que permite:

- **Ver o histórico** de partidas e de decisões tomadas
- **Retomar** um torneio já iniciado
- **Voltar a um save anterior** (checkpoint ao fim de cada rodada)
- Consultar a **classificação** calculada direto das partidas

| Tabela        | Conteúdo                                                        |
|---------------|-----------------------------------------------------------------|
| `torneios`    | Um save por linha: time do usuário, rodada atual, medidores     |
| `partidas`    | Todas as partidas simuladas (mandante, visitante, gols)         |
| `decisoes`    | Decisões tomadas e medidores resultantes                        |
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

## Testes

Execute a partir da **raiz** do projeto:

```bash
python -m tests.teste_decisoes
```

## Estrutura do projeto

```
├── main.py                  # janela e laço principal do pygame
├── constantes.py            # tamanho da tela, FPS, cores e caminhos
├── times.py                 # dados dos times (nome, escudo, força)
├── data/
│   └── decisoes.json        # decisões do técnico por partida
├── src/
│   └── systems/
│       ├── sistema_decisao.py   # carrega decisões e aplica efeitos nos medidores
│       └── banco_dados.py       # persistência com SQLite
└── tests/
    └── teste_decisoes.py
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
      "efeitos": {"relacionamento": 10, "estabilidade": 5, "reputacao": 0}
    }
  ]
}
```

Para adicionar uma decisão, basta incluir um novo objeto no arquivo, informando em qual partida ela deve aparecer (`id_partida`).

## Roadmap

- [x] Sistema de decisões com medidores limitados entre 0 e 100
- [x] Camada de persistência em SQLite (histórico, retomar e voltar save)
- [ ] Cadastro dos times e escudos
- [ ] Calendário todos contra todos
- [ ] Simulação de partidas influenciada pelos medidores
- [ ] Telas do pygame (menu, decisão, resultado, classificação)
- [ ] Integração do jogo com o salvamento
- [ ] Testes do calendário e do banco de dados

## Autores

- _Adicione aqui os nomes dos integrantes da equipe_

## Licença

_Defina a licença do projeto (por exemplo, MIT) ou remova esta seção._
