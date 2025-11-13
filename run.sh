#!/bin/bash
# Script de lancement rapide

if [ ! -d "venv" ]; then
    echo "❌ Environnement virtuel non trouvé. Exécutez d'abord: bash setup.sh"
    exit 1
fi

source venv/bin/activate

echo "🦆 Lancement de la recherche du canard mauve..."
echo ""
echo "Quelle version voulez-vous utiliser?"
echo "1) Playwright (recommandé) - Gère mieux JavaScript"
echo "2) Requests - Plus rapide mais moins robuste"
echo "3) Explorer - Juste explorer le site"
echo ""
read -p "Votre choix (1-3): " choice

case $choice in
    1)
        echo "Lancement avec Playwright..."
        python duck_finder_playwright.py
        ;;
    2)
        echo "Lancement avec Requests..."
        python duck_finder.py
        ;;
    3)
        echo "Lancement de l'explorateur..."
        python explore_centris.py
        ;;
    *)
        echo "Choix invalide. Lancement de la version Playwright par défaut..."
        python duck_finder_playwright.py
        ;;
esac
