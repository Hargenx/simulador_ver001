import random
import math
import matplotlib.pyplot as plt
import numpy as np
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
        self.historico_precos.append(self.preco_cota)
        self.preco_cota = novo_preco

    def calcular_dividendos(self, num_cotas: int) -> float:
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

        # Atualiza a carteira do vendedor
        if self.ativo in self.vendedor.carteira:
            self.vendedor.carteira[self.ativo] -= self.quantidade
            if self.vendedor.carteira[self.ativo] == 0:
                del self.vendedor.carteira[self.ativo]


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
    def __init__(
        self, nome: str, saldo: float = 10000.0, carteira=None, precos_mercado=None
    ):
        self.nome: str = nome
        self.caixa: float = saldo
        self.carteira: Dict[str, int] = carteira or {}
        precos_mercado = precos_mercado or {}
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
        if len(self.patrimonio) > 22:
            patrimonio_t = self.patrimonio[-1]
            patrimonio_t_22 = self.patrimonio[-22]
            return (patrimonio_t / patrimonio_t_22) - 1
        return 0.0

    def calcula_l_social(self) -> float:
        if self.vizinhos:
            return sum(vizinho.calcula_l_privada() for vizinho in self.vizinhos) / len(
                self.vizinhos
            )
        return 0.0

    def sorteia_news(self) -> float:
        return random.gauss(0, 1)

    def atualiza_sentimento(self) -> None:
        l_privada = self.calcula_l_privada()
        l_social = self.calcula_l_social()
        news = self.sorteia_news()
        sentimento_bruto = 0.2 * l_privada + 0.3 * l_social + 0.05 * news
        self.sentimento = max(-1, min(1, sentimento_bruto))

    def calcula_preco_expectativa(self, preco_mercado: float) -> float:
        return preco_mercado * math.exp(self.sentimento / 10)

    def gera_ordem(self, ativo: str, preco_mercado: float) -> Ordem:
        self.atualiza_sentimento()
        preco_expectativa = self.calcula_preco_expectativa(preco_mercado)
        quantidade = 1
        tipo_ordem = "compra" if self.sentimento > 0 else "venda"
        return Ordem(tipo_ordem, self, ativo, preco_expectativa, quantidade)

    def atualiza_vizinhos(self, agentes: List["Agente"], max_vizinhos: int = 3) -> None:
        self.vizinhos = random.sample(agentes, min(len(agentes), max_vizinhos))

    def atualiza_patrimonio(
        self,
        precos_mercado: Dict[str, float],
        fundos_imobiliarios: Dict[str, FundoImobiliario],
    ) -> None:
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
    ativos: Dict[str, float]
    fundos_imobiliarios: Dict[str, FundoImobiliario] = field(default_factory=dict)

    def pagar_dividendos(self, agentes: List["Agente"]) -> None:
        for fundo in self.fundos_imobiliarios.values():
            for agente in agentes:
                num_cotas = agente.carteira.get(fundo.nome, 0)
                if num_cotas > 0:
                    dividendos = fundo.calcular_dividendos(num_cotas)
                    agente.caixa += dividendos
                    print(
                        f"[DIVIDENDOS] {agente.nome} recebeu {dividendos:.2f} de dividendos do fundo {fundo.nome}."
                    )


