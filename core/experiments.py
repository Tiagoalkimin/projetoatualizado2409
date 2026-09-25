# -*- coding: utf-8 -*-
"""LABORATÓRIO DE EXPERIMENTOS do EnergyLens.

Cada experimento roda o MESMO motor da simulação principal (Track, energy,
thermal, stress) com uma carga controlada e devolve tabelas, séries para
gráficos e uma conclusão em texto. Todos os números vêm da simulação — nada é
escrito à mão (incluindo os textos de conclusão, que são montados a partir dos
resultados).

Reprodutibilidade: as execuções usam uma semente fixa (SEED) e restauram o
estado do gerador aleatório ao final, então rodar o mesmo experimento duas
vezes dá exatamente o mesmo resultado e não interfere no resto do app.

IMPORTANTE (fins didáticos): o modelo térmico é uma aproximação de 1ª ordem.
A temperatura de equilíbrio é proporcional à potência por construção; em
hardware real a relação não é perfeitamente linear.
"""

import random

import pandas as pd

from models.computer import Computer
from models.components import COOLING
from . import energy, thermal, stress, recommendations as reco
from .simulator import Track

SEED = 7
DT_S = 2                      # passo de simulação (s)
DURACAO_S = 600               # 10 min simulados: > 10 constantes de tempo (tau máx. = 55 s)
FRACAO_AVISO = 0.85           # mesmo limiar de aviso/throttling de stress.check_thermal_event
FRACAO_INSTAVEL = 0.95        # mesmo limiar de instabilidade
FRACAO_NORMAL_MAX = 0.75      # abaixo disso: situação "Normal" (ver temp_badge)
LIMITE_TERMICO_LAB_C = 84.0   # limite térmico fixo do componente no experimento de refrigeração

