"""Testes automáticos da AVL e do algoritmo de roteirização. Execute: python testes.py"""
import math
import random

from arvore_avl import ArvoreAVL
from calculadora_prioridade import NIVEL_OBRIGATORIA, CalculadoraPrioridade, Contexto
from dados import Demanda, Parada, criar_cenario_demonstracao, montar_cadastro
from roteirizador import Roteirizador


def _p(i: int) -> Parada:
    return Parada(i, 0.0, 0.0, 0, 0)


def _avl_com(chaves):
    t = ArvoreAVL()
    for pont, i in chaves:
        t.inserir(_p(i), pont)
    return t


def teste_insercao_mantem_balanceamento():
    t = ArvoreAVL()
    for i in range(1, 201):                       # pior caso para BST comum: chaves crescentes
        t.inserir(_p(i), float(i)); t.validar()
    assert len(t) == 200
    assert t.altura <= 1.45 * math.log2(200 + 2), f"altura {t.altura} alta demais"
    assert [n.identificador for n in t.em_ordem()] == list(range(1, 201))


def teste_remocao_mantem_balanceamento():
    rng = random.Random(7)
    ids = list(range(300))
    rng.shuffle(ids)
    t = ArvoreAVL()
    for i in ids:
        t.inserir(_p(i), round(rng.random(), 3))
    t.validar()
    chaves = [n.chave for n in t.em_ordem()]
    rng.shuffle(chaves)
    for k in chaves:
        assert t.remover(k) is not None
        t.validar()                               # balanceada após CADA remoção
        assert t.buscar(k) is None
    assert t.vazia() and len(t) == 0
    assert t.remover((0.5, 999)) is None          # chave inexistente


def teste_quatro_rotacoes():
    casos = {
        "simples_direita":        [(30, 3), (20, 2), (10, 1)],   # LL
        "simples_esquerda":       [(10, 1), (20, 2), (30, 3)],   # RR
        "dupla_esquerda_direita": [(30, 3), (10, 1), (20, 2)],   # LR
        "dupla_direita_esquerda": [(10, 1), (30, 3), (20, 2)],   # RL
    }
    for nome, chaves in casos.items():
        t = _avl_com(chaves)
        t.validar()
        assert t.raiz.chave == (20, 2), f"{nome}: raiz deveria ser 20"
        assert t.raiz.esq.chave == (10, 1) and t.raiz.dir.chave == (30, 3)
        assert t.contagem_rotacoes[nome] == 1, f"{nome}: rotação não registrada"
        assert sum(t.contagem_rotacoes.values()) == 1


def teste_maximo_e_percursos():
    rng = random.Random(1)
    chaves = [(round(rng.random(), 4), i) for i in range(100)]
    t = _avl_com(chaves)
    assert t.maximo().chave == max(chaves)
    assert t.maximo().dir is None                 # é o nó mais à direita
    em = [n.chave for n in t.em_ordem()]
    assert em == sorted(chaves)
    assert len(t.pre_ordem()) == len(t.pos_ordem()) == 100
    assert t.pre_ordem()[0] is t.raiz and t.pos_ordem()[-1] is t.raiz
    # remover o máximo sucessivas vezes devolve ordem decrescente
    ordem = []
    while not t.vazia():
        m = t.maximo(); ordem.append(m.chave); t.remover(m.chave); t.validar()
    assert ordem == sorted(chaves, reverse=True)
    assert t.maximo() is None


def teste_pontuacoes_iguais_coexistem():
    t = _avl_com([(0.5, 1), (0.5, 2), (0.5, 3)])
    assert len(t) == 3 and t.validar()
    assert [n.identificador for n in t.em_ordem()] == [1, 2, 3]   # desempate por id
    assert t.maximo().identificador == 3
    assert t.buscar((0.5, 2)) is not None
    try:
        t.inserir(_p(2), 0.5)
        assert False, "deveria rejeitar chave idêntica"
    except ValueError:
        pass
    assert len(t) == 3                                            # árvore intacta


def teste_operacoes_aleatorias_contra_referencia():
    rng = random.Random(42)
    t, ref = ArvoreAVL(), {}
    prox = 0
    for _ in range(2000):
        if ref and rng.random() < 0.45:
            k = rng.choice(list(ref)); t.remover(k); del ref[k]
        else:
            k = (round(rng.random(), 2), prox); prox += 1
            t.inserir(_p(k[1]), k[0]); ref[k] = True
        t.validar()
        assert (t.maximo(contar=False).chave if ref else None) == (max(ref) if ref else None)
    assert [n.chave for n in t.em_ordem()] == sorted(ref)


TESTES_AVL = [
    teste_insercao_mantem_balanceamento,
    teste_remocao_mantem_balanceamento,
    teste_quatro_rotacoes,
    teste_maximo_e_percursos,
    teste_pontuacoes_iguais_coexistem,
    teste_operacoes_aleatorias_contra_referencia,
]

def executar_testes(testes):
    for teste in testes:
        teste()
        print(f"  ✔ {teste.__name__}")
    print(f"\nTodos os {len(testes)} testes passaram.")


def _cenario_teste_padrao():
    cadastro, demandas, pos = criar_cenario_demonstracao()
    return Roteirizador(cadastro, demandas, pos, capacidade=30)


