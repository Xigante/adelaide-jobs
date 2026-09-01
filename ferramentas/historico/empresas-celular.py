"""No celular, a aba Empresas abria com uma tela inteira de filtro.

Medido a 390px: o texto de abertura mais os 10 chips de setor mais o
seletor de ordem mais os dois chips de visitadas davam ~1.400px — a
primeira empresa só aparecia depois de rolar uma tela e meia.

É exatamente o problema que o Diretório já tinha e que foi resolvido em
31/08: a busca fica sempre à vista, porque é o que ele usa em quase
todo caso, e o resto entra num "Filtros" que abre e fecha, com a conta
de quantos estão ligados. No desktop nada muda — lá cabe tudo.

O texto de abertura também encolheu. Seis linhas para dizer o que a aba
é, num aparelho de 390px, é meia tela gasta antes do conteúdo.
"""
import pathlib
import shutil

ARQ = pathlib.Path(__file__).resolve().parent / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"


def troca(s, velho, novo, rotulo):
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    return s.replace(velho, novo, 1)


CSS = """
/* ═══ Aba Empresas no celular ═════════════════════════════════════ */
@media (max-width:760px){
  /* 1.400px de filtro grudado no topo não é sticky, é uma parede. */
  .emp-topo{position:static}
  #emp-mais-filtros[hidden]{display:none}
  #emp-mais-filtros{margin-top:var(--sp3)}
  .emp-topo .chip{padding:0 var(--sp3);font-size:var(--fs-micro);min-height:44px}
  .emp-topo select{max-width:100%}
  .emp-intro{font-size:var(--fs-body-sm)}
  .mais-btn #emp-mais-n:not(:empty){background:var(--brand);
    color:var(--brand-ink);border-radius:999px;padding:.1em .5em;
    font-size:var(--fs-micro);font-weight:700}
}
"""

JS = """
<script>
/* Filtros recolhíveis na aba Empresas — mesmo padrão do Diretório. */
(function(){
  "use strict";
  var btn = document.getElementById("emp-mais-btn");
  var caixa = document.getElementById("emp-mais-filtros");
  if (!btn || !caixa) return;

  function estreito(){ return window.matchMedia("(max-width:760px)").matches; }

  function contar(){
    var n = caixa.querySelectorAll('.chip[aria-pressed="true"]').length;
    var sel = document.getElementById("emp-ordem");
    if (sel && sel.value !== "vagas") n++;
    document.getElementById("emp-mais-n").textContent = n ? String(n) : "";
  }

  function aplicar(){
    caixa.hidden = estreito() && btn.getAttribute("aria-expanded") !== "true";
  }

  btn.addEventListener("click", function(){
    btn.setAttribute("aria-expanded",
      String(btn.getAttribute("aria-expanded") !== "true"));
    aplicar();
  });
  caixa.addEventListener("click", contar);
  var sel = document.getElementById("emp-ordem");
  if (sel) sel.addEventListener("change", contar);
  window.addEventListener("resize", aplicar);

  /* Começa fechado no celular: a busca resolve a maioria dos casos. */
  if (estreito()) btn.setAttribute("aria-expanded", "false");
  aplicar();
  contar();
})();
</script>
"""

INTRO_VELHA = """  <p class="rota-intro">Todas as empresas que já anunciaram vaga em Adelaide
  desde que a coleta começou — <b id="emp-total">0</b> delas. Uma vaga sai do
  ar em duas semanas; a empresa continua contratando o mesmo tipo de gente.
  Esta lista é sem curadoria, de propósito: é para procurar. O
  <b>Diretório</b> é o oposto — poucos, conferidos a mão.</p>"""

INTRO_NOVA = """  <p class="rota-intro emp-intro"><b id="emp-total">0</b> empresas que já
  anunciaram vaga em Adelaide. O anúncio some em duas semanas; a empresa
  continua contratando. Sem curadoria, de propósito — é para procurar.
  O <b>Diretório</b> é o oposto: poucos, conferidos a mão.</p>"""


s = ARQ.read_text(encoding="utf-8")
if "emp-mais-filtros" in s:
    raise SystemExit("já aplicado")
shutil.copy(ARQ, ARQ.with_suffix(".html.bak12"))

s = troca(s, INTRO_VELHA, INTRO_NOVA, "texto de abertura")

# ATENÇÃO à âncora: o Diretório TAMBÉM tem uma linha
# `<div class="frow"><span class="lbl">Setor</span>`, com a mesma
# indentação, desde que ele ganhou filtros recolhíveis. Ancorar só nela
# derrubava o botão dentro do bloco do Diretório, que no celular está
# hidden — e ainda deixava as divs desbalanceadas. A âncora tem que
# incluir o id que só existe aqui.
ANCORA_SETOR = ('    <div class="frow"><span class="lbl">Setor</span>\n'
                '      <div class="emp-tags" id="emp-setores"')
s = troca(s,
    ANCORA_SETOR,
    '    <button class="mais-btn" id="emp-mais-btn" type="button" aria-expanded="true"\n'
    '            aria-controls="emp-mais-filtros">Filtros <span id="emp-mais-n"></span></button>\n'
    '    <div id="emp-mais-filtros">\n'
    + ANCORA_SETOR,
    "abre o bloco de filtros")

s = troca(s,
    '<button class="chip" type="button" id="emp-esconder-visitadas" aria-pressed="false">esconder visitadas</button>\n    </div>',
    '<button class="chip" type="button" id="emp-esconder-visitadas" aria-pressed="false">esconder visitadas</button>\n'
    '    </div>\n    </div>',
    "fecha o bloco de filtros")

s = troca(s, "</style>", CSS + "</style>", "CSS do celular")
s = troca(s, "</body>", JS + "</body>", "JS dos filtros")

ARQ.write_text(s, encoding="utf-8")
print("aba Empresas: filtros recolhíveis no celular")