# --------------------------------------------------------------- metadados --
EXPERIMENTOS = {
    1: {
        "titulo": "Condição normal × consumo elevado",
        "aba": "1 · Normal × elevado",
        "grupo": "essencial",
        "objetivo": "Estabelecer como o sistema se comporta em condição normal e comparar com uma condição de consumo elevado.",
        "pergunta": "Como o aumento da carga altera a corrente, a potência e a temperatura do computador?",
        "procedimento": [
            "Cenário A — alimentação estável, carga normal (25%).",
            "Cenário B — mesma máquina com a carga elevada a 100%.",
            "Registrar corrente estimada da CPU, potência e temperatura ao longo de 10 min simulados.",
            "Comparar o consumo medido com a faixa esperada para a carga normal (detector de anomalia do simulador).",
        ],
        "observar": "Carga ↑ → Corrente ↑ → Potência ↑ → Calor gerado ↑ → Temperatura ↑.",
    },
    2: {
        "titulo": "Aumento progressivo da carga",
        "aba": "2 · Carga progressiva",
        "grupo": "essencial",
        "objetivo": "Mostrar, com dados, como a potência e a temperatura respondem a degraus de carga.",
        "pergunta": "Existe uma relação entre carga e potência, e entre potência e temperatura?",
        "procedimento": [
            "Rodar quatro condições: 25%, 50%, 75% e 100% de carga (10 min simulados cada).",
            "Registrar a corrente estimada, a potência e a temperatura estabilizada de cada uma.",
            "Montar os gráficos Carga × Potência e Carga × Temperatura.",
        ],
        "observar": "Se carga ↑ ⇒ P ↑ e se P ↑ ⇒ T ↑ — e se cada degrau custa o mesmo ou mais que o anterior.",
    },
    3: {
        "titulo": "Consumo elétrico × aquecimento",
        "aba": "3 · Potência × temperatura",
        "grupo": "essencial",
        "objetivo": "Isolar a relação entre potência dissipada e temperatura (Termodinâmica).",
        "pergunta": "Como o aumento da potência consumida influencia a temperatura do sistema?",
        "procedimento": [
            "Série 1 — variar a potência mudando a carga de 10% a 100%.",
            "Série 2 — variar a potência com carga fixa (30%) acrescentando um processo desnecessário em segundo plano.",
            "Registrar a temperatura de equilíbrio de cada ponto e montar o gráfico Potência × Temperatura.",
        ],
        "observar": "Efeito Joule, dissipação de calor e equilíbrio térmico: a temperatura depende da potência dissipada, não de onde ela vem.",
    },
    4: {
        "titulo": "O papel da refrigeração",
        "aba": "4 · Refrigeração",
        "grupo": "essencial",
        "objetivo": "Introduzir a capacidade de dissipação de calor como variável, mantendo o consumo constante.",
        "pergunta": "Como a capacidade de dissipação de calor influencia a temperatura de um computador submetido à mesma carga elétrica?",
        "procedimento": [
            "Cenário A — carga elevada com refrigeração reduzida (básica).",
            "Cenário B — mesma carga com refrigeração normal (intermediária).",
            "Cenário C — mesma carga com refrigeração eficiente (robusta).",
            "Todos os cenários usam o mesmo limite térmico do componente, para comparar só a dissipação.",
        ],
        "observar": "Mesma carga → boa dissipação: temperatura controlada; má dissipação: temperatura elevada, mais throttling e instabilidade.",
    },
    5: {
        "titulo": "Tempo de operação × temperatura",
        "aba": "5 · Tempo × temperatura",
        "grupo": "complementar",
        "objetivo": "Explicar o conceito de equilíbrio térmico observando a evolução no tempo.",
        "pergunta": "A temperatura aumenta rápido, devagar, estabiliza ou continua subindo?",
        "procedimento": [
            "Escolher uma carga e deixar a simulação evoluir por 10 min simulados.",
            "Registrar tempo, potência e temperatura em 0, 10, 20, 30, 60, 120, 300 e 600 s.",
        ],
        "observar": "A curva sobe rápido no início e depois se aproxima de um valor de equilíbrio.",
    },
    6: {
        "titulo": "Simulação de sobrecarga",
        "aba": "6 · Sobrecarga",
        "grupo": "complementar",
        "objetivo": "Representar diretamente o problema: uma sobrecarga súbita em um sistema que operava normalmente.",
        "pergunta": "O que acontece, e em quanto tempo, quando um computador em operação normal sofre uma sobrecarga?",
        "procedimento": [
            "Operar em carga normal (25%) por 2 min simulados.",
            "Aumentar a carga para 100% e manter por 8 min simulados.",
            "Registrar potência, corrente estimada, temperatura, tempo até os limites e o alerta de consumo.",
        ],
        "observar": "Operação normal → aumento da demanda → aumento do consumo → mais potência dissipada → mais calor → temperatura elevada.",
    },
    7: {
        "titulo": "Variação brusca de carga",
        "aba": "7 · Variação brusca",
        "grupo": "opcional",
        "objetivo": "Comparar a resposta elétrica (rápida) com a resposta térmica (gradual).",
        "pergunta": "A resposta elétrica e a resposta térmica acontecem da mesma maneira quando a carga muda de repente?",
        "procedimento": [
            "Carga em 25% (2 min) → salta para 100% (4 min) → volta para 25% (4 min).",
            "Observar como a potência e a temperatura respondem em cada mudança.",
        ],
        "observar": "A potência muda quase imediatamente; a temperatura evolui de forma gradual, tanto na subida quanto na descida.",
    },
    8: {
        "titulo": "Qual situação é mais crítica?",
        "aba": "8 · Comparativo",
        "grupo": "complementar",
        "objetivo": "Fechar a análise comparando cenários de uso e classificando cada situação.",
        "pergunta": "Entre uso leve, moderado, intenso e intenso com baixa dissipação, qual é a situação mais crítica?",
        "procedimento": [
            "A — uso leve (20%), B — uso moderado (50%), C — uso intenso (90%).",
            "D — uso intenso (90%) com refrigeração reduzida (básica).",
            "Classificar cada cenário pela temperatura máxima em relação ao limite do componente.",
        ],
        "observar": "Consumo alto sozinho gera 'Atenção'; consumo alto com baixa dissipação leva ao 'Crítico'.",
    },
}

GRUPO_ROTULO = {"essencial": "⭐ essencial", "opcional": "🔄 opcional", "complementar": "complementar"}


# ------------------------------------------------------------ infraestrutura --
def make_computer(tier: str, cooling_tier: str = None) -> Computer:
    """Computador do preset `tier`; opcionalmente com a refrigeração de outro nível."""
    pc = Computer(tier)
    if cooling_tier and cooling_tier != tier:
        pc.cooling = dict(COOLING[cooling_tier])
    return pc


def _linha_inicial(computer: Computer, carga: float, waste_w: float = 0.0) -> dict:
    p = energy.compute_power(computer, carga, carga, waste_w)
    return {
        "t": 0.0, "segmento": 0, "carga": float(carga), "potencia": p["total_w"],
        "cpu_w": p["cpu_w"], "gpu_w": p["gpu_w"],
        "corrente_cpu_a": round(p["cpu_w"] / computer.cpu.voltage_v(carga), 2),
        "temp": round(thermal.AMBIENTE_C + 5, 1), "desempenho": 100.0,
        "fps": computer.fps_base, "travamentos": 0, "reinicios": 0, "nivel": "normal", "kwh": 0.0,
    }


