import numpy as np
import random
import math
import matplotlib.pyplot as plt

class Agente:
    def __init__(self, id, literacia_financeira, comportamento, caixa, cotas):
        self.id = id
        self.LF = literacia_financeira  # Literacia Financeira
        self.comportamento = (
            comportamento  # Comportamento do agente (ex: "fundamentalista")
        )
        self.caixa = caixa  # Montante financeiro disponível
        self.cotas = cotas  # Quantidade de cotas possuídas

        # Atributos decisórios
        self.sentimento = 0  # Sentimento (S) entre -1 e 1
        self.RD = 0  # Risco Desejado
        self.percentual_alocacao = 0  # Percentual ideal de alocação

        # Expectativas
        self.expectativa_inflacao = 0  # Expectativa individual de inflação
        self.expectativa_premio = 0  # Expectativa individual de prêmio de risco

        # Histórico e estatísticas
        self.historico_precos = []  # Preços observados para calcular estatísticas
        self.retornos_dia = []  # Retornos diários registrados
        self.historico_riqueza = [caixa + cotas * 100]  # Riqueza inicial estimada
        self.dividendos_recebidos = 0  # Total de dividendos recebidos

    def atualizar_caixa(self, taxa_selic, dividendos):
        """
        Atualiza o caixa do agente com base na taxa SELIC e dividendos recebidos.
        """
        self.caixa += self.caixa * taxa_selic  # Incremento pela taxa SELIC
        self.caixa += dividendos  # Incremento por dividendos

    def calcular_sentimento_risco_alocacao(self, mercado, vizinhos, parametros):
        """
        Calcula o Sentimento, Risco Desejado e Percentual de Alocação.
        """
        I_privado = random.uniform(0, 1)  # Simulação de desempenho próprio
        I_social = sum([v.LF for v in vizinhos]) / len(
            vizinhos
        )  # Média dos LF dos vizinhos
        volatilidade_percebida = mercado.volatilidade_historica

        a_i = parametros["a0"] + parametros["alpha"] * self.LF
        b_i = parametros["b0"] - parametros["gamma"] * self.LF
        c_i = parametros["c0"] - parametros["delta"] * self.LF

        S_bruto = a_i * I_privado + b_i * I_social + c_i * mercado.news
        self.sentimento = max(min(S_bruto, 1), -1)
        self.RD = (self.sentimento + 1) / 2 * volatilidade_percebida

        if volatilidade_percebida > 0:
            self.percentual_alocacao = self.RD / volatilidade_percebida
        else:
            self.percentual_alocacao = 0

    def calcular_expectativa_inflacao(self, mercado, noticias):
        """
        Atualiza a expectativa de inflação do agente com base nas notícias e inflação do mercado.
        """
        impacto_news = noticias / 10  # Exemplo: impacto proporcional das notícias
        self.expectativa_inflacao = mercado.expectativa_inflacao + impacto_news

    def calcular_expectativa_premio(self, mercado):
        """
        Atualiza a expectativa de prêmio de risco do agente com base no Sentimento e volatilidade.
        """
        # Verificar se os atributos realmente existem
        assert isinstance(
            mercado.banco_central, BancoCentral
        ), "mercado.banco_central não é uma instância de BancoCentral"
        assert hasattr(
            mercado.banco_central, "premio_risco"
        ), "BancoCentral não tem o atributo 'premio_risco'"

        assert hasattr(
            mercado, "banco_central"
        ), "O objeto Mercado não tem o atributo banco_central"
        assert hasattr(
            mercado.banco_central, "premio_risco"
        ), "O BancoCentral não tem o atributo premio_risco"

        """print(f"Banco Central: {mercado.banco_central}")  # Diagnóstico
        print(f"Prêmio de Risco: {mercado.banco_central.premio_risco}")  # Diagnóstico
        print(f"Volatilidade Histórica: {mercado.volatilidade_historica}")  # Diagnóstico"""

        # Calculando a expectativa de prêmio corretamente
        self.expectativa_premio = mercado.banco_central.premio_risco * (
            1 + self.sentimento * mercado.volatilidade_historica
        )

    def calcular_estatisticas_historicas(self):
        """
        Calcula a média de retornos, volatilidade e Sharpe Ratio com base na janela observada.
        """
        if len(self.historico_precos) < 2:
            return None  # Não há dados suficientes

        retornos = [
            (self.historico_precos[i] - self.historico_precos[i - 1])
            / self.historico_precos[i - 1]
            for i in range(1, len(self.historico_precos))
        ]

        media_retorno = np.mean(retornos)
        volatilidade = np.std(retornos)
        sharpe_ratio = media_retorno / volatilidade if volatilidade > 0 else 0

        return {
            "media_retorno": media_retorno,
            "volatilidade": volatilidade,
            "sharpe_ratio": sharpe_ratio,
        }

    def calcular_preco_esperado(self, mercado, ruido):
        """
        Calcula o preço esperado pelo agente.
        """
        x_i = self.LF / math.exp(1)
        z_i = (1 - self.LF) * (1 - x_i)
        y_i = 1 - x_i - z_i

        preco_fundamentalista = (
            mercado.dividendos * (1 + mercado.expectativa_inflacao)
        ) / mercado.premio_risco
        r_fundamentalista = math.log(preco_fundamentalista / mercado.preco_mercado)
        r_especulador = math.log(mercado.media_precos_semana / mercado.media_precos_mes)

        expectativa_retorno = (
            x_i * r_especulador + y_i * r_fundamentalista + z_i * ruido
        )
        return mercado.preco_mercado * math.exp(expectativa_retorno)

    def calcular_retornos_dia(self, preco_atual):
        """
        Calcula e registra o retorno diário com base no preço atual e no último preço registrado.
        """
        if self.historico_precos:
            preco_anterior = self.historico_precos[-1]
            retorno = (preco_atual - preco_anterior) / preco_anterior
            self.retornos_dia.append(retorno)
        self.historico_precos.append(preco_atual)

    def atualizar_historico(self):
        """
        Atualiza o histórico de riqueza diária.
        """
        riqueza_atual = self.caixa + self.cotas * 100  # Exemplo: preço fixo de cotas
        self.historico_riqueza.append(riqueza_atual)


