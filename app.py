# -*- coding: utf-8 -*-
"""EnergyLens — Simulador de Consumo Energético de Computadores
Projeto de Hackathon de Engenharia da Computação.

Rode com: streamlit run app.py
"""

import streamlit as st
import pandas as pd

from models.computer import Computer, COMPUTER_PRESETS
from models.activities import ACTIVITIES, get_task
from core.simulator import Simulator, StressTest
from core import report as report_mod
from core import stress as stress_mod
from core import experiments as exp_mod

st.set_page_config(page_title="EnergyLens", page_icon="⚡", layout="wide")

SCREENS = [
    "intro_problema",
    "novidade", "afetados", "impactos", "solucoes",
    "intro_objetivo", "intro_voltagem",
    "intro_quartzo", "intro_geometria",
    "selecionar_pc", "selecionar_atividade",
    "simulacao", "relatorio",
    "teste_estresse_intro", "teste_estresse_execucao",
    "teste_estresse_resultado", "teste_estresse_explicacao",
    "laboratorio",
    "conclusao",
]

# ---------------------------------------------------------------- estado ----
if "screen" not in st.session_state:
    st.session_state.screen = SCREENS[0]
if "sim" not in st.session_state:
    st.session_state.sim = None
if "computer" not in st.session_state:
    st.session_state.computer = None
if "tarifa" not in st.session_state:
    st.session_state.tarifa = 0.90
if "stress_test" not in st.session_state:
    st.session_state.stress_test = None
if "stress_test_report" not in st.session_state:
    st.session_state.stress_test_report = None


def goto(screen_key):
    st.session_state.screen = screen_key
    st.rerun()


def nav_buttons(prev_key=None, next_key=None, next_label="Continuar →", prev_label="← Voltar"):
    c1, _, c3 = st.columns([1, 4, 1])
    with c1:
        if prev_key and st.button(prev_label, use_container_width=True):
            goto(prev_key)
    with c3:
        if next_key and st.button(next_label, type="primary", use_container_width=True):
            goto(next_key)


# ========================================================== TELA: PROBLEMA ==
def screen_intro_problema():
    st.title("⚡ EnergyLens")
    st.subheader("Qual é o problema?")
    st.markdown("""
Todo computador **consome energia elétrica** — mas essa quantidade não é fixa.
Ela muda de acordo com:

- a **carga da CPU** (processamento);
- a **carga da GPU** (gráficos);
- a **tarefa realizada** (navegar é diferente de renderizar um vídeo);
- o **tempo de utilização**;
- as **configurações de desempenho** escolhidas.

Computadores mais potentes **podem consumir muito mais energia** quando
usados em cargas elevadas — e a maioria das pessoas nunca vê esse consumo
acontecer em tempo real.
    """)
    st.info("Este simulador torna esse processo **visível**.")
    nav_buttons(next_key="novidade")


# ========================================================== TELA: OBJETIVO ==
def screen_intro_objetivo():
    st.title("Objetivo do simulador")
    st.markdown("""
Este simulador representa, **de forma simplificada**, o que acontece na
prática dentro de um computador:

> **CPU + GPU + outros componentes → consumo → calor → temperatura → energia → custo**

Ele não pretende reproduzir perfeitamente um computador real — os valores são
**estimativas plausíveis para fins educacionais**, construídas a partir de
perfis de hardware modernos.
    """)
    nav_buttons(prev_key="solucoes", next_key="intro_voltagem")


# ========================================================== TELA: VOLTAGEM ==
def screen_intro_voltagem():
    st.title("Um pouco de eletricidade")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
- **Tensão (V):** "força" que empurra a corrente elétrica.
- **Corrente (A):** quantidade de carga elétrica que flui por segundo.
- **Potência (W):** V × A — energia usada *por instante*.
- **Energia (kWh):** potência **ao longo do tempo** — o que a concessionária cobra.
        """)
    with col2:
        st.markdown("""
O computador **não usa direto** os 127/220 V da tomada:

**Tomada → Fonte → Placa-mãe / VRM → CPU / GPU**

O **VRM** regula a tensão que chega ao processador. Quando a carga aumenta,
o VRM eleva ligeiramente a tensão para sustentar o clock — e isso **aumenta a
potência consumida e o calor gerado**.
        """)
    st.caption("Simplificado de propósito — o objetivo é intuição, não uma aula de eletrônica.")
    nav_buttons(prev_key="intro_objetivo", next_key="intro_quartzo")


# ========================================================== TELA: QUARTZO ==
def screen_intro_quartzo():
    st.title("O papel do quartzo")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
Cristais de **quartzo** são usados em **osciladores de frequência/clock**,
ajudando o computador a ter uma **referência de tempo estável**.

> O quartzo pode ser usado para ajudar a manter uma frequência de referência
> estável nos circuitos eletrônicos. Essa referência funciona como um
> "relógio" para organizar o funcionamento dos componentes.

**Analogia:** imagine uma banda tocando música. O clock funciona como o
ritmo que ajuda todos os instrumentos a permanecerem sincronizados.
        """)
    with col2:
        st.info(
            "**O que o quartzo NÃO faz:** ele não retira calor da CPU e não "
            "é responsável por resfriar o computador. Sua função é fornecer "
            "uma referência de frequência estável — quem cuida do calor é o "
            "sistema de refrigeração (ventoinhas, dissipadores, water cooler) "
            "e a geometria dos componentes, como você verá na próxima tela."
        )
        st.warning(
            "A temperatura pode, sim, influenciar circuitos eletrônicos "
            "(incluindo os que dependem de uma referência de frequência). Por "
            "isso, mais adiante, o simulador mostra uma pequena variação de "
            "clock em altas temperaturas — deixamos claro que isso é uma "
            "**simplificação educativa**, não um efeito direto do quartzo."
        )
    nav_buttons(prev_key="intro_voltagem", next_key="intro_geometria")


