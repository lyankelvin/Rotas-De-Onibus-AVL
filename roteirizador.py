"""Roteirizador: ciclo seleção (máximo da AVL) → deslocamento → atendimento → remoção → atualização."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from arvore_avl import ArvoreAVL, NoAVL
from calculadora_prioridade import CalculadoraPrioridade, Contexto, Prioridade
from dados import Demanda, Onibus, Parada


@dataclass
class PassoRota:
    """Linha da tabela de acompanhamento."""
    ordem: int
    identificador: int
    pontuacao: float      # P (base) no momento da seleção
    nivel: str
    distancia: float
    embarcados: int
    desembarcados: int
    ocupacao: int
    nao_embarcados: int


NOMES_ROTACAO = {
    "simples_direita": "simples à direita (LL)",
    "simples_esquerda": "simples à esquerda (RR)",
    "dupla_esquerda_direita": "dupla esquerda-direita (LR)",
    "dupla_direita_esquerda": "dupla direita-esquerda (RL)",
}


def descrever_rotacoes(antes: dict, depois: dict) -> str:
    partes = [f"{depois[k] - antes[k]}× {NOMES_ROTACAO[k]}" for k in depois if depois[k] > antes[k]]
    return ", ".join(partes) if partes else "nenhuma rotação"


class Roteirizador:
    LIMIAR_LOTACAO = 0.8   # a partir de 80 % da capacidade, desembarques viram "obrigatórios"

    def __init__(self, cadastro: Dict[int, Parada], demandas: List[Demanda],
                 posicao_inicial: Tuple[float, float], capacidade: int = 30,
                 calculadora: Optional[CalculadoraPrioridade] = None):
        self.cadastro = cadastro                         # cadastro geral (nunca é apagado)
        self.calculadora = calculadora or CalculadoraPrioridade()
        self.onibus = Onibus(posicao_inicial[0], posicao_inicial[1], capacidade)
        self.inicio = tuple(posicao_inicial)

        # passageiros aguardando em cada parada (cópias: a execução altera as quantidades)
        self.esperando: Dict[int, List[Demanda]] = defaultdict(list)
        for d in demandas:
            if d.origem is None:
                self.onibus.a_bordo[d.destino] += d.quantidade
            else:
                self.esperando[d.origem].append(Demanda(d.origem, d.destino, d.quantidade))
        if self.onibus.ocupacao > capacidade:
            raise ValueError("Passageiros iniciais excedem a capacidade do ônibus")

        # AVL da rota atual: contém SOMENTE as paradas ainda pendentes
        self.avl = ArvoreAVL()
        self.pendentes = set(cadastro)
        self.atendidas: List[int] = []
        self.prioridades: Dict[int, Prioridade] = {}

        # ---- registros da execução ----
        self.passos: List[PassoRota] = []
        self.trajeto: List[Tuple[float, float]] = [self.inicio]
        self.distancia_total = 0.0
        self.total_embarcados = 0
        self.total_desembarcados = 0
        self.total_nao_embarcados = 0
        self.remocoes_atendimento = 0
        self.remocoes_atualizacao = 0
        self.altura_maxima = 0
        self.historico_prioridades: List[Dict[int, float]] = []   # P base de cada pendente em cada seleção
        self.prioridades_iniciais: Dict[int, Prioridade] = {}
        self.quadros: List[dict] = []                              # "fotografias" para a animação
        self.log: List[str] = []
        self.inicializado = False

    # ---------------- contexto para a calculadora ----------------
    def _contexto(self) -> Contexto:
        embarque = {i: sum(d.quantidade for d in self.esperando[i]) for i in self.pendentes}
        dependentes: Counter = Counter()
        for origem in self.pendentes:
            for d in self.esperando[origem]:
                if d.destino in self.pendentes and d.destino != origem:
                    dependentes[d.destino] += d.quantidade
        ob = self.onibus
        return Contexto(
            x=ob.x, y=ob.y, livre=ob.livre,
            lotado=ob.ocupacao >= self.LIMIAR_LOTACAO * ob.capacidade,
            embarque=embarque,
            desembarque_bordo={i: ob.a_bordo.get(i, 0) for i in self.pendentes},
            dependentes=dict(dependentes),
        )

    def _calcular_pendentes(self, nos: Optional[List[NoAVL]] = None) -> Dict[int, Prioridade]:
        ids = sorted(self.pendentes) if nos is None else [n.identificador for n in nos]
        return self.calculadora.calcular([self.cadastro[i] for i in ids], self._contexto())

    def _inserir_na_avl(self, ident: int, prio: Prioridade) -> None:
        ctx_emb = sum(d.quantidade for d in self.esperando[ident])
        self.avl.inserir(self.cadastro[ident], prio.pontuacao,
                         embarque=ctx_emb, desembarque=prio.desembarque_bordo, info=prio)
        self.altura_maxima = max(self.altura_maxima, self.avl.altura)

    # ---------------- Etapa 1: inicialização ----------------
    def inicializar(self) -> None:
        self.prioridades = self._calcular_pendentes()
        self.prioridades_iniciais = dict(self.prioridades)
        for ident in sorted(self.pendentes):
            self._inserir_na_avl(ident, self.prioridades[ident])
        self.insercoes_iniciais = self.avl.insercoes
        self.altura_inicial = self.avl.altura
        self.inicializado = True
        self._fotografar("inicial", "Estado inicial",
                         "AVL construída com todas as paradas. O nó mais à direita é a próxima parada.")

    # ---------------- Etapas 2 a 5: um passo do ciclo ----------------
    def passo(self) -> bool:
        """Executa um ciclo completo. Devolve False quando não há mais paradas pendentes."""
        # ETAPA 2 — seleção: consulta ao MAIOR elemento da AVL (nó mais à direita, O(log n))
        no = self.avl.maximo()
        if no is None:
            return False
        ident = no.identificador
        prio = self.prioridades[ident]
        self.historico_prioridades.append({i: self.prioridades[i].base for i in self.pendentes})

        # ETAPA 3 — deslocamento e atendimento
        distancia = self.calculadora.distancia(self.onibus.x, self.onibus.y,
                                               self.cadastro[ident].x, self.cadastro[ident].y)
        self.onibus.x, self.onibus.y = self.cadastro[ident].x, self.cadastro[ident].y
        self.distancia_total += distancia
        self.trajeto.append((self.onibus.x, self.onibus.y))
        desembarcados = self.onibus.a_bordo.pop(ident, 0)           # destino respeitado
        embarcados, nao_embarcados = self._embarcar(ident)
        self.total_desembarcados += desembarcados
        self.total_embarcados += embarcados
        self.total_nao_embarcados += nao_embarcados

        # ETAPA 4 — remoção permanente da parada atendida da AVL da rota atual
        rot0 = dict(self.avl.contagem_rotacoes)
        removido = self.avl.remover(no.chave)
        assert removido is not None, "parada selecionada deveria estar na AVL"
        self.remocoes_atendimento += 1
        self.pendentes.discard(ident)
        self.atendidas.append(ident)
        rot1 = dict(self.avl.contagem_rotacoes)
        self._fotografar("remocao", f"Passo {len(self.atendidas)}: ônibus chegou a P{ident}; P{ident} removida da AVL",
                         f"Remoção: {descrever_rotacoes(rot0, rot1)}. "
                         f"Desembarcaram {desembarcados}, embarcaram {embarcados}. "
                         f"(pontuações dos nós ainda são as antigas)", ident)

        # ETAPA 5 — recalcular as prioridades das paradas restantes (O(n)) e reordenar a AVL
        self._atualizar_prioridades()
        rot2 = dict(self.avl.contagem_rotacoes)
        self._fotografar("atualizacao", f"Passo {len(self.atendidas)}: prioridades recalculadas",
                         f"Remoção + reinserção das {len(self.pendentes)} paradas restantes: "
                         f"{descrever_rotacoes(rot1, rot2)}.", ident)

        self.passos.append(PassoRota(len(self.atendidas), ident, prio.base, prio.nivel, distancia,
                                     embarcados, desembarcados, self.onibus.ocupacao, nao_embarcados))
        self.log.append(
            f"Passo {len(self.atendidas):2d}: P{ident:<2d} | P={prio.base:.3f} ({prio.nivel}) | "
            f"dist={distancia:5.1f} | +{embarcados:2d} embarcam, -{desembarcados:2d} desembarcam | "
            f"a bordo: {self.onibus.ocupacao:2d}/{self.onibus.capacidade}")
        return True

    def _embarcar(self, ident: int) -> Tuple[int, int]:
        """Embarca quem aguarda em `ident`, respeitando capacidade e destinos ainda atendíveis."""
        embarcados = nao_embarcados = 0
        for d in self.esperando.pop(ident, []):
            if d.destino not in self.pendentes:      # destino já visitado: não seria entregue
                nao_embarcados += d.quantidade
                continue
            n = min(d.quantidade, self.onibus.livre)
            self.onibus.a_bordo[d.destino] += n
            embarcados += n
            nao_embarcados += d.quantidade - n       # sem vaga: fica na parada
        return embarcados, nao_embarcados

    def _atualizar_prioridades(self) -> None:
        """
        Recalcula distâncias e pontuações dos pendentes e reordena a AVL.
        Regra de ouro: NUNCA alterar a chave de um nó dentro da árvore.
        Para cada parada: remover(chave antiga) -> inserir(chave nova).
        """
        if self.avl.vazia():
            self.prioridades = {}
            return
        nos = self.avl.em_ordem()                    # lista dos nós pendentes (O(n))
        novas = self._calcular_pendentes(nos)        # distâncias + normalização + pontuações (O(n))
        antigas = [(n.chave, n.identificador) for n in nos]
        self.prioridades = novas
        for chave_antiga, ident in antigas:
            removido = self.avl.remover(chave_antiga)    # sai com a chave ANTIGA ...
            assert removido is not None
            self.remocoes_atualizacao += 1
            self._inserir_na_avl(ident, novas[ident])    # ... e volta com a chave NOVA (novo nó)

    def executar(self, verbose: bool = True) -> None:
        if not self.inicializado:
            self.inicializar()
        while self.passo():                          # ETAPA 6 — repete até a AVL esvaziar
            pass
        self.nao_entregues = self.onibus.ocupacao    # passageiros que não chegaram ao destino
        if verbose:
            print("\n".join(self.log))

    # ---------------- registros para visualização e métricas ----------------
    def _fotografar(self, fase: str, titulo: str, detalhe: str, ultima: Optional[int] = None) -> None:
        proximo = self.avl.maximo(contar=False)       # só para destacar; não conta como consulta do algoritmo
        estado = {}
        for i in self.pendentes:
            estado[i] = (sum(d.quantidade for d in self.esperando[i]), self.onibus.a_bordo.get(i, 0))
        self.quadros.append({
            "fase": fase, "titulo": titulo, "detalhe": detalhe,
            "arvore": self.avl.para_dict(),
            "onibus": (self.onibus.x, self.onibus.y),
            "trajeto": list(self.trajeto),
            "atendidas": list(self.atendidas),
            "proximo": proximo.identificador if proximo else None,
            "estado": estado,
            "ocupacao": self.onibus.ocupacao,
            "capacidade": self.onibus.capacidade,
        })

    def metricas(self) -> Dict[str, object]:
        c = self.avl.contagem_rotacoes
        return {
            "Quantidade inicial de paradas": len(self.cadastro),
            "Paradas atendidas": len(self.atendidas),
            "Distância total percorrida": round(self.distancia_total, 2),
            "Passageiros embarcados (total)": self.total_embarcados,
            "Passageiros desembarcados (total)": self.total_desembarcados,
            "Passageiros não embarcados (sem vaga/destino)": self.total_nao_embarcados,
            "Passageiros não entregues": getattr(self, "nao_entregues", self.onibus.ocupacao),
            "Altura inicial da AVL": self.altura_inicial,
            "Altura máxima observada da AVL": self.altura_maxima,
            "Altura final da AVL (árvore vazia)": self.avl.altura,
            "Operações de inserção (total)": self.avl.insercoes,
            "   └ inserções iniciais": self.insercoes_iniciais,
            "   └ reinserções para atualizar prioridades": self.avl.insercoes - self.insercoes_iniciais,
            "Operações de remoção (total)": self.avl.remocoes,
            "   └ remoções por atendimento": self.remocoes_atendimento,
            "   └ remoções para atualizar prioridades": self.remocoes_atualizacao,
            "Rotações realizadas (elementares)": self.avl.rotacoes_elementares,
            "   └ simples à direita (LL)": c["simples_direita"],
            "   └ simples à esquerda (RR)": c["simples_esquerda"],
            "   └ duplas esquerda-direita (LR)": c["dupla_esquerda_direita"],
            "   └ duplas direita-esquerda (RL)": c["dupla_direita_esquerda"],
            "Consultas ao maior elemento": self.avl.consultas_maximo,
        }
