from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .agente import Agente

@dataclass
class Transacao:
    """
    Classe que representa uma transação de compra ou venda no mercado.

    Uma transação ocorre entre um comprador e um vendedor, envolvendo um ativo,
    uma quantidade negociada e o preço acordado de execução.

    A execução da transação ajusta os saldos dos agentes envolvidos e atualiza
    suas respectivas carteiras de ativos.
    """
    comprador: "Agente"
    vendedor: "Agente"
    ativo: str
    quantidade: int
    preco_execucao: float

    def executar(self):
        """
        Executa a transação de compra ou venda entre os agentes.

        Esta função realiza as seguintes ações:
        - Deduz o valor total da transação do saldo do comprador.
        - Adiciona o valor total ao saldo do vendedor.
        - Atualiza a carteira do comprador com a quantidade adquirida do ativo.
        - Atualiza a carteira do vendedor, removendo a quantidade vendida do ativo.
          Se a quantidade do ativo chegar a zero na carteira do vendedor, o ativo
          é removido da carteira.

        A transação é concluída de forma atômica, garantindo que os saldos e
        carteiras de ambos os agentes estejam consistentes após sua execução.

        Args:
            None

        Returns:
            None
        """
        valor_total = self.quantidade * self.preco_execucao
        self.comprador.saldo -= valor_total
        self.vendedor.saldo += valor_total

        # Atualiza a carteira do comprador
        self.comprador.carteira[self.ativo] = (
            self.comprador.carteira.get(self.ativo, 0) + self.quantidade
        )

        # Atualiza a carteira do vendedor
        if self.ativo in self.vendedor.carteira:
            self.vendedor.carteira[self.ativo] -= self.quantidade
            if self.vendedor.carteira[self.ativo] == 0:
                del self.vendedor.carteira[self.ativo]
