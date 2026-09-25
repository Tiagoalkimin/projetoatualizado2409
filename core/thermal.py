"""Simulação térmica: a temperatura sobe/desce gradualmente até um alvo,
nunca instantaneamente — aproximando o comportamento real de um PC."""

import math

AMBIENTE_C = 24.0


def target_temperature(power_w: float, max_power_w: float, temp_max_ref: float) -> float:
    """Temperatura de equilíbrio para a potência atual (0-100% do máximo)."""
    carga = max(0.0, min(1.0, power_w / max_power_w))
    return AMBIENTE_C + carga * (temp_max_ref - AMBIENTE_C)


def update_temperature(current_temp: float, target_temp: float, dt_seconds: float, tau: float) -> float:
    """Aproximação exponencial (1ª ordem) em direção à temperatura-alvo.

    tau (segundos) é a constante de tempo térmica: quanto menor, mais rápido
    o sistema reage (refrigeração melhor = tau menor).
    """
    if tau <= 0:
        return target_temp
    fator = 1 - math.exp(-dt_seconds / tau)
    return current_temp + (target_temp - current_temp) * fator
