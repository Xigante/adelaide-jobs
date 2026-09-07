"""Aba Empresas: o cadastro de quem já contratou em Adelaide.

POR QUE ELA EXISTE
    O anúncio sai do ar em duas semanas e leva o nome da empresa junto.
    Mas a empresa continua lá, e continua contratando o mesmo tipo de
    gente. Esta aba é a lista de portas em que vale a pena bater com
    currículo impresso — 2.995 delas, com o que cada uma costuma pedir.

    O Diretório continua sendo o que é: 269 empregadores escolhidos a
    mão, com endereço conferido e opinião sobre a chance. Aqui é o
    oposto: tudo que apareceu, sem curadoria, para busca.

DE ONDE VEM O DADO
    adelaide-jobs/exports/empregadores.json, gerado pelo `export` a cada
    coleta. Este script embute o arquivo dentro do HTML — não dá para
    ler de fora, porque o material também é aberto como arquivo local
    (file://) e aí o navegador bloqueia fetch.

RODAR
    python aba-empresas.py

    Pode rodar quantas vezes quiser. Na primeira, monta a aba; nas
    seguintes, só troca o dado embutido pelo cadastro mais recente.
    O ATUALIZAR-VAGAS.bat chama este script sozinho no fim da coleta.
"""
import datetime
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import re
import shutil

import caminhos


def _escrever(caminho, texto: str) -> None:
    """Grava sempre com quebra de linha \n.

    O write_text() do Windows troca todo \n por \r\n. O material tem
    1.761 linhas: com CRLF o git enxerga o arquivo INTEIRO como mudado
    a cada coleta, e a mudanca de verdade (uma linha, a dos dados das
    empresas) some no meio de 3.522 linhas de ruido.
    """
    with open(caminho, "w", encoding="utf-8", newline="\n") as f:
        f.write(texto)

ARQ = caminhos.material()
DADOS = caminhos.empregadores_json()


def troca(s: str, velho: str, novo: str, rotulo: str) -> str:
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    return s.replace(velho, novo, 1)


# ══════════════════════════════════════════════════════════════════════
CSS = """
/* ═══ Aba Empresas ════════════════════════════════════════════════
   2.995 linhas. Duas decisões mandam no desenho:

   1. Nunca renderizar tudo. O navegador do celular engasga em 3.000
      nós; a lista mostra 50 e cresce sob demanda.
   2. A linha responde uma pergunta só — "vale a pena bater nesta
      porta?" — então mostra o que decide isso: quantas vagas ela já
      teve, o que ela pede, onde fica, e se eu já fui lá. */
.emp-topo{position:sticky;top:0;z-index:5;background:var(--surface);
  border-bottom:1px solid var(--line);padding:var(--sp3) var(--sp4);
  margin:0 calc(var(--sp4) * -1) var(--sp4)}
.emp-cont{color:var(--ink-3);font-size:var(--fs-caption);
  margin:var(--sp2) 0 0;font-variant-numeric:tabular-nums}
.emp-lista{display:grid;gap:var(--sp2);margin:0;padding:0;list-style:none}
.emp{display:grid;grid-template-columns:1fr auto;gap:var(--sp1) var(--sp3);
  padding:var(--sp3) var(--sp4);background:var(--surface-2);
  border:1px solid var(--line);border-radius:var(--r-md)}
.emp-nome{font-weight:700;color:var(--ink);font-size:var(--fs-body-sm);
  line-height:1.35;overflow-wrap:anywhere}
.emp-nums{display:flex;flex-direction:column;align-items:flex-end;gap:2px;
  font-variant-numeric:tabular-nums;white-space:nowrap}
.emp-vagas{font-weight:700;font-size:var(--fs-body-sm);color:var(--ink)}
.emp-nota{font-size:var(--fs-micro);color:var(--ink-3)}
.emp-tags{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:var(--sp1);
  align-items:center}
.emp-tag{font-size:var(--fs-micro);font-weight:700;padding:.15em .6em;
  border-radius:var(--r-pill);background:var(--surface-3);color:var(--ink-2)}
.emp-cargos{grid-column:1/-1;color:var(--ink-2);font-size:var(--fs-caption);
  line-height:1.5}
.emp-cargos b{color:var(--ink);font-weight:600}
.emp-pe{grid-column:1/-1;display:flex;flex-wrap:wrap;gap:var(--sp3);
  align-items:center;color:var(--ink-3);font-size:var(--fs-micro);
  margin-top:var(--sp1)}
.emp-pe a{color:var(--brand)}
.emp-marcar{min-height:32px;padding:0 var(--sp3);border-radius:var(--r-pill);
  border:1px solid var(--line-ctl);background:transparent;color:var(--ink-2);
  font:600 var(--fs-micro)/1 inherit;cursor:pointer}
.emp-marcar:hover{border-color:var(--brand);color:var(--ink)}
.emp[data-visitada="1"]{background:var(--r-ganho-bg);
  border-color:var(--r-ganho-br)}
.emp[data-visitada="1"] .emp-marcar{border-color:var(--r-ganho-br);
  color:var(--r-ganho-fg);font-weight:700}
.emp-mais{margin:var(--sp4) auto 0;display:block;min-height:44px;
  padding:0 var(--sp6);border-radius:var(--r-pill);
  border:1px solid var(--line-ctl);background:var(--surface-2);
  color:var(--ink);font:700 var(--fs-body-sm)/1 inherit;cursor:pointer}
.emp-vazio{padding:var(--sp8) var(--sp4);text-align:center;color:var(--ink-3)}
@media (min-width:760px){
  .emp{grid-template-columns:1fr auto auto;align-items:baseline}
  .emp-cargos{grid-column:1/-1}
}
@media (max-width:560px){
  .emp-topo{position:static;margin-bottom:var(--sp3)}
  .emp{padding:var(--sp3)}
}
"""


