import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

# Simulando dados para dois agentes (caixa e portfólio)
rodadas = list(range(1, 31))
dados_agentes = {
    "Agente 1": {
        "caixa": [
            9949.81,
            9999.64,
            9949.61,
            9899.27,
            9849.06,
            9898.75,
            9948.55,
            9998.50,
            9998.50,
            9948.09,
            9897.64,
            9847.41,
            9797.34,
            9747.22,
            9697.18,
            9646.55,
            9596.34,
            9646.09,
            9696.01,
            9745.93,
            9695.62,
            9745.29,
            9794.78,
            9744.73,
            9694.64,
            9744.31,
            9694.07,
            9743.91,
            9693.38,
            9743.15,
        ],
        "portfolio": [
            1,
            0,
            1,
            2,
            3,
            2,
            1,
            0,
            0,
            1,
            2,
            3,
            4,
            5,
            6,
            7,
            8,
            7,
            6,
            5,
            6,
            5,
            4,
            5,
            6,
            5,
            6,
            5,
            6,
            5,
        ],
    },
    "Agente 2": {
        "caixa": [
            10000,
            9949.43,
            9999.69,
            10000,
            9999.75,
            10000,
            9949.43,
            9899.45,
            9849.36,
            9799.39,
            9797.71,
            9747.67,
            9697.22,
            9747.15,
            9797.02,
            9846.85,
            9796.77,
            9746.72,
            9696.48,
            9746.37,
            9696.15,
            9746.09,
            9745.95,
            9745.71,
            9795.63,
            9745.44,
            9795.07,
            9844.65,
            9794.61,
            9844.39,
        ],
        "portfolio": [
            0,
            1,
            0,
            0,
            0,
            0,
            2,
            1,
            3,
            2,
            4,
            5,
            6,
            5,
            4,
            3,
            4,
            5,
            6,
            5,
            6,
            5,
            6,
            5,
            4,
            5,
            4,
            3,
            4,
            3,
        ],
    },
}

# DataFrame
df_agentes = pd.DataFrame(
    {
        "Rodadas": rodadas,
        "Caixa_Agente1": dados_agentes["Agente 1"]["caixa"],
        "Portfolio_Agente1": dados_agentes["Agente 1"]["portfolio"],
        "Caixa_Agente2": dados_agentes["Agente 2"]["caixa"],
        "Portfolio_Agente2": dados_agentes["Agente 2"]["portfolio"],
    }
)

# Gráficos
fig, axes = plt.subplots(2, 2, figsize=(15, 10))

# Caixa
axes[0, 0].plot(df_agentes["Rodadas"], df_agentes["Caixa_Agente1"], label="Agente 1")
axes[0, 0].plot(df_agentes["Rodadas"], df_agentes["Caixa_Agente2"], label="Agente 2")
axes[0, 0].set_title("Evolução do Caixa")
axes[0, 0].set_xlabel("Rodadas")
axes[0, 0].set_ylabel("Caixa")
axes[0, 0].legend()

# Portfólio
axes[0, 1].plot(
    df_agentes["Rodadas"], df_agentes["Portfolio_Agente1"], label="Agente 1"
)
axes[0, 1].plot(
    df_agentes["Rodadas"], df_agentes["Portfolio_Agente2"], label="Agente 2"
)
axes[0, 1].set_title("Evolução do Portfólio")
axes[0, 1].set_xlabel("Rodadas")
axes[0, 1].set_ylabel("Portfólio")
axes[0, 1].legend()

# Comparação inicial e final do caixa
axes[1, 0].bar(
    ["Inicial", "Final"],
    [10000, df_agentes["Caixa_Agente1"].iloc[-1]],
    label="Agente 1",
)
axes[1, 0].bar(
    ["Inicial", "Final"],
    [10000, df_agentes["Caixa_Agente2"].iloc[-1]],
    label="Agente 2",
)
axes[1, 0].set_title("Comparação Caixa Inicial vs Final")
axes[1, 0].set_ylabel("Caixa")
axes[1, 0].legend()

# Diferença de portfólio entre rodadas
axes[1, 1].plot(
    df_agentes["Rodadas"],
    np.diff([0] + df_agentes["Portfolio_Agente1"].tolist()),
    label="Agente 1",
)
axes[1, 1].plot(
    df_agentes["Rodadas"],
    np.diff([0] + df_agentes["Portfolio_Agente2"].tolist()),
    label="Agente 2",
)
axes[1, 1].set_title("Variação no Portfólio por Rodada")
axes[1, 1].set_xlabel("Rodadas")
axes[1, 1].set_ylabel("Δ Portfólio")
axes[1, 1].legend()

plt.tight_layout()
plt.show()
