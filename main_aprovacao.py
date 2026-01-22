import pandas as pd
import os
import sys

current_dir = os.getcwd()
project_root = os.path.abspath(os.path.join(current_dir, '..'))
if project_root not in sys.path:
    sys.path.append(project_root)

from requisicao import df_dax_bi 
from querys import query_aprovacao_hora, query_aprovacao_dia
from params import DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page
import numpy as np

df_hora = df_dax_bi(query_aprovacao_hora, DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page)
df_dia = df_dax_bi(query_aprovacao_dia, DIRECTORY_ID, CLIENT_ID, CLIENT_SECRET, one_page)


df_dia = df_dia.rename(columns={
    'Base One Page[dia]': 'Data',
    '[Receita_Aprovada]': 'Receita_Aprovada',
    '[Receita_Captada]': 'Receita_Captada',
    '[Taxa_de_Aprovação]' : 'Aprovacao'
})

df_hora = df_hora.rename(columns={
    'Base One Page[dia]': 'Data',
    'Base One Page[hora]': 'Hora',
    '[Receita_Aprovada]': 'Receita_Aprovada',
    '[Receita_Captada]': 'Receita_Captada',
    '[Taxa_de_Aprovação]' : 'Aprovacao'
})

# Aplica a regra para criar a coluna 'estado' em ambos os DataFrames
df_hora['estado'] = np.where(df_hora['Aprovacao'] < 0.8, 'abaixo', 'ok')
df_dia['estado'] = np.where(df_dia['Aprovacao'] < 0.8, 'abaixo', 'ok')

data_hoje = df_hora['Data'].max()
df_hoje_hora = df_hora[df_hora['Data'] == data_hoje].copy()
df_filtrado_hora = df_hoje_hora[df_hoje_hora['Aprovacao'] > 0]

if not df_filtrado_hora.empty:
    hora_maxima = df_filtrado_hora['Hora'].max()
    df_resultado_hora = df_filtrado_hora[df_filtrado_hora['Hora'] == hora_maxima]
else:
    df_resultado_hora = pd.DataFrame(columns=df_hora.columns)

df_resultado_hora

df_resultado_dia = df_dia[df_dia['Data']==data_hoje]

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
status_hora = df_resultado_hora['estado'].iloc[0] if not df_resultado_hora.empty else None
status_dia = df_resultado_dia['estado'].iloc[0] if not df_resultado_dia.empty else None

# Define o status que dispara o alerta
status_alerta = 'abaixo'

# Verifica se algum dos status requer um alerta e se os dataframes não estão vazios
if (status_hora == status_alerta or status_dia == status_alerta) and not df_resultado_hora.empty and not df_resultado_dia.empty:
    
    # Extrai os valores para a mensagem
    hora = df_resultado_hora['Hora'].iloc[0]
    aprovacao_hora = df_resultado_hora['Aprovacao'].iloc[0]
    
    aprovacao_dia = df_resultado_dia['Aprovacao'].iloc[0]
    
    # Define a meta e calcula a diferença em pontos percentuais
    aprovacao_esperada = 0.80
    diff_hora = (aprovacao_hora - aprovacao_esperada) * 100
    diff_dia = (aprovacao_dia - aprovacao_esperada) * 100

    # Formata a mensagem
    MENSAGEM = (
        f"🔥🔥*ATENÇÃO ALERTA DE APROVAÇÃO!!!*🔥🔥\n\n"
        f"Parcial das {hora}h\n"
        f"Aprovação: {aprovacao_hora:.2%}\n"
        f"Aprovação esperada: {aprovacao_esperada:.2%} ({diff_hora:+.2f} p.p.)\n\n"
        f"Acumulado do dia:\n" 
        f"Aprovação: {aprovacao_dia:.2%}\n"
        f"Aprovação esperada: {aprovacao_esperada:.2%} ({diff_dia:+.2f} p.p.)\n\n"
        f"<users/all>"
    )

    # Envia a mensagem
    print("Enviando alerta para o Google Chat...")
    enviar_mensagem_gchat(WEBHOOK_URL, MENSAGEM)
    #print(MENSAGEM)
else:
    print("Taxa de aprovação dentro do normal ou dados insuficientes para alerta. Nenhum alerta enviado.")