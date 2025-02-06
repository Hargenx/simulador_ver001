import numpy as np
import random
import matplotlib.pyplot as plt
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ==========================================
# Classes de Microestrutura de Mercado
# ==========================================


@dataclass
class Ordem:
    tipo: str  # "compra" ou "venda"
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
        self.comprador.carteira[self.ativo] = (
            self.comprador.carteira.get(self.ativo, 0) + self.quantidade
        )
        if self.ativo in self.vendedor.carteira:
            self.vendedor.carteira[self.ativo] -= self.quantidade
            if self.vendedor.carteira[self.ativo] <= 0:
                del self.vendedor.carteira[self.ativo]


@dataclass
class OrderBook:
    ordens_compra: Dict[str, List[Ordem]] = field(default_factory=dict)
    ordens_venda: Dict[str, List[Ordem]] = field(default_factory=dict)

    def adicionar_ordem(self, ordem: Ordem) -> None:
        if ordem.tipo == "compra":
            self.ordens_compra.setdefault(ordem.ativo, []).append(ordem)
        elif ordem.tipo == "venda":
            self.ordens_venda.setdefault(ordem.ativo, []).append(ordem)

    def executar_ordens(self, ativo: str, mercado: "Mercado") -> None:
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
                    mercado.fii.preco_cota = preco_execucao
                    ordem_compra.quantidade -= quantidade_exec
                    ordem_venda.quantidade -= quantidade_exec
                    if ordem_compra.quantidade == 0:
                        self.ordens_compra[ativo].pop(0)
                    if ordem_venda.quantidade == 0:
                        self.ordens_venda[ativo].pop(0)
                else:
                    break


# ==========================================
# Classes do ABM
# ==========================================


class BancoCentral:
    def __init__(self, taxa_selic, expectativa_inflacao, premio_risco):
        self.taxa_selic = taxa_selic
        self.expectativa_inflacao = expectativa_inflacao
        self.premio_risco = premio_risco


class Midia:
    @staticmethod
    def gerar_noticia():
        return random.uniform(-3, 3)


class Imovel:
    def __init__(self, valor, aluguel, vacancia, custo_manutencao):
        self.valor = valor
        self.aluguel = aluguel
        self.vacancia = vacancia
        self.custo_manutencao = custo_manutencao

    def gerar_fluxo_aluguel(self):
        return self.aluguel * (1 - self.vacancia)


