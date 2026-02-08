"""
Application principale - Analyse de maturité IA pour DSI agroalimentaires
"""
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
import os

from app.api import analysis

app = FastAPI(
    title="Analyse Maturité IA - DSI Agroalimentaires",
    description="Dashboard d'analyse des résultats du questionnaire de maturité IA",
    version="1.0.0"
)

# Mount static files
static_path = os.path.join(os.path.dirname(__file__), "static")
templates_path = os.path.join(os.path.dirname(__file__), "templates")

os.makedirs(static_path, exist_ok=True)
os.makedirs(templates_path, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# Include API routes
app.include_router(analysis.router, prefix="/api", tags=["analysis"])


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Page d'accueil - Dashboard principal"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "healthy"}
