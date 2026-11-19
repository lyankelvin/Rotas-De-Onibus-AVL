"""
Demonstração: roteirização de transporte público com Árvore AVL.

Execute:  python main.py
Gera na pasta `saida/`: quadro_inicial.png, grafico_final.png e animacao_rota.html
(a animação abre em qualquer navegador). Tabelas e métricas são impressas no terminal.
"""
import os

import pandas as pd

from dados import criar_cenario_demonstracao
from roteirizador import Roteirizador
from testes import executar_todos
from visualizador import Visualizador

PASTA_SAIDA = "saida"


def imprimir(titulo: str, tabela) -> None:
    print(f"\n{titulo}")
    print(tabela.to_string())


def main() -> None:
    os.makedirs(PASTA_SAIDA, exist_ok=True)

    # 1) testes automáticos
    executar_todos()

    # 2) cenário e execução da rota
    cadastro, demandas, posicao_inicial = criar_cenario_demonstracao()
    roteirizador = Roteirizador(cadastro, demandas, posicao_inicial, capacidade=30)
    imprimir("Cadastro das paradas:", pd.DataFrame(
        [{"Parada": p.rotulo, "X": p.x, "Y": p.y, "Aguardando embarque": p.embarque,
          "Com destino à parada": p.desembarque} for p in cadastro.values()]).set_index("Parada"))
    print(f"\nÔnibus: garagem em {posicao_inicial}, capacidade {roteirizador.onibus.capacidade}, "
          f"{roteirizador.onibus.ocupacao} passageiros a bordo no início.\n")
    roteirizador.executar()          # imprime uma linha por passo
    roteirizador.avl.validar()       # a AVL continua válida ao final

    # 3) resultados
    v = Visualizador(roteirizador)
    imprimir("Decomposição da primeira pontuação:", v.tabela_decomposicao_inicial())
    imprimir("Acompanhamento da execução:", v.tabela_execucao())
    rota = " → ".join(["Garagem"] + [f"P{p.identificador}" for p in roteirizador.passos])
    print(f"\nRESUMO DA ROTA FINAL\n  {rota}")
    print(f"  Distância total: {roteirizador.distancia_total:.1f} | embarcados: {roteirizador.total_embarcados} | "
          f"desembarcados: {roteirizador.total_desembarcados} | não entregues: {roteirizador.nao_entregues}")
    imprimir("Evolução das prioridades (P no instante de cada seleção):",
             v.tabela_evolucao_prioridades().round(2).fillna("—"))
    print("\nMétricas:")
    for nome, valor in roteirizador.metricas().items():
        print(f"  {nome}: {valor}")

    # 4) figuras
    v.mostrar_quadro(0, salvar_em=os.path.join(PASTA_SAIDA, "quadro_inicial.png"))
    v.grafico_final(salvar_em=os.path.join(PASTA_SAIDA, "grafico_final.png"))
    v.salvar_animacao(os.path.join(PASTA_SAIDA, "animacao_rota.html"))
    print(f"\nArquivos gerados em '{PASTA_SAIDA}/'.")


if __name__ == "__main__":
    main()
