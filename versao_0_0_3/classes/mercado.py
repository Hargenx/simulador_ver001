from dataclasses import dataclass, field
from typing import List, Dict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .fundo_imobiliario import FundoImobiliario
    from .agente import Agente

@dataclass
class Mercado:
    """
    Classe que representa o mercado financeiro.

    O mercado gerencia os ativos financeiros, fundos imobiliários e informações de inflação.
    Ele também fornece funcionalidades para registrar inflação e pagar dividendos aos agentes.

    Atributos:
        ativos (Dict[str, float]): Um dicionário onde as chaves são os nomes dos ativos
                                   e os valores são os preços atuais.
        fundos_imobiliarios (Dict[str, FundoImobiliario]): Um dicionário com os fundos
                                                           imobiliários disponíveis no mercado.
        historico_inflacao (List[float]): Lista contendo o histórico das taxas de inflação registradas.
    """
    ativos: Dict[str, float]
    fundos_imobiliarios: Dict[str, "FundoImobiliario"] = field(default_factory=dict)
    historico_inflacao: List[float] = field(default_factory=list)

    def registrar_inflacao(self, taxa_inflacao: float) -> None:
        """
        Registra uma taxa de inflação para a rodada atual no mercado.

        :param taxa_inflacao: Taxa de inflação registrada (em formato decimal, por exemplo, 0.005 para 0,5%).
        :return: None
        """
        self.historico_inflacao.append(taxa_inflacao)
        print(f"[MERCADO] Registrada inflação de {taxa_inflacao:.4%} na rodada.")

    def pagar_dividendos(self, agentes: List["Agente"]) -> None:
        """
        Calcula e distribui os dividendos dos fundos imobiliários para os agentes
        com base no número de cotas possuídas.

        :param agentes: Lista de agentes que participam do mercado.
        :return: None
        """
        for fundo in self.fundos_imobiliarios.values():
            for agente in agentes:
                num_cotas = agente.carteira.get(fundo.nome, 0)
                if num_cotas > 0:
                    dividendos = fundo.calcular_dividendos(num_cotas)
                    agente.caixa += dividendos
                    print(
                        f"[DIVIDENDOS] {agente.nome} recebeu {dividendos:.2f} de dividendos do fundo {fundo.nome}."
                    )
