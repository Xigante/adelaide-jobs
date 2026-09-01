"""Substitui o esquema desenhado por um mapa real (Leaflet + OpenStreetMap)
e acrescenta o botão que abre a rota inteira no Google Maps.
"""
import pathlib
import re

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")

# ── Leaflet, do cdnjs ────────────────────────────────────────────────
LEAFLET = ('<link rel="stylesheet" '
           'href="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css">\n'
           '<script src="https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js">'
           '</script>\n</head>')
assert "</head>" in s
s = s.replace("</head>", LEAFLET, 1)

# ── o contêiner do mapa no lugar do <div id="rota-svg-wrap"> ─────────
s = s.replace('<div id="rota-svg-wrap"></div>',
              '<div id="rota-mapa"></div>\n      '
              '<p class="rota-semnet" id="rota-semnet" hidden>O mapa precisa de internet '
              'para carregar as ruas. A lista de paradas abaixo funciona offline.</p>', 1)

# ── botão do Google Maps ao lado dos outros ──────────────────────────
s = s.replace('<button class="linkbtn" type="button" id="rota-limpar">limpar seleção</button>',
              '<a class="btn-maps" id="rota-gmaps" target="_blank" rel="noopener" href="#">'
              'Abrir no Google&nbsp;Maps</a>\n        '
              '<button class="linkbtn" type="button" id="rota-limpar">limpar seleção</button>', 1)

CSS = """
#rota-mapa{height:520px;border-radius:var(--r-md);border:1px solid var(--line);
  background:var(--surface-2)}
@media (max-width:899px){#rota-mapa{height:380px}}
.leaflet-container{font:inherit;background:var(--surface-2)}
.leaflet-popup-content{margin:12px 14px;font-size:var(--fs-body-sm);line-height:1.5}
.leaflet-popup-content b{display:block;margin-bottom:2px}
.leaflet-popup-content .pend{color:var(--ink-2);font-size:var(--fs-caption)}
.leaflet-popup-content .pq{display:block;margin-top:6px;padding-top:6px;
  border-top:1px solid var(--line-2);color:var(--ink-2);font-size:var(--fs-caption)}
.leaflet-popup-content a{font-weight:700}
.num-parada{background:var(--brand);color:var(--brand-ink);border-radius:50%;
  width:26px;height:26px;text-align:center;line-height:26px;font-weight:700;
  font-size:13px;box-shadow:0 0 0 3px var(--surface)}
.marc-ilsc{background:var(--s2);color:#fff;border-radius:50%;width:30px;height:30px;
  text-align:center;line-height:30px;font-weight:700;font-size:11px;
  box-shadow:0 0 0 3px var(--surface)}
.btn-maps{display:inline-flex;align-items:center;min-height:44px;padding:0 var(--sp5);
  background:var(--surface);border:1px solid var(--line-ctl);border-radius:var(--r-sm);
  color:var(--brand);font:700 var(--fs-body-sm)/1 inherit;text-decoration:none}
.btn-maps:hover{border-color:var(--brand)}
.btn-maps[aria-disabled="true"]{opacity:.45;pointer-events:none}
.rota-semnet{font-size:var(--fs-caption);color:var(--no,var(--ink-3));margin:var(--sp2) 0 0}
"""
s = s.replace("</style>", CSS + "</style>", 1)

# ── troca o módulo JS inteiro ────────────────────────────────────────
i = s.rindex("<script>\n/* ═══ Rota a pé")
j = s.index("</script>", i) + len("</script>")

