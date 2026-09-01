"""A aba "Rota a pé": mini-mapa do centro + roteiro de CV impresso.

Depende do mapa-e-rota.py ter rodado antes (ele grava x, y, jan e jpq
em cada registro).
"""
import pathlib
import re
import shutil

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")
shutil.copy(ARQ, ARQ.with_suffix(".html.bak4"))


def troca(velho, novo, rotulo):
    global s
    if velho not in s:
        raise SystemExit(f"ÂNCORA NÃO ENCONTRADA: {rotulo}")
    s = s.replace(velho, novo, 1)


# ── 1. a aba, entre "Diretório" e "Top 10" ──────────────────────────
troca('<button role="tab" id="tab-top"',
      '<button role="tab" id="tab-rota" aria-controls="pane-rota" aria-selected="false" '
      'tabindex="-1" data-pane="rota">Rota a pé</button>\n  '
      '<button role="tab" id="tab-top"',
      "aba Rota a pé")

# ── 2. o painel ─────────────────────────────────────────────────────
PAINEL = """
<section role="tabpanel" tabindex="0" aria-labelledby="tab-rota" id="pane-rota" hidden>
  <div class="rota-intro">
    <h2 class="rota-h">Bater na porta com o currículo na mão</h2>
    <p>Em Adelaide, café e restaurante independentes contratam assim — e o
    material tem 116 cafés e 114 restaurantes. Escolha os lugares, e a rota
    sai ordenada a partir do ILSC.</p>
    <div class="rota-avisos">
      <p><b>O mapa é um esquema, não um GPS.</b> A rua de cada ponto é exata;
      a posição ao longo dela é aproximada, tirada do número. Serve para
      ordenar a caminhada e entender a cidade. O que salva o esquema é que o
      centro de Adelaide é uma grade de 1&nbsp;km por 1&nbsp;km entre as
      quatro Terraces, com King William no meio — então as distâncias saem
      perto das reais.</p>
      <p><b>O horário é norma do setor, não o horário daquela loja.</b> Eu não
      tenho o horário de funcionamento de 232 empregadores e não vou inventar.
      O que existe e é sólido é a norma do ramo sobre quando o gerente está
      presente e sem rush. Confirme a loja específica no Google Maps antes de
      sair.</p>
    </div>
  </div>

  <div class="rota-cols">
    <div class="rota-mapa-box">
      <div class="rota-jan" role="group" aria-label="Janela de visita">
        <button class="chip" type="button" data-jan="tarde" aria-pressed="true">Tarde &middot; 14h–16h</button>
        <button class="chip" type="button" data-jan="manha" aria-pressed="false">Manhã &middot; 9h–11h30</button>
      </div>
      <div id="rota-svg-wrap"></div>
      <p class="rota-legenda" id="rota-legenda"></p>
    </div>

    <div class="rota-painel">
      <div class="rota-acoes">
        <button class="btn-primario" type="button" id="rota-auto">Montar a melhor rota</button>
        <button class="linkbtn" type="button" id="rota-limpar">limpar seleção</button>
      </div>
      <label class="rota-campo">
        <span>Quantas paradas</span>
        <input type="range" id="rota-n" min="3" max="14" value="8">
        <output id="rota-n-out">8</output>
      </label>
      <div class="rota-setores" id="rota-setores" role="group" aria-label="Setores"></div>
      <p class="rota-resumo" role="status" aria-live="polite" id="rota-resumo"></p>
      <ol class="rota-lista" id="rota-lista"></ol>
      <div id="rota-fora" class="rota-fora"></div>
    </div>
  </div>
</section>
"""
troca('<section role="tabpanel" tabindex="0" aria-labelledby="tab-top" id="pane-top"',
      PAINEL + '\n<section role="tabpanel" tabindex="0" aria-labelledby="tab-top" id="pane-top"',
      "painel da rota")

# ── 3. registra o painel no seletor de abas ─────────────────────────
troca('["dir","top","crono","sal","visto","docs","fora"]',
      '["dir","rota","top","crono","sal","visto","docs","fora"]',
      "lista de painéis")

