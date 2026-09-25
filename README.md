# ⚡ EnergyLens — Simulador de Consumo Energético de Computadores

Protótipo de Hackathon (Engenharia da Computação) que demonstra, de forma
visual e interativa, a cadeia:

**Uso de CPU/GPU → Consumo (W) → Calor → Temperatura → Energia (kWh) → Custo (R$)**

## Como rodar

```bash
cd energy_sim
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

O navegador abrirá automaticamente em `http://localhost:8501`.

## Estrutura do projeto

```
energy_sim/
├── app.py                  # Interface Streamlit (todas as telas)
├── models/
│   ├── cpu.py               # Perfis de CPU e cálculo de potência/tensão
│   ├── gpu.py                # Perfis de GPU e cálculo de potência
│   ├── components.py        # Placa-mãe, RAM, SSD, ventoinhas, refrigeração
│   ├── computer.py          # Classe Computer (agrega CPU+GPU+componentes)
│   └── activities.py        # Tarefas (leve/moderado/pesado) e faixas de uso
├── core/
│   ├── energy.py            # Potência, kWh, custo, projeções, faixa esperada
│   ├── thermal.py           # Temperatura gradual (aproximação exponencial)
│   ├── simulator.py         # Orquestra o avanço do tempo e as decisões
│   ├── stress.py            # Estresse prolongado, throttling, instabilidade
│   ├── experiments.py       # Laboratório de experimentos (8 experimentos)
│   ├── recommendations.py   # Modos de energia, detecção de anomalia, dicas
│   └── report.py            # Relatório final da simulação
└── requirements.txt
```

O fluxo da interface segue exatamente as etapas pedidas: apresentação do
problema → objetivo do simulador → explicação de voltagem → escolha do PC →
escolha da atividade → simulação ao vivo com HUD e decisões interativas →
relatório final → quem é afetado / impactos / soluções → teste de estresse →
**laboratório de experimentos** → conclusão.

## 🔬 Laboratório de experimentos

Tela nova (depois do teste de estresse) que transforma o simulador em
experimento científico: uma variável é alterada, os parâmetros são medidos e a
conclusão sai dos dados. **Nada é fixado no código** — tabelas, gráficos e até
os textos de conclusão são calculados pela simulação (semente fixa, então o
resultado é reproduzível). Cada experimento tem pergunta, objetivo,
procedimento e o que observar, e permite baixar a tabela em CSV.

| # | Experimento | Variável alterada | O que é medido |
|---|-------------|-------------------|----------------|
| 1 ⭐ | Condição normal × consumo elevado | carga 25% × 100% | corrente da CPU, potência, temperatura, alerta de anomalia |
| 2 ⭐ | Aumento progressivo da carga | 25 / 50 / 75 / 100% | gráficos Carga × Potência e Carga × Temperatura |
| 3 ⭐ | Consumo elétrico × aquecimento | potência (por carga e por processo extra) | gráfico Potência × Temperatura de equilíbrio |
| 4 ⭐ | O papel da refrigeração | refrigeração reduzida / normal / eficiente (mesma carga) | temperatura, margem até o limite, estabilidade |
| 5 | Tempo de operação × temperatura | tempo (0–600 s) | equilíbrio térmico e constante de tempo |
| 6 | Simulação de sobrecarga | salto de carga normal → 100% | tempo até aviso térmico, travamento, queda de desempenho |
| 7 🔄 | Variação brusca de carga | 25% → 100% → 25% | resposta elétrica (rápida) × térmica (gradual) |
| 8 | Qual situação é mais crítica? | uso leve / moderado / intenso / intenso + baixa dissipação | classificação Normal / Atenção / Crítico |

⭐ = essenciais · 🔄 = opcional. Há um "modo enxuto" que mostra só os
recomendados (4 essenciais + variação brusca).

**Limitações assumidas:** o modelo térmico é de 1ª ordem — a temperatura de
equilíbrio é proporcional à potência por construção — e a corrente da CPU é
estimada como `I = P / V`. Os experimentos demonstram o conceito com um modelo
educativo; não são medições de hardware real.

## Como funciona a simulação (resumo técnico)

- **Potência:** cada componente tem uma potência "idle" e uma "máxima"; o
  consumo cresce de forma levemente não-linear com a utilização (`util^1.15`
  para CPU, `util^1.1` para GPU), simulando boost de clock/tensão.
- **Temperatura:** nunca muda instantaneamente. A cada "tick", ela se
  aproxima exponencialmente (`1 - e^(-dt/τ)`) de uma temperatura-alvo que
  depende da potência atual e da capacidade de refrigeração do PC escolhido.
- **kWh:** integração simples de potência × tempo (`W × h / 1000`).
- **Custo:** `kWh × tarifa configurável (R$/kWh)`, com projeções para 1h, 8h
  e 30 dias mantendo a potência média observada.
- **Economia obtida:** o simulador roda **duas trilhas em paralelo** — uma
  "real" (com as decisões do usuário) e uma "baseline" (sem otimizações). A
  diferença percentual entre as duas é a economia mostrada no relatório.
- **Detecção de anomalia:** compara o consumo atual com uma faixa esperada
  calculada a partir da própria tarefa selecionada; um botão permite injetar
  um "processo desnecessário" (+90 W) para demonstrar a detecção na prática.

## O que eu expandiria primeiro

1. **Atualização automática em tempo real:** hoje o avanço do tempo é feito
   por botões ("Avançar 10s/60s/5min") para manter o protótipo simples e
   sem dependências extras. Um próximo passo natural é usar
   `streamlit-autorefresh` (ou um loop com `st.fragment` + `time.sleep`) para
   que o HUD atue como um painel realmente "ao vivo", sem clique.
2. **Leitura de hardware real (opcional):** integrar `psutil` para mostrar,
   lado a lado, o uso real da CPU/GPU da máquina do usuário comparado com a
   simulação — reforçando a ponte entre o didático e o real.
3. **Persistência de histórico:** salvar relatórios de sessões anteriores
   (SQLite ou arquivo JSON) para comparar "meu uso de hoje vs. ontem" e criar
   um ranking de eficiência entre diferentes perfis de uso.
4. **Curvas de hardware mais realistas:** substituir as curvas simplificadas
   por dados de TDP/consumo reais (ex. tabelas públicas de fabricantes) para
   aumentar a credibilidade técnica perante a banca.
5. **Modo "história guiada":** transformar as telas explicativas (problema,
   afetados, impactos, soluções) em um carrossel com progresso salvo, e
   adicionar uma trilha sonora/ilustrações para reforçar o clima de
   apresentação de Hackathon.
