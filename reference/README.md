# Dossier d'image de référence 🦆

Mets ici l'image du canard mauve que tu cherches!

## Comment utiliser

1. **Télécharge l'image du canard mauve** que tu veux trouver
2. **Renomme-la** en `duck_reference.jpg` ou `duck_reference.png`
3. **Place-la dans ce dossier** (`reference/`)

## Analyse de l'image de référence

Une fois que tu as mis ton image, lance:

```bash
python analyze_reference.py
```

Ce script va:
- Analyser les couleurs de l'image
- Extraire les caractéristiques du canard
- Créer un profil de détection optimisé
- Afficher les statistiques de couleur

## Images supportées

- `duck_reference.jpg`
- `duck_reference.png`
- `duck_reference.jpeg`
- `duck_reference.webp`

Le script utilisera automatiquement l'image de référence si elle existe!

## Exemple

```bash
# 1. Télécharge l'image du canard
wget https://exemple.com/canard-mauve.jpg -O reference/duck_reference.jpg

# 2. Analyse l'image
python3 analyze_reference.py

# 3. Lance le scan avec l'image de référence
python3 duck_finder_fast.py
```

Le script va maintenant chercher des images similaires à ton canard de référence!
