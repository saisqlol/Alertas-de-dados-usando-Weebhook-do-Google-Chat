import pandas as pd
import os
import sys

current_dir = os.getcwd()
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from requisicao import df_dax_bi 
from querys import query_onepage,query_conversao_geral
from params import DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page
import numpy as np

df_hora = df_dax_bi(query_onepage, DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page)
df_dia = df_dax_bi(query_conversao_geral, DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page)


df_dia = df_dia.rename(columns={
    'Calendário[Dia]': 'Data',
    '[Taxa_de_conversão]': 'Tx_Conversao',
    '[Visitas]': 'Visitas',
    '[Visitas_Engajadas]' : 'Visistas_Engajadas'
})

df_hora = df_hora.rename(columns={
    'Calendário[Dia]': 'Data',
    'Base One Page[hora]':'Hora',
    '[Taxa_de_conversão]': 'Tx_Conversao',
    '[Visitas]': 'Visitas',
    '[Visitas_Engajadas]' : 'Visistas_Engajadas'
})


# --- Pré-processamento e Funções ---

# 1. Garante que as colunas 'Data' estão no formato datetime
df_hora['Data'] = pd.to_datetime(df_hora['Data'])
df_dia['Data'] = pd.to_datetime(df_dia['Data'])

# 2. Define os pesos e a função para a média móvel ponderada
window_size = 7
weights = np.arange(1, window_size + 1)
def weighted_moving_average(series):
    return series.rolling(window=window_size).apply(lambda x: np.average(x, weights=weights), raw=True)

# 3. Adiciona a coluna 'Dia_Semana' em português
dias_semana_map = {
    0: 'Segunda-feira', 1: 'Terça-feira', 2: 'Quarta-feira', 
    3: 'Quinta-feira', 4: 'Sexta-feira', 5: 'Sábado', 6: 'Domingo'
}
df_dia['Dia_Semana'] = df_dia['Data'].dt.dayofweek.map(dias_semana_map)
df_hora['Dia_Semana'] = df_hora['Data'].dt.dayofweek.map(dias_semana_map)


# --- Processamento para df_dia ---
print("Processando df_dia...")
# AGREGAÇÃO: Garante que há apenas uma linha por dia para que os cálculos de janela funcionem corretamente.
df_dia = df_dia.groupby(['Data', 'Dia_Semana']).agg({
    'Tx_Conversao': 'mean',
    'Visitas': 'sum',
    'Visistas_Engajadas': 'sum'
}).reset_index()
df_dia = df_dia.sort_values(by='Data').reset_index(drop=True)

# Média Ponderada dos últimos 7 dias
df_dia['Tx_Conversao_Ponderada'] = weighted_moving_average(df_dia['Tx_Conversao'])

# Mediana dos últimos 7 dias
df_dia['Tx_Conversao_Mediana_7D'] = df_dia['Tx_Conversao'].rolling(window=7).median()

# Média das últimas 4 semanas (mesmo dia da semana)
df_dia['Tx_Conversao_Media_4_Semanas'] = df_dia.groupby('Dia_Semana')['Tx_Conversao'].transform(lambda x: x.rolling(window=4).mean())


# --- Processamento para df_hora ---
print("Processando df_hora...")
df_hora = df_hora.sort_values(by=['Hora', 'Data']).reset_index(drop=True)

# Média Ponderada dos últimos 7 dias (por hora)
df_hora['Tx_Conversao_Ponderada'] = df_hora.groupby('Hora')['Tx_Conversao'].transform(weighted_moving_average)

# Mediana dos últimos 7 dias (por hora)
df_hora['Tx_Conversao_Mediana_7D'] = df_hora.groupby('Hora')['Tx_Conversao'].transform(lambda x: x.rolling(window=7).median())

# Média das últimas 4 semanas (mesmo dia da semana e hora)
df_hora['Tx_Conversao_Media_4_Semanas'] = df_hora.groupby(['Dia_Semana', 'Hora'])['Tx_Conversao'].transform(lambda x: x.rolling(window=4).mean())


# --- Reordenação e Exibição ---
df_hora = df_hora.sort_values(by=['Data', 'Hora']).reset_index(drop=True)

