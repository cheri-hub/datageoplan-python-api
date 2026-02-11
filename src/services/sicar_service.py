"""
Serviço de integração com o SICAR.

Este módulo gerencia downloads diretos (streaming) do SICAR,
sem persistência em banco de dados.
"""

import os
import logging
import io
import time
import random
import base64
from typing import Tuple

from src.infrastructure.sicar_package.SICAR import Sicar, State, Polygon
from src.infrastructure.sicar_package.SICAR.drivers import Tesseract

# Configurar pytesseract para Windows
try:
    import pytesseract
    tesseract_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(tesseract_path):
        pytesseract.pytesseract.tesseract_cmd = tesseract_path
except ImportError:
    pass

logger = logging.getLogger(__name__)


class SicarService:
    """
    Serviço para download streaming de shapefiles do SICAR.
    
    Esta versão faz apenas streaming direto, sem persistência em banco.
    """

    def __init__(self, driver: str = "tesseract"):
        """
        Inicializa o serviço SICAR.
        
        Args:
            driver: Driver de OCR para captcha ("tesseract" ou "paddle")
        """
        # Por enquanto só suportamos Tesseract
        self.sicar = Sicar(driver=Tesseract)
        logger.debug(f"SicarService inicializado com driver: {driver}")

    def download_polygon_as_bytes(
        self,
        state: str,
        polygon: str
    ) -> Tuple[bytes, str]:
        """
        Baixa um polígono específico do SICAR e retorna os bytes do arquivo.
        
        Args:
            state: Sigla do estado (ex: "SP")
            polygon: Tipo de polígono (ex: "APPS", "AREA_PROPERTY")
            
        Returns:
            Tuple com (bytes do arquivo ZIP, nome do arquivo)
            
        Raises:
            Exception: Se o download falhar
        """
        import httpx
        from urllib.parse import urlencode
        
        logger.info(f"Iniciando download streaming: {state} - {polygon}")
        
        # Converter strings para enums
        state_enum = State[state.upper()]
        polygon_enum = Polygon[polygon.upper()]
        
        max_retries = 25
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Obter captcha
                captcha = self.sicar._driver.get_captcha(self.sicar._download_captcha())
                
                if len(captcha) != 5:
                    retry_count += 1
                    logger.debug(f"[{retry_count:02d}] Captcha inválido (tamanho {len(captcha)}): '{captcha}'")
                    time.sleep(random.random() + random.random())
                    continue
                
                logger.info(f"[{retry_count + 1:02d}/{max_retries}] Tentando com captcha: {captcha}")
                
                # Fazer download para bytes
                query = urlencode({
                    "idEstado": state_enum.value, 
                    "tipoBase": polygon_enum.value, 
                    "ReCaptcha": captcha
                })
                
                url = f"{self.sicar._DOWNLOAD_BASE}?{query}"
                logger.debug(f"URL de download: {url}")
                
                with self.sicar._session.stream("GET", url) as response:
                    status_code = response.status_code
                    content_type = response.headers.get("Content-Type", "")
                    content_length = int(response.headers.get("Content-Length", 0))
                    
                    logger.debug(f"Response: status={status_code}, content_type={content_type}, length={content_length}")
                    
                    if status_code != httpx.codes.OK:
                        raise Exception(f"HTTP {status_code}")
                    
                    if content_length == 0:
                        raise Exception("Content-Length é 0 (captcha provavelmente incorreto)")
                    
                    if not content_type.startswith("application/zip"):
                        raise Exception(f"Content-Type inválido: {content_type}")
                    
                    # Ler todos os bytes
                    buffer = io.BytesIO()
                    for chunk in response.iter_bytes():
                        buffer.write(chunk)
                    
                    file_bytes = buffer.getvalue()
                    filename = f"{state_enum.value}_{polygon_enum.value}.zip"
                    
                    logger.info(f"Download streaming concluído: {filename} ({len(file_bytes)} bytes)")
                    return file_bytes, filename
                    
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"[{retry_count:02d}] Erro: {e}")
                time.sleep(random.random() + random.random())
        
        raise Exception(f"Download falhou após {max_retries} tentativas: {last_error}")

    def download_car_as_bytes(
        self,
        car_number: str
    ) -> Tuple[bytes, str]:
        """
        Baixa shapefile de uma propriedade pelo CAR e retorna os bytes do arquivo.
        
        Args:
            car_number: Número do CAR (ex: "SP-3538709-4861E981046E49BC81720C879459E554")
            
        Returns:
            Tuple com (bytes do arquivo ZIP, nome do arquivo)
            
        Raises:
            Exception: Se o download falhar
        """
        import httpx
        
        logger.info(f"Iniciando download streaming CAR: {car_number}")
        
        # Buscar propriedade para obter internal_id
        property_data = self.sicar.search_by_car_number(car_number)
        internal_id = property_data.get("id")
        
        if not internal_id:
            raise Exception(f"Internal ID não encontrado para CAR: {car_number}")
        
        logger.info(f"Internal ID encontrado: {internal_id}")
        
        max_retries = 25
        retry_count = 0
        last_error = None
        
        while retry_count < max_retries:
            try:
                # Obter captcha
                captcha = self.sicar._driver.get_captcha(self.sicar._download_captcha())
                
                if len(captcha) != 5:
                    retry_count += 1
                    logger.debug(f"[{retry_count:02d}] Captcha inválido (tamanho {len(captcha)}): '{captcha}'")
                    time.sleep(random.random() + random.random())
                    continue
                
                logger.info(f"[{retry_count + 1:02d}/{max_retries}] Tentando com captcha: {captcha}")
                
                # Fazer download
                response = self.sicar._session.post(
                    f"{self.sicar._BASE}/imoveis/exportShapeFile",
                    data={
                        "idImovel": internal_id,
                        "ReCaptcha": captcha
                    }
                )
                
                status_code = response.status_code
                content_type = response.headers.get("Content-Type", "")
                content_length = len(response.content)
                
                logger.debug(f"Response: status={status_code}, content_type={content_type}, length={content_length}")
                
                if status_code != httpx.codes.OK:
                    raise Exception(f"HTTP {status_code}")
                
                # Verificar se resposta é base64
                content = response.content
                if response.text.startswith("data:application/zip;base64,"):
                    base64_data = response.text.split(",", 1)[1]
                    content = base64.b64decode(base64_data)
                    logger.info(f"Resposta em base64 decodificada: {len(content)} bytes")
                
                # Verificar se é um arquivo válido
                if "application/zip" in content_type or "application/octet-stream" in content_type or len(content) > 1000:
                    file_bytes = content
                    safe_car = car_number.replace("-", "_").replace("/", "_")
                    filename = f"{safe_car}.zip"
                    
                    logger.info(f"Download streaming CAR concluído: {filename} ({len(file_bytes)} bytes)")
                    return file_bytes, filename
                else:
                    raise Exception(f"Resposta inválida: content_type={content_type}, length={len(content)}")
                    
            except Exception as e:
                retry_count += 1
                last_error = e
                logger.warning(f"[{retry_count:02d}] Erro: {e}")
                time.sleep(random.random() + random.random())
        
        raise Exception(f"Download CAR falhou após {max_retries} tentativas: {last_error}")

    def download_and_process_state(
        self,
        state: str,
        polygon: str,
        include_sld: bool = True
    ) -> Tuple[bytes, str, dict]:
        """
        Baixa e processa shapefile de um estado, retornando dados organizados.
        
        Args:
            state: Sigla do estado (ex: "SP")
            polygon: Tipo de polígono (ex: "AREA_PROPERTY")
            include_sld: Se deve incluir arquivos SLD
            
        Returns:
            Tuple com (bytes do ZIP processado, nome do arquivo, resultado)
            
        Raises:
            Exception: Se o download ou processamento falhar
        """
        from src.services.car_processor import CarProcessor
        
        logger.info(f"Iniciando download + processamento: {state} - {polygon}")
        
        # 1. Baixar do SICAR
        zip_bytes, _ = self.download_polygon_as_bytes(state, polygon)
        
        # 2. Processar
        processor = CarProcessor()
        processed_bytes, filename, resultado = processor.processar_zip_bytes(
            zip_bytes,
            include_sld=include_sld
        )
        
        logger.info(f"Processamento concluído: {resultado['temas_processados']} temas")
        
        return processed_bytes, filename, resultado

    def download_and_process_car(
        self,
        car_number: str,
        include_sld: bool = True
    ) -> Tuple[bytes, str, dict]:
        """
        Baixa e processa shapefile de CAR, retornando dados organizados.
        
        Args:
            car_number: Número do CAR
            include_sld: Se deve incluir arquivos SLD
            
        Returns:
            Tuple com (bytes do ZIP processado, nome do arquivo, resultado)
            
        Raises:
            Exception: Se o download ou processamento falhar
        """
        from src.services.car_processor import CarProcessor
        
        logger.info(f"Iniciando download + processamento CAR: {car_number}")
        
        # 1. Baixar do SICAR
        zip_bytes, _ = self.download_car_as_bytes(car_number)
        
        # 2. Processar
        processor = CarProcessor()
        processed_bytes, filename, resultado = processor.processar_zip_bytes(
            zip_bytes,
            include_sld=include_sld
        )
        
        # Usar o recibo do CAR no nome do arquivo
        if resultado.get("recibo"):
            filename = f"{resultado['recibo']}_processado.zip"
        else:
            safe_car = car_number.replace("-", "_").replace("/", "_")
            filename = f"{safe_car}_processado.zip"
        
        logger.info(f"Processamento CAR concluído: {resultado['temas_processados']} temas, {resultado['feicoes_total']} feições")
        
        return processed_bytes, filename, resultado


# Polígonos disponíveis para documentação
AVAILABLE_POLYGONS = [
    "AREA_PROPERTY",      # Área do Imóvel
    "APPS",               # Áreas de Preservação Permanente
    "NATIVE_VEGETATION",  # Vegetação Nativa
    "HYDROGRAPHY",        # Hidrografia
    "LEGAL_RESERVE",      # Reserva Legal
    "RESTRICTED_USE",     # Uso Restrito
    "CONSOLIDATED_AREA",  # Área Consolidada
    "ADMINISTRATIVE_SERVICE",  # Servidão Administrativa
    "AREA_FALL",          # Área de Pousio
]

# Estados disponíveis
AVAILABLE_STATES = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO",
    "MA", "MT", "MS", "MG", "PA", "PB", "PR", "PE", "PI",
    "RJ", "RN", "RS", "RO", "RR", "SC", "SP", "SE", "TO"
]
