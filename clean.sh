#!/bin/bash
# Script pour nettoyer les résultats et recommencer à zéro

echo "🧹 Nettoyage des résultats..."
echo ""

# Demander confirmation
read -p "⚠️  Voulez-vous vraiment supprimer tous les résultats et le checkpoint? (o/N): " confirm

if [ "$confirm" != "o" ] && [ "$confirm" != "O" ]; then
    echo "Annulé."
    exit 0
fi

# Compter les fichiers avant suppression
total_files=0
if [ -d "potential_ducks" ]; then
    total_files=$((total_files + $(find potential_ducks -type f | wc -l)))
fi
if [ -d "images" ]; then
    total_files=$((total_files + $(find images -type f | wc -l)))
fi
if [ -d "screenshots" ]; then
    total_files=$((total_files + $(find screenshots -type f | wc -l)))
fi
if [ -d "test_results" ]; then
    total_files=$((total_files + $(find test_results -type f | wc -l)))
fi
if [ -f "checkpoint.json" ]; then
    total_files=$((total_files + 1))
fi

echo ""
echo "Fichiers à supprimer: $total_files"
echo ""

# Supprimer les dossiers de résultats
if [ -d "potential_ducks" ]; then
    echo "🗑️  Suppression de potential_ducks/..."
    rm -rf potential_ducks/*
fi

if [ -d "images" ]; then
    echo "🗑️  Suppression de images/..."
    rm -rf images/*
fi

if [ -d "screenshots" ]; then
    echo "🗑️  Suppression de screenshots/..."
    rm -rf screenshots/*
fi

if [ -d "test_results" ]; then
    echo "🗑️  Suppression de test_results/..."
    rm -rf test_results/*
fi

# Supprimer le checkpoint
if [ -f "checkpoint.json" ]; then
    echo "🗑️  Suppression de checkpoint.json..."
    rm -f checkpoint.json
fi

echo ""
echo "✅ Nettoyage terminé!"
echo ""
echo "Vous pouvez maintenant relancer le scan avec:"
echo "  python duck_finder_complete.py"
echo ""
