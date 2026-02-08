"""
Module de chargement et traitement des données depuis Firestore
"""
import pandas as pd
import numpy as np
from google.cloud import firestore
from functools import lru_cache
from typing import Dict, List, Any

# Définition des axes de maturité
AXES = [
    "Stratégie et gouvernance",
    "Organisation et compétences",
    "Données et pipelines",
    "Plateforme et opérations",
    "Sécurité et conformité",
    "Processus et adoption métier",
    "Cas d'usage – valeur (économies + création)",
    "Économie et mesure de la valeur (KPIs/ROI/TCO)"
]

AXES_SHORT = [
    "Stratégie",
    "Organisation",
    "Données",
    "Plateforme",
    "Sécurité",
    "Processus",
    "Cas d'usage",
    "Économie"
]

COLLECTION_NAME = "survey_responses"


@lru_cache(maxsize=1)
def load_data() -> pd.DataFrame:
    """
    Charge les données depuis Firestore et les convertit en DataFrame pandas
    Les données sont mises en cache pour optimiser les performances
    """
    print("[DATA] Chargement des données depuis Firestore...")
    
    # Initialiser le client Firestore (utilise les credentials par défaut de Cloud Run)
    db = firestore.Client()
    
    # Récupérer tous les documents de la collection
    docs = db.collection(COLLECTION_NAME).stream()
    
    # Transformer les documents Firestore en liste de dictionnaires
    rows = []
    for doc in docs:
        data = doc.to_dict()
        
        # Construire une ligne au format attendu par le reste du code
        row = {}
        
        # Métadonnées
        metadata = data.get("metadata", {})
        row["Dans quel groupe ton entreprise se situe-t-elle ?"] = metadata.get("groupe", "")
        row["Tranche de chiffre d'affaires"] = metadata.get("ca", "")
        row["Effectif de l'entreprise"] = metadata.get("effectif_entreprise", "")
        row["Effectif de la DSI"] = metadata.get("effectif_dsi", "")
        
        # Données par axe
        axes_data = data.get("axes", {})
        for axe, short_name in zip(AXES, AXES_SHORT):
            axe_info = axes_data.get(short_name, {})
            
            # Colonnes format original
            row[f"{axe} : le niveau de ton entreprise"] = axe_info.get("niveau_raw")
            row[f"{axe} : une force ou une initiative réussie"] = axe_info.get("force")
            row[f"{axe} : une faiblesse ou un frein"] = axe_info.get("faiblesse")
            
            # Colonne niveau pré-extrait
            row[f"{axe}_niveau"] = axe_info.get("niveau")
        
        rows.append(row)
    
    # Créer le DataFrame
    df = pd.DataFrame(rows)
    
    print(f"[DATA] ✓ {len(df)} réponses chargées depuis Firestore")
    
    return df


def get_processed_data() -> pd.DataFrame:
    """
    Retourne les données avec les niveaux extraits pour chaque axe
    Note: Les niveaux sont déjà extraits lors du chargement depuis Firestore
    """
    return load_data().copy()


def get_column_mapping() -> Dict[str, Dict[str, str]]:
    """
    Retourne le mapping des colonnes pour chaque axe
    """
    mapping = {}
    for axe in AXES:
        mapping[axe] = {
            "niveau": f"{axe} : le niveau de ton entreprise",
            "force": f"{axe} : une force ou une initiative réussie",
            "faiblesse": f"{axe} : une faiblesse ou un frein"
        }
    return mapping


def get_statistics_by_group(group_col: str) -> Dict[str, Any]:
    """
    Calcule les statistiques de maturité par groupe
    
    Args:
        group_col: Colonne de groupement (groupe, CA, effectif)
    """
    df = get_processed_data()
    
    result = {}
    
    for group_value, group_df in df.groupby(group_col):
        if pd.isna(group_value) or group_value == "":
            continue
        
        stats = {"count": len(group_df), "axes": {}}
        
        for i, axe in enumerate(AXES):
            col = f"{axe}_niveau"
            if col in group_df.columns:
                values = group_df[col].dropna()
                if len(values) > 0:
                    stats["axes"][AXES_SHORT[i]] = {
                        "moyenne": round(values.mean(), 2),
                        "min": int(values.min()),
                        "max": int(values.max()),
                        "distribution": values.value_counts().to_dict()
                    }
        
        result[str(group_value)] = stats
    
    return result


def get_global_statistics() -> Dict[str, Any]:
    """Calcule les statistiques globales de maturité"""
    df = get_processed_data()
    
    result = {"total_responses": len(df), "axes": {}}
    
    for i, axe in enumerate(AXES):
        col = f"{axe}_niveau"
        if col in df.columns:
            values = df[col].dropna()
            if len(values) > 0:
                distribution = {int(k): int(v) for k, v in values.value_counts().items()}
                result["axes"][AXES_SHORT[i]] = {
                    "moyenne": round(values.mean(), 2),
                    "ecart_type": round(values.std(), 2),
                    "min": int(values.min()),
                    "max": int(values.max()),
                    "distribution": distribution
                }
    
    return result