def _run(computer: Computer, segmentos: list, dt: int = DT_S, limite_ref: float = None, seed: int = SEED):
    """Executa uma sequência de segmentos {"dur": s, "carga": %, "waste_w": W}.

    Devolve (track, linhas). A carga é aplicada igualmente a CPU e GPU.
    """
    estado_rng = random.getstate()
    random.seed(seed)
    try:
        track = Track(computer)
        track.modo = "laboratorio"
        track.temp_limite_ref = limite_ref
        linhas = []
        for idx, seg in enumerate(segmentos):
            carga = float(seg["carga"])
            track.waste_w = float(seg.get("waste_w", 0.0))
            restante = seg["dur"]
            while restante > 0:
                passo = min(dt, restante)
                r = track.tick((carga, carga), (carga, carga), passo)
                h = track.history[-1]
                linhas.append({
                    "t": h["t"], "segmento": idx, "carga": carga,
                    "potencia": h["power"],
                    "cpu_w": h["power_detail"]["cpu_w"], "gpu_w": h["power_detail"]["gpu_w"],
                    "corrente_cpu_a": round(h["power_detail"]["cpu_w"] / computer.cpu.voltage_v(h["cpu"]), 2),
                    "temp": h["temp"], "desempenho": h["performance_pct"], "fps": h["fps"],
                    "travamentos": h["lockups"], "reinicios": h["restarts"],
                    "nivel": r["evento"]["nivel"], "kwh": track.kwh,
                })
                restante -= passo
    finally:
        random.setstate(estado_rng)
    return track, linhas


def _tempo_ate(linhas, condicao, t0: float = 0.0):
    """Segundos (a partir de t0) até a primeira linha que cumpre a condição; None se nunca."""
    for r in linhas:
        if r["t"] > t0 and condicao(r):
            return r["t"] - t0
    return None


def _t63(linhas, t_ini: float, temp_ini: float, temp_fim: float):
    """Tempo (s) para a temperatura percorrer 63,2% da variação temp_ini → temp_fim."""
    if abs(temp_fim - temp_ini) < 0.5:
        return None
    alvo = temp_ini + 0.632 * (temp_fim - temp_ini)
    subindo = temp_fim >= temp_ini
    return _tempo_ate(
        linhas, lambda r: (r["temp"] >= alvo) if subindo else (r["temp"] <= alvo), t0=t_ini
    )


def _inclinacao(xs, ys) -> float:
    """Inclinação da reta de mínimos quadrados (dy/dx)."""
    n = len(xs)
    if n < 2:
        return 0.0
    mx, my = sum(xs) / n, sum(ys) / n
    den = sum((x - mx) ** 2 for x in xs)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / den if den else 0.0


def _media(linhas, chave) -> float:
    return sum(r[chave] for r in linhas) / len(linhas)


def _fmt_seg(valor) -> str:
    return "não ocorreu" if valor is None else f"{valor:.0f} s"


def _estado_termico(temp: float, ref: float) -> str:
    b = stress.temp_badge(temp, ref)
    return f"{b['emoji']} {b['label']}"


def _situacao(temp_max: float, limite: float, reinicios: int) -> str:
    frac = temp_max / limite if limite else 0.0
    if reinicios > 0 or frac >= FRACAO_INSTAVEL:
        return "🔴 Crítico"
    if frac >= FRACAO_NORMAL_MAX:
        return "🟠 Atenção"
    return "🟢 Normal"


