"""Atividades que o usuário pode simular, agrupadas por intensidade."""

ACTIVITIES = {
    "leve": {
        "titulo": "Uso Leve",
        "tarefas": {
            "Navegador + documentos": {"cpu": (8, 18), "gpu": (2, 8)},
            "Música / vídeo em streaming": {"cpu": (10, 20), "gpu": (5, 15)},
            "Programação simples (editor de texto)": {"cpu": (12, 22), "gpu": (2, 6)},
        },
    },
    "moderado": {
        "titulo": "Uso Moderado",
        "tarefas": {
            "Multitarefa (várias abas + apps)": {"cpu": (30, 45), "gpu": (15, 30)},
            "Edição de imagens": {"cpu": (35, 55), "gpu": (25, 45)},
            "Programação pesada (build/compilação)": {"cpu": (45, 65), "gpu": (5, 15)},
            "Jogos leves": {"cpu": (30, 50), "gpu": (35, 55)},
        },
    },
    "pesado": {
        "titulo": "Uso Pesado",
        "tarefas": {
            "Jogos pesados (alta resolução)": {"cpu": (55, 75), "gpu": (85, 100)},
            "Renderização 3D": {"cpu": (85, 100), "gpu": (70, 95)},
            "Edição de vídeo (exportação)": {"cpu": (75, 95), "gpu": (60, 85)},
            "Processamento / treinamento de IA": {"cpu": (60, 80), "gpu": (90, 100)},
        },
    },
}


def get_task(categoria: str, tarefa: str) -> dict:
    return ACTIVITIES[categoria]["tarefas"][tarefa]
