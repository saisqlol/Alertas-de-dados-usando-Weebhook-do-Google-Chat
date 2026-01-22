
query_onepage = f"""
        DEFINE
            VAR Base = 
                FILTER(
                    KEEPFILTERS(
                        SUMMARIZECOLUMNS(
                            'Calendário'[Dia],
                            'Base One Page'[hora],
                            "Taxa_de_conversão", ('Medidas'[Taxa de conversão])*100,
                            "Visitas", 'Medidas'[Visitas],
                            "Visitas_Engajadas", 'Medidas'[Visitas Engajadas]
                        )
                    ),
                    [Visitas_Engajadas] <> 0
                )

        EVALUATE
            Base

        ORDER BY
            'Calendário'[Dia] DESC, 'Base One Page'[hora] DESC
            
    """

query_conversao_geral = f"""
        DEFINE
            VAR Base = 
                FILTER(
                    KEEPFILTERS(
                        SUMMARIZECOLUMNS(
                            'Calendário'[Dia],
                            "Taxa_de_conversão", ('Medidas'[Taxa de conversão])*100,
                            "Visitas", 'Medidas'[Visitas],
                            "Visitas_Engajadas", 'Medidas'[Visitas Engajadas]
                        )
                    ),
                    [Visitas_Engajadas] <> 0
                )

        EVALUATE
            Base

        ORDER BY
            'Calendário'[Dia] DESC
            
    """

query_aprovacao_hora = f"""
        DEFINE
            VAR Data_Min = 
            TODAY()-31
            VAR Filtro_Data = 
                FILTER(
                    KEEPFILTERS(VALUES('Base One Page'[dia])),
                        'Base One Page'[dia] >= DATE(YEAR(Data_Min), MONTH(Data_Min), DAY(Data_Min))
                )

            VAR Base = 
                SUMMARIZECOLUMNS(
                    'Base One Page'[dia], 
                    'Base One Page'[hora],
                    Filtro_Data,
                    "Receita_Aprovada", 'Medidas'[Receita Aprovada],
                    "Receita_Captada", 'Medidas'[Receita Captada],
                    "Taxa_de_Aprovação", 'Medidas'[Taxa de Aprovação]
                )

        EVALUATE
            Base

        ORDER BY
        'Base One Page'[dia] DESC, 'Base One Page'[hora] ASC



"""


query_aprovacao_dia = f"""
        DEFINE
            VAR Data_Min = 
            TODAY()-31
            VAR Filtro_Data = 
                FILTER(
                    KEEPFILTERS(VALUES('Base One Page'[dia])),
                        'Base One Page'[dia] >= DATE(YEAR(Data_Min), MONTH(Data_Min), DAY(Data_Min))
                )

            VAR Base = 
                SUMMARIZECOLUMNS(
                    'Base One Page'[dia], 
                    Filtro_Data,
                    "Receita_Aprovada", 'Medidas'[Receita Aprovada],
                    "Receita_Captada", 'Medidas'[Receita Captada],
                    "Taxa_de_Aprovação", 'Medidas'[Taxa de Aprovação]
                )

        EVALUATE
            Base

        ORDER BY
        'Base One Page'[dia] DESC



"""



query_comissao_influs = f""" 

    SELECT * FROM `epoca-230913.Google_Sheets.PB_Comissao`

    """

query_comissao_skus = f""" 

    SELECT * FROM `epoca-230913.Google_Sheets.SKU_Comissao` 

    """

query_comissao_familia  = f""" 

    SELECT * FROM `epoca-230913.Google_Sheets.Categoria_Comissao` 

    """

query_comissao_marca  = f""" 

    SELECT * FROM `epoca-230913.Google_Sheets.Marca_Comissao` 

    """

query_comissao_cupom  = f""" 

    SELECT * FROM `epoca-230913.Google_Sheets.Cupom_Comissao`

    """

