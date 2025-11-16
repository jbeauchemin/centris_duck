"""
Configuration pour le Duck Finder
"""

# Paramètres de recherche
MAX_PROPERTIES = 50  # Nombre maximum de propriétés à analyser
MAX_IMAGES_PER_PROPERTY = 100  # Nombre maximum d'images par propriété

# Paramètres de détection du canard mauve
# Couleur exacte du canard: #c97ef2 (RGB: 201, 126, 242) -> HSV: (139, 122, 242)
PURPLE_DETECTION = {
    # Plage HSV STRICTE pour détecter le violet spécifique du canard
    # Hue: 139 ± 8 (131-147) pour capturer les variations d'éclairage
    # Saturation: 122 ± 40 (82-162) pour capturer différentes saturations
    # Value: 242 ± 50 (192-255) pour capturer différentes luminosités
    'lower_hsv_exact': (131, 82, 192),
    'upper_hsv_exact': (147, 162, 255),

    # Plage pour les zones d'ombre du canard
    'lower_hsv_shadow': (129, 60, 150),
    'upper_hsv_shadow': (149, 180, 200),

    # Pourcentage minimum de pixels mauves pour considérer l'image suspecte
    # Augmenté à 1.0% pour réduire les faux positifs
    'min_purple_percentage': 1.0,

    # Taille minimale d'un contour pour être considéré significatif
    # Augmenté à 500 pixels² pour éviter les petits artefacts
    'min_contour_area': 500,

    # Taille d'un contour pour être considéré comme "très suspect" (probablement le canard!)
    'large_contour_area': 2000,

    # Taille du kernel pour les opérations morphologiques (réduction du bruit)
    'morphology_kernel_size': 3,
}

# Paramètres de navigation
BROWSER_CONFIG = {
    'headless': True,  # False pour voir le navigateur en action
    'viewport': {'width': 1920, 'height': 1080},
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
}

# Délais (en millisecondes)
DELAYS = {
    'between_properties': 1000,  # Délai entre chaque propriété
    'page_load': 3000,  # Délai après chargement de page
    'after_click': 1000,  # Délai après un clic
}

# Chemins de sortie
OUTPUT_DIRS = {
    'results': 'potential_ducks',  # Dossier pour les images suspectes
    'temp_images': 'images',  # Dossier temporaire pour les images téléchargées
    'screenshots': 'screenshots',  # Dossier pour les captures d'écran
}

# URLs Centris
CENTRIS_URLS = {
    'base': 'https://www.centris.ca',
    'search': 'https://www.centris.ca/fr/propriete~a-vendre?uc=1',
}

# Options de logging
LOGGING = {
    'verbose': True,  # Afficher les messages détaillés
    'save_masks': True,  # Sauvegarder les masques de détection
    'save_info_files': True,  # Sauvegarder les fichiers d'information
}
