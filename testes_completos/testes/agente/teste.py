import unittest
import numpy as np

from agente import Agente

# Supondo que a classe Agente refatorada esteja disponível para importação.
# Caso esteja no mesmo diretório, pode-se fazer:
# from agente import Agente
# Para este exemplo, assumiremos que a classe Agente já foi definida conforme o código refatorado.

# =============================================================================
# Classes Dummy para simular os objetos dependentes
# =============================================================================


class DummyFundoImobiliario:
    def __init__(self, nome, historico_precos, dividendos=1.0):
        self.nome = nome
        self.historico_precos = historico_precos
        self.dividendos = dividendos

    def calcular_dividendos_cota(self):
        return self.dividendos


class DummyMercado:
    def __init__(self, ativos, historico_precos, fundos_imobiliarios):
        """
        ativos: dict mapping asset name to current price.
        historico_precos: dict mapping asset name to list of historical prices.
        fundos_imobiliarios: dict mapping asset name to DummyFundoImobiliario.
        """
        self.ativos = ativos
        self.historico_precos = historico_precos
        self.fundos_imobiliarios = fundos_imobiliarios


class DummyOrderBook:
    def __init__(self):
        self.ordens = []

    def adicionar_ordem(self, ordem):
        self.ordens.append(ordem)


# Se necessário, podemos definir também um DummyOrdem,
# mas como a classe Agente apenas instancia a ordem e a adiciona ao order book,
# basta verificarmos se a ordem foi adicionada.

# =============================================================================
# Testes Unitários para a classe Agente
# =============================================================================

# Supondo que a classe Agente já esteja definida conforme a versão refatorada:
# from agente import Agente
# Para este exemplo, a classe Agente deve estar disponível no ambiente de testes.


