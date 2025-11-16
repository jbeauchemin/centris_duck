#!/bin/bash
# Script d'installation pour Centris Duck Finder

echo "🦆 Installation de Centris Duck Finder..."
echo "=========================================="

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 n'est pas installé"
    exit 1
fi

echo "✓ Python 3 trouvé: $(python3 --version)"

# Créer un environnement virtuel
echo ""
echo "📦 Création de l'environnement virtuel..."
python3 -m venv venv

# Activer l'environnement virtuel
echo "✓ Activation de l'environnement virtuel..."
source venv/bin/activate

# Installer les dépendances
echo ""
echo "📥 Installation des dépendances..."
pip install --upgrade pip
pip install -r requirements.txt

# Installer Playwright browsers
echo ""
echo "🌐 Installation des navigateurs Playwright..."
playwright install chromium

echo ""
echo "=========================================="
echo "✅ Installation terminée!"
echo ""
echo "Pour utiliser le finder:"
echo "  1. Activez l'environnement: source venv/bin/activate"
echo "  2. Lancez le script:"
echo "     - Version COMPLÈTE (recommandé): python duck_finder_complete.py"
echo "       → Scanne TOUT le site avec pagination + checkpoints"
echo "     - Version Playwright: python duck_finder_playwright.py (limité à 50 propriétés)"
echo "     - Version requests: python duck_finder.py"
echo "     - Explorer le site: python explore_centris.py"
echo ""
echo "OU utilisez: bash run.sh (menu interactif)"
echo ""
echo "Bonne chasse au canard! 🦆"
