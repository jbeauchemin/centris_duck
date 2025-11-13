#!/usr/bin/env python3
"""
Centris Duck Finder - Version Playwright pour sites JavaScript
Utilise Playwright pour naviguer sur centris.ca et trouver le canard mauve
"""

import os
import sys
import time
import asyncio
from pathlib import Path
from typing import List, Dict
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from tqdm import tqdm
from playwright.async_api import async_playwright, Page


class PlaywrightDuckFinder:
    """Finder utilisant Playwright pour gérer le JavaScript"""

    def __init__(self):
        self.results_dir = Path('potential_ducks')
        self.results_dir.mkdir(exist_ok=True)
        self.images_dir = Path('images')
        self.images_dir.mkdir(exist_ok=True)

    async def search_listings(self, page: Page, max_listings: int = 50) -> List[str]:
        """
        Recherche les URLs des propriétés sur Centris
        """
        print("🔍 Recherche des propriétés...")

        # Aller sur la page de recherche
        await page.goto('https://www.centris.ca/fr/propriete~a-vendre?uc=1', wait_until='networkidle')
        await page.wait_for_timeout(2000)

        # Récupérer les liens des propriétés
        property_links = await page.eval_on_selector_all(
            'a.property-thumbnail-item, a[href*="/proprietes/"], div.property-card a',
            'elements => elements.map(e => e.href).filter(h => h && h.includes("/proprietes/"))'
        )

        # Dédupliquer
        property_links = list(set(property_links))[:max_listings]

        print(f"✓ {len(property_links)} propriétés trouvées")
        return property_links

    async def get_property_images(self, page: Page, property_url: str) -> List[str]:
        """
        Récupère toutes les images d'une propriété
        """
        try:
            await page.goto(property_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Essayer de trouver et cliquer sur le bouton de la galerie si présent
            try:
                gallery_button = page.locator('button:has-text("Photos"), .photo-gallery-trigger, [class*="gallery"]').first
                if await gallery_button.count() > 0:
                    await gallery_button.click()
                    await page.wait_for_timeout(1000)
            except:
                pass

            # Récupérer toutes les images
            image_urls = await page.eval_on_selector_all(
                'img[src*="jpg"], img[src*="jpeg"], img[src*="png"], img[data-src*="jpg"], img[data-src*="jpeg"]',
                '''elements => elements.map(img => {
                    return img.src || img.dataset.src || img.getAttribute('data-src');
                }).filter(url => url && url.startsWith('http') && (url.includes('jpg') || url.includes('jpeg') || url.includes('png')))'''
            )

            # Filtrer les petites images (thumbnails, logos, etc.)
            filtered_images = [url for url in image_urls if 'thumb' not in url.lower() and 'logo' not in url.lower()]

            return list(set(filtered_images))

        except Exception as e:
            print(f"⚠ Erreur pour {property_url}: {e}")
            return []

    def detect_purple_duck(self, image_path: Path, property_url: str, image_url: str) -> bool:
        """
        Analyse une image pour détecter du mauve
        """
        try:
            # Charger l'image
            image = cv2.imread(str(image_path))
            if image is None:
                return False

            # Convertir BGR vers HSV
            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Plage de couleur mauve/violet
            # Pour le mauve: Hue ~270-320° → ~135-160 en OpenCV (0-180)
            lower_purple = np.array([130, 50, 50])
            upper_purple = np.array([160, 255, 255])

            # Créer masque
            mask = cv2.inRange(hsv, lower_purple, upper_purple)

            # Appliquer des opérations morphologiques pour réduire le bruit
            kernel = np.ones((5, 5), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

            # Calculer le pourcentage de pixels mauves
            purple_pixels = np.sum(mask > 0)
            total_pixels = mask.shape[0] * mask.shape[1]
            purple_percentage = (purple_pixels / total_pixels) * 100

            # Seuil de détection
            is_suspicious = purple_percentage > 0.5

            if is_suspicious:
                # Sauvegarder l'image suspecte
                filename = f"duck_{int(time.time() * 1000)}_{purple_percentage:.2f}pct.jpg"
                filepath = self.results_dir / filename
                cv2.imwrite(str(filepath), image)

                # Sauvegarder le masque
                mask_filename = f"mask_{int(time.time() * 1000)}.jpg"
                mask_filepath = self.results_dir / mask_filename
                cv2.imwrite(str(mask_filepath), mask)

                # Sauvegarder l'info
                info_file = self.results_dir / f"info_{int(time.time() * 1000)}.txt"
                with open(info_file, 'w') as f:
                    f.write(f"Propriété: {property_url}\n")
                    f.write(f"Image: {image_url}\n")
                    f.write(f"Pixels mauves: {purple_percentage:.2f}%\n")

                print(f"\n🦆 CANARD POTENTIEL TROUVÉ! 🦆")
                print(f"   URL propriété: {property_url}")
                print(f"   Pixels mauves: {purple_percentage:.2f}%")
                print(f"   Sauvegardé: {filepath}")

            return is_suspicious

        except Exception as e:
            print(f"⚠ Erreur d'analyse: {e}")
            return False

    async def download_and_analyze_image(self, page: Page, image_url: str, property_url: str, index: int) -> bool:
        """
        Télécharge et analyse une image
        """
        try:
            # Naviguer vers l'image
            response = await page.request.get(image_url)
            if response.status != 200:
                return False

            # Sauvegarder temporairement
            image_data = await response.body()
            temp_path = self.images_dir / f"temp_{index}_{int(time.time() * 1000)}.jpg"

            with open(temp_path, 'wb') as f:
                f.write(image_data)

            # Analyser
            is_suspicious = self.detect_purple_duck(temp_path, property_url, image_url)

            # Nettoyer si pas suspect
            if not is_suspicious:
                temp_path.unlink()

            return is_suspicious

        except Exception as e:
            print(f"⚠ Erreur téléchargement: {e}")
            return False

    async def run(self):
        """
        Fonction principale
        """
        print("🦆 CENTRIS DUCK FINDER (Playwright) 🦆")
        print("=" * 50)

        async with async_playwright() as p:
            # Lancer le navigateur
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            # Récupérer les listings
            property_urls = await self.search_listings(page, max_listings=50)

            if not property_urls:
                print("❌ Aucune propriété trouvée")
                await browser.close()
                return

            total_images = 0
            suspicious_count = 0

            # Analyser chaque propriété
            for i, prop_url in enumerate(tqdm(property_urls, desc="Analyse des propriétés")):
                print(f"\n[{i+1}/{len(property_urls)}] {prop_url}")

                # Récupérer les images
                images = await self.get_property_images(page, prop_url)
                print(f"  → {len(images)} images trouvées")
                total_images += len(images)

                # Analyser chaque image
                for j, img_url in enumerate(images):
                    is_suspicious = await self.download_and_analyze_image(page, img_url, prop_url, j)
                    if is_suspicious:
                        suspicious_count += 1

                # Petit délai entre les propriétés
                await page.wait_for_timeout(1000)

            await browser.close()

            print("\n" + "=" * 50)
            print(f"✓ Analyse terminée!")
            print(f"  Propriétés analysées: {len(property_urls)}")
            print(f"  Images analysées: {total_images}")
            print(f"  Images suspectes: {suspicious_count}")
            print(f"  Résultats dans: {self.results_dir}/")


async def main():
    """Point d'entrée"""
    finder = PlaywrightDuckFinder()
    await finder.run()


if __name__ == "__main__":
    asyncio.run(main())
