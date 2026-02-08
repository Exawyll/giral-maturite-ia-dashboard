# Analyse Maturité IA - DSI Agroalimentaires

Dashboard d'analyse des résultats du questionnaire de maturité IA pour les DSI du secteur agroalimentaire.

## Fonctionnalités

- **Statistiques globales** : Vue d'ensemble de la maturité sur les 8 axes
- **Analyses par groupe** : Comparaison par type d'entreprise, CA, effectif
- **Vue Radar** : Visualisation graphique de la maturité globale
- **Distribution des niveaux** : Répartition N0-N4 par axe
- **Matrice de corrélation** : Analyse des liens entre les différents axes
- **Forces et faiblesses** : Regroupement thématique des réponses qualitatives
- **Infobulles explicatives** : Chaque KPI et graphique dispose d'une icône (?) affichant une explication sur les données et leur calcul

## Guide des infobulles

Le dashboard intègre des infobulles contextuelles pour améliorer la compréhension des données :

| Élément | Explication fournie |
|---------|---------------------|
| Réponses totales | Nombre d'entreprises ayant complété le questionnaire |
| Maturité moyenne | Score moyen sur l'ensemble des 5 axes (échelle 0-4) |
| Axe le plus mature | Axe ayant la moyenne la plus élevée |
| Axe à améliorer | Axe nécessitant des efforts prioritaires |
| Vue Radar | Représentation visuelle de la maturité par axe |
| Comparaison par groupe | Écarts de maturité selon le critère de regroupement |
| Distribution des niveaux | Répartition des réponses N0 à N4 par axe |
| Matrice de corrélation | Coefficient de Pearson entre paires d'axes |
| Corrélations significatives | Paires d'axes avec coefficient > 0.5 |
| Forces et Faiblesses | Analyse qualitative des réponses textuelles |

## Axes analysés

1. Stratégie et gouvernance
2. Organisation et compétences
3. Données et pipelines
4. Plateforme et opérations (MLOps/LLMOps)
5. Sécurité et conformité
6. Processus et adoption métier
7. Cas d'usage – valeur (économies + création)
8. Économie et mesure de la valeur (KPIs/ROI/TCO)

## 📊 Gestion des données

Les données du questionnaire sont stockées dans **Cloud Firestore** et complètement séparées du code de l'application.

### Architecture

```
Fichier Excel (local)  →  Script Python  →  Firestore  →  Application
    .docs/              upload_data.py    (cloud)      (Cloud Run)
```

### Mettre à jour les données

1. **Placer le fichier Excel** dans `.docs/` (en local uniquement, jamais commité)
2. **Exécuter le script de migration** :
   ```bash
   python scripts/upload_data.py
   ```
3. Les données sont uploadées sur Firestore et **immédiatement accessibles** par l'application

### Avantages

- ✅ **Séparation** : Données et code complètement découplés
- ✅ **Mise à jour** : Modifier les données sans redéployer l'application
- ✅ **Sécurité** : Pas de fichier sensible dans Git
- ✅ **Gratuit** : Firestore offre 1 GB gratuit (largement suffisant)
- ✅ **Performance** : Données en cache, latence < 50ms

### Première configuration (une seule fois)

```bash
# 1. Créer la base Firestore
gcloud firestore databases create --location=europe-west1

# 2. Ajouter Firebase au projet GCP (une seule fois)
firebase projects:addfirebase maturite-ia-dashboard

# 3. Déployer les règles de sécurité
firebase deploy --only firestore:rules

# 4. Uploader les premières données
python scripts/upload_data.py
```

Pour plus de détails, voir [scripts/README.md](scripts/README.md).

## Installation locale

```bash
# Créer un environnement virtuel
python3 -m venv venv
source venv/bin/activate

# Installer les dépendances
pip install -r requirements.txt

# S'authentifier avec GCP pour accéder à Firestore
gcloud auth application-default login

# Lancer l'application
uvicorn app.main:app --reload --port 8080
```

Ouvrir http://localhost:8080 dans le navigateur.

**Note** : L'application charge les données depuis Firestore. Assurez-vous que les données ont été uploadées avec `python scripts/upload_data.py`.

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
│   │   └── index.html       # Dashboard HTML avec infobulles
│   ├── static/              # Fichiers statiques
│   ├── __init__.py
│   ├── main.py              # Application FastAPI
│   └── data_loader.py       # Chargement depuis Firestore
├── scripts/
│   ├── upload_data.py       # Migration Excel → Firestore
│   └── README.md            # Documentation des scripts
├── .docs/                   # Local uniquement (dans .gitignore)
│   └── *.xlsx               # Fichier Excel source
├── firestore.rules          # Règles de sécurité Firestore
├── Dockerfile               # Build sans dépendance aux données
├── cloudbuild.yaml          # Configuration Cloud Build
├── requirements.txt         # Dépendances Python (avec Firestore)
└── README.md
```

## Technologies

- **Backend** : FastAPI (Python 3.11)
- **Frontend** : HTML5, Bootstrap 5, Chart.js, Plotly.js
- **Base de données** : Cloud Firestore (NoSQL)
- **Déploiement** : Docker, Google Cloud Run
- **CI/CD** : Cloud Build
