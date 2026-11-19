"""Árvore AVL implementada manualmente, ordenada por (pontuação, identificador) em ordem crescente.
O nó mais à direita é a parada de maior prioridade."""
from typing import List, Optional, Tuple

from dados import Parada


class NoAVL:
    """Nó da AVL: representa uma parada pendente da rota atual."""

    def __init__(self, parada: Parada, pontuacao: float,
                 embarque: Optional[int] = None, desembarque: Optional[int] = None,
                 info=None):
        self.identificador = parada.identificador
        self.x = parada.x
        self.y = parada.y
        # valores vigentes no momento da inserção (usados no cálculo da pontuação)
        self.embarque = parada.embarque if embarque is None else embarque
        self.desembarque = parada.desembarque if desembarque is None else desembarque
        self.pontuacao = pontuacao          # pontuação de prioridade (parte principal da chave)
        self.altura = 1                     # folha = 1
        self.esq: Optional["NoAVL"] = None  # filho esquerdo (prioridades menores)
        self.dir: Optional["NoAVL"] = None  # filho direito (prioridades maiores)
        self.info = info                    # detalhamento do cálculo (apenas para exibição)

    @property
    def chave(self) -> Tuple[float, int]:
        """Chave composta (pontuação, identificador). NUNCA é alterada com o nó na árvore."""
        return (self.pontuacao, self.identificador)


