# Centris Duck Finder 🦆

Ce projet cherche le canard mauve caché dans les photos des propriétés à vendre sur [centris.ca](https://centris.ca).

## Description

Un canard mauve est caché quelque part dans les photos d'une des maisons à vendre sur Centris. Ce script automatise la recherche en:
1. Récupérant les listings de propriétés sur centris.ca
2. Téléchargeant toutes les photos des propriétés
3. Analysant chaque image pour détecter la présence d'un canard mauve

## Installation

```bash
pip install -r requirements.txt
```

## Utilisation

```bash
python duck_finder.py
```

Le script va parcourir les propriétés et signaler toute image contenant des pixels de couleur mauve/violet qui pourraient être le canard.

## Résultats

Les images suspectes sont sauvegardées dans le dossier `potential_ducks/` pour inspection manuelle.

## Stratégie de détection

Le script détecte les zones de couleur mauve/violet en utilisant:
- Analyse HSV pour identifier les pixels dans la plage de couleur mauve (Hue: 270-320°)
- Détection de clusters de pixels mauves qui pourraient former un canard
- Sauvegarde des images candidates pour vérification manuelle