def categorizar_conversao(row):
    tx_conversao = row['Tx_Conversao']
    tx_ponderada = row['Tx_Conversao_Media_4_Semanas']

    # Lida com casos onde a média ponderada é nula ou zero para evitar divisão por zero
    if pd.isna(tx_ponderada) or tx_ponderada == 0:
        if tx_conversao > 0:
            return 'super acima intervalo' # Se a conversão é positiva e a média é zero, é um grande aumento
        else:
            return 'dentro intervalo' # Se ambos são zero, estão "iguais"

    ratio = tx_conversao / tx_ponderada

    if ratio > 1.5:
        return 'super acima intervalo'
    elif ratio > 1.0: # de 100% a 150%
        return 'acima intervalo'
    elif ratio >= 0.97: # de 97% a 100%
        return 'dentro intervalo'
    elif ratio >= 0.70: # de 70% a 97%
        return 'abaixo intervalo'
    else: # abaixo de 70%
        return 'super abaixo intervalo'

print("--- Categorização de Conversão para df_hora ---")
df_hora['Status_Conversao'] = df_hora.apply(categorizar_conversao, axis=1)

print("--- Categorização de Conversão para df_dia ---")
df_dia['Status_Conversao'] = df_dia.apply(categorizar_conversao, axis=1)

data_hoje = df_hora['Data'].max()
df_hoje_hora = df_hora[df_hora['Data'] == data_hoje].copy()
df_filtrado_hora = df_hoje_hora[df_hoje_hora['Tx_Conversao'] > 0]

if not df_filtrado_hora.empty:
    hora_maxima = df_filtrado_hora['Hora'].max()

    df_resultado_hora = df_filtrado_hora[df_filtrado_hora['Hora'] == hora_maxima]
else:
    
    df_resultado_hora = pd.DataFrame(columns=df_hora.columns)

df_resultado_hora['Tx_Conversao'] = df_resultado_hora['Tx_Conversao']/100


df_resultado_dia = df_dia[df_dia['Data']==data_hoje]
df_resultado_dia['Tx_Conversao'] = df_resultado_dia['Tx_Conversao']/100

import requests
import json

def enviar_mensagem_gchat(url_webhook, mensagem):
    """
    Envia uma mensagem simples para um espaço do Google Chat via Webhook.
    """
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = {'text': mensagem}
    try:
        resposta = requests.post(url_webhook, headers=headers, data=json.dumps(payload))
        resposta.raise_for_status()
        print("Mensagem enviada com sucesso!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem: {e}")

# URL do webhook do Google Chat
WEBHOOK_URL = "Inserir a sua webhook aqui"
# --- Lógica de Alerta ---

# Extrai o status de cada dataframe, tratando o caso de estarem vazios
status_hora = df_resultado_hora['Status_Conversao'].iloc[0] if not df_resultado_hora.empty else None
status_dia = df_resultado_dia['Status_Conversao'].iloc[0] if not df_resultado_dia.empty else None

# Define os status que disparam o alerta
status_alerta = ['abaixo intervalo', 'super abaixo intervalo']

# Verifica se algum dos status requer um alerta
if status_hora in status_alerta or status_dia in status_alerta:
    
    # Extrai os valores para a mensagem, tratando casos de dataframes vazios
    hora = df_resultado_hora['Hora'].iloc[0] if status_hora else "N/A"
    tx_hora = df_resultado_hora['Tx_Conversao'].iloc[0] if status_hora else 0
    tx_dia = df_resultado_dia['Tx_Conversao'].iloc[0] if status_dia else 0

    # Formata a mensagem
    MENSAGEM = (
        f"🔥🔥*ATENÇÃO ALERTA DE CONVERSÃO!!!*🔥🔥\n\n"
        f"Parcial das ({hora}h)\n"
        f"A conversão está em {tx_hora:.2%}.\n"
        f"No acumulado dia:\n" 
        f"A conversão está em {tx_dia:.2%}.\n"
        f"<users/all>"
    )

    # Envia a mensagem
    print("Enviando alerta para o Google Chat...")
    enviar_mensagem_gchat(WEBHOOK_URL, MENSAGEM)

else:
    print("Status de conversão dentro do normal. Nenhum alerta enviado.")

