import random
import math
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict

import numpy as np


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
        self.comprador.saldo -= valor_total
        self.vendedor.saldo += valor_total

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


@dataclass
class Agente:
    nome: str
    saldo: float
    carteira: Dict[str, int]
    sentimento: float  # Sentimento como valor numérico entre -1 e 1
    expectativa: List[float]  # [min, esperada, max]
    conhecimento: str
    literacia_financeira: (
        float  # Entre 0 e 1, representa o nível de conhecimento financeiro
    )
    comportamento_especulador: (
        float  # Entre 0 e 1, maior valor indica comportamento especulador
    )
    comportamento_ruido: float  # Entre 0 e 1, maior valor indica maior impacto de ruído
    expectativa_inflacao: float  # Expectativa do agente em relação à inflação
    patrimonio: List[float] = field(default_factory=list)
    tau: int = field(init=False)
    volatilidade_percebida: float = field(default=0.0, init=False)

    def __post_init__(self):
        self.tau = random.randint(22, 252)  # Sorteio do tempo observado.

    def calcular_volatilidade_percebida(self, historico_precos: List[float]):
        if len(historico_precos) >= self.tau:
            retornos = [
                math.log(historico_precos[i] / historico_precos[i - 1])
                for i in range(1, self.tau)
            ]
            self.volatilidade_percebida = np.std(retornos)
        else:
            self.volatilidade_percebida = 0.0

    def calcular_risco_desejado(self) -> float:
        risco_base = (
            (self.sentimento + 1)
            * self.volatilidade_percebida
            / (2 + self.literacia_financeira)
        )
        fator_especulacao = self.comportamento_especulador * 0.2
        fator_ruido = self.comportamento_ruido * 0.1
        return risco_base + fator_especulacao - fator_ruido

    def ajustar_preco_por_inflacao(self, preco: float) -> float:
        confianca = max(0.5, self.literacia_financeira - self.comportamento_ruido)
        return preco * (1 + self.expectativa_inflacao * confianca)

    def calcular_quantidade_baseada_em_risco(self, risco_desejado: float) -> float:
        if self.volatilidade_percebida > 0:
            return risco_desejado / self.volatilidade_percebida
        return 0.0

    def tomar_decisao(self, mercado, order_book):
        for ativo, preco in mercado.ativos.items():
            self.calcular_volatilidade_percebida(mercado.historico_precos[ativo])
            risco_desejado = self.calcular_risco_desejado()

            # Ajusta a decisão com base na expectativa de inflação
            if self.expectativa_inflacao > 0.03:  # Exemplo: inflação > 3% ao mês
                print(
                    f"[DECISÃO] {self.nome} hesitou devido à alta inflação ({self.expectativa_inflacao:.2%})"
                )
                continue  # Pula a decisão para ativos específicos

            quantidade = max(
                1, int(self.calcular_quantidade_baseada_em_risco(risco_desejado))
            )
            prob_compra = random.uniform(0, 1)

            if prob_compra > 0.5:  # Compra
                preco_limite = preco * random.uniform(
                    0.9, 1.1 + self.comportamento_especulador * 0.1
                )
                ordem = Ordem("compra", self, ativo, preco_limite, quantidade)
            else:  # Venda
                quantidade = random.randint(1, self.carteira.get(ativo, 0))
                preco_limite = preco * random.uniform(
                    0.9, 1.1 + self.comportamento_especulador * 0.1
                )
                ordem = Ordem("venda", self, ativo, preco_limite, quantidade)
            order_book.adicionar_ordem(ordem)

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
        ajuste_literacia = self.literacia_financeira * 0.1
        ajuste_comportamento = self.comportamento_especulador * 0.15
        return preco_mercado * math.exp(
            (self.sentimento + ajuste_literacia - ajuste_comportamento) / 10
        )

    def gerar_ordem(self, ativo: str, preco_mercado: float) -> Ordem:
        self.atualiza_sentimento()
        preco_ajustado = self.ajustar_preco_por_inflacao(preco_mercado)
        preco_expectativa = self.calcula_preco_expectativa(preco_ajustado)
        preco_expectativa += random.gauss(0, self.comportamento_ruido)
        quantidade = max(
            1,
            int(
                self.calcular_quantidade_baseada_em_risco(
                    self.calcular_risco_desejado()
                )
            ),
        )
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
        self.patrimonio.append(self.saldo + valor_ativos + valor_fundos)


