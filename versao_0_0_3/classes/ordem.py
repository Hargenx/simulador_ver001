from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agente import Agente

@dataclass
class Ordem:
    """
    Classe que representa uma ordem de compra ou venda no mercado.

    Uma ordem define as condições sob as quais um agente deseja realizar
    uma transação, incluindo o tipo de operação (compra ou venda),
    o ativo envolvido, o preço limite e a quantidade.

    Atributos:
        tipo (str): Tipo da ordem, podendo ser "compra" ou "venda".
        agente (Agente): O agente responsável pela criação da ordem.
        ativo (str): O nome do ativo financeiro associado à ordem.
        preco_limite (float): O preço máximo (para compra) ou mínimo (para venda)
            que o agente está disposto a aceitar.
        quantidade (int): A quantidade do ativo a ser negociada.
    """
    tipo: str
    agente: "Agente"
    ativo: str
    preco_limite: float
    quantidade: int
