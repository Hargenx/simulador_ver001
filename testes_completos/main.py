import random
from typing import List


class Agente:
    """
    Representa um agente participante do mercado.
    """

    def __init__(self, nome: str, caixa: float = 10000.0):
        self.nome: str = nome
        self.caixa: float = caixa
        self.portfolio: int = 0
        self.historico_caixa: List[float] = [caixa]  # Histórico de caixa
        self.risco: float = 0.0  # Inicializa risco do agente
        self.vizinhos: List["Agente"] = []
        self.sentimento_atual: float = random.uniform(0, 1)

    def calcula_risco(self) -> float:
        """
        Calcula o risco do agente com base na variação de caixa e no portfolio.
        Risco maior se houve grandes variações ou muitas compras.
        """
        variacao_caixa = (
            abs(self.caixa - self.historico_caixa[-1]) / self.historico_caixa[-1]
        )
        risco_portfolio = min(
            self.portfolio / 10, 1
        )  # Normaliza risco do portfolio entre 0 e 1
        self.risco = (variacao_caixa + risco_portfolio) / 2  # Média dos dois riscos
        return self.risco

    def atualiza_sentimento(self) -> float:
        """
        Atualiza o sentimento do agente com base em risco, vizinhos e histórico.
        """
        # Histórico do agente
        variacao_caixa = (self.caixa - self.historico_caixa[-1]) / self.historico_caixa[
            -1
        ]
        impacto_historico = max(0, min(1, 0.5 + variacao_caixa))

        # Sentimento dos vizinhos
        if self.vizinhos:
            sentimento_vizinhos = sum(
                vizinho.sentimento_atual for vizinho in self.vizinhos
            ) / len(self.vizinhos)
        else:
            sentimento_vizinhos = random.uniform(0, 1)

        # Fator aleatório e risco
        fator_aleatorio = random.uniform(0, 1)
        risco_atual = (
            1 - self.calcula_risco()
        )  # Inverso do risco (quanto menor o risco, maior o impacto positivo)

        # Combinação com peso no risco
        self.sentimento_atual = (
            impacto_historico + sentimento_vizinhos + fator_aleatorio + risco_atual
        ) / 4
        return self.sentimento_atual

    def atualiza_vizinhos(self, agentes: List["Agente"], max_vizinhos: int = 3) -> None:
        """
        Seleciona vizinhos aleatórios, excluindo o próprio agente.
        """
        agentes_disponiveis = [agente for agente in agentes if agente != self]
        self.vizinhos = random.sample(
            agentes_disponiveis, min(len(agentes_disponiveis), max_vizinhos)
        )

    def gera_ordem(self, preco: float) -> "Ordem":
        """
        Gera uma ordem com base no sentimento e no risco atual.
        """
        sentimento = self.atualiza_sentimento()
        tipo_ordem = "compra" if sentimento > 0.5 else "venda"
        quantidade = int(
            sentimento * 10 * (1 - self.risco)
        )  # Menor quantidade se o risco for alto
        return Ordem(tipo_ordem, quantidade, preco, self)

    def executa_ordem(self, ordem: "Ordem") -> None:
        """
        Executa a ordem e atualiza o caixa e o portfolio do agente.
        """
        if ordem.tipo == "compra":
            custo_total = ordem.quantidade * ordem.preco
            if self.caixa >= custo_total:
                self.caixa -= custo_total
                self.portfolio += ordem.quantidade
        elif ordem.tipo == "venda" and self.portfolio >= ordem.quantidade:
            receita_total = ordem.quantidade * ordem.preco
            self.caixa += receita_total
            self.portfolio -= ordem.quantidade

    def registra_historico(self) -> None:
        """
        Registra o estado atual do caixa no histórico.
        """
        self.historico_caixa.append(self.caixa)


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
    Simulador do mercado B3.
    """

    def __init__(self, agentes: List[Agente], rodadas: int = 30):
        self.agentes: List[Agente] = agentes
        self.rodadas: int = rodadas
        self.preco: float = 50.0

    def run(self) -> None:
        """
        Executa a simulação.
        """
        for rodada in range(1, self.rodadas + 1):
            print(f"\n--- Rodada {rodada} ---")

            # Atualiza vizinhos
            for agente in self.agentes:
                agente.atualiza_vizinhos(self.agentes)

            # Gera e executa ordens
            for agente in self.agentes:
                ordem = agente.gera_ordem(self.preco)
                agente.executa_ordem(ordem)
                print(
                    f"Agente: {agente.nome} | Ordem: {ordem.tipo} {ordem.quantidade} ações | Caixa: {agente.caixa:.2f} | "
                    f"Portfolio: {agente.portfolio} | Risco: {agente.risco:.2f}"
                )

            # Registra histórico
            for agente in self.agentes:
                agente.registra_historico()


if __name__ == "__main__":
    # Criação de agentes
    agentes = [Agente(f"Agente {i+1}") for i in range(10)]

    # Inicia simulador
    simulador = Simulador(agentes)
    simulador.run()