@dataclass
class FundoImobiliario:
    nome: str
    preco_cota: float
    historico_precos: List[float] = field(default_factory=list)
    rendimento_mensal: float = 0.005  # 0,5% do valor total do patrimônio.

    def atualizar_preco(self, novo_preco: float):
        self.historico_precos.append(self.preco_cota)
        self.preco_cota = novo_preco

    def calcular_dividendos(self, num_cotas: int) -> float:
        return num_cotas * self.preco_cota * self.rendimento_mensal


@dataclass
class Mercado:
    ativos: Dict[str, float]
    fundos_imobiliarios: Dict[str, FundoImobiliario] = field(default_factory=dict)
    historico_inflacao: List[float] = field(default_factory=list)

    def registrar_inflacao(self, taxa_inflacao):
        self.historico_inflacao.append(taxa_inflacao)
        print(f"[MERCADO] Registrada inflação de {taxa_inflacao:.4%} na rodada.")

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


def main() -> None:
    """
    Função principal que executa a simulação do mercado financeiro.

    Esta função cria e inicializa o mercado, agentes e outros componentes necessários
    para simular um mercado financeiro. A simulação é realizada ao longo de um número
    definido de rodadas, onde a inflação é aplicada, ordens são geradas e executadas,
    e o patrimônio dos agentes é atualizado. Ao final, os resultados são apresentados
    em gráficos.

    Etapas:
        1. Configuração inicial do mercado e dos agentes.
        2. Registro e aplicação da inflação mensal.
        3. Atualização de vizinhos e geração de ordens por parte dos agentes.
        4. Execução de ordens no order book e atualização de preços.
        5. Atualização do patrimônio dos agentes.
        6. Cálculo do valor total do mercado em cada rodada.
        7. Pagamento de dividendos em intervalos definidos.
        8. Normalização dos históricos para consistência.
        9. Geração de gráficos para análise dos resultados.

    Parâmetros:
        Nenhum.

    Retorno:
        None
    """
    num_agentes = 10
    num_rodadas = 23

    # Configuração inicial do mercado
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
            carteira={"PETR4": random.randint(0, 50), "VALE3": random.randint(0, 50)},
            sentimento=random.uniform(-1, 1),
            expectativa=[40.0, 50.0, 60.0],
            conhecimento=random.choice(["alto", "médio", "baixo"]),
            literacia_financeira=random.uniform(0, 1),
            comportamento_especulador=random.uniform(0, 1),
            comportamento_ruido=random.uniform(0, 1),
            expectativa_inflacao=random.uniform(-0.02, 0.05),
        )
        for i in range(num_agentes)
    ]

    historico_precos = {ativo: [] for ativo in mercado.ativos.keys()}
    historico_precos.update(
        {fii.nome: [] for fii in mercado.fundos_imobiliarios.values()}
    )
    historico_patrimonios = {agente.nome: [] for agente in agentes}
    historico_valor_mercado = []  # Novo histórico para o valor total do mercado

    for rodada in range(num_rodadas):
        print(f"\n--- RODADA {rodada + 1} ---")

        # Definir a inflação para a rodada
        taxa_inflacao_mensal = random.gauss(
            0.005, 0.002
        )  # Média de 0.5% ao mês com desvio padrão de 0.2%
        mercado.registrar_inflacao(taxa_inflacao_mensal)
        aplicar_inflacao(mercado, taxa_inflacao_mensal)

        # Atualiza vizinhos e gera ordens
        for agente in agentes:
            agente.atualiza_vizinhos(agentes)
            gerar_e_adicionar_ordens(agente, mercado, order_book)

        # Executa ordens para ativos tradicionais e FIIs
        executar_ordens_e_atualizar_precos(mercado, order_book, historico_precos)

        # Atualiza patrimônio dos agentes
        atualizar_patrimonio_agentes(agentes, mercado, historico_patrimonios, rodada)

        # Calcula o valor total do mercado
        valor_total_mercado = calcular_valor_total_mercado(mercado, agentes)
        historico_valor_mercado.append(valor_total_mercado)

        # Pagamento de dividendos no dia 22
        if (rodada + 1) % 22 == 0:
            print(f"[DIVIDENDOS] Pagamento de dividendos no dia {rodada + 1}")
            pagar_dividendos(mercado, agentes)

    # Garante que todos os históricos estejam consistentes
    normalizar_historicos(historico_precos, historico_patrimonios, num_rodadas)

    # Cálculo de volatilidade e gráficos
    plotar_resultados(
        historico_precos,
        historico_patrimonios,
        historico_valor_mercado,
        num_rodadas,
        mercado.historico_inflacao,
    )


