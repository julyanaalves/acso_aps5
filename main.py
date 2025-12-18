import copy
import os
import sys

SWITCH_MARK = 'Escalonador'
IDLE_MARK = 'Ocioso'


def _tick_idle(linha_tempo, tempo_atual):
    linha_tempo.append(IDLE_MARK)
    return tempo_atual + 1


def _tick_switch(linha_tempo, tempo_atual):
    linha_tempo.append(SWITCH_MARK)
    return tempo_atual + 1

class Processo:
    def __init__(self, pid, chegada, prioridade, tempo_cpu):
        self.pid = pid
        self.chegada = chegada
        self.prioridade = prioridade
        self.tempo_cpu = tempo_cpu
        self.tempo_restante = tempo_cpu
        self.tempo_inicio = -1
        self.tempo_fim = 0
        self.tempo_retorno = 0 # Turnaround

def ler_arquivo(nome_arquivo):
    processos = []
    try:
        with open(nome_arquivo, 'r') as f:
            linhas = f.readlines()
            linhas = [l.strip() for l in linhas if l.strip()] # Limpa vazias
            
            # Configuração
            config = linhas[0].split(',')
            if not config[0].isdigit():
                 print("Erro: A primeira linha deve conter os numeros de configuracao.")
                 sys.exit(1)
                 
            n_proc = int(config[0])
            quantum = int(config[1])
            t_troca = int(config[2])
            
            # Processos
            count = 0
            for linha in linhas[1:]:
                if count >= n_proc: break # Para se ja leu todos
                if not linha[0].isdigit(): break # Para se achou texto
                    
                dados = linha.split(',')
                if len(dados) < 4: continue
                
                p = Processo(int(dados[0]), int(dados[1]), int(dados[2]), int(dados[3]))
                processos.append(p)
                count += 1
                
    except FileNotFoundError:
        print(f"Erro: Arquivo '{nome_arquivo}' nao encontrado.")
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler arquivo: {e}")
        sys.exit(1)
        
    return processos, quantum, t_troca

def log(texto, arquivo_saida):
    print(texto, end='') 
    with open(arquivo_saida, 'a', encoding='utf-8') as f: 
        f.write(texto)

def imprimir_resultados(nome_algo, processos_finalizados, trocas, t_troca, tempo_total, linha_tempo, arquivo_saida):
    texto = []
    texto.append(f"=== {nome_algo} ===\n")
    
    processos_finalizados.sort(key=lambda x: x.pid)
    
    soma_turnaround = 0
    texto.append(f"{'PID':<5} | {'Retorno (Turnaround)':<20}\n")
    texto.append("-" * 30 + "\n")
    
    for p in processos_finalizados:
        p.tempo_retorno = p.tempo_fim - p.chegada
        soma_turnaround += p.tempo_retorno
        texto.append(f"{p.pid:<5} | {p.tempo_retorno:<18}ms\n")
    
    media_turnaround = soma_turnaround / len(processos_finalizados) if processos_finalizados else 0
    
    # Overhead como Fração e Porcentagem
    tempo_trocas = trocas * t_troca
    overhead_frac = tempo_trocas / tempo_total if tempo_total > 0 else 0
    overhead_perc = overhead_frac * 100
    
    texto.append("-" * 30 + "\n")
    texto.append(f"Tempo Medio de Retorno:  {media_turnaround:.2f}ms\n")
    texto.append(f"Trocas de Contexto:      {trocas}\n")
    texto.append(f"Tempo Total Simulacao:   {tempo_total}ms\n")
    texto.append(f"Overhead do Sistema:     {overhead_frac:.4f} ({overhead_perc:.2f}%)\n")
    
    def formatar_linha_tempo(itens, largura=120):
        partes = []
        for item in itens:
            if isinstance(item, int):
                partes.append(f"P{item}")
            else:
                partes.append(str(item))

        linhas = []
        linha_atual = ""
        for p in partes:
            if not linha_atual:
                linha_atual = p
                continue
            candidato = linha_atual + " " + p
            if len(candidato) > largura:
                linhas.append(linha_atual)
                linha_atual = p
            else:
                linha_atual = candidato
        if linha_atual:
            linhas.append(linha_atual)

        return "\n".join(linhas)

    texto.append("\nLinha do Tempo (CPU por instante):\n")
    texto.append(formatar_linha_tempo(linha_tempo) + "\n")
    texto.append("\n" + "="*50 + "\n\n")

    log("".join(texto), arquivo_saida)