# ======================================================== TELA: GEOMETRIA ==
def screen_intro_geometria():
    st.title("Por que o formato dos componentes importa?")
    st.markdown("""
A **geometria** de um dissipador de calor influencia diretamente sua
capacidade de resfriar um componente: quanto **maior a área de contato com o
ar**, mais calor ele consegue transferir para fora.
    """)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("#### Componente de entrada")
        st.code(
            "┌──────────────┐\n"
            "│      CPU     │\n"
            "└──────────────┘\n"
            "     █████\n"
            "     █████",
            language=None,
        )
        st.caption("Dissipador pequeno, poucas aletas → pouca área para liberar calor.")
    with col2:
        st.markdown("#### Componente High-End")
        st.code(
            "│ │ │ │ │ │ │\n"
            "│ │ │ │ │ │ │\n"
            "█████████████\n"
            "     CPU",
            language=None,
        )
        st.caption("Dissipador com várias aletas → mais área de contato com o ar.")

    st.success(
        "As aletas aumentam a área disponível para transferir calor para o ar. "
        "Isso pode ajudar o componente a trabalhar em temperaturas menores."
    )

    st.markdown("#### Fluxo de ar")
    st.markdown(
        "**AR FRIO → COMPONENTE → AR QUENTE.** Uma boa circulação de ar ajuda a "
        "retirar o calor acumulado dentro do computador."
    )
    c1, c2 = st.columns(2)
    with c1:
        st.caption("PC de Entrada: fluxo de ar mais simples")
        st.text("❄️ →  [CPU]  → 🔥")
    with c2:
        st.caption("PC High-End: fluxo de ar melhor, VRM mais robusta")
        st.text("❄️❄️❄️ →  [CPU]  → 🔥🔥🔥")

    st.caption(
        "No simulador, essa diferença de geometria e fluxo de ar já está "
        "representada pelos parâmetros de refrigeração de cada PC (o quão "
        "rápido ele esfria e qual a temperatura máxima que costuma atingir)."
    )
    nav_buttons(prev_key="intro_quartzo", next_key="selecionar_pc")


# ======================================================= TELA: ESCOLHER PC ==
def screen_selecionar_pc():
    st.title("Escolha o computador")
    cols = st.columns(3)
    escolhido = None
    for col, key in zip(cols, COMPUTER_PRESETS.keys()):
        preset = COMPUTER_PRESETS[key]
        c_tier = Computer(key)
        with col:
            with st.container(border=True):
                st.markdown(f"### {preset['nome']}")
                st.caption(preset["descricao"])
                st.write(f"**CPU:** {c_tier.cpu.nome}")
                st.write(f"**GPU:** {c_tier.gpu.nome}")
                st.write(f"**Refrigeração:** {c_tier.cooling['nome']}")
                st.write(f"**Consumo máx. estimado:** {c_tier.max_power_w():.0f} W")
                st.caption(
                    f"📐 Dissipador com ~{c_tier.aletas_dissipador} aletas · "
                    f"fluxo de ar: {c_tier.fluxo_ar}"
                )
                if st.button(f"Selecionar", key=f"pc_{key}", use_container_width=True):
                    escolhido = key
    if escolhido:
        st.session_state.computer = escolhido
        goto("selecionar_atividade")
    nav_buttons(prev_key="intro_geometria")


# =================================================== TELA: ESCOLHER TAREFA ==
def screen_selecionar_atividade():
    st.title("Escolha a atividade")
    if not st.session_state.computer:
        st.warning("Selecione um computador primeiro.")
        nav_buttons(prev_key="selecionar_pc")
        return

    st.session_state.tarifa = st.number_input(
        "Tarifa de energia (R$/kWh)", min_value=0.10, max_value=3.00,
        value=st.session_state.tarifa, step=0.05,
    )

    categoria = st.radio(
        "Intensidade de uso", options=list(ACTIVITIES.keys()),
        format_func=lambda k: ACTIVITIES[k]["titulo"], horizontal=True,
    )
    tarefa = st.selectbox("Tarefa específica", options=list(ACTIVITIES[categoria]["tarefas"].keys()))

    if st.button("Iniciar simulação →", type="primary"):
        computer = Computer(st.session_state.computer)
        ranges = get_task(categoria, tarefa)
        st.session_state.sim = Simulator(
            computer, categoria, tarefa, ranges, tarifa_kwh=st.session_state.tarifa
        )
        st.session_state.sim.advance(10, passo=2)  # aquece um pouco antes de mostrar
        goto("simulacao")

    nav_buttons(prev_key="selecionar_pc")


