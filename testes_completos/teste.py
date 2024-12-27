import random
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict


# Classes Atualizadas
@dataclass
class Ativo:
    nome: str
    preco_atual: float
    historico_precos: List[float] = field(default_factory=list)

    def atualizar_preco(self, novo_preco: float) -> None:
        self.historico_precos.append(self.preco_atual)
        self.preco_atual = novo_preco

    def obter_media_precos(self) -> float:
        return (
            sum(self.historico_precos) / len(self.historico_precos)
            if self.historico_precos
            else self.preco_atual
        )


@dataclass
class Agente:
    nome: str
    saldo: float
    carteira: Dict[str, int]
    sentimento: str
    expectativa: List[float]  # [min, esperada, max]
    conhecimento: str

    def tomar_decisao(self, mercado, order_book):
        for ativo, preco in mercado.ativos.items():
            prob_compra = random.uniform(0, 1)
            if prob_compra > 0.5:  # Compra
                quantidade = random.randint(1, 10)
                preco_limite = preco * random.uniform(0.98, 1.02)
                ordem = Ordem("compra", self, ativo, preco_limite, quantidade)
                print(f"[COMPRA] {self.nome} deseja comprar {quantidade} de {ativo} por até {preco_limite:.2f}")
            else:  # Venda
                quantidade_maxima = self.carteira.get(ativo, 0)
                if quantidade_maxima > 0:  # Só vende se tiver ativos na carteira
                    quantidade = random.randint(1, quantidade_maxima)
                    preco_limite = preco * random.uniform(0.98, 1.02)
                    ordem = Ordem("venda", self, ativo, preco_limite, quantidade)
                    print(f"[VENDA] {self.nome} deseja vender {quantidade} de {ativo} por pelo menos {preco_limite:.2f}")
                    order_book.adicionar_ordem(ordem)


@dataclass
class Ordem:
    tipo: str
    agente: Agente
    ativo: str
    preco_limite: float
    quantidade: int


@dataclass
class Transacao:
    comprador: Agente
    vendedor: Agente
    ativo: str
    quantidade: int
    preco_execucao: float

    def executar(self):
        valor_total = self.quantidade * self.preco_execucao
        self.comprador.saldo -= valor_total
        self.vendedor.saldo += valor_total
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

                print(
                    f"Melhor ordem de compra: {ordem_compra.preco_limite} | Quantidade: {ordem_compra.quantidade}"
                )
                print(
                    f"Melhor ordem de venda: {ordem_venda.preco_limite} | Quantidade: {ordem_venda.quantidade}"
                )

                if ordem_compra.preco_limite >= ordem_venda.preco_limite:
                    preco_execucao = (
                        ordem_compra.preco_limite + ordem_venda.preco_limite
                    ) / 2
                    quantidade_exec = min(ordem_compra.quantidade, ordem_venda.quantidade)

                    transacao = Transacao(
                        comprador=ordem_compra.agente,
                        vendedor=ordem_venda.agente,
                        ativo=ativo,
                        quantidade=quantidade_exec,
                        preco_execucao=preco_execucao,
                    )
                    transacao.executar()

                    mercado.ativos[ativo] = preco_execucao
                    print(f"Preço do ativo {ativo} atualizado para: {preco_execucao:.2f}")

                    ordem_compra.quantidade -= quantidade_exec
                    ordem_venda.quantidade -= quantidade_exec

                    if ordem_compra.quantidade == 0:
                        self.ordens_compra[ativo].pop(0)
                    if ordem_venda.quantidade == 0:
                        self.ordens_venda[ativo].pop(0)
                else:
                    print(f"Sem execução: preços não compatíveis para {ativo}.")
                    break

            # Remover ordens vazias como precaução
            self.ordens_compra[ativo] = [
                o for o in self.ordens_compra[ativo] if o.quantidade > 0
            ]
            self.ordens_venda[ativo] = [
                o for o in self.ordens_venda[ativo] if o.quantidade > 0
            ]


@dataclass
class Mercado:
    ativos: Dict[str, float]

    def atualizar_preco(self, ativo, novo_preco):
        self.ativos[ativo] = novo_preco


# Função Principal
def main() -> None:
    """
    Executa a simulação.
    """
    num_agentes = 10
    num_rodadas = 20

    # Inicializa o mercado e o livro de ordens
    mercado = Mercado(ativos={"PETR4": 50.0, "VALE3": 45.0})
    order_book = OrderBook()

    # Cria os agentes
    agentes = [
        Agente(
            nome=f"Agente {i+1}",
            saldo=random.uniform(1000, 5000),
            carteira={"PETR4": random.randint(0, 50), "VALE3": random.randint(0, 50)},
            sentimento=random.choice(["positivo", "negativo", "neutro"]),
            expectativa=[40.0, 50.0, 60.0],
            conhecimento=random.choice(["alto", "médio", "baixo"]),
        )
        for i in range(num_agentes)
    ]

    historico_precos = {ativo: [] for ativo in mercado.ativos.keys()}

    for rodada in range(num_rodadas):
        print(f"\n--- Rodada {rodada + 1} ---")

        # Processa decisões dos agentes
        for agente in agentes:
            agente.tomar_decisao(mercado, order_book)

        # Executa as ordens no livro de ordens
        for ativo in mercado.ativos.keys():
            order_book.executar_ordens(ativo, mercado)
            historico_precos[ativo].append(mercado.ativos[ativo])

        # Resumo da rodada
        print("\nResumo após a rodada:")
        for agente in agentes:
            print(
                f"Agente: {agente.nome} | Caixa: {agente.saldo:.2f} | "
                f"Carteira: {agente.carteira} | Sentimento: {agente.sentimento} | "
                f"Expectativa: {agente.expectativa} | Conhecimento: {agente.conhecimento}"
            )

        # Exibe o preço atualizado de cada ativo
        for ativo, preco in mercado.ativos.items():
            print(f"Ativo: {ativo} | Preço Atual: {preco:.2f}")

    # Gráficos
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
