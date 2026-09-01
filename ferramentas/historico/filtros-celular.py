"""No celular, os filtros comiam a tela inteira antes do primeiro resultado.

Medido em 390px: 7 chips de setor + 6 de chance + um select + 3 chips de
opção = cerca de 1.300px de filtro. E `.filters` é `position:sticky`,
então esse bloco de 1.300px ficava GRUDADO no topo enquanto você rolava
— não sobrava tela para o conteúdo.

Em tela estreita, a busca continua sempre visível (é o que ele usa em
90% das vezes) e o resto entra num "Filtros" que abre e fecha, com a
contagem de quantos estão ligados. No desktop nada muda: lá cabe tudo.
"""
import pathlib
import re

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")


def troca(velho, novo, rotulo):
    global s
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    s = s.replace(velho, novo, 1)


# ── 1. botão de abrir/fechar + embrulho nas três linhas de filtro ───
troca('<div class="frow"><span class="lbl">Setor</span>',
      '<button class="mais-btn" id="mais-btn" type="button" aria-expanded="true" '
      'aria-controls="mais-filtros">Filtros <span id="mais-n"></span></button>\n'
      '    <div id="mais-filtros">\n'
      '    <div class="frow"><span class="lbl">Setor</span>',
      "abre o bloco de filtros")

troca('<button class="chip" id="fview" type="button" aria-pressed="false">visão em tabela</button></div>\n  </div>',
      '<button class="chip" id="fview" type="button" aria-pressed="false">visão em tabela</button></div>\n'
      '    </div>\n  </div>',
      "fecha o bloco de filtros")

# ── 2. CSS ──────────────────────────────────────────────────────────
CSS = """
/* ═══ Filtros no celular ══════════════════════════════════════════ */
.mais-btn{display:none}
@media (max-width:760px){
  /* Um bloco de 1.300px grudado no topo não é "sticky", é uma parede. */
  .filters{position:static;padding:var(--sp3) var(--sp4)}
  .mais-btn{display:inline-flex;align-items:center;gap:var(--sp2);
    min-height:44px;padding:0 var(--sp4);margin-top:var(--sp2);
    background:var(--surface-2);border:1px solid var(--line-ctl);
    border-radius:var(--r-pill);color:var(--ink);font:600 var(--fs-body-sm)/1 inherit;
    cursor:pointer}
  .mais-btn::after{content:"▾";font-size:.85em;color:var(--ink-3)}
  .mais-btn[aria-expanded="true"]::after{content:"▴"}
  .mais-btn #mais-n:not(:empty){background:var(--brand);color:var(--brand-ink);
    border-radius:999px;padding:.1em .5em;font-size:var(--fs-micro);font-weight:700}
  #mais-filtros[hidden]{display:none}
  #mais-filtros{margin-top:var(--sp3)}
  .filters .chip{padding:0 var(--sp3);font-size:var(--fs-micro);min-height:44px}
  .filters .frow{margin-bottom:var(--sp2)}
  .lbl{font-size:var(--fs-micro)}
  select{max-width:100%}
}
"""
troca("</style>", CSS + "</style>", "CSS dos filtros no celular")

# ── 3. JS ───────────────────────────────────────────────────────────
JS = """
<script>
/* Filtros recolhíveis no celular — ver comentário no CSS. */
(function(){
  "use strict";
  var btn = document.getElementById("mais-btn");
  var caixa = document.getElementById("mais-filtros");
  if (!btn || !caixa) return;

  function estreito(){ return window.matchMedia("(max-width:760px)").matches; }

  function contar(){
    var n = document.querySelectorAll('#mais-filtros .chip[aria-pressed="true"]').length;
    var sel = document.getElementById("fregiao");
    if (sel && sel.value) n++;
    document.getElementById("mais-n").textContent = n ? String(n) : "";
  }

  function aplicar(){
    if (estreito()){
      var aberto = btn.getAttribute("aria-expanded") === "true";
      caixa.hidden = !aberto;
    } else {
      caixa.hidden = false;          /* no desktop cabe tudo, sempre aberto */
    }
  }

  btn.addEventListener("click", function(){
    btn.setAttribute("aria-expanded", String(btn.getAttribute("aria-expanded") !== "true"));
    aplicar();
  });
  document.getElementById("mais-filtros").addEventListener("click", contar);
  var sel = document.getElementById("fregiao");
  if (sel) sel.addEventListener("change", contar);
  var limpar = document.getElementById("clear");
  if (limpar) limpar.addEventListener("click", function(){ setTimeout(contar, 0); });
  window.addEventListener("resize", aplicar);

  /* Começa fechado no celular: a busca resolve a maioria dos casos. */
  if (estreito()) btn.setAttribute("aria-expanded", "false");
  aplicar();
  contar();
})();
</script>
"""
troca("</body>", JS + "</body>", "JS dos filtros")

ARQ.write_text(s, encoding="utf-8")
scripts = re.findall(r"<script[^>]*>(.*?)</script>", s, re.S)
pathlib.Path("/tmp/f.js").write_text(scripts[-1], encoding="utf-8")
print("filtros recolhíveis instalados · blocos:", [len(x) for x in scripts])
