from classes.mercado import Mercado
from classes.agente import Agente
from classes.order_book import OrderBook
from typing import List, Dict

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
