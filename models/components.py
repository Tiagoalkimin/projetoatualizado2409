"""Demais componentes: placa-mãe, RAM, SSD, ventoinhas e refrigeração."""

EXTRA_COMPONENTS = {
    "entrada": {
        "base_sistema_w": 18,   # placa-mãe + fontes + perdas
        "ram_w": 4,
        "ssd_w": 2,
        "fans_w": 3,
    },
    "intermediario": {
        "base_sistema_w": 25,
        "ram_w": 6,
        "ssd_w": 3,
        "fans_w": 6,
    },
    "premium": {
        "base_sistema_w": 35,
        "ram_w": 10,
        "ssd_w": 5,
        "fans_w": 12,
    },
}

# Capacidade de refrigeração: quanto maior, mais rápido estabiliza e menor o
# teto de temperatura em carga máxima.
COOLING = {
    "entrada": {"nome": "Refrigeração Básica (cooler stock)", "tau": 55, "temp_max_ref": 92},
    "intermediario": {"nome": "Refrigeração Intermediária (air cooler)", "tau": 40, "temp_max_ref": 84},
    "premium": {"nome": "Refrigeração Robusta (water cooler)", "tau": 28, "temp_max_ref": 75},
}


def extras_power_w(tier: str) -> float:
    e = EXTRA_COMPONENTS[tier]
    return e["base_sistema_w"] + e["ram_w"] + e["ssd_w"] + e["fans_w"]


def cooling_profile(tier: str) -> dict:
    return COOLING[tier]
