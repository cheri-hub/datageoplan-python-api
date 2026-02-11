# ====================================================================
# PROCESSADOR DE DADOS CAR - Versão Geopandas
# Lê shapefiles CAR do disco e gera shapefiles modelo organizados com SLD
# ====================================================================

"""
PROCESSADOR DE DADOS CAR - Sistema de Processamento de Cadastro Ambiental Rural

Este script processa shapefiles CAR baixados do SICAR e gera uma estrutura
organizada de shapefiles com estilos SLD padronizados.

USO:
    python processar_car.py <caminho_pasta_car> [caminho_saida]
    
EXEMPLO:
    python processar_car.py C:/Downloads/CAR_12345
    python processar_car.py C:/Downloads/CAR_12345 E:/Saida/CAR_Processado

REQUISITOS:
    - Python 3.9+
    - geopandas
    - shapely
    - pandas
"""

import os
import sys
import glob
from collections import defaultdict
import geopandas as gpd
from shapely.geometry import Point, MultiPoint
import pandas as pd


# ====================================================================
# CONFIGURAÇÕES
# ====================================================================

# CRS padrão (SIRGAS 2000)
CRS_PADRAO = "EPSG:4674"

# Nomes esperados das camadas CAR
NOMES_CAMADAS_ESPERADAS = [
    "MARCADORES_Area_de_Preservacao_Permanente",
    "Area_de_Preservacao_Permanente",
    "Area_do_Imovel",
    "Cobertura_do_Solo",
    "Reserva_Legal",
    "Servidao_Administrativa",
    "Area_de_Uso_Restrito"
]


# ====================================================================
# IMPORTAR MODELO DE REFERÊNCIA
# ====================================================================

try:
    from modelo_car_referencia import MODELO_CAR, buscar_tema
except ImportError:
    print("ERRO: Não foi possível importar 'modelo_car_referencia.py'")
    print("Certifique-se de que o arquivo está no mesmo diretório ou no PYTHONPATH")
    sys.exit(1)


# ====================================================================
# FUNÇÕES DE GERAÇÃO DE SLD
# ====================================================================

def hex_para_rgb(hex_color):
    """
    Converte cor hexadecimal para RGB (0-255).
    
    Args:
        hex_color (str): Cor em formato hexadecimal (#RRGGBB)
        
    Returns:
        tuple: (R, G, B) em valores 0-255
    """
    if hex_color is None:
        return (0, 0, 0)
    
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def criar_sld_polygon(nome_arquivo, cor_preenchimento, cor_contorno, opacidade=0.7):
    """
    Cria arquivo SLD 1.1.0 para polígonos (compatível com QGIS e Geoserver).
    
    Args:
        nome_arquivo (str): Nome da camada
        cor_preenchimento (str): Cor hex de preenchimento (ou None para transparente)
        cor_contorno (str): Cor hex do contorno
        opacidade (float): Opacidade do preenchimento (0.0 a 1.0)
        
    Returns:
        str: Conteúdo XML do SLD
    """
    # Converter cores para RGB
    rgb_contorno = hex_para_rgb(cor_contorno)
    
    if cor_preenchimento is None:
        # Sem preenchimento (apenas contorno)
        fill_xml = '''<se:Fill>
              <se:SvgParameter name="fill-opacity">0.0</se:SvgParameter>
            </se:Fill>'''
    else:
        rgb_preench = hex_para_rgb(cor_preenchimento)
        fill_xml = f'''<se:Fill>
              <se:SvgParameter name="fill">#{cor_preenchimento.lstrip('#')}</se:SvgParameter>
              <se:SvgParameter name="fill-opacity">{opacidade}</se:SvgParameter>
            </se:Fill>'''
    
    sld = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:se="http://www.opengis.net/se" version="1.1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ogc="http://www.opengis.net/ogc" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <se:Name>{nome_arquivo}</se:Name>
    <UserStyle>
      <se:Name>{nome_arquivo}</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name>Single symbol</se:Name>
          <se:PolygonSymbolizer>
            {fill_xml}
            <se:Stroke>
              <se:SvgParameter name="stroke">#{cor_contorno.lstrip('#')}</se:SvgParameter>
              <se:SvgParameter name="stroke-width">0.8</se:SvgParameter>
            </se:Stroke>
          </se:PolygonSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    return sld




