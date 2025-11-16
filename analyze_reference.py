#!/usr/bin/env python3
"""
Script pour analyser l'image de référence du canard mauve
Extrait les couleurs dominantes et crée un profil de détection optimisé
"""

import cv2
import numpy as np
from pathlib import Path
import json
from collections import Counter


def find_reference_image():
    """Trouve l'image de référence dans le dossier reference/"""
    ref_dir = Path('reference')
    possible_names = [
        'duck_reference.jpg',
        'duck_reference.png',
        'duck_reference.jpeg',
        'duck_reference.webp',
    ]

    for name in possible_names:
        path = ref_dir / name
        if path.exists():
            return path

    return None


def analyze_reference_image(image_path):
    """Analyse complète de l'image de référence"""
    print(f"🔍 Analyse de l'image de référence: {image_path}")
    print("=" * 60)

    # Charger l'image
    image = cv2.imread(str(image_path))
    if image is None:
        print(f"❌ Impossible de charger l'image: {image_path}")
        return None

    h, w = image.shape[:2]
    print(f"\n📐 Dimensions: {w}x{h} pixels")

    # Convertir en HSV
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)

    # Extraire tous les pixels
    pixels = hsv.reshape(-1, 3)

    # Analyser les couleurs dominantes
    print(f"\n🎨 Analyse des couleurs...")

    # Calculer l'histogramme de Hue
    hue_values = pixels[:, 0]
    sat_values = pixels[:, 1]
    val_values = pixels[:, 2]

    # Statistiques
    hue_mean = np.mean(hue_values)
    hue_std = np.std(hue_values)
    hue_min = np.min(hue_values)
    hue_max = np.max(hue_values)

    sat_mean = np.mean(sat_values)
    sat_std = np.std(sat_values)
    sat_min = np.min(sat_values)
    sat_max = np.max(sat_values)

    val_mean = np.mean(val_values)
    val_std = np.std(val_values)
    val_min = np.min(val_values)
    val_max = np.max(val_values)

    print(f"\n📊 Statistiques HSV:")
    print(f"  Hue (Teinte):")
    print(f"    Moyenne: {hue_mean:.1f} ± {hue_std:.1f}")
    print(f"    Min-Max: {hue_min} - {hue_max}")

    print(f"  Saturation:")
    print(f"    Moyenne: {sat_mean:.1f} ± {sat_std:.1f}")
    print(f"    Min-Max: {sat_min} - {sat_max}")

    print(f"  Value (Luminosité):")
    print(f"    Moyenne: {val_mean:.1f} ± {val_std:.1f}")
    print(f"    Min-Max: {val_min} - {val_max}")

    # Trouver les pixels les plus saturés (couleur pure du canard)
    # On prend les pixels avec une saturation élevée
    saturated_pixels = pixels[pixels[:, 1] > 100]  # Saturation > 100

    if len(saturated_pixels) > 0:
        pure_hue_mean = np.mean(saturated_pixels[:, 0])
        pure_sat_mean = np.mean(saturated_pixels[:, 1])
        pure_val_mean = np.mean(saturated_pixels[:, 2])

        print(f"\n🎨 Couleur pure du canard (pixels saturés):")
        print(f"  Hue: {pure_hue_mean:.1f}")
        print(f"  Saturation: {pure_sat_mean:.1f}")
        print(f"  Value: {pure_val_mean:.1f}")

        # Convertir en RGB pour affichage
        sample_hsv = np.uint8([[[pure_hue_mean, pure_sat_mean, pure_val_mean]]])
        sample_rgb = cv2.cvtColor(sample_hsv, cv2.COLOR_HSV2BGR)[0][0]
        r, g, b = int(sample_rgb[2]), int(sample_rgb[1]), int(sample_rgb[0])
        hex_color = f"#{r:02x}{g:02x}{b:02x}"
        print(f"  RGB: ({r}, {g}, {b})")
        print(f"  HEX: {hex_color}")
    else:
        pure_hue_mean = hue_mean
        pure_sat_mean = sat_mean
        pure_val_mean = val_mean

    # Calculer les plages de détection recommandées
    print(f"\n🎯 Plages de détection recommandées:")

    # Plage stricte (±2 écarts types)
    hue_margin = min(15, hue_std * 2)
    sat_margin = min(50, sat_std * 2)
    val_margin = min(50, val_std * 2)

    lower_strict = [
        max(0, int(pure_hue_mean - hue_margin)),
        max(0, int(pure_sat_mean - sat_margin)),
        max(0, int(pure_val_mean - val_margin))
    ]
    upper_strict = [
        min(180, int(pure_hue_mean + hue_margin)),
        min(255, int(pure_sat_mean + sat_margin)),
        min(255, int(pure_val_mean + val_margin))
    ]

    print(f"  Stricte:")
    print(f"    Lower: ({lower_strict[0]}, {lower_strict[1]}, {lower_strict[2]})")
    print(f"    Upper: ({upper_strict[0]}, {upper_strict[1]}, {upper_strict[2]})")

    # Plage tolérante (±3 écarts types)
    hue_margin_wide = min(20, hue_std * 3)
    sat_margin_wide = min(70, sat_std * 3)
    val_margin_wide = min(70, val_std * 3)

    lower_wide = [
        max(0, int(hue_mean - hue_margin_wide)),
        max(0, int(sat_mean - sat_margin_wide)),
        max(0, int(val_mean - val_margin_wide))
    ]
    upper_wide = [
        min(180, int(hue_mean + hue_margin_wide)),
        min(255, int(sat_mean + sat_margin_wide)),
        min(255, int(val_mean + val_margin_wide))
    ]

    print(f"  Tolérante:")
    print(f"    Lower: ({lower_wide[0]}, {lower_wide[1]}, {lower_wide[2]})")
    print(f"    Upper: ({upper_wide[0]}, {upper_wide[1]}, {upper_wide[2]})")

    # Créer le profil de détection
    profile = {
        'image_path': str(image_path),
        'dimensions': {'width': w, 'height': h},
        'hsv_stats': {
            'hue': {'mean': float(hue_mean), 'std': float(hue_std), 'min': int(hue_min), 'max': int(hue_max)},
            'saturation': {'mean': float(sat_mean), 'std': float(sat_std), 'min': int(sat_min), 'max': int(sat_max)},
            'value': {'mean': float(val_mean), 'std': float(val_std), 'min': int(val_min), 'max': int(val_max)},
        },
        'pure_color': {
            'hue': float(pure_hue_mean),
            'saturation': float(pure_sat_mean),
            'value': float(pure_val_mean)
        },
        'detection_ranges': {
            'strict': {
                'lower': lower_strict,
                'upper': upper_strict
            },
            'tolerant': {
                'lower': lower_wide,
                'upper': upper_wide
            }
        }
    }

    # Sauvegarder le profil
    profile_path = Path('reference/duck_profile.json')
    with open(profile_path, 'w') as f:
        json.dump(profile, f, indent=2)

    print(f"\n💾 Profil sauvegardé: {profile_path}")

    # Créer une visualisation
    output_dir = Path('reference')

    # Masque avec la plage stricte
    mask_strict = cv2.inRange(hsv, np.array(lower_strict), np.array(upper_strict))
    mask_path = output_dir / 'duck_mask_strict.jpg'
    cv2.imwrite(str(mask_path), mask_strict)
    print(f"💾 Masque strict sauvegardé: {mask_path}")

    # Masque avec la plage tolérante
    mask_wide = cv2.inRange(hsv, np.array(lower_wide), np.array(upper_wide))
    mask_wide_path = output_dir / 'duck_mask_tolerant.jpg'
    cv2.imwrite(str(mask_wide_path), mask_wide)
    print(f"💾 Masque tolérant sauvegardé: {mask_wide_path}")

    # Overlay
    overlay = image.copy()
    overlay[mask_strict > 0] = [255, 0, 255]  # Magenta
    result = cv2.addWeighted(image, 0.7, overlay, 0.3, 0)
    overlay_path = output_dir / 'duck_overlay.jpg'
    cv2.imwrite(str(overlay_path), result)
    print(f"💾 Overlay sauvegardé: {overlay_path}")

    # Calculer le pourcentage de pixels mauves
    purple_pixels = np.sum(mask_strict > 0)
    total_pixels = mask_strict.shape[0] * mask_strict.shape[1]
    purple_percentage = (purple_pixels / total_pixels) * 100

    print(f"\n📊 Détection sur l'image de référence:")
    print(f"  Pixels détectés (strict): {purple_percentage:.1f}%")

    purple_pixels_wide = np.sum(mask_wide > 0)
    purple_percentage_wide = (purple_pixels_wide / total_pixels) * 100
    print(f"  Pixels détectés (tolérant): {purple_percentage_wide:.1f}%")

    print(f"\n" + "=" * 60)
    print("✅ Analyse terminée!")
    print(f"\nLe profil a été créé. Les scripts vont maintenant utiliser")
    print(f"ces plages de couleur pour détecter le canard!")
    print("=" * 60)

    return profile


def main():
    """Point d'entrée"""
    print("\n🦆 ANALYSE DE L'IMAGE DE RÉFÉRENCE DU CANARD")
    print("=" * 60)

    # Chercher l'image de référence
    ref_image = find_reference_image()

    if ref_image is None:
        print("\n❌ Aucune image de référence trouvée!")
        print("\nPlace une image du canard mauve dans le dossier 'reference/' avec un de ces noms:")
        print("  - duck_reference.jpg")
        print("  - duck_reference.png")
        print("  - duck_reference.jpeg")
        print("  - duck_reference.webp")
        print("\nPuis relance ce script.")
        return

    # Analyser l'image
    profile = analyze_reference_image(ref_image)

    if profile:
        print(f"\n🚀 Tu peux maintenant lancer le scan:")
        print(f"   python duck_finder_fast.py")
        print(f"\nLe script utilisera automatiquement le profil de couleur de ton canard!")


if __name__ == "__main__":
    main()