class FII:
    def __init__(self, num_cotas, caixa):
        self.num_cotas = num_cotas  # Quantidade total de cotas
        self.caixa = caixa  # Recursos financeiros disponíveis
        self.imoveis = []  # Lista de imóveis no portfólio do fundo
        self.retornos_diarios = []  # Histórico dos retornos diários das cotas
        self.preco_cota = 100  # Preço inicial da cota

    def adicionar_imovel(self, imovel):
        """
        Adiciona um imóvel ao portfólio do fundo.
        """
        self.imoveis.append(imovel)

    def calcular_fluxo_aluguel(self):
        """
        Calcula o montante total de aluguéis gerados pelos imóveis.
        """
        return sum(imovel.gerar_fluxo_aluguel() for imovel in self.imoveis)

    def distribuir_dividendos(self):
        """
        Calcula o valor dos dividendos a serem distribuídos por cota com base no fluxo de aluguéis.
        """
        fluxo_aluguel = self.calcular_fluxo_aluguel()
        dividendos = fluxo_aluguel / self.num_cotas if self.num_cotas > 0 else 0
        self.caixa += fluxo_aluguel  # Adiciona ao caixa antes da distribuição
        return dividendos

    def atualizar_caixa_para_despesas(self, despesas):
        """
        Deduz despesas operacionais do caixa.
        """
        self.caixa -= despesas
        if self.caixa < 0:
            self.caixa = 0  # Evitar valores negativos

    def realizar_investimento(self, valor):
        """
        Realiza investimentos, como melhorias nos imóveis, deduzindo do caixa.
        """
        if self.caixa >= valor:
            self.caixa -= valor
        else:
            raise ValueError("Caixa insuficiente para realizar o investimento.")

    def calcular_retorno_diario(self, novo_preco_cota):
        """
        Calcula o retorno diário das cotas com base na valorização/desvalorização do preço.
        """
        if self.preco_cota > 0:
            retorno = (novo_preco_cota - self.preco_cota) / self.preco_cota
            self.retornos_diarios.append(retorno)
        self.preco_cota = novo_preco_cota

    def obter_estatisticas_retornos(self):
        """
        Calcula estatísticas dos retornos diários, como média e volatilidade.
        """
        if not self.retornos_diarios:
            return None

        media_retorno = np.mean(self.retornos_diarios)
        volatilidade = np.std(self.retornos_diarios)

        return {"media_retorno": media_retorno, "volatilidade": volatilidade}