def aplicar_inflacao(mercado: Mercado, taxa_inflacao_mensal: float) -> None:
    """
    Aplica a taxa de inflação diária, derivada da taxa mensal, aos preços dos ativos e fundos imobiliários.

    A inflação afeta tanto os preços dos ativos quanto os fundos imobiliários,
    simulando a depreciação do valor do dinheiro ao longo das rodadas.

    :param mercado: Objeto do mercado contendo ativos e fundos imobiliários.
    :param taxa_inflacao_mensal: Taxa de inflação mensal (ex.: 0.005 para 0.5%).
    :return: None
    """
    taxa_inflacao_diaria = (1 + taxa_inflacao_mensal) ** (1 / 30) - 1
    print(
        f"[INFLAÇÃO] Aplicando taxa mensal de {taxa_inflacao_mensal:.2%} "
        f"(diária: {taxa_inflacao_diaria:.4%}) aos ativos."
    )
    for ativo in mercado.ativos.keys():
        preco_anterior = mercado.ativos[ativo]
        mercado.ativos[ativo] *= 1 + taxa_inflacao_diaria
        print(f" - {ativo}: {preco_anterior:.2f} -> {mercado.ativos[ativo]:.2f}")

    for fii in mercado.fundos_imobiliarios.values():
        preco_anterior = fii.preco_cota
        fii.preco_cota *= 1 + taxa_inflacao_diaria
        print(f" - {fii.nome}: {preco_anterior:.2f} -> {fii.preco_cota:.2f}")

    print(
        f"[INFLAÇÃO] Taxa mensal: {taxa_inflacao_mensal * 100:.2f}%, "
        f"Taxa diária aplicada: {taxa_inflacao_diaria * 100:.4f}%"
    )


def gerar_e_adicionar_ordens(
    agente: Agente, mercado: Mercado, order_book: OrderBook
) -> None:
    """
    Gera ordens de compra ou venda para os ativos e fundos imobiliários e as adiciona ao order book.

    Esta função reflete as decisões de negociação de um agente em relação ao mercado,
    levando em consideração os preços atuais e as expectativas do agente.

    :param agente: O agente que está realizando as ordens.
    :param mercado: Objeto do mercado com os preços dos ativos e fundos.
    :param order_book: O order book onde as ordens serão registradas.
    :return: None
    """

    for ativo, preco in mercado.ativos.items():
        ordem = agente.gerar_ordem(ativo, preco)
        order_book.adicionar_ordem(ordem)
        print(
            f"[DECISÃO] {agente.nome} {ordem.tipo.upper()} {ordem.quantidade} de {ativo} "
            f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
        )
    for fii_nome, fii in mercado.fundos_imobiliarios.items():
        ordem = agente.gerar_ordem(fii_nome, fii.preco_cota)
        order_book.adicionar_ordem(ordem)
        print(
            f"[DECISÃO] {agente.nome} {ordem.tipo.upper()} {ordem.quantidade} de {fii_nome} "
            f"por {'até' if ordem.tipo == 'compra' else 'pelo menos'} {ordem.preco_limite:.2f}"
        )