def criar_sld_point(nome_arquivo, cor_preenchimento, cor_contorno, tamanho=3):
    """
    Cria arquivo SLD 1.1.0 para pontos (compatível com QGIS e Geoserver).
    
    Args:
        nome_arquivo (str): Nome da camada
        cor_preenchimento (str): Cor hex de preenchimento
        cor_contorno (str): Cor hex do contorno
        tamanho (int): Tamanho do ponto em pixels
        
    Returns:
        str: Conteúdo XML do SLD
    """
    cor_fill = cor_preenchimento if cor_preenchimento else cor_contorno
    
    sld = f'''<?xml version="1.0" encoding="UTF-8"?>
<StyledLayerDescriptor xmlns="http://www.opengis.net/sld" xmlns:se="http://www.opengis.net/se" version="1.1.0" xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:ogc="http://www.opengis.net/ogc" xsi:schemaLocation="http://www.opengis.net/sld http://schemas.opengis.net/sld/1.1.0/StyledLayerDescriptor.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <NamedLayer>
    <se:Name>{nome_arquivo}</se:Name>
    <UserStyle>
      <se:Name>{nome_arquivo}</se:Name>
      <se:FeatureTypeStyle>
        <se:Rule>
          <se:Name>Single symbol</se:Name>
          <se:PointSymbolizer>
            <se:Graphic>
              <se:Mark>
                <se:WellKnownName>circle</se:WellKnownName>
                <se:Fill>
                  <se:SvgParameter name="fill">#{cor_fill.lstrip('#')}</se:SvgParameter>
                </se:Fill>
                <se:Stroke>
                  <se:SvgParameter name="stroke">#{cor_contorno.lstrip('#')}</se:SvgParameter>
                  <se:SvgParameter name="stroke-width">1.5</se:SvgParameter>
                </se:Stroke>
              </se:Mark>
              <se:Size>{tamanho}</se:Size>
            </se:Graphic>
          </se:PointSymbolizer>
        </se:Rule>
      </se:FeatureTypeStyle>
    </UserStyle>
  </NamedLayer>
</StyledLayerDescriptor>'''
    
    return sld




def salvar_sld(caminho_shp, info_tema):
    """
    Salva arquivo SLD para o shapefile.
    
    Args:
        caminho_shp (str): Caminho do shapefile
        info_tema (dict): Informações do tema
    """
    caminho_sld = caminho_shp.replace('.shp', '.sld')
    nome_arquivo = info_tema['arquivo_modelo']
    
    if info_tema['tipo'] == 'Polygon':
        sld_content = criar_sld_polygon(
            nome_arquivo,
            info_tema['cor_preenchimento'],
            info_tema['cor_contorno'],
            opacidade=0.7
        )
    else:  # Point
        sld_content = criar_sld_point(
            nome_arquivo,
            info_tema['cor_preenchimento'],
            info_tema['cor_contorno'],
            tamanho=3
        )
    
    with open(caminho_sld, 'w', encoding='utf-8') as f:
        f.write(sld_content)


# ====================================================================
# FUNÇÕES DE LEITURA DE SHAPEFILES
# ====================================================================

