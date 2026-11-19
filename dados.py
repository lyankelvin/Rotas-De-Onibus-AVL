"""Dados do domínio: cadastro de paradas, grupos de passageiros, ônibus e cenário de demonstração."""
from collections import Counter
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class Parada:
    """Cadastro geral de uma parada (permanente, não depende da AVL)."""
    identificador: int
    x: float
    y: float
    embarque: int      # passageiros que aguardam o ônibus nesta parada (no início)
    desembarque: int   # passageiros (a bordo ou ainda por embarcar) com destino a esta parada

    @property
    def rotulo(self) -> str:
        return f"P{self.identificador}"


@dataclass
class Demanda:
    """Grupo de passageiros: origem -> destino. origem=None => já está no ônibus."""
    origem: Optional[int]
    destino: int
    quantidade: int


class Onibus:
    """Estado do veículo: posição, capacidade e passageiros a bordo (por destino)."""

    def __init__(self, x: float, y: float, capacidade: int):
        self.x = x
        self.y = y
        self.capacidade = capacidade
        self.a_bordo: Counter = Counter()   # destino -> quantidade

    @property
    def ocupacao(self) -> int:
        return sum(self.a_bordo.values())

    @property
    def livre(self) -> int:
        return self.capacidade - self.ocupacao


def montar_cadastro(coordenadas: Dict[int, Tuple[float, float]],
                    demandas: List[Demanda]) -> Dict[int, Parada]:
    """Deriva embarque/desembarque de cada parada a partir dos grupos de passageiros."""
    cadastro = {}
    for i, (x, y) in coordenadas.items():
        emb = sum(d.quantidade for d in demandas if d.origem == i)
        des = sum(d.quantidade for d in demandas if d.destino == i)
        cadastro[i] = Parada(i, x, y, emb, des)
    return cadastro


def criar_cenario_demonstracao():
    """
    Cidade fictícia com 10 paradas distribuídas de forma não linear (plano 100 x 100).
    O ônibus parte da garagem em (50, 50), com 7 passageiros já a bordo.
    Os fluxos de passageiros formam um grafo sem ciclos (origem sempre antes do destino),
    o que torna possível entregar todos com uma única visita por parada.
    """
    coordenadas = {
        1: (20, 15), 2: (35, 40), 3: (12, 55), 4: (30, 80), 5: (55, 70),
        6: (75, 85), 7: (85, 55), 8: (70, 30), 9: (50, 20), 10: (90, 12),
    }
    demandas = [
        # já a bordo no início
        Demanda(None, 2, 3), Demanda(None, 8, 4),
        # passageiros aguardando (origem -> destino)
        Demanda(1, 3, 6), Demanda(1, 5, 4),
        Demanda(2, 6, 5),
        Demanda(3, 4, 3), Demanda(3, 6, 2),
        Demanda(4, 7, 4),
        Demanda(5, 7, 7), Demanda(5, 10, 3),
        Demanda(6, 10, 2),
        Demanda(7, 10, 4),
        Demanda(8, 9, 3), Demanda(8, 10, 3),
        Demanda(9, 10, 2),
    ]
    cadastro = montar_cadastro(coordenadas, demandas)
    posicao_inicial = (50.0, 50.0)
    return cadastro, demandas, posicao_inicial