class TestAgente(unittest.TestCase):

    def setUp(self):
        # Cria um agente com parâmetros válidos
        self.agent = Agente(
            nome="Teste",
            saldo=10000.0,
            carteira={"FII1": 10},
            sentimento=0.0,
            expectativa=[90, 100, 110],
            literacia_financeira=0.5,
            comportamento_fundamentalista=0.5,
            comportamento_especulador=0.5,
            comportamento_ruido=0.5,
            expectativa_inflacao=0.02,
        )
        # Para garantir reprodutibilidade, fixamos tau para um valor conhecido
        self.agent.tau = 22

    def test_invalid_literacia_financeira(self):
        with self.assertRaises(ValueError):
            Agente(
                nome="Invalid",
                saldo=1000,
                carteira={},
                sentimento=0,
                expectativa=[0, 0, 0],
                literacia_financeira=1.5,  # valor inválido (> 1)
                comportamento_fundamentalista=0.5,
                comportamento_especulador=0.5,
                comportamento_ruido=0.5,
                expectativa_inflacao=0.02,
            )

    def test_invalid_sentimento(self):
        with self.assertRaises(ValueError):
            Agente(
                nome="Invalid",
                saldo=1000,
                carteira={},
                sentimento=2,  # valor inválido (maior que 1)
                expectativa=[0, 0, 0],
                literacia_financeira=0.5,
                comportamento_fundamentalista=0.5,
                comportamento_especulador=0.5,
                comportamento_ruido=0.5,
                expectativa_inflacao=0.02,
            )

    def test_calcular_volatilidade_percebida_insuficiente(self):
        # Histórico de preços menor que tau: deve definir volatilidade como 0
        historico_precos = [100] * (self.agent.tau - 1)
        self.agent.calcular_volatilidade_percebida(historico_precos)
        self.assertEqual(self.agent.volatilidade_percebida, 0.0)

    def test_calcular_volatilidade_percebida_suficiente(self):
        # Histórico com exatamente tau elementos (linearmente crescente)
        historico_precos = np.linspace(100, 120, self.agent.tau).tolist()
        self.agent.calcular_volatilidade_percebida(historico_precos)
        self.assertGreater(self.agent.volatilidade_percebida, 0)

    def test_calcular_risco_desejado(self):
        # Configura volatilidade e sentimento
        self.agent.volatilidade_percebida = 0.2
        self.agent.sentimento = 0.5
        risco = self.agent.calcular_risco_desejado()
        expected = (0.5 + 1) * 0.2 / 2
        self.assertAlmostEqual(risco, expected)

    def test_calcular_quantidade_baseada_em_risco(self):
        self.agent.volatilidade_percebida = 0.2
        risco_desejado = 0.3
        quantidade = self.agent.calcular_quantidade_baseada_em_risco(risco_desejado)
        expected = risco_desejado / 0.2
        self.assertAlmostEqual(quantidade, expected)

    def test_calcular_preco_especulativo(self):
        # Cria um fundo com histórico linearmente crescente
        historico_precos = [100 + i for i in range(30)]
        fundo = DummyFundoImobiliario("FII1", historico_precos)
        self.agent.tau = 20  # Ajusta tau para o teste
        preco_predito = self.agent.calcular_preco_especulativo(fundo)
        # Em uma tendência linear, o preço predito deve ser maior que o último valor observado
        self.assertGreater(preco_predito, historico_precos[-1])

    def test_calcular_expectativa_preco(self):
        historico_precos = [100 + i for i in range(30)]
        fundo = DummyFundoImobiliario("FII1", historico_precos, dividendos=2.0)
        self.agent.tau = 20
        expectativa = self.agent.calcular_expectativa_preco(fundo)
        # A expectativa não deve ser exatamente igual ao preço atual
        self.assertNotEqual(expectativa, historico_precos[-1])

    def test_tomar_decisao(self):
        # Configura um mercado dummy com um ativo e fundo correspondente
        historico_precos = [100 + i for i in range(30)]
        fundo = DummyFundoImobiliario("FII1", historico_precos, dividendos=2.0)
        ativos = {"FII1": historico_precos[-1]}
        mercado = DummyMercado(
            ativos=ativos,
            historico_precos={"FII1": historico_precos},
            fundos_imobiliarios={"FII1": fundo},
        )
        order_book = DummyOrderBook()
        # Garante que o agente possua o ativo na carteira e defina um patrimônio inicial
        self.agent.carteira = {"FII1": 10}
        self.agent.patrimonio = [10000]
        self.agent.tomar_decisao(mercado, order_book)
        # Verifica se alguma ordem foi adicionada ao order book
        self.assertGreater(len(order_book.ordens), 0)

    def test_atualizar_patrimonio(self):
        # Configura dados dummy para mercado e fundos
        precos_mercado = {"Ativo1": 50}
        historico_precos_fundo = [100 + i for i in range(30)]
        fundo = DummyFundoImobiliario("FII1", historico_precos_fundo, dividendos=2.0)
        fundos_imobiliarios = {"FII1": fundo}
        self.agent.carteira = {"Ativo1": 10, "FII1": 5}
        self.agent.saldo = 5000
        self.agent.atualizar_patrimonio(precos_mercado, fundos_imobiliarios)
        # Verifica se o patrimônio foi atualizado (lista não vazia)
        self.assertTrue(len(self.agent.patrimonio) > 0)

    def test_calcular_I_privada(self):
        # Cria um histórico de patrimônio com mais de 22 registros
        self.agent.patrimonio = [100 + i for i in range(30)]
        I_privada = self.agent.calcular_I_privada()
        expected = (self.agent.patrimonio[-1] / self.agent.patrimonio[-22]) - 1
        self.assertAlmostEqual(I_privada, expected)

    def test_calcular_I_social(self):
        # Cria dois vizinhos com patrimônios conhecidos
        neighbor1 = Agente(
            nome="Vizinho1",
            saldo=1000,
            carteira={},
            sentimento=0,
            expectativa=[0, 0, 0],
            literacia_financeira=0.5,
            comportamento_fundamentalista=0.5,
            comportamento_especulador=0.5,
            comportamento_ruido=0.5,
            expectativa_inflacao=0.02,
        )
        neighbor1.patrimonio = [100 + i for i in range(30)]
        neighbor2 = Agente(
            nome="Vizinho2",
            saldo=1000,
            carteira={},
            sentimento=0,
            expectativa=[0, 0, 0],
            literacia_financeira=0.5,
            comportamento_fundamentalista=0.5,
            comportamento_especulador=0.5,
            comportamento_ruido=0.5,
            expectativa_inflacao=0.02,
        )
        neighbor2.patrimonio = [200 + i for i in range(30)]
        self.agent.vizinhos = [neighbor1, neighbor2]
        I_social = self.agent.calcular_I_social()
        expected = (neighbor1.calcular_I_privada() + neighbor2.calcular_I_privada()) / 2
        self.assertAlmostEqual(I_social, expected)

    def test_atualiza_sentimento(self):
        # Para tornar o teste determinístico, sobrepõe sorteia_news para retornar valor fixo
        self.agent.sorteia_news = lambda: 0.5
        # Configura um histórico de patrimônio para calcular I_privada
        self.agent.patrimonio = [100] * 30
        self.agent.vizinhos = []  # Sem vizinhos para este teste
        sentimento = self.agent.atualiza_sentimento()
        # Verifica que o sentimento atualizado esteja dentro do intervalo [-1, 1]
        self.assertGreaterEqual(sentimento, -1)
        self.assertLessEqual(sentimento, 1)


if __name__ == "__main__":
    unittest.main()
