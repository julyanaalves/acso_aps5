import copy

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
            
            # Limpa linhas vazias
            linhas = [l.strip() for l in linhas if l.strip()]
            
            # Primeira linha: nProc, Quantum, tTroca
            config = linhas[0].split(',')
            # Garante que leu números
            if not config[0].isdigit():
                 print("Erro: A primeira linha do arquivo deve conter os números de configuração.")
                 exit()
                 
            n_proc = int(config[0]) # Não usado diretamente mas serve pra validar
            quantum = int(config[1])
            t_troca = int(config[2])
            
            # Restante das linhas: Processos
            for linha in linhas[1:]:
                # Se a linha começar com letra (texto explicativo), para de ler
                if not linha[0].isdigit():
                    break
                    
                dados = linha.split(',')
                if len(dados) < 4: continue # Proteção contra linhas incompletas
                
                # ID, Chegada, Prio, Tcpu
                p = Processo(int(dados[0]), int(dados[1]), int(dados[2]), int(dados[3]))
                processos.append(p)
                
    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        print("Certifique-se de que ele está na mesma pasta que este script.")
        exit()
    except ValueError:
        print("Erro de Formatação: O arquivo contém caracteres inválidos onde deveriam ser números.")
        exit()
        
    return processos, quantum, t_troca

def imprimir_resultados(nome_algo, processos_finalizados, trocas, t_troca, tempo_total, linha_tempo):
    print(f"=== {nome_algo} ===")
    
    # Ordenar por PID para mostrar bonitinho
    processos_finalizados.sort(key=lambda x: x.pid)
    
    soma_turnaround = 0
    print("PID\tRetorno (Turnaround)")
    for p in processos_finalizados:
        p.tempo_retorno = p.tempo_fim - p.chegada
        soma_turnaround += p.tempo_retorno
        print(f"{p.pid}\t{p.tempo_retorno}ms")
    
    media_turnaround = soma_turnaround / len(processos_finalizados) if processos_finalizados else 0
    overhead = (trocas * t_troca) / tempo_total * 100 if tempo_total > 0 else 0
    
    print("-" * 30)
    print(f"Tempo Médio de Retorno: {media_turnaround:.2f}ms")
    print(f"Trocas de Contexto: {trocas}")
    print(f"Tempo Total Simulação: {tempo_total}ms")
    print(f"Overhead do Sistema: {overhead:.2f}%")
    
    # Formatar Linha do Tempo (Gantt) simplificada
    gantt_str = "|"
    for item in linha_tempo:
        # Se for troca de contexto, marca com X
        if item == 'Troca':
            gantt_str += " (Troca) |"
        else:
            gantt_str += f" P{item} |"
    
    print("\nLinha do Tempo (Gantt):")
    print(gantt_str)
    print("\n" + "="*40 + "\n")

# --- ALGORITMOS ---

def run_fcfs(processos, t_troca):
    # FCFS: Ordena puramente por chegada
    fila = sorted(processos, key=lambda x: x.chegada)
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    
    for p in fila:
        # Se CPU estiver ociosa até o processo chegar
        if tempo_atual < p.chegada:
            tempo_atual = p.chegada
        
        # Troca de contexto (se não for o primeiro instante absoluto 0 com processo 0)
        if tempo_atual > 0: 
            trocas += 1
            tempo_atual += t_troca
            linha_tempo.append('Troca')
            
        p.tempo_inicio = tempo_atual
        tempo_atual += p.tempo_cpu
        p.tempo_fim = tempo_atual
        p.tempo_restante = 0
        linha_tempo.append(p.pid)
        
    return fila, trocas, tempo_atual, linha_tempo

def run_sjf(processos, t_troca):
    # SJF Não Preemptivo
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    finalizados = []
    pendentes = sorted(processos, key=lambda x: x.chegada) # Todos os procs
    
    while len(finalizados) < len(processos):
        # Filtra quem já chegou
        disponiveis = [p for p in pendentes if p.chegada <= tempo_atual and p not in finalizados]
        
        if not disponiveis:
            tempo_atual += 1 
            continue
            
        # Escolhe o de menor CPU (Shortest Job)
        escolhido = min(disponiveis, key=lambda x: x.tempo_cpu)
        
        # Troca de contexto
        if tempo_atual > 0:
            trocas += 1
            tempo_atual += t_troca
            linha_tempo.append('Troca')
            
        escolhido.tempo_inicio = tempo_atual
        tempo_atual += escolhido.tempo_cpu
        escolhido.tempo_fim = tempo_atual
        escolhido.tempo_restante = 0
        linha_tempo.append(escolhido.pid)
        finalizados.append(escolhido)
        
    return finalizados, trocas, tempo_atual, linha_tempo