# ══════════════════════════════════════════════════════════════════════
HTML_ABA = (
    '<button role="tab" id="tab-emp" aria-controls="pane-emp" '
    'aria-selected="false" tabindex="-1" data-pane="emp">Empresas</button>\n  '
)

HTML_PAINEL = """
<section role="tabpanel" tabindex="0" aria-labelledby="tab-emp" id="pane-emp" hidden>
  <p class="rota-intro">Todas as empresas que já anunciaram vaga em Adelaide
  desde que a coleta começou — <b id="emp-total">0</b> delas. Uma vaga sai do
  ar em duas semanas; a empresa continua contratando o mesmo tipo de gente.
  Esta lista é sem curadoria, de propósito: é para procurar. O
  <b>Diretório</b> é o oposto — poucos, conferidos a mão.</p>

  <div class="emp-topo">
    <div class="frow"><span class="lbl">Buscar</span>
      <input type="search" id="emp-q" placeholder="Nome da empresa, cargo, bairro…"
             aria-label="Buscar empresa">
      <button class="linkbtn" type="button" id="emp-limpar">limpar</button>
    </div>
    <div class="frow"><span class="lbl">Setor</span>
      <div class="emp-tags" id="emp-setores" role="group" aria-label="Setor"></div>
    </div>
    <div class="frow"><span class="lbl">Ordem</span>
      <select id="emp-ordem" aria-label="Ordenar por">
        <option value="vagas">mais vagas primeiro</option>
        <option value="nota">melhor nota primeiro</option>
        <option value="recente">quem anunciou mais recentemente</option>
        <option value="nome">ordem alfabética</option>
      </select>
      <button class="chip" type="button" id="emp-so-visitadas" aria-pressed="false">só as visitadas</button>
      <button class="chip" type="button" id="emp-esconder-visitadas" aria-pressed="false">esconder visitadas</button>
    </div>
    <p class="emp-cont" id="emp-cont" role="status" aria-live="polite"></p>
  </div>

  <ul class="emp-lista" id="emp-lista"></ul>
  <button class="emp-mais" type="button" id="emp-mais" hidden>mostrar mais 50</button>
</section>
"""


