# ====================================================================
# DICIONÁRIO DE REFERÊNCIA - MODELO CAR
# Mapeia todos os valores possíveis do campo "tema" para shapefiles modelo
# ====================================================================

"""
Este dicionário contém a estrutura completa do CAR com:
- Mapeamento de temas (valores do campo "tema") para nomes de arquivo
- Cores de preenchimento e contorno
- Tipo de geometria (Polygon ou Point)
- Organização em grupos hierárquicos

Uso:
    from modelo_car_referencia import MODELO_CAR, get_cor_tema
"""

# ====================================================================
# DICIONÁRIO PRINCIPAL - MODELO CAR
# ====================================================================

MODELO_CAR = {
    # ================================================================
    # GRUPO 7: RESUMO (aparece no final)
    # ================================================================
    "_Totalizadores": {
        "nome_grupo": "Resumo",
        "ordem": 7,
        "temas_possiveis": [
            {
                "tema_car": "APP Total",
                "arquivo_modelo": "APP_Total",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Reserva Legal Total",
                "arquivo_modelo": "Area_de_Reserva_Legal_Total",
                "cor_preenchimento": "#228b22",
                "cor_contorno": "#1a6b1a",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Servidão Administrativa Total",
                "arquivo_modelo": "Area_de_Servidao_Administrativa_Total",
                "cor_preenchimento": "#8e4d7d",
                "cor_contorno": "#8e4d7d",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Uso Restrito total",
                "arquivo_modelo": "Uso_Restrito_Total",
                "cor_preenchimento": "#ff8390",
                "cor_contorno": "#ff8390",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 1: ÁREA DO IMÓVEL
    # ================================================================
    "Area_do_Imovel": {
        "nome_grupo": "Área do Imóvel",
        "ordem": 1,
        "temas_possiveis": [
            {
                "tema_car": "Área do Imovel",
                "arquivo_modelo": "Area_do_Imovel",
                "cor_preenchimento": None,
                "cor_contorno": "#f8cd24",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Sede ou Ponto de Referência do Imóvel",
                "arquivo_modelo": "Sede_ou_Ponto_de_Referencia_do_Imovel",
                "cor_preenchimento": "#e5bd00",
                "cor_contorno": "#e5bd00",
                "tipo": "Point"
            },
            {
                "tema_car": "Área Líquida do Imóvel",
                "arquivo_modelo": "Area_Liquida_do_Imovel",
                "cor_preenchimento": "#868585",
                "cor_contorno": "#e1b816",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 6: ÁREA DE USO RESTRITO
    # ================================================================
    "Area_de_Uso_Restrito": {
        "nome_grupo": "Área de Uso Restrito",
        "ordem": 6,
        "temas_possiveis": [
            {
                "tema_car": "Área de Uso Restrito para declividade de 25 a 45 graus",
                "arquivo_modelo": "Area_de_Uso_Restrito_Declividade_25_a_45_graus",
                "cor_preenchimento": "#ffaab1",
                "cor_contorno": "#ffaab1",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Uso Restrito para regiões pantaneras",
                "arquivo_modelo": "Area_de_Uso_Restrito_Regioes_Pantaneras",
                "cor_preenchimento": "#ff606e",
                "cor_contorno": "#ff606e",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 2: SERVIDÃO ADMINISTRATIVA
    # ================================================================
    "Servidao_Administrativa": {
        "nome_grupo": "Servidão Administrativa",
        "ordem": 2,
        "temas_possiveis": [
            {
                "tema_car": "Infraestrutura Pública",
                "arquivo_modelo": "Infraestrutura_Publica",
                "cor_preenchimento": "#844646",
                "cor_contorno": "#844646",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Utilidade Pública",
                "arquivo_modelo": "Utilidade_Publica",
                "cor_preenchimento": "#9e5353",
                "cor_contorno": "#9e5353",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Reservatório para Abastecimento ou Geração de Energia",
                "arquivo_modelo": "Reservatorio_Abastecimento_ou_Geracao_Energia",
                "cor_preenchimento": "#7238ad",
                "cor_contorno": "#7238ad",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Entorno de Reservatório para Abastecimento ou Geração de Energia",
                "arquivo_modelo": "Entorno_Reservatorio_Abastecimento_ou_Geracao_Energia",
                "cor_preenchimento": "#ad389a",
                "cor_contorno": "#ad389a",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 3: COBERTURA DO SOLO
    # ================================================================
    "Cobertura_do_Solo": {
        "nome_grupo": "Cobertura do Solo",
        "ordem": 3,
        "temas_possiveis": [
            {
                "tema_car": "Área Consolidada",
                "arquivo_modelo": "Area_Consolidada",
                "cor_preenchimento": "#dddddd",
                "cor_contorno": "#dddddd",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Remanescente de Vegetação Nativa",
                "arquivo_modelo": "Remanescente_de_Vegetacao_Nativa",
                "cor_preenchimento": "#4fb370",
                "cor_contorno": "#059a37",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Pousio",
                "arquivo_modelo": "Area_de_Pousio",
                "cor_preenchimento": "#a0c49b",
                "cor_contorno": "#a0c49b",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área não Classificada",
                "arquivo_modelo": "Area_nao_Classificada",
                "cor_preenchimento": "#e0e0e0",
                "cor_contorno": "#b0b0b0",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 4: ÁREA DE PRESERVAÇÃO PERMANENTE
    # ================================================================
    "Area_de_Preservacao_Permanente": {
        "nome_grupo": "Área de Preservação Permanente",
        "ordem": 4,
        "temas_possiveis": [
            # GEOMETRIAS BASE (polígonos de referência)
            {
                "tema_car": "Curso d'água natural de até 10 metros",
                "arquivo_modelo": "Curso_dagua_natural_ate_10_metros",
                "cor_preenchimento": "#a0dcf1",
                "cor_contorno": "#a0dcf1",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Curso d'água natural de 10 a 50 metros",
                "arquivo_modelo": "Curso_dagua_natural_10_a_50_metros",
                "cor_preenchimento": "#7fb8ff",
                "cor_contorno": "#7fb8ff",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Curso d'água natural de 50 a 200 metros",
                "arquivo_modelo": "Curso_dagua_natural_50_a_200_metros",
                "cor_preenchimento": "#9696ff",
                "cor_contorno": "#9696ff",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Curso d'água natural de 200 a 600 metros",
                "arquivo_modelo": "Curso_dagua_natural_200_a_600_metros",
                "cor_preenchimento": "#5656ff",
                "cor_contorno": "#5656ff",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Curso d'água natural acima de 600 metros",
                "arquivo_modelo": "Curso_dagua_natural_acima_600_metros",
                "cor_preenchimento": "#0000ff",
                "cor_contorno": "#0000ff",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Lago ou lagoa natural",
                "arquivo_modelo": "Lago_ou_Lagoa_Natural",
                "cor_preenchimento": "#2892d3",
                "cor_contorno": "#93def5",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Nascente ou olho d'água perene",
                "arquivo_modelo": "Nascente_ou_Olho_dagua_Perene",
                "cor_preenchimento": "#2892d3",
                "cor_contorno": "#93def5",
                "tipo": "Point"
            },
            {
                "tema_car": "Reservatório artificial decorrente de barramento ou represamento de cursos d'água naturais",
                "arquivo_modelo": "Reservatorio_Artificial",
                "cor_preenchimento": "#258ac7",
                "cor_contorno": "#c7cacc",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Manguezal",
                "arquivo_modelo": "Manguezal",
                "cor_preenchimento": "#c4682b",
                "cor_contorno": "#c4682b",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Vereda",
                "arquivo_modelo": "Vereda",
                "cor_preenchimento": "#ff8a3d",
                "cor_contorno": "#ff8a3d",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Restinga",
                "arquivo_modelo": "Restinga",
                "cor_preenchimento": "#c49473",
                "cor_contorno": "#c49473",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área com altitude superior a 1.800 metros",
                "arquivo_modelo": "Area_Altitude_Superior_1800_metros",
                "cor_preenchimento": "#914d1f",
                "cor_contorno": "#914d1f",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de declividade maior que 45 graus",
                "arquivo_modelo": "Area_Declividade_Maior_45_graus",
                "cor_preenchimento": "#c49473",
                "cor_contorno": "#c49473",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Borda de chapada",
                "arquivo_modelo": "Borda_Chapada",
                "cor_preenchimento": "#ffc7a3",
                "cor_contorno": "#ffc7a3",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de topo de morro",
                "arquivo_modelo": "Area_Topo_Morro",
                "cor_preenchimento": "#ff9e5e",
                "cor_contorno": "#ff9e5e",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Reservatório de geração de energia elétrica construído até 24/08/2001",
                "arquivo_modelo": "Reservatorio_Geracao_Energia_Eletrica_ate_24082001",
                "cor_preenchimento": "#258ac7",
                "cor_contorno": "#f57337",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Banhado",
                "arquivo_modelo": "Banhado",
                "cor_preenchimento": "#55b7b7",
                "cor_contorno": "#55b7b7",
                "tipo": "Polygon"
            },
            
            # ÁREAS ANÁLISADAS PELO CAR (São geradas após o envio dos arquivos para o sistema do CAR)
            {
                "tema_car": "Área de Preservação Permanente em área antropizada não declarada como área consolidada",
                "arquivo_modelo": "APP_em_Area_Antropizada_nao_Declarada_Consolidada",
                "cor_preenchimento": "#fc2e01",
                "cor_contorno": "#fc2e01",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente em área consolidada",
                "arquivo_modelo": "APP_em_Area_Consolidada",
                "cor_preenchimento": "#831c00",
                "cor_contorno": "#160804",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente em área de Vegetação Nativa",
                "arquivo_modelo": "APP_em_Vegetacao_Nativa",
                "cor_preenchimento": "#9000ab",
                "cor_contorno": "#9000ab",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Rios até 10 metros",
                "arquivo_modelo": "APP_Rios_ate_10_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Rios de 10 até 50 metros",
                "arquivo_modelo": "APP_Rios_10_ate_50_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Rios de 50 até 200 metros",
                "arquivo_modelo": "APP_Rios_50_ate_200_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Rios de 200 até 600 metros",
                "arquivo_modelo": "APP_Rios_200_ate_600_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Rios com mais de 600 metros",
                "arquivo_modelo": "APP_Rios_mais_600_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Nascentes ou Olhos D'água Perenes",
                "arquivo_modelo": "APP_Nascentes_ou_Olhos_Dagua_Perenes",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Lagos e Lagoas Naturais",
                "arquivo_modelo": "APP_Lagos_e_Lagoas_Naturais",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Reservatório artificial decorrente de barramento de cursos d’água",
                "arquivo_modelo": "APP_Reservatorio_Artificial_Barramento",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Topos de Morro",
                "arquivo_modelo": "APP_Topo_Morro",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Manguezais",
                "arquivo_modelo": "APP_Manguezais",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Áreas com Altitude Superior a 1800 metros",
                "arquivo_modelo": "APP_Altitude_Superior_1800_metros",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Bordas de Chapada",
                "arquivo_modelo": "APP_Borda_Chapada",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Restingas",
                "arquivo_modelo": "APP_Restingas",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Áreas com Declividades Superiores a 45 graus",
                "arquivo_modelo": "APP_Declividade_Maior_45_graus",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Banhado",
                "arquivo_modelo": "APP_Banhado",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de Veredas",
                "arquivo_modelo": "APP_Veredas",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente de geração de energia elétrica construído até 24/08/2001",
                "arquivo_modelo": "APP_Reservatorio_Geracao_Eletrica_ate_24082001",
                "cor_preenchimento": "#fffb00",
                "cor_contorno": "#fffb00",
                "tipo": "Polygon"
            },
            
            # ÁREAS A RECOMPOR
            {
                "tema_car": "Área de Preservação Permanente a Recompor de Rios até 10 metros",
                "arquivo_modelo": "APP_a_Recompor_Rios_ate_10_metros",
                "cor_preenchimento": "#ffd700",
                "cor_contorno": "#ffa500",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente a Recompor de Rios de 10 até 50 metros",
                "arquivo_modelo": "APP_a_Recompor_Rios_10_ate_50_metros",
                "cor_preenchimento": "#ffd700",
                "cor_contorno": "#ffa500",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente a Recompor de Nascentes ou Olhos D'água Perenes",
                "arquivo_modelo": "APP_a_Recompor_Nascentes_ou_Olhos_Dagua_Perenes",
                "cor_preenchimento": "#ffd700",
                "cor_contorno": "#ffa500",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Área de Preservação Permanente a Recompor de Veredas",
                "arquivo_modelo": "APP_a_Recompor_Veredas",
                "cor_preenchimento": "#ffd700",
                "cor_contorno": "#ffa500",
                "tipo": "Polygon"
            },
            
            # ARTIGO 61-A
            {
                "tema_car": "APP segundo art. 61-A da Lei nº 12.651/2012",
                "arquivo_modelo": "APP_segundo_art_61A_Lei_12651_2012",
                "cor_preenchimento": "#e6ff00",
                "cor_contorno": "#ccdd00",
                "tipo": "Polygon"
            }
        ]
    },
    
    # ================================================================
    # GRUPO 5: RESERVA LEGAL
    # ================================================================
    "Reserva_Legal": {
        "nome_grupo": "Reserva Legal",
        "ordem": 5,
        "temas_possiveis": [
            {
                "tema_car": "Reserva Legal Proposta",
                "arquivo_modelo": "Reserva_Legal_Proposta",
                "cor_preenchimento": "#289926",
                "cor_contorno": "#50512c",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Reserva Legal Averbada",
                "arquivo_modelo": "Reserva_Legal_Averbada",
                "cor_preenchimento": "#289926",
                "cor_contorno": "#c84905",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Reserva Legal Aprovada e não Averbada",
                "arquivo_modelo": "Reserva_Legal_Aprovada_nao_Averbada",
                "cor_preenchimento": "#289926",
                "cor_contorno": "#61cf0b",
                "tipo": "Polygon"
            },
            {
                "tema_car": "Reserva legal vinculada à compensação de outro imóvel",
                "arquivo_modelo": "Reserva_Legal_Vinculada_Compensacao",
                "cor_preenchimento": "#9ef1b1",
                "cor_contorno": "#e3add6",
                "tipo": "Polygon"
            }
        ]
    }
}


# ====================================================================
# FUNÇÕES AUXILIARES
# ====================================================================


def criar_indice_busca():
    """
    Cria um índice invertido para busca rápida de temas.
    
    Returns:
        dict: Dicionário {tema: info_completa}
    """
    indice = {}
    
    for classe_nome, classe_dados in MODELO_CAR.items():
        for tema_info in classe_dados["temas_possiveis"]:
            indice[tema_info["tema_car"]] = {
                "classe": classe_nome,
                "nome_grupo": classe_dados["nome_grupo"],
                "ordem": classe_dados["ordem"],
                **tema_info
            }
    
    return indice

def buscar_tema(tema_original):
    """
    Busca informações sobre um tema no modelo CAR.
    
    Args:
        tema_original (str): Valor do campo "tema" do CAR
        
    Returns:
        dict ou None: Informações do tema ou None se não encontrado
    """
    indice = criar_indice_busca()
    return indice.get(tema_original)


def get_cor_tema(tema_original):
    """
    Retorna as cores de um tema.
    
    Args:
        tema_original (str): Valor do campo "tema" do CAR
        
    Returns:
        tuple: (cor_preenchimento, cor_contorno) ou (None, None)
    """
    info = buscar_tema(tema_original)
    if info:
        return (info["cor_preenchimento"], info["cor_contorno"])
    return (None, None)


def listar_todos_temas():
    """
    Lista todos os temas possíveis do modelo CAR.
    
    Returns:
        list: Lista de todos os temas cadastrados
    """
    temas = []
    for classe_dados in MODELO_CAR.values():
        for tema_info in classe_dados["temas_possiveis"]:
            temas.append(tema_info["tema_car"])
    return temas


def contar_temas():
    """
    Conta quantos temas existem no modelo.
    
    Returns:
        dict: Contagem por classe e total
    """
    contagem = {"total": 0}
    
    for classe_nome, classe_dados in MODELO_CAR.items():
        num_temas = len(classe_dados["temas_possiveis"])
        contagem[classe_nome] = num_temas
        contagem["total"] += num_temas
    
    return contagem