# Simulador de Escalonamento de Processos

Este projeto implementa uma simulação de diversos algoritmos de escalonamento de processos em Python. O objetivo é comparar o desempenho de diferentes estratégias de escalonamento com base em um conjunto de processos fornecido.

## Algoritmos Implementados

O simulador executa os seguintes algoritmos para o mesmo conjunto de processos:

1.  **FCFS (First-Come First-Served):** O primeiro processo a chegar é o primeiro a ser executado. Não preemptivo.
2.  **SJF (Shortest Job First):** Escolhe o processo com o menor tempo de CPU (burst time). Não preemptivo.
3.  **SRTF (Shortest Remaining Time First):** Versão preemptiva do SJF. Se um processo novo chega com tempo menor que o restante do atual, ocorre troca.
4.  **Round Robin:** Cada processo recebe uma fatia de tempo (Quantum). Se não terminar, volta para o fim da fila.
5.  **Prioridade:** Escolhe o processo com maior prioridade. Preemptivo (se chegar um processo com prioridade maior, o atual é interrompido).

Obs.: conforme o enunciado, **quanto menor o valor numérico da prioridade, maior é a prioridade**.

## Estrutura do Projeto

-   `main.py`: Script principal contendo a lógica de simulação e os algoritmos.
-   `EntradaProcessos.txt`: Arquivo de configuração e lista de processos a serem simulados.

## Como Executar

Certifique-se de ter o Python instalado em sua máquina.

1.  Prepare seu arquivo de entrada (ex: `in/Teste1.txt`).
2.  Execute o script passando o caminho do arquivo como argumento:

```bash
python main.py in/Teste1.txt
```

O programa lerá o arquivo especificado e gerará um relatório na pasta `report/`.

### Saída

Os resultados serão salvos automaticamente na pasta `report/` com o prefixo `Saida_`.
Exemplo:
- Entrada: `in/Teste1.txt`
- Saída: `report/Saida_Teste1.txt`

## Formato do Arquivo de Entrada (`EntradaProcessos.txt`)

O arquivo deve seguir estritamente o formato abaixo (separado por vírgulas):

**Primeira Linha (Configuração Global):**
```text
nProc,Quantum,tTroca
```
-   `nProc`: Número de processos (informativo).
-   `Quantum`: Tamanho da fatia de tempo para o Round Robin.
-   `tTroca`: Tempo gasto na troca de contexto (overhead).

**Linhas Seguintes (Processos):**
```text
ID,Chegada,Prioridade,TempoCPU
```
-   `ID`: Identificador único do processo.
-   `Chegada`: Tempo em que o processo chega na fila de prontos.
-   `Prioridade`: Prioridade do processo (maior valor indica maior prioridade).

> No algoritmo de Prioridade deste projeto, **menor número = maior prioridade**, como pedido no enunciado.
-   `TempoCPU`: Tempo total de execução necessário (Burst Time).

**Exemplo:**
```text
5,20,1
1,0,1,50
2,1,0,15
3,3,2,10
4,5,0,100
5,6,3,60
```

## Métricas Calculadas

Para cada algoritmo, o simulador exibe:
-   **Turnaround Time (Tempo de Retorno):** Tempo desde a chegada até a conclusão do processo.
-   **Tempo Médio de Retorno:** Média dos turnarounds de todos os processos.
-   **Trocas de Contexto:** Quantidade total de vezes que a CPU alternou entre processos.
-   **Tempo Total de Simulação:** Tempo total gasto para executar todos os processos, incluindo trocas.
-   **Overhead do Sistema:** Porcentagem do tempo total gasto apenas em trocas de contexto.
-   **Linha do Tempo (Gantt):** Visualização simplificada da ordem de execução.

### Linha do tempo

A “Linha do Tempo (CPU por instante)” mostra **a ocupação da CPU a cada unidade de tempo** do início ao fim:
- `P<id>` quando um processo está executando
- `Escalonador` durante a troca de contexto (por `tTroca` instantes)
- `Ocioso` quando não há processo pronto para executar
