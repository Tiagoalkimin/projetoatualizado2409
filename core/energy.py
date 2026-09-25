"""Cálculos de potência, energia acumulada (kWh) e custo financeiro."""


def compute_power(computer, cpu_util: float, gpu_util: float, waste_w: float = 0.0) -> dict:
    """Retorna a decomposição de potência (W) do sistema completo."""
    cpu_w = computer.cpu.power_w(cpu_util)
    gpu_w = computer.gpu.power_w(gpu_util)
    extras_w = computer.extras_w
    total_w = cpu_w + gpu_w + extras_w + waste_w
    return {
        "cpu_w": cpu_w,
        "gpu_w": gpu_w,
        "extras_w": extras_w,
        "waste_w": round(waste_w, 1),
        "total_w": round(total_w, 1),
    }


def energy_kwh(power_w: float, dt_seconds: float) -> float:
    """Energia (kWh) consumida em um intervalo dt (segundos) a uma potência dada."""
    horas = dt_seconds / 3600.0
    return (power_w / 1000.0) * horas


def cost_from_kwh(kwh: float, tarifa_reais_kwh: float) -> float:
    return kwh * tarifa_reais_kwh


def cost_projection(avg_power_w: float, tarifa_reais_kwh: float) -> dict:
    """Projeta o custo para 1h, 8h e 30 dias mantendo a potência média atual."""
    def custo_para(horas):
        kwh = (avg_power_w / 1000.0) * horas
        return round(cost_from_kwh(kwh, tarifa_reais_kwh), 2), round(kwh, 3)

    custo_1h, kwh_1h = custo_para(1)
    custo_8h, kwh_8h = custo_para(8)
    custo_30d, kwh_30d = custo_para(8 * 30)  # 8h/dia por 30 dias

    return {
        "1h": {"kwh": kwh_1h, "custo": custo_1h},
        "8h": {"kwh": kwh_8h, "custo": custo_8h},
        "30d": {"kwh": kwh_30d, "custo": custo_30d},
    }


def expected_power_range(computer, cpu_range, gpu_range) -> tuple:
    """Faixa de consumo esperado (W) para uma tarefa, usada na detecção de anomalias."""
    low = compute_power(computer, cpu_range[0], gpu_range[0])["total_w"]
    high = compute_power(computer, cpu_range[1], gpu_range[1])["total_w"]
    return round(low, 1), round(high, 1)
