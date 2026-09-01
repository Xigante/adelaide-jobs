"""Rota a pé: não bater duas vezes na mesma porta, e levar a rota junto.

TRÊS COISAS

1. QUEM JÁ FOI VISITADO SAI DA ROTA.
   É o pedido inteiro: montar de novo uma rota que já foi feita é
   desperdício de manhã. O chip "esconder quem já visitei" nasce
   LIGADO — o padrão é o comportamento certo, e desligar é a exceção.

2. MARCAR NA PRÓPRIA PARADA.
   Ele marca na rua, no celular, logo depois de entregar o currículo.
   Se para isso tiver que sair da rota e procurar a empresa noutra
   aba, não vai marcar. O botão fica na parada.

3. COPIAR A ROTA.
   Texto puro, para colar no WhatsApp ou nas notas. Na rua o celular
   perde sinal e a página pode não recarregar; o texto fica.

   navigator.clipboard não existe em file:// — o Chrome não considera
   arquivo local um contexto seguro. Por isso a cópia tem o caminho
   antigo, com textarea e execCommand, como reserva.

Este script também move o módulo Visitas para ANTES do script da rota:
a rota chama render() na carga, e precisa que window.Visitas já exista.

RODAR
    python rota-visitas.py
"""
import pathlib
import shutil

AQUI = pathlib.Path(__file__).resolve().parent
ARQ = AQUI / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"

MARCA_VISITAS = "/* ═══ Visitas ══════════════"
MARCA_ROTA = "/* ═══ Rota a pé — mapa real (Leaflet + OpenStreetMap) ═══"


def troca(s, velho, novo, rotulo):
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    return s.replace(velho, novo, 1)


CSS = """
/* ═══ Visitadas ═══════════════════════════════════════════════════ */
.rota-lista li[data-fui="1"]{background:var(--r-ganho-bg);
  border-color:var(--r-ganho-br)}
.fui{min-height:32px;padding:0 var(--sp3);margin-top:var(--sp2);
  border-radius:var(--r-pill);border:1px solid var(--line-ctl);
  background:transparent;color:var(--ink-2);
  font:600 var(--fs-micro)/1 inherit;cursor:pointer}
.fui:hover{border-color:var(--brand);color:var(--ink)}
li[data-fui="1"] .fui{border-color:var(--r-ganho-br);
  color:var(--r-ganho-fg);font-weight:700}
.btn-copiar{min-height:44px;padding:0 var(--sp5);border-radius:var(--r-sm);
  border:1px solid var(--line-ctl);background:var(--surface-2);color:var(--ink);
  font:600 var(--fs-body-sm)/1 inherit;cursor:pointer}
.btn-copiar:hover{border-color:var(--brand)}
.bkp{margin:var(--sp8) 0 0;padding:var(--sp4);background:var(--surface-2);
  border:1px solid var(--line);border-radius:var(--r-md)}
.bkp summary{cursor:pointer;font-weight:700;font-size:var(--fs-body-sm);
  min-height:44px;display:flex;align-items:center}
.bkp p{color:var(--ink-2);font-size:var(--fs-caption);line-height:1.55;
  margin:var(--sp2) 0}
.bkp textarea{width:100%;min-height:120px;margin-top:var(--sp2);
  font:400 var(--fs-micro)/1.5 ui-monospace,monospace;color:var(--ink);
  background:var(--surface);border:1px solid var(--line-ctl);
  border-radius:var(--r-sm);padding:var(--sp3);resize:vertical}
.bkp-acoes{display:flex;flex-wrap:wrap;gap:var(--sp2);margin-top:var(--sp3)}
"""

# ── o botão de copiar, na barra de ações da rota ───────────────────
BOTAO_COPIAR = (
    '<button class="btn-copiar" type="button" id="rota-copiar">Copiar a rota</button>\n'
    '        <button class="linkbtn" type="button" id="rota-limpar">'
)

