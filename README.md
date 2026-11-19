# Sistema Inteligente de Definição de Rotas de Transporte Público com Árvore AVL

Projeto acadêmico demonstrativo em Python. Uma **Árvore AVL implementada manualmente** é o núcleo decisório da roteirização: ela mantém as paradas pendentes ordenadas por prioridade e entrega a próxima parada a ser atendida (o nó mais à direita) em O(log n), sem varrer as paradas.

## Arquivos

| Arquivo | Descrição |
|---|---|
| `rotas_onibus_avl.ipynb` | Notebook para o Google Colab, com código, testes, visualizações e explicações, em ordem de execução. |
| `rotas_onibus_avl.py` | O mesmo código em um único script, com as células marcadas por `# %%` (útil em VS Code/Spyder). Usa `IPython.display`, então deve ser executado em ambiente Jupyter/IPython. |
| `README.md` | Este arquivo. |

## Como executar

1. Acesse [colab.research.google.com](https://colab.research.google.com/drive/1kHaLLzGIM3pzurV1jOshmNyBsHUuP7Es?usp=sharing) e escolha **Arquivo ▸ Fazer upload de notebook**.
2. Execute **Ambiente de execução ▸ Executar tudo**, ou rode as células em ordem.

Não há instalação extra: o notebook usa apenas `matplotlib`, `pandas` e `IPython`, já disponíveis no Colab. Localmente, são necessários Python 3.9+ e essas três bibliotecas (por exemplo, em Jupyter).

## Como o algoritmo funciona

1. **Inicialização:** calcula a pontuação de cada parada e insere todas na AVL com a chave `(pontuação, identificador)`.
2. **Seleção:** `avl.maximo()` devolve o nó mais à direita, a parada mais prioritária (O(log n)).
3. **Deslocamento e atendimento:** o ônibus vai até a parada, desembarca quem tem destino ali e embarca quem aguarda, respeitando a capacidade.
4. **Remoção:** a parada atendida sai da AVL da rota (o cadastro geral permanece) e não é mais selecionada.
5. **Atualização:** as distâncias e pontuações das paradas restantes são recalculadas. Cada nó é removido com a chave antiga e reinserido com a chave nova (nenhuma chave é alterada dentro da árvore).
6. **Repetição** até a AVL ficar vazia.

### Pontuação de prioridade

`P = 0,4·E + 0,4·D + 0,2·G`

| Fator | Significado | Normalização |
|---|---|---|
| E | Passageiros aguardando embarque (limitados às vagas livres) | `valor / maior valor entre as pendentes` |
| D | Passageiros a bordo com destino à parada | `valor / maior valor entre as pendentes` |
| G | Proximidade (distância euclidiana do ônibus) | `1 − (d − d_min)/(d_max − d_min)`; se todas as distâncias forem iguais, `G = 1` |

### Níveis de prioridade

O nível é somado à pontuação (como `P ∈ [0, 1]`, os níveis nunca se misturam):

- **OBRIGATÓRIA (+10):** ônibus com 80 % da capacidade ou mais, passageiros a bordo com destino à parada e ninguém esperando em outra parada para ir até ela.
- **NORMAL (0):** caso geral.
- **ADIADA (−10):** ainda há passageiros esperando em outras paradas com destino a ela. Como cada parada é visitada uma única vez, visitá-la antes deixaria essas pessoas sem entrega.

## Estrutura do código

| Classe | Responsabilidade |
|---|---|
| `Parada`, `Demanda`, `Onibus` | Dados do cadastro, grupos de passageiros (origem → destino) e estado do veículo. |
| `NoAVL`, `ArvoreAVL` | Inserção, remoção, busca, consulta ao máximo, altura, fator de balanceamento, 4 rotações, 3 percursos e `validar()`. |
| `CalculadoraPrioridade` | Distâncias, normalização, pontuação e níveis. |
| `Roteirizador` | Ciclo completo da rota e métricas. |
| `Visualizador` | Mapa cartesiano, AVL animada, tabelas e gráficos. |

## Cenário de demonstração

10 paradas distribuídas de forma não linear em um plano 100 × 100, ônibus com capacidade 30, partindo da garagem em (50, 50) com 7 passageiros a bordo.

Resultado obtido:

- Rota: Garagem → P8 → P2 → P1 → P3 → P5 → P6 → P4 → P7 → P9 → P10
- Distância total: 401,2 · embarcados: 48 · desembarcados: 55 · não entregues: 0
- AVL: altura máxima 4, 55 inserções, 55 remoções, 33 rotações elementares, 11 consultas ao máximo

A primeira parada escolhida (P8) não é a mais próxima (P2) nem a de maior embarque (P1): a escolha vem da combinação dos fatores.

## Visualizações

- Mapa cartesiano com paradas pendentes e atendidas, garagem, ônibus e trajeto numerado.
- AVL com identificador, pontuação, fator de balanceamento e destaque para o nó de maior prioridade.
- Animação com duas fotografias por passo: remoção da parada atendida e atualização das prioridades (com as rotações ocorridas no rodapé).
- Tabela de acompanhamento, resumo da rota, evolução das prioridades e tabela de métricas.

## Testes

Executados automaticamente pelo notebook (13 testes):

- **AVL:** balanceamento após inserções e após cada remoção, as quatro rotações, consulta ao máximo, pontuações iguais coexistindo, e operações aleatórias comparadas com uma referência.
- **Roteirização:** atualização de prioridades preserva a ordenação, parada atendida é removida e nunca reselecionada, encerramento correto, desembarque obrigatório, dependência de embarque, capacidade respeitada e distâncias iguais.

## Complexidade

| Operação | Complexidade |
|---|---|
| Busca | O(log n) |
| Inserção | O(log n) |
| Remoção | O(log n) |
| Consulta ao maior elemento | O(log n) |
| Cálculo das prioridades de todas as paradas restantes | O(n) por atualização |
| Reorganização de n paradas por inserções/remoções individuais | O(n log n) |

A consulta à parada prioritária é O(log n), mas o algoritmo completo **não** é: com n deslocamentos, cada um exigindo recálculo e reordenação, o custo total da roteirização é **O(n² log n)**.

## Limitações

- É uma **heurística gulosa**: decide com base no estado atual e não garante a menor rota global.
- A distância euclidiana é apenas uma aproximação da distância geográfica real.
- Cada parada é visitada **uma única vez**; fluxos cíclicos de passageiros (A→B e B→A) não podem ser atendidos por completo, e os passageiros afetados são contabilizados como "não embarcados".
- Uma aplicação real consideraria malha viária e sentido das ruas, tempo de deslocamento, múltiplos veículos, horários e frequência, restrições operacionais e novas demandas durante a execução.
