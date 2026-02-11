# ====================================================================
# GERADOR DE ARQUIVOS SLD (Styled Layer Descriptor)
# Gera estilos SLD 1.1.0 compatíveis com QGIS e GeoServer
# ====================================================================

"""
Módulo para geração de arquivos SLD (Styled Layer Descriptor).

Este módulo gera arquivos SLD 1.1.0 compatíveis com:
- QGIS
- GeoServer
- MapServer
- Outros clientes OGC

Uso:
    from src.infrastructure.sicar_package.sld_generator import criar_sld_polygon, criar_sld_point
"""

from typing import Tuple, Optional


def hex_para_rgb(hex_color: Optional[str]) -> Tuple[int, int, int]:
    """
    Converte cor hexadecimal para RGB (0-255).
    
    Args:
        hex_color: Cor em formato hexadecimal (#RRGGBB)
        
    Returns:
        Tupla (R, G, B) em valores 0-255
    """
    if hex_color is None:
        return (0, 0, 0)
    
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def criar_sld_polygon(
    nome_arquivo: str,
    cor_preenchimento: Optional[str],
    cor_contorno: str,
    opacidade: float = 0.7
) -> str:
    """
    Cria arquivo SLD 1.1.0 para polígonos (compatível com QGIS e GeoServer).
    
    Args:
        nome_arquivo: Nome da camada
        cor_preenchimento: Cor hex de preenchimento (ou None para transparente)
        cor_contorno: Cor hex do contorno
        opacidade: Opacidade do preenchimento (0.0 a 1.0)
        
    Returns:
        Conteúdo XML do SLD
    """
    if cor_preenchimento is None:
        # Sem preenchimento (apenas contorno)
        fill_xml = '''<se:Fill>
              <se:SvgParameter name="fill-opacity">0.0</se:SvgParameter>
            </se:Fill>'''
    else:
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


def criar_sld_point(
    nome_arquivo: str,
    cor_preenchimento: Optional[str],
    cor_contorno: str,
    tamanho: int = 3
) -> str:
    """
    Cria arquivo SLD 1.1.0 para pontos (compatível com QGIS e GeoServer).
    
    Args:
        nome_arquivo: Nome da camada
        cor_preenchimento: Cor hex de preenchimento
        cor_contorno: Cor hex do contorno
        tamanho: Tamanho do ponto em pixels
        
    Returns:
        Conteúdo XML do SLD
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


def criar_sld_para_tema(info_tema: dict) -> str:
    """
    Cria SLD baseado nas informações do tema.
    
    Args:
        info_tema: Dicionário com informações do tema (arquivo_modelo, cor_*, tipo)
        
    Returns:
        Conteúdo XML do SLD
    """
    nome_arquivo = info_tema['arquivo_modelo']
    tipo = info_tema.get('tipo', 'Polygon')
    
    if tipo == 'Point':
        return criar_sld_point(
            nome_arquivo,
            info_tema.get('cor_preenchimento'),
            info_tema['cor_contorno'],
            tamanho=3
        )
    else:
        return criar_sld_polygon(
            nome_arquivo,
            info_tema.get('cor_preenchimento'),
            info_tema['cor_contorno'],
            opacidade=0.7
        )


def gerar_sld_por_nome(nome_tema: str) -> Optional[str]:
    """
    Gera SLD para um tema pelo nome do arquivo modelo.
    
    Args:
        nome_tema: Nome do arquivo modelo (ex: "Area_do_Imovel")
        
    Returns:
        Conteúdo XML do SLD ou None se tema não encontrado
    """
    from src.infrastructure.sicar_package.car_reference import MODELO_CAR
    
    # Buscar tema pelo arquivo_modelo
    for classe_dados in MODELO_CAR.values():
        for tema_info in classe_dados["temas_possiveis"]:
            if tema_info["arquivo_modelo"] == nome_tema:
                return criar_sld_para_tema(tema_info)
    
    return None