def get_correlations() -> Dict[str, Any]:
    """Calcule les corrélations entre les axes de maturité"""
    df = get_processed_data()
    
    niveau_cols = [f"{axe}_niveau" for axe in AXES]
    existing_cols = [c for c in niveau_cols if c in df.columns]
    
    if len(existing_cols) < 2:
        return {"error": "Pas assez de données pour calculer les corrélations"}
    
    # Matrice de corrélation
    corr_df = df[existing_cols].corr()
    
    # Remplacer NaN et Infinity par 0 pour éviter les erreurs JSON
    corr_df = corr_df.fillna(0)
    corr_df = corr_df.replace([np.inf, -np.inf], 0)
    
    # Renommer les colonnes/index avec les noms courts
    rename_dict = {f"{axe}_niveau": short for axe, short in zip(AXES, AXES_SHORT) if f"{axe}_niveau" in existing_cols}
    corr_df = corr_df.rename(columns=rename_dict, index=rename_dict)
    
    # Convertir en format JSON-friendly
    actual_labels = list(corr_df.columns)
    result = {
        "matrix": corr_df.round(3).to_dict(),
        "labels": actual_labels,
        "strong_correlations": []
    }
    
    # Identifier les corrélations fortes (> 0.5)
    for i, axe1 in enumerate(actual_labels):
        for j, axe2 in enumerate(actual_labels):
            if i < j:  # Éviter les doublons
                corr_val = corr_df.loc[axe1, axe2]
                if not pd.isna(corr_val) and abs(corr_val) > 0.5:
                    result["strong_correlations"].append({
                        "axe1": axe1,
                        "axe2": axe2,
                        "correlation": round(corr_val, 3)
                    })
    
    return result


def get_strengths_weaknesses() -> Dict[str, Any]:
    """
    Analyse les forces et faiblesses pour chaque axe
    Regroupe par thématiques communes
    """
    df = load_data()
    mapping = get_column_mapping()
    
    result = {}
    
    for i, axe in enumerate(AXES):
        force_col = mapping[axe]["force"]
        faiblesse_col = mapping[axe]["faiblesse"]
        
        forces = []
        faiblesses = []
        
        if force_col in df.columns:
            forces = df[force_col].dropna().tolist()
        
        if faiblesse_col in df.columns:
            faiblesses = df[faiblesse_col].dropna().tolist()
        
        # Grouper par thématiques (analyse simple basée sur mots-clés)
        result[AXES_SHORT[i]] = {
            "axe_complet": axe,
            "forces": {
                "count": len(forces),
                "responses": forces,
                "themes": extract_themes(forces)
            },
            "faiblesses": {
                "count": len(faiblesses),
                "responses": faiblesses,
                "themes": extract_themes(faiblesses)
            }
        }
    
    return result


def extract_themes(texts: List[str]) -> Dict[str, List[str]]:
    """
    Extrait et groupe les réponses par thèmes communs
    """
    if not texts:
        return {}
    
    # Mots-clés thématiques
    theme_keywords = {
        "Formation & Compétences": ["formation", "compétence", "équipe", "talent", "webinaire", "sensibilisation"],
        "Budget & Coûts": ["budget", "coût", "cout", "investissement", "financement", "ressource"],
        "Gouvernance & Organisation": ["gouvernance", "organisation", "comité", "stratégie", "direction", "management"],
        "Données & Qualité": ["données", "data", "qualité", "catalogue", "référentiel", "master data"],
        "Technologie & Outils": ["outil", "technologie", "plateforme", "infrastructure", "cloud", "poc"],
        "Processus & Adoption": ["processus", "adoption", "métier", "usage", "intégration"],
        "Sécurité & Conformité": ["sécurité", "conformité", "rgpd", "risque", "audit"]
    }
    
    themes = {theme: [] for theme in theme_keywords}
    themes["Autres"] = []
    
    for text in texts:
        if not text or not isinstance(text, str):
            continue
        text_lower = text.lower()
        matched = False
        
        for theme, keywords in theme_keywords.items():
            if any(kw in text_lower for kw in keywords):
                themes[theme].append(text)
                matched = True
                break
        
        if not matched:
            themes["Autres"].append(text)
    
    # Retirer les thèmes vides
    return {k: v for k, v in themes.items() if v}


def get_filters_options() -> Dict[str, List[str]]:
    """Retourne les options disponibles pour les filtres"""
    df = load_data()
    
    return {
        "groupes": sorted([x for x in df["Dans quel groupe ton entreprise se situe-t-elle ?"].dropna().unique().tolist() if x]),
        "tranches_ca": sorted([x for x in df["Tranche de chiffre d'affaires"].dropna().unique().tolist() if x]),
        "effectifs_entreprise": sorted([x for x in df["Effectif de l'entreprise"].dropna().unique().tolist() if x]),
        "effectifs_dsi": sorted([x for x in df["Effectif de la DSI"].dropna().unique().tolist() if x])
    }
