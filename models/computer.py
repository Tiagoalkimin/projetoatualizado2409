"""Classe Computer: agrega CPU, GPU, componentes e refrigeração de um PC."""

from .cpu import CPU
from .gpu import GPU
from . import components as comp

COMPUTER_PRESETS = {
    "entrada": {
        "nome": "PC de Entrada",
        "descricao": "CPU básica + GPU integrada + refrigeração simples.",
        "cpu_tier": "entrada",
        "gpu_tier": "integrada",
        "fps_base": 70,
        "aletas_dissipador": 2,
        "area_dissipador_rel": 1.0,
        "fluxo_ar": "fraco",
    },
    "intermediario": {
        "nome": "PC Intermediário",
        "descricao": "CPU intermediária + GPU dedicada intermediária.",
        "cpu_tier": "intermediario",
        "gpu_tier": "dedicada_intermediaria",
        "fps_base": 100,
        "aletas_dissipador": 5,
        "area_dissipador_rel": 1.6,
        "fluxo_ar": "moderado",
    },
    "premium": {
        "nome": "PC Premium",
        "descricao": "CPU de alto desempenho + GPU dedicada de ponta.",
        "cpu_tier": "premium",
        "gpu_tier": "dedicada_alta",
        "fps_base": 140,
        "aletas_dissipador": 9,
        "area_dissipador_rel": 2.4,
        "fluxo_ar": "forte",
    },
}


class Computer:
    def __init__(self, preset_key: str):
        if preset_key not in COMPUTER_PRESETS:
            raise ValueError(f"Preset de computador inválido: {preset_key}")
        preset = COMPUTER_PRESETS[preset_key]
        self.preset_key = preset_key
        self.nome = preset["nome"]
        self.descricao = preset["descricao"]
        self.cpu = CPU(preset["cpu_tier"])
        self.gpu = GPU(preset["gpu_tier"])
        self.extras_w = comp.extras_power_w(preset_key)
        self.cooling = comp.cooling_profile(preset_key)

        # Usados pelas mecânicas educativas de desempenho/geometria (não são
        # medições reais — servem para tornar os conceitos visíveis).
        self.fps_base = preset.get("fps_base", 90)
        self.aletas_dissipador = preset.get("aletas_dissipador", 3)
        self.area_dissipador_rel = preset.get("area_dissipador_rel", 1.0)
        self.fluxo_ar = preset.get("fluxo_ar", "moderado")

    def max_power_w(self) -> float:
        return self.cpu.max_w() + self.gpu.max_w() + self.extras_w
