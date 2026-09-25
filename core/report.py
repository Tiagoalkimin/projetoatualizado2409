"""Geração do relatório final da simulação."""

from . import energy, stress


def build_report(sim) -> dict:
    hist = sim.real.history
    if not hist:
        return None

    powers = [h["power"] for h in hist]
    temps = [h["temp"] for h in hist]
    cpus = [h["cpu"] for h in hist]
    gpus = [h["gpu"] for h in hist]

    consumo_medio = sum(powers) / len(powers)
    consumo_max = max(powers)
    temp_media = sum(temps) / len(temps)
    temp_max = max(temps)
    cpu_medio = sum(cpus) / len(cpus)
    gpu_medio = sum(gpus) / len(gpus)

    perfs = [h.get("performance_pct", 100.0) for h in hist]
    fps_vals = [h.get("fps", sim.computer.fps_base) for h in hist]
    performance_medio = sum(perfs) / len(perfs)
    fps_medio = sum(fps_vals) / len(fps_vals)
    stress_max = max(h.get("stress_s", 0.0) for h in hist)
    estabilidade = stress.estabilidade_rating(sim.real.lockups, sim.real.restarts, performance_medio)

    custo_atual = energy.cost_from_kwh(sim.real.kwh, sim.tarifa_kwh)
    projecao = energy.cost_projection(consumo_medio, sim.tarifa_kwh)
    economia_pct = sim.economia_percentual()

    conclusao = (
        f"Durante sua simulação, seu computador consumiu {sim.real.kwh:.3f} kWh "
        f"em {sim.real.elapsed_s/60:.1f} minutos de uso simulado, com custo estimado de "
        f"R$ {custo_atual:.2f}."
    )
    if economia_pct > 0:
        conclusao += (
            f" As decisões tomadas durante a simulação reduziram o consumo estimado em "
            f"{economia_pct:.1f}% em relação a um cenário sem otimização."
        )
    else:
        conclusao += (
            " Nenhuma otimização foi aplicada nesta simulação — experimente ativar o "
            "modo Economia ou verificar processos para observar o impacto."
        )
    conclusao += " Isso demonstra como monitoramento e gerenciamento consciente podem reduzir desperdícios."

    return {
        "computador": sim.computer.nome,
        "atividade": f"{sim.categoria} — {sim.tarefa}",
        "tempo_min": round(sim.real.elapsed_s / 60, 1),
        "consumo_medio_w": round(consumo_medio, 1),
        "consumo_max_w": round(consumo_max, 1),
        "kwh": round(sim.real.kwh, 4),
        "custo": round(custo_atual, 2),
        "temp_media": round(temp_media, 1),
        "temp_max": round(temp_max, 1),
        "cpu_medio": round(cpu_medio, 1),
        "gpu_medio": round(gpu_medio, 1),
        "economia_pct": economia_pct,
        "projecao": projecao,
        "conclusao": conclusao,
        "decisoes": sim.decisoes_aplicadas,
        "performance_medio": round(performance_medio, 1),
        "fps_medio": round(fps_medio, 0),
        "stress_max_s": round(stress_max, 1),
        "lockups": sim.real.lockups,
        "restarts": sim.real.restarts,
        "estabilidade": estabilidade,
    }


def build_stress_test_report(track) -> dict:
    """Relatório do TESTE DE ESTRESSE / LONGA DURAÇÃO para uma trilha (Track)
    de um dos computadores comparados. Todos os números vêm da simulação —
    nada é fixado no código (item 13 do roteiro)."""
    hist = track.history
    if not hist:
        return None

    temps = [h["temp"] for h in hist]
    perfs = [h["performance_pct"] for h in hist]
    fps_vals = [h["fps"] for h in hist]
    performance_medio = sum(perfs) / len(perfs)

    return {
        "nome": track.computer.nome,
        "temp_max": round(max(temps), 1),
        "performance_medio": round(performance_medio, 1),
        "fps_medio": round(sum(fps_vals) / len(fps_vals), 0),
        "travamentos": track.lockups,
        "reinicializacoes": track.restarts,
        "estabilidade": stress.estabilidade_rating(track.lockups, track.restarts, performance_medio),
    }
