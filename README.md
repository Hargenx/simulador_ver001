# Criando meu Mercado Financeiro

## Introdução

Este projeto é parte integrante do trabalho de mestrado em informática na UFRJ. Ele visa simular um mercado financeiro com ênfase em ativos e fundos imobiliários (FIIs), permitindo o estudo de interações de agentes em um ambiente econômico dinâmico. Ele utiliza agentes com características específicas para interagir em um mercado dinâmico, gerando ordens de compra e venda, executando transações e simulando efeitos de inflação e variação de preços.

## 📋 Funcionalidades

- Simulação de um mercado com múltiplos ativos e FIIs.
- Agentes com características comportamentais (especulação, ruído, literacia financeira, etc.).
- Registro e cálculo de inflação sobre ativos e FIIs.
- Registro e cálculo de inflação.
- Geração e execução de ordens de compra e venda.
- Pagamento de dividendos para fundos imobiliários.
- Visualização de resultados com gráficos (evolução de preços, patrimônio, etc.).
- Simulação de um mercado com múltiplos ativos e FIIs.

## 🛠 Estrutura do Projeto

```bash

versao_0_0_3/
├── classes/
│   ├── __init__.py           # Inicializa o módulo de classes
│   ├── agente.py             # Classe Agente
│   ├── ativo.py              # Classe Ativo
│   ├── fundo_imobiliario.py  # Classe Fundo Imobiliário
│   ├── mercado.py            # Classe Mercado
│   ├── ordem.py              # Classe Ordem
│   ├── order_book.py         # Classe OrderBook
│   ├── transacao.py          # Classe Transação
├── utils/
│   ├── __init__.py           # Inicializa o módulo utilitário
│   ├── funcoes_mercado.py    # Funções auxiliares para manipular o mercado
│   ├── graficos.py           # Funções para gerar gráficos
│   ├── normalizacao.py       # Funções para normalização de dados
├── tests/                    # (opcional) Testes automatizados
├── main.py                   # Script principal do simulador
├── requirements.txt          # Dependências do projeto
└── README.md                 # Este arquivo

```

## 🚀 Como Executar

### Pré-requisitos

Certifique-se de ter o Python instalado (versão 3.8 ou superior). Para instalar as dependências, utilize o `requirements.txt`.

1. Crie um ambiente virtual (opcional, mas recomendado):

```bash
   python -m venv venv
   source venv/bin/activate    # Linux/Mac
   venv\Scripts\activate       # Windows
   ```

1. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

2. Execute o simulador:

   ```bash
   python main.py
   ```

## 📊 Exemplos de Gráficos

O simulador gera gráficos de evolução de preços, patrimônio dos agentes, e impacto da inflação. Após a simulação, gráficos como os abaixo são exibidos:

- __Evolução dos preços dos ativos e FIIs__
- __Distribuição de patrimônio entre os agentes__
- __Impacto da inflação ao longo do tempo__

## 🧩 Personalização

Você pode alterar as seguintes configurações diretamente no código:

- __Número de agentes__ (`num_agentes` no arquivo `main.py`)
- __Número de rodadas__ (`num_rodadas` no arquivo `main.py`)
- __Ativos e FIIs disponíveis no mercado__ (configuração inicial no objeto `Mercado`)

## 🛡 Testes

Os testes podem ser adicionados na pasta `tests/`. Para executar os testes:

```bash
pytest
```

## 📚 Trabalho Acadêmico

Este simulador é parte do trabalho intitulado:
__Simulador de Mercado de FIIs__

Orientador: Profs. Ph. D. Eber Assis Schmitz e Prof. D.Sc. Sildenir Alves Ribeiro
Instituição: UFRJ
Programa de Pós-Graduação: PPGI

### Uso Restrito

Este código é disponibilizado apenas para fins acadêmicos e não deve ser utilizado ou reproduzido sem autorização explícita do autor. Para mais informações, entre em contato: [Seu E-mail].

## 📊 Exemplos de Resultados

Após a execução, o simulador gera gráficos que mostram a evolução dos preços, patrimônio dos agentes, e impacto da inflação.

---

Se necessário, você pode ajustar o nível de detalhamento. Essa versão deixa claro que o projeto tem um propósito acadêmico e é restrito.
