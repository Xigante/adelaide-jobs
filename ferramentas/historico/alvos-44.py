"""Os botões novos estavam com 32px de altura. Na rua isso não se aperta.

O material inteiro segue 44×44 desde a auditoria de 30/08 (WCAG 2.5.5).
Os três controles que entraram hoje ficaram fora do padrão:

    .emp-marcar   100×32   "marcar que fui"
    .fui          213×32   "marcar que entreguei aqui"
    #emp-q        268×40   a busca da aba Empresas

E são justamente os que ele vai apertar andando, no celular, com uma
mão só e o currículo na outra. A busca do Diretório já tem 44 — a nova
tinha 40 só porque a regra antiga é `.filters input` e a aba nova não
está dentro de `.filters`.

Medido com Playwright, não no olho.
"""
import pathlib
import shutil

ARQ = pathlib.Path(__file__).resolve().parent / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"

CSS = """
/* ═══ Alvos de toque dos controles novos ══════════════════════════
   44×44 é o mínimo do material inteiro. Estes três são apertados na
   rua, andando, com uma mão — não é lugar de economizar pixel. */
.emp-marcar,.fui{min-height:44px;padding:0 var(--sp4)}
.emp-topo input[type=search]{min-height:44px;padding:0 var(--sp3);
  border:1px solid var(--line-ctl);border-radius:var(--r-sm);
  background:var(--surface);color:var(--ink);font:400 var(--fs-body-sm)/1 inherit;
  flex:1;min-width:0}
.emp-topo select{min-height:44px}
.emp-topo .frow{display:flex;align-items:center;gap:var(--sp3);
  flex-wrap:wrap;margin-bottom:var(--sp2)}
"""

s = ARQ.read_text(encoding="utf-8")
if ".emp-marcar,.fui{min-height:44px" in s:
    raise SystemExit("já aplicado")
shutil.copy(ARQ, ARQ.with_suffix(".html.bak11"))
ARQ.write_text(s.replace("</style>", CSS + "</style>", 1), encoding="utf-8")
print("alvos de toque corrigidos para 44px")
