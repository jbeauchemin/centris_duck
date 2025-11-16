#!/usr/bin/env python3
"""Test pour calculer les valeurs HSV exactes du canard mauve #c97ef2"""

import cv2
import numpy as np

# Couleur du canard en RGB
duck_color_hex = "#c97ef2"
r = int(duck_color_hex[1:3], 16)  # 201
g = int(duck_color_hex[3:5], 16)  # 126
b = int(duck_color_hex[5:7], 16)  # 242

print(f"Couleur du canard mauve:")
print(f"  HEX: {duck_color_hex}")
print(f"  RGB: ({r}, {g}, {b})")

# Créer une image d'un seul pixel avec cette couleur
pixel_rgb = np.uint8([[[b, g, r]]])  # OpenCV utilise BGR
pixel_hsv = cv2.cvtColor(pixel_rgb, cv2.COLOR_BGR2HSV)

h, s, v = pixel_hsv[0][0]

print(f"  HSV OpenCV: ({h}, {s}, {v})")
print(f"\nPlages de détection recommandées (strictes):")
print(f"  Lower HSV: ({max(0, h-5)}, {max(0, s-30)}, {max(0, v-30)})")
print(f"  Upper HSV: ({min(180, h+5)}, {min(255, s+30)}, {min(255, v+30)})")
print(f"\nPlages de détection recommandées (tolérantes):")
print(f"  Lower HSV: ({max(0, h-10)}, {max(0, s-50)}, {max(0, v-50)})")
print(f"  Upper HSV: ({min(180, h+10)}, {min(255, s+50)}, 255)")