def main():
    num_agentes = 10
    num_rodadas = 20

    # Configuração inicial do mercado
    mercado = Mercado(
        ativos={"PETR4": 50.0, "VALE3": 45.0},
        fundos_imobiliarios={
            "FII_A": FundoImobiliario(nome="FII_A", preco_cota=100.0),
            "FII_B": FundoImobiliario(nome="FII_B", preco_cota=150.0),
        },
    )
    order_book = OrderBook()

    # Criação dos agentes
    agentes = [
        Agente(
            nome=f"Agente {i+1}",
            saldo=random.uniform(1000, 5000),
            carteira={ativo: random.randint(0, 50) for ativo in mercado.ativos.keys()},
            precos_mercado={
                **mercado.ativos,
                **{f.nome: f.preco_cota for f in mercado.fundos_imobiliarios.values()},
            },
        )
        for i in range(num_agentes)
    ]

    historico_precos = {ativo: [] for ativo in mercado.ativos.keys()}
    historico_precos.update(
        {fii.nome: [] for fii in mercado.fundos_imobiliarios.values()}
    )
    historico_patrimonios = {agente.nome: [] for agente in agentes}

    for rodada in range(num_rodadas):
        print(f"\n--- RODADA {rodada + 1} ---")

        # Atualiza vizinhos e gera ordens
        for agente in agentes:
            agente.atualiza_vizinhos(agentes)
            for ativo, preco in mercado.ativos.items():
                ordem = agente.gera_ordem(ativo, preco)
                order_book.adicionar_ordem(ordem)
                print(
                    f"[DECISÃO] {agente.nome} {ordem.tipo.upper()} {ordem.quantidade} de {ativo} "
                    f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
                )
            for fii_nome, fii in mercado.fundos_imobiliarios.items():
                ordem = agente.gera_ordem(fii_nome, fii.preco_cota)
                order_book.adicionar_ordem(ordem)
                print(
                    f"[DECISÃO] {agente.nome} {ordem.tipo.upper()} {ordem.quantidade} de {fii_nome} "
                    f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
                )

        # Executa ordens para ativos tradicionais
        for ativo in mercado.ativos.keys():
            print(f"[EXECUTANDO ORDENS] Para o ativo {ativo}")
            order_book.executar_ordens(ativo, mercado)
            historico_precos[ativo].append(mercado.ativos[ativo])
            print(f"[PREÇO ATUALIZADO] {ativo}: {mercado.ativos[ativo]:.2f}")

        # Executa ordens para FIIs
        for fii_nome, fii in mercado.fundos_imobiliarios.items():
            print(f"[EXECUTANDO ORDENS] Para o fundo imobiliário {fii_nome}")
            order_book.executar_ordens(fii_nome, mercado)
            historico_precos[fii_nome].append(fii.preco_cota)
            print(f"[PREÇO ATUALIZADO] {fii_nome}: {fii.preco_cota:.2f}")

        # Atualiza patrimônio dos agentes
        print(f"\n[RESUMO DA RODADA {rodada + 1}]")
        for agente in agentes:
            agente.atualiza_patrimonio(mercado.ativos, mercado.fundos_imobiliarios)
            historico_patrimonios[agente.nome].append(agente.patrimonio[-1])
            print(
                f"{agente.nome}: Patrimônio: {agente.patrimonio[-1]:.2f} | Caixa: {agente.caixa:.2f} | "
                f"Carteira: {agente.carteira}"
            )

    # Garante que todos os históricos estejam consistentes
    for ativo, precos in historico_precos.items():
        historico_precos[ativo] = normalizar_tamanho(precos, num_rodadas)

    for agente, patrimonios in historico_patrimonios.items():
        historico_patrimonios[agente] = normalizar_tamanho(patrimonios, num_rodadas)

    # Cálculo de volatilidade e gráficos
    plotar_resultados(historico_precos, historico_patrimonios, num_rodadas)


def normalizar_tamanho(lista, tamanho, valor_padrao=0):
    """
    Normaliza o tamanho de uma lista para o valor especificado.
    Preenche com o último valor conhecido ou um valor padrão.
    """
    while len(lista) < tamanho:
        lista.append(lista[-1] if lista else valor_padrao)
    if len(lista) > tamanho:
        lista = lista[:tamanho]
    return lista


def plotar_resultados(historico_precos, historico_patrimonios, num_rodadas):
    # Garantir que todos os históricos estejam normalizados
    for ativo, precos in historico_precos.items():
        historico_precos[ativo] = normalizar_tamanho(precos, num_rodadas)
    for agente, patrimonios in historico_patrimonios.items():
        historico_patrimonios[agente] = normalizar_tamanho(patrimonios, num_rodadas)

    # Cálculo de volatilidade
    volatilidade = {
        ativo: [
            (
                100
                * (historico_precos[ativo][i] - historico_precos[ativo][i - 1])
                / historico_precos[ativo][i - 1]
                if i > 0
                else 0
            )
            for i in range(len(historico_precos[ativo]))
        ]
        for ativo in historico_precos.keys()
    }
    volatilidade_media = {
        ativo: round(np.std(var), 2) for ativo, var in volatilidade.items()
    }

    # Gráficos
    plt.figure(figsize=(12, 8))

    # Gráfico 1: Evolução dos preços
    plt.subplot(3, 1, 1)
    for ativo, precos in historico_precos.items():
        plt.plot(
            range(num_rodadas),
            precos,
            label=f"{ativo} (Vol: {volatilidade_media[ativo]}%)",
        )
    plt.xlabel("Rodadas")
    plt.ylabel("Preços")
    plt.title("Evolução dos Preços dos Ativos e FIIs")
    plt.legend()
    plt.grid(True)

    # Gráfico 2: Variações percentuais nos preços
    plt.subplot(3, 1, 2)
    for ativo, variacoes in volatilidade.items():
        plt.plot(range(num_rodadas), variacoes, label=f"Variação {ativo}")
    plt.xlabel("Rodadas")
    plt.ylabel("Variação Percentual (%)")
    plt.title("Variações Percentuais nos Preços dos Ativos e FIIs")
    plt.legend()
    plt.grid(True)

    # Gráfico 3: Distribuição de patrimônio
    plt.subplot(3, 1, 3)
    for agente, patrimonios in historico_patrimonios.items():
        plt.plot(range(num_rodadas), patrimonios, label=agente)
    plt.xlabel("Rodadas")
    plt.ylabel("Patrimônio")
    plt.title("Distribuição de Patrimônio entre os Agentes")
    plt.legend()
    plt.grid(True)

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
