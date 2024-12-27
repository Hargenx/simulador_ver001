from dataclasses import dataclass, field
from typing import List


@dataclass
class FundoImobiliario:
    """
    Classe que representa um fundo imobiliário.

    Um fundo imobiliário é um tipo de investimento que possui um preço por cota e
    oferece rendimentos periódicos baseados em um percentual fixo de rendimento mensal.

    Atributos:
        nome (str): Nome do fundo imobiliário.
        preco_cota (float): Preço atual de uma cota do fundo.
        historico_precos (List[float]): Histórico dos preços das cotas.
        rendimento_mensal (float): Percentual fixo de rendimento mensal sobre o preço da cota.
    """
    nome: str
    preco_cota: float
    historico_precos: List[float] = field(default_factory=list)
    rendimento_mensal: float = (
        0.05  # Percentual fixo do rendimento mensal, por exemplo, 5%
    )

    def atualizar_preco(self, novo_preco: float) -> None:
        """
        Atualiza o preço atual da cota do fundo imobiliário e registra o preço anterior
        no histórico de preços.

        :param novo_preco: Novo preço da cota do fundo imobiliário.
        :return: None
        """
        self.historico_precos.append(self.preco_cota)
        self.preco_cota = novo_preco

    def calcular_dividendos(self, num_cotas: int) -> float:
        """
        Calcula o valor total de dividendos com base no número de cotas possuídas
        e no rendimento mensal do fundo.

        :param num_cotas: Número de cotas possuídas.
        :return: Valor total dos dividendos.
        """
        return num_cotas * self.preco_cota * self.rendimento_mensal
