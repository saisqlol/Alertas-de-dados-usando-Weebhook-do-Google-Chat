# Automações e Alertas para Power BI

Este repositório contém scripts Python que automatizam a extração de dados diretamente de conjuntos de dados do Power BI e do BigQuery. Após a extração, os scripts realizam transformações nos dados e verificam condições específicas para enviar alertas via webhook para o Google Chat.

## Scripts Principais

-   `main_aprovacao.py`: Extrai dados da **taxa de aprovação** do Power BI. O script processa essas informações e, caso a taxa de aprovação (parcial do dia ou acumulada) fique abaixo de um limite pré-definido, envia um alerta detalhado para o Google Chat.

-   `main_blogueiras.py`: Conecta-se ao BigQuery para validar as bases de comissionamento de **influenciadoras**. O script verifica a existência de duplicatas ou sobreposição de datas nas regras de comissão e, se encontrar erros, envia um alerta para o Google Chat com os detalhes dos problemas.

-   `main_conversao.py`: Extrai dados da **taxa de conversão** do Power BI. O script calcula métricas de acompanhamento (como média móvel ponderada) e, se a conversão estiver abaixo dos parâmetros esperados, dispara um alerta para o Google Chat.
