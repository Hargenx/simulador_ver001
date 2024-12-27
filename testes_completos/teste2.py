import random
import math
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class Ativo:
    nome: str
    preco_atual: float
    historico_precos: List[float] = field(default_factory=list)

    def atualizar_preco(self, novo_preco: float) -> None:
        self.historico_precos.append(self.preco_atual)
        self.preco_atual = novo_preco


@dataclass
class Ordem:
    tipo: str
    agente: "Agente"
    ativo: str
    preco_limite: float
    quantidade: int


@dataclass
class Transacao:
    comprador: "Agente"
    vendedor: "Agente"
    ativo: str
    quantidade: int
    preco_execucao: float

    def executar(self):
        valor_total = self.quantidade * self.preco_execucao
        self.comprador.caixa -= valor_total
        self.vendedor.caixa += valor_total
        self.comprador.carteira[self.ativo] = (
            self.comprador.carteira.get(self.ativo, 0) + self.quantidade
        )
        self.vendedor.carteira[self.ativo] -= self.quantidade


@dataclass
class OrderBook:
    ordens_compra: Dict[str, List[Ordem]] = field(default_factory=dict)
    ordens_venda: Dict[str, List[Ordem]] = field(default_factory=dict)

    def adicionar_ordem(self, ordem: Ordem):
        if ordem.tipo == "compra":
            self.ordens_compra.setdefault(ordem.ativo, []).append(ordem)
        elif ordem.tipo == "venda":
            self.ordens_venda.setdefault(ordem.ativo, []).append(ordem)

    def executar_ordens(self, ativo, mercado):
        if ativo in self.ordens_compra and ativo in self.ordens_venda:
            self.ordens_compra[ativo].sort(key=lambda x: x.preco_limite, reverse=True)
            self.ordens_venda[ativo].sort(key=lambda x: x.preco_limite)

            while self.ordens_compra[ativo] and self.ordens_venda[ativo]:
                ordem_compra = self.ordens_compra[ativo][0]
                ordem_venda = self.ordens_venda[ativo][0]

                if ordem_compra.preco_limite >= ordem_venda.preco_limite:
                    preco_execucao = (
                        ordem_compra.preco_limite + ordem_venda.preco_limite
                    ) / 2
                    quantidade_exec = min(
                        ordem_compra.quantidade, ordem_venda.quantidade
                    )

                    transacao = Transacao(
                        comprador=ordem_compra.agente,
                        vendedor=ordem_venda.agente,
                        ativo=ativo,
                        quantidade=quantidade_exec,
                        preco_execucao=preco_execucao,
                    )
                    transacao.executar()

                    mercado.ativos[ativo] = preco_execucao

                    ordem_compra.quantidade -= quantidade_exec
                    ordem_venda.quantidade -= quantidade_exec

                    if ordem_compra.quantidade == 0:
                        self.ordens_compra[ativo].pop(0)
                    if ordem_venda.quantidade == 0:
                        self.ordens_venda[ativo].pop(0)
                else:
                    break


class Agente:
    """
    Representa um agente participante do mercado.
    """

    def __init__(self, nome: str, saldo: float = 10000.0, carteira=None, precos_mercado=None):
        """
        Inicializa o agente com nome, saldo, carteira de ativos e os preços do mercado.
        """
        self.nome: str = nome
        self.caixa: float = saldo
        self.carteira: Dict[str, int] = carteira or {}
        precos_mercado = precos_mercado or {}
        
        # Calcula o patrimônio inicial com base nos preços de mercado
        self.patrimonio: List[float] = [
            saldo + sum(precos_mercado.get(ativo, 0) * quantidade for ativo, quantidade in self.carteira.items())
        ]
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

    def gera_ordem(self, ativo: str, preco_mercado: float) -> Ordem:
        """
        Gera uma ordem de compra ou venda com base no sentimento.
        """
        self.atualiza_sentimento()
        preco_expectativa = self.calcula_preco_expectativa(preco_mercado)
        quantidade = 1  # Quantidade fixa conforme regra
        tipo_ordem = "compra" if self.sentimento > 0 else "venda"
        return Ordem(tipo_ordem, self, ativo, preco_expectativa, quantidade)

    def atualiza_vizinhos(self, agentes: List["Agente"], max_vizinhos: int = 3) -> None:
        """
        Seleciona vizinhos aleatórios.
        """
        self.vizinhos = random.sample(agentes, min(len(agentes), max_vizinhos))

    def atualiza_patrimonio(self, preco_mercado: Dict[str, float]) -> None:
        """
        Atualiza o patrimônio com base no preço atual de mercado.
        """
        valor_ativos = sum(
            preco_mercado[ativo] * quantidade
            for ativo, quantidade in self.carteira.items()
        )
        self.patrimonio.append(self.caixa + valor_ativos)


@dataclass
class Mercado:
    ativos: Dict[str, float]


# Função Principal
def main():
    num_agentes = 10
    num_rodadas = 20

    mercado = Mercado(ativos={"PETR4": 50.0, "VALE3": 45.0})
    order_book = OrderBook()

    agentes = [
        Agente(
            nome=f"Agente {i+1}",
            saldo=random.uniform(1000, 5000),
            carteira={ativo: random.randint(0, 50) for ativo in mercado.ativos.keys()},
            precos_mercado=mercado.ativos,  # Passa os preços do mercado
        )
        for i in range(num_agentes)
    ]

    historico_precos = {ativo: [] for ativo in mercado.ativos.keys()}

    for rodada in range(num_rodadas):
        print(f"\n--- Rodada {rodada + 1} ---")

        for agente in agentes:
            agente.atualiza_vizinhos(agentes)

        for agente in agentes:
            for ativo, preco in mercado.ativos.items():
                ordem = agente.gera_ordem(ativo, preco)
                order_book.adicionar_ordem(ordem)
                print(
                    f"[{ordem.tipo.upper()}] {agente.nome} deseja {ordem.tipo} {ordem.quantidade} de {ativo} "
                    f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
                )

        for ativo in mercado.ativos.keys():
            order_book.executar_ordens(ativo, mercado)
            historico_precos[ativo].append(mercado.ativos[ativo])

        for agente in agentes:
            agente.atualiza_patrimonio(mercado.ativos)

        print("\nResumo após a rodada:")
        for agente in agentes:
            print(
                f"Agente: {agente.nome} | Caixa: {agente.caixa:.2f} | "
                f"Carteira: {agente.carteira} | Sentimento: {agente.sentimento:.2f} | "
                f"Patrimônio: {agente.patrimonio[-1]:.2f}"
            )

        # Exibe o preço atualizado de cada ativo
        for ativo, preco in mercado.ativos.items():
            print(f"Ativo: {ativo} | Preço Atual: {preco:.2f}")

    plt.figure(figsize=(12, 8))
    for ativo, precos in historico_precos.items():
        plt.plot(range(num_rodadas), precos, label=ativo)
    plt.xlabel("Rodadas")
    plt.ylabel("Preços")
    plt.title("Evolução dos Preços dos Ativos")
    plt.legend()
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    main()
