# Scripts de gestion des données

Ce dossier contient les scripts pour gérer les données du dashboard.

## 📤 upload_data.py

Script de migration des données Excel vers Firestore.

### Prérequis

1. **Authentification GCP** :
   ```bash
   gcloud auth application-default login
   ```

2. **Dépendances Python** :
   ```bash
   pip install pandas openpyxl google-cloud-firestore
   ```

3. **Fichier Excel** : Placer le fichier `.xlsx` dans le dossier `.docs/` à la racine du projet

### Utilisation

```bash
# Depuis la racine du projet
python scripts/upload_data.py
```

Le script va :
1. Lire le fichier Excel dans `.docs/`
2. Demander confirmation avant d'écraser les données
3. Supprimer toutes les données existantes dans Firestore
4. Uploader les nouvelles données

### Options

- **Projet GCP** : Le script détecte automatiquement le projet via `GOOGLE_CLOUD_PROJECT` ou demande l'ID du projet
- **Données** : Toutes les données sont transformées et stockées dans la collection `survey_responses`

### Structure des données

Chaque réponse au questionnaire est stockée comme un document :

```json
{
  "id": "response_000",
  "metadata": {
    "groupe": "Coopérative",
    "ca": "< 100M€",
    "effectif_entreprise": "100-500",
    "effectif_dsi": "5-10"
  },
  "axes": {
    "Stratégie": {
      "niveau": 2,
      "niveau_raw": "N2",
      "force": "POC IA lancé avec succès",
      "faiblesse": "Manque de budget dédié"
    },
    ...
  }
}
```

### Résolution des problèmes

**Erreur d'authentification** :
```bash
gcloud auth application-default login
```

**Firestore non créé** :
```bash
gcloud firestore databases create --location=europe-west1
```

**Fichier Excel introuvable** :
- Vérifier que le fichier `.xlsx` est bien dans `.docs/`
- Le fichier ne doit pas commencer par `~` (fichier temporaire)

### Sécurité

- ⚠️ Ne jamais commiter le fichier Excel dans Git (`.docs/` est dans `.gitignore`)
- ℹ️ Les données sont anonymisées (pas d'informations personnelles)
- 🔒 Firestore est configuré en lecture seule pour l'application
