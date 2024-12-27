from dataclasses import dataclass, field
from typing import List

@dataclass
class Ativo:
    """
    Classe que representa um ativo financeiro no mercado.

    Um ativo é caracterizado por seu nome, preço atual e histórico de preços,
    permitindo rastrear sua evolução ao longo do tempo.
    """
    nome: str
    preco_atual: float
    historico_precos: List[float] = field(default_factory=list)

    def atualizar_preco(self, novo_preco: float) -> None:
        """
        Atualiza o preço atual do ativo e registra o preço anterior no histórico.

        Esta função é usada para refletir mudanças no preço de mercado de um ativo.
        O preço anterior é armazenado no histórico para possibilitar análises futuras.

        Args:
            novo_preco (float): O novo preço do ativo.

        Returns:
            None
        """
        self.historico_precos.append(self.preco_atual)
        self.preco_atual = novo_preco
