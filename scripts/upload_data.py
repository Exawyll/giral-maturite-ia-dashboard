#!/usr/bin/env python3
"""
Script de migration des données Excel vers Firestore
Exécuter depuis la racine du projet : python scripts/upload_data.py

Ce script :
1. Lit le fichier Excel dans .docs/
2. Transforme chaque ligne en document structuré
3. Upload vers Firestore en ÉCRASANT toutes les données existantes
"""

import os
import sys
import pandas as pd
from google.cloud import firestore
from typing import Dict, Any
import re

# Ajouter le dossier parent au path pour importer les constantes
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Définition des axes (identique à data_loader.py)
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


def get_excel_path() -> str:
    """Trouve le fichier Excel dans .docs/"""
    docs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".docs")
    
    if not os.path.isdir(docs_dir):
        raise FileNotFoundError(f"Le dossier .docs/ n'existe pas : {docs_dir}")
    
    xlsx_files = [f for f in os.listdir(docs_dir) if f.endswith('.xlsx') and not f.startswith('~')]
    
    if not xlsx_files:
        raise FileNotFoundError(f"Aucun fichier .xlsx trouvé dans {docs_dir}")
    
    return os.path.join(docs_dir, xlsx_files[0])


def extract_level(text: str) -> int:
    """Extrait le niveau de maturité (0-4) d'une chaîne de caractères"""
    if pd.isna(text) or not isinstance(text, str):
        return None
    
    match = re.match(r'N(\d)', str(text))
    if match:
        return int(match.group(1))
    return None


def load_excel_data() -> pd.DataFrame:
    """Charge les données depuis le fichier Excel"""
    excel_path = get_excel_path()
    print(f"📂 Lecture du fichier : {excel_path}")
    
    df = pd.read_excel(excel_path, sheet_name="Données")
    print(f"✅ {len(df)} réponses chargées")
    
    return df


def transform_row_to_document(row: pd.Series, row_idx: int) -> Dict[str, Any]:
    """Transforme une ligne du DataFrame en document Firestore"""
    
    # Colonnes de métadonnées
    metadata = {
        "groupe": str(row.get("Dans quel groupe ton entreprise se situe-t-elle ?", "")) if pd.notna(row.get("Dans quel groupe ton entreprise se situe-t-elle ?")) else "",
        "ca": str(row.get("Tranche de chiffre d'affaires", "")) if pd.notna(row.get("Tranche de chiffre d'affaires")) else "",
        "effectif_entreprise": str(row.get("Effectif de l'entreprise", "")) if pd.notna(row.get("Effectif de l'entreprise")) else "",
        "effectif_dsi": str(row.get("Effectif de la DSI", "")) if pd.notna(row.get("Effectif de la DSI")) else ""
    }
    
    # Données par axe
    axes_data = {}
    for axe, short_name in zip(AXES, AXES_SHORT):
        niveau_col = f"{axe} : le niveau de ton entreprise"
        force_col = f"{axe} : une force ou une initiative réussie"
        faiblesse_col = f"{axe} : une faiblesse ou un frein"
        
        niveau_raw = row.get(niveau_col)
        niveau = extract_level(niveau_raw)
        
        force = row.get(force_col)
        faiblesse = row.get(faiblesse_col)
        
        axes_data[short_name] = {
            "niveau": niveau if niveau is not None else None,
            "niveau_raw": str(niveau_raw) if pd.notna(niveau_raw) else None,
            "force": str(force) if pd.notna(force) else None,
            "faiblesse": str(faiblesse) if pd.notna(faiblesse) else None
        }
    
    return {
        "id": f"response_{row_idx:03d}",
        "metadata": metadata,
        "axes": axes_data
    }


def upload_to_firestore(project_id: str = None):
    """
    Upload les données vers Firestore en ÉCRASANT tout
    
    Args:
        project_id: ID du projet GCP (détecté automatiquement si None)
    """
    
    # Initialiser le client Firestore
    if project_id:
        db = firestore.Client(project=project_id)
    else:
        db = firestore.Client()  # Utilise GOOGLE_CLOUD_PROJECT ou credentials par défaut
    
    print(f"🔗 Connexion à Firestore (projet: {db.project})")
    
    # Charger les données Excel
    df = load_excel_data()
    
    # Référence à la collection
    collection_ref = db.collection(COLLECTION_NAME)
    
    # ÉTAPE 1 : Supprimer tous les documents existants
    print(f"\n🗑️  Suppression des anciennes données...")
    deleted_count = 0
    docs = collection_ref.stream()
    batch = db.batch()
    batch_count = 0
    
    for doc in docs:
        batch.delete(doc.reference)
        batch_count += 1
        deleted_count += 1
        
        # Firestore limite à 500 opérations par batch
        if batch_count >= 500:
            batch.commit()
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    print(f"   ✓ {deleted_count} anciens documents supprimés")
    
    # ÉTAPE 2 : Insérer les nouvelles données
    print(f"\n📤 Upload des nouvelles données...")
    
    batch = db.batch()
    batch_count = 0
    uploaded_count = 0
    
    for idx, row in df.iterrows():
        doc_data = transform_row_to_document(row, idx)
        doc_id = doc_data["id"]
        
        doc_ref = collection_ref.document(doc_id)
        batch.set(doc_ref, doc_data)
        batch_count += 1
        uploaded_count += 1
        
        if batch_count >= 500:
            batch.commit()
            print(f"   ✓ {uploaded_count} documents uploadés...")
            batch = db.batch()
            batch_count = 0
    
    if batch_count > 0:
        batch.commit()
    
    print(f"\n✅ Migration terminée !")
    print(f"   • {deleted_count} anciens documents supprimés")
    print(f"   • {uploaded_count} nouveaux documents créés")
    print(f"   • Collection : {COLLECTION_NAME}")
    print(f"   • Projet GCP : {db.project}")


def main():
    """Point d'entrée du script"""
    
    print("=" * 70)
    print("🚀 MIGRATION EXCEL → FIRESTORE")
    print("=" * 70)
    
    # Vérifier que le fichier Excel existe
    try:
        excel_path = get_excel_path()
    except FileNotFoundError as e:
        print(f"\n❌ Erreur : {e}")
        print("\n💡 Assurez-vous que le fichier Excel est bien dans .docs/")
        sys.exit(1)
    
    # Demander confirmation
    print(f"\n⚠️  ATTENTION : Cette opération va :")
    print(f"   1. Supprimer TOUTES les données existantes dans Firestore")
    print(f"   2. Uploader les données depuis : {excel_path}")
    
    confirm = input(f"\n❓ Continuer ? (oui/non) : ").strip().lower()
    
    if confirm not in ["oui", "o", "yes", "y"]:
        print("\n❌ Opération annulée")
        sys.exit(0)
    
    # Récupérer le projet GCP (optionnel)
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        project_input = input(f"\n🔧 ID du projet GCP (ou Enter pour auto-détection) : ").strip()
        if project_input:
            project_id = project_input
    
    # Lancer la migration
    try:
        upload_to_firestore(project_id=project_id)
    except Exception as e:
        print(f"\n❌ Erreur lors de la migration : {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("✨ Migration réussie ! Les données sont maintenant sur Firestore.")
    print("=" * 70)


if __name__ == "__main__":
    main()
