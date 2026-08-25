import os
import json

# Ruta a tu carpeta local de GitHub Pages
# Cambia esto si tu repositorio está en otro lugar
BASE_PATH = r"C:\Users\Inti\Documents\GitHub\Pages\Pages\images"

EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}

categories = [
    "materials",
    "textures",
    "brushes",
    "decals",
    "dynamic_textures",
    "dynamic_decals",
    "fade_slider",
]

for cat in categories:
    folder = os.path.join(BASE_PATH, cat)
    if not os.path.exists(folder):
        print(f"⚠️  Carpeta no encontrada: {folder}")
        continue

    files = sorted([
        f for f in os.listdir(folder)
        if os.path.splitext(f)[1].lower() in EXTENSIONS
    ])

    manifest_path = os.path.join(folder, "manifest.json")
    with open(manifest_path, 'w') as mf:
        json.dump(files, mf)

    print(f"✅ {cat}: {len(files)} imágenes → manifest.json generado")

print("\nListo. Sube los archivos manifest.json a GitHub junto con tus imágenes.")
