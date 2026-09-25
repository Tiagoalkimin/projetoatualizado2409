"""Modelo de CPU: perfis de consumo, tensão e comportamento sob carga."""

CPU_PROFILES = {
    "entrada": {
        "nome": "CPU de Entrada (4 núcleos)",
        "idle_w": 6,
        "max_w": 45,
        "v_idle": 0.85,
        "v_boost": 1.25,
    },
    "intermediario": {
        "nome": "CPU Intermediária (6-8 núcleos)",
        "idle_w": 9,
        "max_w": 95,
        "v_idle": 0.95,
        "v_boost": 1.35,
    },
    "premium": {
        "nome": "CPU de Alto Desempenho (12+ núcleos)",
        "idle_w": 14,
        "max_w": 170,
        "v_idle": 1.00,
        "v_boost": 1.50,
    },
}


class CPU:
    """Representa a CPU do computador simulado."""

    def __init__(self, tier: str):
        if tier not in CPU_PROFILES:
            raise ValueError(f"Tier de CPU inválido: {tier}")
        self.tier = tier
        self.profile = CPU_PROFILES[tier]
        self.nome = self.profile["nome"]

    def power_w(self, util_percent: float) -> float:
        """Potência (W) consumida pela CPU para um dado percentual de uso."""
        util = max(0.0, min(100.0, util_percent)) / 100.0
        # Curva levemente não-linear: cargas altas custam proporcionalmente mais
        # (boost de clock e tensão), representando o comportamento real de CPUs.
        curva = util ** 1.15
        idle = self.profile["idle_w"]
        maxw = self.profile["max_w"]
        return round(idle + (maxw - idle) * curva, 1)

    def voltage_v(self, util_percent: float) -> float:
        """Tensão efetiva (V) simplificada — regulada pelo VRM conforme a carga."""
        util = max(0.0, min(100.0, util_percent)) / 100.0
        v_idle = self.profile["v_idle"]
        v_boost = self.profile["v_boost"]
        return round(v_idle + (v_boost - v_idle) * util, 3)

    def max_w(self) -> float:
        return self.profile["max_w"]
