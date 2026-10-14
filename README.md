# ⚽ Simulador de Técnico de Futebol

Jogo em Python + pygame em que o jogador assume o papel de técnico de um time em um campeonato de pontos corridos. A cada rodada surgem situações de bastidores — vestiário, imprensa, diretoria, torcida e ambiente de competição — e as decisões tomadas alteram os medidores do técnico, que influenciam diretamente a força do time nas partidas.

O projeto combina gestão, simulação esportiva, persistência em banco SQLite e uma interface gráfica em pygame. A vitória depende de boas escolhas, mais do que de sorte.

## ✅ Novas funcionalidades implementadas

- Sistema de torneio completo em pontos corridos
- Calendário gerado automaticamente com todos contra todos
- Simulação de partidas com força base, variação aleatória e bônus do técnico
- Medidores de desempenho com limites entre 0 e 100
- Decisões condicionais por contexto de rodada e situação do time
- Fluxos de telas dinâmicos por partida
- Histórico de partidas e decisões salvas em banco de dados
- Múltiplos saves simultâneos com retomada do progresso
- Checkpoints por rodada para voltar em um save anterior
- Classificação calculada no próprio jogo
- Modo de terminal para testes sem abrir a janela do pygame
- Menu com seleção de time, carregamento de save e tela de configurações
- Música em loop com controle de volume e ações de voltar ao menu/sair
- Testes automatizados cobrindo decisões, regras novas e persistência

## 🎮 Como o jogo funciona

### Torneio e calendário

- O campeonato é montado com todos os times jogando entre si em turno único.
- Cada rodada contém uma lista de jogos.
- O usuário controla apenas um time, enquanto os demais são simulados pelo sistema.
- O torneio termina quando todas as rodadas forem disputadas.
- Vitória vale 3 pontos, empate 1 e derrota 0.
- Critérios de desempate: saldo de gols e gols marcados.

### Medidores do técnico

Cada escolha do técnico altera três medidores:

- Relacionamento: clima com elenco e torcida
- Estabilidade: segurança no cargo
- Reputação: imagem perante imprensa e diretoria

Os medidores ficam entre 0 e 100 e impactam a força do time. Também são usados para validar a saúde do técnico durante o torneio.

### Regras de decisão

- Cada partida pode ter uma ou mais decisões.
- O arquivo de decisões define o fluxo de telas, textos, opções e efeitos.
- A escolha do jogador pode ser assertiva ou não, conforme o campo `assertiva` da opção.
- Decisões podem depender de condições do momento, como:
  - número de derrotas
  - posição na tabela
  - status da rodada
  - resultado anterior do time
- O sistema aceita `condicao` e também o fluxo alternativo `senao`.

### Simulação de força e resultado

- A força de cada time varia em torno da base do clube em até ±15 pontos.
- O técnico adiciona um bônus ou penalidade com base na média dos medidores.
- Decisões assertivas aumentam a força do time naquela partida em 8 pontos por acerto, até o limite máximo.
- Quando a média dos medidores cai demais, ou a sequência de decisões assertivas não é suficiente, o time pode entrar em situação crítica.

## 💾 Salvamento com SQLite

O progresso é salvo em um banco SQLite em `data/jogo.db`, criado automaticamente. Isso permite:

- Retomar um torneio já iniciado
- Ver histórico de partidas
- Consultar decisões tomadas
- Salvar vários torneios ao mesmo tempo
- Voltar para um checkpoint anterior de rodada
- Continuar do ponto exato em que o jogo foi interrompido

### Estrutura das tabelas

| Tabela | Conteúdo |
| --- | --- |
| `torneios` | Save principal do torneio: time do usuário, rodada atual, medidores e status |
| `partidas` | Resultados de cada partida, incluindo gols, força utilizada e acertos |
| `decisoes` | Decisões tomadas pelo usuário e os efeitos aplicados |
| `checkpoints` | Instante do fim de cada rodada para permitir voltar no save |

A rodada é gravada de uma vez ao fim do processamento. Se o jogo for fechado no meio da rodada, o sistema evita deixar dados incompletos.

## 🧩 Arquitetura do projeto

