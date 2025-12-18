import copy
import os
import sys

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
            
            # 1. Leitura da Configuração (Linha 1)
            config = linhas[0].split(',')
            if not config[0].isdigit():
                 print("Erro: A primeira linha do arquivo deve conter os números de configuração.")
                 exit()
                 
            n_proc = int(config[0])
            quantum = int(config[1])
            t_troca = int(config[2])
            
            # 2. Leitura dos Processos
            count = 0
            for linha in linhas[1:]:
                if count >= n_proc: break # Para se já leu todos os processos
                if not linha[0].isdigit(): break # Para se achou texto
                    
                dados = linha.split(',')
                if len(dados) < 4: continue
                
                p = Processo(int(dados[0]), int(dados[1]), int(dados[2]), int(dados[3]))
                processos.append(p)
                count += 1
                
    except FileNotFoundError:
        print(f"Erro: O arquivo '{nome_arquivo}' não foi encontrado.")
        sys.exit(1)
    except ValueError:
        print("Erro de Formatação no arquivo de entrada.")
        sys.exit(1)
    except IndexError:
        print("Erro: Arquivo vazio ou mal formatado.")
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
    overhead = (trocas * t_troca) / tempo_total * 100 if tempo_total > 0 else 0
    
    texto.append("-" * 30 + "\n")
    texto.append(f"Tempo Medio de Retorno:  {media_turnaround:.2f}ms\n")
    texto.append(f"Trocas de Contexto:      {trocas}\n")
    texto.append(f"Tempo Total Simulacao:   {tempo_total}ms\n")
    texto.append(f"Overhead do Sistema:     {overhead:.2f}%\n")
    
    gantt_str = "|"
    for item in linha_tempo:
        if item == 'Troca':
            gantt_str += " (Troca) |"
        else:
            gantt_str += f" P{item} |"
    
    texto.append("\nLinha do Tempo (Gantt):\n")
    texto.append(gantt_str + "\n")
    texto.append("\n" + "="*50 + "\n\n")

    log("".join(texto), arquivo_saida)

# --- ALGORITMOS ---

def run_fcfs(processos, t_troca):
    fila = sorted(processos, key=lambda x: x.chegada)
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    for p in fila:
        if tempo_atual < p.chegada: tempo_atual = p.chegada
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
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    finalizados = []
    pendentes = sorted(processos, key=lambda x: x.chegada)
    while len(finalizados) < len(processos):
        disponiveis = [p for p in pendentes if p.chegada <= tempo_atual and p not in finalizados]
        if not disponiveis:
            tempo_atual += 1 
            continue
        escolhido = min(disponiveis, key=lambda x: x.tempo_cpu)
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
        escolhido = min(disponiveis, key=lambda x: x.tempo_restante)
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

def run_rr(processos, quantum, t_troca):
    tempo_atual = 0
    trocas = 0
    linha_tempo = []
    fila = []
    idx_chegada = 0
    processos.sort(key=lambda x: x.chegada) 
    if processos:
        if processos[0].chegada > tempo_atual: tempo_atual = processos[0].chegada
        fila.append(processos[0])
        idx_chegada = 1
    while fila or idx_chegada < len(processos):
        if not fila and idx_chegada < len(processos):
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
        for _ in range(tempo_exec):
            p.tempo_restante -= 1
            tempo_atual += 1
            while idx_chegada < len(processos) and processos[idx_chegada].chegada <= tempo_atual:
                fila.append(processos[idx_chegada])
                idx_chegada += 1
        linha_tempo.append(p.pid)
        if p.tempo_restante > 0: fila.append(p) 
        else: p.tempo_fim = tempo_atual
    return processos, trocas, tempo_atual, linha_tempo

def run_prioridade(processos, t_troca):
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
    # Verifica argumentos da linha de comando
    if len(sys.argv) < 2:
        print("Erro: Forneca o arquivo de entrada.")
        print("Exemplo: python main.py in/EntradaProcessos.txt")
        sys.exit(1)

    arquivo_entrada = sys.argv[1]
    pasta_saida = 'report'
    
    # Gera nome da saída baseado na entrada
    # Ex: in/EntradaTeste1.txt -> report/Saida_EntradaTeste1.txt
    nome_base = os.path.basename(arquivo_entrada) # Pega só o nome do arquivo (sem pasta)
    nome_sem_extensao = os.path.splitext(nome_base)[0] # Tira o .txt
    arquivo_saida = os.path.join(pasta_saida, f"Saida_{nome_sem_extensao}.txt")
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    # Limpa arquivo anterior
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
    imprimir_resultados("Prioridade (Preemptiva)", p_prio, tr, t, tot, lin, arquivo_saida)
    
    print(f"\nSucesso! Arquivo '{arquivo_saida}' gerado.")