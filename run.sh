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
echo "1) Version COMPLÈTE (recommandé) - Scanne TOUT le site avec pagination + checkpoints"
echo "2) Playwright - Limité à 50 propriétés"
echo "3) Requests - Plus rapide mais moins robuste"
echo "4) Explorer - Juste explorer le site"
echo ""
read -p "Votre choix (1-4): " choice

case $choice in
    1)
        echo "Lancement de la version complète..."
        echo "Cette version va scanner TOUT le site Centris avec pagination complète."
        echo "Appuyez sur Ctrl+C pour arrêter (la progression sera sauvegardée)."
        echo ""
        python duck_finder_complete.py
        ;;
    2)
        echo "Lancement avec Playwright (limité à 50 propriétés)..."
        python duck_finder_playwright.py
        ;;
    3)
        echo "Lancement avec Requests..."
        python duck_finder.py
        ;;
    4)
        echo "Lancement de l'explorateur..."
        python explore_centris.py
        ;;
    *)
        echo "Choix invalide. Lancement de la version complète par défaut..."
        python duck_finder_complete.py
        ;;
esac
