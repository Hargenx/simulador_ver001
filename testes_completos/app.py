import random
import math
from typing import List


class Agente:
    """
    Representa um agente participante do mercado.
    """

    def __init__(self, nome: str, caixa: float = 10000.0):
        self.nome: str = nome
        self.caixa: float = caixa
        self.portfolio: int = 0
        self.patrimonio: List[float] = [caixa]  # Histórico do patrimônio
        self.vizinhos: List["Agente"] = []
        self.sentimento: float = 0.0

    def calcula_l_privada(self) -> float:
        """
        Calcula l_privada como a variação percentual do patrimônio em 22 períodos.
        """
        if len(self.patrimonio) > 22:
            patrimonio_t = self.patrimonio[-1]
            patrimonio_t_22 = self.patrimonio[-22]
            return (patrimonio_t / patrimonio_t_22) - 1
        return 0.0

    def calcula_l_social(self) -> float:
        """
        Calcula l_social como a média aritmética do l_privada dos vizinhos.
        """
        if self.vizinhos:
            return sum(vizinho.calcula_l_privada() for vizinho in self.vizinhos) / len(
                self.vizinhos
            )
        return 0.0

    def sorteia_news(self) -> float:
        """
        Sorteia um valor da distribuição normal com média 0 e desvio padrão 1.
        """
        return random.gauss(0, 1)

    def atualiza_sentimento(self) -> None:
        """
        Atualiza o sentimento com base em l_privada, l_social e news.
        """
        l_privada = self.calcula_l_privada()
        l_social = self.calcula_l_social()
        news = self.sorteia_news()
        sentimento_bruto = 0.2 * l_privada + 0.3 * l_social + 0.05 * news
        self.sentimento = max(
            -1, min(1, sentimento_bruto)
        )  # Garante que o sentimento está entre -1 e 1

    def calcula_preco_expectativa(self, preco_mercado: float) -> float:
        """
        Calcula o preço de expectativa do agente com base no sentimento.
        """
        return preco_mercado * math.exp(self.sentimento / 10)

    def gera_ordem(self, preco_mercado: float) -> "Ordem":
        """
        Gera uma ordem de compra ou venda com base no sentimento.
        """
        self.atualiza_sentimento()
        preco_expectativa = self.calcula_preco_expectativa(preco_mercado)
        quantidade = 1  # Quantidade fixa conforme regra
        tipo_ordem = "compra" if self.sentimento > 0 else "venda"
        return Ordem(tipo_ordem, quantidade, preco_expectativa, self)

    def atualiza_vizinhos(self, agentes: List["Agente"], max_vizinhos: int = 3) -> None:
        """
        Seleciona vizinhos aleatórios.
        """
        self.vizinhos = random.sample(agentes, min(len(agentes), max_vizinhos))

    def atualiza_patrimonio(self, ordem: "Ordem", preco_mercado: float) -> None:
        """
        Atualiza o patrimônio e o portfólio com base na ordem executada.
        """
        if ordem.tipo == "compra" and self.caixa >= ordem.preco:
            self.caixa -= ordem.preco
            self.portfolio += ordem.quantidade
        elif ordem.tipo == "venda" and self.portfolio > 0:
            self.caixa += ordem.preco
            self.portfolio -= ordem.quantidade
        # Atualiza o histórico do patrimônio
        self.patrimonio.append(self.caixa + self.portfolio * preco_mercado)


class Ordem:
    """
    Representa uma ordem de compra ou venda.
    """

    def __init__(self, tipo: str, quantidade: int, preco: float, agente: Agente):
        self.tipo: str = tipo
        self.quantidade: int = quantidade
        self.preco: float = preco
        self.agente: Agente = agente


class Simulador:
    """
    Simulador do mercado com agentes e rodadas.
    """

    def __init__(
        self, agentes: List[Agente], rodadas: int = 30, preco_inicial: float = 50.0
    ):
        self.agentes = agentes
        self.rodadas = rodadas
        self.preco_mercado = preco_inicial  # Preço inicial da ação
        self.historico_preco = [preco_inicial]  # Histórico do preço do mercado

    def atualiza_preco(self):
        """
        Atualiza o preço das ações com base na oferta e demanda.
        """
        compras = sum(1 for agente in self.agentes if agente.sentimento > 0)
        vendas = len(self.agentes) - compras

        # Preço sobe com mais compras, cai com mais vendas, e inclui um ruído aleatório
        variacao = (compras - vendas) / len(self.agentes) + random.uniform(-0.01, 0.01)
        self.preco_mercado *= 1 + variacao  # Atualiza o preço proporcionalmente
        self.historico_preco.append(self.preco_mercado)

    def run(self) -> None:
        """
        Executa a simulação.
        """
        for rodada in range(1, self.rodadas + 1):
            print(f"\n--- Rodada {rodada} ---")

            # Cada agente toma decisões e gera uma ordem
            for agente in self.agentes:
                agente.atualiza_vizinhos(self.agentes)  # Atualiza a rede de vizinhos
                ordem = agente.gera_ordem(
                    self.preco_mercado
                )  # Gera ordem baseada no sentimento
                agente.atualiza_patrimonio(
                    ordem, self.preco_mercado
                )  # Atualiza o patrimônio

                print(
                    f"Agente: {agente.nome} | Ordem: {ordem.tipo} | Preço: {ordem.preco:.2f} | "
                    f"Caixa: {agente.caixa:.2f} | Portfólio: {agente.portfolio} | Sentimento: {agente.sentimento:.2f}"
                )

            # Atualiza o preço do mercado ao final de cada rodada
            self.atualiza_preco()
            print(f"Preço de mercado atualizado: {self.preco_mercado:.2f}")


if __name__ == "__main__":
    # Inicializa agentes e simulador
    agentes = [Agente(f"Agente {i+1}") for i in range(10)]
    # simulador = Simulador(agentes)
    # simulador.run()
    import matplotlib.pyplot as plt

    # Após executar a simulação:
    simulador = Simulador(agentes, rodadas=30)
    simulador.run()

    # Gráfico do preço do mercado ao longo das rodadas
    plt.plot(range(1, len(simulador.historico_preco) + 1), simulador.historico_preco)
    plt.title("Evolução do Preço do Mercado")
    plt.xlabel("Rodadas")
    plt.ylabel("Preço")
    plt.grid()
    plt.show()
