"""
Configuration pour le Duck Finder
"""

# Paramètres de recherche
MAX_PROPERTIES = 50  # Nombre maximum de propriétés à analyser
MAX_IMAGES_PER_PROPERTY = 100  # Nombre maximum d'images par propriété

# Paramètres de détection du canard mauve
PURPLE_DETECTION = {
    # Plage HSV pour détecter le mauve/violet
    # Hue: 130-160 (dans l'échelle OpenCV 0-180)
    # Saturation: 50-255
    # Value: 50-255
    'lower_hsv': (130, 50, 50),
    'upper_hsv': (160, 255, 255),

    # Pourcentage minimum de pixels mauves pour considérer l'image suspecte
    'min_purple_percentage': 0.5,

    # Taille du kernel pour les opérations morphologiques (réduction du bruit)
    'morphology_kernel_size': 5,
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