```text
├── main.py                    # tela principal e fluxo do jogo em pygame
├── maingame.py                # módulo de fluxo e lógica do jogo
├── jogo_terminal.py           # versão textual do campeonato
├── tela.py                    # interface gráfica principal
├── constantes.py              # ajustes gerais, cores, dimensões e caminhos
├── times.py                   # dados dos times e configurações da liga
├── torneio.py                 # calendário, simulação e lógica do torneio
├── data/
│   ├── decisoes.json          # regras das decisões e opções do jogo
│   └── jogo.db               # banco SQLite gerado automaticamente
├── audio/
│   └── audiojogo.mpeg         # música de fundo do jogo
├── imagens/
│   ├── coletiva.jfif
│   ├── jogadorbarato.piskel
│   ├── sem_fundo/
│   ├── técnico.piskel
│   └── vorcaro.jfif
├── src/
│   ├── __init__.py
│   ├── core/
│   ├── entities/
│   ├── ui/
│   └── systems/
│       ├── __init__.py
│       ├── banco_dados.py     # persistência com SQLite
│       ├── bandoDados.py      # alternativa/arquivo auxiliar de banco
│       ├── sistema_decisao.py # leitura, condição e aplicabilidade das decisões
│       └── copytxt
├── tests/
│   ├── teste_decisoes.py
│   ├── teste_novas_regras.py
│   └── ...
├── README.md
├── para_agente.txt
├── remover_fundo.py
├── desfazer_projeto.py
├── logo rated.piskel
├── campo de futebol.piskel
├── técnico.piskel
├── jogadorbarato.piskel
└── ...
```

## 🧠 Formato das decisões

O arquivo `data/decisoes.json` organiza cada evento em um objeto com estrutura similar a esta:

```json
{
  "id": "d01",
  "id_partida": 1,
  "texto": "Seu time perdeu a estreia e o clima no vestiário está pesado",
  "fluxo": ["anuncio", "decisao", "resultado", "tabela"],
  "condicao": {"derrotas_acima_de": 2},
  "opcoes": [
    {
      "texto": "Reunir elenco e assumir parte da culpa",
      "assertiva": true,
      "efeitos": {
        "relacionamento": 10,
        "estabilidade": 5,
        "reputacao": 0
      }
    },
    {
      "texto": "Cobrar mais dos atletas na coletiva",
      "assertiva": false,
      "efeitos": {
        "relacionamento": -8,
        "estabilidade": 4,
        "reputacao": 3
      }
    }
  ]
}
```

### Observações importantes

- `id_partida` representa a partida do time do usuário, e não a rodada do campeonato.
- `condicao` permite decidir entre alternativas conforme a situação atual do clube.
- `assertiva` marca uma opção como decision point que aumenta a força do time.
- O campo `fluxo` controla a ordem das telas da rodada.

## 🛠️ Tecnologias utilizadas

- Python
- pygame
- SQLite
- JSON para dados de decisão e configuração

## ▶️ Como executar

```bash
# 1. clone o repositório
git clone <url-do-repositorio>
cd <pasta-do-projeto>

# 2. (opcional) crie um ambiente virtual
python -m venv venv
venv\Scripts\activate       # Windows
# source venv/bin/activate  # Linux/macOS

# 3. instale as dependências
pip install pygame

# 4. execute a versão gráfica
python main.py
```

Também existe uma versão textual do jogo, útil para testar regras e lógica sem abrir a janela:

```bash
python jogo_terminal.py
```

## 🧪 Testes

Execute a partir da raiz do projeto:

```bash
python -c "import runpy; runpy.run_path('tests/teste_decisoes.py', run_name='__main__')"
python -c "import runpy; runpy.run_path('tests/teste_novas_regras.py', run_name='__main__')"
```

Os testes usam banco em memória e não alteram o banco real do jogo (`data/jogo.db`).

## 📌 Roadmap e status

- [x] Sistema de decisões com medidores limitados entre 0 e 100
- [x] Persistência com SQLite e saves múltiplos
- [x] Checkpoints e retorno de rodada
- [x] Calendário de todos contra todos
- [x] Simulação de partidas com força, bônus e ranqueamento
- [x] Interface em pygame com menu, decisão, resultado e classificação
- [x] Sistema de histórico e classificação
- [x] Música, volume e opções de menu
- [x] Condições em decisões e fluxo dinâmico
- [x] Testes automatizados de regras e banco
- [ ] Evolução de assets e artes finais
- [ ] Novos modos e expansões de conteúdo
- [ ] Ajustes visuais e refinamento da UI

## 👥 Autores

Equipe responsável pelo desenvolvimento do projeto.

## 📄 Licença

A licença ainda não foi definida para este repositório. Defina uma licença antes de distribuir o projeto publicamente.