def encontrar_shapefiles_car(caminho_entrada):
    """
    Procura por shapefiles CAR.
    Suporta três formatos:
    1. ZIP principal contendo ZIPs internos (ex: GO-123.zip contém Area_do_Imovel.zip)
    2. Diretório com ZIPs (ex: pasta com Area_do_Imovel.zip, Cobertura_do_Solo.zip)
    3. Diretório com shapefiles soltos (ex: pasta com Area_do_Imovel.shp)
    
    Args:
        caminho_entrada (str): Caminho do ZIP principal, diretório com ZIPs, ou diretório com shapefiles
        
    Returns:
        dict: {nome_camada: caminho_para_ler}
    """
    import zipfile
    
    shapefiles_encontrados = {}
    
    # ============================================================
    # CASO 1: ZIP PRINCIPAL (contém outros ZIPs dentro)
    # ============================================================
    if caminho_entrada.endswith('.zip') and os.path.isfile(caminho_entrada):
        print(f"Detectado ZIP principal: {os.path.basename(caminho_entrada)}")
        
        try:
            with zipfile.ZipFile(caminho_entrada, 'r') as zip_externo:
                # Listar arquivos dentro do ZIP principal
                arquivos_internos = zip_externo.namelist()
                
                # Buscar ZIPs internos
                zips_internos = [f for f in arquivos_internos if f.endswith('.zip')]
                
                if zips_internos:
                    print(f"Encontrados {len(zips_internos)} ZIP(s) interno(s)")
                    
                    # Processar cada ZIP interno
                    for zip_interno_nome in zips_internos:
                        nome_base = os.path.basename(zip_interno_nome).replace('.zip', '')
                        
                        # Caminho para ler: zip://zip_externo!zip_interno!shapefile.shp
                        # Formato especial para ZIP dentro de ZIP
                        caminho_zip_interno = f"zip://{caminho_entrada}!{zip_interno_nome}"
                        
                        try:
                            # Tentar ler o ZIP interno para listar shapefiles
                            # Precisamos extrair temporariamente ou ler de forma diferente
                            # Geopandas não suporta ZIP dentro de ZIP diretamente
                            
                            # Extrair ZIP interno em memória
                            zip_interno_bytes = zip_externo.read(zip_interno_nome)
                            
                            # Criar ZIP temporário em memória
                            import io
                            zip_interno_io = io.BytesIO(zip_interno_bytes)
                            
                            with zipfile.ZipFile(zip_interno_io, 'r') as zip_interno:
                                # Buscar .shp dentro do ZIP interno
                                shapefiles_internos = [f for f in zip_interno.namelist() if f.endswith('.shp')]
                                
                                if shapefiles_internos:
                                    # Pegar o primeiro .shp (normalmente só tem um)
                                    shp_nome = shapefiles_internos[0]
                                    
                                    # Para ler, vamos precisar extrair temporariamente
                                    # Ou salvar em temp e ler
                                    # Por enquanto, vamos criar um caminho especial
                                    
                                    # Validar lendo algumas linhas
                                    import tempfile
                                    import shutil
                                    
                                    # Criar diretório temporário
                                    temp_dir = tempfile.mkdtemp()
                                    
                                    try:
                                        # Extrair todos arquivos do ZIP interno para temp
                                        zip_interno.extractall(temp_dir)
                                        
                                        # Caminho do shapefile extraído
                                        shp_temp = os.path.join(temp_dir, shp_nome)
                                        
                                        # Ler para validar
                                        gdf = gpd.read_file(shp_temp, rows=1)
                                        campos = gdf.columns.tolist()
                                        
                                        # Verificar campos essenciais
                                        if 'tema' not in campos or 'area' not in campos or 'recibo' not in campos:
                                            shutil.rmtree(temp_dir)
                                            continue
                                        
                                        # Identificar tipo de camada
                                        for nome_esperado in NOMES_CAMADAS_ESPERADAS:
                                            if nome_esperado == "MARCADORES_Area_de_Preservacao_Permanente":
                                                if "marcadores" in nome_base.lower():
                                                    # Guardar caminho: (zip_externo, zip_interno_nome)
                                                    shapefiles_encontrados[nome_esperado] = (caminho_entrada, zip_interno_nome)
                                                    break
                                            else:
                                                if nome_esperado.lower() in nome_base.lower() and "marcadores" not in nome_base.lower():
                                                    shapefiles_encontrados[nome_esperado] = (caminho_entrada, zip_interno_nome)
                                                    break
                                        
                                        # Limpar temp
                                        shutil.rmtree(temp_dir)
                                        
                                    except Exception as e:
                                        # Limpar temp em caso de erro
                                        if os.path.exists(temp_dir):
                                            shutil.rmtree(temp_dir)
                                        raise e
                                        
                        except Exception as e:
                            print(f"  AVISO: Erro ao processar {zip_interno_nome}: {str(e)}")
                            continue
                    
                    return shapefiles_encontrados
        
        except Exception as e:
            print(f"ERRO ao ler ZIP principal: {str(e)}")
            return shapefiles_encontrados
    
    # ============================================================
    # CASO 2: DIRETÓRIO COM ZIPs (sem ZIP principal)
    # ============================================================
    if os.path.isdir(caminho_entrada):
        pattern_zip = os.path.join(caminho_entrada, "*.zip")
        arquivos_zip = glob.glob(pattern_zip)
        
        if arquivos_zip:
            print(f"Encontrados {len(arquivos_zip)} arquivo(s) ZIP no diretório")
            
            for caminho_zip in arquivos_zip:
                nome_zip = os.path.basename(caminho_zip).replace('.zip', '')
                
                # Construir caminho para ler shapefile dentro do ZIP
                caminho_shp_zip = f"zip://{caminho_zip}!{nome_zip}.shp"
                
                try:
                    gdf = gpd.read_file(caminho_shp_zip, rows=1)
                    campos = gdf.columns.tolist()
                    
                    if 'tema' not in campos or 'area' not in campos or 'recibo' not in campos:
                        continue
                    
                    for nome_esperado in NOMES_CAMADAS_ESPERADAS:
                        if nome_esperado == "MARCADORES_Area_de_Preservacao_Permanente":
                            if "marcadores" in nome_zip.lower():
                                shapefiles_encontrados[nome_esperado] = caminho_shp_zip
                                break
                        else:
                            if nome_esperado.lower() in nome_zip.lower() and "marcadores" not in nome_zip.lower():
                                shapefiles_encontrados[nome_esperado] = caminho_shp_zip
                                break
                except Exception as e:
                    continue
            
            return shapefiles_encontrados
    
    # ============================================================
    # CASO 3: DIRETÓRIO COM SHAPEFILES SOLTOS
    # ============================================================
    if os.path.isdir(caminho_entrada):
        pattern_shp = os.path.join(caminho_entrada, "*.shp")
        arquivos_shp = glob.glob(pattern_shp)
        
        if arquivos_shp:
            print(f"Encontrados {len(arquivos_shp)} shapefile(s) solto(s)")
            
            for caminho_shp in arquivos_shp:
                nome_arquivo = os.path.basename(caminho_shp).replace('.shp', '')
                
                try:
                    gdf = gpd.read_file(caminho_shp, rows=1)
                    campos = gdf.columns.tolist()
                    
                    if 'tema' not in campos or 'area' not in campos or 'recibo' not in campos:
                        continue
                    
                    for nome_esperado in NOMES_CAMADAS_ESPERADAS:
                        if nome_esperado == "MARCADORES_Area_de_Preservacao_Permanente":
                            if "marcadores" in nome_arquivo.lower():
                                shapefiles_encontrados[nome_esperado] = caminho_shp
                                break
                        else:
                            if nome_esperado.lower() in nome_arquivo.lower() and "marcadores" not in nome_arquivo.lower():
                                shapefiles_encontrados[nome_esperado] = caminho_shp
                                break
                except Exception as e:
                    continue
    
    return shapefiles_encontrados