def run_srtf(processos, t_troca):
    # SRTF (SJF Preemptivo)
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    
    pendentes = processos
    ultimo_pid = -1
    concluidos = 0
    
    while concluidos < len(processos):
        disponiveis = [p for p in pendentes if p.chegada <= tempo_atual and p.tempo_restante > 0]
        
        if not disponiveis:
            tempo_atual += 1
            continue
            
        # Escolhe o que falta menos tempo
        escolhido = min(disponiveis, key=lambda x: x.tempo_restante)
        
        # Se mudou o processo, paga o t_troca
        if escolhido.pid != ultimo_pid:
            if ultimo_pid != -1: 
                trocas += 1
                tempo_atual += t_troca
                linha_tempo.append('Troca')
            ultimo_pid = escolhido.pid
            
        # Executa 1 unidade de tempo
        escolhido.tempo_restante -= 1
        tempo_atual += 1
        
        if len(linha_tempo) == 0 or linha_tempo[-1] != escolhido.pid:
             if linha_tempo and linha_tempo[-1] == 'Troca': pass
             else: linha_tempo.append(escolhido.pid)
        
        if escolhido.tempo_restante == 0:
            escolhido.tempo_fim = tempo_atual
            concluidos += 1
            ultimo_pid = -1 
            
    return processos, trocas, tempo_atual, linha_tempo

def run_rr(processos, quantum, t_troca):
    # Round Robin
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    fila = []
    
    # Controladores
    idx_chegada = 0
    processos.sort(key=lambda x: x.chegada) 
    
    if processos:
        # Se o primeiro processo não chega no tempo 0, avança o tempo
        if processos[0].chegada > tempo_atual:
             tempo_atual = processos[0].chegada
             
        fila.append(processos[0])
        idx_chegada = 1
        
    while fila or idx_chegada < len(processos):
        if not fila and idx_chegada < len(processos):
             # Avança tempo se o próximo ainda não chegou e fila tá vazia
             if tempo_atual < processos[idx_chegada].chegada:
                 tempo_atual = processos[idx_chegada].chegada
             fila.append(processos[idx_chegada])
             idx_chegada += 1
        
        if not fila: break 
        
        p = fila.pop(0)
        
        trocas += 1
        if tempo_atual > 0:
            tempo_atual += t_troca
            linha_tempo.append('Troca')
            
        tempo_exec = min(quantum, p.tempo_restante)
        
        # Executa passo a passo para verificar chegadas durante a execução
        for _ in range(tempo_exec):
            p.tempo_restante -= 1
            tempo_atual += 1
            # Verifica chegadas
            while idx_chegada < len(processos) and processos[idx_chegada].chegada <= tempo_atual:
                fila.append(processos[idx_chegada])
                idx_chegada += 1
                
        linha_tempo.append(p.pid)
            
        if p.tempo_restante > 0:
            fila.append(p) 
        else:
            p.tempo_fim = tempo_atual
            
    return processos, trocas, tempo_atual, linha_tempo

def run_prioridade(processos, t_troca):
    # Prioridade Preemptiva
    # Assumindo: Maior número = Maior prioridade (comum).
    # Se quiser o contrário (Unix style), use key=lambda x: (x.prioridade, x.chegada)
    
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    pendentes = processos
    ultimo_pid = -1
    concluidos = 0
    
    while concluidos < len(processos):
        disponiveis = [p for p in pendentes if p.chegada <= tempo_atual and p.tempo_restante > 0]
        
        if not disponiveis:
            tempo_atual += 1
            continue
        
        # Ordena por Prioridade (Maior primeiro) e depois por chegada
        escolhido = sorted(disponiveis, key=lambda x: (-x.prioridade, x.chegada))[0]
        
        if escolhido.pid != ultimo_pid:
            if ultimo_pid != -1:
                trocas += 1
                tempo_atual += t_troca
                linha_tempo.append('Troca')
            ultimo_pid = escolhido.pid
            
        escolhido.tempo_restante -= 1
        tempo_atual += 1
        
        if len(linha_tempo) == 0 or linha_tempo[-1] != escolhido.pid:
             if linha_tempo and linha_tempo[-1] == 'Troca': pass
             else: linha_tempo.append(escolhido.pid)

        if escolhido.tempo_restante == 0:
            escolhido.tempo_fim = tempo_atual
            concluidos += 1
            ultimo_pid = -1
            
    return processos, trocas, tempo_atual, linha_tempo


# --- MAIN ---
if __name__ == "__main__":
    # Nome exato do arquivo que você mandou
    arquivo = 'EntradaProcessos.txt'
    
    print(f"Lendo arquivo: {arquivo} ...\n")
    
    # 1. FCFS
    procs, q, t = ler_arquivo(arquivo)
    p_fcfs, trocas, total, linha = run_fcfs(copy.deepcopy(procs), t)
    imprimir_resultados("FCFS (First-Come First-Served)", p_fcfs, trocas, t, total, linha)
    
    # 2. SJF
    p_sjf, trocas, total, linha = run_sjf(copy.deepcopy(procs), t)
    imprimir_resultados("SJF (Shortest Job First - Não Preemptivo)", p_sjf, trocas, t, total, linha)
    
    # 3. SRTF
    p_srtf, trocas, total, linha = run_srtf(copy.deepcopy(procs), t)
    imprimir_resultados("SRTF (Shortest Remaining Time First - Preemptivo)", p_srtf, trocas, t, total, linha)
    
    # 4. Round Robin
    p_rr, trocas, total, linha = run_rr(copy.deepcopy(procs), q, t)
    imprimir_resultados(f"Round Robin (Quantum={q})", p_rr, trocas, t, total, linha)
    
    # 5. Prioridade
    p_prio, trocas, total, linha = run_prioridade(copy.deepcopy(procs), t)
    imprimir_resultados("Prioridade Preemptiva", p_prio, trocas, t, total, linha)
    
    input("Pressione Enter para sair...")