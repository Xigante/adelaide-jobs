"""Três ajustes no mini-mapa, vistos na renderização:

1. O nome das ruas saía cortado — a margem esquerda de 62 px não cabia
   "Wakefield / Grote". Margens separadas por lado.
2. Negócios no mesmo endereço (três lojas no mesmo shopping) caíam
   exatamente no mesmo ponto e viravam um borrão. Deslocamento mínimo,
   determinístico, só para separar visualmente.
3. "0 m da parada anterior" agora diz "mesmo prédio", que é o que
   aquele zero significa.
"""
import pathlib
import re

ARQ = pathlib.Path("Trabalho_Adelaide_CONSOLIDADO_Ago2026.html")
s = ARQ.read_text(encoding="utf-8")

NOVA = r"""  function svgMapa(rota){
    var ME = 168, MT = 46, MD = 26, MB = 60;      /* margens por lado */
    var p = ['<svg viewBox="0 0 ' + (ME+1000+MD) + ' ' + (MT+1000+MB) + '" role="img" ' +
             'aria-label="Esquema do centro de Adelaide com as paradas da rota">'];

    /* Vários negócios dividem o mesmo endereço — três lojas no mesmo
       shopping caem no mesmo ponto e viram um borrão. Um deslocamento
       mínimo e determinístico (sempre o mesmo para o mesmo registro)
       separa visualmente sem inventar posição nenhuma. */
    function px(d){ return ME + d.x + ((d.id * 37) % 5 - 2) * 7; }
    function py(d){ return MT + d.y + ((d.id * 53) % 5 - 2) * 7; }

    p.push('<rect x="'+ME+'" y="'+MT+'" width="1000" height="1000" fill="none" ' +
           'stroke="var(--line-ctl)" stroke-width="2"/>');
    CORREDORES.forEach(function(c){
      if (c[0] === 0 || c[0] === 1000) return;
      p.push('<line x1="'+ME+'" y1="'+(MT+c[0])+'" x2="'+(ME+1000)+'" y2="'+(MT+c[0])+
             '" stroke="var(--line)" stroke-width="1"/>');
      p.push('<text x="'+(ME-12)+'" y="'+(MT+c[0]+7)+'" text-anchor="end" font-size="20" ' +
             'fill="var(--ink-3)">'+esc(c[1])+'</text>');
    });
    TRANSV.forEach(function(t){
      if (t[0] === 0 || t[0] === 1000) return;
      p.push('<line x1="'+(ME+t[0])+'" y1="'+MT+'" x2="'+(ME+t[0])+'" y2="'+(MT+1000)+
             '" stroke="var(--line)" stroke-width="1"/>');
      p.push('<text x="'+(ME+t[0])+'" y="'+(MT-14)+'" text-anchor="middle" font-size="20" ' +
             'fill="var(--ink-3)">'+esc(t[1])+'</text>');
    });
    /* Victoria Square, o único marco que quebra a grade */
    p.push('<rect x="'+(ME+455)+'" y="'+(MT+600)+'" width="90" height="120" ' +
           'fill="var(--surface-2)" stroke="var(--line)"/>');
    p.push('<text x="'+(ME+500)+'" y="'+(MT+665)+'" text-anchor="middle" font-size="18" ' +
           'fill="var(--ink-3)">Victoria Sq</text>');

    filtrados().forEach(function(d){
      if (estado.sel.has(d.id)) return;
      p.push('<g class="pt" data-id="'+d.id+'"><circle cx="'+px(d)+'" cy="'+py(d)+'" r="9" ' +
             'fill="var(--s'+SLOTS[d.setor]+')" opacity=".55"/><title>'+esc(d.empregador)+
             ' — '+esc(d.endereco)+'</title></g>');
    });

    if (rota.length){
      var linha = [(ME+ILSC.x)+','+(MT+ILSC.y)]
        .concat(rota.map(function(q){ return px(q)+','+py(q); })).join(' ');
      p.push('<polyline points="'+linha+'" fill="none" stroke="var(--brand)" stroke-width="4" ' +
             'stroke-linejoin="round" stroke-dasharray="14 8" opacity=".85"/>');
      rota.forEach(function(d, i){
        p.push('<g class="pt" data-id="'+d.id+'"><circle cx="'+px(d)+'" cy="'+py(d)+'" r="17" ' +
               'fill="var(--brand)"/><text x="'+px(d)+'" y="'+(py(d)+7)+'" text-anchor="middle" ' +
               'font-size="20" font-weight="700" fill="var(--brand-ink)">'+(i+1)+'</text>' +
               '<title>'+esc(d.empregador)+'</title></g>');
      });
    }

    p.push('<g><circle cx="'+(ME+ILSC.x)+'" cy="'+(MT+ILSC.y)+'" r="13" fill="none" ' +
           'stroke="var(--s2)" stroke-width="4"/><text x="'+(ME+ILSC.x)+'" y="'+(MT+ILSC.y-24)+
           '" text-anchor="middle" font-size="21" font-weight="700" fill="var(--s2)">ILSC</text>' +
           '<title>'+esc(ILSC.nome)+'</title></g>');
    p.push('<text x="'+(ME+500)+'" y="'+(MT+1044)+'" text-anchor="middle" font-size="19" ' +
           'fill="var(--ink-3)">esquema · 1 km entre as Terraces</text>');
    p.push('</svg>');
    return p.join('');
  }
"""

# a função vai de "function svgMapa" até a linha em branco antes de "function filtrados"
i = s.index("  function svgMapa(rota){")
j = s.index("  function filtrados(){")
s = s[:i] + NOVA + "\n" + s[j:]

# ── "0 m da parada anterior" não é informação, é ruído ──────────────
velho = """        return '<li><span class="nome">'+esc(d.empregador)+"""
novo = """        var trecho = passo < 25
          ? 'mesmo prédio da parada anterior'
          : passo + ' m da parada anterior · ' + Math.max(1, Math.round(passo/80)) + ' min';
        return '<li><span class="nome">'+esc(d.empregador)+"""
assert velho in s
s = s.replace(velho, novo, 1)

velho = """          '<span class="andar">'+passo+' m da parada anterior · '+Math.max(1,Math.round(passo/80))+' min</span>'+"""
assert velho in s
s = s.replace(velho, """          '<span class="andar">'+trecho+'</span>'+""", 1)

ARQ.write_text(s, encoding="utf-8")

js = re.findall(r"<script[^>]*>(.*?)</script>", s, re.S)[-1]
pathlib.Path("/tmp/chk.js").write_text(js, encoding="utf-8")
print("svgMapa trocada ·", len(re.findall(r"\(M\+", js)), "referências antigas a M+ restantes")