NOVO = r"""<script>
/* ═══ Rota a pé — mapa real (Leaflet + OpenStreetMap) ═════════════
   O pino é APROXIMADO: veja o cabeçalho da aba. O que é exato é o
   endereço e o link do Google Maps, que manda o texto do endereço e
   deixa o Google geocodificar no aparelho. ═══════════════════════ */
(function(){
  "use strict";
  if (typeof DATA === "undefined") return;

  var ILSC = {lat:-34.9245006, lon:138.6039721, nome:"ILSC", end:"115 Grenfell Street, Adelaide SA 5000"};
  var PONTOS = DATA.filter(function(d){ return typeof d.lat === "number"; });
  var JANELA = {tarde:"14h–16h", manha:"9h–11h30"};
  var estado = {jan:"tarde", setores:new Set(), sel:new Set(), n:8};
  var mapa = null, camada = null, iniciado = false;

  function esc(t){ return String(t==null?"":t).replace(/[&<>"]/g, function(c){
    return {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;"}[c]; }); }
  function gmaps(end){ return "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(end); }

  /* Distância real entre dois pontos, em metros (haversine). */
  function dist(a,b){
    var R=6371000, p=Math.PI/180;
    var dLat=(b.lat-a.lat)*p, dLon=(b.lon-a.lon)*p;
    var h=Math.sin(dLat/2)*Math.sin(dLat/2) +
          Math.cos(a.lat*p)*Math.cos(b.lat*p)*Math.sin(dLon/2)*Math.sin(dLon/2);
    return 2*R*Math.asin(Math.sqrt(h));
  }

  function filtrados(){
    return PONTOS.filter(function(d){
      if (d.jan !== estado.jan) return false;
      if (estado.setores.size && !estado.setores.has(d.setor)) return false;
      return true;
    });
  }

  function rotear(pontos){
    if (!pontos.length) return [];
    var restam=pontos.slice(), atual=ILSC, ordem=[];
    while (restam.length){
      var m=0;
      for (var i=1;i<restam.length;i++) if (dist(atual,restam[i])<dist(atual,restam[m])) m=i;
      atual=restam.splice(m,1)[0]; ordem.push(atual);
    }
    var melhorou=true, voltas=0;
    while (melhorou && voltas++ < 40){
      melhorou=false;
      for (var a=0;a<ordem.length-1;a++){
        for (var b=a+1;b<ordem.length;b++){
          var antes=(a===0?ILSC:ordem[a-1]);
          var d1=dist(antes,ordem[a])+dist(ordem[b],ordem[b+1]||ordem[b]);
          var d2=dist(antes,ordem[b])+dist(ordem[a],ordem[b+1]||ordem[a]);
          if (d2+0.01 < d1){
            ordem = ordem.slice(0,a).concat(ordem.slice(a,b+1).reverse(), ordem.slice(b+1));
            melhorou=true;
          }
        }
      }
    }
    return ordem;
  }

  function comprimento(rota){
    var t=0, ant=ILSC;
    rota.forEach(function(d){ t+=dist(ant,d); ant=d; });
    return t + dist(ant, ILSC);
  }

  function iniciarMapa(){
    if (iniciado || typeof L === "undefined") return;
    iniciado = true;
    mapa = L.map("rota-mapa", {scrollWheelZoom:false}).setView([ILSC.lat, ILSC.lon], 15);
    L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: "&copy; OpenStreetMap"
    }).addTo(mapa);
    camada = L.layerGroup().addTo(mapa);
  }

  function desenhar(rota){
    if (!mapa) return;
    camada.clearLayers();

    filtrados().forEach(function(d){
      if (estado.sel.has(d.id)) return;
      L.circleMarker([d.lat,d.lon], {radius:6, weight:1.5, color:"#fff",
        fillColor:getComputedStyle(document.documentElement).getPropertyValue("--s"+SLOTS[d.setor]).trim(),
        fillOpacity:.85})
        .bindPopup(popup(d)).addTo(camada)
        .on("click", function(){ /* o popup abre; a seleção é pelo botão dentro dele */ });
    });

    if (rota.length){
      L.polyline([[ILSC.lat,ILSC.lon]].concat(rota.map(function(d){return [d.lat,d.lon];})),
        {color:"#1a3763", weight:4, opacity:.8, dashArray:"10 7"}).addTo(camada);
      rota.forEach(function(d,i){
        L.marker([d.lat,d.lon], {icon: L.divIcon({className:"", iconSize:[26,26],
          html:'<div class="num-parada">'+(i+1)+'</div>'})})
          .bindPopup(popup(d, i+1)).addTo(camada);
      });
    }

    L.marker([ILSC.lat,ILSC.lon], {icon: L.divIcon({className:"", iconSize:[30,30],
      html:'<div class="marc-ilsc">ILSC</div>'})})
      .bindPopup("<b>ILSC Adelaide</b><span class=\"pend\">115 Grenfell Street</span>")
      .addTo(camada);

    var alvos = rota.length ? rota.concat([ILSC]) : filtrados().concat([ILSC]);
    if (alvos.length > 1){
      mapa.fitBounds(alvos.map(function(d){ return [d.lat,d.lon]; }), {padding:[36,36], maxZoom:17});
    }
  }

  function popup(d, n){
    return '<b>'+(n?n+'. ':'')+esc(d.empregador)+'</b>'+
      '<span class="pend">'+esc(d.endereco)+'</span>'+
      '<span class="pq"><b style="display:inline">'+JANELA[d.jan]+'.</b> '+esc(d.jpq)+'</span>'+
      '<span class="pq"><a href="'+gmaps(d.endereco)+'" target="_blank" rel="noopener">abrir no Google Maps</a>'+
      ' &middot; <button type="button" class="linkbtn" data-sel="'+d.id+'">'+
      (estado.sel.has(d.id)?'tirar da rota':'pôr na rota')+'</button></span>';
  }

  /* O Google Maps aceita origem, destino e até 9 pontos no meio. */
  function linkGoogle(rota){
    if (!rota.length) return null;
    var paradas = rota.slice(0, 10);
    var meio = paradas.slice(0, -1).map(function(d){ return d.endereco; });
    var url = "https://www.google.com/maps/dir/?api=1&travelmode=walking" +
      "&origin=" + encodeURIComponent(ILSC.end) +
      "&destination=" + encodeURIComponent(paradas[paradas.length-1].endereco);
    if (meio.length) url += "&waypoints=" + meio.map(encodeURIComponent).join("|");
    return url;
  }

  function render(){
    var sel = filtrados().filter(function(d){ return estado.sel.has(d.id); });
    var rota = rotear(sel);
    iniciarMapa();
    if (mapa){ desenhar(rota); setTimeout(function(){ mapa.invalidateSize(); }, 60); }
    else { var av=document.getElementById("rota-semnet"); if(av) av.hidden=false; }

    var botao = document.getElementById("rota-gmaps");
    var url = linkGoogle(rota);
    botao.href = url || "#";
    botao.setAttribute("aria-disabled", String(!url));
    botao.textContent = rota.length > 10
      ? "Abrir as 10 primeiras no Google Maps"
      : "Abrir no Google Maps";

    var lista = document.getElementById("rota-lista");
    var resumo = document.getElementById("rota-resumo");
    if (!rota.length){
      lista.innerHTML = '<li class="rota-vazio" style="padding-left:var(--sp5)">'+
        'Clique num ponto do mapa, ou use <b>Montar a melhor rota</b>.</li>';
      resumo.textContent = "";
    } else {
      var metros = Math.round(comprimento(rota));
      var andando = Math.round(metros/80), conversa = rota.length*5;
      resumo.textContent = rota.length+" paradas · "+(metros/1000).toFixed(1)+
        " km a pé · "+andando+" min andando + "+conversa+" min de conversa = "+
        (andando+conversa)+" min no total. Janela: "+JANELA[estado.jan]+
        ", saindo e voltando ao ILSC.";
      var ant = ILSC;
      lista.innerHTML = rota.map(function(d){
        var passo = Math.round(dist(ant,d)); ant = d;
        var trecho = passo < 40 ? "praticamente ao lado da parada anterior"
          : passo+" m da anterior · "+Math.max(1,Math.round(passo/80))+" min";
        return '<li><span class="nome">'+esc(d.empregador)+
          (d.unidade?' <span style="font-weight:400;color:var(--ink-2)">— '+esc(d.unidade)+'</span>':'')+
          '</span><span class="end">'+esc(d.endereco)+' · '+
          '<a href="'+gmaps(d.endereco)+'" target="_blank" rel="noopener">no Maps</a></span>'+
          '<span class="andar">'+trecho+'</span>'+
          '<span class="quando"><b>'+JANELA[d.jan]+'.</b> '+esc(d.jpq)+'</span></li>';
      }).join("");
    }

    var fora = DATA.filter(function(d){
      return typeof d.lat !== "number" && d.jan === estado.jan &&
             (!estado.setores.size || estado.setores.has(d.setor));
    });
    document.getElementById("rota-fora").innerHTML = fora.length
      ? '<h3>Fora do centro — '+fora.length+' lugares</h3><p>Precisam de ônibus ou trem, '+
        'então ficam fora da caminhada:</p><ul>'+fora.slice(0,8).map(function(d){
          return '<li><b>'+esc(d.empregador)+'</b> — '+esc(d.regiao||d.endereco)+'</li>';
        }).join("")+'</ul>' : "";

    document.getElementById("rota-legenda").innerHTML =
      '<b>'+filtrados().length+'</b> lugares no centro nesta janela. O círculo laranja é o '+
      'ILSC. Clique num ponto para ver o endereço e pôr na rota. <b>O pino é aproximado</b> '+
      '— pode cair na quadra vizinha. O endereço escrito e o botão do Google Maps são exatos.';
  }

  /* o botão "pôr na rota" mora dentro do popup, que nasce depois */
  document.addEventListener("click", function(e){
    var b = e.target.closest && e.target.closest("[data-sel]");
    if (!b) return;
    var id = +b.dataset.sel;
    if (estado.sel.has(id)) estado.sel.delete(id); else estado.sel.add(id);
    if (mapa) mapa.closePopup();
    render();
  });

  var caixa = document.getElementById("rota-setores");
  Object.keys(SLOTS).forEach(function(nome){
    var b=document.createElement("button");
    b.className="chip"; b.type="button"; b.setAttribute("aria-pressed","false");
    b.innerHTML='<span class="dot" style="background:var(--s'+SLOTS[nome]+')"></span>'+esc(nome);
    b.addEventListener("click", function(){
      var on=b.getAttribute("aria-pressed")==="true";
      b.setAttribute("aria-pressed", String(!on));
      if (on) estado.setores.delete(nome); else estado.setores.add(nome);
      render();
    });
    caixa.appendChild(b);
  });

  document.querySelectorAll(".rota-jan .chip").forEach(function(b){
    b.addEventListener("click", function(){
      document.querySelectorAll(".rota-jan .chip").forEach(function(o){
        o.setAttribute("aria-pressed", String(o===b)); });
      estado.jan=b.dataset.jan; estado.sel.clear(); render();
    });
  });

  var faixa=document.getElementById("rota-n");
  faixa.addEventListener("input", function(){
    estado.n=+faixa.value;
    document.getElementById("rota-n-out").textContent=faixa.value;
  });

  document.getElementById("rota-auto").addEventListener("click", function(){
    var cand=filtrados().slice().sort(function(a,b){
      var pa=PRIO[a.chance]||3, pb=PRIO[b.chance]||3;
      if (pa!==pb) return pa-pb;
      return dist(ILSC,a)-dist(ILSC,b);
    });
    estado.sel=new Set(cand.slice(0,estado.n).map(function(d){return d.id;}));
    render();
  });
  document.getElementById("rota-limpar").addEventListener("click", function(){
    estado.sel.clear(); render();
  });

  /* Leaflet só mede certo num contêiner visível: a aba começa escondida. */
  var abaRota=document.getElementById("tab-rota");
  if (abaRota) abaRota.addEventListener("click", function(){
    setTimeout(function(){ iniciarMapa(); if(mapa) mapa.invalidateSize(); render(); }, 80);
  });

  render();
})();
</script>"""

s = s[:i] + NOVO + s[j:]
ARQ.write_text(s, encoding="utf-8")
js = re.findall(r"<script>(.*?)</script>", s, re.S)[-1]
pathlib.Path("/tmp/chk.js").write_text(js, encoding="utf-8")
print("mapa real instalado ·", len(s), "bytes")
