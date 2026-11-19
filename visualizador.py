"""Visualização: mapa cartesiano, árvore AVL animada, tabelas de execução e gráfico de prioridades."""
from typing import Dict, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib import animation, rc
from matplotlib.lines import Line2D

from calculadora_prioridade import NIVEL_ADIADA, NIVEL_NORMAL, NIVEL_OBRIGATORIA
from roteirizador import Roteirizador

# Permite embutir animações maiores no HTML
rc("animation", embed_limit=80)


class Visualizador:
    COR_NIVEL = {NIVEL_OBRIGATORIA: "#f28b82", NIVEL_NORMAL: "#8ab4f8", NIVEL_ADIADA: "#d5d8dc"}
    COR_PENDENTE, COR_ATENDIDA, COR_DESTAQUE = "#1a73e8", "#34a853", "#f9ab00"

    def __init__(self, roteirizador: Roteirizador):
        self.r = roteirizador
        self.cadastro = roteirizador.cadastro

    # ---------- mapa cartesiano ----------
    def _desenhar_mapa(self, ax, q: dict) -> None:
        ax.set_xlim(-6, 106); ax.set_ylim(-6, 106); ax.set_aspect("equal")
        ax.grid(True, linestyle=":", alpha=0.5)
        ax.set_xlabel("X"); ax.set_ylabel("Y")
        ax.set_title(f"Mapa da cidade — ônibus com {q['ocupacao']}/{q['capacidade']} passageiros", fontsize=10)

        # trajeto percorrido (setas numeradas)
        pts = q["trajeto"]
        for k in range(1, len(pts)):
            (x1, y1), (x2, y2) = pts[k - 1], pts[k]
            ax.annotate("", xy=(x2, y2), xytext=(x1, y1),
                        arrowprops=dict(arrowstyle="-|>", color="#2e7d32", lw=1.8, shrinkA=9, shrinkB=11))
            ax.text((x1 + x2) / 2, (y1 + y2) / 2, str(k), fontsize=8, color="white", ha="center", va="center",
                    bbox=dict(boxstyle="circle,pad=0.2", fc="#2e7d32", ec="none"), zorder=6)

        # próxima parada (seta tracejada a partir da posição atual do ônibus)
        prox = q["proximo"]
        if prox is not None and q["fase"] != "remocao":
            p = self.cadastro[prox]
            ax.annotate("", xy=(p.x, p.y), xytext=q["onibus"],
                        arrowprops=dict(arrowstyle="-|>", color=self.COR_DESTAQUE, lw=2, ls="--",
                                        shrinkA=10, shrinkB=13))

        # paradas
        for i, p in self.cadastro.items():
            atendida = i in q["atendidas"]
            cor = self.COR_ATENDIDA if atendida else self.COR_PENDENTE
            ax.scatter(p.x, p.y, s=170, c=cor, edgecolors="white", linewidths=1.2, zorder=4)
            if i == prox and q["fase"] != "remocao":
                ax.scatter(p.x, p.y, s=420, facecolors="none", edgecolors=self.COR_DESTAQUE, linewidths=2.5, zorder=3)
            ax.text(p.x + 2.6, p.y + 2.6, p.rotulo, fontsize=10, fontweight="bold", zorder=7)
            if not atendida:
                e, d = q["estado"][i]
                ax.text(p.x + 2.6, p.y - 4.8, f"↑{e}  ↓{d}", fontsize=7.5, color="#444", zorder=7)

        # garagem e ônibus
        ax.scatter(*self.r.inicio, marker="D", s=90, c="black", zorder=5)
        ax.text(self.r.inicio[0] + 3.5, self.r.inicio[1] + 3.5, "Garagem", fontsize=8, ha="left")
        ax.scatter(*q["onibus"], marker="s", s=330, facecolors="none", edgecolors="black", linewidths=2, zorder=8)

        ax.legend(handles=[
            Line2D([], [], marker="o", ls="", color=self.COR_PENDENTE, label="pendente"),
            Line2D([], [], marker="o", ls="", color=self.COR_ATENDIDA, label="atendida"),
            Line2D([], [], marker="s", ls="", mfc="none", mec="black", mew=2, label="ônibus"),
            Line2D([], [], marker="D", ls="", color="black", label="garagem"),
        ], loc="upper left", fontsize=7.5, framealpha=0.9, bbox_to_anchor=(0, -0.08), ncol=4, frameon=False)
        ax.text(0.99, 0.01, "↑ aguardando embarque   ↓ a bordo com destino aqui", transform=ax.transAxes,
                ha="right", va="bottom", fontsize=7, color="#555")

    # ---------- árvore AVL ----------
    @staticmethod
    def _posicoes(raiz) -> Dict[int, Tuple[float, int]]:
        pos, contador = {}, [0]
        def rec(n, profundidade):
            if n is None:
                return
            rec(n["esq"], profundidade + 1)
            pos[n["id"]] = (contador[0], -profundidade)
            contador[0] += 1
            rec(n["dir"], profundidade + 1)
        rec(raiz, 0)
        return pos

    def _desenhar_arvore(self, ax, q: dict) -> None:
        total = len(self.cadastro)
        ax.set_xlim(-0.9, total - 0.1); ax.set_ylim(-4.7, 0.8); ax.axis("off")
        raiz = q["arvore"]
        altura = raiz["altura"] if raiz else 0
        ax.set_title(f"Árvore AVL — {len(q['estado'])} nós pendentes, altura {altura}", fontsize=10)
        if raiz is None:
            ax.text((total - 1) / 2, -2, "AVL vazia\n(todas as paradas foram atendidas)", ha="center", fontsize=12, color="#555")
            return
        pos = self._posicoes(raiz)
        deslocamento = (total - len(pos)) / 2          # centraliza a árvore
        P = lambda i: (pos[i][0] + deslocamento, pos[i][1])

        def arestas(n):
            for filho in (n["esq"], n["dir"]):
                if filho is not None:
                    (x1, y1), (x2, y2) = P(n["id"]), P(filho["id"])
                    ax.plot([x1, x2], [y1, y2], color="#888", lw=1.3, zorder=1)
                    arestas(filho)
        arestas(raiz)

        def nos(n):
            if n is None:
                return
            x, y = P(n["id"])
            destaque = (n["id"] == q["proximo"] and q["fase"] != "remocao")
            ax.scatter(x, y, s=1250, c=self.COR_NIVEL[n["nivel"]], zorder=3,
                       edgecolors=self.COR_DESTAQUE if destaque else "#555",
                       linewidths=3.8 if destaque else 1)
            ax.text(x, y + 0.02, f"P{n['id']}\n{n['base']:.2f}", ha="center", va="center", fontsize=8.5,
                    fontweight="bold", zorder=4)
            ax.text(x, y - 0.36, f"fb={n['fb']:+d}", ha="center", va="center", fontsize=6.5, color="#555", zorder=4)
            if destaque:
                ax.text(x, y + 0.40, "MAIOR →\npróxima", ha="center", va="bottom", fontsize=7.5,
                        color="#b06f00", fontweight="bold", zorder=5)
            nos(n["esq"]); nos(n["dir"])
        nos(raiz)

        ax.legend(handles=[
            Line2D([], [], marker="o", ls="", ms=11, mfc=self.COR_NIVEL[NIVEL_OBRIGATORIA], mec="#555", label="obrigatória"),
            Line2D([], [], marker="o", ls="", ms=11, mfc=self.COR_NIVEL[NIVEL_NORMAL], mec="#555", label="normal"),
            Line2D([], [], marker="o", ls="", ms=11, mfc=self.COR_NIVEL[NIVEL_ADIADA], mec="#555", label="adiada"),
        ], loc="lower center", ncol=3, fontsize=8, frameon=False, bbox_to_anchor=(0.5, -0.04))
        ax.text(0.0, 0.97, "esquerda = menor prioridade · direita = maior prioridade", transform=ax.transAxes,
                fontsize=7.5, color="#555", va="top")

    # ---------- quadro completo ----------
    def _desenhar_quadro(self, fig, ax_mapa, ax_arvore, titulo, rodape, q: dict) -> None:
        ax_mapa.clear(); ax_arvore.clear()
        self._desenhar_mapa(ax_mapa, q)
        self._desenhar_arvore(ax_arvore, q)
        titulo.set_text(q["titulo"])
        rodape.set_text(q["detalhe"])

    def _nova_figura(self):
        fig, (ax_mapa, ax_arvore) = plt.subplots(1, 2, figsize=(15, 7), gridspec_kw={"width_ratios": [1, 1.2]})
        fig.subplots_adjust(top=0.9, bottom=0.12, left=0.05, right=0.99, wspace=0.12)
        titulo = fig.suptitle("", fontsize=13, fontweight="bold")
        rodape = fig.text(0.5, 0.02, "", ha="center", fontsize=10, color="#333")
        return fig, ax_mapa, ax_arvore, titulo, rodape

    def mostrar_quadro(self, indice: int, salvar_em: Optional[str] = None) -> None:
        """Exibe (ou salva em PNG, se `salvar_em` for informado) um quadro estático (0 = estado inicial)."""
        fig, a1, a2, t, rd = self._nova_figura()
        self._desenhar_quadro(fig, a1, a2, t, rd, self.r.quadros[indice])
        self._finalizar(fig, salvar_em)

    @staticmethod
    def _finalizar(fig, salvar_em: Optional[str]) -> None:
        if salvar_em:
            fig.savefig(salvar_em, dpi=100)
            plt.close(fig)
        else:
            plt.show()

    def animacao(self, intervalo_ms: int = 2200) -> str:
        """Animação com controles de reprodução. Devolve o HTML (use salvar_animacao para gravar em arquivo)."""
        fig, a1, a2, t, rd = self._nova_figura()
        fig.set_dpi(75)
        quadros = self.r.quadros

        def atualizar(i):
            self._desenhar_quadro(fig, a1, a2, t, rd, quadros[i])
            return []

        anim = animation.FuncAnimation(fig, atualizar, frames=len(quadros), interval=intervalo_ms, blit=False)
        html = anim.to_jshtml(default_mode="once")
        plt.close(fig)
        return html

    def salvar_animacao(self, caminho: str) -> None:
        """Grava a animação (mapa + AVL) em um arquivo .html que abre em qualquer navegador."""
        with open(caminho, "w", encoding="utf-8") as f:
            f.write(self.animacao())

    # ---------- tabelas e gráficos de resultado ----------
    def tabela_execucao(self) -> pd.DataFrame:
        linhas = [{
            "Ordem": p.ordem, "Parada": f"P{p.identificador}", "Pontuação P": round(p.pontuacao, 3),
            "Nível": p.nivel, "Distância": round(p.distancia, 1),
            "Embarcados": p.embarcados, "Desembarcados": p.desembarcados,
            "A bordo após": p.ocupacao,
        } for p in self.r.passos]
        return pd.DataFrame(linhas).set_index("Ordem")

    def tabela_evolucao_prioridades(self) -> pd.DataFrame:
        ids = sorted(self.cadastro)
        linhas = []
        for k, hist in enumerate(self.r.historico_prioridades, start=1):
            linhas.append({f"P{i}": hist.get(i, float("nan")) for i in ids})
        return pd.DataFrame(linhas, index=pd.Index(range(1, len(linhas) + 1), name="Seleção nº"))

    def tabela_decomposicao_inicial(self) -> pd.DataFrame:
        linhas = []
        for i, pr in sorted(self.r.prioridades_iniciais.items()):
            linhas.append({"Parada": f"P{i}", "Distância": round(pr.distancia, 1),
                           "Aguardando (E bruto)": pr.embarque_efetivo, "A bordo p/ cá (D bruto)": pr.desembarque_bordo,
                           "E": round(pr.E, 2), "D": round(pr.D, 2), "G": round(pr.G, 2),
                           "P = 0,4E+0,4D+0,2G": round(pr.base, 3), "Nível": pr.nivel})
        return pd.DataFrame(linhas).set_index("Parada")

    def grafico_final(self, salvar_em: Optional[str] = None) -> None:
        fig, (a1, a2) = plt.subplots(1, 2, figsize=(15, 6.5), gridspec_kw={"width_ratios": [1, 1.2]})
        q = dict(self.r.quadros[-1]); q["proximo"] = None
        self._desenhar_mapa(a1, q)
        a1.set_title(f"Rota final — distância total {self.r.distancia_total:.1f}", fontsize=11)

        hist = self.r.historico_prioridades
        cores = plt.get_cmap("tab10")
        for n, i in enumerate(sorted(self.cadastro)):
            xs = [k for k, h in enumerate(hist, start=1) if i in h]
            ys = [hist[k - 1][i] for k in xs]
            a2.plot(xs, ys, marker="o", ms=4, lw=1.6, color=cores(n % 10), label=f"P{i}")
            if xs:  # destaca o momento em que a parada foi escolhida (último ponto)
                a2.scatter(xs[-1], ys[-1], s=160, facecolors="none", edgecolors="black", linewidths=1.8, zorder=5)
        a2.set_xticks(range(1, len(hist) + 1))
        a2.set_xlabel("Seleção nº (ordem de atendimento)"); a2.set_ylabel("Pontuação P (0 a 1)")
        a2.set_title("Como as prioridades mudam a cada deslocamento\n(círculo preto = parada escolhida naquele passo)", fontsize=10)
        a2.grid(True, linestyle=":", alpha=0.6)
        a2.legend(ncol=5, fontsize=8, loc="upper center", bbox_to_anchor=(0.5, -0.14), frameon=False)
        fig.tight_layout()
        self._finalizar(fig, salvar_em)