# ================================================================ EXPERIMENTO 1
def exp1_normal_vs_elevado(tier: str, carga_normal: float = 25, carga_alta: float = 100, dur: int = DURACAO_S) -> dict:
    cenarios = (("A — Normal", carga_normal), ("B — Consumo elevado", carga_alta))
    linhas_tab, series, finais = [], {}, {}
    faixa = None

    for nome, carga in cenarios:
        pc = make_computer(tier)
        ref = pc.cooling["temp_max_ref"]
        track, linhas = _run(pc, [{"carga": carga, "dur": dur}])
        fim = linhas[-1]
        if faixa is None:  # faixa esperada = carga normal ± 5 pontos percentuais
            lo, hi = max(0, carga - 5), min(100, carga + 5)
            faixa = energy.expected_power_range(pc, (lo, hi), (lo, hi))
        anom = reco.detect_anomaly(fim["potencia"], faixa)
        finais[nome] = fim
        series[nome] = pd.Series({r["t"]: r["temp"] for r in linhas})
        linhas_tab.append({
            "Cenário": nome,
            "Carga (%)": carga,
            "Corrente CPU (A)": fim["corrente_cpu_a"],
            "Potência (W)": fim["potencia"],
            "Temp. final (°C)": fim["temp"],
            "Estado térmico": _estado_termico(fim["temp"], ref),
            "Desempenho médio (%)": round(_media(linhas, "desempenho"), 1),
            "Travamentos": fim["travamentos"],
            "Consumo vs. esperado": "⚠️ acima do esperado" if anom["anomalo"] else "✅ dentro do esperado",
        })

    a, b = finais[cenarios[0][0]], finais[cenarios[1][0]]
    conclusao = (
        f"Ao elevar a carga de {carga_normal:.0f}% para {carga_alta:.0f}%, a corrente estimada da CPU foi de "
        f"{a['corrente_cpu_a']} A para {b['corrente_cpu_a']} A, a potência de {a['potencia']:.0f} W para "
        f"{b['potencia']:.0f} W ({(b['potencia'] / a['potencia'] - 1) * 100:+.0f}%) e a temperatura estabilizada de "
        f"{a['temp']:.1f} °C para {b['temp']:.1f} °C ({b['temp'] - a['temp']:+.1f} °C). "
        f"A faixa de consumo esperada para a carga normal é {faixa[0]:.0f}–{faixa[1]:.0f} W."
    )
    return {
        "tabela": pd.DataFrame(linhas_tab),
        "temp_tempo": pd.DataFrame(series).rename_axis("t (s)"),
        "faixa_esperada": faixa,
        "conclusao": conclusao,
    }


# ================================================================ EXPERIMENTO 2
def exp2_carga_progressiva(tier: str, cargas=(25, 50, 75, 100), dur: int = DURACAO_S) -> dict:
    linhas_tab = []
    for c in cargas:
        pc = make_computer(tier)
        _, linhas = _run(pc, [{"carga": c, "dur": dur}])
        fim = linhas[-1]
        linhas_tab.append({
            "Carga (%)": c,
            "Corrente CPU (A)": fim["corrente_cpu_a"],
            "Potência (W)": fim["potencia"],
            "Temp. estabilizada (°C)": fim["temp"],
        })
    df = pd.DataFrame(linhas_tab)

    pot, temp = list(df["Potência (W)"]), list(df["Temp. estabilizada (°C)"])
    crescentes = all(pot[i] < pot[i + 1] for i in range(len(pot) - 1)) and \
        all(temp[i] < temp[i + 1] for i in range(len(temp) - 1))
    incrementos = [round(pot[i + 1] - pot[i], 1) for i in range(len(pot) - 1)]

    partes = [
        f"De {cargas[0]}% para {cargas[-1]}% de carga, a potência foi de {pot[0]:.0f} W para {pot[-1]:.0f} W "
        f"e a temperatura estabilizada de {temp[0]:.1f} °C para {temp[-1]:.1f} °C."
    ]
    if crescentes:
        partes.append("Em todos os degraus, mais carga resultou em mais potência e mais temperatura.")
    else:
        partes.append("Atenção: nem todos os degraus mostraram aumento simultâneo de potência e temperatura.")
    if len(incrementos) >= 2:
        txt_inc = ", ".join(f"{x:+.0f} W" for x in incrementos)
        if incrementos[-1] > incrementos[0]:
            partes.append(
                f"O aumento de potência por degrau foi de {txt_inc}: cargas altas custam proporcionalmente mais "
                f"(efeito de boost de clock/tensão do modelo)."
            )
        else:
            partes.append(f"O aumento de potência por degrau foi de {txt_inc}.")

    return {
        "tabela": df,
        "carga_potencia": df.set_index("Carga (%)")[["Potência (W)"]],
        "carga_temp": df.set_index("Carga (%)")[["Temp. estabilizada (°C)"]],
        "conclusao": " ".join(partes),
    }


