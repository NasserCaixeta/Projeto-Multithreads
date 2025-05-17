import threading
import time
from datetime import datetime
from openpyxl import Workbook

# Variáveis globais
balde_capacidade = 100
balde_atual = 0
lock = threading.Lock()
vezes_lavador = 0
litros_retirados = 0
tempo_maximo = 120  # 2 minutos

# Contadores por ajudante
contador_ajudantes = {
    "Ajudante-1": {"encheu": 0, "esperou": 0},
    "Ajudante-2": {"encheu": 0, "esperou": 0},
    "Ajudante-3": {"encheu": 0, "esperou": 0},
}

# Evento para encerrar o processo
encerrar = threading.Event()

# Lista para armazenar logs (timestamp, mensagem)
log_eventos = []

def log(msg):
    """Registra evento no console e na lista"""
    agora = datetime.now().strftime("%H:%M:%S")
    mensagem = f"[{agora}] {msg}"
    print(mensagem)
    log_eventos.append((agora, msg))

def ajudante(nome):
    global balde_atual
    inicio = time.time()
    while time.time() - inicio < tempo_maximo and not encerrar.is_set():
        with lock:
            if balde_atual + 3 > balde_capacidade:
                log(f"{nome} tentou encher, mas o balde está cheio. Aguardando 2s...")
                contador_ajudantes[nome]["esperou"] += 1
            else:
                balde_atual += 3
                log(f"{nome} encheu 3L. Total no balde: {balde_atual}L")
                contador_ajudantes[nome]["encheu"] += 1
                time.sleep(0.5)
                continue
        time.sleep(2)

def lavador():
    global balde_atual, vezes_lavador, litros_retirados
    time.sleep(3)  # Espera inicial
    while not encerrar.is_set():
        with lock:
            if balde_atual >= 10:
                balde_atual -= 10
                vezes_lavador += 1
                litros_retirados += 10
                log(f"Lavador retirou 10L. Restante no balde: {balde_atual}L")
            elif balde_atual > 0:
                log(f"Lavador retirou {balde_atual}L. Balde esvaziado.")
                litros_retirados += balde_atual
                balde_atual = 0
                vezes_lavador += 1
                encerrar.set()
                break
            else:
                log("Lavador foi ao balde, mas estava vazio. Aguardando...")
        time.sleep(1)

# Criando threads
ajudantes = [
    threading.Thread(target=ajudante, args=(f"Ajudante-{i+1}",))
    for i in range(3)
]
lavador_thread = threading.Thread(target=lavador)

# Iniciando
inicio_total = datetime.now()
for t in ajudantes:
    t.start()
lavador_thread.start()

# Finalizando
for t in ajudantes:
    t.join()
encerrar.set()
lavador_thread.join()
fim_total = datetime.now()

# ---------- Logs finais ----------
log(f"PROCESSO ENCERRADO: Lavador foi ao balde {vezes_lavador} vezes.")
log(f"Total de litros retirados: {litros_retirados}L")
duracao = fim_total - inicio_total
log(f"Duração total do processo: {duracao}")

# ---------- Salvando em planilha Excel ----------
def salvar_em_excel(dados_log, arquivo="log_balde.xlsx"):
    wb = Workbook()

    # Aba 1: Log do Processo
    ws1 = wb.active
    ws1.title = "Log do Processo"
    ws1.append(["Timestamp", "Evento"])
    for linha in dados_log:
        ws1.append(linha)

    # Aba 2: Resumo
    ws2 = wb.create_sheet(title="Resumo")
    ws2.append(["Resumo", "Valor"])
    ws2.append(["Total de idas do lavador ao balde", vezes_lavador])
    ws2.append(["Total de litros retirados", litros_retirados])
    ws2.append(["Duração total (s)", round(duracao.total_seconds(), 2)])
    ws2.append([])

    # Detalhes dos ajudantes
    ws2.append(["Ajudante", "Tentativas de Encher", "Esperas por balde cheio"])
    for nome, stats in contador_ajudantes.items():
        ws2.append([nome, stats["encheu"], stats["esperou"]])

    wb.save(arquivo)

salvar_em_excel(log_eventos)
log("Log salvo em 'log_balde.xlsx'.")
