"""
SICAR Package - Client for SICAR (Sistema de Cadastro Ambiental Rural).

Provides functionality to download shapefiles from the SICAR system.
"""

from src.infrastructure.sicar_package.SICAR import Sicar, State, Polygon
from src.infrastructure.sicar_package.SICAR.drivers import Tesseract

__all__ = ["Sicar", "State", "Polygon", "Tesseract"]