# ====================================================================
# FUNÇÕES DE PROCESSAMENTO
# ====================================================================

# ====================================================================
# FUNÇÕES DE PROCESSAMENTO
# ====================================================================

def ler_shapefile_de_zip_aninhado(zip_info):
    """
    Lê shapefile de dentro de um ZIP que está dentro de outro ZIP.
    
    Args:
        zip_info: Pode ser:
            - str: caminho direto (zip://... ou arquivo normal)
            - tuple: (zip_externo, zip_interno_nome) para ZIP aninhado
            
    Returns:
        GeoDataFrame ou None
    """
    import zipfile
    import tempfile
    import shutil
    
    # Se for string, é caminho direto
    if isinstance(zip_info, str):
        # Forçar encoding UTF-8
        gdf = gpd.read_file(zip_info, encoding='utf-8')
        return gdf
    
    # Se for tupla, é ZIP aninhado
    if isinstance(zip_info, tuple):
        zip_externo_path, zip_interno_nome = zip_info
        
        temp_dir = tempfile.mkdtemp()
        
        try:
            # Abrir ZIP externo
            with zipfile.ZipFile(zip_externo_path, 'r') as zip_externo:
                # Extrair ZIP interno
                zip_interno_bytes = zip_externo.read(zip_interno_nome)
                
                # Abrir ZIP interno em memória
                import io
                zip_interno_io = io.BytesIO(zip_interno_bytes)
                
                with zipfile.ZipFile(zip_interno_io, 'r') as zip_interno:
                    # Extrair todos arquivos para temp
                    zip_interno.extractall(temp_dir)
                    
                    # Encontrar o .shp
                    shp_files = glob.glob(os.path.join(temp_dir, "*.shp"))
                    
                    if not shp_files:
                        return None
                    
                    # Ler shapefile com encoding UTF-8
                    gdf = gpd.read_file(shp_files[0], encoding='utf-8')
                    
                    return gdf
        
        finally:
            # Limpar temp
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
    
    return None


