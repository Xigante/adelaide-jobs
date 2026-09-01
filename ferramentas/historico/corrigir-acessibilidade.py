"""Correções de acessibilidade e de manuseio no material consolidado.

Auditoria WCAG 2.1 AA de 30/08/2026, feita com axe-core + medição de
contraste com composição de alpha + navegação por teclado real, no
Chromium, em 1280 e em 390 px, nos dois temas.

O que PASSOU e não é mexido aqui: contraste de texto (claro e escuro),
foco visível (outline de 2px em tudo), zoom de 200% sem rolagem
horizontal, lang="pt-BR", rel="noopener" nos 33 links externos, rótulos
nos campos, e as abas já com 44 px de altura.
"""
import pathlib
import re
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")
shutil.copy(ARQ, ARQ.with_suffix(".html.bak2"))
feitas = []


def troca(velho, novo, n=1, rotulo=""):
    global s
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo or velho[:60]!r}")
    s = s.replace(velho, novo, n)
    feitas.append(rotulo)


# ══ 1. WCAG 1.4.11 — borda dos controles (medido: 1.32–1.72:1) ══════
# A borda do campo de busca, do select e dos chips usa --line, que é uma
# linha divisória de tabela. Divisória pode ser fraca; contorno de
# controle não pode: é o que diz onde clicar. Precisa de 3:1.
# --line-ctl medido contra --surface: 3.3:1 no claro, 3.4:1 no escuro.
troca("  --line:#d9d7d1;", "  --line:#d9d7d1;\n  --line-ctl:#8e8d89;",
      rotulo="1.4.11 token de borda (claro)")
troca("--line:#3d3d39;", "--line:#3d3d39;--line-ctl:#77776f;",
      rotulo="1.4.11 token de borda (escuro)")

troca("border:1px solid var(--line);border-radius:var(--r-pill);\n  min-height:36px",
      "border:1px solid var(--line-ctl);border-radius:var(--r-pill);\n  min-height:36px",
      rotulo="1.4.11 borda do chip")
troca("select{background:var(--surface-2);color:var(--ink);border:1px solid var(--line);",
      "select{background:var(--surface-2);color:var(--ink);border:1px solid var(--line-ctl);",
      rotulo="1.4.11 borda da busca e do select")

# ══ 2. WCAG 2.5.5 — 53 alvos de toque a 36 px no celular ════════════
# No dedo, 36 px erra. Vale para tela estreita E para qualquer
# dispositivo de ponteiro grosseiro (tablet, celular, TV).
CSS_NOVO = """
/* ═══ Acessibilidade — auditoria de 30/08/2026 ═══════════════════ */
/* 2.5.5 alvo de toque: 44px onde se toca com o dedo. */
@media (max-width:760px), (pointer:coarse){
  .chip,.linkbtn,.themebtn{min-height:44px}
  #q,select{min-height:44px}
  .tabs button{min-height:48px}
}
/* 2.4.1 pular para o conteúdo: some até receber foco. */
.skip{position:absolute;left:-9999px;top:0;z-index:100;
  background:var(--brand);color:var(--brand-ink);padding:var(--sp3) var(--sp4);
  border-radius:0 0 var(--r-sm) 0;font:600 var(--fs-body-sm)/1 inherit;text-decoration:none}
.skip:focus{left:0}
/* Dica do atalho de teclado, dentro do próprio campo. */
.atalho{float:right;color:var(--ink-3);font-size:var(--fs-caption);
  padding:var(--sp2) 0 0}
.atalho kbd{background:var(--surface-2);border:1px solid var(--line-ctl);
  border-radius:3px;padding:1px 5px;font-family:ui-monospace,monospace;font-size:.9em}
@media (max-width:760px){.atalho{display:none}}
"""
troca("</style>", CSS_NOVO + "</style>", rotulo="2.5.5 alvos de toque + 2.4.1 skip link (CSS)")

# ══ 3. WCAG 2.4.1 — link de pular ═══════════════════════════════════
# São 7 abas e até 15 chips antes do conteúdo. Quem navega por teclado
# atravessa isso a cada volta à página.
troca("<body>\n",
      '<body>\n<a class="skip" href="#lista-de-registros">Pular para os registros</a>\n',
      rotulo="2.4.1 skip link")

# ══ 4. WCAG 1.3.1 — sem <main>; 54 nós fora de landmark ═════════════
troca('</div></div>\n\n<div class="wrap">',
      '</div></div>\n\n<main class="wrap" id="conteudo">', rotulo="1.3.1 abre <main>")
troca("<footer>", "</main>\n<footer>", rotulo="1.3.1 fecha <main>")