# ======================================================== TELA: SIMULAÇÃO ==
def hud_card(col, titulo, valor, unidade, delta=None):
    with col:
        st.metric(titulo, f"{valor:.1f} {unidade}" if isinstance(valor, float) else f"{valor} {unidade}")


def screen_simulacao():
    sim: Simulator = st.session_state.sim
    if sim is None:
        st.warning("Nenhuma simulação em andamento.")
        nav_buttons(prev_key="selecionar_atividade")
        return

    st.title(f"📊 Simulação — {sim.computer.nome}")
    st.caption(f"Atividade: {sim.categoria} — {sim.tarefa}")

    snap = sim.snapshot()

    # ---- HUD ----
    st.markdown("#### CPU")
    c1, c2, c3 = st.columns(3)
    c1.metric("Utilização", f"{snap['cpu_util']:.0f} %")
    c2.progress(min(1.0, snap['cpu_util'] / 100))
    c3.metric("Potência CPU", f"{snap['power']['cpu_w']:.1f} W")

    st.markdown("#### GPU")
    g1, g2, g3 = st.columns(3)
    g1.metric("Utilização", f"{snap['gpu_util']:.0f} %")
    g2.progress(min(1.0, snap['gpu_util'] / 100))
    g3.metric("Potência GPU", f"{snap['power']['gpu_w']:.1f} W")

    st.markdown("#### Sistema")
    s1, s2, s3, s4, s5 = st.columns(5)
    s1.metric("Consumo total", f"{snap['power']['total_w']:.0f} W")
    s2.metric("Temperatura", f"{snap['temp']:.1f} °C")
    s3.progress(min(1.0, snap['temp'] / snap['temp_max_ref']))
    s4.metric("Energia acumulada", f"{snap['kwh']:.4f} kWh")
    s5.metric("Tempo simulado", f"{snap['elapsed_s']/60:.1f} min")

    custo_atual = snap['kwh'] * sim.tarifa_kwh
    st.metric("💰 Custo acumulado", f"R$ {custo_atual:.4f}")

    if snap["anomaly"]["anomalo"]:
        st.error(f"⚠️ CONSUMO ACIMA DO ESPERADO: {snap['power']['total_w']:.0f} W "
                  f"(esperado {snap['anomaly']['esperado_min']:.0f}–{snap['anomaly']['esperado_max']:.0f} W)")

    # ---- estresse prolongado / desempenho / (in)estabilidade ----
    st.divider()
    st.markdown("#### 🔥 Estresse prolongado")
    badge = stress_mod.temp_badge(snap["temp"], snap["temp_max_ref"])
    e1, e2, e3, e4 = st.columns(4)
    e1.metric("⏱️ Tempo sob estresse", stress_mod.fmt_mmss(snap["stress_s"]))
    e2.metric("🎯 Desempenho", f"{snap['performance_pct']:.0f} %")
    e3.metric(f"{badge['emoji']} Estado térmico", badge["label"])
    e4.metric("🖼️ FPS (educativo)", f"{snap['fps']:.0f}")
    st.caption(
        "O indicador de FPS é **ilustrativo** (não é medição de um jogo real) — "
        "serve só para tornar a perda de desempenho mais intuitiva."
    )

    if snap["last_event"]:
        nivel_msg = snap["last_event"]
        if "TELA AZUL" in nivel_msg:
            st.error(nivel_msg)
        elif "INSTÁVEL" in nivel_msg:
            st.error(nivel_msg)
        else:
            st.warning(nivel_msg)
        st.caption(
            "Quando os componentes ficam muito quentes, o computador pode "
            "reduzir seu desempenho para evitar danos e manter a temperatura "
            "sob controle (redução automática de desempenho / *thermal throttling*)."
        )

    with st.expander("🕰️ Clock ilustrativo e fluxo de ar deste PC"):
        cc1, cc2 = st.columns(2)
        cc1.metric("Clock (ilustrativo)", f"{snap['clock_ghz']:.2f} GHz")
        cc1.caption(
            "Valor meramente educativo. O quartzo fornece a referência de "
            "frequência do sistema, mas não é ele quem causa essa variação — "
            "isso representa, de forma simplificada, o *throttling* térmico."
        )
        cc2.write(f"🌬️ Fluxo de ar: **{sim.computer.fluxo_ar}**")
        cc2.write(f"📐 Aletas do dissipador: **{sim.computer.aletas_dissipador}**")
        cc2.caption("Veja a explicação completa na tela 'Por que o formato dos componentes importa?'.")

    if snap["lockups"] or snap["restarts"]:
        st.caption(f"Ocorrências nesta simulação — travamentos: {snap['lockups']} · reinicializações: {snap['restarts']}")

    # ---- controles de tempo ----
    st.divider()
    tcol1, tcol2, tcol3 = st.columns(3)
    if tcol1.button("⏱️ Avançar 10s"):
        sim.advance(10, passo=2)
        st.rerun()
    if tcol2.button("⏱️ Avançar 60s"):
        sim.advance(60, passo=2)
        st.rerun()
    if tcol3.button("⏱️ Avançar 5 min"):
        sim.advance(300, passo=5)
        st.rerun()

    # ---- gráficos ----
    if len(sim.real.history) > 1:
        df = pd.DataFrame(sim.real.history)
        gcol1, gcol2 = st.columns(2)
        with gcol1:
            st.caption("Potência (W) ao longo do tempo")
            st.line_chart(df.set_index("t")[["power"]])
        with gcol2:
            st.caption("Temperatura (°C) ao longo do tempo")
            st.line_chart(df.set_index("t")[["temp"]])

    # ---- desafio interativo: cenário de decisão ----
    st.divider()
    st.subheader("🧩 O que você faria?")
    st.write(
        f"O computador está em **{snap['power']['total_w']:.0f} W**, "
        f"**{snap['temp']:.0f} °C**, GPU em **{snap['gpu_util']:.0f}%**."
    )
    if st.button("😈 Simular processo desnecessário em segundo plano (+90 W)"):
        sim.inject_waste(90)
        st.rerun()

    d1, d2, d3, d4, d5 = st.columns(5)
    decisao = None
    if d1.button("🌱 Modo Economia"):
        decisao = "modo_economia"
    if d2.button("⚖️ Modo Equilibrado"):
        decisao = "modo_equilibrado"
    if d3.button("🚀 Modo Desempenho"):
        decisao = "modo_desempenho"
    if d4.button("🔍 Verificar processos"):
        decisao = "verificar_processos"
    if d5.button("⏭️ Não fazer nada"):
        decisao = "nada"

    if decisao:
        registro = sim.apply_decision(decisao)
        antes, depois = registro["antes"], registro["depois"]
        st.success(
            f"**Antes:** {antes['power']['total_w']:.0f} W — {antes['temp']:.0f} °C   →   "
            f"**Depois:** {depois['power']['total_w']:.0f} W — {depois['temp']:.0f} °C   "
            f"(Δ potência: {antes['power']['total_w']-depois['power']['total_w']:+.0f} W)"
        )
        st.rerun()

    with st.expander("Recomendações do sistema"):
        for dica in sim.recommendations():
            st.write(dica)

    st.divider()
    nav_buttons(prev_key="selecionar_atividade", next_key="relatorio", next_label="Ver relatório final →")


