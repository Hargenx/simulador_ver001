from dataclasses import dataclass, field
from typing import List, Dict
import random
import numpy as np
from sklearn.linear_model import LinearRegression
import pandas as pd

# Importa classes que representam o ambiente de mercado e ativos
from testes_completos.atual import FundoImobiliario, Mercado, Ordem, OrderBook


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
        vizinhos (List[Agente]): Lista de agentes vizinhos (para influência social).
        tau (int): Período para cálculo da volatilidade percebida.
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
    vizinhos: List["Agente"] = field(default_factory=list)

    tau: int = field(init=False)
    volatilidade_percebida: float = field(default=0.0, init=False)

    def __post_init__(self):
        self.tau = random.randint(22, 252)
        if not (0 <= self.literacia_financeira <= 1):
            raise ValueError("literacia_financeira deve estar entre 0 e 1.")
        if not (-1 <= self.sentimento <= 1):
            raise ValueError("sentimento deve estar entre -1 e 1.")

    def calcular_volatilidade_percebida(self, historico_precos: List[float]) -> None:
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
        """
        if self.volatilidade_percebida > 0:
            return risco_desejado / self.volatilidade_percebida
        return 0.0

    def calcular_preco_especulativo(self, fundo: FundoImobiliario) -> float:
        """
        Extrapola o preço futuro de um fundo imobiliário utilizando regressão linear.
        """
        # Define uma janela para observação (mínimo 2 pontos)
        window_size = max(int(self.tau / 4), 2)
        precos_obs = fundo.historico_precos[-window_size:]
        X = np.arange(len(precos_obs)).reshape(-1, 1)
        y = np.array(precos_obs)
        modelo = LinearRegression()
        modelo.fit(X, y)
        # Projeta para um número de períodos futuro (mínimo 1)
        futuro_steps = max(int(self.tau / 10), 1)
        futuro = np.arange(len(precos_obs), len(precos_obs) + futuro_steps).reshape(
            -1, 1
        )
        previsoes_futuras = modelo.predict(futuro)
        return round(previsoes_futuras[-1], 2)

    def calcular_expectativa_preco(self, fundo: FundoImobiliario) -> float:
        """
        Calcula a expectativa de preço para um fundo imobiliário considerando
        componentes fundamentalistas, especulativos e ruído.
        """
        premio = 0.15  # Valor fixo do prêmio para cada agente
        # Modelo de Gordon para análise fundamentalista
        gordon = (
            fundo.calcular_dividendos_cota()
            * 12
            * (1 + self.expectativa_inflacao)
            / (premio - self.expectativa_inflacao)
        )
        retorno_fundamentalista = gordon / fundo.historico_precos[-1] - 1

        preco_especulativo = self.calcular_preco_especulativo(fundo)
        retorno_especulativo = preco_especulativo / fundo.historico_precos[-1] - 1

        ruido = random.normalvariate(0, 0.1)

        expectativa_retorno = (
            self.comportamento_fundamentalista * retorno_fundamentalista
            + self.comportamento_especulador * retorno_especulativo
            + self.comportamento_ruido * ruido
        )
        return fundo.historico_precos[-1] * (1 + expectativa_retorno)

    def tomar_decisao(self, mercado: Mercado, order_book: OrderBook) -> None:
        """
        Realiza uma decisão de compra ou venda de ativos no mercado, criando uma ordem.
        """
        for ativo, preco in mercado.ativos.items():
            if ativo not in self.carteira:
                continue

            historico_precos = mercado.historico_precos.get(ativo, [])
            self.calcular_volatilidade_percebida(historico_precos)
            risco_desejado = self.calcular_risco_desejado()
            patrimonio_atual = self.patrimonio[-1] if self.patrimonio else self.saldo
            quantidade = max(
                1,
                int(
                    self.calcular_quantidade_baseada_em_risco(risco_desejado)
                    * patrimonio_atual
                    / preco
                ),
            )
            fundo = mercado.fundos_imobiliarios.get(ativo)
            if not fundo:
                continue
            expectativa_preco = self.calcular_expectativa_preco(fundo)
            if expectativa_preco > preco:  # Estratégia de COMPRA
                preco_limite = expectativa_preco * 0.9
                ordem = Ordem("compra", self, ativo, preco_limite, quantidade)
            else:  # Estratégia de VENDA
                quantidade_venda = random.randint(1, self.carteira.get(ativo, 0))
                preco_limite = preco * random.uniform(
                    0.9, 1.1 + self.comportamento_especulador * 0.1
                )
                ordem = Ordem("venda", self, ativo, preco_limite, quantidade_venda)
            order_book.adicionar_ordem(ordem)

    def atualizar_patrimonio(
        self,
        precos_mercado: Dict[str, float],
        fundos_imobiliarios: Dict[str, FundoImobiliario],
    ) -> None:
        """
        Atualiza o patrimônio do agente com base no saldo e no valor dos ativos.
        """
        if not precos_mercado and not fundos_imobiliarios:
            raise ValueError("Não há dados de mercado para atualizar o patrimônio.")

        valor_ativos = sum(
            quantidade * precos_mercado.get(ativo, 0)
            for ativo, quantidade in self.carteira.items()
            if ativo not in fundos_imobiliarios
        )

        valor_fundos = sum(
            quantidade * fundos_imobiliarios[ativo].historico_precos[-1]
            for ativo, quantidade in self.carteira.items()
            if ativo in fundos_imobiliarios
            and fundos_imobiliarios[ativo].historico_precos
        )

        patrimonio_atual = self.saldo + valor_ativos + valor_fundos
        self.patrimonio.append(patrimonio_atual)

    def calcular_quantidade_desejada(self, fundo: FundoImobiliario) -> float:
        """
        Calcula a quantidade desejada de cotas de um fundo imobiliário com base
        no risco assumido e no patrimônio atual.
        """
        patrimonio_atual = self.patrimonio[-1] if self.patrimonio else self.saldo
        risco_desejado = self.calcular_risco_desejado()
        quantidade_base_risco = self.calcular_quantidade_baseada_em_risco(
            risco_desejado
        )
        preco_cota = fundo.historico_precos[-1]
        return (patrimonio_atual * quantidade_base_risco) / preco_cota

    def decidir_operacao(self, fundo: FundoImobiliario) -> None:
        """
        Decide se deve comprar ou vender cotas de um fundo imobiliário e exibe a operação.
        """
        preco_cota = fundo.historico_precos[-1]
        preco_expec = self.calcular_expectativa_preco(fundo)
        quant_desejada = int(self.calcular_quantidade_desejada(fundo))
        quantidade_atual = self.carteira.get(fundo.nome, 0)

        if preco_expec > preco_cota:
            if quant_desejada > quantidade_atual:
                quantidade_ordem = quant_desejada - quantidade_atual
                print(
                    f"Ordem de COMPRA: {quantidade_ordem} cotas, por {round(preco_expec, 2)}"
                )
            else:
                quantidade_ordem = max(1, (quantidade_atual - quant_desejada) // 3)
                print(
                    f"Ordem de COMPRA: {quantidade_ordem} cotas, por {round(preco_expec, 2)}"
                )
        else:
            if quant_desejada > quantidade_atual:
                quantidade_ordem = quant_desejada - quantidade_atual
                print(
                    f"Ordem de VENDA: {quantidade_ordem} cotas, por {round(preco_expec, 2)}"
                )
            else:
                quantidade_ordem = max(1, (quantidade_atual - quant_desejada) // 3)
                print(
                    f"Ordem de VENDA: {quantidade_ordem} cotas, por {round(preco_expec, 2)}"
                )

    def calcular_I_privada(self) -> float:
        """
        Calcula a taxa de crescimento percentual do patrimônio do agente
        nos últimos 22 períodos.
        """
        if len(self.patrimonio) > 22:
            patrimonio_atual = self.patrimonio[-1]
            patrimonio_22 = self.patrimonio[-22]
            if patrimonio_22 != 0:
                return (patrimonio_atual / patrimonio_22) - 1
        return 0.0

    def calcular_I_social(self) -> float:
        """
        Calcula a média do crescimento percentual do patrimônio dos vizinhos.
        """
        if self.vizinhos:
            taxas = [
                vizinho.calcular_I_privada()
                for vizinho in self.vizinhos
                if len(vizinho.patrimonio) > 22
            ]
            if taxas:
                return sum(taxas) / len(taxas)
        return 0.0

    def sorteia_news(self) -> float:
        """
        Gera um valor aleatório para representar o impacto de notícias no sentimento.
        """
        return round(random.gauss(0.5, 1), 2)

    def atualiza_sentimento(self) -> float:
        """
        Atualiza o sentimento do agente com base em fatores privados, sociais e notícias.
        """
        I_privada = self.calcular_I_privada()
        I_social = self.calcular_I_social()
        news = self.sorteia_news()
        sentimento_bruto = 0.5 * I_privada + 0.3 * I_social + 0.05 * news
        self.sentimento = max(-1, min(1, sentimento_bruto))
        return self.sentimento
