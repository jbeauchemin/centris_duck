#!/usr/bin/env python3
"""
Script de test pour vérifier la détection de couleur sur une image
Utilise pour tester la détection avant de lancer le scan complet
"""

import sys
import cv2
import numpy as np
from pathlib import Path


def test_duck_detection(image_path):
    """Teste la détection sur une image donnée"""

    print(f"🔍 Test de détection sur: {image_path}")
    print("=" * 60)

    # Charger l'image
    image = cv2.imread(image_path)
    if image is None:
        print(f"❌ Impossible de charger l'image: {image_path}")
        return

    h, w = image.shape[:2]
    print(f"📐 Dimensions: {w}x{h} pixels")

    # Convertir en HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Couleur EXACTE du canard: #c97ef2
    print(f"\n🎨 Couleur cible du canard: #c97ef2")
    print(f"   RGB: (201, 126, 242)")
    print(f"   HSV OpenCV: (139, 122, 242)")

    # Plages de détection
    lower_purple_exact = np.array([131, 82, 192])
    upper_purple_exact = np.array([147, 162, 255])
    lower_purple_shadow = np.array([129, 60, 150])
    upper_purple_shadow = np.array([149, 180, 200])

    print(f"\n🔬 Plages de détection:")
    print(f"   Principale: H:{lower_purple_exact[0]}-{upper_purple_exact[0]}, S:{lower_purple_exact[1]}-{upper_purple_exact[1]}, V:{lower_purple_exact[2]}-{upper_purple_exact[2]}")
    print(f"   Ombre:      H:{lower_purple_shadow[0]}-{upper_purple_shadow[0]}, S:{lower_purple_shadow[1]}-{upper_purple_shadow[1]}, V:{lower_purple_shadow[2]}-{upper_purple_shadow[2]}")

    # Créer masques
    mask1 = cv2.inRange(hsv, lower_purple_exact, upper_purple_exact)
    mask2 = cv2.inRange(hsv, lower_purple_shadow, upper_purple_shadow)
    mask = cv2.bitwise_or(mask1, mask2)

    # Opérations morphologiques
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)

    # Statistiques
    purple_pixels = np.sum(mask > 0)
    total_pixels = mask.shape[0] * mask.shape[1]
    purple_percentage = (purple_pixels / total_pixels) * 100

    print(f"\n📊 Résultats:")
    print(f"   Pixels mauves: {purple_pixels:,} / {total_pixels:,}")
    print(f"   Pourcentage: {purple_percentage:.2f}%")

    # Contours
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    significant_contours = [cnt for cnt in contours if cv2.contourArea(cnt) > 500]
    max_contour_area = max([cv2.contourArea(cnt) for cnt in significant_contours], default=0)

    print(f"   Contours totaux: {len(contours)}")
    print(f"   Contours significatifs (>500px²): {len(significant_contours)}")
    print(f"   Plus gros contour: {max_contour_area:.0f} pixels²")

    # Décision
    is_suspicious = (
        (purple_percentage > 1.0 and len(significant_contours) > 0) or
        (max_contour_area > 2000)
    )

    print(f"\n{'='*60}")
    if is_suspicious:
        print(f"🦆 VERDICT: CANARD POTENTIEL DÉTECTÉ!")
        if max_contour_area > 2000:
            print(f"   Raison: Très gros contour ({max_contour_area:.0f} pixels²)")
        else:
            print(f"   Raison: {purple_percentage:.2f}% pixels mauves + {len(significant_contours)} contours")
    else:
        print(f"❌ VERDICT: Pas de canard détecté")
        if purple_percentage < 1.0:
            print(f"   Raison: Pas assez de pixels mauves ({purple_percentage:.2f}% < 1.0%)")
        elif len(significant_contours) == 0:
            print(f"   Raison: Aucun contour significatif")
        else:
            print(f"   Raison: Critères non remplis")
    print(f"{'='*60}")

    # Sauvegarder les visualisations
    output_dir = Path('test_results')
    output_dir.mkdir(exist_ok=True)

    image_name = Path(image_path).stem

    # Sauvegarder le masque
    mask_path = output_dir / f"{image_name}_mask.jpg"
    cv2.imwrite(str(mask_path), mask)
    print(f"\n💾 Masque sauvegardé: {mask_path}")

    # Sauvegarder l'image avec contours
    contour_image = image.copy()
    cv2.drawContours(contour_image, significant_contours, -1, (0, 255, 0), 3)
    contours_path = output_dir / f"{image_name}_contours.jpg"
    cv2.imwrite(str(contours_path), contour_image)
    print(f"💾 Contours sauvegardés: {contours_path}")

    # Créer une version avec overlay
    overlay = image.copy()
    overlay[mask > 0] = [255, 0, 255]  # Magenta pour les zones détectées
    result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    overlay_path = output_dir / f"{image_name}_overlay.jpg"
    cv2.imwrite(str(overlay_path), result)
    print(f"💾 Overlay sauvegardé: {overlay_path}")

    print(f"\n✓ Fichiers de test créés dans: {output_dir}/")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_detection.py <chemin_image>")
        print("\nExemple:")
        print("  python test_detection.py image.jpg")
        print("  python test_detection.py potential_ducks/duck_12345.jpg")
        sys.exit(1)

    image_path = sys.argv[1]
    if not Path(image_path).exists():
        print(f"❌ Fichier introuvable: {image_path}")
        sys.exit(1)

    test_duck_detection(image_path)