# ========================================================== TELA: RELATÓRIO
def screen_relatorio():
    sim = st.session_state.sim
    if sim is None or not sim.real.history:
        st.warning("Rode a simulação primeiro.")
        nav_buttons(prev_key="simulacao")
        return

    r = report_mod.build_report(sim)
    st.title("Relatório da Simulação")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Computador", r["computador"])
    c2.metric("Tempo simulado", f"{r['tempo_min']} min")
    c3.metric("Consumo médio", f"{r['consumo_medio_w']} W")
    c4.metric("Consumo máx.", f"{r['consumo_max_w']} W")

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Energia total", f"{r['kwh']} kWh")
    c6.metric("Custo estimado", f"R$ {r['custo']}")
    c7.metric("Temp. média", f"{r['temp_media']} °C")
    c8.metric("Temp. máxima", f"{r['temp_max']} °C")

    st.markdown(f"**Utilização média:** CPU {r['cpu_medio']}% · GPU {r['gpu_medio']}%")
    st.markdown(f"**Economia obtida pelas decisões do usuário:** {r['economia_pct']}%")

    st.divider()
    st.subheader("Estresse prolongado e estabilidade")
    b1, b2, b3, b4, b5 = st.columns(5)
    b1.metric("Tempo máx. sob estresse", stress_mod.fmt_mmss(r["stress_max_s"]))
    b2.metric("Desempenho médio", f"{r['performance_medio']}%")
    b3.metric("FPS médio (educativo)", f"{r['fps_medio']:.0f}")
    b4.metric("Travamentos", r["lockups"])
    b5.metric("Reinicializações", r["restarts"])
    st.markdown(f"**Estabilidade geral:** {r['estabilidade']}")

    st.subheader("Projeção de custo")
    proj = r["projecao"]
    p1, p2, p3 = st.columns(3)
    p1.metric("1 hora", f"R$ {proj['1h']['custo']}", f"{proj['1h']['kwh']} kWh")
    p2.metric("8 horas", f"R$ {proj['8h']['custo']}", f"{proj['8h']['kwh']} kWh")
    p3.metric("30 dias (8h/dia)", f"R$ {proj['30d']['custo']}", f"{proj['30d']['kwh']} kWh")

    st.divider()
    st.subheader("Conclusão")
    st.success(r["conclusao"])

    nav_buttons(prev_key="simulacao", next_key="teste_estresse_intro", next_label="Teste de estresse: Entrada x High-End →")


# ====================================================== TELAS EXPLICATIVAS ==
def screen_novidade():
    st.title("Esse problema é novo?")
    st.markdown("""
**Não.** Eficiência energética em computação já é um problema conhecido nas
áreas de computação, eletrônica e infraestrutura. Já existem:

- gerenciamento de energia (power management);
- modos de economia de energia;
- monitoramento de hardware (sensores, telemetria);
- controle dinâmico de frequência e tensão (DVFS);
- gerenciamento térmico ativo.

O diferencial deste projeto é apresentar essas relações de forma **simples,
visual e interativa** — mostrando não só o consumo, mas **por que ele
acontece, qual o impacto e o que pode ser feito**.
    """)
    nav_buttons(prev_key="intro_problema", next_key="afetados")