# ── chip de esconder visitadas, junto dos chips de janela ──────────
CHIP_VISITADAS = (
    '<button class="chip" type="button" id="rota-sem-visitadas" '
    'aria-pressed="true">esconder quem já visitei</button>\n      </div>'
)

# ── caixa de backup, no fim da aba Empresas ────────────────────────
BACKUP = """
<details class="bkp">
  <summary>Backup das visitas</summary>
  <p>As empresas que você marcou ficam guardadas <b>no navegador deste
  aparelho</b>. Não existe servidor por trás desta página, então o arquivo
  no computador e o site no <code>xigante.github.io</code> são endereços
  diferentes e cada um tem a sua memória — marcar num não aparece no outro.</p>
  <p>Para levar de um para o outro: <b>Copiar</b> aqui, abrir o outro,
  colar no mesmo campo e apertar <b>Importar</b>. A importação junta,
  nunca apaga o que já estava lá.</p>
  <label for="bkp-texto" class="lbl">Suas visitas, em texto</label>
  <textarea id="bkp-texto" spellcheck="false"
    aria-describedby="bkp-aviso"></textarea>
  <div class="bkp-acoes">
    <button class="btn-copiar" type="button" id="bkp-copiar">Copiar</button>
    <button class="btn-copiar" type="button" id="bkp-importar">Importar o que está no campo</button>
  </div>
  <p class="emp-cont" id="bkp-aviso" role="status" aria-live="polite"></p>
</details>
"""

JS_BACKUP = """
<script>
/* ═══ Backup das visitas ═══════════════════════════════════════════
   localStorage é por origem. file:// e https://xigante.github.io são
   origens diferentes, então são duas memórias separadas. Isto é a
   ponte manual entre elas — e o único jeito, sem servidor. */
(function(){
  "use strict";
  var campo = document.getElementById("bkp-texto");
  var aviso = document.getElementById("bkp-aviso");
  if (!campo) return;

  function encher(){ campo.value = window.Visitas.exportar(); }
  encher();
  document.addEventListener("visitas:mudou", encher);

  document.getElementById("bkp-copiar").addEventListener("click", function(){
    window.copiarTexto(campo.value, function(ok){
      aviso.textContent = ok ? "Copiado. Cole no outro aparelho."
                             : "Não consegui copiar. Selecione o texto e use Ctrl+C.";
    });
  });

  document.getElementById("bkp-importar").addEventListener("click", function(){
    try {
      var n = window.Visitas.importar(campo.value);
      aviso.textContent = n + (n === 1 ? " visita nova importada."
                                       : " visitas novas importadas.");
    } catch (e) {
      aviso.textContent = "Esse texto não é um backup válido. " +
        "Cole exatamente o que o botão Copiar gerou do outro lado.";
    }
  });
})();
</script>
"""

JS_COPIAR = """
<script>
/* Copiar texto num arquivo local.

   navigator.clipboard só existe em contexto seguro, e o Chrome não
   considera file:// seguro. Como o material é aberto das duas formas —
   arquivo no computador e página no GitHub — precisa dos dois caminhos. */
window.copiarTexto = function(texto, pronto){
  function reserva(){
    var ta = document.createElement("textarea");
    ta.value = texto;
    ta.setAttribute("readonly", "");
    ta.style.cssText = "position:fixed;top:-1000px;opacity:0";
    document.body.appendChild(ta);
    ta.select();
    var ok = false;
    try { ok = document.execCommand("copy"); } catch (e) { ok = false; }
    document.body.removeChild(ta);
    pronto(ok);
  }
  if (navigator.clipboard && window.isSecureContext){
    navigator.clipboard.writeText(texto).then(function(){ pronto(true); }, reserva);
  } else {
    reserva();
  }
};
</script>
"""


