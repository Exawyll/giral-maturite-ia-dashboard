# Analyse Maturité IA - DSI Agroalimentaires

Dashboard d'analyse des résultats du questionnaire de maturité IA pour les DSI du secteur agroalimentaire.

## Fonctionnalités

- **Statistiques globales** : Vue d'ensemble de la maturité sur les 8 axes
- **Analyses par groupe** : Comparaison par type d'entreprise, CA, effectif
- **Vue Radar** : Visualisation graphique de la maturité globale
- **Distribution des niveaux** : Répartition N0-N4 par axe
- **Matrice de corrélation** : Analyse des liens entre les différents axes
- **Forces et faiblesses** : Regroupement thématique des réponses qualitatives

## Axes analysés

1. Stratégie et gouvernance
2. Organisation et compétences
3. Données et pipelines
4. Plateforme et opérations (MLOps/LLMOps)
5. Sécurité et conformité
6. Processus et adoption métier
7. Cas d'usage – valeur (économies + création)
8. Économie et mesure de la valeur (KPIs/ROI/TCO)

## Installation locale

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
uvicorn app.main:app --reload --port 8080
```

Ouvrir http://localhost:8080 dans le navigateur.

## Déploiement sur Google Cloud Run

### Prérequis

- Un projet GCP avec la facturation activée
- `gcloud` CLI installé et configuré
- APIs activées : Cloud Run, Cloud Build, Container Registry

### Déploiement rapide

```bash
# Se connecter à GCP
gcloud auth login

# Configurer le projet
gcloud config set project YOUR_PROJECT_ID

# Build et déploiement en une commande
gcloud run deploy maturite-ia-dashboard \
  --source . \
  --region europe-west1 \
  --allow-unauthenticated
```

### Déploiement avec Cloud Build

```bash
# Remplacer PROJECT_ID dans cloudbuild.yaml puis :
gcloud builds submit --config cloudbuild.yaml
```

### Déploiement manuel avec Docker

```bash
# Build de l'image
docker build -t gcr.io/YOUR_PROJECT_ID/maturite-ia-dashboard .

# Push vers Container Registry
docker push gcr.io/YOUR_PROJECT_ID/maturite-ia-dashboard

# Déployer sur Cloud Run
gcloud run deploy maturite-ia-dashboard \
  --image gcr.io/YOUR_PROJECT_ID/maturite-ia-dashboard \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard principal |
| `GET /health` | Health check |
| `GET /api/stats/global` | Statistiques globales |
| `GET /api/stats/by-group?group_by=` | Stats par groupe (groupe, ca, effectif, effectif_dsi) |
| `GET /api/correlations` | Matrice de corrélation |
| `GET /api/strengths-weaknesses` | Forces et faiblesses par axe |
| `GET /api/filters` | Options de filtres disponibles |
| `GET /api/axes` | Liste des axes de maturité |

## Structure du projet

```
giral-recap/
├── app/
│   ├── api/
│   │   ├── __init__.py
│   │   └── analysis.py      # API endpoints
│   ├── templates/
│   │   └── index.html       # Dashboard HTML
│   ├── static/              # Fichiers statiques
│   ├── __init__.py
│   ├── main.py              # Application FastAPI
│   └── data_loader.py       # Chargement et analyse des données
├── .docs/
│   └── Matrice de maturité data seules.xlsx
├── Dockerfile
├── cloudbuild.yaml
├── requirements.txt
└── README.md
```

## Technologies

- **Backend** : FastAPI (Python 3.11)
- **Frontend** : HTML5, Bootstrap 5, Chart.js, Plotly.js
- **Déploiement** : Docker, Google Cloud Run
