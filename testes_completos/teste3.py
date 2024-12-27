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
class FundoImobiliario:
    nome: str
    preco_cota: float
    historico_precos: List[float] = field(default_factory=list)
    rendimento_mensal: float = (
        0.05  # Percentual fixo do rendimento mensal, por exemplo, 5%
    )

    def atualizar_preco(self, novo_preco: float) -> None:
        """
        Atualiza o preço da cota no mercado.
        """
        self.historico_precos.append(self.preco_cota)
        self.preco_cota = novo_preco

    def calcular_dividendos(self, num_cotas: int) -> float:
        """
        Calcula o valor dos dividendos baseados no número de cotas e no rendimento mensal.
        """
        return num_cotas * self.preco_cota * self.rendimento_mensal


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
        
        # Atualiza a carteira do comprador
        self.comprador.carteira[self.ativo] = (
            self.comprador.carteira.get(self.ativo, 0) + self.quantidade
        )
        
        # Atualiza a carteira do vendedor, com verificação para evitar o KeyError
        if self.ativo in self.vendedor.carteira:
            self.vendedor.carteira[self.ativo] -= self.quantidade
            if self.vendedor.carteira[self.ativo] == 0:
                del self.vendedor.carteira[self.ativo]  # Remove o ativo se a quantidade for zero


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

    def __init__(
        self, nome: str, saldo: float = 10000.0, carteira=None, precos_mercado=None
    ):
        """
        Inicializa o agente com nome, saldo, carteira de ativos e os preços do mercado.
        """
        self.nome: str = nome
        self.caixa: float = saldo
        self.carteira: Dict[str, int] = carteira or {}
        precos_mercado = precos_mercado or {}

        # Calcula o patrimônio inicial com base nos preços de mercado
        self.patrimonio: List[float] = [
            saldo
            + sum(
                precos_mercado.get(ativo, 0) * quantidade
                for ativo, quantidade in self.carteira.items()
            )
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

    def atualiza_patrimonio(
    self, precos_mercado: Dict[str, float], fundos_imobiliarios: Dict[str, FundoImobiliario]
) -> None:
        """
        Atualiza o patrimônio com base no preço atual de mercado dos ativos e fundos imobiliários.
        """
        valor_ativos = sum(
            precos_mercado.get(ativo, 0) * quantidade
            for ativo, quantidade in self.carteira.items()
        )
        valor_fundos = sum(
            fundo.preco_cota * quantidade
            for fundo_nome, fundo in fundos_imobiliarios.items()
            for ativo, quantidade in self.carteira.items()
            if fundo_nome == ativo
        )
        self.patrimonio.append(self.caixa + valor_ativos + valor_fundos)


@dataclass
class Mercado:
    ativos: Dict[str, float]  # Ações tradicionais
    fundos_imobiliarios: Dict[str, FundoImobiliario] = field(default_factory=dict)

    def pagar_dividendos(self, agentes: List["Agente"]) -> None:
        """
        Paga os dividendos dos fundos imobiliários para os agentes.
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


# Função Principal
def main():
    num_agentes = 10
    num_rodadas = 20

    mercado = Mercado(
        ativos={"PETR4": 50.0, "VALE3": 45.0},
        fundos_imobiliarios={
            "FII_A": FundoImobiliario(nome="FII_A", preco_cota=100.0),
            "FII_B": FundoImobiliario(nome="FII_B", preco_cota=150.0),
        },
    )
    order_book = OrderBook()

    agentes = [
        Agente(
            nome=f"Agente {i+1}",
            saldo=random.uniform(1000, 5000),
            carteira={
                ativo: random.randint(0, 50)
                for ativo in {**mercado.ativos, **mercado.fundos_imobiliarios}.keys()
            },
            precos_mercado={
                **mercado.ativos,
                **{
                    fundo.nome: fundo.preco_cota
                    for fundo in mercado.fundos_imobiliarios.values()
                },
            },
        )
        for i in range(num_agentes)
    ]

    historico_precos = {
        ativo: []
        for ativo in {
            **mercado.ativos,
            **{fundo.nome: fundo for fundo in mercado.fundos_imobiliarios.values()},
        }
    }

    for rodada in range(num_rodadas):
        print(f"\n--- Rodada {rodada + 1} ---")

        # Atualiza vizinhos para cada agente
        for agente in agentes:
            agente.atualiza_vizinhos(agentes)

        # Processa ordens de ações e fundos imobiliários
        for agente in agentes:
            for ativo, preco in mercado.ativos.items():
                ordem = agente.gera_ordem(ativo, preco)
                order_book.adicionar_ordem(ordem)
                print(
                    f"[{ordem.tipo.upper()}] {agente.nome} deseja {ordem.tipo} {ordem.quantidade} de {ativo} "
                    f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
                )
            for fundo_nome, fundo in mercado.fundos_imobiliarios.items():
                ordem = agente.gera_ordem(fundo_nome, fundo.preco_cota)
                order_book.adicionar_ordem(ordem)
                print(
                    f"[{ordem.tipo.upper()}] {agente.nome} deseja {ordem.tipo} {ordem.quantidade} de {fundo_nome} "
                    f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
                )

        # Executa ordens de ações e atualiza o histórico de preços
        for ativo in mercado.ativos.keys():
            order_book.executar_ordens(ativo, mercado)

            # Adiciona o preço atual ao histórico
            if len(historico_precos[ativo]) < rodada + 1:
                historico_precos[ativo].append(mercado.ativos[ativo])

        # Executa ordens de fundos imobiliários e atualiza o histórico de preços
        for fundo_nome, fundo in mercado.fundos_imobiliarios.items():
            order_book.executar_ordens(fundo_nome, mercado)

            # Adiciona o preço atual ao histórico
            if len(historico_precos[fundo_nome]) < rodada + 1:
                historico_precos[fundo_nome].append(fundo.preco_cota)

        # Paga dividendos dos fundos imobiliários
        mercado.pagar_dividendos(agentes)

        # Atualiza patrimônio dos agentes
        for agente in agentes:
            agente.atualiza_patrimonio(mercado.ativos, mercado.fundos_imobiliarios)

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

    # Garante que todas as listas de preços tenham o mesmo comprimento que o número de rodadas
    for ativo, precos in historico_precos.items():
        while len(precos) < num_rodadas:
            precos.append(precos[-1])  # Preenche com o último preço registrado

    # Gráficos de evolução e variações
    plt.figure(figsize=(12, 8))
    rodadas_selecionadas = range(
        0, num_rodadas, max(1, num_rodadas // 10)
    )  # Granularidade para rodadas

    # Gráfico 1: Evolução dos preços
    plt.subplot(2, 1, 1)
    for ativo, precos in historico_precos.items():
        plt.plot(range(num_rodadas), precos, label=ativo)
    plt.xticks(rodadas_selecionadas)  # Define rodadas selecionadas para granularidade
    plt.xlabel("Rodadas")
    plt.ylabel("Preços")
    plt.title("Evolução dos Preços dos Ativos")
    plt.legend()
    plt.grid(True)

    # Gráfico 2: Variações percentuais
    plt.subplot(2, 1, 2)
    for ativo, precos in historico_precos.items():
        variacoes = [
            100 * (precos[i] - precos[i - 1]) / precos[i - 1] if i > 0 else 0
            for i in range(len(precos))
        ]
        plt.plot(range(num_rodadas), variacoes, label=f"Variação {ativo}")
    plt.xticks(rodadas_selecionadas)  # Define rodadas selecionadas para granularidade
    plt.xlabel("Rodadas")
    plt.ylabel("Variação Percentual (%)")
    plt.title("Variações Percentuais nos Preços dos Ativos")
    plt.legend()
    plt.grid(True)

    # Exibe os gráficos
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