def extrair_recibo_car(shapefiles_dict):
    """
    Extrai o código do recibo dos shapefiles CAR.
    Funciona com shapefiles soltos, em ZIP, ou em ZIP aninhado.
    
    Args:
        shapefiles_dict (dict): Dicionário de shapefiles
        
    Returns:
        str: Código do recibo
    """
    for zip_info in shapefiles_dict.values():
        try:
            gdf = ler_shapefile_de_zip_aninhado(zip_info)
            
            if gdf is not None and not gdf.empty and 'recibo' in gdf.columns:
                recibo = gdf.iloc[0]['recibo']
                if recibo:
                    return str(recibo).strip()
        except:
            continue
    
    return "CAR_Processado"


def analisar_temas_presentes(shapefiles_dict):
    """
    Analisa quais temas estão presentes nos shapefiles CAR.
    Funciona com shapefiles soltos, em ZIP, ou em ZIP aninhado.
    
    Args:
        shapefiles_dict (dict): Dicionário de shapefiles (podem ser caminhos ou tuplas)
        
    Returns:
        dict: {tema_original: {info_tema, gdfs}}
    """
    temas_encontrados = defaultdict(lambda: {
        'info': None,
        'gdfs': []
    })
    
    temas_nao_reconhecidos = []
    
    for nome_camada, zip_info in shapefiles_dict.items():
        try:
            # Ler shapefile (suporta todos os formatos)
            gdf = ler_shapefile_de_zip_aninhado(zip_info)
            
            if gdf is None:
                continue
            
            # Agrupar por tema
            for tema_original in gdf['tema'].unique():
                if pd.isna(tema_original) or tema_original == '':
                    continue
                
                info_tema = buscar_tema(str(tema_original))
                
                if info_tema:
                    temas_encontrados[tema_original]['info'] = info_tema
                    # Filtrar GeoDataFrame por tema
                    gdf_tema = gdf[gdf['tema'] == tema_original].copy()
                    temas_encontrados[tema_original]['gdfs'].append(gdf_tema)
                else:
                    if tema_original not in temas_nao_reconhecidos:
                        temas_nao_reconhecidos.append(tema_original)
        
        except Exception as e:
            print(f"AVISO: Erro ao ler {nome_camada}: {str(e)}")
            continue
    
    # Avisar sobre temas não reconhecidos
    if temas_nao_reconhecidos:
        print(f"AVISO: {len(temas_nao_reconhecidos)} tema(s) não reconhecido(s):")
        for tema in temas_nao_reconhecidos[:5]:
            print(f"  - {tema}")
        if len(temas_nao_reconhecidos) > 5:
            print(f"  ... e mais {len(temas_nao_reconhecidos) - 5} tema(s)")
    
    return dict(temas_encontrados)


