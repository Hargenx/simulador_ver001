from typing import Dict, List

def normalizar_historicos(
    historico_precos: Dict[str, List[float]],
    historico_patrimonios: Dict[str, List[float]],
    num_rodadas: int,
) -> None:
    """
    Normaliza os históricos de preços e patrimônios para garantir consistência com o número de rodadas.

    :param historico_precos: Dicionário com os históricos de preços de cada ativo.
    :param historico_patrimonios: Dicionário com os históricos de patrimônio de cada agente.
    :param num_rodadas: Número total de rodadas da simulação.
    :return: None
    """
    for ativo, precos in historico_precos.items():
        historico_precos[ativo] = normalizar_tamanho(precos, num_rodadas)

    for agente, patrimonios in historico_patrimonios.items():
        historico_patrimonios[agente] = normalizar_tamanho(patrimonios, num_rodadas)


def normalizar_tamanho(
    lista: List[float], tamanho: int, valor_padrao: float = 0
) -> List[float]:
    """
    Ajusta o tamanho de uma lista, preenchendo com um valor padrão se necessário.

    :param lista: Lista a ser normalizada.
    :param tamanho: Tamanho desejado da lista.
    :param valor_padrao: Valor padrão a ser usado para preencher a lista.
    :return: Lista normalizada.
    """
    while len(lista) < tamanho:
        lista.append(lista[-1] if lista else valor_padrao)
    if len(lista) > tamanho:
        lista = lista[:tamanho]
    return lista
