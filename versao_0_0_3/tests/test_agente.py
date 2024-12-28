import unittest
from unittest.mock import patch
import sys
import os

# Adicionar caminho do projeto para importações relativas
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from classes.agente import Agente
from classes.mercado import Mercado
from classes.fundo_imobiliario import FundoImobiliario


class TestAgente(unittest.TestCase):
    """
    Classe de testes para a classe Agente.
    """

    def setUp(self):
        """
        Configuração inicial para os testes.
        """
        self.agente = Agente(
            nome="Test Agent",
            saldo=1000.0,
            carteira={"PETR4": 10, "VALE3": 5},
            sentimento=0.5,
            expectativa=[40.0, 50.0, 60.0],
            literacia_financeira=0.8,
            comportamento_especulador=0.4,
            comportamento_ruido=0.2,
            comportamento_fundamentalista=0.3,
            expectativa_inflacao=0.02,
        )
        self.agente.vizinhos = [
            Agente(
                nome="Vizinho 1",
                saldo=1000.0,
                carteira={"PETR4": 5},
                sentimento=0.3,
                expectativa=[30.0, 40.0, 50.0],
                literacia_financeira=0.7,
                comportamento_especulador=0.2,
                comportamento_ruido=0.1,
                comportamento_fundamentalista=0.4,
                expectativa_inflacao=0.01,
            ),
            Agente(
                nome="Vizinho 2",
                saldo=1200.0,
                carteira={"VALE3": 7},
                sentimento=-0.2,
                expectativa=[20.0, 30.0, 40.0],
                literacia_financeira=0.9,
                comportamento_especulador=0.3,
                comportamento_ruido=0.2,
                comportamento_fundamentalista=0.5,
                expectativa_inflacao=0.02,
            ),
        ]
        # Inicializa o mercado
        self.mercado = Mercado(
            ativos={"PETR4": 50.0, "VALE3": 45.0},
            fundos_imobiliarios={
                "FII_A": FundoImobiliario(nome="FII_A", preco_cota=100.0),
                "FII_B": FundoImobiliario(nome="FII_B", preco_cota=150.0),
            },
        )

    def test_gerar_ordem_compra(self):
        """
        Testa a geração de uma ordem de compra.
        """
        ordem = self.agente.gerar_ordem("PETR4", 50.0)
        self.assertEqual(ordem.tipo, "compra")
        self.assertGreaterEqual(ordem.quantidade, 1)
        self.assertLessEqual(ordem.quantidade * ordem.preco_limite, self.agente.saldo)

    def test_gerar_ordem_venda(self):
        """
        Testa a geração de uma ordem de venda.
        """
        self.agente.sentimento = -0.5  # Forçar sentimento negativo para priorizar venda
        with patch("random.uniform", return_value=0.4):  # Garantir que `prob_compra < 0.5`
            ordem = self.agente.gerar_ordem("PETR4", 50.0)
            self.assertEqual(ordem.tipo, "venda")  # Confirmar que é uma venda
            self.assertEqual(ordem.ativo, "PETR4")  # Ativo correto
            self.assertGreaterEqual(ordem.preco_limite, 0)  # Preço limite válido
            self.assertGreaterEqual(ordem.quantidade, 1)  # Quantidade válida
            self.assertLessEqual(ordem.quantidade, self.agente.carteira["PETR4"])  # Não vender mais do que possui

    

    def test_atualizar_patrimonio(self):
        """
        Testa a atualização do patrimônio do agente.
        """
        self.agente.atualiza_patrimonio(
            self.mercado.ativos, self.mercado.fundos_imobiliarios
        )
        patrimonio_esperado = (
            self.agente.saldo
            + self.mercado.ativos["PETR4"] * self.agente.carteira["PETR4"]
            + self.mercado.ativos["VALE3"] * self.agente.carteira["VALE3"]
        )
        self.assertAlmostEqual(
            self.agente.patrimonio[-1], patrimonio_esperado, places=2
        )

    def test_calcular_volatilidade_percebida(self):
        """
        Testa o cálculo da volatilidade percebida pelo agente.
        """
        historico_precos = [50, 51, 49, 48, 50] * 20  # Histórico para 100 dias
        self.agente.calcular_volatilidade_percebida(historico_precos)
        self.assertGreaterEqual(self.agente.volatilidade_percebida, 0)

    def test_calcular_risco_desejado(self):
        """
        Testa o cálculo do risco desejado pelo agente.
        """
        risco = self.agente.calcular_risco_desejado()
        self.assertGreater(risco, 0)

    def test_saldo_insuficiente(self):
        """
        Testa a geração de ordens quando o saldo é insuficiente.
        """
        self.agente.saldo = 10.0  # Define saldo insuficiente
        ordem = self.agente.gerar_ordem("PETR4", 50.0)
        if ordem.tipo == "compra":
            self.assertLessEqual(ordem.quantidade * ordem.preco_limite, self.agente.saldo)
        else:
            self.assertGreaterEqual(ordem.quantidade, 1)  # Quantidade mínima para venda

    def test_carteira_vazia(self):
        self.agente.carteira = {"PETR4": 0}  # Carteira sem ativos suficientes
        ordem = self.agente.gerar_ordem("PETR4", 50.0)
        if ordem.tipo == "venda":
            self.assertEqual(self.agente.carteira[ordem.ativo], 0)

    def test_inflacao_impacto(self):
        preco_ajustado = self.agente.ajustar_preco_por_inflacao(50.0)
        self.assertGreater(preco_ajustado, 50.0)

    def test_volatilidade_curta(self):
        historico_precos = [50, 51]  # Histórico curto
        self.agente.calcular_volatilidade_percebida(historico_precos)
        self.assertEqual(self.agente.volatilidade_percebida, 0.0)


if __name__ == "__main__":
    unittest.main()