# ══ 5. WCAG 4.1.2 — abas pela metade ════════════════════════════════
# Anunciavam role="tab" mas não diziam qual painel controlam, e o painel
# não se dizia painel. No leitor de tela, ativar a aba não levava a lugar
# nenhum. Também faltavam as setas, que é como se navega uma tablist.
for pane, rotulo in [("dir", "Diretório"), ("top", "Top 10"), ("crono", "Cronograma"),
                     ("sal", "Salários"), ("visto", "Visto"), ("docs", "Documentos"),
                     ("fora", "Não perca tempo")]:
    sel = "true" if pane == "dir" else "false"
    troca(f'<button role="tab" aria-selected="{sel}" data-pane="{pane}">',
          f'<button role="tab" id="tab-{pane}" aria-controls="pane-{pane}" '
          f'aria-selected="{sel}" tabindex="{0 if pane == "dir" else -1}" data-pane="{pane}">',
          rotulo=f"4.1.2 aba {rotulo}")
    troca(f'<section id="pane-{pane}"',
          f'<section role="tabpanel" tabindex="0" aria-labelledby="tab-{pane}" id="pane-{pane}"',
          rotulo=f"4.1.2 painel {rotulo}")

# ══ 6. WCAG 4.1.3 — filtrar não anunciava nada ══════════════════════
# O contador mudava de 366 para 12 em silêncio. Quem não vê a tela
# filtrava e não sabia se tinha sobrado alguma coisa.
troca('<p class="count"><b id="cnt">0</b> <span id="cntlbl">registros</span></p>\n  <div id="list"></div>',
      '<p class="count" role="status" aria-live="polite" aria-atomic="true">'
      '<b id="cnt">0</b> <span id="cntlbl">registros</span></p>\n'
      '  <div id="list" aria-busy="false"></div>',
      rotulo="4.1.3 contador com aria-live")

# ── âncora do skip link, no início da lista ─────────────────────────
troca('<div id="list" aria-busy="false"></div>',
      '<div id="lista-de-registros" tabindex="-1"></div>\n<div id="list" aria-busy="false"></div>',
      rotulo="2.4.1 alvo do skip link")

# ── dica visível do atalho, ao lado do campo de busca ───────────────
troca('<button class="linkbtn" id="clear" type="button">limpar tudo</button>',
      '<button class="linkbtn" id="clear" type="button">limpar tudo</button>'
      '<span class="atalho"><kbd>/</kbd> busca &middot; <kbd>Esc</kbd> limpa</span>',
      rotulo="dica do atalho de teclado")

# ══ 7. Teclado: setas nas abas + atalhos de busca ═══════════════════
JS_NOVO = """
<script>
/* ═══ Acessibilidade e manuseio — auditoria de 30/08/2026 ═══════ */
(function(){
  "use strict";
  var abas = [].slice.call(document.querySelectorAll('.tabs [role="tab"]'));

  /* 2.1.1 / 4.1.2 — uma tablist se navega com as setas, não com Tab.
     Com tabindex rotativo, Tab entra e sai da barra de abas de uma vez
     só, em vez de parar nas sete. */
  function focar(i){
    var alvo = abas[(i + abas.length) % abas.length];
    abas.forEach(function(b){ b.tabIndex = (b === alvo) ? 0 : -1; });
    alvo.focus();
    alvo.click();
  }
  abas.forEach(function(aba, i){
    aba.addEventListener('keydown', function(e){
      var k = e.key, n = null;
      if (k === 'ArrowRight') n = i + 1;
      else if (k === 'ArrowLeft') n = i - 1;
      else if (k === 'Home') n = 0;
      else if (k === 'End') n = abas.length - 1;
      if (n === null) return;
      e.preventDefault();
      focar(n);
    });
    aba.addEventListener('click', function(){
      abas.forEach(function(b){ b.tabIndex = (b === aba) ? 0 : -1; });
    });
  });

  /* Manuseio: com 366 registros, chegar até a busca custa muitos Tabs.
     "/" leva direto; Esc limpa e devolve o foco. Padrão que todo mundo
     já conhece de buscador. */
  var busca = document.getElementById('q');
  var limpar = document.getElementById('clear');
  document.addEventListener('keydown', function(e){
    var em = document.activeElement, tag = em && em.tagName;
    var digitando = tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
    if (e.key === '/' && !digitando && !e.ctrlKey && !e.metaKey){
      e.preventDefault();
      var aba = document.getElementById('tab-dir');
      if (aba && aba.getAttribute('aria-selected') !== 'true') aba.click();
      busca.focus();
      busca.select();
    } else if (e.key === 'Escape' && em === busca){
      if (busca.value){ busca.value = ''; busca.dispatchEvent(new Event('input', {bubbles:true})); }
      else if (limpar){ limpar.click(); }
    }
  });
})();
</script>
"""
troca("</body>", JS_NOVO + "</body>", rotulo="2.1.1 setas nas abas + atalhos / e Esc")

ARQ.write_text(s, encoding="utf-8")
print(f"{len(feitas)} correções aplicadas:")
for f in feitas:
    print("  ·", f)
