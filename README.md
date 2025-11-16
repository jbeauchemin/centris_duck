# Centris Duck Finder 🦆

Ce projet cherche le canard mauve caché dans les photos des propriétés à vendre sur [centris.ca](https://centris.ca).

## Description

Un canard mauve est caché quelque part dans les photos d'une des maisons à vendre sur Centris. Ce script automatise la recherche en:
1. Parcourant **TOUTES** les propriétés sur centris.ca avec pagination complète
2. Téléchargeant toutes les photos de chaque propriété
3. Analysant chaque image avec détection de couleur + détection de contours
4. Sauvegardant les images suspectes pour inspection manuelle

## Installation

```bash
# Installer les dépendances Python
pip install -r requirements.txt

# Installer les navigateurs Playwright
playwright install chromium
```

## Utilisation

### Version complète (recommandée) 🚀

Cette version parcourt **TOUT** le site Centris avec pagination complète et système de reprise:

```bash
# Mode normal (recommandé) - affiche la progression en temps réel
python duck_finder_complete.py

# Mode VISUEL - voir le navigateur en action! 👁️
python duck_finder_complete.py --show-browser

# Mode silencieux - seulement les résultats importants
python duck_finder_complete.py --quiet
```

**Fonctionnalités:**
- ✅ Pagination automatique pour parcourir toutes les pages de résultats
- ✅ Système de checkpoint pour reprendre en cas d'interruption
- ✅ Détection améliorée avec analyse de contours
- ✅ Statistiques en temps réel avec progression détaillée
- ✅ Sauvegarde automatique de la progression tous les 10 propriétés
- ✅ Mode visuel optionnel pour voir le navigateur en action

**Ce que tu verras pendant l'exécution:**
- 📍 URL de chaque propriété en cours d'analyse
- 🖼️ Nombre d'images trouvées par propriété
- ⏱️ Temps écoulé et statistiques en temps réel
- 🦆 Alertes immédiates quand un canard potentiel est détecté
- 💾 Confirmations de sauvegarde de checkpoint
- 📊 Statistiques tous les 10 propriétés

Si le script est interrompu (Ctrl+C), tu peux simplement le relancer et il reprendra là où il s'est arrêté grâce au fichier `checkpoint.json`.

### Versions basiques

```bash
# Version avec Playwright (pour sites JavaScript) - limité à 50 propriétés
python duck_finder_playwright.py

# Version avec requests (peut ne pas fonctionner sur Centris)
python duck_finder.py
```

### Script d'exploration

Pour explorer la structure du site Centris:

```bash
python explore_centris.py
```

### Script de test de détection 🧪

Pour tester la détection sur une image spécifique avant de lancer le scan complet:

```bash
python test_detection.py <chemin_image>

# Exemples:
python test_detection.py test_image.jpg
python test_detection.py potential_ducks/duck_12345.jpg
```

Ce script va:
- Analyser l'image avec les mêmes critères que le scan complet
- Afficher les statistiques détaillées (pourcentage de pixels mauves, contours, etc.)
- Créer des visualisations dans `test_results/`:
  - `*_mask.jpg` - Masque de détection
  - `*_contours.jpg` - Image avec contours
  - `*_overlay.jpg` - Overlay des zones mauves

### Nettoyage 🧹

Pour supprimer tous les résultats et recommencer à zéro:

```bash
bash clean.sh
```

Cela supprime:
- `potential_ducks/` - Images suspectes trouvées
- `images/` - Images temporaires
- `screenshots/` - Captures d'écran
- `test_results/` - Résultats de tests
- `checkpoint.json` - Fichier de progression

## Résultats

Les images suspectes sont sauvegardées dans le dossier `potential_ducks/` avec:
- L'image originale (`duck_*.jpg`)
- Le masque de détection (`mask_*.jpg`)
- L'image avec contours détectés (`contours_*.jpg`)
- Les informations détaillées (`info_*.txt`)

## Stratégie de détection

Le script utilise une détection multi-niveaux ciblée sur la couleur **exacte** du canard:

### Couleur du canard 🎨
- **HEX:** `#c97ef2`
- **RGB:** (201, 126, 242)
- **HSV:** (139, 122, 242) dans l'espace OpenCV

### Méthode de détection

1. **Détection de couleur HSV stricte**
   - **Plage principale (lumière):** H: 131-147, S: 82-162, V: 192-255
   - **Plage secondaire (ombre):** H: 129-149, S: 60-180, V: 150-200
   - Ces plages sont **beaucoup plus strictes** pour éviter les faux positifs

2. **Opérations morphologiques**
   - Nettoyage du bruit avec fermeture/ouverture (kernel 3x3)
   - Amélioration des contours

3. **Détection de contours**
   - Identification de formes cohérentes (un canard!)
   - Filtrage par taille minimale: **> 500 pixels²** (augmenté pour éviter les artefacts)

4. **Critères de suspicion STRICTS**
   - Au moins **1.0%** de pixels mauves dans l'image (augmenté de 0.3%)
   - **ET** au moins un contour significatif de > 500 pixels²
   - **OU** un très gros contour de > 2000 pixels² (probablement le canard!)

Ces critères stricts réduisent drastiquement les faux positifs tout en gardant une bonne sensibilité pour le vrai canard.

## Progression et reprise

Le fichier `checkpoint.json` contient:
- Liste des propriétés déjà visitées
- Liste des images déjà analysées
- Statistiques de progression
- Date de dernière mise à jour

Pour recommencer depuis zéro, supprime simplement `checkpoint.json`.

## Performance

Le script peut prendre plusieurs heures pour analyser tout le site Centris (plusieurs milliers de propriétés). La progression est automatiquement sauvegardée tous les 10 propriétés.