def screen_afetados():
    st.title("Quem é afetado por esse problema?")
    cols = st.columns(5)
    dados = [
        ("Usuários domésticos", "Aumento na conta de energia pelo uso prolongado."),
        ("Gamers", "CPU e GPU em carga elevada por várias horas seguidas."),
        ("Estudantes/profissionais", "Computador ligado por muitas horas de trabalho/estudo."),
        ("Empresas", "Muitos computadores ligados diariamente — pequenas economias somam muito."),
        ("Data centers", "Grandes volumes de equipamentos e altíssima demanda energética."),
    ]
    for col, (titulo, texto) in zip(cols, dados):
        with col:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.caption(texto)
    nav_buttons(prev_key="novidade", next_key="impactos")


def screen_impactos():
    st.title("O que esse problema causa?")
    cols = st.columns(4)
    dados = [
        ("Financeiro", "Maior consumo → maior custo de eletricidade."),
        ("Térmico", "Mais calor precisa ser dissipado — desgaste e ruído."),
        ("Desperdício", "Usar mais potência do que a tarefa exige."),
        ("Ambiental", "Consumo elétrico está ligado aos impactos da geração de energia."),
    ]
    for col, (titulo, texto) in zip(cols, dados):
        with col:
            with st.container(border=True):
                st.markdown(f"**{titulo}**")
                st.caption(texto)
    nav_buttons(prev_key="afetados", next_key="solucoes")


def screen_solucoes():
    st.title("O que podemos fazer?")
    st.markdown("""
1. **Monitorar o consumo** — W, kWh, temperatura, uso de CPU/GPU em tempo real.
2. **Modos de energia** — Economia / Equilibrado / Desempenho, conforme a necessidade.
3. **Escolher hardware adequado** — nem sempre o mais potente é o necessário.
4. **Gerenciar a GPU** — reduzir uso desnecessário em cargas leves.
5. **Gerenciar processos** — identificar aplicações consumindo recursos à toa.
6. **Melhorar a refrigeração** — reduz picos de temperatura.
7. **Detectar consumo anormal** — comparar consumo esperado × consumo real, como
   você viu na simulação.
    """)
    st.info("Você já experimentou várias dessas soluções na etapa de simulação!")
    nav_buttons(prev_key="impactos", next_key="intro_objetivo")


# ============================================== TESTE DE ESTRESSE / LONGA DURAÇÃO
def screen_teste_estresse_intro():
    st.title("Teste de Estresse: PC de Entrada x PC High-End")
    st.markdown("""
Um pico rápido de carga é diferente de **manter o computador trabalhando
intensamente por muito tempo**. Quanto maior o tempo sob estresse, maior a
chance de:

- aumento da temperatura;
- redução de desempenho (throttling);
- quedas de FPS;
- travamentos;
- redução da estabilidade;
- necessidade de resfriamento.

Agora vamos rodar a **mesma tarefa pesada, ao mesmo tempo**, em um **PC de
Entrada** e em um **PC High-End**, para ver essa diferença acontecer.
    """)

    tarefas_pesadas = list(ACTIVITIES["pesado"]["tarefas"].keys())
    tarefa = st.selectbox("Tarefa do teste de estresse", options=tarefas_pesadas)

    if st.button("Iniciar teste de estresse →", type="primary"):
        ranges = get_task("pesado", tarefa)
        st.session_state.stress_test = StressTest(
            "entrada", "premium", ranges["cpu"], ranges["gpu"]
        )
        st.session_state.stress_test_report = None
        goto("teste_estresse_execucao")

    nav_buttons(prev_key="relatorio")