# ================================================================ EXPERIMENTO 3
def exp3_potencia_x_temperatura(tier: str, cargas=tuple(range(10, 101, 10)), carga_fixa: float = 30,
                                fracoes_extra=(0.0, 0.10, 0.20, 0.30, 0.40), dur: int = DURACAO_S) -> dict:
    pmax = make_computer(tier).max_power_w()
    linhas_tab = []

    for c in cargas:  # Série 1: potência variada pela carga
        pc = make_computer(tier)
        _, linhas = _run(pc, [{"carga": c, "dur": dur}])
        fim = linhas[-1]
        linhas_tab.append({
            "Série": "Variando a carga", "Carga (%)": c, "Processo extra (W)": 0.0,
            "Potência (W)": fim["potencia"], "Temp. estabilizada (°C)": fim["temp"],
        })

    for frac in fracoes_extra:  # Série 2: carga fixa + processo desnecessário
        waste = round(frac * pmax, 1)
        pc = make_computer(tier)
        _, linhas = _run(pc, [{"carga": carga_fixa, "waste_w": waste, "dur": dur}])
        fim = linhas[-1]
        linhas_tab.append({
            "Série": f"Carga fixa {carga_fixa:.0f}% + processo extra", "Carga (%)": carga_fixa,
            "Processo extra (W)": waste,
            "Potência (W)": fim["potencia"], "Temp. estabilizada (°C)": fim["temp"],
        })

    df = pd.DataFrame(linhas_tab)
    inclinacoes = {}
    for serie, g in df.groupby("Série", sort=False):
        inclinacoes[serie] = _inclinacao(list(g["Potência (W)"]), list(g["Temp. estabilizada (°C)"])) * 100

    valores = list(inclinacoes.values())
    por_10w = [v / 10 for v in valores]  # °C por +10 W
    conclusao = (
        f"Nas duas séries, mais potência significou mais temperatura de equilíbrio: cada +10 W elevou a temperatura "
        f"em cerca de {por_10w[0]:.1f} °C (série da carga) e {por_10w[1]:.1f} °C (série do processo extra)."
    )
    if max(abs(v) for v in valores) > 0 and abs(valores[0] - valores[1]) / max(abs(v) for v in valores) < 0.05:
        conclusao += (
            " As duas séries seguem praticamente a mesma reta: a temperatura depende da potência dissipada, "
            "não de qual atividade a produziu."
        )
    return {"tabela": df, "inclinacoes": inclinacoes, "conclusao": conclusao}


# ================================================================ EXPERIMENTO 4
COOLING_CENARIOS = (
    ("A — Refrigeração reduzida", "entrada"),
    ("B — Refrigeração normal", "intermediario"),
    ("C — Refrigeração eficiente", "premium"),
)


def exp4_refrigeracao(tier: str, carga: float = 80, dur: int = DURACAO_S) -> dict:
    linhas_tab, series, potencias, tmax = [], {}, [], {}
    for nome, ctier in COOLING_CENARIOS:
        pc = make_computer(tier, cooling_tier=ctier)
        track, linhas = _run(pc, [{"carga": carga, "dur": dur}], limite_ref=LIMITE_TERMICO_LAB_C)
        fim = linhas[-1]
        perf_medio = _media(linhas, "desempenho")
        temp_max = max(r["temp"] for r in linhas)
        tmax[nome] = temp_max
        potencias.append(fim["potencia"])
        series[nome] = pd.Series({r["t"]: r["temp"] for r in linhas})
        linhas_tab.append({
            "Cenário": nome,
            "Refrigeração": pc.cooling["nome"],
            "τ térmico (s)": pc.cooling["tau"],
            "Potência (W)": fim["potencia"],
            "Temp. máx. (°C)": temp_max,
            "Margem até o limite (°C)": round(LIMITE_TERMICO_LAB_C - temp_max, 1),
            "Desempenho médio (%)": round(perf_medio, 1),
            "Travamentos": fim["travamentos"],
            "Reinicializações": fim["reinicios"],
            "Estabilidade": stress.estabilidade_rating(fim["travamentos"], fim["reinicios"], perf_medio),
        })

    nomes = [n for n, _ in COOLING_CENARIOS]
    pior, melhor = tmax[nomes[0]], tmax[nomes[-1]]
    mesma_pot = max(potencias) - min(potencias) < 0.05
    conclusao = (
        f"{'Com a mesma potência' if mesma_pot else 'Com potências parecidas'} ({potencias[0]:.0f} W), a temperatura "
        f"máxima foi de {tmax[nomes[0]]:.1f} °C (reduzida), {tmax[nomes[1]]:.1f} °C (normal) e "
        f"{tmax[nomes[2]]:.1f} °C (eficiente) — uma diferença de {pior - melhor:.1f} °C só por causa da capacidade de "
        f"dissipar calor. Contra um limite térmico de {LIMITE_TERMICO_LAB_C:.0f} °C, as margens foram de "
        f"{LIMITE_TERMICO_LAB_C - tmax[nomes[0]]:+.1f}, {LIMITE_TERMICO_LAB_C - tmax[nomes[1]]:+.1f} e "
        f"{LIMITE_TERMICO_LAB_C - tmax[nomes[2]]:+.1f} °C."
    )
    return {
        "tabela": pd.DataFrame(linhas_tab),
        "temp_tempo": pd.DataFrame(series).rename_axis("t (s)"),
        "conclusao": conclusao,
    }