# ══════════════════════════════════════════════════════════════════════
# O módulo de visitas fica aqui porque a aba Empresas é a primeira a
# usá-lo. A aba Rota usa o mesmo objeto — marcar numa aparece na outra.
JS_VISITAS = """
<script>
/* ═══ Visitas ══════════════════════════════════════════════════════
   Que portas eu já bati. Guardado no navegador (localStorage), porque
   este arquivo não tem servidor nenhum atrás dele.

   ATENÇÃO, e é uma limitação real: o arquivo no seu computador e a
   página no xigante.github.io são endereços diferentes para o
   navegador, então cada um tem a sua memória. Marcar num não aparece
   no outro. Por isso existe o botão de backup: ele copia tudo em
   texto, e cola de volta do outro lado. */
window.Visitas = (function(){
  "use strict";
  var CHAVE = "adelaide:visitas:v1";
  var mem = {};              /* fallback quando o navegador barra o storage */

  function normal(nome){
    return String(nome || "").toLowerCase()
      .normalize("NFD").replace(/[\\u0300-\\u036f]/g, "")
      .replace(/[^a-z0-9]/g, "");
  }
  function ler(){
    try {
      var cru = window.localStorage.getItem(CHAVE);
      return cru ? JSON.parse(cru) : {};
    } catch (e) { return mem; }
  }
  function gravar(d){
    mem = d;
    try { window.localStorage.setItem(CHAVE, JSON.stringify(d)); }
    catch (e) { /* modo privado, ou storage desligado: fica só em memória */ }
    document.dispatchEvent(new CustomEvent("visitas:mudou"));
  }
  return {
    chave: normal,
    tem: function(nome){ return !!ler()[normal(nome)]; },
    get: function(nome){ return ler()[normal(nome)] || null; },
    todas: ler,
    quantas: function(){ return Object.keys(ler()).length; },
    marcar: function(nome, nota){
      var d = ler();
      d[normal(nome)] = {
        nome: nome,
        data: new Date().toISOString().slice(0, 10),
        nota: nota || ""
      };
      gravar(d);
    },
    desmarcar: function(nome){
      var d = ler();
      delete d[normal(nome)];
      gravar(d);
    },
    exportar: function(){ return JSON.stringify(ler(), null, 1); },
    importar: function(texto){
      var novo = JSON.parse(texto);
      if (!novo || typeof novo !== "object") throw new Error("formato");
      var d = ler(), n = 0;
      Object.keys(novo).forEach(function(k){
        if (!d[k]) { d[k] = novo[k]; n++; }   /* junta, não substitui */
      });
      gravar(d);
      return n;
    }
  };
})();
</script>
"""