def run_fcfs(processos, t_troca):
    # Desempate: Chegada -> PID menor
    fila = sorted(processos, key=lambda x: (x.chegada, x.pid))
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    ultimo_pid = None

    for p in fila:
        while tempo_atual < p.chegada:
            tempo_atual = _tick_idle(linha_tempo, tempo_atual)

        if ultimo_pid is not None and ultimo_pid != p.pid:
            trocas += 1
            for _ in range(t_troca):
                tempo_atual = _tick_switch(linha_tempo, tempo_atual)

        p.tempo_inicio = tempo_atual
        for _ in range(p.tempo_cpu):
            linha_tempo.append(p.pid)
            tempo_atual += 1

        p.tempo_fim = tempo_atual
        p.tempo_restante = 0
        ultimo_pid = p.pid

    return fila, trocas, tempo_atual, linha_tempo

def run_sjf(processos, t_troca):
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    finalizados = []
    ultimo_pid = None
    # Ordena lista principal por Chegada -> PID
    pendentes = sorted(processos, key=lambda x: (x.chegada, x.pid))
    
    while len(finalizados) < len(processos):
        disponiveis = [p for p in pendentes if p.chegada <= tempo_atual and p not in finalizados]
        
        if not disponiveis:
            tempo_atual = _tick_idle(linha_tempo, tempo_atual)
            continue
            
        # SJF: Menor CPU -> Menor Chegada -> Menor PID
        escolhido = min(disponiveis, key=lambda x: (x.tempo_cpu, x.chegada, x.pid))
        
        if ultimo_pid is not None and ultimo_pid != escolhido.pid:
            trocas += 1
            for _ in range(t_troca):
                tempo_atual = _tick_switch(linha_tempo, tempo_atual)

        escolhido.tempo_inicio = tempo_atual
        for _ in range(escolhido.tempo_cpu):
            linha_tempo.append(escolhido.pid)
            tempo_atual += 1

        escolhido.tempo_fim = tempo_atual
        escolhido.tempo_restante = 0
        finalizados.append(escolhido)
        ultimo_pid = escolhido.pid
        
    return finalizados, trocas, tempo_atual, linha_tempo

def run_srtf(processos, t_troca):
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    pid_ultimo_executado = None
    concluidos = 0

    while concluidos < len(processos):
        disponiveis = [p for p in processos if p.chegada <= tempo_atual and p.tempo_restante > 0]

        if not disponiveis:
            tempo_atual = _tick_idle(linha_tempo, tempo_atual)
            pid_ultimo_executado = None
            continue

        # SRTF: Menor Restante -> Menor Chegada -> Menor PID
        escolhido = min(disponiveis, key=lambda x: (x.tempo_restante, x.chegada, x.pid))

        if pid_ultimo_executado is not None and pid_ultimo_executado != escolhido.pid:
            trocas += 1
            for _ in range(t_troca):
                tempo_atual = _tick_switch(linha_tempo, tempo_atual)
            pid_ultimo_executado = None
            continue

        escolhido.tempo_restante -= 1
        linha_tempo.append(escolhido.pid)
        tempo_atual += 1
        pid_ultimo_executado = escolhido.pid

        if escolhido.tempo_restante == 0:
            escolhido.tempo_fim = tempo_atual
            concluidos += 1
            # Mantém pid_ultimo_executado para contar a troca ao iniciar outro processo

    return processos, trocas, tempo_atual, linha_tempo