def screen_teste_estresse_execucao():
    test: StressTest = st.session_state.stress_test
    if test is None:
        st.warning("Inicie o teste de estresse primeiro.")
        nav_buttons(prev_key="teste_estresse_intro")
        return

    st.title("📊 Teste de Estresse em andamento")
    snap = test.snapshot()
    a, b = snap["a"], snap["b"]

    ALVO_S = 600  # "longa duração" de referência para a barra de progresso
    tempo_frac = min(1.0, a["t"] / ALVO_S)
    st.markdown("##### ⏱️ Tempo de teste")
    st.progress(tempo_frac, text=f"{a['t']:.0f}s / {ALVO_S}s (referência de longa duração)")

    col1, col2 = st.columns(2)
    for col, snap_pc, tier_label in ((col1, a, "PC DE ENTRADA"), (col2, b, "PC HIGH-END")):
        with col:
            st.markdown(f"### {tier_label}")
            badge = stress_mod.temp_badge(snap_pc["temp"], snap_pc["temp_max_ref"])
            st.metric("Temperatura", f"{snap_pc['temp']:.1f} °C", delta=f"{badge['emoji']} {badge['label']}", delta_color="off")
            st.progress(min(1.0, snap_pc["temp"] / snap_pc["temp_max_ref"]), text="Temperatura")
            st.metric("Desempenho", f"{snap_pc['performance_pct']:.0f} %")
            st.progress(snap_pc["performance_pct"] / 100, text="Desempenho")
            st.metric("FPS (educativo)", f"{snap_pc['fps']:.0f}")
            st.metric("Tempo sob estresse", stress_mod.fmt_mmss(snap_pc["stress_s"]))
            problemas = snap_pc["lockups"] + snap_pc["restarts"]
            st.metric("Problemas (travamentos + reinícios)", problemas)
            estab_parcial = stress_mod.estabilidade_rating(
                snap_pc["lockups"], snap_pc["restarts"], snap_pc["performance_pct"]
            )
            st.write(f"**Estabilidade parcial:** {estab_parcial}")

            track = test.track_a if tier_label == "PC DE ENTRADA" else test.track_b
            if track.last_event:
                if "TELA AZUL" in track.last_event or "INSTÁVEL" in track.last_event:
                    st.error(track.last_event)
                else:
                    st.warning(track.last_event)

    if len(test.track_a.history) > 1:
        st.divider()
        st.caption("Temperatura ao longo do tempo")
        df_cmp = pd.DataFrame({
            "t": [h["t"] for h in test.track_a.history],
            "PC de Entrada": [h["temp"] for h in test.track_a.history],
            "PC High-End": [h["temp"] for h in test.track_b.history],
        }).set_index("t")
        st.line_chart(df_cmp)

    st.divider()
    t1, t2, t3 = st.columns(3)
    if t1.button("⏱️ Avançar 10s"):
        test.advance(10, passo=2)
        st.rerun()
    if t2.button("⏱️ Avançar 60s"):
        test.advance(60, passo=2)
        st.rerun()
    if t3.button("⏱️ Avançar 2 min (uso prolongado)"):
        test.advance(120, passo=5)
        st.rerun()

    st.divider()
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("← Reiniciar teste"):
            st.session_state.stress_test = None
            goto("teste_estresse_intro")
    with c2:
        if st.button("🏁 Finalizar teste e ver resultado →", type="primary"):
            st.session_state.stress_test_report = {
                "entrada": report_mod.build_stress_test_report(test.track_a),
                "high_end": report_mod.build_stress_test_report(test.track_b),
            }
            goto("teste_estresse_resultado")


def screen_teste_estresse_resultado():
    rep = st.session_state.stress_test_report
    if rep is None:
        st.warning("Finalize o teste de estresse primeiro.")
        nav_buttons(prev_key="teste_estresse_execucao")
        return

    st.title("🏁 Resultado do Teste de Estresse")
    ra, rb = rep["entrada"], rep["high_end"]

    df = pd.DataFrame({
        "": ["Temp. máxima (°C)", "Desempenho médio (%)", "FPS médio", "Travamentos", "Reinicializações", "Estabilidade"],
        "PC de Entrada": [ra["temp_max"], ra["performance_medio"], ra["fps_medio"], ra["travamentos"], ra["reinicializacoes"], ra["estabilidade"]],
        "PC High-End": [rb["temp_max"], rb["performance_medio"], rb["fps_medio"], rb["travamentos"], rb["reinicializacoes"], rb["estabilidade"]],
    }).set_index("")
    st.table(df)

    st.caption(
        "Todos os valores acima foram **calculados pela simulação** durante o "
        "teste que você acabou de rodar — nada foi fixado no código."
    )
    nav_buttons(prev_key="teste_estresse_execucao", next_key="teste_estresse_explicacao", next_label="Por que existiu essa diferença? →")


def screen_teste_estresse_explicacao():
    st.title("🔎 Por que existiu essa diferença?")
    st.markdown("""
A diferença de comportamento entre o PC de Entrada e o PC High-End sob carga
prolongada acontece por um conjunto de fatores combinados:

- **Melhor dissipação de calor** — dissipadores com mais aletas e maior área de contato com o ar.
- **Melhor circulação de ar** — fluxo de ar mais forte remove o calor acumulado mais rápido.
- **Geometria dos dissipadores** — mais área de superfície transfere mais calor por segundo.
- **Componentes mais preparados para cargas prolongadas** — CPU/GPU e VRM com maior margem térmica.
- **Menor perda de energia e menor aquecimento** relativo à potência entregue.
- **Maior estabilidade** — menos throttling, menos travamentos, menos reinicializações.
    """)
    st.info(
        "🔷 **Sobre o quartzo:** ele tem outra função — ajudar em referências de "
        "frequência e sincronização dos circuitos. Ele **não é responsável pela "
        "dissipação de calor** nem pela diferença de estabilidade observada acima."
    )
    st.warning(
        "⚠️ Os valores utilizados nesta simulação são **simplificados e "
        "hipotéticos**, para demonstrar conceitos de Física e Computação. Não "
        "representam testes reais de placas-mãe ou componentes específicos."
    )
    nav_buttons(prev_key="teste_estresse_resultado", next_key="laboratorio", next_label="Laboratório de experimentos →")


# ============================================== LABORATÓRIO DE EXPERIMENTOS
# Todos os números vêm de core/experiments.py, que roda o mesmo motor da
# simulação principal com carga controlada (semente fixa → reproduzível).
def _lab_topo(exp_id: int):
    meta = exp_mod.EXPERIMENTOS[exp_id]
    st.markdown(f"### Experimento {exp_id} — {meta['titulo']}")
    st.caption(exp_mod.GRUPO_ROTULO[meta["grupo"]])
    st.markdown(f"**Pergunta experimental:** {meta['pergunta']}")
    with st.expander("Objetivo, procedimento e o que observar"):
        st.markdown(f"**Objetivo:** {meta['objetivo']}")
        st.markdown("**Procedimento:**")
        st.markdown("\n".join(f"{i}. {p}" for i, p in enumerate(meta["procedimento"], 1)))
        st.markdown(f"**O que observar:** {meta['observar']}")