JS_ABA = """
<script>
/* ═══ Aba Empresas ═════════════════════════════════════════════════ */
(function(){
  "use strict";
  var caixa = document.getElementById("dados-empresas");
  if (!caixa) return;
  var base = JSON.parse(caixa.textContent);
  var TODAS = base.empresas || [];
  var ADZ = base.adzuna || "";
  var LOTE = 50, mostrando = LOTE;

  var q = document.getElementById("emp-q");
  var lista = document.getElementById("emp-lista");
  var cont = document.getElementById("emp-cont");
  var mais = document.getElementById("emp-mais");
  var ordem = document.getElementById("emp-ordem");
  var soVis = document.getElementById("emp-so-visitadas");
  var semVis = document.getElementById("emp-esconder-visitadas");
  document.getElementById("emp-total").textContent = TODAS.length.toLocaleString("pt-BR");

  function esc(t){
    return String(t == null ? "" : t).replace(/[&<>"']/g, function(c){
      return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c];
    });
  }
  function semAcento(t){
    return String(t || "").toLowerCase().normalize("NFD").replace(/[\\u0300-\\u036f]/g, "");
  }
  /* Índice de busca montado uma vez. Refazer isso a cada tecla, em
     3.000 registros, dava lag visível ao digitar. */
  TODAS.forEach(function(e){
    e._b = semAcento([e.n, (e.c || []).join(" "), (e.b || []).join(" "),
                      (e.s || []).join(" ")].join(" "));
  });

  /* Chips de setor, a partir do que existe no dado. */
  var setores = {};
  TODAS.forEach(function(e){ (e.s || []).forEach(function(x){ setores[x] = (setores[x] || 0) + 1; }); });
  var ligados = {};
  var caixaSetores = document.getElementById("emp-setores");
  Object.keys(setores).sort(function(a, b){ return setores[b] - setores[a]; })
    .forEach(function(nome){
      var b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.setAttribute("aria-pressed", "false");
      b.textContent = nome + " (" + setores[nome] + ")";
      b.addEventListener("click", function(){
        var on = b.getAttribute("aria-pressed") === "true";
        b.setAttribute("aria-pressed", String(!on));
        if (on) { delete ligados[nome]; } else { ligados[nome] = 1; }
        mostrando = LOTE; render();
      });
      caixaSetores.appendChild(b);
    });

  function filtradas(){
    var termo = semAcento(q.value.trim());
    var setoresLigados = Object.keys(ligados);
    var apenas = soVis.getAttribute("aria-pressed") === "true";
    var esconder = semVis.getAttribute("aria-pressed") === "true";
    var out = TODAS.filter(function(e){
      if (termo && e._b.indexOf(termo) === -1) return false;
      if (setoresLigados.length &&
          !setoresLigados.some(function(s){ return (e.s || []).indexOf(s) > -1; })) return false;
      var v = window.Visitas.tem(e.n);
      if (apenas && !v) return false;
      if (esconder && v) return false;
      return true;
    });
    var como = ordem.value;
    out.sort(function(a, b){
      if (como === "nome") return a.n.localeCompare(b.n, "pt-BR");
      if (como === "nota") return (b.p == null ? -1 : b.p) - (a.p == null ? -1 : a.p);
      if (como === "recente") return String(b.ate || "").localeCompare(String(a.ate || ""));
      return (b.v || 0) - (a.v || 0);
    });
    return out;
  }

  function data(d){
    if (!d) return "";
    var p = d.split("-");
    return p[2] + "/" + p[1];
  }

  function linha(e){
    var v = window.Visitas.get(e.n);
    var link = e.a ? (ADZ + e.a) : (e.u || "");
    var cargos = (e.c || []).map(esc);
    var extra = e.t && e.t > cargos.length ? " <b>+" + (e.t - cargos.length) + "</b>" : "";
    return '<li class="emp" data-visitada="' + (v ? "1" : "0") + '" data-nome="' + esc(e.n) + '">' +
      '<div class="emp-nome">' + esc(e.n) + (e.x ? ' <span class="emp-tag">anunciante sem nome</span>' : '') + '</div>' +
      '<div class="emp-nums"><span class="emp-vagas">' + (e.v || 0) + (e.v === 1 ? " vaga" : " vagas") + '</span>' +
        (e.p != null ? '<span class="emp-nota">melhor nota ' + e.p + '</span>' : '') + '</div>' +
      '<div class="emp-tags">' + (e.s || []).map(function(s){
          return '<span class="emp-tag">' + esc(s) + '</span>'; }).join("") + '</div>' +
      (cargos.length ? '<p class="emp-cargos">' + cargos.join(" &middot; ") + extra + '</p>' : '') +
      '<div class="emp-pe">' +
        ((e.b || []).length ? '<span>' + esc(e.b.join(", ")) + '</span>' : '') +
        (e.de ? '<span>' + data(e.de) + " &rarr; " + data(e.ate) + '</span>' : '') +
        (link ? '<a href="' + esc(link) + '" target="_blank" rel="noopener">último anúncio &#8599;</a>' : '') +
        '<button class="emp-marcar" type="button">' +
          (v ? "✓ fui em " + data(v.data) : "marcar que fui") + '</button>' +
      '</div></li>';
  }

  function render(){
    var todas = filtradas();
    lista.innerHTML = todas.slice(0, mostrando).map(linha).join("") ||
      '<li class="emp-vazio">Nenhuma empresa com esse filtro.</li>';
    var n = todas.length;
    cont.textContent = n.toLocaleString("pt-BR") + (n === 1 ? " empresa" : " empresas") +
      (n > mostrando ? " · mostrando " + mostrando : "") +
      " · " + window.Visitas.quantas() + " já visitadas";
    mais.hidden = n <= mostrando;
    mais.textContent = "mostrar mais " + Math.min(LOTE, n - mostrando);
  }

  lista.addEventListener("click", function(ev){
    var botao = ev.target.closest(".emp-marcar");
    if (!botao) return;
    var nome = botao.closest(".emp").dataset.nome;
    if (window.Visitas.tem(nome)) {
      window.Visitas.desmarcar(nome);
    } else {
      var nota = window.prompt("O que aconteceu? (pode deixar em branco)\\n\\n" + nome, "");
      if (nota === null) return;
      window.Visitas.marcar(nome, nota);
    }
    render();
  });

  var atraso;
  q.addEventListener("input", function(){
    clearTimeout(atraso);
    atraso = setTimeout(function(){ mostrando = LOTE; render(); }, 120);
  });
  document.getElementById("emp-limpar").addEventListener("click", function(){
    q.value = ""; mostrando = LOTE; render(); q.focus();
  });
  ordem.addEventListener("change", function(){ mostrando = LOTE; render(); });
  [soVis, semVis].forEach(function(b){
    b.addEventListener("click", function(){
      var on = b.getAttribute("aria-pressed") === "true";
      b.setAttribute("aria-pressed", String(!on));
      /* Os dois juntos não fazem sentido: um cancela o outro. */
      if (!on) {
        var outro = (b === soVis) ? semVis : soVis;
        outro.setAttribute("aria-pressed", "false");
      }
      mostrando = LOTE; render();
    });
  });
  mais.addEventListener("click", function(){ mostrando += LOTE; render(); });
  document.addEventListener("visitas:mudou", render);

  render();
})();
</script>
"""


