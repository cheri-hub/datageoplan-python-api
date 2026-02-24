# ====================================================================
# PROCESSADOR DE DADOS CAR - Versão API
# Processa shapefiles CAR em memória e gera shapefiles organizados com SLD
# ====================================================================

"""
PROCESSADOR DE DADOS CAR - Sistema de Processamento de Cadastro Ambiental Rural

Este módulo processa shapefiles CAR baixados do SICAR e gera uma estrutura
organizada de shapefiles com estilos SLD padronizados.

Uso na API:
    from src.services.car_processor import CarProcessor
    
    processor = CarProcessor()
    resultado = processor.processar_zip_bytes(zip_bytes)
"""

import io
import os
import glob
import tempfile
import shutil
import zipfile
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Any, Union

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, MultiPoint

from src.core.logging import get_logger
from src.infrastructure.sicar_package.car_reference import MODELO_CAR, buscar_tema
from src.infrastructure.sicar_package.sld_generator import criar_sld_para_tema

logger = get_logger(__name__)


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
# CLASSE PROCESSADOR CAR
# ====================================================================

class CarProcessor:
    """
    Processador de dados CAR.
    
    Processa shapefiles CAR baixados do SICAR e gera uma estrutura
    organizada de shapefiles com estilos SLD padronizados.
    """
    
    def __init__(self):
        """Inicializa o processador CAR."""
        self.temp_dirs: List[str] = []
    
    def __del__(self):
        """Limpa diretórios temporários ao destruir o objeto."""
        self._limpar_temp_dirs()
    
    def _limpar_temp_dirs(self):
        """Remove todos os diretórios temporários criados."""
        for temp_dir in self.temp_dirs:
            if os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as e:
                    logger.warning(f"Erro ao remover temp dir {temp_dir}: {e}")
        self.temp_dirs = []
    
    def _criar_temp_dir(self) -> str:
        """Cria e registra um diretório temporário."""
        temp_dir = tempfile.mkdtemp(prefix="car_processor_")
        self.temp_dirs.append(temp_dir)
        return temp_dir

    # ====================================================================
    # FUNÇÕES DE LEITURA DE SHAPEFILES
    # ====================================================================

    def encontrar_shapefiles_car(self, caminho_entrada: str) -> Dict[str, Any]:
        """
        Procura por shapefiles CAR.
        Suporta três formatos:
        1. ZIP principal contendo ZIPs internos
        2. Diretório com ZIPs
        3. Diretório com shapefiles soltos
        
        Args:
            caminho_entrada: Caminho do ZIP ou diretório
            
        Returns:
            Dicionário {nome_camada: caminho_para_ler}
        """
        shapefiles_encontrados = {}
        
        # CASO 1: ZIP PRINCIPAL (contém outros ZIPs dentro)
        if caminho_entrada.endswith('.zip') and os.path.isfile(caminho_entrada):
            logger.debug(f"Detectado ZIP principal: {os.path.basename(caminho_entrada)}")
            
            try:
                with zipfile.ZipFile(caminho_entrada, 'r') as zip_externo:
                    arquivos_internos = zip_externo.namelist()
                    zips_internos = [f for f in arquivos_internos if f.endswith('.zip')]
                    
                    if zips_internos:
                        logger.debug(f"Encontrados {len(zips_internos)} ZIP(s) interno(s)")
                        
                        for zip_interno_nome in zips_internos:
                            nome_base = os.path.basename(zip_interno_nome).replace('.zip', '')
                            
                            try:
                                zip_interno_bytes = zip_externo.read(zip_interno_nome)
                                zip_interno_io = io.BytesIO(zip_interno_bytes)
                                
                                with zipfile.ZipFile(zip_interno_io, 'r') as zip_interno:
                                    shapefiles_internos = [f for f in zip_interno.namelist() if f.endswith('.shp')]
                                    
                                    if shapefiles_internos:
                                        temp_dir = self._criar_temp_dir()
                                        zip_interno.extractall(temp_dir)
                                        
                                        shp_temp = os.path.join(temp_dir, shapefiles_internos[0])
                                        gdf = gpd.read_file(shp_temp, rows=1)
                                        campos = gdf.columns.tolist()
                                        
                                        if 'tema' not in campos or 'area' not in campos or 'recibo' not in campos:
                                            continue
                                        
                                        for nome_esperado in NOMES_CAMADAS_ESPERADAS:
                                            if nome_esperado == "MARCADORES_Area_de_Preservacao_Permanente":
                                                if "marcadores" in nome_base.lower():
                                                    shapefiles_encontrados[nome_esperado] = (caminho_entrada, zip_interno_nome)
                                                    break
                                            else:
                                                if nome_esperado.lower() in nome_base.lower() and "marcadores" not in nome_base.lower():
                                                    shapefiles_encontrados[nome_esperado] = (caminho_entrada, zip_interno_nome)
                                                    break
                                        
                            except Exception as e:
                                logger.warning(f"Erro ao processar {zip_interno_nome}: {str(e)}")
                                continue
                        
                        return shapefiles_encontrados
            
            except Exception as e:
                logger.error(f"Erro ao ler ZIP principal: {str(e)}")
                return shapefiles_encontrados
        
        # CASO 2: DIRETÓRIO COM ZIPs
        if os.path.isdir(caminho_entrada):
            pattern_zip = os.path.join(caminho_entrada, "*.zip")
            arquivos_zip = glob.glob(pattern_zip)
            
            if arquivos_zip:
                logger.debug(f"Encontrados {len(arquivos_zip)} arquivo(s) ZIP no diretório")
                
                for caminho_zip in arquivos_zip:
                    nome_zip = os.path.basename(caminho_zip).replace('.zip', '')
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
                    except Exception:
                        continue
                
                return shapefiles_encontrados
        
        # CASO 3: DIRETÓRIO COM SHAPEFILES SOLTOS
        if os.path.isdir(caminho_entrada):
            pattern_shp = os.path.join(caminho_entrada, "*.shp")
            arquivos_shp = glob.glob(pattern_shp)
            
            if arquivos_shp:
                logger.debug(f"Encontrados {len(arquivos_shp)} shapefile(s) solto(s)")
                
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
                    except Exception:
                        continue
        
        return shapefiles_encontrados

    # ====================================================================
    # FUNÇÕES DE PROCESSAMENTO
    # ====================================================================

    def ler_shapefile_de_zip_aninhado(self, zip_info: Union[str, Tuple[str, str]]) -> Optional[gpd.GeoDataFrame]:
        """
        Lê shapefile de dentro de um ZIP que está dentro de outro ZIP.
        
        Args:
            zip_info: Pode ser:
                - str: caminho direto (zip://... ou arquivo normal)
                - tuple: (zip_externo, zip_interno_nome) para ZIP aninhado
                
        Returns:
            GeoDataFrame ou None
        """
        # Se for string, é caminho direto
        if isinstance(zip_info, str):
            gdf = gpd.read_file(zip_info, encoding='utf-8')
            return gdf
        
        # Se for tupla, é ZIP aninhado
        if isinstance(zip_info, tuple):
            zip_externo_path, zip_interno_nome = zip_info
            
            temp_dir = self._criar_temp_dir()
            
            try:
                with zipfile.ZipFile(zip_externo_path, 'r') as zip_externo:
                    zip_interno_bytes = zip_externo.read(zip_interno_nome)
                    zip_interno_io = io.BytesIO(zip_interno_bytes)
                    
                    with zipfile.ZipFile(zip_interno_io, 'r') as zip_interno:
                        zip_interno.extractall(temp_dir)
                        
                        shp_files = glob.glob(os.path.join(temp_dir, "*.shp"))
                        
                        if not shp_files:
                            return None
                        
                        gdf = gpd.read_file(shp_files[0], encoding='utf-8')
                        return gdf
            
            except Exception as e:
                logger.error(f"Erro ao ler ZIP aninhado: {e}")
                return None
        
        return None

    def extrair_recibo_car(self, shapefiles_dict: Dict) -> str:
        """
        Extrai o código do recibo dos shapefiles CAR.
        
        Args:
            shapefiles_dict: Dicionário de shapefiles
            
        Returns:
            Código do recibo
        """
        for zip_info in shapefiles_dict.values():
            try:
                gdf = self.ler_shapefile_de_zip_aninhado(zip_info)
                
                if gdf is not None and not gdf.empty and 'recibo' in gdf.columns:
                    recibo = gdf.iloc[0]['recibo']
                    if recibo:
                        return str(recibo).strip()
            except Exception:
                continue
        
        return "CAR_Processado"

    def analisar_temas_presentes(self, shapefiles_dict: Dict) -> Dict[str, Dict]:
        """
        Analisa quais temas estão presentes nos shapefiles CAR.
        
        Args:
            shapefiles_dict: Dicionário de shapefiles
            
        Returns:
            Dicionário {tema_original: {info_tema, gdfs}}
        """
        temas_encontrados = defaultdict(lambda: {
            'info': None,
            'gdfs': []
        })
        
        temas_nao_reconhecidos = []
        
        for nome_camada, zip_info in shapefiles_dict.items():
            try:
                gdf = self.ler_shapefile_de_zip_aninhado(zip_info)
                
                if gdf is None:
                    continue
                
                for tema_original in gdf['tema'].unique():
                    if pd.isna(tema_original) or tema_original == '':
                        continue
                    
                    info_tema = buscar_tema(str(tema_original))
                    
                    if info_tema:
                        temas_encontrados[tema_original]['info'] = info_tema
                        gdf_tema = gdf[gdf['tema'] == tema_original].copy()
                        temas_encontrados[tema_original]['gdfs'].append(gdf_tema)
                    else:
                        if tema_original not in temas_nao_reconhecidos:
                            temas_nao_reconhecidos.append(tema_original)
            
            except Exception as e:
                logger.warning(f"Erro ao ler {nome_camada}: {str(e)}")
                continue
        
        if temas_nao_reconhecidos:
            logger.warning(f"{len(temas_nao_reconhecidos)} tema(s) não reconhecido(s)")
        
        return dict(temas_encontrados)

    def explodir_multipoint(self, gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
        """
        Explode geometrias MultiPoint em Points individuais.
        
        Args:
            gdf: GeoDataFrame com possíveis MultiPoints
            
        Returns:
            GeoDataFrame com apenas Points
        """
        tem_multipoint = gdf.geometry.apply(lambda g: isinstance(g, MultiPoint)).any()
        
        if not tem_multipoint:
            return gdf
        
        linhas_novas = []
        
        for idx, row in gdf.iterrows():
            geom = row.geometry
            
            if isinstance(geom, MultiPoint):
                for ponto in geom.geoms:
                    nova_linha = row.copy()
                    nova_linha.geometry = ponto
                    linhas_novas.append(nova_linha)
            else:
                linhas_novas.append(row)
        
        gdf_novo = gpd.GeoDataFrame(linhas_novas, crs=gdf.crs)
        return gdf_novo

    def processar_e_salvar_shapefile(
        self,
        tema_original: str,
        dados_tema: Dict,
        dir_classe: str
    ) -> Tuple[Optional[str], int, bool]:
        """
        Processa e salva um shapefile com seus dados.
        
        Args:
            tema_original: Tema original
            dados_tema: Dados do tema (info + gdfs)
            dir_classe: Diretório da classe
            
        Returns:
            Tupla (caminho_shp, num_feicoes, sucesso)
        """
        info_tema = dados_tema['info']
        gdfs_lista = dados_tema['gdfs']
        nome_arquivo = info_tema['arquivo_modelo']
        
        caminho_shp = os.path.join(dir_classe, f"{nome_arquivo}.shp")
        
        try:
            gdf_final = pd.concat(gdfs_lista, ignore_index=True)
            
            if gdf_final.crs is None:
                gdf_final.set_crs(CRS_PADRAO, inplace=True)
            elif gdf_final.crs.to_string() != CRS_PADRAO:
                gdf_final = gdf_final.to_crs(CRS_PADRAO)
            
            if info_tema['tipo'] == 'Point':
                gdf_final = self.explodir_multipoint(gdf_final)
            
            gdf_final = gdf_final[~gdf_final.geometry.is_empty]
            
            if len(gdf_final) == 0:
                return (None, 0, False)
            
            # Selecionar campos
            campos_base = ['recibo', 'area', 'tema', 'geometry']
            
            if "Area_do_Imovel" in nome_arquivo or "Area_Liquida" in nome_arquivo:
                campos_extras = []
                if 'modfiscais' in gdf_final.columns:
                    campos_extras.append('modfiscais')
                if 'municipio' in gdf_final.columns:
                    campos_extras.append('municipio')
                if 'estado' in gdf_final.columns:
                    campos_extras.append('estado')
                
                campos_base = campos_base[:-1] + campos_extras + ['geometry']
            
            campos_disponiveis = [c for c in campos_base if c in gdf_final.columns]
            gdf_final = gdf_final[campos_disponiveis]
            
            # Salvar shapefile
            gdf_final.to_file(caminho_shp, encoding='utf-8')
            
            # Detectar tipo de geometria real
            tipo_geom_real = gdf_final.geometry.iloc[0].geom_type
            
            info_tema_sld = info_tema.copy()
            
            if tipo_geom_real in ['Point', 'MultiPoint']:
                info_tema_sld['tipo'] = 'Point'
                
                if info_tema['tipo'] == 'Polygon':
                    tema_marcador = info_tema['tema_car'] + " - MARCADOR"
                    info_marcador = buscar_tema(tema_marcador)
                    
                    if info_marcador:
                        info_tema_sld['cor_preenchimento'] = info_marcador['cor_preenchimento']
                        info_tema_sld['cor_contorno'] = info_marcador['cor_contorno']
            
            elif tipo_geom_real in ['Polygon', 'MultiPolygon']:
                info_tema_sld['tipo'] = 'Polygon'
            
            # Criar arquivo SLD
            caminho_sld = caminho_shp.replace('.shp', '.sld')
            sld_content = criar_sld_para_tema(info_tema_sld)
            
            with open(caminho_sld, 'w', encoding='utf-8') as f:
                f.write(sld_content)
            
            return (caminho_shp, len(gdf_final), True)
            
        except Exception as e:
            logger.error(f"Erro ao processar {nome_arquivo}: {str(e)}")
            return (None, 0, False)

    # ====================================================================
    # FUNÇÕES PRINCIPAIS
    # ====================================================================

    def processar_car(
        self,
        diretorio_entrada: str,
        diretorio_saida: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Função principal que processa os shapefiles CAR.
        
        Args:
            diretorio_entrada: Caminho do diretório ou ZIP com shapefiles CAR
            diretorio_saida: Caminho do diretório de saída (opcional)
            
        Returns:
            Dicionário com resultado do processamento
        """
        resultado = {
            "sucesso": False,
            "recibo": None,
            "temas_processados": 0,
            "feicoes_total": 0,
            "arquivos_gerados": [],
            "erros": [],
            "diretorio_saida": None
        }
        
        # Validar entrada
        if not os.path.exists(diretorio_entrada):
            resultado["erros"].append(f"Caminho não encontrado: {diretorio_entrada}")
            return resultado
        
        if not (os.path.isdir(diretorio_entrada) or diretorio_entrada.endswith('.zip')):
            resultado["erros"].append("Caminho deve ser um diretório ou arquivo .zip")
            return resultado
        
        logger.info(f"Processando CAR de: {diretorio_entrada}")
        
        # 1. Encontrar shapefiles CAR
        shapefiles_dict = self.encontrar_shapefiles_car(diretorio_entrada)
        
        if not shapefiles_dict:
            resultado["erros"].append("Nenhum shapefile CAR encontrado")
            return resultado
        
        logger.info(f"Encontrados {len(shapefiles_dict)} camada(s) CAR")
        
        # 2. Extrair recibo
        if diretorio_entrada.endswith('.zip'):
            nome_zip = os.path.basename(diretorio_entrada).replace('.zip', '')
            if '-' in nome_zip and len(nome_zip) > 10:
                recibo = nome_zip
            else:
                recibo = self.extrair_recibo_car(shapefiles_dict)
        else:
            recibo = self.extrair_recibo_car(shapefiles_dict)
        
        resultado["recibo"] = recibo
        logger.info(f"Recibo CAR: {recibo}")
        
        # 3. Definir diretório de saída
        if diretorio_saida is None:
            diretorio_saida = os.path.join(os.path.dirname(diretorio_entrada), f"CAR_Processado_{recibo}")
        else:
            diretorio_saida = os.path.join(diretorio_saida, recibo)
        
        resultado["diretorio_saida"] = diretorio_saida
        
        # 4. Analisar temas presentes
        temas_presentes = self.analisar_temas_presentes(shapefiles_dict)
        
        if not temas_presentes:
            resultado["erros"].append("Nenhum tema reconhecido foi encontrado")
            return resultado
        
        logger.info(f"Identificados {len(temas_presentes)} tema(s) único(s)")
        
        # 5. Criar estrutura de diretórios
        if not os.path.exists(diretorio_saida):
            os.makedirs(diretorio_saida)
        
        temas_por_classe = defaultdict(list)
        for tema_original, dados in temas_presentes.items():
            info = dados['info']
            classe = info['classe']
            temas_por_classe[classe].append((tema_original, dados))
        
        # Ordenar classes pela ordem definida no MODELO_CAR
        classes_ordenadas = sorted(
            temas_por_classe.keys(),
            key=lambda c: MODELO_CAR.get(c, {}).get("ordem", 999)
        )
        
        # Mapear chave da classe para nome de pasta amigável (ex: "1-Area_do_Imovel")
        classe_para_pasta = {}
        for classe in classes_ordenadas:
            dados_classe = MODELO_CAR.get(classe, {})
            ordem = dados_classe.get("ordem", 99)
            nome_grupo = dados_classe.get("nome_grupo", classe)
            # Substituir espaços por underscores e remover acentos problemáticos para filesystem
            nome_pasta = nome_grupo.replace(" ", "_")
            classe_para_pasta[classe] = f"{ordem}-{nome_pasta}"
        
        for classe in classes_ordenadas:
            dir_classe = os.path.join(diretorio_saida, classe_para_pasta[classe])
            if not os.path.exists(dir_classe):
                os.makedirs(dir_classe)
        
        # 6. Processar e salvar shapefiles
        logger.info("Criando shapefiles...")
        
        for classe in classes_ordenadas:
            temas_lista = temas_por_classe[classe]
            dir_classe = os.path.join(diretorio_saida, classe_para_pasta[classe])
            
            for tema_original, dados in temas_lista:
                caminho_shp, num_feicoes, sucesso = self.processar_e_salvar_shapefile(
                    tema_original, dados, dir_classe
                )
                
                if sucesso:
                    resultado["temas_processados"] += 1
                    resultado["feicoes_total"] += num_feicoes
                    resultado["arquivos_gerados"].append(caminho_shp)
                else:
                    nome_arquivo = dados['info']['arquivo_modelo']
                    resultado["erros"].append(f"Erro ao processar: {nome_arquivo}")
        
        resultado["sucesso"] = resultado["temas_processados"] > 0
        
        logger.info(f"Processamento concluído: {resultado['temas_processados']} temas, {resultado['feicoes_total']} feições")
        
        return resultado

    def processar_zip_bytes(
        self,
        zip_bytes: bytes,
        include_sld: bool = True
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """
        Processa um ZIP CAR em bytes e retorna ZIP processado.
        
        Args:
            zip_bytes: Bytes do arquivo ZIP do SICAR
            include_sld: Se deve incluir arquivos SLD
            
        Returns:
            Tupla (bytes_zip_processado, nome_arquivo, resultado)
        """
        temp_entrada = self._criar_temp_dir()
        temp_saida = self._criar_temp_dir()
        
        try:
            # Salvar ZIP de entrada
            zip_entrada_path = os.path.join(temp_entrada, "input.zip")
            with open(zip_entrada_path, 'wb') as f:
                f.write(zip_bytes)
            
            # Processar
            resultado = self.processar_car(zip_entrada_path, temp_saida)
            
            if not resultado["sucesso"]:
                raise Exception(f"Erro no processamento: {resultado['erros']}")
            
            # Criar ZIP de saída
            output_buffer = io.BytesIO()
            
            with zipfile.ZipFile(output_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for arquivo_shp in resultado["arquivos_gerados"]:
                    # Adicionar todos arquivos do shapefile
                    base_path = arquivo_shp.replace('.shp', '')
                    base_name = os.path.basename(base_path)
                    
                    # Obter caminho relativo a partir do diretório de saída
                    rel_dir = os.path.dirname(arquivo_shp).replace(resultado["diretorio_saida"], "").lstrip(os.sep)
                    
                    for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
                        arquivo = base_path + ext
                        if os.path.exists(arquivo):
                            arcname = os.path.join(rel_dir, base_name + ext)
                            zip_out.write(arquivo, arcname)
                    
                    # Adicionar SLD se solicitado
                    if include_sld:
                        sld_path = base_path + '.sld'
                        if os.path.exists(sld_path):
                            arcname = os.path.join(rel_dir, base_name + '.sld')
                            zip_out.write(sld_path, arcname)
            
            output_buffer.seek(0)
            
            nome_arquivo = f"{resultado['recibo']}_processado.zip"
            
            return output_buffer.getvalue(), nome_arquivo, resultado
            
        finally:
            self._limpar_temp_dirs()
