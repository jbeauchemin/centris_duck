#!/usr/bin/env python3
"""
Centris Duck Finder - Cherche le canard mauve caché dans les propriétés de centris.ca
"""

import os
import sys
import time
import requests
from pathlib import Path
from typing import List, Tuple, Dict
from urllib.parse import urljoin
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from bs4 import BeautifulSoup


class DuckFinder:
    """Classe principale pour trouver le canard mauve sur Centris"""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.results_dir = Path('potential_ducks')
        self.results_dir.mkdir(exist_ok=True)

    def get_listings(self, max_pages: int = 5) -> List[Dict]:
        """
        Récupère les listings de propriétés sur Centris
        """
        print("🔍 Récupération des listings de propriétés...")
        listings = []

        # URL de recherche Centris pour les propriétés à vendre
        base_url = "https://www.centris.ca/fr/propriete~a-vendre?uc=1"

        try:
            response = self.session.get(base_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Trouver les liens vers les propriétés
            property_links = soup.find_all('a', class_='property-thumbnail-item')

            for link in property_links[:50]:  # Limiter à 50 propriétés pour commencer
                href = link.get('href')
                if href:
                    full_url = urljoin(base_url, href)
                    listings.append({'url': full_url})

            print(f"✓ {len(listings)} propriétés trouvées")

        except Exception as e:
            print(f"⚠ Erreur lors de la récupération des listings: {e}")

        return listings

    def get_property_images(self, property_url: str) -> List[str]:
        """
        Récupère toutes les URLs des images d'une propriété
        """
        images = []

        try:
            response = self.session.get(property_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # Chercher les images dans la galerie
            img_tags = soup.find_all('img', class_='photo')

            for img in img_tags:
                src = img.get('src') or img.get('data-src')
                if src:
                    full_url = urljoin(property_url, src)
                    images.append(full_url)

        except Exception as e:
            print(f"⚠ Erreur pour {property_url}: {e}")

        return images

    def detect_purple_duck(self, image_url: str, property_url: str) -> Tuple[bool, float]:
        """
        Analyse une image pour détecter la présence d'un canard mauve

        Returns:
            (is_suspicious, purple_score): True si l'image contient beaucoup de mauve
        """
        try:
            # Télécharger l'image
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()

            # Convertir en format numpy pour OpenCV
            image = Image.open(BytesIO(response.content))
            image_array = np.array(image)

            # Convertir RGB vers HSV
            if len(image_array.shape) == 2:  # Image en niveaux de gris
                return False, 0.0

            hsv = cv2.cvtColor(image_array, cv2.COLOR_RGB2HSV)

            # Définir la plage de couleur mauve/violet
            # Mauve/Violet: Hue entre 270-320° (normalisé à 0-180 pour OpenCV)
            # On cherche: Hue ~130-160, Saturation >50, Value >50
            lower_purple1 = np.array([130, 50, 50])
            upper_purple1 = np.array([160, 255, 255])

            # Créer un masque pour les pixels mauves
            mask = cv2.inRange(hsv, lower_purple1, upper_purple1)

            # Calculer le pourcentage de pixels mauves
            purple_pixels = np.sum(mask > 0)
            total_pixels = mask.shape[0] * mask.shape[1]
            purple_percentage = (purple_pixels / total_pixels) * 100

            # Si plus de 0.5% de pixels mauves, c'est suspect
            is_suspicious = purple_percentage > 0.5

            if is_suspicious:
                # Sauvegarder l'image suspecte
                filename = f"duck_{int(time.time())}_{purple_percentage:.2f}pct.jpg"
                filepath = self.results_dir / filename
                image.save(filepath)

                # Sauvegarder aussi le masque
                mask_filename = f"mask_{int(time.time())}.jpg"
                mask_filepath = self.results_dir / mask_filename
                cv2.imwrite(str(mask_filepath), mask)

                print(f"\n🦆 CANARD POTENTIEL TROUVÉ! 🦆")
                print(f"   URL propriété: {property_url}")
                print(f"   URL image: {image_url}")
                print(f"   Pixels mauves: {purple_percentage:.2f}%")
                print(f"   Sauvegardé: {filepath}")

            return is_suspicious, purple_percentage

        except Exception as e:
            print(f"⚠ Erreur d'analyse: {e}")
            return False, 0.0

    def search_for_duck(self):
        """
        Fonction principale: cherche le canard dans toutes les propriétés
        """
        print("🦆 CENTRIS DUCK FINDER 🦆")
        print("=" * 50)

        # Récupérer les listings
        listings = self.get_listings()

        if not listings:
            print("❌ Aucune propriété trouvée")
            return

        total_images = 0
        suspicious_images = 0

        # Parcourir chaque propriété
        for i, listing in enumerate(tqdm(listings, desc="Analyse des propriétés")):
            property_url = listing['url']

            # Récupérer les images de cette propriété
            images = self.get_property_images(property_url)
            total_images += len(images)

            # Analyser chaque image
            for img_url in images:
                is_suspicious, score = self.detect_purple_duck(img_url, property_url)
                if is_suspicious:
                    suspicious_images += 1

                # Petit délai pour être poli avec le serveur
                time.sleep(0.5)

        print("\n" + "=" * 50)
        print(f"✓ Analyse terminée!")
        print(f"  Images analysées: {total_images}")
        print(f"  Images suspectes: {suspicious_images}")
        print(f"  Résultats dans: {self.results_dir}/")


def main():
    """Point d'entrée du script"""
    finder = DuckFinder()
    finder.search_for_duck()


if __name__ == "__main__":
    main()