def teste_atualizacao_preserva_ordenacao():
    r = _cenario_teste_padrao(); r.inicializar()
    while not r.avl.vazia():
        r.avl.validar()
        # toda chave na árvore coincide com a pontuação vigente de sua parada
        for n in r.avl.em_ordem():
            assert n.chave == (r.prioridades[n.identificador].pontuacao, n.identificador)
        chaves = [n.chave for n in r.avl.em_ordem()]
        assert chaves == sorted(chaves)
        # a parada escolhida é exatamente a de maior pontuação vigente
        esperado = max(r.prioridades.values(), key=lambda p: (p.pontuacao, p.identificador))
        assert r.avl.maximo(contar=False).identificador == esperado.identificador
        r.passo()
    r.avl.validar()


def teste_parada_atendida_e_removida_e_nunca_reselecionada():
    r = _cenario_teste_padrao(); r.inicializar()
    selecionadas = []
    while not r.avl.vazia():
        proxima = r.avl.maximo(contar=False)
        chave = proxima.chave
        ident = proxima.identificador
        r.passo()
        selecionadas.append(ident)
        assert r.avl.buscar(chave) is None                                   # chave antiga sumiu
        assert ident not in [n.identificador for n in r.avl.em_ordem()]      # não está mais na AVL
        assert ident not in r.pendentes and ident in r.cadastro              # sai da rota, não do cadastro
    assert len(selecionadas) == len(set(selecionadas)) == len(r.cadastro)    # nenhuma repetida


def teste_encerramento_correto():
    r = _cenario_teste_padrao(); r.executar(verbose=False)
    assert r.avl.vazia() and not r.pendentes
    assert sorted(r.atendidas) == sorted(r.cadastro)
    assert r.onibus.ocupacao == 0 and r.nao_entregues == 0       # todos desembarcaram no destino certo
    assert r.total_embarcados == sum(p.embarque for p in r.cadastro.values())
    assert r.total_desembarcados == r.total_embarcados + 7        # 7 já estavam a bordo
    assert r.avl.consultas_maximo == len(r.cadastro) + 1         # uma por passo + a consulta final (vazia)
    assert r.passo() is False                                    # nada mais a fazer


def teste_desembarque_obrigatorio():
    # ônibus (capacidade 10) com 9 passageiros para F, que está longe e teria pontuação baixa.
    coords = {1: (1, 0), 2: (100, 100), 3: (60, 60)}
    demandas = [Demanda(None, 2, 9), Demanda(1, 3, 8)]           # N=P1 (perto, muita demanda), F=P2, Z=P3
    cad = montar_cadastro(coords, demandas)
    lotado = Roteirizador(cad, demandas, (0, 0), capacidade=10)
    lotado.executar(verbose=False)
    assert lotado.atendidas[0] == 2, "com o ônibus lotado, o desembarque em F é obrigatório e vem primeiro"
    assert lotado.passos[0].nivel == NIVEL_OBRIGATORIA
    folgado = Roteirizador(cad, demandas, (0, 0), capacidade=100)
    folgado.executar(verbose=False)
    assert folgado.atendidas[0] == 1, "sem lotação, vale a pontuação normal (N é próxima e tem demanda)"
    for r in (lotado, folgado):
        assert r.nao_entregues == 0 and r.avl.vazia()


def teste_dependencia_de_embarque():
    # C(3) -> A(2) -> B(1). B é perto e tem muita demanda a bordo, mas só pode ser atendida depois de A.
    coords = {1: (1, 1), 2: (90, 90), 3: (50, 0)}
    demandas = [Demanda(None, 1, 5), Demanda(2, 1, 3), Demanda(3, 2, 2)]
    r = Roteirizador(montar_cadastro(coords, demandas), demandas, (0, 0), capacidade=30)
    r.executar(verbose=False)
    assert r.atendidas == [3, 2, 1]
    assert r.nao_entregues == 0 and r.total_nao_embarcados == 0


def teste_capacidade_respeitada():
    coords = {1: (10, 10), 2: (50, 50)}
    demandas = [Demanda(1, 2, 25)]
    r = Roteirizador(montar_cadastro(coords, demandas), demandas, (0, 0), capacidade=10)
    r.executar(verbose=False)
    assert r.total_embarcados == 10 and r.total_nao_embarcados == 15
    assert max(p.ocupacao for p in r.passos) <= 10


def teste_distancias_iguais():
    # todas equidistantes: G = 1 para todas e sem divisão por zero
    calc = CalculadoraPrioridade()
    ctx = Contexto(0, 0, 10, False, {1: 2, 2: 2}, {1: 0, 2: 0}, {})
    res = calc.calcular([Parada(1, 5, 0, 2, 0), Parada(2, 0, 5, 2, 0)], ctx)
    assert res[1].G == res[2].G == 1.0 and res[1].base == res[2].base


TESTES_ROTEIRIZADOR = [
    teste_atualizacao_preserva_ordenacao,
    teste_parada_atendida_e_removida_e_nunca_reselecionada,
    teste_encerramento_correto,
    teste_desembarque_obrigatorio,
    teste_dependencia_de_embarque,
    teste_capacidade_respeitada,
    teste_distancias_iguais,
]


def executar_todos() -> None:
    print("Testes da Árvore AVL:")
    executar_testes(TESTES_AVL)
    print("\nTestes do Roteirizador:")
    executar_testes(TESTES_ROTEIRIZADOR)


if __name__ == "__main__":
    executar_todos()