def explodir_multipoint(gdf):
    """
    Explode geometrias MultiPoint em Points individuais.
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame com possíveis MultiPoints
        
    Returns:
        GeoDataFrame: GeoDataFrame com apenas Points
    """
    # Verificar se há MultiPoints
    tem_multipoint = gdf.geometry.apply(lambda g: isinstance(g, MultiPoint)).any()
    
    if not tem_multipoint:
        return gdf
    
    # Explodir MultiPoints
    linhas_novas = []
    
    for idx, row in gdf.iterrows():
        geom = row.geometry
        
        if isinstance(geom, MultiPoint):
            # Explodir cada ponto do MultiPoint
            for ponto in geom.geoms:
                nova_linha = row.copy()
                nova_linha.geometry = ponto
                linhas_novas.append(nova_linha)
        else:
            linhas_novas.append(row)
    
    # Criar novo GeoDataFrame
    gdf_novo = gpd.GeoDataFrame(linhas_novas, crs=gdf.crs)
    
    return gdf_novo


def processar_e_salvar_shapefile(tema_original, dados_tema, dir_classe):
    """
    Processa e salva um shapefile com seus dados.
    
    Args:
        tema_original (str): Tema original
        dados_tema (dict): Dados do tema (info + gdfs)
        dir_classe (str): Diretório da classe
        
    Returns:
        tuple: (caminho_shp, num_feicoes, sucesso)
    """
    info_tema = dados_tema['info']
    gdfs_lista = dados_tema['gdfs']
    nome_arquivo = info_tema['arquivo_modelo']
    
    # Caminho do shapefile
    caminho_shp = os.path.join(dir_classe, f"{nome_arquivo}.shp")
    
    try:
        # Concatenar todos os GeoDataFrames deste tema
        gdf_final = pd.concat(gdfs_lista, ignore_index=True)
        
        # Garantir CRS correto
        if gdf_final.crs is None:
            gdf_final.set_crs(CRS_PADRAO, inplace=True)
        elif gdf_final.crs.to_string() != CRS_PADRAO:
            gdf_final = gdf_final.to_crs(CRS_PADRAO)
        
        # Explodir MultiPoint se necessário
        if info_tema['tipo'] == 'Point':
            gdf_final = explodir_multipoint(gdf_final)
        
        # Remover geometrias vazias
        gdf_final = gdf_final[~gdf_final.geometry.is_empty]
        
        if len(gdf_final) == 0:
            return (None, 0, False)
        
        # Selecionar apenas campos necessários
        campos_base = ['recibo', 'area', 'tema', 'geometry']
        
        # Campos extras para Área do Imóvel
        if "Area_do_Imovel" in nome_arquivo or "Area_Liquida" in nome_arquivo:
            campos_extras = []
            if 'modfiscais' in gdf_final.columns:
                campos_extras.append('modfiscais')
            if 'municipio' in gdf_final.columns:
                campos_extras.append('municipio')
            if 'estado' in gdf_final.columns:
                campos_extras.append('estado')
            
            campos_base = campos_base[:-1] + campos_extras + ['geometry']
        
        # Filtrar campos disponíveis
        campos_disponiveis = [c for c in campos_base if c in gdf_final.columns]
        gdf_final = gdf_final[campos_disponiveis]
        
        # Salvar shapefile
        gdf_final.to_file(caminho_shp, encoding='utf-8')
        
        # CORREÇÃO: Detectar tipo de geometria REAL para gerar SLD correto
        # (o modelo pode ter tipo errado - ex: modelo diz Polygon mas dados são Point)
        tipo_geom_real = gdf_final.geometry.iloc[0].geom_type
        
        # Criar cópia do info_tema para não modificar o original
        info_tema_sld = info_tema.copy()
        
        # Sobrescrever tipo com a geometria real
        if tipo_geom_real in ['Point', 'MultiPoint']:
            info_tema_sld['tipo'] = 'Point'
            
            # Se o modelo tinha tipo Polygon, buscar versão MARCADOR para pegar cores corretas
            if info_tema['tipo'] == 'Polygon':
                tema_marcador = info_tema['tema_car'] + " - MARCADOR"
                info_marcador = buscar_tema(tema_marcador)
                
                if info_marcador:
                    # Usar cores do MARCADOR
                    info_tema_sld['cor_preenchimento'] = info_marcador['cor_preenchimento']
                    info_tema_sld['cor_contorno'] = info_marcador['cor_contorno']
                    print(f"  → Usando cores do tema MARCADOR: {tema_marcador}")
        
        elif tipo_geom_real in ['Polygon', 'MultiPolygon']:
            info_tema_sld['tipo'] = 'Polygon'
        
        # Criar arquivo SLD com o tipo correto
        salvar_sld(caminho_shp, info_tema_sld)
        
        return (caminho_shp, len(gdf_final), True)
        
    except Exception as e:
        print(f"ERRO ao processar {nome_arquivo}: {str(e)}")
        return (None, 0, False)


