import pandas as pd
import os
import sys
import datetime
import numpy as np
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = r'chave.json'
from google.cloud import bigquery
from querys import query_comissao_familia, query_comissao_cupom, query_comissao_influs, query_comissao_marca, query_comissao_skus


def Base_BQ(query):

    client = bigquery.Client()
    query_job = client.query(query)
    df= query_job.result().to_dataframe()
    return df

comissao_categoria = Base_BQ(query_comissao_familia)
comissao_cupom = Base_BQ(query_comissao_cupom)
comissao_influenciador = Base_BQ(query_comissao_influs)
comissao_marca = Base_BQ(query_comissao_marca)
comissao_skus = Base_BQ(query_comissao_skus)

# Lista de DataFrames para processar
dataframes_para_converter = {
    "comissao_skus": comissao_skus,
    "comissao_categoria": comissao_categoria,
    "comissao_marca": comissao_marca
}

# Loop para converter as colunas de data em cada DataFrame
for nome, df in dataframes_para_converter.items():
    if 'Data_Inicio' in df.columns:
        df['Data_Inicio'] = pd.to_datetime(df['Data_Inicio'], dayfirst=True, errors='coerce')
    if 'Data_Fim' in df.columns:
        df['Data_Fim'] = pd.to_datetime(df['Data_Fim'], dayfirst=True, errors='coerce')
    print(f"Colunas de data em '{nome}' convertidas.")

# Exemplo de verificação
print("\nTipos de dados em comissao_skus após a conversão:")
comissao_skus.info()


# --- VALIDAÇÃO DE DUPLICATAS E SOBREPOSIÇÕES ---
import requests
import json

print("Iniciando a verificação de erros nas bases de comissão...")

# --- 0. Função de Envio para o Google Chat ---
def enviar_mensagem_gchat(url_webhook, mensagem):
    """
    Envia uma mensagem simples para um espaço do Google Chat via Webhook.
    """
    headers = {'Content-Type': 'application/json; charset=UTF-8'}
    payload = {'text': mensagem}
    try:
        resposta = requests.post(url_webhook, headers=headers, data=json.dumps(payload))
        resposta.raise_for_status()
        print("Mensagem de erro enviada com sucesso para o Google Chat!")
    except requests.exceptions.RequestException as e:
        print(f"Erro ao enviar mensagem para o Google Chat: {e}")

# --- 1. Lógica para Sobreposição de Datas ---
def find_date_overlaps(df, group_col, start_col='Data_Inicio', end_col='Data_Fim'):
    """
    Encontra sobreposições de períodos de data dentro de grupos de um DataFrame.
    Retorna um DataFrame com os pares de linhas que se sobrepõem.
    """
    if df.empty or group_col not in df.columns or start_col not in df.columns or end_col not in df.columns:
        return pd.DataFrame()
    
    df_copy = df.reset_index().rename(columns={'index': 'original_index'})
    merged = pd.merge(df_copy, df_copy, on=group_col, suffixes=('_1', '_2'))
    merged = merged[merged['original_index_1'] < merged['original_index_2']]
    
    overlap_condition = (merged[start_col + '_1'] <= merged[end_col + '_2']) & \
                        (merged[end_col + '_1'] >= merged[start_col + '_2'])
    
    overlapping_pairs = merged[overlap_condition]
    return overlapping_pairs

# --- Verificações ---
erros_encontrados = {}

# Categoria
overlaps_categoria_pairs = find_date_overlaps(comissao_categoria, 'Categoria')
if not overlaps_categoria_pairs.empty:
    # Define a data específica da exceção
    data_excecao = pd.to_datetime('2025-11-26')
    # Condição para a exceção: Categoria é PERFUMES e uma das datas de fim é a data de exceção
    excecao_condition = (overlaps_categoria_pairs['Categoria'] == 'PERFUMES') & \
                        ((overlaps_categoria_pairs['Data_Fim_1'] == data_excecao) | \
                         (overlaps_categoria_pairs['Data_Fim_2'] == data_excecao))
    
    # Filtra para manter apenas os erros que NÃO são a exceção
    erros_reais_categoria = overlaps_categoria_pairs[~excecao_condition]
    
    if not erros_reais_categoria.empty:
        # Coleta os IDs únicos das linhas com sobreposição real
        ids_erro = pd.unique(erros_reais_categoria[['original_index_1', 'original_index_2']].values.ravel('K'))
        erros_encontrados['Sobreposição em Categorias'] = comissao_categoria.iloc[ids_erro].sort_values(by=['Categoria', 'Data_Inicio'])

# Marca
overlaps_marca_pairs = find_date_overlaps(comissao_marca, 'Marca')
if not overlaps_marca_pairs.empty:
    ids_erro = pd.unique(overlaps_marca_pairs[['original_index_1', 'original_index_2']].values.ravel('K'))
    erros_encontrados['Sobreposição em Marcas'] = comissao_marca.iloc[ids_erro].sort_values(by=['Marca', 'Data_Inicio'])

# SKUs
if 'sku' in comissao_skus.columns and 'Sku' not in comissao_skus.columns:
    comissao_skus = comissao_skus.rename(columns={'sku': 'Sku'})
overlaps_skus_pairs = find_date_overlaps(comissao_skus, 'Sku')
if not overlaps_skus_pairs.empty:
    ids_erro = pd.unique(overlaps_skus_pairs[['original_index_1', 'original_index_2']].values.ravel('K'))
    erros_encontrados['Sobreposição em SKUs'] = comissao_skus.iloc[ids_erro].sort_values(by=['Sku', 'Data_Inicio'])

# Influenciador
dups_influ = comissao_influenciador[comissao_influenciador.duplicated(subset=['Source_Unificada'], keep=False)]
if not dups_influ.empty:
    erros_encontrados['Duplicatas em Influenciadores'] = dups_influ.sort_values('Source_Unificada')

# Cupom
dups_cupom = comissao_cupom[comissao_cupom.duplicated(subset=['Cupom'], keep=False)]
if not dups_cupom.empty:
    erros_encontrados['Duplicatas em Cupons'] = dups_cupom.sort_values('Cupom')

# --- 3. Lógica de Alerta para o Google Chat ---
if erros_encontrados:
    WEBHOOK_URL = "Inserir a sua webhook aqui"
    mensagem_partes = ["🛡️*ATENÇÃO: ERRO NA BASE DE COMISSÃO!!!*🛡️\n\nForam encontrados os seguintes problemas:\n"]
    
    for nome_erro, df_erro in erros_encontrados.items():
        mensagem_partes.append(f"\n*{nome_erro}:*\n")
        # Formata o DataFrame como texto, limitando o número de linhas para não poluir o chat
        df_texto = df_erro.to_string(index=False, max_rows=10)
        mensagem_partes.append(f"```{df_texto}```")

    mensagem_partes.append("\n<users/all>")
    MENSAGEM = "\n".join(mensagem_partes)
    
    print("Enviando alerta de erro para o Google Chat...")
    enviar_mensagem_gchat(WEBHOOK_URL, MENSAGEM)
else:
    print("\n✅ Nenhuma duplicata ou sobreposição encontrada em todas as bases.")