def main() -> None:
    s = ARQ.read_text(encoding="utf-8")
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak9"))
    if 'id="rota-copiar"' in s:
        raise SystemExit("a rota já tem o copiar e o visitadas")

    # ── 1. Visitas tem que existir antes do script da rota ──────────
    ini = s.find("<script>\n" + MARCA_VISITAS)
    if ini < 0:
        raise SystemExit("ÂNCORA NÃO ENCONTRADA: bloco Visitas")
    fim = s.find("</script>", ini) + len("</script>\n")
    bloco_visitas = s[ini:fim]
    s = s[:ini] + s[fim:]
    alvo = s.find("<script>\n" + MARCA_ROTA)
    if alvo < 0:
        raise SystemExit("ÂNCORA NÃO ENCONTRADA: script da rota")
    s = s[:alvo] + JS_COPIAR + bloco_visitas + s[alvo:]

    # ── 2. CSS ──────────────────────────────────────────────────────
    s = troca(s, "</style>", CSS + "</style>", "CSS das visitadas")

    # ── 3. HTML ─────────────────────────────────────────────────────
    s = troca(s,
              '<button class="linkbtn" type="button" id="rota-limpar">',
              BOTAO_COPIAR, "botão copiar a rota")
    s = troca(s,
              '<button class="chip" type="button" data-jan="manha" aria-pressed="false">Manhã &middot; 9h–11h30</button>\n      </div>',
              '<button class="chip" type="button" data-jan="manha" aria-pressed="false">Manhã &middot; 9h–11h30</button>\n        '
              + CHIP_VISITADAS, "chip esconder visitadas")
    s = troca(s,
              '  <button class="emp-mais" type="button" id="emp-mais" hidden>mostrar mais 50</button>\n</section>',
              '  <button class="emp-mais" type="button" id="emp-mais" hidden>mostrar mais 50</button>\n'
              + BACKUP + '</section>', "caixa de backup")

    # ── 4. filtrados() passa a pular quem já foi visitado ───────────
    s = troca(s,
"""  function filtrados(){
    return PONTOS.filter(function(d){
      if (d.jan !== estado.jan) return false;
      if (estado.setores.size && !estado.setores.has(d.setor)) return false;
      return true;
    });
  }""",
"""  function jaFui(d){
    return !!(window.Visitas && window.Visitas.tem(d.empregador));
  }

  function filtrados(){
    return PONTOS.filter(function(d){
      if (d.jan !== estado.jan) return false;
      if (estado.setores.size && !estado.setores.has(d.setor)) return false;
      /* O pedido inteiro: refazer uma rota já feita é perder a manhã.
         Quem já recebeu currículo sai da lista de candidatos. */
      if (estado.semVisitadas && jaFui(d) && !estado.sel.has(d.id)) return false;
      return true;
    });
  }""", "filtrados() sem visitadas")

    s = troca(s,
              'var estado = {jan:"tarde", setores:new Set(), sel:new Set(), n:8};',
              'var estado = {jan:"tarde", setores:new Set(), sel:new Set(), n:8,\n'
              '                semVisitadas:true};', "estado.semVisitadas")

    # ── 5. botão "fui" em cada parada ───────────────────────────────
    s = troca(s,
"""        return '<li><span class="nome">'+esc(d.empregador)+""",
"""        var v = window.Visitas && window.Visitas.get(d.empregador);
        return '<li data-fui="'+(v?"1":"0")+'" data-emp="'+esc(d.empregador)+'">'+
          '<span class="nome">'+esc(d.empregador)+""", "li com data-fui")

    s = troca(s,
"""          '<span class="andar">'+trecho+'</span>'+
          horario(d)+'</li>';""",
"""          '<span class="andar">'+trecho+'</span>'+
          horario(d)+
          '<button class="fui" type="button">'+
            (v ? "✓ entreguei em "+v.data.slice(8,10)+"/"+v.data.slice(5,7)
               : "marcar que entreguei aqui")+'</button>'+
          '</li>';""", "botão fui na parada")

    # ── 6. handlers ─────────────────────────────────────────────────
    s = troca(s,
"""  var caixa = document.getElementById("rota-setores");""",
"""  /* Marcar acontece na rua, no celular, logo depois de entregar. Se
     precisar sair da rota para marcar, ele não marca. */
  document.getElementById("rota-lista").addEventListener("click", function(e){
    var b = e.target.closest && e.target.closest(".fui");
    if (!b) return;
    var nome = b.closest("li").dataset.emp;
    if (window.Visitas.tem(nome)) {
      window.Visitas.desmarcar(nome);
    } else {
      var nota = window.prompt("O que aconteceu?  (pode deixar em branco)\\n\\n" + nome, "");
      if (nota === null) return;
      window.Visitas.marcar(nome, nota);
    }
    render();
  });

  var chipVis = document.getElementById("rota-sem-visitadas");
  if (chipVis) chipVis.addEventListener("click", function(){
    estado.semVisitadas = chipVis.getAttribute("aria-pressed") !== "true";
    chipVis.setAttribute("aria-pressed", String(estado.semVisitadas));
    render();
  });

  /* Texto puro. Na rua o sinal cai e a página pode não recarregar;
     o que está colado nas notas do celular continua lá. */
  function rotaEmTexto(rota){
    if (!rota.length) return "";
    var metros = Math.round(comprimento(rota));
    var andando = Math.round(metros/80);
    var linhas = [
      "ROTA A PÉ — " + rota.length + " paradas · " + (metros/1000).toFixed(1) +
        " km · " + andando + " min andando",
      "Janela: " + JANELA[estado.jan] + ". Saindo e voltando ao ILSC, " + ILSC.end,
      ""
    ];
    var ant = ILSC;
    rota.forEach(function(d, i){
      var passo = Math.round(dist(ant, d)); ant = d;
      linhas.push((i+1) + ". " + d.empregador + (d.unidade ? " — " + d.unidade : ""));
      linhas.push("   " + d.endereco);
      if (d.ir)  linhas.push("   IR:     " + d.ir);
      if (d.nao) linhas.push("   EVITAR: " + d.nao);
      linhas.push("   " + passo + " m da parada anterior");
      linhas.push("");
    });
    var u = linkGoogle(rota);
    if (u) linhas.push("Mapa: " + u);
    return linhas.join("\\n");
  }

  document.getElementById("rota-copiar").addEventListener("click", function(){
    var rota = rotear(filtrados().filter(function(d){ return estado.sel.has(d.id); }));
    var botao = document.getElementById("rota-copiar");
    if (!rota.length){
      botao.textContent = "Monte a rota primeiro";
      setTimeout(function(){ botao.textContent = "Copiar a rota"; }, 2000);
      return;
    }
    window.copiarTexto(rotaEmTexto(rota), function(ok){
      botao.textContent = ok ? "✓ Copiado" : "Não consegui copiar";
      setTimeout(function(){ botao.textContent = "Copiar a rota"; }, 2000);
    });
  });

  var caixa = document.getElementById("rota-setores");""", "handlers da rota")

    # ── 7. mensagem de lista vazia mais honesta na aba Empresas ─────
    s = troca(s,
"""    lista.innerHTML = todas.slice(0, mostrando).map(linha).join("") ||
      '<li class="emp-vazio">Nenhuma empresa com esse filtro.</li>';""",
"""    lista.innerHTML = todas.slice(0, mostrando).map(linha).join("") ||
      '<li class="emp-vazio">' + (
        soVis.getAttribute("aria-pressed") === "true"
          ? "Você ainda não marcou nenhuma visita com esses filtros."
          : "Nenhuma empresa com esse filtro."
      ) + '</li>';""", "mensagem de vazio")

    s = troca(s, "</body>", JS_BACKUP + "</body>", "script do backup")

    ARQ.write_text(s, encoding="utf-8")
    print(f"rota com visitadas e copiar · material {ARQ.stat().st_size/1024:.0f} KB")
    print(f"backup do anterior: {ARQ.name}.bak9")


if __name__ == "__main__":
    main()