def _lab_fim(exp_id: int, df: pd.DataFrame, conclusao: str):
    st.success(f"**Conclusão gerada pela simulação:** {conclusao}")
    st.download_button(
        "Baixar tabela (CSV)", df.to_csv(index=False).encode("utf-8-sig"),
        file_name=f"experimento_{exp_id}.csv", mime="text/csv", key=f"lab_dl_{exp_id}",
    )


def _lab_exp1(tier):
    _lab_topo(1)
    r = exp_mod.exp1_normal_vs_elevado(tier)
    st.dataframe(r["tabela"], hide_index=True)
    lo, hi = r["faixa_esperada"]
    st.caption(f"Faixa de consumo esperada para a carga normal: {lo:.0f}–{hi:.0f} W (limite de alerta = 115% do máximo esperado).")
    st.caption("Temperatura (°C) ao longo do tempo")
    st.line_chart(r["temp_tempo"])
    _lab_fim(1, r["tabela"], r["conclusao"])


def _lab_exp2(tier):
    _lab_topo(2)
    r = exp_mod.exp2_carga_progressiva(tier)
    st.dataframe(r["tabela"], hide_index=True)
    g1, g2 = st.columns(2)
    with g1:
        st.caption("Carga (%) × Potência (W)")
        st.line_chart(r["carga_potencia"])
    with g2:
        st.caption("Carga (%) × Temperatura estabilizada (°C)")
        st.line_chart(r["carga_temp"])
    _lab_fim(2, r["tabela"], r["conclusao"])


def _lab_exp3(tier):
    _lab_topo(3)
    r = exp_mod.exp3_potencia_x_temperatura(tier)
    st.caption("Potência (W) × Temperatura de equilíbrio (°C)")
    st.scatter_chart(r["tabela"], x="Potência (W)", y="Temp. estabilizada (°C)", color="Série")
    with st.expander("Ver tabela de dados"):
        st.dataframe(r["tabela"], hide_index=True)
    _lab_fim(3, r["tabela"], r["conclusao"])


def _lab_exp4(tier):
    _lab_topo(4)
    carga = st.slider("Carga do sistema (%)", 50, 100, 80, step=5, key="lab_exp4_carga")
    r = exp_mod.exp4_refrigeracao(tier, carga=carga)
    st.dataframe(r["tabela"], hide_index=True)
    st.caption(f"Temperatura (°C) ao longo do tempo — limite térmico do componente: {exp_mod.LIMITE_TERMICO_LAB_C:.0f} °C")
    st.line_chart(r["temp_tempo"])
    _lab_fim(4, r["tabela"], r["conclusao"])


def _lab_exp5(tier):
    _lab_topo(5)
    carga = st.slider("Carga do sistema (%)", 20, 100, 80, step=5, key="lab_exp5_carga")
    r = exp_mod.exp5_tempo_x_temperatura(tier, carga=carga)
    c1, c2 = st.columns([1, 2])
    with c1:
        st.dataframe(r["tabela"], hide_index=True)
    with c2:
        st.caption("Temperatura (°C) × tempo (s)")
        st.line_chart(r["temp_tempo"])
    _lab_fim(5, r["tabela"], r["conclusao"])


def _lab_exp6(tier):
    _lab_topo(6)
    r = exp_mod.exp6_sobrecarga(tier)
    st.dataframe(r["tabela"], hide_index=True)
    st.caption(f"A sobrecarga começa em t = {r['t_sobrecarga_s']} s.")
    g1, g2 = st.columns(2)
    with g1:
        st.caption("Temperatura (°C)")
        st.line_chart(r["series"][["Temperatura (°C)"]])
    with g2:
        st.caption("Desempenho entregue (%)")
        st.line_chart(r["series"][["Desempenho (%)"]])
    _lab_fim(6, r["tabela"], r["conclusao"])


def _lab_exp7(tier):
    _lab_topo(7)
    r = exp_mod.exp7_variacao_brusca(tier)
    st.dataframe(r["tabela"], hide_index=True)
    g1, g2, g3 = st.columns(3)
    with g1:
        st.caption("Carga (%)")
        st.line_chart(r["series"][["Carga (%)"]])
    with g2:
        st.caption("Potência (W) — resposta elétrica")
        st.line_chart(r["series"][["Potência (W)"]])
    with g3:
        st.caption("Temperatura (°C) — resposta térmica")
        st.line_chart(r["series"][["Temperatura (°C)"]])
    _lab_fim(7, r["tabela"], r["conclusao"])


def _lab_exp8(tier):
    _lab_topo(8)
    r = exp_mod.exp8_comparativo(tier)
    st.dataframe(r["tabela"], hide_index=True)
    st.caption(f"Limite térmico do componente usado na classificação: {r['limite_c']:.0f} °C.")
    _lab_fim(8, r["tabela"], r["conclusao"])


