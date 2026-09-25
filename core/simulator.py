"""Simulator: orquestra o avanço do tempo, consumo, temperatura e decisões.

Mantém DUAS trilhas em paralelo:
- "real": o que de fato acontece, considerando as decisões do usuário.
- "baseline": o que aconteceria se nenhuma decisão de otimização fosse tomada.

A diferença entre as duas ao final é a "economia obtida pelas decisões do
usuário", exigida no relatório final.
"""

import random

from . import energy, thermal, recommendations as reco, stress
from models.computer import Computer


class Track:
    """Uma trilha de simulação (real ou baseline)."""

    def __init__(self, computer):
        self.computer = computer
        self.temp = thermal.AMBIENTE_C + 5
        self.kwh = 0.0
        self.elapsed_s = 0.0
        self.history = []  # lista de dicts: t, power, temp, cpu, gpu, ...
        self.modo = "equilibrado"
        self.waste_w = 0.0  # consumo "desperdiçado" por processos desnecessários

        # ---- Estresse prolongado / desempenho / (in)estabilidade ----------
        self.stress_s = 0.0          # tempo acumulado sob carga alta
        self.performance_pct = 100.0
        self.fps = self.computer.fps_base
        self.clock_ghz = stress.CLOCK_BASE_GHZ
        self.lockups = 0             # travamentos
        self.restarts = 0            # reinicializações ("tela azul")
        self.last_event = None       # última mensagem de evento térmico

        # Limite térmico FIXO do componente (opcional). Por padrão é None e o
        # simulador usa a temperatura de referência da própria refrigeração,
        # como sempre. O Laboratório de Experimentos usa este campo para
        # comparar refrigerações diferentes contra o MESMO limite do componente.
        self.temp_limite_ref = None

    def tick(self, cpu_range, gpu_range, dt_seconds):
        fator = reco.MODOS[self.modo]["fator_util"]
        # pequena variação aleatória para parecer um sistema real
        cpu_util = min(100, (random.uniform(*cpu_range)) * fator)
        gpu_util = min(100, (random.uniform(*gpu_range)) * fator)

        power = energy.compute_power(self.computer, cpu_util, gpu_util, self.waste_w)
        temp_max_ref = self.computer.cooling["temp_max_ref"]
        target = thermal.target_temperature(
            power["total_w"], self.computer.max_power_w(), temp_max_ref
        ) * reco.MODOS[self.modo]["fator_temp_alvo"]
        self.temp = thermal.update_temperature(self.temp, target, dt_seconds, self.computer.cooling["tau"])
        self.kwh += energy.energy_kwh(power["total_w"], dt_seconds)
        self.elapsed_s += dt_seconds

        # ---- estresse prolongado, desempenho e clock ilustrativo ----------
        ref_estado = self.temp_limite_ref or temp_max_ref
        carga = stress.carga_fracao(power["total_w"], self.computer.max_power_w())
        self.stress_s = stress.update_stress_time(self.stress_s, carga, dt_seconds)
        self.performance_pct = stress.compute_performance_pct(self.temp, ref_estado, self.stress_s)
        self.fps = stress.fps_educativo(self.performance_pct, self.computer.fps_base)
        self.clock_ghz = stress.clock_ghz_ilustrativo(self.temp, ref_estado, carga)

        evento = stress.check_thermal_event(self.temp, ref_estado)
        if evento["travou"]:
            self.lockups += 1
        if evento["reiniciou"]:
            self.restarts += 1
            # reinicialização: temperatura despenca, estresse zera
            self.temp = thermal.AMBIENTE_C + 8
            self.stress_s = 0.0
        self.last_event = evento["mensagem"]

        self.history.append({
            "t": self.elapsed_s,
            "power": power["total_w"],
            "power_detail": power,
            "temp": round(self.temp, 1),
            "cpu": round(cpu_util, 1),
            "gpu": round(gpu_util, 1),
            "stress_s": round(self.stress_s, 1),
            "performance_pct": self.performance_pct,
            "fps": self.fps,
            "clock_ghz": self.clock_ghz,
            "lockups": self.lockups,
            "restarts": self.restarts,
        })
        return {
            "power": power, "cpu_util": cpu_util, "gpu_util": gpu_util,
            "temp": self.temp, "evento": evento,
        }


