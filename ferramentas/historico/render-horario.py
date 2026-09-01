"""Renderiza o horário como instrução e arruma a aba de rota no celular."""
import pathlib
import re

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")


def troca(velho, novo, rotulo):
    global s
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    s = s.replace(velho, novo, 1)


# ══ 1. CSS ═════════════════════════════════════════════════════════
CSS = """
/* ═══ Horário: instrução, não parágrafo ═══════════════════════════
   Antes era uma frase corrida com três orações. A pergunta que a
   pessoa faz — "vou antes ou depois?" — não aparecia em lugar nenhum.
   Agora são duas linhas, uma verde e uma vermelha, e o porquê fica em
   letra menor para quem quiser. */
.hora{display:grid;gap:var(--sp2);margin:var(--sp3) 0 0}
.hora-l{display:grid;grid-template-columns:auto auto 1fr;gap:var(--sp2) var(--sp3);
  align-items:baseline;font-size:var(--fs-body-sm);line-height:1.45}
.hora-i{font-weight:700;font-size:1.05em;line-height:1;width:1em;text-align:center}
.hora-r{font:700 var(--fs-micro)/1.4 inherit;text-transform:uppercase;
  letter-spacing:.07em;white-space:nowrap;padding-top:.15em}
.hora-v .hora-i,.hora-v .hora-r{color:var(--r-ganho-fg)}
.hora-n .hora-i,.hora-n .hora-r{color:var(--r-alerta-fg)}
.hora-v b{color:var(--ink);font-weight:700}
.hora-n span{color:var(--ink-2)}
.hora-pq{grid-column:1/-1;color:var(--ink-3);font-size:var(--fs-caption);
  line-height:1.5;margin:var(--sp1) 0 0;padding-left:calc(1em + var(--sp3))}
@media (max-width:560px){
  .hora-l{grid-template-columns:auto 1fr}
  .hora-r{grid-column:2;font-size:calc(var(--fs-micro) * 1.05)}
  .hora-l > :last-child{grid-column:2}
  .hora-pq{padding-left:0}
}

/* ═══ Rota no celular ═════════════════════════════════════════════
   O mapa de 380px comia a primeira tela e o botão principal ficava
   abaixo da dobra: a pessoa caía dentro de um mapa sem saber o que
   fazer. Em tela estreita a ordem passa a ser escolher a janela,
   apertar o botão, e só então o mapa. */
@media (max-width:899px){
  .rota-cols{display:flex;flex-direction:column}
  .rota-mapa-box{order:2}
  .rota-painel{order:1}
  .rota-painel .rota-acoes{order:0}
  #rota-mapa{height:300px}
  .rota-legenda{font-size:var(--fs-micro)}
  /* 7 chips de setor em 7 linhas era metade da tela. */
  .rota-setores .chip,.rota-jan .chip{padding:0 var(--sp3);font-size:var(--fs-micro)}
  .rota-setores .chip .dot{width:7px;height:7px}
  .rota-acoes{display:grid;grid-template-columns:1fr;gap:var(--sp2)}
  .rota-acoes .btn-primario,.rota-acoes .btn-maps{justify-content:center;width:100%}
  .rota-acoes .linkbtn{justify-self:center}
  /* Na rua, o botão do Maps é o que ele aperta. */
  .btn-maps:not([aria-disabled="true"]){background:var(--brand-soft);
    border-color:var(--brand);font-weight:700}
  .rota-lista li{padding-left:var(--sp8)}
  .rota-avisos p{font-size:var(--fs-caption)}
}
@media (max-width:420px){
  .rota-lista li{padding:var(--sp3) var(--sp3) var(--sp3) var(--sp8)}
  .rota-lista li::before{left:var(--sp2)}
}
"""
troca("</style>", CSS + "</style>", "CSS do horário e do celular")


# ══ 2. o componente, em JS ═════════════════════════════════════════
COMP = """
  /* Duas linhas e um porquê. Nada de parágrafo. */
  function horario(d, compacto){
    if (!d || !d.ir) return "";
    var online = d.jan === "online";
    return '<div class="hora">'+
      '<div class="hora-l hora-v"><span class="hora-i">'+(online?'✕':'✓')+'</span>'+
      '<span class="hora-r">'+(online?'Não vá':'Vá entre')+'</span>'+
      '<b>'+esc(d.ir)+'</b></div>'+
      '<div class="hora-l hora-n"><span class="hora-i">'+(online?'!':'✕')+'</span>'+
      '<span class="hora-r">'+(online?'Por quê':'Não vá')+'</span>'+
      '<span>'+esc(d.nao)+'</span></div>'+
      (compacto?"":'<p class="hora-pq">'+esc(d.jpq)+'</p>')+
    '</div>';
  }
"""
troca("  function filtrados(){", COMP + "\n  function filtrados(){", "função horario()")

# ── lista de paradas ───────────────────────────────────────────────
troca("""          '<span class="quando"><b>'+JANELA[d.jan]+'.</b> '+esc(d.jpq)+'</span></li>';""",
      """          horario(d)+'</li>';""", "horário na lista de paradas")

# ── popup do mapa ──────────────────────────────────────────────────
troca("""      '<span class="pq"><b style="display:inline">'+JANELA[d.jan]+'.</b> '+esc(d.jpq)+'</span>'+""",
      """      horario(d, true)+""", "horário no popup")


# ══ 3. no card do diretório também ═════════════════════════════════
# É lá que ele navega; o horário tem que estar onde a decisão é tomada.
troca("""${r.dica?`<p class="tip">${esc(r.dica)}</p>`:""}""",
      """${r.ir?horarioCard(r):""}
    ${r.dica?`<p class="tip">${esc(r.dica)}</p>`:""}""",
      "horário no card do diretório")

CARD = """
function horarioCard(r){
  var online = r.jan === "online";
  return `<div class="hora">
    <div class="hora-l hora-v"><span class="hora-i">${online?"✕":"✓"}</span>
    <span class="hora-r">${online?"Não vá":"Vá entre"}</span><b>${esc(r.ir)}</b></div>
    <div class="hora-l hora-n"><span class="hora-i">${online?"!":"✕"}</span>
    <span class="hora-r">${online?"Por quê":"Não vá"}</span><span>${esc(r.nao)}</span></div>
    <p class="hora-pq">${esc(r.jpq)}</p></div>`;
}
function card(r){"""
troca("function card(r){", CARD, "horarioCard() no escopo do diretório")

ARQ.write_text(s, encoding="utf-8")
scripts = re.findall(r"<script[^>]*>(.*?)</script>", s, re.S)
pathlib.Path("/tmp/c1.js").write_text(scripts[0], encoding="utf-8")
pathlib.Path("/tmp/c2.js").write_text(scripts[-1], encoding="utf-8")
print("renderização trocada · blocos de script:", [len(x) for x in scripts])