# ================================================================ EXPERIMENTO 5
MARCOS_S = (0, 10, 20, 30, 60, 120, 300, 600)


def exp5_tempo_x_temperatura(tier: str, carga: float = 80, dur: int = DURACAO_S) -> dict:
    pc = make_computer(tier)
    ref = pc.cooling["temp_max_ref"]
    _, linhas = _run(pc, [{"carga": carga, "dur": dur}])
    todas = [_linha_inicial(pc, carga)] + linhas
    por_t = {r["t"]: r for r in todas}

    tab, anterior = [], None
    for m in (x for x in MARCOS_S if x <= dur):
        r = por_t[float(m)]
        tab.append({
            "Tempo (s)": m,
            "Potência (W)": r["potencia"],
            "Temperatura (°C)": r["temp"],
            "Variação desde o marco anterior (°C)": None if anterior is None else round(r["temp"] - anterior, 1),
        })
        anterior = r["temp"]
    df = pd.DataFrame(tab)

    t0, tf = todas[0]["temp"], todas[-1]["temp"]
    alvo = thermal.target_temperature(todas[-1]["potencia"], pc.max_power_w(), ref)
    t63 = _t63(linhas, 0.0, t0, tf)
    janela = 60 if dur >= 120 else max(DT_S, dur // 2)
    var_final = todas[-1]["temp"] - por_t[float(dur - janela)]["temp"]
    estabilizou = abs(var_final) < 0.3
    ganho_30 = por_t[30.0]["temp"] - t0 if dur >= 30 else None

    partes = [f"Com carga de {carga:.0f}% (potência {todas[-1]['potencia']:.0f} W), a temperatura subiu de {t0:.1f} °C para {tf:.1f} °C."]
    if ganho_30 is not None:
        partes.append(f"Só nos primeiros 30 s ela subiu {ganho_30:.1f} °C ({ganho_30 / (tf - t0) * 100:.0f}% da subida total).")
    partes.append(
        f"Nos últimos {janela} s a variação foi de apenas {var_final:+.1f} °C — o sistema "
        + (f"estabilizou perto de {alvo:.1f} °C (equilíbrio térmico)." if estabilizou else "ainda estava aquecendo.")
    )
    if t63 is not None:
        partes.append(f"O tempo para percorrer 63% da subida foi de ~{t63:.0f} s (constante de tempo do modelo: τ = {pc.cooling['tau']} s).")

    serie = pd.DataFrame({"Temperatura (°C)": {r["t"]: r["temp"] for r in todas}}).rename_axis("t (s)")
    return {"tabela": df, "temp_tempo": serie, "temp_equilibrio": alvo, "t63": t63, "conclusao": " ".join(partes)}


# ================================================================ EXPERIMENTO 6
def exp6_sobrecarga(tier: str, carga_normal: float = 25, carga_sobrecarga: float = 100,
                    t_normal: int = 120, t_sobrecarga: int = 480) -> dict:
    pc = make_computer(tier)
    ref = pc.cooling["temp_max_ref"]
    _, linhas = _run(pc, [
        {"carga": carga_normal, "dur": t_normal},
        {"carga": carga_sobrecarga, "dur": t_sobrecarga},
    ])
    seg0 = [r for r in linhas if r["segmento"] == 0]
    seg1 = [r for r in linhas if r["segmento"] == 1]
    antes, depois = seg0[-1], seg1[-1]

    lo, hi = max(0, carga_normal - 5), min(100, carga_normal + 5)
    faixa = energy.expected_power_range(pc, (lo, hi), (lo, hi))
    anom = reco.detect_anomaly(depois["potencia"], faixa)
    limite_alerta = round(faixa[1] * 1.15, 1)

    t_aviso = _tempo_ate(seg1, lambda r: r["temp"] >= FRACAO_AVISO * ref, t0=t_normal)
    t_instavel = _tempo_ate(seg1, lambda r: r["temp"] >= FRACAO_INSTAVEL * ref, t0=t_normal)
    t_trava = _tempo_ate(seg1, lambda r: r["travamentos"] > antes["travamentos"], t0=t_normal)
    perf_min = min(r["desempenho"] for r in seg1)
    fps_min = min(r["fps"] for r in seg1)
    temp_max = max(r["temp"] for r in linhas)

    marcos = [
        ("Potência antes → depois da sobrecarga", f"{antes['potencia']:.0f} W → {depois['potencia']:.0f} W"),
        ("Corrente estimada da CPU antes → depois", f"{antes['corrente_cpu_a']} A → {depois['corrente_cpu_a']} A"),
        ("Temperatura no instante da sobrecarga → máxima", f"{antes['temp']:.1f} °C → {temp_max:.1f} °C"),
        ("Alerta de consumo anormal", (
            f"⚠️ disparou (potência {depois['potencia']:.0f} W > limite {limite_alerta:.0f} W)" if anom["anomalo"]
            else f"não disparou (potência {depois['potencia']:.0f} W ≤ limite {limite_alerta:.0f} W)"
        )),
        (f"Tempo até o aviso térmico ({FRACAO_AVISO * 100:.0f}% da temp. de referência = {FRACAO_AVISO * ref:.0f} °C)", _fmt_seg(t_aviso)),
        (f"Tempo até a instabilidade ({FRACAO_INSTAVEL * 100:.0f}% = {FRACAO_INSTAVEL * ref:.0f} °C)", _fmt_seg(t_instavel)),
        ("Tempo até o 1º travamento", _fmt_seg(t_trava)),
        ("Desempenho mínimo / FPS mínimo (educativo)", f"{perf_min:.0f}% / {fps_min:.0f}"),
    ]
    df = pd.DataFrame(marcos, columns=["Marco", "Resultado"])

    conclusao = (
        f"Em operação normal ({carga_normal:.0f}%) o sistema estava a {antes['potencia']:.0f} W e {antes['temp']:.1f} °C. "
        f"Ao subir a carga para {carga_sobrecarga:.0f}%, a potência foi para {depois['potencia']:.0f} W "
        f"({(depois['potencia'] / antes['potencia'] - 1) * 100:+.0f}%) e a temperatura chegou a {temp_max:.1f} °C; "
        f"o aviso térmico veio após {_fmt_seg(t_aviso)} e o desempenho caiu para {perf_min:.0f}%."
    )
    serie = pd.DataFrame(
        {"Temperatura (°C)": {r["t"]: r["temp"] for r in linhas},
         "Desempenho (%)": {r["t"]: r["desempenho"] for r in linhas},
         "Potência (W)": {r["t"]: r["potencia"] for r in linhas}}
    ).rename_axis("t (s)")
    return {"tabela": df, "series": serie, "t_sobrecarga_s": t_normal, "faixa_esperada": faixa,
            "limite_alerta_w": limite_alerta, "conclusao": conclusao}


# ================================================================ EXPERIMENTO 7
def exp7_variacao_brusca(tier: str, baixa: float = 25, alta: float = 100,
                         t_baixa: int = 120, t_alta: int = 240, t_volta: int = 240) -> dict:
    pc = make_computer(tier)
    _, linhas = _run(pc, [
        {"carga": baixa, "dur": t_baixa},
        {"carga": alta, "dur": t_alta},
        {"carga": baixa, "dur": t_volta},
    ])
    fim_seg = [[r for r in linhas if r["segmento"] == i][-1] for i in range(3)]
    fases = ["1 · Carga baixa", "2 · Carga alta", "3 · Volta à carga baixa"]
    df = pd.DataFrame([{
        "Fase": fases[i], "Carga (%)": fim_seg[i]["carga"],
        "Potência (W)": fim_seg[i]["potencia"], "Temp. no fim da fase (°C)": fim_seg[i]["temp"],
    } for i in range(3)])

    # resposta ao degrau de subida
    t_step = float(t_baixa)
    temp_antes, temp_pico, temp_fim = fim_seg[0]["temp"], fim_seg[1]["temp"], fim_seg[2]["temp"]
    primeiro = next(r for r in linhas if r["t"] > t_step)
    frac_1passo = (primeiro["temp"] - temp_antes) / (temp_pico - temp_antes) * 100 if temp_pico != temp_antes else 0.0
    pot_imediata = abs(primeiro["potencia"] - fim_seg[1]["potencia"]) < 0.05

    t63_subida = _t63([r for r in linhas if r["segmento"] == 1], t_step, temp_antes, temp_pico)
    t63_descida = _t63([r for r in linhas if r["segmento"] == 2], t_step + t_alta, temp_pico, temp_fim)

    txt = (
        f"Na subida ({baixa:.0f}% → {alta:.0f}%), a potência foi de {fim_seg[0]['potencia']:.0f} W para "
        f"{fim_seg[1]['potencia']:.0f} W"
    )
    if pot_imediata:
        txt += f" já no primeiro passo de {DT_S} s, enquanto a temperatura percorreu apenas {frac_1passo:.0f}% da sua variação total."
    else:
        txt += " em poucos passos."
    if t63_subida is not None:
        txt += f" A temperatura levou ~{t63_subida:.0f} s para percorrer 63% da subida"
        if t63_descida is not None:
            txt += f" e ~{t63_descida:.0f} s para percorrer 63% da descida quando a carga voltou ao normal."
        else:
            txt += "."
    txt += " A resposta elétrica é quase imediata; a térmica é gradual."
    partes = [txt]

    serie = pd.DataFrame(
        {"Carga (%)": {r["t"]: r["carga"] for r in linhas},
         "Potência (W)": {r["t"]: r["potencia"] for r in linhas},
         "Temperatura (°C)": {r["t"]: r["temp"] for r in linhas}}
    ).rename_axis("t (s)")
    return {"tabela": df, "series": serie, "t63_subida": t63_subida, "t63_descida": t63_descida,
            "conclusao": " ".join(partes)}


# ================================================================ EXPERIMENTO 8
CENARIOS_USO = (
    ("A — Uso leve", 20, None),
    ("B — Uso moderado", 50, None),
    ("C — Uso intenso", 90, None),
    ("D — Uso intenso + baixa dissipação", 90, "entrada"),
)


def exp8_comparativo(tier: str, dur: int = DURACAO_S) -> dict:
    limite = make_computer(tier).cooling["temp_max_ref"]  # limite do componente = ref. do PC escolhido
    linhas_tab, situacoes = [], {}
    for nome, carga, cooling_tier in CENARIOS_USO:
        pc = make_computer(tier, cooling_tier=cooling_tier)
        track, linhas = _run(pc, [{"carga": carga, "dur": dur}], limite_ref=limite)
        fim = linhas[-1]
        temp_max = max(r["temp"] for r in linhas)
        sit = _situacao(temp_max, limite, fim["reinicios"])
        situacoes[nome] = sit
        linhas_tab.append({
            "Cenário": nome,
            "Carga (%)": carga,
            "Potência (W)": fim["potencia"],
            "Energia em 10 min (Wh)": round(track.kwh * 1000, 1),
            "Temp. máx. (°C)": temp_max,
            "Desempenho médio (%)": round(_media(linhas, "desempenho"), 1),
            "Travamentos": fim["travamentos"],
            "Reinicializações": fim["reinicios"],
            "Situação": sit,
        })
    df = pd.DataFrame(linhas_tab)

    ordem = {"🟢 Normal": 0, "🟠 Atenção": 1, "🔴 Crítico": 2}
    chave = lambda r: (ordem[r["Situação"]], r["Temp. máx. (°C)"])
    melhor_chave = max(chave(r) for r in linhas_tab)
    criticos = [r for r in linhas_tab if chave(r) == melhor_chave]
    nomes = " e ".join(f"«{r['Cenário']}»" for r in criticos)
    r0 = criticos[0]
    conclusao = (
        f"{'Os cenários mais críticos foram' if len(criticos) > 1 else 'O cenário mais crítico foi'} {nomes}, com "
        f"temperatura máxima de {r0['Temp. máx. (°C)']:.1f} °C ({r0['Temp. máx. (°C)'] / limite * 100:.1f}% do limite de "
        f"{limite:.0f} °C), classificado como «{r0['Situação'].split(' ', 1)[1]}». "
        f"Critério: Normal abaixo de {FRACAO_NORMAL_MAX * 100:.0f}% do limite; Atenção de {FRACAO_NORMAL_MAX * 100:.0f}% a "
        f"{FRACAO_INSTAVEL * 100:.0f}%; Crítico a partir de {FRACAO_INSTAVEL * 100:.0f}% (ou com reinicializações)."
    )
    if make_computer(tier).cooling == dict(COOLING["entrada"]):
        conclusao += " No PC de Entrada a refrigeração já é a mais básica, então C e D coincidem; escolha outro PC para ver o efeito da baixa dissipação."
    return {"tabela": df, "limite_c": limite, "conclusao": conclusao}