# ── 4. CSS ──────────────────────────────────────────────────────────
CSS = """
/* ═══ Aba Rota a pé ═══════════════════════════════════════════════ */
.rota-h{font-size:var(--fs-h2);line-height:var(--lh-h2);margin:0 0 var(--sp2)}
.rota-intro{margin-bottom:var(--sp5)}
.rota-intro>p{max-width:66ch;color:var(--ink-2)}
.rota-avisos{display:grid;gap:var(--sp3);margin-top:var(--sp4)}
.rota-avisos p{margin:0;max-width:70ch;font-size:var(--fs-body-sm);
  line-height:var(--lh-body-sm);color:var(--ink-2);
  border-left:3px solid var(--s4);padding-left:var(--sp4)}
.rota-cols{display:grid;gap:var(--sp5);align-items:start}
@media (min-width:900px){.rota-cols{grid-template-columns:minmax(0,1fr) minmax(0,1fr)}}
.rota-mapa-box{position:sticky;top:var(--sp4)}
@media (max-width:899px){.rota-mapa-box{position:static}}
.rota-jan{display:flex;gap:var(--sp2);margin-bottom:var(--sp3);flex-wrap:wrap}
#rota-svg-wrap{background:var(--surface);border:1px solid var(--line);
  border-radius:var(--r-md);padding:var(--sp3)}
#rota-svg-wrap svg{width:100%;height:auto;display:block}
.rota-legenda{font-size:var(--fs-caption);color:var(--ink-3);margin:var(--sp3) 0 0;
  line-height:1.5}
.rota-acoes{display:flex;gap:var(--sp3);align-items:center;flex-wrap:wrap;
  margin-bottom:var(--sp4)}
.btn-primario{background:var(--brand);color:var(--brand-ink);border:0;
  border-radius:var(--r-sm);min-height:44px;padding:0 var(--sp5);
  font:700 var(--fs-body-sm)/1 inherit;cursor:pointer}
.btn-primario:hover{filter:brightness(1.1)}
.rota-campo{display:flex;align-items:center;gap:var(--sp3);
  font-size:var(--fs-body-sm);color:var(--ink-2);margin-bottom:var(--sp4)}
.rota-campo input[type=range]{flex:1;min-width:120px;accent-color:var(--brand)}
.rota-campo output{font-weight:700;color:var(--ink);min-width:2ch;
  font-variant-numeric:tabular-nums}
.rota-setores{display:flex;flex-wrap:wrap;gap:var(--sp2);margin-bottom:var(--sp4)}
.rota-resumo{background:var(--r-ganho-bg);border-left:3px solid var(--r-ganho-br);
  color:var(--r-ganho-fg);padding:var(--sp3) var(--sp4);border-radius:0 var(--r-sm) var(--r-sm) 0;
  font-size:var(--fs-body-sm);margin:0 0 var(--sp4)}
.rota-resumo:empty{display:none}
.rota-lista{list-style:none;counter-reset:parada;margin:0;padding:0;
  display:flex;flex-direction:column;gap:var(--sp3)}
.rota-lista li{counter-increment:parada;background:var(--surface);
  border:1px solid var(--line);border-radius:var(--r-md);
  padding:var(--sp4) var(--sp4) var(--sp4) var(--sp10);position:relative}
.rota-lista li::before{content:counter(parada);position:absolute;
  left:var(--sp3);top:var(--sp4);width:26px;height:26px;border-radius:50%;
  background:var(--brand);color:var(--brand-ink);text-align:center;
  font:700 13px/26px ui-monospace,monospace}
.rota-lista .nome{font-weight:700;display:block}
.rota-lista .end{font-size:var(--fs-caption);color:var(--ink-2);display:block;
  margin-top:2px}
.rota-lista .quando{font-size:var(--fs-caption);color:var(--ink-2);display:block;
  margin-top:var(--sp2);border-top:1px solid var(--line-2);padding-top:var(--sp2)}
.rota-lista .andar{font-size:var(--fs-caption);color:var(--ink-3);
  font-variant-numeric:tabular-nums}
.rota-fora{margin-top:var(--sp5);font-size:var(--fs-body-sm);color:var(--ink-2)}
.rota-fora h3{font-size:var(--fs-h3);margin:0 0 var(--sp2)}
.rota-fora ul{margin:0;padding-left:1.2em}
.rota-vazio{color:var(--ink-3);padding:var(--sp5);text-align:center;
  border:1px dashed var(--line-ctl);border-radius:var(--r-md)}
.pt{cursor:pointer}
.pt:hover circle{stroke:var(--ink);stroke-width:2}
"""
troca("</style>", CSS + "</style>", "CSS da rota")