class Mercado:
    def __init__(self, agentes, fii, banco_central, midia):
        self.agentes = agentes  # Lista de agentes
        self.fii = fii  # Instância do FII
        self.banco_central = banco_central  # Banco Central
        self.midia = midia  # Mídia (para notícias diárias)
        self.volatilidade_historica = 0.1  # Inicializa com uma volatilidade padrão
        self.news = 0  # Índice de notícias diário

    def executar_dia(self, parametros):
        """
        Simula um dia de operação no mercado com base no Algoritmo 1.
        """
        # Atualizar o índice de notícias para o dia
        self.news = self.midia.gerar_noticia()

        # Passo 1: Atualizar informações e definir ordens
        for agente in self.agentes:
            agente.calcular_sentimento_risco_alocacao(self, self.agentes, parametros)
            agente.calcular_expectativa_inflacao(self.banco_central, self.news)
            # agente.calcular_expectativa_premio(self.banco_central)
            agente.calcular_expectativa_premio(self)

        # Passo 2: Processar ordens no mercado
        self.processar_ordens()

        # Passo 3: Atualizar histórico de riqueza dos agentes
        for agente in self.agentes:
            agente.atualizar_historico()

        # Passo 4: Atualizar informações do FII
        self.fii.distribuir_dividendos()
        self.fii.atualizar_caixa_para_despesas(2000)  # Exemplo de despesas fixas

        # Atualizar volatilidade histórica com base nos retornos do FII
        self.atualizar_volatilidade_historica()

    def atualizar_volatilidade_historica(self):
        """
        Atualiza a volatilidade histórica com base nos retornos do FII.
        """
        if len(self.fii.retornos_diarios) > 1:
            self.volatilidade_historica = np.std(self.fii.retornos_diarios)

    def processar_ordens(self):
        """
        Processa as ordens dos agentes e ajusta o preço do mercado (simplificado).
        """
        # Simulação simplificada de ajuste de preço com base em sentimento médio
        sentimento_medio = np.mean([agente.sentimento for agente in self.agentes])
        ajuste = sentimento_medio * random.uniform(-0.5, 0.5)
        novo_preco = self.fii.preco_cota + ajuste
        self.fii.calcular_retorno_diario(novo_preco)


class BancoCentral:
    def __init__(self, taxa_selic, expectativa_inflacao, premio_risco):
        self.taxa_selic = taxa_selic  # Taxa SELIC
        self.expectativa_inflacao = expectativa_inflacao  # Expectativa de inflação
        self.premio_risco = premio_risco  # Prêmio de risco


class Midia:
    @staticmethod
    def gerar_noticia():
        """
        Gera um índice de notícia aleatório entre -3 e 3.
        """
        return random.uniform(-3, 3)


class Imovel:
    def __init__(self, valor, aluguel, vacancia, custo_manutencao):
        self.valor = valor  # Valor total do imóvel
        self.aluguel = aluguel  # Valor do aluguel gerado
        self.vacancia = vacancia  # Percentual de vacância
        self.custo_manutencao = custo_manutencao  # Custo de manutenção

    def gerar_fluxo_aluguel(self):
        """
        Calcula o fluxo de aluguel líquido, considerando vacância.
        """
        return self.aluguel * (1 - self.vacancia)


