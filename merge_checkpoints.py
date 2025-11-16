#!/usr/bin/env python3
"""
Fusionne les checkpoints de toutes les instances parallèles
"""

import json
from pathlib import Path
from datetime import datetime


def merge_checkpoints():
    """Fusionne tous les checkpoints d'instances en un seul"""

    print("🔄 Fusion des checkpoints...")
    print("=" * 60)

    # Trouver tous les fichiers de checkpoint d'instances
    checkpoint_files = list(Path('.').glob('checkpoint_instance_*.json'))

    if not checkpoint_files:
        print("❌ Aucun checkpoint d'instance trouvé")
        return

    print(f"📁 Trouvé {len(checkpoint_files)} checkpoints")

    # Ensembles combinés
    all_visited_properties = set()
    all_visited_images = set()

    # Stats combinées
    combined_stats = {
        'total_properties': 0,
        'total_images': 0,
        'suspicious_images': 0,
        'errors': 0,
        'start_time': float('inf')
    }

    # Lire chaque checkpoint
    for checkpoint_file in sorted(checkpoint_files):
        print(f"  📄 {checkpoint_file.name}...", end=' ')

        try:
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)

            # Ajouter les propriétés visitées
            visited_props = set(data.get('visited_properties', []))
            all_visited_properties.update(visited_props)

            # Ajouter les images visitées
            visited_imgs = set(data.get('visited_images', []))
            all_visited_images.update(visited_imgs)

            # Combiner les stats
            stats = data.get('stats', {})
            combined_stats['total_properties'] += stats.get('total_properties', 0)
            combined_stats['total_images'] += stats.get('total_images', 0)
            combined_stats['suspicious_images'] += stats.get('suspicious_images', 0)
            combined_stats['errors'] += stats.get('errors', 0)

            if stats.get('start_time'):
                combined_stats['start_time'] = min(
                    combined_stats['start_time'],
                    stats['start_time']
                )

            print(f"✓ {stats.get('total_properties', 0)} propriétés, {stats.get('total_images', 0)} images")

        except Exception as e:
            print(f"❌ Erreur: {e}")

    # Créer le checkpoint combiné
    merged_checkpoint = {
        'visited_properties': list(all_visited_properties),
        'visited_images': list(all_visited_images),
        'stats': combined_stats,
        'last_update': datetime.now().isoformat(),
        'merged_from': [str(f) for f in checkpoint_files]
    }

    # Sauvegarder
    output_file = Path('checkpoint_merged.json')
    with open(output_file, 'w') as f:
        json.dump(merged_checkpoint, f, indent=2)

    print("\n" + "=" * 60)
    print("✅ Fusion terminée!")
    print(f"📊 Résultats combinés:")
    print(f"   Propriétés visitées: {len(all_visited_properties)}")
    print(f"   Images visitées: {len(all_visited_images)}")
    print(f"   Canards trouvés: {combined_stats['suspicious_images']}")
    print(f"   Erreurs: {combined_stats['errors']}")
    print(f"\n💾 Sauvegardé dans: {output_file}")
    print("=" * 60)

    # Option pour nettoyer les checkpoints individuels
    print(f"\nVoulez-vous supprimer les checkpoints individuels?")
    response = input("(o/N): ")

    if response.lower() == 'o':
        for checkpoint_file in checkpoint_files:
            checkpoint_file.unlink()
            print(f"  🗑️  Supprimé: {checkpoint_file.name}")
        print("✓ Checkpoints individuels supprimés")


if __name__ == "__main__":
    merge_checkpoints()
