import random
from classes.mercado import Mercado
from classes.agente import Agente
from classes.order_book import OrderBook
from classes.fundo_imobiliario import FundoImobiliario
from utils.graficos import plotar_resultados
from utils.funcoes_mercado import aplicar_inflacao, gerar_e_adicionar_ordens, executar_ordens_e_atualizar_precos, atualizar_patrimonio_agentes, calcular_valor_total_mercado, pagar_dividendos
from utils.normalizacao import normalizar_historicos

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
    num_rodadas = 67

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
            literacia_financeira=random.uniform(0, 1),
            comportamento_especulador=random.uniform(0, 1),
            comportamento_fundamentalista=random.uniform(0, 1),
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

if __name__ == "__main__":
    main()