class Agente:
    def __init__(self, id, literacia_financeira, comportamento, caixa, cotas):
        self.id = id
        self.LF = literacia_financeira
        self.comportamento = comportamento
        self.caixa = caixa
        self.cotas = cotas

        self.saldo = caixa
        self.carteira = {"FII": cotas}

        self.sentimento = 0
        self.RD = 0
        self.percentual_alocacao = 0

        self.expectativa_inflacao = 0
        self.expectativa_premio = 0

        self.historico_precos = []
        self.retornos_dia = []
        self.historico_riqueza = [caixa + cotas * 100]
        self.dividendos_recebidos = 0

    def atualizar_caixa(self, taxa_selic, dividendos):
        self.caixa += self.caixa * taxa_selic
        self.caixa += dividendos

    def calcular_sentimento_risco_alocacao(self, mercado, vizinhos, parametros):
        I_privado = random.uniform(0, 1)
        I_social = sum([v.LF for v in vizinhos]) / len(vizinhos)
        volatilidade_percebida = mercado.volatilidade_historica

        a_i = parametros["a0"] + parametros["alpha"] * self.LF
        b_i = parametros["b0"] - parametros["gamma"] * self.LF
        c_i = parametros["c0"] - parametros["delta"] * self.LF

        S_bruto = a_i * I_privado + b_i * I_social + c_i * mercado.news
        self.sentimento = max(min(S_bruto, 1), -1)
        self.RD = (self.sentimento + 1) / 2 * volatilidade_percebida
        if volatilidade_percebida > 0:
            self.percentual_alocacao = self.RD / volatilidade_percebida
        else:
            self.percentual_alocacao = 0

    def calcular_expectativa_inflacao(self, mercado, noticias):
        impacto_news = noticias / 10
        self.expectativa_inflacao = mercado.expectativa_inflacao + impacto_news

    def calcular_expectativa_premio(self, mercado):
        self.expectativa_premio = mercado.banco_central.premio_risco * (
            1 + self.sentimento * mercado.volatilidade_historica
        )

    def calcular_estatisticas_retoricas(self):
        if len(self.historico_precos) < 2:
            return None
        retornos = [
            (self.historico_precos[i] - self.historico_precos[i - 1])
            / self.historico_precos[i - 1]
            for i in range(1, len(self.historico_precos))
        ]
        media_retorno = np.mean(retornos)
        volatilidade = np.std(retornos)
        sharpe_ratio = media_retorno / volatilidade if volatilidade > 0 else 0
        return {
            "media_retorno": media_retorno,
            "volatilidade": volatilidade,
            "sharpe_ratio": sharpe_ratio,
        }

    def calcular_retornos_dia(self, preco_atual):
        if self.historico_precos:
            preco_anterior = self.historico_precos[-1]
            retorno = (preco_atual - preco_anterior) / preco_anterior
            self.retornos_dia.append(retorno)
        self.historico_precos.append(preco_atual)

    def atualizar_historico(self, preco_fii):
        riqueza_atual = self.caixa + self.carteira.get("FII", 0) * preco_fii
        self.historico_riqueza.append(riqueza_atual)

    def criar_ordem(self, mercado) -> Optional[Ordem]:
        ativo = "FII"
        preco_mercado = mercado.fii.preco_cota
        patrimonio = self.saldo + self.carteira.get(ativo, 0) * preco_mercado
        alocacao_atual = (
            (self.carteira.get(ativo, 0) * preco_mercado) / patrimonio
            if patrimonio > 0
            else 0
        )
        alocacao_desejada = 0.4

        if alocacao_atual < alocacao_desejada * 0.9 and self.saldo >= preco_mercado:
            if self.sentimento > 0.1 or random.random() < 0.3:
                preco_limite = preco_mercado * (1 + random.uniform(0, 0.02))
                return Ordem(
                    tipo="compra",
                    agente=self,
                    ativo=ativo,
                    preco_limite=preco_limite,
                    quantidade=1,
                )
        elif (
            alocacao_atual > alocacao_desejada * 1.1 and self.carteira.get(ativo, 0) > 0
        ):
            if self.sentimento < -0.1 or random.random() < 0.3:
                preco_limite = preco_mercado * (1 - random.uniform(0, 0.02))
                return Ordem(
                    tipo="venda",
                    agente=self,
                    ativo=ativo,
                    preco_limite=preco_limite,
                    quantidade=1,
                )
        if self.carteira.get(ativo, 0) > 0 and random.random() < 0.05:
            preco_limite = preco_mercado * (1 - random.uniform(0, 0.01))
            return Ordem(
                tipo="venda",
                agente=self,
                ativo=ativo,
                preco_limite=preco_limite,
                quantidade=1,
            )
        return None


class FII:
    def __init__(self, num_cotas, caixa):
        self.num_cotas = num_cotas
        self.caixa = caixa
        self.imoveis = []
        self.retornos_diarios = []
        self.preco_cota = 100

    def adicionar_imovel(self, imovel):
        self.imoveis.append(imovel)

    def calcular_fluxo_aluguel(self):
        return sum(imovel.gerar_fluxo_aluguel() for imovel in self.imoveis)

    def distribuir_dividendos(self):
        fluxo_aluguel = self.calcular_fluxo_aluguel()
        dividendos = fluxo_aluguel / self.num_cotas if self.num_cotas > 0 else 0
        self.caixa += fluxo_aluguel
        return dividendos

    def atualizar_caixa_para_despesas(self, despesas):
        self.caixa -= despesas
        if self.caixa < 0:
            self.caixa = 0

    def realizar_investimento(self, valor):
        if self.caixa >= valor:
            self.caixa -= valor
        else:
            raise ValueError("Caixa insuficiente para realizar o investimento.")

    def calcular_retorno_diario(self, novo_preco_cota):
        if self.preco_cota > 0:
            retorno = (novo_preco_cota - self.preco_cota) / self.preco_cota
            self.retornos_diarios.append(retorno)
        self.preco_cota = novo_preco_cota

    def obter_estatisticas_retornos(self):
        if not self.retornos_diarios:
            return None
        media_retorno = np.mean(self.retornos_diarios)
        volatilidade = np.std(self.retornos_diarios)
        return {"media_retorno": media_retorno, "volatilidade": volatilidade}