def executar_ordens_e_atualizar_precos(
    mercado: Mercado, order_book: OrderBook, historico_precos: Dict[str, List[float]]
) -> None:
    """
    Executa as ordens no order book e atualiza os preços dos ativos e fundos imobiliários.

    Esta função realiza a execução das ordens registradas, ajusta os preços dos ativos
    e registra os preços atualizados no histórico.

    :param mercado: Objeto do mercado onde os preços serão atualizados.
    :param order_book: O order book com as ordens a serem executadas.
    :param historico_precos: Dicionário para registrar os preços históricos de cada ativo.
    :return: None
    """

    for ativo in mercado.ativos.keys():
        print(f"[EXECUTANDO ORDENS] Para o ativo {ativo}")
        order_book.executar_ordens(ativo, mercado)
        historico_precos[ativo].append(mercado.ativos[ativo])
        print(f"[PREÇO ATUALIZADO] {ativo}: {mercado.ativos[ativo]:.2f}")

    for fii_nome, fii in mercado.fundos_imobiliarios.items():
        print(f"[EXECUTANDO ORDENS] Para o fundo imobiliário {fii_nome}")
        order_book.executar_ordens(fii_nome, mercado)
        historico_precos[fii_nome].append(fii.preco_cota)
        print(f"[PREÇO ATUALIZADO] {fii_nome}: {fii.preco_cota:.2f}")


def atualizar_patrimonio_agentes(
    agentes: List[Agente],
    mercado: Mercado,
    historico_patrimonios: Dict[str, List[float]],
    rodada: int,
) -> None:
    """
    Atualiza o patrimônio de cada agente com base nos preços atuais dos ativos e fundos imobiliários.

    Registra o patrimônio atualizado no histórico de patrimônio de cada agente.

    :param agentes: Lista de agentes cujos patrimônios serão atualizados.
    :param mercado: Objeto do mercado com os preços atuais dos ativos e fundos.
    :param historico_patrimonios: Dicionário que armazena o histórico de patrimônio de cada agente.
    :param rodada: Número da rodada atual da simulação.
    :return: None
    """

    print(f"\n[RESUMO DA RODADA {rodada + 1}]")
    for agente in agentes:
        agente.atualiza_patrimonio(mercado.ativos, mercado.fundos_imobiliarios)
        historico_patrimonios[agente.nome].append(agente.patrimonio[-1])
        print(
            f"{agente.nome}: Patrimônio: {agente.patrimonio[-1]:.2f} | Saldo: {agente.saldo:.2f} | "
            f"Carteira: {agente.carteira}"
        )


def calcular_valor_total_mercado(mercado: Mercado, agentes: List[Agente]) -> float:
    """
    Calcula o valor total do mercado com base nos ativos e fundos imobiliários possuídos pelos agentes.

    :param mercado: Objeto do mercado contendo os preços dos ativos e fundos.
    :param agentes: Lista de agentes com suas carteiras de ativos e fundos.
    :return: Valor total do mercado.
    """
    valor_total_mercado = sum(
        mercado.ativos[ativo] * sum(agente.carteira.get(ativo, 0) for agente in agentes)
        for ativo in mercado.ativos.keys()
    )
    valor_total_mercado += sum(
        mercado.fundos_imobiliarios[fii].preco_cota
        * sum(agente.carteira.get(fii, 0) for agente in agentes)
        for fii in mercado.fundos_imobiliarios.keys()
    )
    return valor_total_mercado


def pagar_dividendos(mercado: Mercado, agentes: List[Agente]) -> None:
    """
    Realiza o pagamento de dividendos dos fundos imobiliários para os agentes que possuem cotas.

    :param mercado: Objeto do mercado contendo os fundos imobiliários.
    :param agentes: Lista de agentes que receberão os dividendos.
    :return: None
    """
    print("\n[DIVIDENDOS] Pagamento de dividendos!")
    for fii_nome, fii in mercado.fundos_imobiliarios.items():
        for agente in agentes:
            num_cotas = agente.carteira.get(fii_nome, 0)
            if num_cotas > 0:
                dividendos = fii.calcular_dividendos(num_cotas)
                agente.saldo += dividendos
                print(
                    f"{agente.nome} recebeu R${dividendos:.2f} de dividendos de {fii_nome} ({num_cotas} cotas)."
                )


def normalizar_historicos(
    historico_precos: Dict[str, List[float]],
    historico_patrimonios: Dict[str, List[float]],
    num_rodadas: int,
) -> None:
    """
    Normaliza os históricos de preços e patrimônios para garantir consistência com o número de rodadas.

    :param historico_precos: Dicionário com os históricos de preços de cada ativo.
    :param historico_patrimonios: Dicionário com os históricos de patrimônio de cada agente.
    :param num_rodadas: Número total de rodadas da simulação.
    :return: None
    """
    for ativo, precos in historico_precos.items():
        historico_precos[ativo] = normalizar_tamanho(precos, num_rodadas)

    for agente, patrimonios in historico_patrimonios.items():
        historico_patrimonios[agente] = normalizar_tamanho(patrimonios, num_rodadas)


