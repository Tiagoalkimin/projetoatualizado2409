# -*- coding: utf-8 -*-
"""Mecânicas de ESTRESSE PROLONGADO, desempenho, throttling térmico e
(in)estabilidade do sistema.

IMPORTANTE (fins didáticos):
As fórmulas e limiares aqui são SIMPLIFICAÇÕES EDUCATIVAS para tornar visíveis,
de forma intuitiva, conceitos reais de Física/Engenharia — como redução
automática de desempenho por superaquecimento (thermal throttling) e a
diferença entre um pico rápido de carga e um uso intenso prolongado. Não são
medições de hardware real e não devem ser interpretadas como tal.
"""

import random

# Fração da potência máxima do PC acima da qual consideramos que ele está
# "sob estresse" (carga alta sustentada).
LIMIAR_CARGA_ALTA = 0.55

# Faixa de clock ILUSTRATIVA (não representa um processador real).
CLOCK_BASE_GHZ = 3.6
CLOCK_BOOST_GHZ = 5.0


def carga_fracao(power_total_w: float, max_power_w: float) -> float:
    """Fração (0–1) da potência máxima que o sistema está consumindo agora."""
    if max_power_w <= 0:
        return 0.0
    return max(0.0, min(1.0, power_total_w / max_power_w))


def update_stress_time(stress_s: float, carga: float, dt: float) -> float:
    """Acumula 'tempo sob estresse' enquanto a carga está alta; quando a carga
    cai, o contador recua lentamente (o sistema "esfria" da fadiga de uso
    contínuo). Isso é o que diferencia um pico rápido de um uso prolongado."""
    if carga >= LIMIAR_CARGA_ALTA:
        return stress_s + dt
    return max(0.0, stress_s - dt * 0.5)


def clock_ghz_ilustrativo(temp: float, temp_max_ref: float, carga: float) -> float:
    """Frequência de clock MERAMENTE ILUSTRATIVA.

    Serve só para mostrar, de forma simplificada, que o computador pode reduzir
    a frequência de operação quando está muito quente (thermal throttling).
    O quartzo NÃO é o responsável por essa variação — ele fornece apenas uma
    referência de tempo estável para os circuitos (ver tela sobre o quartzo).
    """
    alvo = CLOCK_BASE_GHZ + (CLOCK_BOOST_GHZ - CLOCK_BASE_GHZ) * carga
    limiar = temp_max_ref * 0.85
    if temp > limiar:
        excesso = min(1.0, (temp - limiar) / (temp_max_ref * 0.20 + 1e-6))
        alvo *= (1 - 0.35 * excesso)
    return round(alvo, 2)


def compute_performance_pct(temp: float, temp_max_ref: float, stress_s: float) -> float:
    """Desempenho entregue (%), considerando:
    1) throttling térmico (perde desempenho ao passar de ~75% da temp. de referência);
    2) tempo prolongado sob carga alta (fadiga de uso contínuo).
    """
    perf = 100.0

    limiar_quente = temp_max_ref * 0.75
    if temp > limiar_quente:
        excesso = min(1.0, (temp - limiar_quente) / (temp_max_ref * 0.30 + 1e-6))
        perf -= 45.0 * excesso

    minutos_estresse = stress_s / 60.0
    perf -= min(25.0, minutos_estresse * 2.5)

    return round(max(15.0, perf), 1)


def fps_educativo(performance_pct: float, fps_base: float) -> float:
    """Indicador de desempenho em 'FPS equivalente' — ILUSTRATIVO, não é
    medição de um jogo real. Ajuda a visualizar a perda de desempenho."""
    return round(fps_base * performance_pct / 100.0, 0)


def check_thermal_event(temp: float, temp_max_ref: float, rng=None) -> dict:
    """Sorteia eventos de instabilidade conforme a temperatura ultrapassa
    limiares crescentes. Retorna flags e uma mensagem para exibição na UI."""
    rng = rng or random

    aviso_temp = temp_max_ref * 0.85
    instavel_temp = temp_max_ref * 0.95
    critico_temp = temp_max_ref * 1.02

    evento = {
        "nivel": "normal",
        "travou": False,
        "reiniciou": False,
        "mensagem": None,
    }

    if temp >= critico_temp:
        evento["nivel"] = "critico"
        if rng.random() < 0.35:
            evento["reiniciou"] = True
            evento["mensagem"] = (
                "🔵 TELA AZUL / REINICIALIZAÇÃO — o sistema reiniciou para se proteger "
                "do superaquecimento."
            )
    elif temp >= instavel_temp:
        evento["nivel"] = "instavel"
        if rng.random() < 0.20:
            evento["travou"] = True
            evento["mensagem"] = "🔴 COMPUTADOR INSTÁVEL — o sistema travou momentaneamente."
    elif temp >= aviso_temp:
        evento["nivel"] = "aviso"
        evento["mensagem"] = (
            "⚠️ COMPUTADOR MUITO QUENTE — desempenho reduzido automaticamente "
            "(redução automática de desempenho / thermal throttling) para evitar danos."
        )

    return evento


def estabilidade_rating(lockups: int, restarts: int, performance_medio: float) -> str:
    """Classificação simples de estabilidade a partir dos eventos observados."""
    if restarts == 0 and lockups == 0 and performance_medio >= 85:
        return "ALTA"
    if restarts <= 1 and lockups <= 3 and performance_medio >= 60:
        return "MÉDIA"
    return "BAIXA"


def temp_badge(temp: float, temp_max_ref: float) -> dict:
    """Indicador visual (verde/amarelo/laranja/vermelho) do estado térmico."""
    frac = temp / temp_max_ref if temp_max_ref else 0.0
    if frac < 0.55:
        return {"emoji": "🟢", "label": "Frio"}
    if frac < 0.75:
        return {"emoji": "🟡", "label": "Aquecendo"}
    if frac < 0.92:
        return {"emoji": "🟠", "label": "Quente"}
    return {"emoji": "🔴", "label": "Muito quente"}


def fmt_mmss(seconds: float) -> str:
    """Formata segundos como MM:SS para o indicador 'Tempo sob estresse'."""
    total = max(0, int(seconds))
    m, s = divmod(total, 60)
    return f"{m:02d}:{s:02d}"