class Simulator:
    def __init__(self, computer, categoria: str, tarefa: str, task_ranges: dict, tarifa_kwh: float = 0.90):
        self.computer = computer
        self.categoria = categoria
        self.tarefa = tarefa
        self.cpu_range = task_ranges["cpu"]
        self.gpu_range = task_ranges["gpu"]
        self.tarifa_kwh = tarifa_kwh

        self.real = Track(computer)
        self.baseline = Track(computer)

        self.decisoes_aplicadas = []  # log de decisões para o relatório
        self.temp_max_atingida = self.real.temp
        self.power_max_atingida = 0.0

    def advance(self, seconds: int, passo: int = 1):
        """Avança a simulação em `seconds`, em passos de `passo` segundos."""
        restante = seconds
        while restante > 0:
            dt = min(passo, restante)
            r = self.real.tick(self.cpu_range, self.gpu_range, dt)
            self.baseline.tick(self.cpu_range, self.gpu_range, dt)  # sempre "equilibrado", sem decisões
            self.temp_max_atingida = max(self.temp_max_atingida, r["temp"])
            self.power_max_atingida = max(self.power_max_atingida, r["power"]["total_w"])
            restante -= dt

    def snapshot(self) -> dict:
        if not self.real.history:
            return None
        last = self.real.history[-1]
        faixa = energy.expected_power_range(self.computer, self.cpu_range, self.gpu_range)
        anomaly = reco.detect_anomaly(last["power"], faixa)
        return {
            "cpu_util": last["cpu"],
            "gpu_util": last["gpu"],
            "power": last["power_detail"],
            "temp": last["temp"],
            "temp_max_ref": self.computer.cooling["temp_max_ref"],
            "kwh": round(self.real.kwh, 4),
            "elapsed_s": self.real.elapsed_s,
            "modo": self.real.modo,
            "anomaly": anomaly,
            "stress_s": self.real.stress_s,
            "performance_pct": self.real.performance_pct,
            "fps": self.real.fps,
            "clock_ghz": self.real.clock_ghz,
            "lockups": self.real.lockups,
            "restarts": self.real.restarts,
            "last_event": self.real.last_event,
        }

    def apply_decision(self, decisao: str) -> dict:
        """Aplica uma decisão do usuário e retorna o snapshot antes/depois."""
        antes = self.snapshot()

        if decisao == "modo_economia":
            self.real.modo = "economia"
        elif decisao == "modo_equilibrado":
            self.real.modo = "equilibrado"
        elif decisao == "modo_desempenho":
            self.real.modo = "desempenho"
        elif decisao == "verificar_processos":
            self.real.waste_w = 0.0
        elif decisao == "reduzir_gpu":
            self.gpu_range = (self.gpu_range[0] * 0.6, self.gpu_range[1] * 0.6)
        elif decisao == "nada":
            pass

        # avança um pequeno intervalo para refletir o efeito da decisão
        self.advance(20, passo=2)
        depois = self.snapshot()

        registro = {"decisao": decisao, "antes": antes, "depois": depois}
        self.decisoes_aplicadas.append(registro)
        return registro

    def inject_waste(self, waste_w: float):
        """Simula processos em segundo plano desperdiçando energia (para o desafio)."""
        self.real.waste_w = waste_w

    def recommendations(self) -> list:
        snap = self.snapshot()
        return reco.recommend(snap)

    def economia_percentual(self) -> float:
        if self.baseline.kwh <= 0:
            return 0.0
        diff = self.baseline.kwh - self.real.kwh
        return round(max(0.0, diff / self.baseline.kwh) * 100, 1)


class StressTest:
    """TESTE DE ESTRESSE / LONGA DURAÇÃO comparando dois computadores (por
    exemplo, PC de Entrada x PC High-End) executando exatamente a mesma
    tarefa, ao mesmo tempo, para tornar visível a diferença de comportamento
    sob carga sustentada (item 4 e 12 do roteiro do projeto).
    """

    def __init__(self, tier_a: str, tier_b: str, cpu_range, gpu_range):
        self.tier_a = tier_a
        self.tier_b = tier_b
        self.track_a = Track(Computer(tier_a))
        self.track_b = Track(Computer(tier_b))
        self.cpu_range = cpu_range
        self.gpu_range = gpu_range
        # Garante pelo menos um registro no histórico assim que o teste é
        # criado, para a tela de execução nunca renderizar com dados vazios.
        self.advance(2, passo=2)

    def advance(self, seconds: int, passo: int = 2):
        restante = seconds
        while restante > 0:
            dt = min(passo, restante)
            self.track_a.tick(self.cpu_range, self.gpu_range, dt)
            self.track_b.tick(self.cpu_range, self.gpu_range, dt)
            restante -= dt

    def snapshot(self) -> dict:
        return {"a": self._snap(self.track_a), "b": self._snap(self.track_b)}

    @staticmethod
    def _snap(track: "Track") -> dict:
        if not track.history:
            return None
        last = dict(track.history[-1])
        last["nome"] = track.computer.nome
        last["temp_max_ref"] = track.computer.cooling["temp_max_ref"]
        return last