def normalizar_tamanho(
    lista: List[float], tamanho: int, valor_padrao: float = 0
) -> List[float]:
    """
    Ajusta o tamanho de uma lista, preenchendo com um valor padrão se necessário.

    :param lista: Lista a ser normalizada.
    :param tamanho: Tamanho desejado da lista.
    :param valor_padrao: Valor padrão a ser usado para preencher a lista.
    :return: Lista normalizada.
    """
    while len(lista) < tamanho:
        lista.append(lista[-1] if lista else valor_padrao)
    if len(lista) > tamanho:
        lista = lista[:tamanho]
    return lista


def plotar_resultados(
    historico_precos: Dict[str, List[float]],
    historico_patrimonios: Dict[str, List[float]],
    historico_valor_mercado: List[float],
    num_rodadas: int,
    historico_inflacao: List[float],
) -> None:
    """
    Gera gráficos para visualizar os resultados da simulação, incluindo preços, patrimônio, valor total do mercado e inflação.

    :param historico_precos: Dicionário com o histórico de preços dos ativos e fundos.
    :param historico_patrimonios: Dicionário com o histórico de patrimônio de cada agente.
    :param historico_valor_mercado: Lista com o valor total do mercado ao longo das rodadas.
    :param num_rodadas: Número total de rodadas da simulação.
    :param historico_inflacao: Lista com o histórico de inflação registrada em cada rodada.
    :return: None
    """

    plt.figure(figsize=(12, 12))

    # Gráfico 1: Evolução dos preços
    plt.subplot(5, 1, 1)
    for ativo, precos in historico_precos.items():
        plt.plot(range(num_rodadas), precos, label=ativo)
    plt.xlabel("Rodadas")
    plt.ylabel("Preços")
    plt.title("Evolução dos Preços dos Ativos e FIIs")
    plt.legend()
    plt.grid(True)

    # Gráfico 2: Variações percentuais nos preços
    plt.subplot(5, 1, 2)
    for ativo, precos in historico_precos.items():
        variacoes = [
            100 * (precos[i] - precos[i - 1]) / precos[i - 1] if i > 0 else 0
            for i in range(len(precos))
        ]
        plt.plot(range(num_rodadas), variacoes, label=f"Variação {ativo}")
    plt.xlabel("Rodadas")
    plt.ylabel("Variação Percentual (%)")
    plt.title("Variações Percentuais nos Preços dos Ativos e FIIs")
    plt.legend()
    plt.grid(True)

    # Gráfico 3: Distribuição de patrimônio
    plt.subplot(5, 1, 3)
    for agente, patrimonios in historico_patrimonios.items():
        plt.plot(range(num_rodadas), patrimonios, label=agente)
    plt.xlabel("Rodadas")
    plt.ylabel("Patrimônio")
    plt.title("Distribuição de Patrimônio entre os Agentes")
    plt.legend()
    plt.grid(True)

    # Gráfico 4: Valor total do mercado
    plt.subplot(5, 1, 4)
    plt.plot(
        range(num_rodadas), historico_valor_mercado, label="Valor Total do Mercado"
    )
    plt.xlabel("Rodadas")
    plt.ylabel("Valor Total do Mercado")
    plt.title("Evolução do Valor Total do Mercado")
    plt.legend()
    plt.grid(True)

    # Gráfico 5: Inflação
    plt.subplot(5, 1, 5)
    plt.plot(
        range(num_rodadas),
        [inflacao * 100 for inflacao in historico_inflacao],
        label="Inflação (%)",
    )
    plt.xlabel("Rodadas")
    plt.ylabel("Inflação (%)")
    plt.title("Evolução da Inflação")
    plt.legend()
    plt.grid(True)

    # Ajustar o layout do gráfico
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Reduz o impacto de "overlap"
    plt.show()


if __name__ == "__main__":
    main()
