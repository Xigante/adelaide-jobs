"""Bug: o chip "esconder quem já visitei" tinha caído dentro do grupo errado.

O que acontecia: eu pus o chip dentro da div `.rota-jan`, que é o grupo
Tarde/Manhã. E existe este handler, de antes:

    document.querySelectorAll(".rota-jan .chip").forEach(...)
      → estado.jan = b.dataset.jan

Ou seja: clicar no chip novo entrava no handler da janela de horário,
gravava `estado.jan = undefined` (ele não tem data-jan) e zerava a
seleção. A rota ficava vazia. E na direção contrária era pior e mais
silencioso: clicar em "Tarde" desmarcava o chip de visitadas sem avisar,
porque o handler força aria-pressed=false em todo chip do grupo.

Achado pelo teste de navegador: "com o chip desligado, ela volta? false"
— tinha que ser true.

Conserto: o chip sai do grupo da janela e vira um grupo próprio.
"""
import pathlib
import shutil

ARQ = pathlib.Path(__file__).resolve().parent / "Trabalho_Adelaide_CONSOLIDADO_Ago2026.html"

VELHO = ('        <button class="chip" type="button" id="rota-sem-visitadas" '
         'aria-pressed="true">esconder quem já visitei</button>\n      </div>')
NOVO = ('      </div>\n'
        '      <div class="rota-setores" role="group" aria-label="Visitas já feitas">\n'
        '        <button class="chip" type="button" id="rota-sem-visitadas" '
        'aria-pressed="true">esconder quem já visitei</button>\n'
        '      </div>')

s = ARQ.read_text(encoding="utf-8")
if VELHO not in s:
    raise SystemExit("ÂNCORA NÃO ENCONTRADA — o chip já foi movido?")
shutil.copy(ARQ, ARQ.with_suffix(".html.bak10"))
ARQ.write_text(s.replace(VELHO, NOVO, 1), encoding="utf-8")
print("chip movido para fora do grupo da janela")
