# Setup initial de Firestore

Ce guide vous permet de configurer Firestore pour la première fois.

## Prérequis

1. **gcloud CLI** installé et configuré
2. **Firebase CLI** installé :
   ```bash
   npm install -g firebase-tools
   ```

## Étapes

### 1. Créer la base Firestore

```bash
gcloud firestore databases create \
  --location=europe-west1 \
  --project=maturite-ia-dashboard
```

**Note** : Choisissez `europe-west1` pour minimiser la latence avec Cloud Run.

### 2. Ajouter Firebase au projet GCP

```bash
firebase projects:addfirebase maturite-ia-dashboard
```

**Note** : Cette étape n'est nécessaire qu'une seule fois pour lier Firebase au projet GCP.

### 3. Déployer les règles de sécurité

```bash
firebase deploy --only firestore:rules --project=maturite-ia-dashboard
```

Les règles configurent :
- ✅ Lecture publique (données anonymisées)
- ❌ Écriture interdite (seulement via script local)

### 3. Uploader les premières données

```bash
# S'authentifier en local
gcloud auth application-default login

# Placer le fichier Excel dans .docs/
# Puis exécuter le script
python scripts/upload_data.py
```

### 4. Vérifier que tout fonctionne

```bash
# Vérifier que Firestore contient les données
gcloud firestore collections list --project=maturite-ia-dashboard

# Devrait afficher : survey_responses
```

## Workflow quotidien

Une fois le setup initial effectué, pour mettre à jour les données :

1. Placer le nouveau fichier Excel dans `.docs/`
2. Exécuter `python scripts/upload_data.py`
3. Les données sont immédiatement disponibles pour l'application

## Troubleshooting

### Erreur "Permission denied"

```bash
gcloud auth application-default login
```

### Base Firestore déjà créée

Si la base existe déjà :
```bash
# Lister les bases
gcloud firestore databases list

# Déployer uniquement les règles
firebase deploy --only firestore:rules
```

### Vérifier les données uploadées

```bash
# Compter les documents
gcloud firestore query "SELECT COUNT(*) FROM survey_responses"
```