def main() -> None:
    if not DADOS.exists():
        raise SystemExit(
            f"não achei {DADOS}\n"
            "Rode o ATUALIZAR-VAGAS.bat primeiro — é ele que gera o cadastro."
        )
    s = ARQ.read_text(encoding="utf-8")
    bruto = DADOS.read_text(encoding="utf-8")
    dados = json.loads(bruto)
    #  </ dentro do JSON fecharia o <script> no meio. Não acontece com
    #  estes dados, mas escapar custa nada e evita uma surpresa.
    embutido = ('<script type="application/json" id="dados-empresas">'
                + bruto.replace("</", "<\\/") + '</script>')

    # ── caso comum: a aba já existe, é só trocar o dado ─────────────
    # Isto roda no fim de toda coleta. Se aqui desse erro em vez de
    # atualizar, a aba congelaria na foto do dia em que foi criada.
    if "pane-emp" in s:
        alvo = '<script type="application/json" id="dados-empresas">'
        i = s.find(alvo)
        if i < 0:
            raise SystemExit("a aba existe mas não achei o bloco de dados")
        fim = s.find("</script>", i) + len("</script>")
        shutil.copy(ARQ, ARQ.with_suffix(".html.bak-dados"))
        _escrever(ARQ, s[:i] + embutido + s[fim:])
        print(f"aba Empresas atualizada · {dados['total']} empresas · "
              f"gerado em {dados.get('gerado_em', '?')}")
        return

    # ── primeira vez: monta a aba inteira ───────────────────────────
    shutil.copy(ARQ, ARQ.with_suffix(".html.bak8"))

    # 1. CSS
    s = troca(s, "</style>", CSS + "</style>", "CSS da aba Empresas")

    # 2. botão da aba, logo depois da Rota
    s = troca(s,
              '<button role="tab" id="tab-top"',
              HTML_ABA + '<button role="tab" id="tab-top"',
              "botão da aba")

    # 3. painel, antes do painel do Top 10
    s = troca(s,
              '<section role="tabpanel" tabindex="0" aria-labelledby="tab-top"',
              HTML_PAINEL + '\n<section role="tabpanel" tabindex="0" aria-labelledby="tab-top"',
              "painel da aba")

    # 4. a lista de painéis no JS que troca de aba
    s = troca(s,
              '["dir","rota","top","crono","sal","visto","docs","fora"]',
              '["dir","rota","emp","top","crono","sal","visto","docs","fora"]',
              "lista de painéis")

    # 5. dado + scripts, no fim do body
    s = troca(s, "</body>", embutido + "\n" + JS_VISITAS + JS_ABA + "</body>",
              "dados e scripts")

    _escrever(ARQ, s)
    kb = ARQ.stat().st_size / 1024
    print(f"aba Empresas instalada · {dados['total']} empresas · "
          f"material agora com {kb:.0f} KB")
    print(f"backup do anterior: {ARQ.name}.bak8")


if __name__ == "__main__":
    main()
