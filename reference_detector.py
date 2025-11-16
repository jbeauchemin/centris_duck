"""
Module pour la détection basée sur l'image de référence
Charge le profil de couleur depuis duck_profile.json si disponible
"""

import json
import numpy as np
from pathlib import Path


def load_reference_profile():
    """Charge le profil de l'image de référence si disponible"""
    profile_path = Path('reference/duck_profile.json')

    if not profile_path.exists():
        return None

    try:
        with open(profile_path, 'r') as f:
            profile = json.load(f)
        print(f"✓ Profil de référence chargé: {profile_path}")
        return profile
    except Exception as e:
        print(f"⚠ Erreur chargement profil: {e}")
        return None


def get_detection_ranges(use_tolerant=False):
    """
    Retourne les plages de détection à utiliser
    Utilise le profil de référence si disponible, sinon les valeurs par défaut
    """
    profile = load_reference_profile()

    if profile:
        # Utiliser le profil de l'image de référence
        if use_tolerant:
            ranges = profile['detection_ranges']['tolerant']
        else:
            ranges = profile['detection_ranges']['strict']

        lower = np.array(ranges['lower'])
        upper = np.array(ranges['upper'])

        print(f"🎯 Utilisation du profil de référence ({'tolérant' if use_tolerant else 'strict'})")
        print(f"   Lower HSV: {lower}")
        print(f"   Upper HSV: {upper}")

        return {
            'exact': (lower, upper),
            'shadow': None  # On n'utilise qu'une plage avec le profil
        }
    else:
        # Valeurs par défaut basées sur #c97ef2
        print(f"🎯 Utilisation des valeurs par défaut (couleur #c97ef2)")

        lower_purple_exact = np.array([131, 82, 192])
        upper_purple_exact = np.array([147, 162, 255])
        lower_purple_shadow = np.array([129, 60, 150])
        upper_purple_shadow = np.array([149, 180, 200])

        return {
            'exact': (lower_purple_exact, upper_purple_exact),
            'shadow': (lower_purple_shadow, upper_purple_shadow)
        }


def get_reference_stats():
    """Retourne les statistiques de l'image de référence"""
    profile = load_reference_profile()

    if profile:
        return {
            'has_reference': True,
            'image_path': profile.get('image_path'),
            'pure_color': profile.get('pure_color'),
            'hsv_stats': profile.get('hsv_stats')
        }
    else:
        return {
            'has_reference': False,
            'default_color': '#c97ef2',
            'default_hsv': (139, 122, 242)
        }