class Mercado:
    def __init__(self, agentes, fii, banco_central, midia):
        self.agentes = agentes
        self.fii = fii
        self.banco_central = banco_central
        self.midia = midia
        self.volatilidade_historica = 0.1
        self.news = 0
        self.order_book = OrderBook()

    def executar_dia(self, parametros):
        self.news = self.midia.gerar_noticia()
        for agente in self.agentes:
            agente.calcular_sentimento_risco_alocacao(self, self.agentes, parametros)
            agente.calcular_expectativa_inflacao(self.banco_central, self.news)
            agente.calcular_expectativa_premio(self)
        self.processar_ordens()
        for agente in self.agentes:
            agente.atualizar_historico(self.fii.preco_cota)
        self.fii.distribuir_dividendos()
        self.fii.atualizar_caixa_para_despesas(2000)
        self.atualizar_volatilidade_historica()

    def atualizar_volatilidade_historica(self):
        if len(self.fii.retornos_diarios) > 1:
            self.volatilidade_historica = np.std(self.fii.retornos_diarios)

    def processar_ordens(self):
        for agente in self.agentes:
            ordem = agente.criar_ordem(self)
            if ordem:
                self.order_book.adicionar_ordem(ordem)
        # Se houver ambas as ordens, tente casar
        if self.order_book.ordens_compra.get(
            "FII"
        ) and self.order_book.ordens_venda.get("FII"):
            self.order_book.executar_ordens("FII", self)
        else:
            # Força uma pequena atualização se não houver transação
            novo_preco = self.fii.preco_cota * (1 + random.uniform(-0.005, 0.005))
            self.fii.calcular_retorno_diario(novo_preco)
        # Limpa o order book para o próximo dia
        self.order_book = OrderBook()


# ==========================================
# Função de Simulação e Plotagem
# ==========================================
def simular_mercado_e_plotar():
    # Criação dos agentes com heterogeneidade: o agente 0 inicia com 20 cotas
    agentes = []
    for i in range(5):
        cotas_iniciais = 20 if i == 0 else 10
        agente = Agente(
            id=i,
            literacia_financeira=random.uniform(0.5, 1.0),
            comportamento="fundamentalista",
            caixa=10000,
            cotas=cotas_iniciais,
        )
        agentes.append(agente)
    # Criação do FII e adição de imóveis
    fii = FII(num_cotas=1000, caixa=50000)
    fii.adicionar_imovel(
        Imovel(valor=100000, aluguel=5000, vacancia=0.1, custo_manutencao=200)
    )
    fii.adicionar_imovel(
        Imovel(valor=200000, aluguel=8000, vacancia=0.2, custo_manutencao=500)
    )
    # Criação do Banco Central e da Mídia
    banco_central = BancoCentral(
        taxa_selic=0.02, expectativa_inflacao=0.03, premio_risco=0.05
    )
    midia = Midia()
    # Criação do Mercado
    mercado = Mercado(
        agentes=agentes, fii=fii, banco_central=banco_central, midia=midia
    )
    # Parâmetros do modelo
    parametros = {
        "a0": 0.5,
        "b0": 0.3,
        "c0": 0.2,
        "alpha": 0.1,
        "gamma": 0.05,
        "delta": 0.02,
    }
    historico_precos_fii = []
    num_dias = 252  # Aproximadamente 1 ano de negociação
    for _ in range(num_dias):
        mercado.executar_dia(parametros)
        historico_precos_fii.append(mercado.fii.preco_cota)
    historico_precos_fii = np.array(historico_precos_fii)
    log_returns = np.diff(np.log(historico_precos_fii))
    window = 20
    volatilidade_rolante = np.full_like(log_returns, np.nan)
    for i in range(window, len(log_returns)):
        volatilidade_rolante[i] = np.std(log_returns[i - window : i])
    print("Preço Final da Cota:", fii.preco_cota)
    print("Caixa Final do FII:", fii.caixa)
    print("Retornos Diários do FII:", fii.retornos_diarios)
    for agente in agentes:
        print(
            f"Agente {agente.id}: Caixa: {agente.caixa}, Sentimento: {agente.sentimento}, Riqueza: {agente.historico_riqueza[-1]}"
        )
    dias = np.arange(num_dias)
    fig, ax = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    ax[0].plot(dias, historico_precos_fii, label="Preço da Cota do FII")
    ax[0].set_title("Evolução do Preço do FII")
    ax[0].set_ylabel("Preço")
    ax[0].legend()
    ax[1].plot(
        dias[1:],
        volatilidade_rolante,
        label="Volatilidade Rolante (20 dias)",
        color="orange",
    )
    ax[1].set_title("Volatilidade Rolante dos Retornos Logarítmicos")
    ax[1].set_ylabel("Volatilidade")
    ax[1].set_xlabel("Dias")
    ax[1].legend()
    plt.tight_layout()
    plt.show()
    return historico_precos_fii, log_returns, volatilidade_rolante


# ----- Executa a Simulação e Plota os Resultados -----
simular_mercado_e_plotar()