# ====================================================================
# FUNÇÃO PRINCIPAL
# ====================================================================

def processar_car(diretorio_entrada, diretorio_saida=None):
    """
    Função principal que processa os shapefiles CAR.
    
    Args:
        diretorio_entrada (str): Caminho do diretório contendo os shapefiles CAR
        diretorio_saida (str): Caminho do diretório de saída (opcional)
        
    Returns:
        bool: True se processamento foi bem-sucedido, False caso contrário
    """
    
    # Validar entrada
    if not os.path.exists(diretorio_entrada):
        print(f"ERRO: Caminho não encontrado: {diretorio_entrada}")
        return False
    
    # Aceita tanto diretório quanto arquivo .zip
    if not (os.path.isdir(diretorio_entrada) or diretorio_entrada.endswith('.zip')):
        print(f"ERRO: Caminho deve ser um diretório ou arquivo .zip")
        return False
    
    print(f"Processando CAR de: {diretorio_entrada}")
    
    # 1. Encontrar shapefiles CAR
    shapefiles_dict = encontrar_shapefiles_car(diretorio_entrada)
    
    if not shapefiles_dict:
        print("ERRO: Nenhum shapefile CAR encontrado no diretório")
        print("Certifique-se de que:")
        print("  - Os arquivos .zip contêm shapefiles CAR válidos, OU")
        print("  - Os shapefiles .shp estão soltos no diretório")
        print("  - Os shapefiles têm os campos: recibo, tema, area")
        return False
    
    print(f"Encontrados {len(shapefiles_dict)} camada(s) CAR")
    
    # 2. Extrair recibo
    # Tentar extrair do nome do arquivo ZIP primeiro (se for .zip)
    if diretorio_entrada.endswith('.zip'):
        nome_zip = os.path.basename(diretorio_entrada).replace('.zip', '')
        # Se o nome do ZIP parece ser um recibo (tem hífens e letras/números)
        if '-' in nome_zip and len(nome_zip) > 10:
            recibo = nome_zip
            print(f"Recibo CAR (do nome do ZIP): {recibo}")
        else:
            # Se não, extrair dos dados
            recibo = extrair_recibo_car(shapefiles_dict)
            print(f"Recibo CAR (dos dados): {recibo}")
    else:
        recibo = extrair_recibo_car(shapefiles_dict)
        print(f"Recibo CAR: {recibo}")
    
    # 3. Definir diretório de saída
    if diretorio_saida is None:
        diretorio_saida = os.path.join(os.path.dirname(diretorio_entrada), f"CAR_Processado_{recibo}")
    else:
        diretorio_saida = os.path.join(diretorio_saida, recibo)
    
    # 4. Analisar temas presentes
    temas_presentes = analisar_temas_presentes(shapefiles_dict)
    
    if not temas_presentes:
        print("ERRO: Nenhum tema reconhecido foi encontrado")
        return False
    
    print(f"Identificados {len(temas_presentes)} tema(s) único(s)")
    
    # 5. Criar estrutura de diretórios
    if not os.path.exists(diretorio_saida):
        os.makedirs(diretorio_saida)
    
    # Organizar temas por classe
    temas_por_classe = defaultdict(list)
    for tema_original, dados in temas_presentes.items():
        info = dados['info']
        classe = info['classe']
        temas_por_classe[classe].append((tema_original, dados))
    
    # Criar subdiretórios
    for classe in temas_por_classe.keys():
        dir_classe = os.path.join(diretorio_saida, classe)
        if not os.path.exists(dir_classe):
            os.makedirs(dir_classe)
    
    # 6. Processar e salvar shapefiles
    print("Criando shapefiles...")
    
    total_criados = 0
    total_feicoes = 0
    erros = []
    
    for classe, temas_lista in temas_por_classe.items():
        dir_classe = os.path.join(diretorio_saida, classe)
        
        for tema_original, dados in temas_lista:
            caminho_shp, num_feicoes, sucesso = processar_e_salvar_shapefile(
                tema_original, dados, dir_classe
            )
            
            if sucesso:
                total_criados += 1
                total_feicoes += num_feicoes
            else:
                nome_arquivo = dados['info']['arquivo_modelo']
                erros.append(nome_arquivo)
    
    # 7. Relatório final
    print("\n" + "="*60)
    print("PROCESSAMENTO CONCLUÍDO")
    print("="*60)
    print(f"Recibo CAR: {recibo}")
    print(f"Shapefiles criados: {total_criados}")
    print(f"Feições processadas: {total_feicoes}")
    print(f"Localização: {diretorio_saida}")
    
    if erros:
        print(f"\nAVISO: {len(erros)} shapefile(s) com erro:")
        for erro in erros[:5]:
            print(f"  - {erro}")
        if len(erros) > 5:
            print(f"  ... e mais {len(erros) - 5}")
    
    print("="*60)
    
    return True


