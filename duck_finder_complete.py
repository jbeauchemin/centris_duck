#!/usr/bin/env python3
"""
Centris Duck Finder - Version complète avec pagination et checkpoints
Parcourt TOUTES les propriétés de Centris.ca pour trouver le canard mauve
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
from tqdm import tqdm
from playwright.async_api import async_playwright, Page, Browser
import hashlib
from reference_detector import get_detection_ranges, get_reference_stats


class CompleteDuckFinder:
    """Finder complet avec pagination et système de reprise"""

    def __init__(self, verbose=True, show_browser=False):
        self.verbose = verbose
        self.show_browser = show_browser

        self.results_dir = Path('potential_ducks')
        self.results_dir.mkdir(exist_ok=True)

        self.images_dir = Path('images')
        self.images_dir.mkdir(exist_ok=True)

        self.screenshots_dir = Path('screenshots')
        self.screenshots_dir.mkdir(exist_ok=True)

        # Fichier de checkpoint pour sauvegarder la progression
        self.checkpoint_file = Path('checkpoint.json')
        self.checkpoint = self.load_checkpoint()

        # Set pour tracker les URLs déjà visitées
        self.visited_properties: Set[str] = set(self.checkpoint.get('visited_properties', []))
        self.visited_images: Set[str] = set(self.checkpoint.get('visited_images', []))

        # Statistiques
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
        """Récupère le nombre total de résultats de la recherche"""
        try:
            # Chercher l'indicateur du nombre de résultats
            # Centris affiche généralement "X résultats" quelque part
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
                        # Extraire le nombre
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

    async def search_all_listings(self, page: Page) -> List[str]:
        """
        Recherche TOUTES les propriétés en parcourant toutes les pages de pagination
        """
        print("🔍 Recherche de TOUTES les propriétés sur Centris...")
        all_property_urls = []

        # URL de base pour la recherche
        base_search_url = 'https://www.centris.ca/fr/propriete~a-vendre'

        try:
            # Aller sur la première page
            await page.goto(base_search_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(3000)

            # Prendre une capture d'écran pour debug
            await page.screenshot(path=str(self.screenshots_dir / 'search_page_1.png'))

            # Obtenir le nombre total de résultats
            total_count = await self.get_total_results_count(page)
            if total_count > 0:
                print(f"📊 Total de propriétés trouvées: {total_count}")

            page_num = 1
            max_pages = 1000  # Limite de sécurité

            while page_num <= max_pages:
                print(f"\n📄 Page {page_num}...")

                # Attendre que la page charge
                await page.wait_for_timeout(2000)

                # Récupérer tous les liens de propriétés sur cette page
                property_links = await self.extract_property_links(page)

                if not property_links:
                    print(f"  ❌ Aucune propriété trouvée sur la page {page_num}")
                    break

                print(f"  ✓ {len(property_links)} propriétés trouvées sur cette page")
                all_property_urls.extend(property_links)

                # Chercher le bouton "Page suivante" ou "Next"
                next_button_found = await self.click_next_page(page)

                if not next_button_found:
                    print("  ✓ Plus de pages disponibles")
                    break

                page_num += 1

                # Petit délai entre les pages
                await page.wait_for_timeout(2000)

            # Dédupliquer
            all_property_urls = list(set(all_property_urls))
            print(f"\n✓ Total: {len(all_property_urls)} propriétés uniques trouvées sur {page_num} pages")

        except Exception as e:
            print(f"⚠ Erreur lors de la recherche: {e}")

        return all_property_urls

    async def extract_property_links(self, page: Page) -> List[str]:
        """Extrait tous les liens de propriétés de la page actuelle"""
        try:
            # Différents sélecteurs possibles pour les liens de propriétés
            property_selectors = [
                'a[href*="/proprietes/"]',
                'a[href*="propriete~a-vendre"]',
                'div.property-card a',
                'article a[href*="propriete"]',
                '.property-thumbnail-item',
                'a.property-link',
                '[data-id^="Prop"]',
            ]

            all_links = []

            # Essayer tous les sélecteurs
            for selector in property_selectors:
                try:
                    links = await page.eval_on_selector_all(
                        selector,
                        '''elements => elements
                            .map(e => e.href)
                            .filter(h => h && h.includes('/proprietes/'))
                        '''
                    )
                    all_links.extend(links)
                except:
                    continue

            # Dédupliquer
            unique_links = list(set(all_links))

            # Filtrer STRICTEMENT pour ne garder que les vraies annonces de propriétés
            property_links = [
                link for link in unique_links
                if '/proprietes/' in link and  # DOIT avoir /proprietes/
                   'blogue' not in link.lower() and  # PAS de blog
                   'conseil' not in link.lower() and  # PAS de conseils
                   'nouvelles' not in link.lower() and  # PAS de nouvelles
                   'immobilier' not in link.lower()  # PAS d'articles généraux
            ]

            return property_links

        except Exception as e:
            print(f"⚠ Erreur extraction liens: {e}")
            return []

    async def click_next_page(self, page: Page) -> bool:
        """
        Clique sur le bouton de la page suivante
        Retourne True si le bouton a été trouvé et cliqué, False sinon
        """
        try:
            # Différents sélecteurs possibles pour la pagination
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
                        # Vérifier que le bouton n'est pas désactivé
                        is_disabled = await next_button.get_attribute('disabled')
                        is_aria_disabled = await next_button.get_attribute('aria-disabled')

                        if is_disabled or is_aria_disabled == 'true':
                            return False

                        # Cliquer sur le bouton
                        await next_button.click()
                        await page.wait_for_timeout(1000)
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
            await page.goto(property_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Essayer de trouver et ouvrir la galerie
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
                        await page.wait_for_timeout(1500)
                        break
                except:
                    continue

            # Récupérer toutes les URLs d'images
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

            # Dédupliquer et convertir en version haute résolution si possible
            unique_images = []
            for url in set(image_urls):
                # Essayer de convertir en version haute résolution
                # Centris utilise souvent des suffixes comme _small, _medium
                high_res_url = url.replace('_small', '').replace('_medium', '').replace('_thumb', '')
                unique_images.append(high_res_url)

            return list(set(unique_images))

        except Exception as e:
            print(f"⚠ Erreur récupération images pour {property_url}: {e}")
            return []

    def detect_purple_duck(self, image_path: Path, property_url: str, image_url: str) -> bool:
        """
        Analyse avancée pour détecter un canard mauve
        Utilise détection de couleur + détection de contours
        Couleur cible du canard: #c97ef2 (RGB: 201, 126, 242) -> HSV: (139, 122, 242)
        """
        try:
            # Charger l'image
            image = cv2.imread(str(image_path))
            if image is None:
                return False

            # Convertir en HSV
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

            # Opérations morphologiques pour nettoyer
            kernel = np.ones((3, 3), np.uint8)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

            # Calculer le pourcentage de pixels mauves
            purple_pixels = np.sum(mask > 0)
            total_pixels = mask.shape[0] * mask.shape[1]
            purple_percentage = (purple_pixels / total_pixels) * 100

            # Détecter des contours pour voir si c'est une forme cohérente (un canard!)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            # Filtrer les contours par taille - un canard devrait être assez gros dans l'image
            # Augmenté à 500 pixels pour éviter les faux positifs
            significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 500]

            # Calculer la taille du plus gros contour
            max_contour_area = max([cv2.contourArea(cnt) for cnt in significant_contours], default=0)

            # Critères de suspicion STRICTS pour réduire les faux positifs:
            # 1. Au moins 1% de pixels mauves (augmenté de 0.3%)
            # 2. ET au moins un contour significatif de >500 pixels
            # 3. OU un très gros contour de >2000 pixels (probablement un canard!)
            is_suspicious = (
                (purple_percentage > 1.0 and len(significant_contours) > 0) or
                (max_contour_area > 2000)
            )

            if is_suspicious:
                # Sauvegarder l'image suspecte
                timestamp = int(time.time() * 1000)
                filename = f"duck_{timestamp}_{purple_percentage:.2f}pct.jpg"
                filepath = self.results_dir / filename
                cv2.imwrite(str(filepath), image)

                # Sauvegarder le masque
                mask_filename = f"mask_{timestamp}.jpg"
                mask_filepath = self.results_dir / mask_filename
                cv2.imwrite(str(mask_filepath), mask)

                # Sauvegarder l'image avec contours
                contour_image = image.copy()
                cv2.drawContours(contour_image, significant_contours, -1, (0, 255, 0), 2)
                contour_filename = f"contours_{timestamp}.jpg"
                cv2.imwrite(str(self.results_dir / contour_filename), contour_image)

                # Sauvegarder l'info
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
                print(f"   Pixels mauves: {purple_percentage:.2f}%")
                print(f"   Contours: {len(significant_contours)}")
                print(f"   Plus gros contour: {max_contour_area} pixels²")
                print(f"   Fichier: {filename}")

                self.stats['suspicious_images'] += 1

            return is_suspicious

        except Exception as e:
            print(f"⚠ Erreur analyse: {e}")
            self.stats['errors'] += 1
            return False

    async def download_and_analyze_image(self, page: Page, image_url: str, property_url: str) -> bool:
        """Télécharge et analyse une image"""

        # Vérifier si déjà visitée
        image_hash = hashlib.md5(image_url.encode()).hexdigest()
        if image_hash in self.visited_images:
            return False

        try:
            # Télécharger l'image
            response = await page.request.get(image_url, timeout=30000)
            if response.status != 200:
                return False

            # Sauvegarder temporairement
            image_data = await response.body()
            temp_path = self.images_dir / f"temp_{image_hash}.jpg"

            with open(temp_path, 'wb') as f:
                f.write(image_data)

            # Analyser
            is_suspicious = self.detect_purple_duck(temp_path, property_url, image_url)

            # Marquer comme visitée
            self.visited_images.add(image_hash)
            self.stats['total_images'] += 1

            # Nettoyer si pas suspect
            if not is_suspicious and temp_path.exists():
                temp_path.unlink()

            return is_suspicious

        except Exception as e:
            print(f"⚠ Erreur téléchargement: {e}")
            self.stats['errors'] += 1
            return False

    async def run(self):
        """Fonction principale"""
        self.log("🦆 CENTRIS DUCK FINDER - VERSION COMPLÈTE 🦆", force=True)
        self.log("=" * 60, force=True)
        self.log("Ce script va parcourir TOUTES les propriétés de Centris!", force=True)

        # Afficher les infos de référence
        ref_stats = get_reference_stats()
        if ref_stats['has_reference']:
            self.log(f"🎯 Image de référence: {ref_stats['image_path']}", force=True)
            pure_color = ref_stats['pure_color']
            self.log(f"   Couleur: H={pure_color['hue']:.0f}, S={pure_color['saturation']:.0f}, V={pure_color['value']:.0f}", force=True)
        else:
            self.log(f"🎯 Couleur par défaut: {ref_stats['default_color']}", force=True)

        self.log("=" * 60, force=True)

        if self.show_browser:
            self.log("\n👁️  Mode VISUEL activé - vous verrez le navigateur en action!", force=True)
        else:
            self.log("\n🔇 Mode silencieux - le navigateur tourne en arrière-plan", force=True)

        async with async_playwright() as p:
            # Lancer le navigateur
            self.log("\n🌐 Lancement du navigateur...", force=True)
            browser = await p.chromium.launch(
                headless=not self.show_browser,
                args=['--disable-blink-features=AutomationControlled']
            )

            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )

            page = await context.new_page()

            try:
                # Récupérer toutes les propriétés
                print("\n" + "=" * 60)
                all_properties = await self.search_all_listings(page)

                if not all_properties:
                    print("❌ Aucune propriété trouvée")
                    await browser.close()
                    return

                # Filtrer les propriétés déjà visitées
                properties_to_analyze = [
                    url for url in all_properties
                    if url not in self.visited_properties
                ]

                print(f"\n📊 Propriétés à analyser: {len(properties_to_analyze)}/{len(all_properties)}")
                print(f"   (Déjà analysées: {len(all_properties) - len(properties_to_analyze)})")

                # Analyser chaque propriété
                self.log("\n" + "=" * 60, force=True)
                self.log("🔍 Début de l'analyse des propriétés...", force=True)
                self.log("=" * 60, force=True)

                for i, prop_url in enumerate(properties_to_analyze):
                    # En-tête de progression
                    elapsed = time.time() - self.stats['start_time']
                    self.log(f"\n{'='*60}", force=True)
                    self.log(f"📍 Propriété [{i+1}/{len(properties_to_analyze)}]", force=True)
                    self.log(f"🔗 {prop_url}", force=True)
                    self.log(f"⏱️  Temps écoulé: {elapsed/60:.1f} min | Images analysées: {self.stats['total_images']} | Canards trouvés: {self.stats['suspicious_images']}", force=True)

                    try:
                        # Récupérer les images
                        self.log(f"  🖼️  Chargement de la page...", force=True)
                        images = await self.get_property_images(page, prop_url)
                        self.log(f"  ✓ {len(images)} images trouvées", force=True)

                        # Analyser chaque image
                        for img_idx, img_url in enumerate(images, 1):
                            self.log(f"    → Analyse image {img_idx}/{len(images)}...", force=False)
                            is_suspicious = await self.download_and_analyze_image(page, img_url, prop_url)
                            if is_suspicious:
                                self.log(f"    🦆 CANARD DÉTECTÉ dans image {img_idx}!", force=True)

                        # Marquer comme visitée
                        self.visited_properties.add(prop_url)
                        self.stats['total_properties'] += 1

                        # Sauvegarder checkpoint tous les 10 propriétés
                        if (i + 1) % 10 == 0:
                            self.save_checkpoint()
                            self.log(f"  💾 Checkpoint sauvegardé (propriété {i+1})", force=True)
                            # Afficher stats intermédiaires
                            self.log(f"  📊 Stats: {self.stats['total_images']} images | {self.stats['suspicious_images']} suspects | {self.stats['errors']} erreurs", force=True)

                        # Petit délai entre les propriétés
                        await page.wait_for_timeout(1500)

                    except Exception as e:
                        self.log(f"  ⚠️  Erreur: {e}", force=True)
                        self.stats['errors'] += 1
                        continue

                # Sauvegarder checkpoint final
                self.save_checkpoint()

            finally:
                await browser.close()

            # Afficher les statistiques finales
            elapsed_time = time.time() - self.stats['start_time']
            print("\n" + "=" * 60)
            print("✓ ANALYSE TERMINÉE!")
            print("=" * 60)
            print(f"  Propriétés analysées: {self.stats['total_properties']}")
            print(f"  Images analysées: {self.stats['total_images']}")
            print(f"  Canards potentiels: {self.stats['suspicious_images']}")
            print(f"  Erreurs: {self.stats['errors']}")
            print(f"  Temps écoulé: {elapsed_time/60:.1f} minutes")
            print(f"  Résultats dans: {self.results_dir}/")
            print("=" * 60)

            if self.stats['suspicious_images'] > 0:
                print(f"\n🎉 {self.stats['suspicious_images']} canard(s) potentiel(s) trouvé(s)!")
                print(f"Vérifie les images dans {self.results_dir}/")


async def main():
    """Point d'entrée"""
    import argparse

    parser = argparse.ArgumentParser(description='Centris Duck Finder - Cherche le canard mauve sur Centris.ca')
    parser.add_argument('--show-browser', action='store_true',
                        help='Affiche le navigateur pendant le scan (mode visuel)')
    parser.add_argument('--quiet', action='store_true',
                        help='Mode silencieux - affiche seulement les résultats importants')

    args = parser.parse_args()

    verbose = not args.quiet
    show_browser = args.show_browser

    if show_browser:
        print("\n" + "="*60)
        print("👁️  MODE VISUEL ACTIVÉ")
        print("="*60)
        print("Vous allez voir le navigateur en action!")
        print("Cela peut ralentir un peu le scan mais c'est cool à regarder 😎")
        print("="*60 + "\n")

    finder = CompleteDuckFinder(verbose=verbose, show_browser=show_browser)
    await finder.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Arrêt demandé par l'utilisateur")
        print("La progression a été sauvegardée dans checkpoint.json")
        print("Relance le script pour reprendre là où tu t'es arrêté!")
        print("\nOptions disponibles:")
        print("  python duck_finder_complete.py              # Mode normal")
        print("  python duck_finder_complete.py --show-browser  # Voir le navigateur")
        print("  python duck_finder_complete.py --quiet       # Mode silencieux")
