#!/usr/bin/env python3
"""
Centris Duck Finder - VERSION RAPIDE avec parallélisation
Beaucoup plus rapide grâce au téléchargement parallèle et multi-threading
"""

import os
import sys
import time
import json
import asyncio
from pathlib import Path
from typing import List, Dict, Set
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
from io import BytesIO
from playwright.async_api import async_playwright, Page, Browser
import hashlib
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from reference_detector import get_detection_ranges, get_reference_stats


class FastDuckFinder:
    """Finder optimisé pour la vitesse avec parallélisation"""

    def __init__(self, verbose=True, show_browser=False, max_workers=4,
                 checkpoint_file='checkpoint.json', instance_id=None,
                 start_page=None, end_page=None):
        self.verbose = verbose
        self.show_browser = show_browser
        self.max_workers = max_workers  # Nombre de téléchargements parallèles
        self.instance_id = instance_id
        self.start_page = start_page
        self.end_page = end_page

        self.results_dir = Path('potential_ducks')
        self.results_dir.mkdir(exist_ok=True)

        # Si multi-instances, créer des dossiers séparés
        if instance_id:
            self.images_dir = Path(f'images_instance_{instance_id}')
        else:
            self.images_dir = Path('images')
        self.images_dir.mkdir(exist_ok=True)

        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)

        self.checkpoint_file = Path(checkpoint_file)
        self.checkpoint = self.load_checkpoint()

        self.visited_properties: Set[str] = set(self.checkpoint.get('visited_properties', []))
        self.visited_images: Set[str] = set(self.checkpoint.get('visited_images', []))

        self.stats = {
            'total_properties': 0,
            'total_images': 0,
            'suspicious_images': 0,
            'errors': 0,
            'start_time': time.time()
        }

    def log(self, message, force=False):
        """Affiche un message si verbose est activé"""
        if self.verbose or force:
            print(message)

    def load_checkpoint(self) -> Dict:
        """Charge le checkpoint s'il existe"""
        if self.checkpoint_file.exists():
            try:
                with open(self.checkpoint_file, 'r') as f:
                    data = json.load(f)
                    print(f"📂 Checkpoint trouvé: {len(data.get('visited_properties', []))} propriétés déjà analysées")
                    return data
            except Exception as e:
                print(f"⚠ Erreur lecture checkpoint: {e}")
        return {'visited_properties': [], 'visited_images': []}

    def save_checkpoint(self):
        """Sauvegarde la progression"""
        try:
            checkpoint_data = {
                'visited_properties': list(self.visited_properties),
                'visited_images': list(self.visited_images),
                'stats': self.stats,
                'last_update': datetime.now().isoformat()
            }
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
        except Exception as e:
            print(f"⚠ Erreur sauvegarde checkpoint: {e}")

    async def get_total_results_count(self, page: Page) -> int:
        """Récupère le nombre total de résultats"""
        try:
            count_selectors = [
                'text=/\\d+\\s+résultats?/i',
                'text=/\\d+\\s+propriétés?/i',
                '[class*="result-count"]',
                '[class*="total-count"]',
            ]

            for selector in count_selectors:
                try:
                    element = page.locator(selector).first
                    if await element.count() > 0:
                        text = await element.text_content()
                        import re
                        numbers = re.findall(r'\d+', text.replace(' ', '').replace('\xa0', ''))
                        if numbers:
                            return int(numbers[0])
                except:
                    continue
            return 0
        except Exception as e:
            print(f"⚠ Erreur comptage résultats: {e}")
            return 0

    async def search_all_listings(self, page: Page, max_pages=None) -> List[str]:
        """Recherche TOUTES les propriétés en parcourant la pagination"""
        if self.instance_id:
            print(f"🔍 [Instance {self.instance_id}] Recherche propriétés (pages {self.start_page}-{self.end_page})...")
        else:
            print("🔍 Recherche de TOUTES les propriétés sur Centris...")

        all_property_urls = []
        base_search_url = 'https://www.centris.ca/fr/propriete~a-vendre'

        try:
            await page.goto(base_search_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            total_count = await self.get_total_results_count(page)
            if total_count > 0:
                print(f"📊 Total de propriétés trouvées: {total_count}")

            # Déterminer les limites de pages
            if self.start_page and self.end_page:
                start = self.start_page
                end = self.end_page
                print(f"📄 Traitement pages {start} à {end}")
            else:
                start = 1
                end = max_pages or 1000

            page_num = start

            # Naviguer jusqu'à la page de départ si nécessaire
            if start > 1:
                print(f"⏩ Navigation jusqu'à la page {start}...")
                for _ in range(start - 1):
                    next_found = await self.click_next_page(page)
                    if not next_found:
                        print(f"❌ Ne peut pas atteindre la page {start}")
                        return []
                    await page.wait_for_timeout(800)

            while page_num <= end:
                print(f"📄 Page {page_num}...", end=' ', flush=True)

                await page.wait_for_timeout(1000)  # Réduit de 2000 à 1000

                property_links = await self.extract_property_links(page)

                if not property_links:
                    print(f"❌ Aucune propriété")
                    break

                print(f"✓ {len(property_links)} propriétés")
                all_property_urls.extend(property_links)

                next_button_found = await self.click_next_page(page)
                if not next_button_found:
                    print("  ✓ Plus de pages disponibles")
                    break

                page_num += 1
                await page.wait_for_timeout(800)  # Réduit de 2000 à 800

            all_property_urls = list(set(all_property_urls))
            print(f"\n✓ Total: {len(all_property_urls)} propriétés uniques sur {page_num} pages")

        except Exception as e:
            print(f"⚠ Erreur lors de la recherche: {e}")

        return all_property_urls

    async def extract_property_links(self, page: Page) -> List[str]:
        """Extrait tous les liens de propriétés de la page actuelle"""
        try:
            property_selectors = [
                'a[href*="/proprietes/"]',
                'a[href*="/fr/"]',
                'div.property-card a',
                'article a[href*="propriete"]',
                '.property-thumbnail-item',
            ]

            all_links = []
            for selector in property_selectors:
                try:
                    links = await page.eval_on_selector_all(
                        selector,
                        '''elements => elements
                            .map(e => e.href)
                            .filter(h => h && (h.includes('/proprietes/') || h.includes('/fr/')))
                        '''
                    )
                    all_links.extend(links)
                except:
                    continue

            unique_links = list(set(all_links))
            property_links = [
                link for link in unique_links
                if 'propriete' in link.lower() or '/fr/' in link
            ]
            return property_links

        except Exception as e:
            print(f"⚠ Erreur extraction liens: {e}")
            return []

    async def click_next_page(self, page: Page) -> bool:
        """Clique sur le bouton de la page suivante"""
        try:
            next_selectors = [
                'button:has-text("Suivant")',
                'a:has-text("Suivant")',
                'button:has-text("Next")',
                'a:has-text("Next")',
                '.pagination-next',
                'a[aria-label*="Next"]',
                'button[aria-label*="Next"]',
                'a[rel="next"]',
                '.pagination a:last-child',
                '[class*="next"]',
            ]

            for selector in next_selectors:
                try:
                    next_button = page.locator(selector).first
                    if await next_button.count() > 0:
                        is_disabled = await next_button.get_attribute('disabled')
                        is_aria_disabled = await next_button.get_attribute('aria-disabled')

                        if is_disabled or is_aria_disabled == 'true':
                            return False

                        await next_button.click()
                        await page.wait_for_timeout(500)  # Réduit de 1000 à 500
                        return True
                except:
                    continue
            return False

        except Exception as e:
            print(f"⚠ Erreur pagination: {e}")
            return False

    async def get_property_images(self, page: Page, property_url: str) -> List[str]:
        """Récupère toutes les images d'une propriété"""
        try:
            await page.goto(property_url, wait_until='domcontentloaded', timeout=30000)  # domcontentloaded au lieu de networkidle
            await page.wait_for_timeout(1000)  # Réduit de 2000 à 1000

            # Essayer d'ouvrir la galerie
            gallery_selectors = [
                'button:has-text("Photos")',
                'button:has-text("Galerie")',
                '.photo-gallery-trigger',
                '[class*="gallery-button"]',
                'a:has-text("Voir toutes les photos")',
            ]

            for selector in gallery_selectors:
                try:
                    gallery_btn = page.locator(selector).first
                    if await gallery_btn.count() > 0:
                        await gallery_btn.click()
                        await page.wait_for_timeout(800)  # Réduit de 1500 à 800
                        break
                except:
                    continue

            # Récupérer les URLs d'images
            image_urls = await page.eval_on_selector_all(
                'img[src], img[data-src]',
                '''elements => elements.map(img => {
                    const src = img.src || img.dataset.src || img.getAttribute('data-src');
                    return src;
                }).filter(url =>
                    url &&
                    url.startsWith('http') &&
                    (url.includes('.jpg') || url.includes('.jpeg') || url.includes('.png')) &&
                    !url.includes('logo') &&
                    !url.includes('icon') &&
                    !url.includes('thumb')
                )'''
            )

            unique_images = []
            for url in set(image_urls):
                high_res_url = url.replace('_small', '').replace('_medium', '').replace('_thumb', '')
                unique_images.append(high_res_url)

            return list(set(unique_images))

        except Exception as e:
            print(f"⚠ Erreur récupération images: {e}")
            return []

    def detect_purple_duck(self, image_path: Path, property_url: str, image_url: str) -> bool:
        """Analyse une image pour détecter le canard mauve"""
        try:
            image = cv2.imread(str(image_path))
            if image is None:
                return False

            hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

            # Obtenir les plages de détection (profil de référence ou valeurs par défaut)
            ranges = get_detection_ranges(use_tolerant=False)

            # Créer le masque avec les plages
            lower_exact, upper_exact = ranges['exact']
            mask1 = cv2.inRange(hsv, lower_exact, upper_exact)

            # Si on a une plage shadow (mode par défaut), l'ajouter
            if ranges['shadow'] is not None:
                lower_shadow, upper_shadow = ranges['shadow']
                mask2 = cv2.inRange(hsv, lower_shadow, upper_shadow)
                mask = cv2.bitwise_or(mask1, mask2)
            else:
                mask = mask1

            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

            purple_pixels = np.sum(mask > 0)
            total_pixels = mask.shape[0] * mask.shape[1]
            purple_percentage = (purple_pixels / total_pixels) * 100

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 500]
            max_contour_area = max([cv2.contourArea(cnt) for cnt in significant_contours], default=0)

            is_suspicious = (
                (purple_percentage > 1.0 and len(significant_contours) > 0) or
                (max_contour_area > 2000)
            )

            if is_suspicious:
                timestamp = int(time.time() * 1000)
                filename = f"duck_{timestamp}_{purple_percentage:.2f}pct.jpg"
                filepath = self.results_dir / filename
                cv2.imwrite(str(filepath), image)

                mask_filename = f"mask_{timestamp}.jpg"
                cv2.imwrite(str(self.results_dir / mask_filename), mask)

                contour_image = image.copy()
                cv2.drawContours(contour_image, significant_contours, -1, (0, 255, 0), 2)
                cv2.imwrite(str(self.results_dir / f"contours_{timestamp}.jpg"), contour_image)

                info_file = self.results_dir / f"info_{timestamp}.txt"
                with open(info_file, 'w', encoding='utf-8') as f:
                    f.write(f"Propriété: {property_url}\n")
                    f.write(f"Image: {image_url}\n")
                    f.write(f"Pixels mauves: {purple_percentage:.2f}%\n")
                    f.write(f"Contours trouvés: {len(significant_contours)}\n")
                    f.write(f"Plus gros contour: {max_contour_area} pixels²\n")
                    f.write(f"Couleur cible: #c97ef2 (violet)\n")
                    f.write(f"Date: {datetime.now().isoformat()}\n")

                print(f"\n🦆 CANARD POTENTIEL TROUVÉ! 🦆")
                print(f"   Pixels: {purple_percentage:.2f}% | Contours: {len(significant_contours)} | Max: {max_contour_area:.0f}px²")

                self.stats['suspicious_images'] += 1

            return is_suspicious

        except Exception as e:
            return False

    async def download_and_analyze_image_batch(self, session: aiohttp.ClientSession, images_data: List[tuple]) -> List[bool]:
        """Télécharge et analyse un batch d'images en parallèle"""
        results = []

        async def process_single_image(img_url, property_url, index):
            image_hash = hashlib.md5(img_url.encode()).hexdigest()
            if image_hash in self.visited_images:
                return False

            try:
                async with session.get(img_url, timeout=aiohttp.ClientTimeout(total=15)) as response:
                    if response.status != 200:
                        return False

                    image_data = await response.read()
                    temp_path = self.images_dir / f"temp_{image_hash}.jpg"

                    with open(temp_path, 'wb') as f:
                        f.write(image_data)

                    # Analyse dans un thread séparé pour ne pas bloquer
                    loop = asyncio.get_event_loop()
                    is_suspicious = await loop.run_in_executor(
                        None,
                        self.detect_purple_duck,
                        temp_path,
                        property_url,
                        img_url
                    )

                    self.visited_images.add(image_hash)
                    self.stats['total_images'] += 1

                    if not is_suspicious and temp_path.exists():
                        temp_path.unlink()

                    return is_suspicious

            except Exception as e:
                self.stats['errors'] += 1
                return False

        # Traiter toutes les images en parallèle
        tasks = [process_single_image(img_url, prop_url, idx) for idx, (img_url, prop_url) in enumerate(images_data)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        return [r for r in results if not isinstance(r, Exception)]

    async def run(self, max_pages=None):
        """Fonction principale optimisée"""
        self.log("🦆 CENTRIS DUCK FINDER - VERSION RAPIDE ⚡", force=True)
        self.log("=" * 60, force=True)
        self.log(f"Parallélisation: {self.max_workers} workers", force=True)

        # Afficher les infos de référence
        ref_stats = get_reference_stats()
        if ref_stats['has_reference']:
            self.log(f"🎯 Image de référence: {ref_stats['image_path']}", force=True)
            pure_color = ref_stats['pure_color']
            self.log(f"   Couleur: H={pure_color['hue']:.0f}, S={pure_color['saturation']:.0f}, V={pure_color['value']:.0f}", force=True)
        else:
            self.log(f"🎯 Couleur par défaut: {ref_stats['default_color']}", force=True)

        self.log("=" * 60, force=True)

        async with async_playwright() as p:
            self.log("\n🌐 Lancement du navigateur...", force=True)
            browser = await p.chromium.launch(
                headless=not self.show_browser,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()

            try:
                all_properties = await self.search_all_listings(page, max_pages)

                if not all_properties:
                    print("❌ Aucune propriété trouvée")
                    await browser.close()
                    return

                properties_to_analyze = [
                    url for url in all_properties
                    if url not in self.visited_properties
                ]

                print(f"\n📊 Propriétés à analyser: {len(properties_to_analyze)}/{len(all_properties)}")

                # Créer une session aiohttp pour les téléchargements parallèles
                async with aiohttp.ClientSession() as session:
                    self.log("\n" + "=" * 60, force=True)
                    self.log("🔍 Début de l'analyse...", force=True)

                    for i, prop_url in enumerate(properties_to_analyze):
                        elapsed = time.time() - self.stats['start_time']
                        self.log(f"\n{'='*60}", force=True)
                        self.log(f"📍 [{i+1}/{len(properties_to_analyze)}] | ⏱️ {elapsed/60:.1f}min | 🖼️ {self.stats['total_images']} | 🦆 {self.stats['suspicious_images']}", force=True)
                        self.log(f"🔗 {prop_url}", force=True)

                        try:
                            self.log(f"  🖼️  Chargement...", force=True)
                            images = await self.get_property_images(page, prop_url)
                            self.log(f"  ✓ {len(images)} images | Téléchargement parallèle...", force=True)

                            # Télécharger et analyser toutes les images en parallèle
                            images_data = [(img_url, prop_url) for img_url in images]

                            # Traiter par batch pour ne pas surcharger
                            batch_size = self.max_workers * 2
                            for batch_start in range(0, len(images_data), batch_size):
                                batch = images_data[batch_start:batch_start + batch_size]
                                await self.download_and_analyze_image_batch(session, batch)

                            self.visited_properties.add(prop_url)
                            self.stats['total_properties'] += 1

                            if (i + 1) % 10 == 0:
                                self.save_checkpoint()
                                self.log(f"  💾 Checkpoint sauvegardé", force=True)

                        except Exception as e:
                            self.log(f"  ⚠️  Erreur: {e}", force=True)
                            self.stats['errors'] += 1
                            continue

                self.save_checkpoint()

            finally:
                await browser.close()

            elapsed_time = time.time() - self.stats['start_time']
            print("\n" + "=" * 60)
            print("✓ ANALYSE TERMINÉE!")
            print("=" * 60)
            print(f"  Propriétés: {self.stats['total_properties']}")
            print(f"  Images: {self.stats['total_images']}")
            print(f"  Canards potentiels: {self.stats['suspicious_images']}")
            print(f"  Erreurs: {self.stats['errors']}")
            print(f"  Temps: {elapsed_time/60:.1f} minutes")
            print(f"  Vitesse: {self.stats['total_images']/(elapsed_time/60):.1f} images/min")
            print("=" * 60)

            if self.stats['suspicious_images'] > 0:
                print(f"\n🎉 {self.stats['suspicious_images']} canard(s) trouvé(s) dans {self.results_dir}/")


async def main():
    """Point d'entrée"""
    import argparse

    parser = argparse.ArgumentParser(description='Centris Duck Finder RAPIDE')
    parser.add_argument('--show-browser', action='store_true', help='Affiche le navigateur')
    parser.add_argument('--quiet', action='store_true', help='Mode silencieux')
    parser.add_argument('--workers', type=int, default=8, help='Nombre de workers parallèles (défaut: 8)')
    parser.add_argument('--max-pages', type=int, help='Limite le nombre de pages à scanner')
    parser.add_argument('--start-page', type=int, help='Page de départ (pour multi-instances)')
    parser.add_argument('--end-page', type=int, help='Page de fin (pour multi-instances)')
    parser.add_argument('--checkpoint', type=str, default='checkpoint.json', help='Fichier de checkpoint')
    parser.add_argument('--instance-id', type=int, help='ID de l\'instance (pour multi-instances)')

    args = parser.parse_args()

    verbose = not args.quiet
    show_browser = args.show_browser
    max_workers = args.workers
    max_pages = args.max_pages
    start_page = args.start_page
    end_page = args.end_page
    checkpoint_file = args.checkpoint
    instance_id = args.instance_id

    if instance_id:
        print(f"\n⚡ INSTANCE {instance_id} - {max_workers} workers")
        print(f"📄 Pages {start_page} à {end_page}")
    else:
        print(f"\n⚡ MODE RAPIDE - {max_workers} workers en parallèle")
        if max_pages:
            print(f"📄 Limité à {max_pages} pages")

    finder = FastDuckFinder(
        verbose=verbose,
        show_browser=show_browser,
        max_workers=max_workers,
        checkpoint_file=checkpoint_file,
        instance_id=instance_id,
        start_page=start_page,
        end_page=end_page
    )
    await finder.run(max_pages=max_pages)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêt demandé")
        print("Progression sauvegardée dans checkpoint.json")