# ====================================================================
# EXECUÇÃO
# ====================================================================

def main():
    """
    Função principal de execução via linha de comando.
    """
    # Verificar argumentos
    if len(sys.argv) < 2:
        print("USO: python processar_car.py <caminho_zip_ou_pasta> [caminho_saida]")
        print("\nEXEMPLOS:")
        print("  # ZIP principal contendo ZIPs internos:")
        print('  python processar_car.py "E:/CAR/GO-5221601-353F4B24CB594EF483B4914C7CC0BEBB.zip"')
        print()
        print("  # Pasta com ZIPs:")
        print('  python processar_car.py "C:/Downloads/CAR_ZIPs"')
        print()
        print("  # Pasta com shapefiles soltos:")
        print('  python processar_car.py "C:/Downloads/CAR_Shapefiles"')
        sys.exit(1)
    
    # Normalizar caminhos (aceita barras invertidas do Windows)
    diretorio_entrada = os.path.normpath(sys.argv[1])
    diretorio_saida = os.path.normpath(sys.argv[2]) if len(sys.argv) > 2 else None
    
    # Processar CAR
    sucesso = processar_car(diretorio_entrada, diretorio_saida)
    
    # Sair com código apropriado
    sys.exit(0 if sucesso else 1)


if __name__ == "__main__":
    main()