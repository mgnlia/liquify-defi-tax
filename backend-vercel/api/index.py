"""
DeFi Tax Intelligence API — Vercel Serverless Handler
"""
import sys
import os

# Add the api directory to the path so imports work
sys.path.insert(0, os.path.dirname(__file__))

from mangum import Mangum
from main import app

handler = Mangum(app, lifespan="off")
