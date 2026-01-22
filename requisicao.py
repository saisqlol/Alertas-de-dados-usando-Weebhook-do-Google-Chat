import requests
import json
import pandas as pd

def df_dax_bi(query, directory_id, client_id, client_secret, dataset_id):

    auth_url = f'https://login.microsoftonline.com/{directory_id}/oauth2/v2.0/token'
    auth_payload = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret,
        'scope': 'https://analysis.windows.net/powerbi/api/.default'
    }

    auth_response = requests.post(auth_url, data=auth_payload)


    if auth_response.status_code != 200:
        print("Erro na autenticação:")
        print(auth_response.json())
        return 0

    access_token = auth_response.json()['access_token']
    print("Autenticação bem-sucedida!")
    

    dax_api_url = f'https://api.powerbi.com/v1.0/myorg/datasets/{dataset_id}/executeQueries'

    dax_query =  query

    query_payload = {
        'queries': [
            {
                'query': dax_query
            }
        ],
        'serializerSettings': {
            'includeNulls': True
        }
    }

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    api_response = requests.post(dax_api_url, data=json.dumps(query_payload), headers=headers,verify=False)
    print(api_response.status_code)

    if api_response.status_code == 200:

        results = api_response.json()
        try:
            rows = results['results'][0]['tables'][0]['rows']
            if not rows:
                print("A consulta não retornou nenhuma linha.")
            df = pd.DataFrame(rows)
            print(df)
            return df
        except (KeyError, IndexError) as e:
            print("\n--- ERRO AO PROCESSAR OS DADOS ---")
            print("A resposta da API não continha a estrutura de dados esperada.")
            print(f"Erro de parsing: {e}")
            print("Resposta completa da API:")
            print(results)
            return 0

    else:
        print(f"Status Code: {api_response.status_code}")
        print("Resposta do Servidor:")
        print(api_response.text)
        return 0