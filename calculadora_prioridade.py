"""Cálculo da pontuação de prioridade: P = 0,4·E + 0,4·D + 0,2·G, com níveis de prioridade."""
import math
from dataclasses import dataclass
from typing import Dict, List

from dados import Parada


NIVEL_OBRIGATORIA = "OBRIGATÓRIA"
NIVEL_NORMAL = "NORMAL"
NIVEL_ADIADA = "ADIADA"


@dataclass
class Contexto:
    """Situação atual da rota, fornecida pelo Roteirizador à calculadora."""
    x: float                           # posição do ônibus
    y: float
    livre: int                         # vagas livres no ônibus
    lotado: bool                       # ônibus acima do limiar de lotação?
    embarque: Dict[int, int]           # parada -> passageiros aguardando agora
    desembarque_bordo: Dict[int, int]  # parada -> passageiros a bordo com destino a ela
    dependentes: Dict[int, int]        # parada -> passageiros ainda esperando em outras paradas e destinados a ela


@dataclass
class Prioridade:
    """Resultado do cálculo para uma parada (guarda também os fatores, para a demonstração)."""
    identificador: int
    distancia: float
    embarque_efetivo: int
    desembarque_bordo: int
    E: float
    D: float
    G: float
    base: float        # P = 0,4E + 0,4D + 0,2G  (em [0, 1])
    nivel: str
    pontuacao: float   # base + deslocamento do nível  => é a pontuação usada na chave da AVL


class CalculadoraPrioridade:
    PESO_EMBARQUE = 0.4
    PESO_DESEMBARQUE = 0.4
    PESO_PROXIMIDADE = 0.2
    DESLOCAMENTO_NIVEL = {NIVEL_OBRIGATORIA: 10.0, NIVEL_NORMAL: 0.0, NIVEL_ADIADA: -10.0}
    CASAS = 6   # arredondamento: evita ruído de ponto flutuante nas chaves

    @staticmethod
    def distancia(x1, y1, x2, y2) -> float:
        """Distância euclidiana (aproximação planar da distância geográfica real)."""
        return math.hypot(x1 - x2, y1 - y2)

    @staticmethod
    def _normalizar_pelo_maximo(valores: Dict[int, float]) -> Dict[int, float]:
        maior = max(valores.values(), default=0)
        if maior <= 0:                       # ninguém tem demanda: contribuição nula
            return {i: 0.0 for i in valores}
        return {i: v / maior for i, v in valores.items()}

    @staticmethod
    def _normalizar_proximidade(distancias: Dict[int, float]) -> Dict[int, float]:
        """Normalização inversa: menor distância => G = 1; maior distância => G = 0."""
        if not distancias:
            return {}
        d_min, d_max = min(distancias.values()), max(distancias.values())
        if d_max - d_min < 1e-12:            # todas equidistantes: não distingue ninguém
            return {i: 1.0 for i in distancias}
        return {i: 1.0 - (d - d_min) / (d_max - d_min) for i, d in distancias.items()}

    def _classificar(self, ident: int, ctx: Contexto) -> str:
        # Dependência: há gente esperando em outra parada com destino a esta. Visitar esta
        # parada agora deixaria essas pessoas sem entrega (cada parada é visitada uma só vez).
        if ctx.dependentes.get(ident, 0) > 0:
            return NIVEL_ADIADA
        # Desembarque obrigatório: ônibus lotado e passageiros a bordo destinados a esta parada.
        # Só desembarcando é possível liberar vagas; por isso supera a seleção normal.
        if ctx.lotado and ctx.desembarque_bordo.get(ident, 0) > 0:
            return NIVEL_OBRIGATORIA
        return NIVEL_NORMAL

    def calcular(self, paradas: List[Parada], ctx: Contexto) -> Dict[int, Prioridade]:
        """Calcula a prioridade de TODAS as paradas informadas (custo O(n))."""
        ids = [p.identificador for p in paradas]
        dist = {p.identificador: self.distancia(ctx.x, ctx.y, p.x, p.y) for p in paradas}
        emb = {i: min(ctx.embarque.get(i, 0), ctx.livre) for i in ids}   # só conta quem cabe no ônibus
        des = {i: ctx.desembarque_bordo.get(i, 0) for i in ids}

        E = self._normalizar_pelo_maximo(emb)
        D = self._normalizar_pelo_maximo(des)
        G = self._normalizar_proximidade(dist)

        resultado = {}
        for i in ids:
            base = round(self.PESO_EMBARQUE * E[i] + self.PESO_DESEMBARQUE * D[i]
                         + self.PESO_PROXIMIDADE * G[i], self.CASAS)
            nivel = self._classificar(i, ctx)
            pont = round(base + self.DESLOCAMENTO_NIVEL[nivel], self.CASAS)
            resultado[i] = Prioridade(i, dist[i], emb[i], des[i], E[i], D[i], G[i], base, nivel, pont)
        return resultado
