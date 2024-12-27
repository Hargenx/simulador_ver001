from dataclasses import dataclass, field
from typing import List, Dict
from typing import TYPE_CHECKING
from .transacao import Transacao
if TYPE_CHECKING:
    from .ordem import Ordem
    from .mercado import Mercado

@dataclass
class OrderBook:
    """
    Classe que representa um livro de ordens (order book).

    O order book é responsável por armazenar e gerenciar as ordens de compra e venda
    de ativos no mercado. Ele também realiza o processo de execução de ordens
    compatíveis, determinando o preço de execução e a quantidade negociada.

    Atributos:
        ordens_compra (Dict[str, List[Ordem]]): Dicionário que armazena listas de ordens
            de compra, categorizadas por ativo.
        ordens_venda (Dict[str, List[Ordem]]): Dicionário que armazena listas de ordens
            de venda, categorizadas por ativo.
    """
    ordens_compra: Dict[str, List["Ordem"]] = field(default_factory=dict)
    ordens_venda: Dict[str, List["Ordem"]] = field(default_factory=dict)

    def adicionar_ordem(self, ordem: "Ordem") -> None:
        """
        Adiciona uma nova ordem ao livro de ordens.

        Dependendo do tipo da ordem, ela será adicionada ao dicionário de
        ordens de compra ou venda.

        :param ordem: Objeto do tipo `Ordem` contendo os detalhes da ordem.
        :return: None
        """
        if ordem.tipo == "compra":
            self.ordens_compra.setdefault(ordem.ativo, []).append(ordem)
        elif ordem.tipo == "venda":
            self.ordens_venda.setdefault(ordem.ativo, []).append(ordem)

    def executar_ordens(self, ativo: str, mercado: "Mercado") -> None:
        """
        Executa ordens de compra e venda para um ativo específico.

        Este método processa as ordens de compra e venda associadas ao ativo.
        Ele combina as ordens compatíveis com base no preço limite e quantidade,
        executando transações quando aplicável.

        :param ativo: Nome do ativo para o qual as ordens devem ser processadas.
        :param mercado: Objeto `Mercado` que mantém o estado do mercado,
            incluindo preços atuais dos ativos.
        :return: None
        """
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

                    mercado.ativos[ativo] = preco_execucao

                    ordem_compra.quantidade -= quantidade_exec
                    ordem_venda.quantidade -= quantidade_exec

                    if ordem_compra.quantidade == 0:
                        self.ordens_compra[ativo].pop(0)
                    if ordem_venda.quantidade == 0:
                        self.ordens_venda[ativo].pop(0)
                else:
                    break
