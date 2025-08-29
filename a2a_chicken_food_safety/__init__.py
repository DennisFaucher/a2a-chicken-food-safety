"""
A2A Chicken Food Safety System

A complete Agent-to-Agent system for checking if foods are safe for chickens.
Implements the standard A2A HTTPS protocol with JSON messaging.
"""

__version__ = "0.1.0"
__author__ = "User"
__email__ = "user@example.com"

from .server import app as server_app
from .client import ChickenFoodSafetyClient

__all__ = ["server_app", "ChickenFoodSafetyClient"]
