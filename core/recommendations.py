"""Geração de recomendações e detecção de consumo anormal."""

MODOS = {
    "economia": {"nome": "Economia", "fator_util": 0.65, "fator_temp_alvo": 0.9},
    "equilibrado": {"nome": "Equilibrado", "fator_util": 0.85, "fator_temp_alvo": 1.0},
    "desempenho": {"nome": "Desempenho", "fator_util": 1.0, "fator_temp_alvo": 1.08},
    # Usado só pelo Laboratório de Experimentos: a carga pedida é aplicada
    # exatamente como definida (sem fator de modo) para que os resultados
    # sejam comparáveis e reproduzíveis.
    "laboratorio": {"nome": "Laboratório (controlado)", "fator_util": 1.0, "fator_temp_alvo": 1.0},
}


def detect_anomaly(power_atual_w: float, faixa_esperada: tuple, margem: float = 1.15) -> dict:
    low, high = faixa_esperada
    limite = high * margem
    anomalo = power_atual_w > limite
    return {
        "anomalo": anomalo,
        "esperado_min": low,
        "esperado_max": high,
        "atual": power_atual_w,
    }


def recommend(state: dict) -> list:
    """Gera recomendações textuais curtas a partir do estado atual da simulação."""
    dicas = []

    if state["temp"] >= state["temp_max_ref"] * 0.92:
        dicas.append("🌡️ Temperatura próxima do limite — considere melhorar a refrigeração "
                      "ou reduzir a carga por alguns minutos.")

    if state["anomaly"]["anomalo"]:
        dicas.append(f"⚠️ Consumo acima do esperado para esta tarefa "
                      f"({state['anomaly']['atual']} W vs. {state['anomaly']['esperado_min']}–"
                      f"{state['anomaly']['esperado_max']} W). Verifique processos em segundo plano.")

    if state["gpu_util"] > 70 and state["cpu_util"] < 30:
        dicas.append("🎮 GPU muito exigida enquanto a CPU está ociosa — normal em jogos/renderização, "
                      "mas confira se não há uso desnecessário em segundo plano.")

    if state["modo"] == "desempenho" and state["cpu_util"] < 40 and state["gpu_util"] < 40:
        dicas.append("⚡ Modo Desempenho ativo com carga baixa — mudar para Equilibrado economizaria "
                      "energia sem perda perceptível.")

    if not dicas:
        dicas.append("✅ Consumo dentro do esperado para a tarefa atual. Nenhuma ação necessária.")

    return dicas
