#!/bin/bash
# Centris Duck Finder - Script tout-en-un
# Usage: bash run.sh

set -e

# Couleurs
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
PURPLE='\033[0;35m'
NC='\033[0m'

clear

echo -e "${PURPLE}"
echo "╔════════════════════════════════════════╗"
echo "║   🦆  CENTRIS DUCK FINDER  🦆          ║"
echo "╚════════════════════════════════════════╝"
echo -e "${NC}"

# Vérifier si c'est la première utilisation
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}📦 Première utilisation - Configuration...${NC}"
    echo ""

    # Vérifier Python
    if ! command -v python3 &> /dev/null; then
        echo -e "${RED}❌ Python 3 requis mais non installé${NC}"
        exit 1
    fi

    echo "✓ Python 3: $(python3 --version)"

    # Créer venv
    echo "• Création de l'environnement virtuel..."
    python3 -m venv .venv

    # Activer et installer
    source .venv/bin/activate
    echo "• Installation des dépendances..."
    pip install -q --upgrade pip
    pip install -q -r requirements.txt

    echo "• Installation du navigateur Chromium..."
    playwright install chromium

    echo -e "${GREEN}✅ Configuration terminée!${NC}"
    echo ""
fi

# Activer l'environnement
source .venv/bin/activate

# Menu principal
echo ""
echo "Que veux-tu faire?"
echo ""
echo -e "${GREEN}1)${NC} 🚀 Scanner tout Centris (mode rapide)"
echo -e "${GREEN}2)${NC} ⚡ Scanner en PARALLÈLE (4-6x plus rapide!)"
echo -e "${GREEN}3)${NC} 🎯 Analyser mon image de canard"
echo -e "${GREEN}4)${NC} 🧪 Tester la détection sur une image"
echo -e "${GREEN}5)${NC} 🔄 Fusionner les checkpoints parallèles"
echo -e "${GREEN}6)${NC} 🧹 Nettoyer les résultats"
echo -e "${GREEN}7)${NC} ❌ Quitter"
echo ""
read -p "Choix (1-7): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}⚡ MODE RAPIDE${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Options:"
        echo "  • 8 téléchargements parallèles"
        echo "  • Sauvegarde automatique (checkpoint)"
        echo "  • ~100-200 images/min"
        echo ""
        read -p "Limiter à un nombre de pages? (Enter = tout scanner): " max_pages

        echo ""
        if [ -z "$max_pages" ]; then
            echo -e "${YELLOW}🔍 Scan de TOUT le site...${NC}"
            python3 duck_finder.py --workers 8
        else
            echo -e "${YELLOW}🔍 Scan de $max_pages pages...${NC}"
            python3 duck_finder.py --workers 8 --max-pages "$max_pages"
        fi
        ;;

    2)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🚀 MODE PARALLÈLE${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo -e "${YELLOW}Configuration recommandée:${NC}"
        echo "  • 4-6 instances"
        echo "  • 8-12 workers par instance"
        echo "  • ~400-600 images/min"
        echo "  • 45,000 maisons en 2-3 heures"
        echo ""

        read -p "Nombre d'instances (défaut: 4): " instances
        instances=${instances:-4}

        read -p "Workers par instance (défaut: 8): " workers
        workers=${workers:-8}

        read -p "Total de pages (défaut: 250): " pages
        pages=${pages:-250}

        echo ""
        echo -e "${YELLOW}🚀 Lancement de $instances instances × $workers workers...${NC}"
        echo ""

        python3 parallel_scan.py --total-pages "$pages" --instances "$instances" --workers "$workers"

        echo ""
        echo -e "${GREEN}✅ Scan terminé!${NC}"
        echo ""
        echo "Pour fusionner les résultats: bash run.sh → option 5"
        ;;

    3)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🎯 ANALYSE D'IMAGE DE RÉFÉRENCE${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Place ton image du canard dans: reference/"
        echo "Formats supportés: .jpg, .png, .jpeg, .webp"
        echo ""
        read -p "Chemin de l'image (ex: reference/duck.jpg): " image_path

        if [ -z "$image_path" ]; then
            echo -e "${RED}❌ Aucun chemin spécifié${NC}"
            exit 1
        fi

        if [ ! -f "$image_path" ]; then
            echo -e "${RED}❌ Image non trouvée: $image_path${NC}"
            exit 1
        fi

        echo ""
        python3 analyze_reference.py "$image_path"
        ;;

    4)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🧪 TEST DE DÉTECTION${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        read -p "Chemin de l'image à tester: " test_image

        if [ -z "$test_image" ]; then
            echo -e "${RED}❌ Aucun chemin spécifié${NC}"
            exit 1
        fi

        if [ ! -f "$test_image" ]; then
            echo -e "${RED}❌ Image non trouvée: $test_image${NC}"
            exit 1
        fi

        echo ""
        python3 test_detection.py "$test_image"
        ;;

    5)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🔄 FUSION DES CHECKPOINTS${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        python3 merge_checkpoints.py
        ;;

    6)
        echo ""
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo -e "${GREEN}🧹 NETTOYAGE${NC}"
        echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
        echo ""
        echo "Ceci va supprimer:"
        echo "  • potential_ducks/"
        echo "  • images/ et images_instance_*/"
        echo "  • screenshots/"
        echo "  • test_results/"
        echo "  • logs/"
        echo "  • checkpoint*.json"
        echo ""
        read -p "⚠️  Confirmer? (o/N): " confirm

        if [ "$confirm" = "o" ] || [ "$confirm" = "O" ]; then
            echo ""
            echo "🗑️  Suppression..."
            rm -rf potential_ducks/ images/ images_instance_*/ screenshots/ test_results/ logs/
            rm -f checkpoint*.json
            echo -e "${GREEN}✅ Nettoyage terminé!${NC}"
        else
            echo "Annulé."
        fi
        ;;

    7)
        echo ""
        echo "👋 À bientôt!"
        exit 0
        ;;

    *)
        echo ""
        echo -e "${RED}❌ Choix invalide${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ Terminé!${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