# Simulação do Mercado
# ----- Função de Simulação com Coleta de Dados para o Gráfico -----
def simular_mercado_e_plotar():
    # Criação dos agentes
    agentes = [
        Agente(
            id=i,
            literacia_financeira=random.uniform(0.5, 1.0),
            comportamento="fundamentalista",
            caixa=10000,
            cotas=10,
        )
        for i in range(5)
    ]

    # Criação do FII e adição de imóveis
    fii = FII(num_cotas=1000, caixa=50000)
    fii.adicionar_imovel(
        Imovel(valor=100000, aluguel=5000, vacancia=0.1, custo_manutencao=200)
    )
    fii.adicionar_imovel(
        Imovel(valor=200000, aluguel=8000, vacancia=0.2, custo_manutencao=500)
    )

    # Criação do Banco Central e Mídia
    banco_central = BancoCentral(
        taxa_selic=0.02, expectativa_inflacao=0.03, premio_risco=0.05
    )
    midia = Midia()

    # Criação do Mercado
    mercado = Mercado(
        agentes=agentes, fii=fii, banco_central=banco_central, midia=midia
    )

    # Parâmetros do modelo
    parametros = {
        "a0": 0.5,
        "b0": 0.3,
        "c0": 0.2,
        "alpha": 0.1,
        "gamma": 0.05,
        "delta": 0.02,
    }

    historico_precos_fii = []  # Armazenará o preço da cota do FII ao fim de cada dia

    num_dias = 252  # Simulação de aproximadamente 1 ano de negociação
    for _ in range(num_dias):
        mercado.executar_dia(parametros)
        historico_precos_fii.append(mercado.fii.preco_cota)

    historico_precos_fii = np.array(historico_precos_fii)

    # Cálculo dos retornos logarítmicos diários
    log_returns = np.diff(np.log(historico_precos_fii))

    # Cálculo da volatilidade rolante (janela de 20 dias)
    window = 20
    volatilidade_rolante = np.full_like(log_returns, np.nan)
    for i in range(window, len(log_returns)):
        volatilidade_rolante[i] = np.std(log_returns[i - window : i])

    # Resultados
    print("Preço Final da Cota:", fii.preco_cota)
    print("Caixa Final do FII:", fii.caixa)
    print("Retornos Diários do FII:", fii.retornos_diarios)
    for agente in agentes:
        print(
            f"Agente {agente.id}: Caixa: {agente.caixa}, Sentimento: {agente.sentimento}, Riqueza: {agente.historico_riqueza[-1]}"
        )
        
    # ----- Plotando os Gráficos -----
    dias = np.arange(num_dias)

    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # Gráfico do Preço do FII
    ax[0].plot(dias, historico_precos_fii, label="Preço da Cota do FII")
    ax[0].set_title("Evolução do Preço do FII")
    ax[0].set_ylabel("Preço")
    ax[0].legend()

    # Gráfico da Volatilidade Rolante dos Retornos (logarítmicos)
    # Lembrando que log_returns tem tamanho num_dias-1; por isso, os dias usados começam em 1
    ax[1].plot(
        dias[1:],
        volatilidade_rolante,
        label="Volatilidade Rolante (20 dias)",
        color="orange",
    )
    ax[1].set_title("Volatilidade Rolante dos Retornos Logarítmicos")
    ax[1].set_ylabel("Volatilidade")
    ax[1].set_xlabel("Dias")
    ax[1].legend()

    plt.tight_layout()
    plt.show()

    # Opcional: Retornar os dados para análises adicionais
    return historico_precos_fii, log_returns, volatilidade_rolante


# ----- Executar a Simulação e Plotar os Gráficos -----
simular_mercado_e_plotar()


# Executar Simulação
# simular_mercado()
