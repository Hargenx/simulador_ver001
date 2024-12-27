import matplotlib.pyplot as plt
from typing import Dict, List

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
