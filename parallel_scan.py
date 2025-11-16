#!/usr/bin/env python3
"""
Lanceur parallèle pour scanner Centris avec plusieurs instances
Divise le travail en tranches et lance plusieurs processus en parallèle
"""

import subprocess
import sys
import time
from pathlib import Path
import json
from datetime import datetime


def run_parallel_scan(total_pages=250, num_instances=4, workers_per_instance=8):
    """
    Lance plusieurs instances du scanner en parallèle

    Args:
        total_pages: Nombre total de pages à scanner
        num_instances: Nombre d'instances parallèles à lancer
        workers_per_instance: Nombre de workers par instance
    """

    print("🚀 CENTRIS DUCK FINDER - MODE PARALLÈLE")
    print("=" * 60)
    print(f"Configuration:")
    print(f"  Total de pages: {total_pages}")
    print(f"  Instances parallèles: {num_instances}")
    print(f"  Workers par instance: {workers_per_instance}")
    print(f"  Total workers: {num_instances * workers_per_instance}")
    print("=" * 60)

    # Créer les dossiers de logs
    logs_dir = Path('logs')
    logs_dir.mkdir(exist_ok=True)

    # Calculer les tranches de pages pour chaque instance
    pages_per_instance = total_pages // num_instances
    remainder = total_pages % num_instances

    print(f"\n📊 Division du travail:")

    processes = []
    start_page = 1

    for i in range(num_instances):
        # Calculer la plage pour cette instance
        end_page = start_page + pages_per_instance - 1

        # Distribuer le reste sur les premières instances
        if i < remainder:
            end_page += 1

        num_pages = end_page - start_page + 1

        print(f"  Instance {i+1}: Pages {start_page}-{end_page} ({num_pages} pages)")

        # Créer un fichier de checkpoint unique pour cette instance
        checkpoint_file = f"checkpoint_instance_{i+1}.json"

        # Log file pour cette instance
        log_file = logs_dir / f"instance_{i+1}.log"

        # Commande pour cette instance
        cmd = [
            sys.executable,
            "duck_finder_fast.py",
            "--workers", str(workers_per_instance),
            "--start-page", str(start_page),
            "--end-page", str(end_page),
            "--checkpoint", checkpoint_file,
            "--instance-id", str(i+1)
        ]

        # Lancer le processus
        log_handle = open(log_file, 'w')
        process = subprocess.Popen(
            cmd,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            text=True
        )

        processes.append({
            'id': i+1,
            'process': process,
            'log_file': log_file,
            'log_handle': log_handle,
            'start_page': start_page,
            'end_page': end_page,
            'checkpoint': checkpoint_file
        })

        start_page = end_page + 1

        # Petit délai entre les lancements
        time.sleep(2)

    print(f"\n✅ {len(processes)} instances lancées!")
    print(f"\n📝 Logs disponibles dans: {logs_dir}/")
    print(f"   Utilise: tail -f logs/instance_1.log")
    print(f"\n⏱️  Surveillance en cours... (Ctrl+C pour arrêter)")

    # Surveiller les processus
    try:
        while True:
            time.sleep(5)

            # Vérifier l'état de chaque processus
            running = 0
            completed = 0

            for proc_info in processes:
                poll = proc_info['process'].poll()
                if poll is None:
                    running += 1
                else:
                    completed += 1

            # Afficher le statut
            print(f"\r🔄 En cours: {running} | ✅ Terminées: {completed}", end='', flush=True)

            # Si tous les processus sont terminés
            if completed == len(processes):
                print(f"\n\n{'='*60}")
                print("🎉 TOUTES LES INSTANCES SONT TERMINÉES!")
                print("="*60)
                break

    except KeyboardInterrupt:
        print(f"\n\n⚠️  Arrêt demandé...")
        print("Arrêt des instances en cours...")

        for proc_info in processes:
            proc_info['process'].terminate()

        # Attendre que tous se terminent
        for proc_info in processes:
            proc_info['process'].wait()
            proc_info['log_handle'].close()

        print("✓ Toutes les instances arrêtées")
        print("La progression a été sauvegardée dans les checkpoints individuels")
        return

    # Fermer les handles de logs
    for proc_info in processes:
        proc_info['log_handle'].close()

    # Afficher les résultats de chaque instance
    print(f"\n📊 Résultats par instance:")
    print("="*60)

    total_properties = 0
    total_images = 0
    total_suspicious = 0

    for proc_info in processes:
        checkpoint_path = Path(proc_info['checkpoint'])
        if checkpoint_path.exists():
            with open(checkpoint_path, 'r') as f:
                data = json.load(f)
                stats = data.get('stats', {})

                props = stats.get('total_properties', 0)
                imgs = stats.get('total_images', 0)
                sus = stats.get('suspicious_images', 0)

                total_properties += props
                total_images += imgs
                total_suspicious += sus

                print(f"  Instance {proc_info['id']}: {props} propriétés | {imgs} images | {sus} canards")

    print("="*60)
    print(f"  TOTAL: {total_properties} propriétés | {total_images} images | {total_suspicious} canards")
    print("="*60)

    if total_suspicious > 0:
        print(f"\n🦆 {total_suspicious} canard(s) potentiel(s) trouvé(s)!")
        print(f"Vérifie les images dans potential_ducks/")

    print(f"\n💡 Pour fusionner les checkpoints:")
    print(f"   python merge_checkpoints.py")


def main():
    """Point d'entrée"""
    import argparse

    parser = argparse.ArgumentParser(description='Lance plusieurs instances en parallèle')
    parser.add_argument('--total-pages', type=int, default=250,
                        help='Nombre total de pages à scanner (défaut: 250)')
    parser.add_argument('--instances', type=int, default=4,
                        help='Nombre d\'instances parallèles (défaut: 4)')
    parser.add_argument('--workers', type=int, default=8,
                        help='Workers par instance (défaut: 8)')

    args = parser.parse_args()

    # Recommandations basées sur les specs
    print("\n💻 Configuration système détectée:")
    print("   MacBook Pro M2 avec 32GB RAM")
    print("\n📊 Recommandations:")
    print("   - 4-6 instances pour un bon équilibre")
    print("   - 8-12 workers par instance")
    print("   - Total: 32-72 workers simultanés")
    print()

    confirm = input("Continuer avec cette configuration? (o/N): ")
    if confirm.lower() != 'o':
        print("Annulé.")
        return

    run_parallel_scan(
        total_pages=args.total_pages,
        num_instances=args.instances,
        workers_per_instance=args.workers
    )


if __name__ == "__main__":
    main()
