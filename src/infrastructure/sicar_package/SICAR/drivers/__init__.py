"""Drivers."""

from .captcha import Captcha
from .tesseract import Tesseract

try:
    from .paddle import Paddle
except ImportError:
    pass
