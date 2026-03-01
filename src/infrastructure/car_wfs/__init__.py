"""
Cliente WFS para consulta de imóveis rurais no GeoServer do SICAR.
"""

from src.infrastructure.car_wfs.client import CarWfsClient

__all__ = [
    "CarWfsClient",
]
