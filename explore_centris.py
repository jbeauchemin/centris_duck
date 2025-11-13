#!/usr/bin/env python3
"""
Script d'exploration pour comprendre la structure de centris.ca
"""

import asyncio
from playwright.async_api import async_playwright


async def explore_centris():
    """Explore la structure du site centris.ca"""

    async with async_playwright() as p:
        print("🌐 Lancement du navigateur...")
        browser = await p.chromium.launch(headless=False)  # headless=False pour voir
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = await context.new_page()

        # Aller sur la page de recherche
        print("📍 Navigation vers centris.ca...")
        await page.goto('https://www.centris.ca/fr', wait_until='networkidle')
        await page.wait_for_timeout(3000)

        # Sauvegarder une capture d'écran
        await page.screenshot(path='centris_homepage.png')
        print("✓ Capture d'écran sauvegardée: centris_homepage.png")

        # Chercher le champ de recherche ou les propriétés
        print("\n🔍 Analyse de la structure HTML...")

        # Essayer de trouver les éléments de recherche
        search_selectors = [
            'input[type="search"]',
            'input[placeholder*="Recherche"]',
            'input[placeholder*="recherche"]',
            '.search-input',
            '#search'
        ]

        for selector in search_selectors:
            count = await page.locator(selector).count()
            if count > 0:
                print(f"✓ Trouvé élément de recherche: {selector} ({count})")

        # Essayer de trouver un lien vers les propriétés à vendre
        try:
            # Chercher un lien "À vendre" ou similaire
            links = await page.locator('a:has-text("vendre"), a:has-text("Vendre")').all()
            print(f"\n✓ Trouvé {len(links)} liens contenant 'vendre'")

            if links:
                first_link = links[0]
                href = await first_link.get_attribute('href')
                print(f"  Premier lien: {href}")

                # Cliquer sur le premier lien
                await first_link.click()
                await page.wait_for_timeout(3000)
                await page.screenshot(path='centris_search_results.png')
                print("✓ Capture des résultats: centris_search_results.png")

                # Analyser la page de résultats
                print("\n📋 Analyse de la page de résultats...")
                current_url = page.url
                print(f"  URL actuelle: {current_url}")

                # Chercher les cartes de propriétés
                property_selectors = [
                    '.property-card',
                    '.property-thumbnail-item',
                    'div[class*="property"]',
                    'article[class*="property"]',
                    'a[href*="propriete"]'
                ]

                for selector in property_selectors:
                    count = await page.locator(selector).count()
                    if count > 0:
                        print(f"✓ Trouvé élément de propriété: {selector} ({count})")

                # Récupérer les liens vers les fiches individuelles
                all_links = await page.locator('a[href]').all()
                property_links = []

                for link in all_links[:50]:  # Limiter à 50 premiers liens
                    href = await link.get_attribute('href')
                    if href and 'propriete' in href.lower():
                        property_links.append(href)

                property_links = list(set(property_links))
                print(f"\n✓ Trouvé {len(property_links)} liens de propriétés uniques")

                if property_links:
                    print("\nExemples de liens:")
                    for link in property_links[:5]:
                        print(f"  - {link}")

                    # Visiter la première propriété
                    print(f"\n🏠 Visite de la première propriété...")
                    first_property = property_links[0]
                    if not first_property.startswith('http'):
                        first_property = 'https://www.centris.ca' + first_property

                    await page.goto(first_property, wait_until='networkidle')
                    await page.wait_for_timeout(3000)
                    await page.screenshot(path='centris_property_detail.png')
                    print("✓ Capture de la fiche: centris_property_detail.png")

                    # Analyser les images
                    print("\n🖼️  Analyse des images...")
                    img_selectors = [
                        'img[src*="jpg"]',
                        'img[src*="jpeg"]',
                        'img[data-src]',
                        '.gallery img',
                        '.photo-gallery img',
                        'picture img'
                    ]

                    all_images = []
                    for selector in img_selectors:
                        imgs = await page.locator(selector).all()
                        for img in imgs[:10]:  # Limiter
                            src = await img.get_attribute('src') or await img.get_attribute('data-src')
                            if src and src not in all_images:
                                all_images.append(src)

                    print(f"✓ Trouvé {len(all_images)} images")
                    if all_images:
                        print("\nExemples d'URLs d'images:")
                        for img_url in all_images[:5]:
                            print(f"  - {img_url[:100]}...")

        except Exception as e:
            print(f"⚠ Erreur: {e}")

        print("\n" + "="*50)
        print("Exploration terminée! Captures d'écran sauvegardées.")
        print("Appuyez sur Entrée pour fermer le navigateur...")
        # await page.pause()  # Décommenter pour inspecter manuellement

        await browser.close()


if __name__ == "__main__":
    asyncio.run(explore_centris())
