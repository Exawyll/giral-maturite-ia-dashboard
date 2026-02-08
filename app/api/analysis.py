"""
API endpoints pour l'analyse des données de maturité IA
"""
from fastapi import APIRouter, Query
from typing import Optional

from app.data_loader import (
    get_global_statistics,
    get_statistics_by_group,
    get_correlations,
    get_strengths_weaknesses,
    get_filters_options,
    AXES_SHORT
)

router = APIRouter()


@router.get("/stats/global")
async def global_statistics():
    """
    Statistiques globales de maturité sur tous les axes
    """
    return get_global_statistics()


@router.get("/stats/by-group")
async def statistics_by_group(
    group_by: str = Query(
        default="groupe",
        description="Type de groupement: groupe, ca, effectif, effectif_dsi"
    )
):
    """
    Statistiques de maturité par groupe
    
    - groupe: Par type d'entreprise (Coopérative/Producteur)
    - ca: Par tranche de chiffre d'affaires
    - effectif: Par effectif de l'entreprise
    - effectif_dsi: Par effectif de la DSI
    """
    column_mapping = {
        "groupe": "Dans quel groupe ton entreprise se situe-t-elle ?",
        "ca": "Tranche de chiffre d'affaires",
        "effectif": "Effectif de l'entreprise",
        "effectif_dsi": "Effectif de la DSI"
    }
    
    col = column_mapping.get(group_by, column_mapping["groupe"])
    return get_statistics_by_group(col)


@router.get("/correlations")
async def correlations():
    """
    Matrice de corrélation entre les axes de maturité
    """
    return get_correlations()


@router.get("/strengths-weaknesses")
async def strengths_weaknesses():
    """
    Analyse des forces et faiblesses par axe, groupées par thématiques
    """
    return get_strengths_weaknesses()


@router.get("/filters")
async def filters():
    """
    Options disponibles pour les filtres
    """
    return get_filters_options()


@router.get("/axes")
async def axes_list():
    """
    Liste des axes de maturité
    """
    return {"axes": AXES_SHORT}


@router.get("/debug")
async def debug_info():
    """
    Debug endpoint to check file paths and data loading
    """
    import os
    from app.data_loader import get_excel_path
    
    excel_path = get_excel_path()
    
    # Check what files exist
    app_files = os.listdir("/app") if os.path.exists("/app") else "N/A"
    docs_files = os.listdir("/app/.docs") if os.path.exists("/app/.docs") else "N/A"
    
    return {
        "cwd": os.getcwd(),
        "excel_path": excel_path,
        "excel_exists": os.path.exists(excel_path),
        "app_files": app_files,
        "docs_files": docs_files
    }
