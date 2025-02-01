import unittest
import random
import numpy as np

from agente import Agente  # Certifique-se de ajustar o caminho conforme necessário


class TestAgente(unittest.TestCase):
    def setUp(self):
        """
        Configura um agente para ser utilizado nos testes.
        """
        random.seed(42)  # Fixando a semente para testes reprodutíveis
        np.random.seed(42)
        self.agente = Agente(
            nome="Agente X",
            saldo=10000.0,
            carteira={"AAPL": 10, "MSFT": 5},
            sentimento=0.5,
            expectativa=[50, 100, 150],
            literacia_financeira=0.7,
            comportamento_fundamentalista=0.4,
            comportamento_especulador=0.4,
            comportamento_ruido=0.2,
            expectativa_inflacao=0.02,
        )

    def test_inicializacao(self):
        """
        Testa se o agente é inicializado corretamente.
        """
        self.assertEqual(self.agente.nome, "Agente X")
        self.assertEqual(self.agente.saldo, 10000.0)
        self.assertEqual(self.agente.carteira, {"AAPL": 10, "MSFT": 5})
        self.assertTrue(0 <= self.agente.literacia_financeira <= 1)
        self.assertTrue(-1 <= self.agente.sentimento <= 1)

    def test_validacao_sentimento(self):
        """
        Testa se um valor inválido para sentimento levanta uma exceção.
        """
        with self.assertRaises(ValueError):
            Agente(
                nome="Erro",
                saldo=5000.0,
                carteira={},
                sentimento=2.0,  # Fora do intervalo permitido
                expectativa=[10, 20, 30],
                literacia_financeira=0.8,
                comportamento_fundamentalista=0.5,
                comportamento_especulador=0.3,
                comportamento_ruido=0.2,
                expectativa_inflacao=0.01,
            )

    def test_calculo_volatilidade(self):
        """
        Testa o cálculo da volatilidade percebida com um histórico de preços.
        """
        historico_precos = [100 + i for i in range(300)]  # Valores simulados
        self.agente.calcular_volatilidade_percebida(historico_precos)
        self.assertGreaterEqual(self.agente.volatilidade_percebida, 0)

    def test_calculo_risco_desejado(self):
        """
        Testa o cálculo do risco desejado pelo agente.
        """
        self.agente.volatilidade_percebida = 0.2  # Simula um valor de volatilidade
        risco = self.agente.calcular_risco_desejado()
        self.assertGreaterEqual(risco, 0)

    def test_calculo_quantidade_baseada_em_risco(self):
        """
        Testa se o cálculo de quantidade baseada em risco retorna um valor coerente.
        """
        self.agente.volatilidade_percebida = 0.1
        risco_desejado = self.agente.calcular_risco_desejado()
        quantidade = self.agente.calcular_quantidade_baseada_em_risco(risco_desejado)
        self.assertGreaterEqual(quantidade, 0)

    def test_atualizacao_patrimonio(self):
        """
        Testa a atualização do patrimônio do agente com preços de mercado.
        """
        precos_mercado = {"AAPL": 150, "MSFT": 300}
        fundos_imobiliarios = {}
        self.agente.atualizar_patrimonio(precos_mercado, fundos_imobiliarios)
        self.assertGreater(len(self.agente.patrimonio), 0)

    def test_calcula_I_privada(self):
        """
        Testa se o cálculo da taxa de crescimento do patrimônio retorna um valor válido.
        """
        self.agente.patrimonio = [
            10000
        ] * 23  # Simula 23 períodos de patrimônio estável
        taxa = self.agente.calcula_I_privada()
        self.assertEqual(taxa, 0.0)  # Como não houve crescimento, a taxa deve ser 0

    def test_sorteia_news(self):
        """
        Testa se o sorteio de notícias gera um número válido.
        """
        news = self.agente.sorteia_news()
        self.assertTrue(
            -3 <= news <= 3
        )  # Garante que está dentro do intervalo esperado

    def test_atualiza_sentimento(self):
        """
        Testa se a atualização do sentimento retorna um valor dentro do intervalo permitido.
        """
        sentimento = self.agente.atualiza_sentimento()
        self.assertTrue(-1 <= sentimento <= 1)


if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