class ArvoreAVL:
    """Árvore AVL ordenada por (pontuação, identificador), em ordem crescente."""

    def __init__(self):
        self.raiz: Optional[NoAVL] = None
        self._tamanho = 0
        # ---- contadores para as métricas ----
        self.insercoes = 0
        self.remocoes = 0
        self.consultas_maximo = 0
        self.contagem_rotacoes = {
            "simples_direita": 0,          # caso Esquerda-Esquerda (LL)
            "simples_esquerda": 0,         # caso Direita-Direita (RR)
            "dupla_esquerda_direita": 0,   # caso Esquerda-Direita (LR)
            "dupla_direita_esquerda": 0,   # caso Direita-Esquerda (RL)
        }

    # ---------------- utilidades básicas ----------------
    def __len__(self) -> int:
        return self._tamanho

    def vazia(self) -> bool:
        return self.raiz is None

    @staticmethod
    def altura_no(no: Optional[NoAVL]) -> int:
        return no.altura if no else 0

    @property
    def altura(self) -> int:
        return self.altura_no(self.raiz)

    def fator_balanceamento(self, no: Optional[NoAVL]) -> int:
        """altura(esquerda) - altura(direita). Válido na AVL: -1, 0 ou +1."""
        return 0 if no is None else self.altura_no(no.esq) - self.altura_no(no.dir)

    def _atualizar_altura(self, no: NoAVL) -> None:
        no.altura = 1 + max(self.altura_no(no.esq), self.altura_no(no.dir))

    @property
    def rotacoes_elementares(self) -> int:
        """Total de rotações elementares (uma rotação dupla = 2 elementares)."""
        c = self.contagem_rotacoes
        return (c["simples_direita"] + c["simples_esquerda"]
                + 2 * (c["dupla_esquerda_direita"] + c["dupla_direita_esquerda"]))

    # ---------------- rotações ----------------
    def _rotacao_direita(self, y: NoAVL) -> NoAVL:
        r"""
        Rotação simples à direita (corrige o caso Esquerda-Esquerda).
                y                x
               / \              / \
              x   C    ==>     A   y
             / \                  / \
            A   B                B   C
        A ordem em-ordem (A x B y C) é preservada.
        """
        x = y.esq
        b = x.dir
        x.dir = y
        y.esq = b
        self._atualizar_altura(y)   # y agora é filho: atualizar primeiro
        self._atualizar_altura(x)
        return x

    def _rotacao_esquerda(self, x: NoAVL) -> NoAVL:
        r"""
        Rotação simples à esquerda (corrige o caso Direita-Direita).
              x                    y
             / \                  / \
            A   y      ==>       x   C
               / \              / \
              B   C            A   B
        """
        y = x.dir
        b = y.esq
        y.esq = x
        x.dir = b
        self._atualizar_altura(x)
        self._atualizar_altura(y)
        return y

    def _balancear(self, no: NoAVL) -> NoAVL:
        """Atualiza a altura de `no` e aplica a rotação adequada se |fb| > 1."""
        self._atualizar_altura(no)
        fb = self.fator_balanceamento(no)

        if fb > 1:  # pesado à esquerda
            if self.fator_balanceamento(no.esq) >= 0:
                # Esquerda-Esquerda: uma rotação simples à direita
                self.contagem_rotacoes["simples_direita"] += 1
                return self._rotacao_direita(no)
            # Esquerda-Direita: rotação à esquerda no filho, depois à direita no nó
            self.contagem_rotacoes["dupla_esquerda_direita"] += 1
            no.esq = self._rotacao_esquerda(no.esq)
            return self._rotacao_direita(no)

        if fb < -1:  # pesado à direita
            if self.fator_balanceamento(no.dir) <= 0:
                # Direita-Direita: uma rotação simples à esquerda
                self.contagem_rotacoes["simples_esquerda"] += 1
                return self._rotacao_esquerda(no)
            # Direita-Esquerda: rotação à direita no filho, depois à esquerda no nó
            self.contagem_rotacoes["dupla_direita_esquerda"] += 1
            no.dir = self._rotacao_direita(no.dir)
            return self._rotacao_esquerda(no)

        return no

    # ---------------- inserção ----------------
    def inserir(self, parada: Parada, pontuacao: float,
                embarque: Optional[int] = None, desembarque: Optional[int] = None,
                info=None) -> NoAVL:
        """Insere um novo nó com a chave (pontuacao, id). O(log n)."""
        novo = NoAVL(parada, pontuacao, embarque, desembarque, info)
        self.raiz = self._inserir(self.raiz, novo)
        self._tamanho += 1
        self.insercoes += 1
        return novo

    def _inserir(self, atual: Optional[NoAVL], novo: NoAVL) -> NoAVL:
        if atual is None:
            return novo
        if novo.chave < atual.chave:
            atual.esq = self._inserir(atual.esq, novo)
        elif novo.chave > atual.chave:
            atual.dir = self._inserir(atual.dir, novo)
        else:
            raise ValueError(f"Chave duplicada: {novo.chave}")
        return self._balancear(atual)  # rebalanceia no caminho de volta da recursão

    # ---------------- remoção ----------------
    def remover(self, chave: Tuple[float, int]) -> Optional[NoAVL]:
        """
        Remove o nó com a chave informada e o devolve (ou None se não existir). O(log n).
        Para alterar a prioridade de uma parada: remover(chave_antiga) e inserir com a chave nova.
        """
        self.raiz, removido = self._remover(self.raiz, chave)
        if removido is not None:
            self._tamanho -= 1
            self.remocoes += 1
        return removido

    def _remover_minimo(self, no: NoAVL):
        """Desliga o menor nó da subárvore. Devolve (nova_raiz_da_subárvore, nó_mínimo)."""
        if no.esq is None:
            return no.dir, no
        no.esq, minimo = self._remover_minimo(no.esq)
        return self._balancear(no), minimo

    def _remover(self, no: Optional[NoAVL], chave):
        if no is None:
            return None, None                      # chave inexistente
        if chave < no.chave:
            no.esq, removido = self._remover(no.esq, chave)
        elif chave > no.chave:
            no.dir, removido = self._remover(no.dir, chave)
        else:
            removido = no
            if no.esq is None or no.dir is None:
                # 0 ou 1 filho: o filho (ou None) ocupa o lugar do nó
                filho = no.esq if no.esq is not None else no.dir
                removido.esq = removido.dir = None
                return filho, removido
            # 2 filhos: o sucessor em ordem (menor nó da subárvore direita)
            # assume o lugar do nó removido. Os nós são religados; nenhuma chave é sobrescrita.
            nova_dir, sucessor = self._remover_minimo(no.dir)
            sucessor.esq = no.esq
            sucessor.dir = nova_dir
            removido.esq = removido.dir = None
            no = sucessor
        if removido is None:
            return no, None
        return self._balancear(no), removido       # rebalanceia no caminho de volta

    # ---------------- buscas ----------------
    def buscar(self, chave: Tuple[float, int]) -> Optional[NoAVL]:
        """Busca binária pela chave. O(log n)."""
        no = self.raiz
        while no is not None:
            if chave == no.chave:
                return no
            no = no.esq if chave < no.chave else no.dir
        return None

    def maximo(self, contar: bool = True) -> Optional[NoAVL]:
        """
        Parada de MAIOR prioridade = nó mais à direita.
        Desce apenas pelos ponteiros da direita: no máximo `altura` passos => O(log n).
        NÃO percorre a árvore inteira.
        """
        if contar:
            self.consultas_maximo += 1
        no = self.raiz
        if no is None:
            return None
        while no.dir is not None:
            no = no.dir
        return no

    # ---------------- percursos (devolvem listas de nós) ----------------
    def pre_ordem(self) -> List[NoAVL]:
        saida: List[NoAVL] = []
        def rec(no):
            if no:
                saida.append(no); rec(no.esq); rec(no.dir)
        rec(self.raiz)
        return saida

    def em_ordem(self) -> List[NoAVL]:
        """Ordem crescente de prioridade."""
        saida: List[NoAVL] = []
        def rec(no):
            if no:
                rec(no.esq); saida.append(no); rec(no.dir)
        rec(self.raiz)
        return saida

    def pos_ordem(self) -> List[NoAVL]:
        saida: List[NoAVL] = []
        def rec(no):
            if no:
                rec(no.esq); rec(no.dir); saida.append(no)
        rec(self.raiz)
        return saida

    # ---------------- verificação das propriedades ----------------
    def validar(self) -> bool:
        """
        Confere (levanta AssertionError se falhar):
        1) propriedade de árvore binária de busca (ordem estrita pelas chaves);
        2) altura armazenada = altura real;
        3) fator de balanceamento de TODOS os nós em {-1, 0, +1};
        4) quantidade de nós = contador interno.
        """
        contador = [0]

        def rec(no, minimo, maximo):
            if no is None:
                return 0
            contador[0] += 1
            assert minimo is None or no.chave > minimo, f"ordem violada em {no.chave}"
            assert maximo is None or no.chave < maximo, f"ordem violada em {no.chave}"
            he = rec(no.esq, minimo, no.chave)
            hd = rec(no.dir, no.chave, maximo)
            assert no.altura == 1 + max(he, hd), f"altura incorreta em {no.chave}"
            assert abs(he - hd) <= 1, f"desbalanceado em {no.chave} (fb={he - hd})"
            return no.altura

        rec(self.raiz, None, None)
        assert contador[0] == self._tamanho, "contador de nós inconsistente"
        return True

    # ---------------- exportação para visualização ----------------
    def para_dict(self) -> Optional[dict]:
        """Cópia estática (dicionário aninhado) da árvore atual, usada pelo Visualizador."""
        def rec(no):
            if no is None:
                return None
            info = no.info
            return {
                "id": no.identificador,
                "pontuacao": no.pontuacao,
                "base": info.base if info is not None else no.pontuacao,
                "nivel": info.nivel if info is not None else "NORMAL",
                "altura": no.altura,
                "fb": self.fator_balanceamento(no),
                "esq": rec(no.esq),
                "dir": rec(no.dir),
            }
        return rec(self.raiz)