# ── 5. JS ───────────────────────────────────────────────────────────
JS = r"""
<script>
/* ═══ Rota a pé: mini-mapa do centro + roteiro de CV impresso ═════ */
(function(){
  "use strict";
  if (typeof DATA === "undefined") return;

  var ILSC = {x: 776, y: 300, nome: "ILSC — 115 Grenfell St"};
  var PONTOS = DATA.filter(function(d){ return typeof d.x === "number"; });
  var JANELA = {tarde: "14h–16h", manha: "9h–11h30"};

  var estado = {jan: "tarde", setores: new Set(), sel: new Set(), n: 8};

  /* ── a grade, desenhada uma vez ─────────────────────────────── */
  var CORREDORES = [
    [0,"North Tce"],[155,"Rundle / Hindley"],[300,"Grenfell / Currie"],
    [420,"Pirie / Waymouth"],[540,"Flinders / Franklin"],[660,"Wakefield / Grote"],
    [770,"Angas / Gouger"],[850,"Carrington / Sturt"],[955,"Gilles / Wright"],
    [1000,"South Tce"]
  ];
  var TRANSV = [[0,"West"],[250,"Morphett"],[500,"King William"],[700,"Pulteney"],[840,"Hutt"],[1000,"East"]];

  function esc(t){ return String(t==null?"":t).replace(/[&<>"]/g, function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]; }); }

  function svgMapa(rota){
    var M = 62, W = 1000 + M*2;
    var p = ['<svg viewBox="0 0 '+W+' '+(W+10)+'" role="img" aria-label="Esquema do centro de Adelaide com as paradas da rota">'];
    p.push('<rect x="'+M+'" y="'+M+'" width="1000" height="1000" fill="none" stroke="var(--line-ctl)" stroke-width="2"/>');
    CORREDORES.forEach(function(c){
      if(c[0]===0||c[0]===1000) return;
      p.push('<line x1="'+M+'" y1="'+(M+c[0])+'" x2="'+(M+1000)+'" y2="'+(M+c[0])+'" stroke="var(--line)" stroke-width="1"/>');
      p.push('<text x="'+(M-6)+'" y="'+(M+c[0]+4)+'" text-anchor="end" font-size="19" fill="var(--ink-3)">'+esc(c[1])+'</text>');
    });
    TRANSV.forEach(function(t){
      if(t[0]===0||t[0]===1000) return;
      p.push('<line x1="'+(M+t[0])+'" y1="'+M+'" x2="'+(M+t[0])+'" y2="'+(M+1000)+'" stroke="var(--line)" stroke-width="1"/>');
      p.push('<text x="'+(M+t[0])+'" y="'+(M-10)+'" text-anchor="middle" font-size="19" fill="var(--ink-3)">'+esc(t[1])+'</text>');
    });
    /* Victoria Square, o único marco que quebra a grade */
    p.push('<rect x="'+(M+455)+'" y="'+(M+600)+'" width="90" height="120" fill="var(--surface-2)" stroke="var(--line)"/>');
    p.push('<text x="'+(M+500)+'" y="'+(M+665)+'" text-anchor="middle" font-size="17" fill="var(--ink-3)">Victoria Sq</text>');

    /* pontos não selecionados */
    var visiveis = filtrados();
    visiveis.forEach(function(d){
      if (estado.sel.has(d.id)) return;
      p.push('<g class="pt" data-id="'+d.id+'"><circle cx="'+(M+d.x)+'" cy="'+(M+d.y)+'" r="9" '+
             'fill="var(--s'+SLOTS[d.setor]+')" opacity=".5"/><title>'+esc(d.empregador)+' — '+esc(d.endereco)+'</title></g>');
    });
    /* a rota */
    if (rota.length){
      var pts = [ILSC].concat(rota);
      var linha = pts.map(function(q){ return (M+q.x)+","+(M+q.y); }).join(" ");
      p.push('<polyline points="'+linha+'" fill="none" stroke="var(--brand)" stroke-width="4" '+
             'stroke-linejoin="round" stroke-dasharray="14 8" opacity=".85"/>');
      rota.forEach(function(d,i){
        p.push('<g class="pt" data-id="'+d.id+'"><circle cx="'+(M+d.x)+'" cy="'+(M+d.y)+'" r="17" fill="var(--brand)"/>'+
               '<text x="'+(M+d.x)+'" y="'+(M+d.y+6)+'" text-anchor="middle" font-size="19" font-weight="700" '+
               'fill="var(--brand-ink)">'+(i+1)+'</text><title>'+esc(d.empregador)+'</title></g>');
      });
    }
    /* a escola, sempre por cima */
    p.push('<g><circle cx="'+(M+ILSC.x)+'" cy="'+(M+ILSC.y)+'" r="13" fill="none" stroke="var(--s2)" stroke-width="4"/>'+
           '<text x="'+(M+ILSC.x)+'" y="'+(M+ILSC.y-22)+'" text-anchor="middle" font-size="20" font-weight="700" '+
           'fill="var(--s2)">ILSC</text><title>'+esc(ILSC.nome)+'</title></g>');
    p.push('<text x="'+(M+500)+'" y="'+(M+1030)+'" text-anchor="middle" font-size="18" fill="var(--ink-3)">'+
           'esquema · 1 km entre as Terraces</text>');
    p.push('</svg>');
    return p.join("");
  }

  function filtrados(){
    return PONTOS.filter(function(d){
      if (d.jan !== estado.jan) return false;
      if (estado.setores.size && !estado.setores.has(d.setor)) return false;
      return true;
    });
  }

  function dist(a,b){ return Math.hypot(a.x-b.x, a.y-b.y); }

  /* Vizinho mais próximo a partir do ILSC, depois 2-opt. O 2-opt custa
     nada nesse tamanho e tira os cruzamentos que o guloso deixa. */
  function rotear(pontos){
    if (!pontos.length) return [];
    var restam = pontos.slice(), atual = ILSC, ordem = [];
    while (restam.length){
      var m = 0;
      for (var i=1;i<restam.length;i++) if (dist(atual,restam[i]) < dist(atual,restam[m])) m = i;
      atual = restam.splice(m,1)[0];
      ordem.push(atual);
    }
    var melhorou = true, voltas = 0;
    while (melhorou && voltas++ < 40){
      melhorou = false;
      for (var a=0;a<ordem.length-1;a++){
        for (var b=a+1;b<ordem.length;b++){
          var antes = (a===0?ILSC:ordem[a-1]);
          var d1 = dist(antes,ordem[a]) + dist(ordem[b], ordem[b+1]||ordem[b]);
          var d2 = dist(antes,ordem[b]) + dist(ordem[a], ordem[b+1]||ordem[a]);
          if (d2 + 0.01 < d1){
            var t = ordem.slice(a,b+1).reverse();
            ordem = ordem.slice(0,a).concat(t, ordem.slice(b+1));
            melhorou = true;
          }
        }
      }
    }
    return ordem;
  }

  function comprimento(rota){
    var total = 0, ant = ILSC;
    rota.forEach(function(d){ total += dist(ant,d); ant = d; });
    return total + dist(ant, ILSC);   /* e voltar */
  }

  function render(){
    var sel = filtrados().filter(function(d){ return estado.sel.has(d.id); });
    var rota = rotear(sel);
    document.getElementById("rota-svg-wrap").innerHTML = svgMapa(rota);
    document.getElementById("rota-svg-wrap").querySelectorAll(".pt").forEach(function(g){
      g.addEventListener("click", function(){
        var id = +g.dataset.id;
        if (estado.sel.has(id)) estado.sel.delete(id); else estado.sel.add(id);
        render();
      });
    });

    var lista = document.getElementById("rota-lista");
    var resumo = document.getElementById("rota-resumo");
    if (!rota.length){
      lista.innerHTML = '<li class="rota-vazio" style="padding-left:var(--sp5)">'+
        'Clique nos pontos do mapa, ou use <b>Montar a melhor rota</b>.</li>';
      resumo.textContent = "";
    } else {
      var metros = Math.round(comprimento(rota));
      var minAndando = Math.round(metros/80);
      var minParadas = rota.length * 5;
      resumo.textContent = rota.length + " paradas · cerca de " + (metros/1000).toFixed(1) +
        " km a pé · " + minAndando + " min andando + " + minParadas +
        " min de conversa = " + (minAndando + minParadas) + " min no total. Janela: " +
        JANELA[estado.jan] + ", saindo e voltando ao ILSC.";
      var ant = ILSC;
      lista.innerHTML = rota.map(function(d){
        var passo = Math.round(dist(ant,d)); ant = d;
        return '<li><span class="nome">'+esc(d.empregador)+
          (d.unidade?' <span style="font-weight:400;color:var(--ink-2)">— '+esc(d.unidade)+'</span>':'')+'</span>'+
          '<span class="end">'+esc(d.endereco)+'</span>'+
          '<span class="andar">'+passo+' m da parada anterior · '+Math.max(1,Math.round(passo/80))+' min</span>'+
          '<span class="quando"><b>'+JANELA[d.jan]+'.</b> '+esc(d.jpq)+'</span>'+
          (d.dica?'<span class="quando">'+esc(d.dica.split(".")[0])+'.</span>':'')+
          '</li>';
      }).join("");
    }

    /* fora do centro: não entram na caminhada, mas existem */
    var fora = DATA.filter(function(d){
      return typeof d.x !== "number" && d.jan === estado.jan &&
             (!estado.setores.size || estado.setores.has(d.setor));
    });
    document.getElementById("rota-fora").innerHTML = fora.length
      ? '<h3>Fora do centro — '+fora.length+' lugares</h3><p>Não entram na caminhada: '+
        'precisam de ônibus ou trem. Os mais próximos:</p><ul>'+
        fora.slice(0,8).map(function(d){
          return '<li><b>'+esc(d.empregador)+'</b> — '+esc(d.regiao||d.endereco)+'</li>'; }).join("")+
        '</ul>'
      : "";

    document.getElementById("rota-legenda").innerHTML =
      '<b>'+filtrados().length+'</b> lugares no centro nesta janela. '+
      'Círculo laranja é o ILSC. Clique num ponto para pôr ou tirar da rota. '+
      'A linha tracejada é a ordem da caminhada, calculada pelo vizinho mais '+
      'próximo com 2-opt — sai sem cruzamentos.';
  }

  /* ── controles ───────────────────────────────────────────────── */
  var caixaSetores = document.getElementById("rota-setores");
  Object.keys(SLOTS).forEach(function(nome){
    var b = document.createElement("button");
    b.className = "chip"; b.type = "button"; b.setAttribute("aria-pressed","false");
    b.innerHTML = '<span class="dot" style="background:var(--s'+SLOTS[nome]+')"></span>'+esc(nome);
    b.addEventListener("click", function(){
      var on = b.getAttribute("aria-pressed") === "true";
      b.setAttribute("aria-pressed", String(!on));
      if (on) estado.setores.delete(nome); else estado.setores.add(nome);
      render();
    });
    caixaSetores.appendChild(b);
  });

  document.querySelectorAll(".rota-jan .chip").forEach(function(b){
    b.addEventListener("click", function(){
      document.querySelectorAll(".rota-jan .chip").forEach(function(o){
        o.setAttribute("aria-pressed", String(o===b)); });
      estado.jan = b.dataset.jan;
      estado.sel.clear();
      render();
    });
  });

  var faixa = document.getElementById("rota-n");
  faixa.addEventListener("input", function(){
    estado.n = +faixa.value;
    document.getElementById("rota-n-out").textContent = faixa.value;
  });

  /* A "melhor rota": pega os de maior chance na janela, e entre os de
     chance igual prefere os mais perto da escola — andar menos por
     oportunidade igual. */
  document.getElementById("rota-auto").addEventListener("click", function(){
    var cand = filtrados().slice().sort(function(a,b){
      var pa = PRIO[a.chance]||3, pb = PRIO[b.chance]||3;
      if (pa !== pb) return pa - pb;
      return dist(ILSC,a) - dist(ILSC,b);
    });
    estado.sel = new Set(cand.slice(0, estado.n).map(function(d){ return d.id; }));
    render();
  });
  document.getElementById("rota-limpar").addEventListener("click", function(){
    estado.sel.clear(); render();
  });

  render();
})();
</script>
"""
troca("</body>", JS + "</body>", "JS da rota")

ARQ.write_text(s, encoding="utf-8")
print("aba Rota a pé injetada")
