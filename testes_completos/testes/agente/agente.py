from dataclasses import dataclass, field
from typing import List, Dict
import random
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

from testes_completos.atual import FundoImobiliario
from testes_completos.atual import FundoImobiliario as fii

@dataclass
class Agente:
    """
    Classe que representa um agente no mercado financeiro.

    Atributos:
        nome (str): Nome do agente.
        saldo (float): Saldo disponível em caixa.
        carteira (Dict[str, int]): Quantidade de ativos na posse do agente.
        sentimento (float): Sentimento do agente, entre -1 (negativo) e 1 (positivo).
        expectativa (List[float]): Lista de valores mínimo, esperado e máximo para ativos.
        literacia_financeira (float): Conhecimento financeiro, entre 0 e 1.
        comportamento_fundamentalista (float): Grau de foco em fundamentos, entre 0 e 1.
        comportamento_especulador (float): Grau de especulação, entre 0 e 1.
        comportamento_ruido (float): Impacto de fatores aleatórios nas decisões, entre 0 e 1.
        expectativa_inflacao (float): Expectativa em relação à inflação.
        patrimonio (List[float]): Histórico do patrimônio do agente ao longo do tempo.
        tau (int): Período para cálculo de volatilidade percebida.
        volatilidade_percebida (float): Volatilidade percebida pelo agente.
    """

    nome: str
    saldo: float
    carteira: Dict[str, int]
    sentimento: float
    expectativa: List[float]
    literacia_financeira: float
    comportamento_fundamentalista: float
    comportamento_especulador: float
    comportamento_ruido: float
    expectativa_inflacao: float
    patrimonio: List[float] = field(default_factory=list)
    tau: int = field(init=False)
    volatilidade_percebida: float = field(default=0.0, init=False)

    def __post_init__(self):
        """
        Inicializa atributos dinâmicos e validações após a criação do objeto.
        """
        self.tau = random.randint(22, 252)
        if not (0 <= self.literacia_financeira <= 1):
            raise ValueError("literacia_financeira deve estar entre 0 e 1.")
        if not (-1 <= self.sentimento <= 1):
            raise ValueError("sentimento deve estar entre -1 e 1.")

    def calcular_volatilidade_percebida(
        self, historico_precos: List[float]
    ) -> None:  # A VOLATILIDADE É CALCULADA CONSIDERANDO O PREÇO DIÁRIO!!!!!
        """
        Calcula a volatilidade percebida com base nos log-retornos dos preços.
        """
        if len(historico_precos) >= self.tau:
            historico_teste = historico_precos[-self.tau :]
            retornos = pd.Series(
                np.log(np.array(historico_teste)[1:] / np.array(historico_teste)[:-1])
            )
            self.volatilidade_percebida = retornos.std() * np.sqrt(
                252
            )  # Anualiza a volatilidade
        else:
            self.volatilidade_percebida = 0.0

    def calcular_risco_desejado(self) -> float:
        """
        Calcula o risco que o agente está disposto a assumir.
        """
        return (self.sentimento + 1) * self.volatilidade_percebida / 2

    def calcular_quantidade_baseada_em_risco(self, risco_desejado: float) -> float:
        """
        Calcula a quantidade de ativos que o agente deseja negociar, com base no risco desejado.

        A quantidade é proporcional ao risco desejado e inversamente proporcional à volatilidade
        percebida. Caso a volatilidade percebida seja zero, retorna 0 para evitar divisão por zero.

        Args:
            risco_desejado (float): Nível de risco que o agente está disposto a assumir.

        Returns:
            float: Quantidade calculada com base no risco desejado.
        """
        if self.volatilidade_percebida > 0:  # A VOL PERCEBIDA É SEMPRE POSITIVA
            return risco_desejado / self.volatilidade_percebida
        return 0.0

    def calcular_preco_especulativo(self, fii: "FundoImobiliario") -> float:
        precos_obs = fii.historico_precos[-int(self.tau / 4) :]

        #  Criar a variável independente (X) e dependente (y)
        X = np.arange(len(precos_obs)).reshape(-1, 1)
        y = np.array(precos_obs)

        # Criar e ajustar o modelo de regressão
        modelo = LinearRegression()
        modelo.fit(X, y)

        # Extrapolação para os próximos termos
        futuro = np.arange(
            len(precos_obs), len(precos_obs) + int(self.tau / 10)
        ).reshape(-1, 1)
        previsoes_futuras = modelo.predict(futuro)

        return round(previsoes_futuras[-1], 2)

    def calcular_expectativa_preco(self, fii: "FundoImobiliario") -> float:
        """
        Calcula a expectativa de preço para um fundo imobiliário com base em
        fatores fundamentalistas, especulativos e ruído.
        """
        premio = 0.15  ############################################################### Cada agente tem 1 prêmio
        gordon = (
            fii.calcular_dividendos_cota()
            * 12
            * (1 + self.expectativa_inflacao)
            / (premio - self.expectativa_inflacao)
        )
        retorno_fundamentalista = gordon / fii.historico_precos[-1] - 1
        preco_especulativo = self.calcular_preco_especulativo(fii)
        retorno_especulativo = preco_especulativo / fii.historico_precos[-1] - 1

        ruido = random.normalvariate(0, 0.1)

        expectativa_retorno = (
            self.comportamento_fundamentalista * retorno_fundamentalista
            + self.comportamento_especulador * retorno_especulativo
            + self.comportamento_ruido * ruido
        )
        return fii.historico_precos[-1] * (1 + expectativa_retorno)

    # def tomar_decisao(self, mercado: "Mercado", order_book: "OrderBook") -> None:
    #     """
    #     Realiza uma decisão de compra ou venda de ativos no mercado.
    #     """
    #     for ativo, preco in mercado.ativos.items():
    #         if ativo not in self.carteira:
    #             continue

    #         self.calcular_volatilidade_percebida(mercado.historico_precos[ativo])
    #         risco_desejado = self.calcular_risco_desejado()

    #         quantidade = max(
    #             1, int(self.calcular_quantidade_baseada_em_risco(risco_desejado) * self.patrimonio[-1] / preco)
    #         )

    #         fii = mercado.fundos_imobiliarios.get(ativo)
    #         if not fii:
    #             continue

    #         expectativa_preco = self.calcular_expectativa_preco(fii)

    #         if expectativa_preco > preco:  # Compra
    #             preco_limite = expectativa_preco * 0.9
    #             ordem = Ordem("compra", self, ativo, preco_limite, quantidade)
    #         else:  # Venda
    #             quantidade = random.randint(1, self.carteira.get(ativo, 0))
    #             preco_limite = preco * random.uniform(0.9, 1.1 + self.comportamento_especulador * 0.1)
    #             ordem = Ordem("venda", self, ativo, preco_limite, quantidade)

    #         order_book.adicionar_ordem(ordem)

    def atualizar_patrimonio(
        self,
        precos_mercado: Dict[str, float],
        fundos_imobiliarios: Dict[str, "FundoImobiliario"],
    ) -> None:
        """
        Atualiza o patrimônio total com base no saldo, ativos e fundos imobiliários.

        Args:
            precos_mercado (Dict[str, float]): Preços dos ativos no mercado.
            fundos_imobiliarios (Dict[str, FundoImobiliario]): Fundos imobiliários e seus preços.
        """
        # Validação inicial
        if not precos_mercado and not fundos_imobiliarios:
            raise ValueError("Não há dados de mercado para atualizar o patrimônio.")

        # Cálculo do valor dos ativos (excluindo FIIs)
        valor_ativos = sum(
            quantidade * precos_mercado.get(ativo, 0)
            for ativo, quantidade in self.carteira.items()
            if ativo not in fundos_imobiliarios
        )

        # Cálculo do valor dos fundos imobiliários (FIIs)
        valor_fundos = sum(
            quantidade * fundos_imobiliarios[ativo].historico_precos[-1]
            for ativo, quantidade in self.carteira.items()
            if ativo in fundos_imobiliarios
            and fundos_imobiliarios[ativo].historico_precos
        )

        # Atualização do patrimônio
        patrimonio_atual = self.saldo + valor_ativos + valor_fundos
        self.patrimonio.append(patrimonio_atual)

    def calcular_quantidade_desejada(self):
        patrimonio_atual = self.patrimonio[-1]
        preco_cota = fii.historico_precos[-1]

        # Calcula a quantidade com base no risco e no patrimônio

        quantidade_base_risco = self.calcular_quantidade_baseada_em_risco()
        return patrimonio_atual * quantidade_base_risco / preco_cota

    def decisao(self):
        preco_cota = fii.historico_precos[-1]
        preco_expec = self.calcular_expectativa_preco(fii)
        quant = int(self.calcular_quantidade_desejada())
        n = self.carteira.get(fii.nome, 0)

        # if quant > n:
        #   print(f"Ordem de COMPRA: {(quant - n)} cotas")
        # else:
        #   print(f"Ordem de VENDA: {(n - quant)} cotas")

        if preco_expec > preco_cota:
            if quant > n:
                q = quant - n
                print(f"Ordem de COMPRA: {q} cotas, por {round(preco_expec,2)}")
            else:
                q = n - quant
                print(
                    f"Ordem de COMPRA: {(int(q/3))} cotas, por {round(preco_expec,2)}"
                )

        else:
            if quant > n:
                q = quant - n
                print(f"Ordem de VENDA: {q} cotas, por {round(preco_expec,2)}")
            else:
                q = n - quant
                print(f"Ordem de VENDA: {(int(q/3))} cotas, por {round(preco_expec,2)}")

    def calcula_I_privada(self) -> float:
        """
        Calcula a taxa de crescimento percentual do patrimônio do agente
        nos últimos 22 períodos.

        O cálculo é baseado na relação entre o patrimônio atual (t) e o
        patrimônio de 22 períodos atrás (t-22). Se o histórico do patrimônio
        for insuficiente ou se o patrimônio de t-22 for zero, retorna 0.0.

        Returns:
            float: A taxa de crescimento percentual do patrimônio, expressa como
            um valor decimal (ex.: 0.05 representa 5% de crescimento). Retorna
            0.0 se o histórico for insuficiente ou se o patrimônio de t-22 for zero.
        """
        if len(self.patrimonio) > 22:
            patrimonio_t = self.patrimonio[-1]
            patrimonio_t_22 = self.patrimonio[-22]
            # Evita divisão por zero
            if patrimonio_t_22 != 0:
                return (patrimonio_t / patrimonio_t_22) - 1
        return 0.0

    def calcula_I_social(self) -> float:
        """
        Calcula a média da taxa de crescimento percentual do patrimônio
        (`l_privada`) dos vizinhos do agente.

        Para cada vizinho, a função considera o resultado de `calcula_l_privada`.
        Se nenhum vizinho tiver um histórico suficiente para o cálculo, ou se
        a lista de vizinhos estiver vazia, retorna 0.0.

        Returns:
            float: A média da taxa de crescimento percentual dos patrimônios dos
            vizinhos, expressa como um valor decimal (ex.: 0.03 representa 3% de
            crescimento). Retorna 0.0 se a lista de vizinhos estiver vazia ou se
            nenhum vizinho tiver histórico suficiente.
        """
        if self.vizinhos:
            I_privada_vizinhos = [
                vizinho.calcula_l_privada()
                for vizinho in self.vizinhos
                if len(vizinho.patrimonio)
                > 22  # Garante que o vizinho tenha histórico suficiente
            ]
            if I_privada_vizinhos:  # Evita divisão por zero caso a lista fique vazia
                return sum(I_privada_vizinhos) / len(I_privada_vizinhos)
        return 0.0

    def sorteia_news(
        self,
    ) -> (
        float
    ):  ####################################### AS NEWS DEVEM SER A MESMA PRA CADA AGENTE, EM CADA RODADA, TALVEZ O IDEAL É COLOCA-LA NO MERCADO
        """
        Gera um valor aleatório para representar o impacto de notícias no sentimento do agente.

        Utiliza uma distribuição normal com média 0 e desvio padrão 1, simulando o ruído
        causado por informações externas.

        Returns:
            float: Valor aleatório gerado para o impacto de notícias.
        """
        return round(random.gauss(0.5, 1), 2)

    def atualiza_sentimento(
        self,
    ) -> float:  ################################### DEIXAR MAIS PRECISO O CÁLCULO
        """
        Atualiza o sentimento do agente com base em fatores privados, sociais e externos.

        O sentimento bruto é calculado considerando:
        - L_private: Retorno privado do agente com base em sua carteira.
        - L_social: Influência média dos vizinhos.
        - Impacto de notícias (news): Fator externo aleatório.

        O valor final do sentimento é limitado entre -1 (pessimismo extremo) e 1 (otimismo extremo).

        Returns:
            float: Impacto das news na rodada atual.
        """
        I_privada = self.calcula_I_privada()
        I_social = 0  # self.calcula_l_social()
        news = self.sorteia_news()
        sentimento_bruto = 0.5 * I_privada + 0.3 * I_social + 0.05 * news
        self.sentimento = max(-1, min(1, sentimento_bruto))
        return self.sentimento