LAB_RENDERERS = {1: _lab_exp1, 2: _lab_exp2, 3: _lab_exp3, 4: _lab_exp4,
                 5: _lab_exp5, 6: _lab_exp6, 7: _lab_exp7, 8: _lab_exp8}


def screen_laboratorio():
    st.title("🔬 Laboratório de Experimentos")
    st.markdown(
        "Até aqui você **usou** o simulador. Agora vamos **medir**: em cada experimento uma variável é alterada, "
        "os parâmetros são registrados e a conclusão vem dos dados — todos os valores são calculados pela "
        "simulação (com semente fixa, então o resultado é reproduzível)."
    )
    st.markdown("##### A grande pergunta do projeto")
    st.info(
        "Como o aumento ou a irregularidade do consumo de energia de um sistema computacional influencia "
        "seu comportamento elétrico e térmico?"
    )
    st.code(
        "1. O consumo aumenta?\n"
        "     ↓\n"
        "2. A potência aumenta?\n"
        "     ↓\n"
        "3. O calor gerado aumenta?\n"
        "     ↓\n"
        "4. A temperatura aumenta?\n"
        "     ↓\n"
        "5. A capacidade de refrigeração consegue controlar esse aumento?",
        language=None,
    )

    c1, c2 = st.columns([1, 2])
    with c1:
        tier = st.selectbox(
            "Computador usado nos experimentos", options=list(COMPUTER_PRESETS.keys()), index=1,
            format_func=lambda k: COMPUTER_PRESETS[k]["nome"], key="lab_pc",
        )
    with c2:
        enxuto = st.checkbox(
            "Modo enxuto: só os recomendados (⭐ 4 essenciais + 🔄 variação brusca)", key="lab_enxuto"
        )

    ids = [i for i, m in exp_mod.EXPERIMENTOS.items()
           if not enxuto or m["grupo"] in ("essencial", "opcional")]
    prefixo = {"essencial": "⭐ ", "opcional": "🔄 ", "complementar": ""}
    rotulos = [prefixo[exp_mod.EXPERIMENTOS[i]["grupo"]] + exp_mod.EXPERIMENTOS[i]["aba"] for i in ids]
    for aba, i in zip(st.tabs(rotulos), ids):
        with aba:
            LAB_RENDERERS[i](tier)

    st.caption(
        "⚠️ Modelo educativo simplificado: a temperatura de equilíbrio é proporcional à potência por construção "
        "(aproximação de 1ª ordem) e a corrente da CPU é estimada como I = P / V. Em hardware real essas relações "
        "não são perfeitamente lineares."
    )
    nav_buttons(prev_key="teste_estresse_explicacao", next_key="conclusao")


def screen_conclusao():
    st.title("Tecnologia também é eficiência")
    st.markdown("""
```
PROBLEMA            → Consumo energético pouco percebido
        ↓
MONITORAMENTO       → CPU + GPU + temperatura + consumo
        ↓
ANÁLISE             → Comparação entre consumo esperado e real
        ↓
DETECÇÃO            → Identificação de desperdícios
        ↓
RECOMENDAÇÃO        → Sugestões de otimização
        ↓
RESULTADO           → Menor consumo + menor temperatura + menor custo
```
    """)
    st.success(
        "Não basta saber que um computador consome energia — é preciso entender "
        "**por que**, qual o **impacto**, e como a **tecnologia** pode ajudar a "
        "identificar e reduzir desperdícios."
    )
    if st.button("Reiniciar simulação"):
        st.session_state.sim = None
        st.session_state.computer = None
        st.session_state.stress_test = None
        st.session_state.stress_test_report = None
        goto("intro_problema")
    nav_buttons(prev_key="laboratorio")


# ================================================================= ROTEADOR
SCREEN_FUNCS = {
    "intro_problema": screen_intro_problema,
    "intro_objetivo": screen_intro_objetivo,
    "intro_voltagem": screen_intro_voltagem,
    "intro_quartzo": screen_intro_quartzo,
    "intro_geometria": screen_intro_geometria,
    "selecionar_pc": screen_selecionar_pc,
    "selecionar_atividade": screen_selecionar_atividade,
    "simulacao": screen_simulacao,
    "relatorio": screen_relatorio,
    "novidade": screen_novidade,
    "afetados": screen_afetados,
    "impactos": screen_impactos,
    "solucoes": screen_solucoes,
    "teste_estresse_intro": screen_teste_estresse_intro,
    "teste_estresse_execucao": screen_teste_estresse_execucao,
    "teste_estresse_resultado": screen_teste_estresse_resultado,
    "teste_estresse_explicacao": screen_teste_estresse_explicacao,
    "laboratorio": screen_laboratorio,
    "conclusao": screen_conclusao,
}

with st.sidebar:
    st.markdown("### ⚡ EnergyLens")
    st.caption("Simulador educativo de consumo energético")
    st.progress((SCREENS.index(st.session_state.screen) + 1) / len(SCREENS))
    st.caption(f"Etapa {SCREENS.index(st.session_state.screen)+1} de {len(SCREENS)}")
    st.caption(
        "⚠️ Valores simplificados e hipotéticos, para fins didáticos — não "
        "representam testes reais de hardware."
    )

SCREEN_FUNCS[st.session_state.screen]()
