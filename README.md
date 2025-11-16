# Centris Duck Finder 🦆

Trouve le canard mauve caché dans les photos des propriétés à vendre sur [centris.ca](https://centris.ca).

## Installation & Utilisation

C'est simple, lance juste:

```bash
bash run.sh
```

**C'est tout!** Le script va:
- ✅ Configurer l'environnement automatiquement (première fois)
- ✅ Installer toutes les dépendances
- ✅ Te montrer un menu interactif

## Menu Principal

Quand tu lances `bash run.sh`, tu as ces options:

### 1) 🚀 Scanner tout Centris (mode rapide)
Scan rapide avec 8 téléchargements parallèles (~100-200 images/min)

### 2) ⚡ Scanner en PARALLÈLE (4-6x plus rapide!)
Lance plusieurs instances en parallèle pour une vitesse maximale:
- 4-6 instances recommandées
- ~400-600 images/min
- 45,000 maisons en 2-3 heures

### 3) 🎯 Analyser mon image de canard
Si tu as une photo du canard que tu cherches:
1. Place-la dans `reference/` (ex: `reference/duck.jpg`)
2. Choisis cette option pour l'analyser
3. Le scan utilisera automatiquement ta couleur de référence!

### 4) 🧪 Tester la détection sur une image
Teste si une image contient du mauve détectable

### 5) 🔄 Fusionner les checkpoints parallèles
Après un scan parallèle, fusionne tous les résultats

### 6) 🧹 Nettoyer les résultats
Supprime tous les résultats et checkpoints pour recommencer

## Comment ça marche

1. **Scan du site:** Le script parcourt toutes les pages de propriétés sur Centris
2. **Téléchargement:** Toutes les images sont téléchargées en parallèle
3. **Détection:** Analyse HSV + détection de contours pour trouver le mauve (#c97ef2)
4. **Sauvegarde:** Les images suspectes sont dans `potential_ducks/`

## Résultats

Les canards potentiels sont sauvegardés dans:
```
potential_ducks/
  ├── duck_1_hash.jpg      # Image avec canard potentiel
  ├── duck_2_hash.jpg
  └── ...
```

## Checkpoints

Le scan sauvegarde automatiquement la progression dans `checkpoint.json`.
Si tu interromps (Ctrl+C), tu peux reprendre là où tu étais!

## Structure du Projet

```
centris_duck/
├── run.sh                    # 👈 LANCE-MOI!
├── duck_finder.py            # Scanner principal
├── parallel_scan.py          # Orchestrateur multi-instances
├── merge_checkpoints.py      # Fusion des checkpoints
├── analyze_reference.py      # Analyse d'image de référence
├── test_detection.py         # Test de détection
├── reference_detector.py     # Module de détection
├── config.py                 # Configuration
└── reference/                # Place ton image de canard ici
```

## Dépendances

Le script installe automatiquement:
- `playwright` - Automatisation du navigateur
- `opencv-python` - Détection d'image
- `numpy` - Calculs mathématiques
- `aiohttp` - Téléchargements parallèles
- `beautifulsoup4` - Parsing HTML
- `Pillow` - Manipulation d'images

## Performance

| Mode | Images/min | Temps pour 45,000 maisons |
|------|-----------|---------------------------|
| Rapide | 100-200 | 8-12 heures |
| Parallèle (4 instances) | 400-600 | 2-3 heures |

## Configuration Recommandée

**MacBook Pro M2 32GB:**
- Mode parallèle: 4-6 instances
- Workers par instance: 8-12
- Total workers: 32-72

## Détection du Canard

Le script cherche:
- Couleur: Mauve #c97ef2 (ou ta couleur de référence)
- Critères stricts:
  - **1%+ de pixels mauves** ET **contours détectés**
  - OU **gros contour mauve** (2000+ pixels²)

Cela réduit drastiquement les faux positifs!

## Tips

- **Première fois?** Teste sur 5 pages: Choisis option 1, puis entre "5"
- **Trop de candidats?** Utilise une image de référence (option 3)
- **Aller plus vite?** Mode parallèle (option 2) avec 4-6 instances
- **Checkpoint corrompu?** Nettoie tout (option 6)

Bonne chasse au canard! 🦆