def run_rr(processos, quantum, t_troca):
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    fila = []
    idx_chegada = 0

    processos.sort(key=lambda x: (x.chegada, x.pid))

    def enfileirar_chegadas():
        nonlocal idx_chegada
        while idx_chegada < len(processos) and processos[idx_chegada].chegada <= tempo_atual:
            fila.append(processos[idx_chegada])
            idx_chegada += 1

    ultimo_pid = None

    while fila or idx_chegada < len(processos):
        if not fila:
            proxima_chegada = processos[idx_chegada].chegada
            while tempo_atual < proxima_chegada:
                tempo_atual = _tick_idle(linha_tempo, tempo_atual)
            enfileirar_chegadas()

        if not fila:
            break

        p = fila.pop(0)

        if ultimo_pid is not None and ultimo_pid != p.pid:
            trocas += 1
            for _ in range(t_troca):
                tempo_atual = _tick_switch(linha_tempo, tempo_atual)
                enfileirar_chegadas()

        tempo_exec = min(quantum, p.tempo_restante)
        for _ in range(tempo_exec):
            p.tempo_restante -= 1
            linha_tempo.append(p.pid)
            tempo_atual += 1
            enfileirar_chegadas()
            if p.tempo_restante == 0:
                break

        if p.tempo_restante > 0:
            fila.append(p)
        else:
            p.tempo_fim = tempo_atual

        ultimo_pid = p.pid

    return processos, trocas, tempo_atual, linha_tempo

def run_prioridade(processos, t_troca):
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    pid_ultimo_executado = None
    concluidos = 0

    while concluidos < len(processos):
        disponiveis = [p for p in processos if p.chegada <= tempo_atual and p.tempo_restante > 0]

        if not disponiveis:
            tempo_atual = _tick_idle(linha_tempo, tempo_atual)
            pid_ultimo_executado = None
            continue

        # ENUNCIADO: menor valor numérico = maior prioridade
        # Desempates: chegada e depois PID
        escolhido = min(disponiveis, key=lambda x: (x.prioridade, x.chegada, x.pid))

        if pid_ultimo_executado is not None and pid_ultimo_executado != escolhido.pid:
            trocas += 1
            for _ in range(t_troca):
                tempo_atual = _tick_switch(linha_tempo, tempo_atual)
            pid_ultimo_executado = None
            continue

        escolhido.tempo_restante -= 1
        linha_tempo.append(escolhido.pid)
        tempo_atual += 1
        pid_ultimo_executado = escolhido.pid

        if escolhido.tempo_restante == 0:
            escolhido.tempo_fim = tempo_atual
            concluidos += 1
            # Mantém pid_ultimo_executado para contar a troca ao iniciar outro processo

    return processos, trocas, tempo_atual, linha_tempo

#Função Principal
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Erro: Forneca o arquivo de entrada.")
        print("Exemplo: python main.py in/EntradaProcessos.txt")
        sys.exit(1)

    arquivo_entrada = sys.argv[1]
    pasta_saida = 'report'
    
    nome_base = os.path.basename(arquivo_entrada) 
    nome_sem_extensao = os.path.splitext(nome_base)[0] 
    arquivo_saida = os.path.join(pasta_saida, f"Saida_{nome_sem_extensao}.txt")
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    open(arquivo_saida, 'w').close()
    
    print(f"Lendo: {arquivo_entrada}")
    print(f"Gerando relatorios em: {arquivo_saida}\n")
    
    procs, q, t = ler_arquivo(arquivo_entrada)
    
    p_fcfs, tr, tot, lin = run_fcfs(copy.deepcopy(procs), t)
    imprimir_resultados("FCFS", p_fcfs, tr, t, tot, lin, arquivo_saida)
    
    p_sjf, tr, tot, lin = run_sjf(copy.deepcopy(procs), t)
    imprimir_resultados("SJF (Nao Preemptivo)", p_sjf, tr, t, tot, lin, arquivo_saida)
    
    p_srtf, tr, tot, lin = run_srtf(copy.deepcopy(procs), t)
    imprimir_resultados("SRTF (Preemptivo)", p_srtf, tr, t, tot, lin, arquivo_saida)
    
    p_rr, tr, tot, lin = run_rr(copy.deepcopy(procs), q, t)
    imprimir_resultados(f"Round Robin (Q={q})", p_rr, tr, t, tot, lin, arquivo_saida)
    
    p_prio, tr, tot, lin = run_prioridade(copy.deepcopy(procs), t)
    imprimir_resultados("Prioridade (Preemptiva - Menor Valor=Maior Prio)", p_prio, tr, t, tot, lin, arquivo_saida)
    
    print(f"\nSucesso! Arquivo '{arquivo_saida}' gerado.")