from dataclasses import dataclass, field
from typing import List, Dict
import random
import math
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mercado import Mercado
    from .order_book import OrderBook
    from .fundo_imobiliario import FundoImobiliario
    
from .ordem import Ordem
import numpy as np


@dataclass
class Agente:
    """
    Classe que representa um agente do mercado.

    Um agente possui características financeiras e comportamentais que influenciam
    suas decisões de compra e venda no mercado. Ele mantém um saldo, uma carteira de
    ativos, e parâmetros como literacia financeira, comportamento especulador e
    expectativa de inflação, que moldam sua interação com o mercado.

    Atributos:
        nome (str): Nome do agente.
        saldo (float): Saldo disponível em caixa.
        carteira (Dict[str, int]): Quantidade de ativos que o agente possui,
            mapeados por nome.
        sentimento (float): Sentimento do agente, representado como um valor
            entre -1 (negativo) e 1 (positivo).
        expectativa (List[float]): Lista contendo os valores mínimo, esperado e
            máximo de preço para os ativos.
        conhecimento (str): Nível de conhecimento financeiro do agente (e.g.,
            "alto", "médio", "baixo").
        literacia_financeira (float): Representa o conhecimento financeiro, com
            valor entre 0 e 1.
        comportamento_especulador (float): Grau de especulação do agente, valor
            entre 0 e 1.
        comportamento_ruido (float): Impacto do ruído nas decisões do agente,
            valor entre 0 e 1.
        expectativa_inflacao (float): Expectativa do agente em relação à inflação.
        patrimonio (List[float]): Histórico do patrimônio do agente ao longo do tempo.
        tau (int): Tempo de observação usado para cálculo da volatilidade percebida.
        volatilidade_percebida (float): Volatilidade percebida pelo agente com base
            no histórico de preços.
    """
    nome: str
    saldo: float
    carteira: Dict[str, int]
    sentimento: float
    expectativa: List[float]
    conhecimento: str
    literacia_financeira: (float)
    comportamento_especulador: (float)
    comportamento_ruido: float
    expectativa_inflacao: float
    patrimonio: List[float] = field(default_factory=list)
    tau: int = field(init=False)
    volatilidade_percebida: float = field(default=0.0, init=False)

    def __post_init__(self) -> None:
        """
        Inicializa atributos dinâmicos após a criação do agente.

        Define o tempo de observação (`tau`) como um valor aleatório entre 22 e 252,
        representando o número de períodos que o agente considera ao calcular a
        volatilidade percebida.

        Returns:
            None
        """
        self.tau = random.randint(22, 252)  # Sorteio do tempo observado.

    def calcular_volatilidade_percebida(self, historico_precos: List[float]) -> None:
        """
        Calcula a volatilidade percebida com base no histórico de preços.

        Este método utiliza o logaritmo natural dos retornos (log-returns) para
        calcular a volatilidade como o desvio padrão dos retornos no período observado
        (`tau`). Caso o histórico de preços seja menor que `tau`, a volatilidade
        percebida é definida como 0.

        Args:
            historico_precos (List[float]): Lista de preços históricos do ativo.

        Returns:
            None
        """
        if len(historico_precos) >= self.tau:
            retornos = [
                math.log(historico_precos[i] / historico_precos[i - 1])
                for i in range(1, self.tau)
            ]
            self.volatilidade_percebida = np.std(retornos)
        else:
            self.volatilidade_percebida = 0.0

    def calcular_risco_desejado(self) -> float:
        """
        Calcula o nível de risco que o agente está disposto a assumir.

        O risco desejado é calculado com base em:
        - Sentimento do agente: quanto mais positivo, maior o risco.
        - Volatilidade percebida do ativo.
        - Nível de literacia financeira: reduz o impacto do risco base.
        - Fatores comportamentais (especulação e ruído).

        Returns:
            float: Valor do risco desejado pelo agente.
        """
        risco_base = (
            (self.sentimento + 1)
            * self.volatilidade_percebida
            / (2 + self.literacia_financeira)
        )
        fator_especulacao = self.comportamento_especulador * 0.2
        fator_ruido = self.comportamento_ruido * 0.1
        return risco_base + fator_especulacao - fator_ruido

    def ajustar_preco_por_inflacao(self, preco: float) -> float:
        """
        Ajusta o preço de um ativo com base na expectativa de inflação do agente.

        O ajuste considera o nível de confiança do agente, derivado da sua literacia
        financeira e do impacto do comportamento de ruído. Um agente com maior confiança
        ajustará menos o preço, enquanto agentes com maior impacto de ruído terão ajustes
        mais conservadores.

        Args:
            preco (float): Preço original do ativo.

        Returns:
            float: Preço ajustado com base na inflação e na confiança do agente.
        """
        confianca = max(0.5, self.literacia_financeira - self.comportamento_ruido)
        return preco * (1 + self.expectativa_inflacao * confianca)

    def calcular_quantidade_baseada_em_risco(self, risco_desejado: float) -> float:
        """
        Calcula a quantidade de ativos que o agente deseja negociar, com base no risco desejado.

        A quantidade é proporcional ao risco desejado e inversamente proporcional à volatilidade
        percebida. Caso a volatilidade percebida seja zero, retorna 0 para evitar divisão por zero.

        Args:
            risco_desejado (float): Nível de risco que o agente está disposto a assumir.

        Returns:
            float: Quantidade calculada com base no risco desejado.
        """
        if self.volatilidade_percebida > 0:
            return risco_desejado / self.volatilidade_percebida
        return 0.0

    def tomar_decisao(self, mercado: "Mercado", order_book: "OrderBook") -> None:
        """
        Toma uma decisão de compra ou venda de ativos no mercado com base nos
        parâmetros do agente e nas condições de mercado.

        Para cada ativo disponível no mercado, o agente calcula a volatilidade percebida
        e determina o risco desejado. A decisão é ajustada com base na expectativa de
        inflação e em parâmetros comportamentais, como comportamento especulador.

        Dependendo da probabilidade gerada, o agente pode:
        - Comprar uma quantidade do ativo, respeitando seu saldo e os limites de preço.
        - Vender uma quantidade do ativo de sua carteira, considerando os limites de preço.

        Caso a expectativa de inflação seja maior que 3% ao mês, o agente pode optar por
        não realizar nenhuma transação para certos ativos.

        Args:
            mercado (Mercado): Objeto que representa o mercado contendo ativos,
                fundos imobiliários e seus preços atuais.
            order_book (OrderBook): Objeto que registra as ordens de compra e venda
                realizadas pelos agentes.

        Returns:
            None
        """
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
        """
        Calcula a taxa de crescimento percentual do patrimônio do agente
        nos últimos 22 períodos.

        O cálculo é baseado na relação entre o patrimônio atual (t) e o
        patrimônio de 22 períodos atrás (t-22). Se o histórico do patrimônio
        for insuficiente ou se o patrimônio de t-22 for zero, retorna 0.0.

        Returns:
            float: A taxa de crescimento percentual do patrimônio, expressa como
            um valor decimal (ex.: 0.05 representa 5% de crescimento). Retorna
            0.0 se o histórico for insuficiente ou se o patrimônio de t-22 for zero.
        """
        if len(self.patrimonio) > 22:
            patrimonio_t = self.patrimonio[-1]
            patrimonio_t_22 = self.patrimonio[-22]
            # Evita divisão por zero
            if patrimonio_t_22 != 0:
                return (patrimonio_t / patrimonio_t_22) - 1
        return 0.0

    def calcula_l_social(self) -> float:
        """
        Calcula a média da taxa de crescimento percentual do patrimônio
        (`l_privada`) dos vizinhos do agente.

        Para cada vizinho, a função considera o resultado de `calcula_l_privada`.
        Se nenhum vizinho tiver um histórico suficiente para o cálculo, ou se
        a lista de vizinhos estiver vazia, retorna 0.0.

        Returns:
            float: A média da taxa de crescimento percentual dos patrimônios dos
            vizinhos, expressa como um valor decimal (ex.: 0.03 representa 3% de
            crescimento). Retorna 0.0 se a lista de vizinhos estiver vazia ou se
            nenhum vizinho tiver histórico suficiente.
        """
        if self.vizinhos:
            l_privada_vizinhos = [
                vizinho.calcula_l_privada() for vizinho in self.vizinhos
                if len(vizinho.patrimonio) > 22  # Garante que o vizinho tenha histórico suficiente
            ]
            if l_privada_vizinhos:  # Evita divisão por zero caso a lista fique vazia
                return sum(l_privada_vizinhos) / len(l_privada_vizinhos)
        return 0.0

    def sorteia_news(self) -> float:
        """
        Gera um valor aleatório para representar o impacto de notícias no sentimento do agente.

        Utiliza uma distribuição normal com média 0 e desvio padrão 1, simulando o ruído
        causado por informações externas.

        Returns:
            float: Valor aleatório gerado para o impacto de notícias.
        """
        return random.gauss(0, 1)

    def atualiza_sentimento(self) -> None:
        """
        Atualiza o sentimento do agente com base em fatores privados, sociais e externos.

        O sentimento bruto é calculado considerando:
        - L_private: Retorno privado do agente com base em sua carteira.
        - L_social: Influência média dos vizinhos.
        - Impacto de notícias (news): Fator externo aleatório.

        O valor final do sentimento é limitado entre -1 (pessimismo extremo) e 1 (otimismo extremo).

        Returns:
            None
        """
        l_privada = self.calcula_l_privada()
        l_social = self.calcula_l_social()
        news = self.sorteia_news()
        sentimento_bruto = 0.2 * l_privada + 0.3 * l_social + 0.05 * news
        self.sentimento = max(-1, min(1, sentimento_bruto))

    def calcula_preco_expectativa(self, preco_mercado: float) -> float:
        """
        Calcula o preço esperado de um ativo com base no sentimento e nos ajustes comportamentais do agente.

        O cálculo considera:
        - Sentimento do agente: impacto direto no ajuste do preço.
        - Literacia financeira: aumenta a precisão da expectativa.
        - Comportamento especulador: reduz a precisão devido a especulações.

        Args:
            preco_mercado (float): Preço atual de mercado do ativo.

        Returns:
            float: Preço esperado pelo agente.
        """
        ajuste_literacia = self.literacia_financeira * 0.1
        ajuste_comportamento = self.comportamento_especulador * 0.15
        return preco_mercado * math.exp(
            (self.sentimento + ajuste_literacia - ajuste_comportamento) / 10
        )

    def gerar_ordem(self, ativo: str, preco_mercado: float) -> "Ordem":
        """
        Gera uma ordem de compra ou venda para um ativo com base no comportamento e no sentimento do agente.

        O processo inclui:
        - Atualização do sentimento do agente.
        - Ajuste do preço com base na inflação.
        - Cálculo do preço esperado, com variação aleatória proporcional ao comportamento de ruído.
        - Definição da quantidade com base no risco desejado.
        - Determinação do tipo de ordem (compra ou venda) com base no sentimento.

        Args:
            ativo (str): Nome do ativo.
            preco_mercado (float): Preço atual de mercado do ativo.

        Returns:
            Ordem: Objeto representando a ordem gerada pelo agente.
        """
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
        """
        Atualiza a lista de vizinhos do agente com base em uma amostra aleatória de outros agentes.

        Esta função simula a interação social do agente, permitindo que ele seja influenciado
        por um subconjunto de outros agentes no mercado.

        Args:
            agentes (List["Agente"]): Lista de todos os agentes disponíveis no mercado.
            max_vizinhos (int): Número máximo de vizinhos a serem selecionados. Padrão: 3.

        Returns:
            None
        """
        self.vizinhos = random.sample(agentes, min(len(agentes), max_vizinhos))

    def atualiza_patrimonio(
        self,
        precos_mercado: Dict[str, float],
        fundos_imobiliarios: Dict[str, "FundoImobiliario"],
    ) -> None:
        """
        Atualiza o patrimônio total do agente com base no saldo, na carteira de ativos
        e na valorização de fundos imobiliários.

        O cálculo inclui:
        - Valor dos ativos: Quantidade de cada ativo na carteira multiplicada pelo preço atual de mercado.
        - Valor dos fundos imobiliários: Quantidade de cotas do fundo multiplicada pelo preço atual da cota.
        - Saldo disponível do agente.

        O patrimônio atualizado é armazenado no histórico do agente.

        Args:
            precos_mercado (Dict[str, float]): Dicionário contendo os preços atuais de mercado dos ativos.
            fundos_imobiliarios (Dict[str, FundoImobiliario]): Dicionário contendo os fundos imobiliários e seus preços.

        Returns:
            None
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
        self.patrimonio.append(self.saldo + valor_ativos + valor_fundos)
