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
echo "2) Version COMPLÈTE avec NAVIGATEUR VISIBLE - Voir le scan en action! 👁️"
echo "3) Playwright - Limité à 50 propriétés"
echo "4) Requests - Plus rapide mais moins robuste"
echo "5) Explorer - Juste explorer le site"
echo ""
read -p "Votre choix (1-5): " choice

case $choice in
    1)
        echo ""
        echo "Lancement de la version complète..."
        echo "Cette version va scanner TOUT le site Centris avec pagination complète."
        echo "Vous verrez la progression en temps réel dans le terminal."
        echo "Appuyez sur Ctrl+C pour arrêter (la progression sera sauvegardée)."
        echo ""
        python duck_finder_complete.py
        ;;
    2)
        echo ""
        echo "Lancement de la version complète en MODE VISUEL..."
        echo "Vous allez voir le navigateur en action!"
        echo "Cela peut ralentir un peu mais c'est cool à regarder 😎"
        echo "Appuyez sur Ctrl+C pour arrêter (la progression sera sauvegardée)."
        echo ""
        python duck_finder_complete.py --show-browser
        ;;
    3)
        echo "Lancement avec Playwright (limité à 50 propriétés)..."
        python duck_finder_playwright.py
        ;;
    4)
        echo "Lancement avec Requests..."
        python duck_finder.py
        ;;
    5)
        echo "Lancement de l'explorateur..."
        python explore_centris.py
        ;;
    *)
        echo "Choix invalide. Lancement de la version complète par défaut..."
        python duck_finder_complete.py
        ;;
esac
