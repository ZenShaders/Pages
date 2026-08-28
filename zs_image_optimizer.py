"""
ZenShaders Image Optimizer
Optimiza imágenes en bulk para los diferentes usos en la landing page
Requiere: pip install pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import threading

# ─── PRESETS ───────────────────────────────────────────────────────────────────
PRESETS = {
    "Gallery Scrollbar (PNG, 512×512)": {
        "format": "PNG",
        "size": (512, 512),
        "keep_alpha": True,
        "quality": None,
        "desc": "Esferas y assets para los scrollbars y carrusel de 4 filas.\nMantiene fondo transparente (alpha)."
    },
    "Fade Slider Renders (JPG, 1404×790)": {
        "format": "JPEG",
        "size": (1404, 790),
        "keep_alpha": False,
        "quality": 85,
        "desc": "Renders cinemáticos para el slider con fade.\nFormato JPG, sin transparencia, calidad 85%."
    },
    "Software Icons (PNG, 128×128)": {
        "format": "PNG",
        "size": (128, 128),
        "keep_alpha": True,
        "quality": None,
        "desc": "Iconos de Blender, Substance, ZBrush, 4K, etc.\nMantiene fondo transparente (alpha)."
    },
    "Category Icons (PNG, 104×104)": {
        "format": "PNG",
        "size": (104, 104),
        "keep_alpha": True,
        "quality": None,
        "desc": "Iconos de categoría (Materials, Brushes, Tools...).\nMantiene fondo transparente (alpha)."
    },
    "Title Cards (PNG, 614×176)": {
        "format": "PNG",
        "size": (614, 176),
        "keep_alpha": True,
        "quality": None,
        "desc": "Imágenes de título de las tarjetas de categoría.\nMantiene fondo transparente (alpha)."
    },
    "Custom...": {
        "format": "PNG",
        "size": (512, 512),
        "keep_alpha": True,
        "quality": 85,
        "desc": "Configura manualmente el formato, tamaño y calidad."
    },
}

# ─── APP ───────────────────────────────────────────────────────────────────────
class ImageOptimizer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZenShaders Image Optimizer")
        self.geometry("640x750")
        self.minsize(640, 600)
        self.resizable(True, True)
        self.configure(bg="#1a1a1a")

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.preset_name = tk.StringVar(value=list(PRESETS.keys())[0])
        self.format_var = tk.StringVar(value="PNG")
        self.width_var = tk.StringVar(value="512")
        self.height_var = tk.StringVar(value="512")
        self.fit_mode_var = tk.StringVar(value="Fill (recorta, sin bordes)")
        self.quality_var = tk.StringVar(value="90")
        self.format_var = tk.StringVar(value="PNG")
        self.keep_alpha_var = tk.BooleanVar(value=True)
        self.quality_var = tk.StringVar(value="85")
        self.alpha_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)

        self._build_ui()
        self._on_preset_change()

    def _label(self, parent, text, size=11, bold=False, color="#e0e0e0"):
        font = ("Arial", size, "bold" if bold else "normal")
        return tk.Label(parent, text=text, font=font, bg="#1a1a1a", fg=color)

    def _entry(self, parent, var, width=20):
        return tk.Entry(parent, textvariable=var, width=width,
                        bg="#2d2d2d", fg="#e0e0e0", insertbackground="#e0e0e0",
                        relief="flat", font=("Arial", 10))

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        # Título
        tk.Label(self, text="ZenShaders Image Optimizer", font=("Arial", 15, "bold"),
                 bg="#1a1a1a", fg="#ffffff").pack(pady=(20, 4))
        tk.Label(self, text="Optimiza imágenes en bulk para la landing page",
                 font=("Arial", 10), bg="#1a1a1a", fg="#888888").pack(pady=(0, 16))

        # Separador
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=4)

        # ── CARPETAS ──
        self._label(self, "Carpeta de entrada", bold=True).pack(anchor="w", **pad)
        f1 = tk.Frame(self, bg="#1a1a1a")
        f1.pack(fill="x", padx=20, pady=2)
        self._entry(f1, self.input_folder, width=46).pack(side="left", ipady=4)
        tk.Button(f1, text="Buscar", command=self._pick_input,
                  bg="#333333", fg="#ffffff", relief="flat", font=("Arial", 9),
                  cursor="hand2").pack(side="left", padx=(8, 0), ipady=4, ipadx=6)

        self._label(self, "Carpeta de salida", bold=True).pack(anchor="w", **pad)
        f2 = tk.Frame(self, bg="#1a1a1a")
        f2.pack(fill="x", padx=20, pady=2)
        self._entry(f2, self.output_folder, width=46).pack(side="left", ipady=4)
        tk.Button(f2, text="Buscar", command=self._pick_output,
                  bg="#333333", fg="#ffffff", relief="flat", font=("Arial", 9),
                  cursor="hand2").pack(side="left", padx=(8, 0), ipady=4, ipadx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # ── PRESET ──
        self._label(self, "Preset", bold=True).pack(anchor="w", **pad)
        preset_menu = ttk.Combobox(self, textvariable=self.preset_name,
                                   values=list(PRESETS.keys()), state="readonly",
                                   font=("Arial", 10), width=42)
        preset_menu.pack(anchor="w", padx=20, pady=2)
        preset_menu.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.desc_label = tk.Label(self, text="", font=("Arial", 9), bg="#1a1a1a",
                                   fg="#888888", justify="left", wraplength=580)
        self.desc_label.pack(anchor="w", padx=20, pady=(4, 8))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=4)

        # ── PARÁMETROS CUSTOM ──
        self._label(self, "Parámetros", bold=True).pack(anchor="w", **pad)

        params = tk.Frame(self, bg="#1a1a1a")
        params.pack(fill="x", padx=20, pady=4)

        # Formato
        tk.Label(params, text="Formato:", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8), pady=4)
        fmt_menu = ttk.Combobox(params, textvariable=self.format_var,
                                values=["PNG", "JPEG", "WEBP"], state="readonly",
                                font=("Arial", 10), width=8)
        fmt_menu.grid(row=0, column=1, sticky="w", pady=4)

        # Ancho
        tk.Label(params, text="Ancho:", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=0, column=2, sticky="w", padx=(20, 8), pady=4)
        self._entry(params, self.width_var, width=6).grid(row=0, column=3, sticky="w", pady=4)
        tk.Label(params, text="px", bg="#1a1a1a", fg="#888888",
                 font=("Arial", 10)).grid(row=0, column=4, sticky="w", padx=(2, 20))

        # Alto
        tk.Label(params, text="Alto:", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=0, column=5, sticky="w", padx=(0, 8), pady=4)
        self._entry(params, self.height_var, width=6).grid(row=0, column=6, sticky="w", pady=4)
        tk.Label(params, text="px", bg="#1a1a1a", fg="#888888",
                 font=("Arial", 10)).grid(row=0, column=7, sticky="w", padx=2)

        # Calidad
        tk.Label(params, text="Calidad (JPG/WEBP):", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
        self._entry(params, self.quality_var, width=4).grid(row=1, column=2, sticky="w", padx=(20,4), pady=4)
        tk.Label(params, text="(1-100)", bg="#1a1a1a", fg="#888888",
                 font=("Arial", 9)).grid(row=1, column=3, sticky="w")

        # Modo de encaje (Fit/Fill) — resuelve imágenes con resoluciones distintas
        tk.Label(params, text="Encaje al recuadro:", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10,4))
        fit_menu = ttk.Combobox(params, textvariable=self.fit_mode_var,
                                values=["Fill (recorta, sin bordes)",
                                        "Fit (contiene, con bordes)",
                                        "Fit + fondo blanco",
                                        "Estirar (deforma)"],
                                state="readonly", font=("Arial", 10), width=26)
        fit_menu.grid(row=2, column=2, columnspan=4, sticky="w", padx=(0,0), pady=(10,4))

        fit_desc = tk.Label(params,
            text="Fill: llena el recuadro entero, recorta el sobrante desde el centro (recomendado).\n"
                 "Fit: la imagen entera cabe dentro, puede dejar huecos transparentes/blancos.",
            font=("Arial", 8), bg="#1a1a1a", fg="#777777", justify="left")
        fit_desc.grid(row=3, column=0, columnspan=7, sticky="w", pady=(0,4))

        # Alpha
        tk.Checkbutton(params, text="Mantener canal alpha (transparencia)",
                       variable=self.alpha_var, bg="#1a1a1a", fg="#e0e0e0",
                       selectcolor="#2d2d2d", activebackground="#1a1a1a",
                       font=("Arial", 10)).grid(row=4, column=0, columnspan=5, sticky="w", pady=4)

        # Sobreescribir
        tk.Checkbutton(params, text="Sobreescribir archivos existentes",
                       variable=self.overwrite_var, bg="#1a1a1a", fg="#e0e0e0",
                       selectcolor="#2d2d2d", activebackground="#1a1a1a",
                       font=("Arial", 10)).grid(row=5, column=0, columnspan=5, sticky="w", pady=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # ── LOG ──
        self.log = tk.Text(self, height=6, bg="#111111", fg="#aaaaaa",
                           font=("Courier", 9), relief="flat", state="disabled")
        self.log.pack(fill="x", padx=20, pady=(0, 10))

        # ── BOTÓN CONVERTIR ──
        self.btn = tk.Button(self, text="▶  Convertir imágenes", command=self._run,
                             bg="#2d5a2d", fg="#ffffff", font=("Arial", 12, "bold"),
                             relief="flat", cursor="hand2", activebackground="#3d7a3d")
        self.btn.pack(pady=(0, 20), ipadx=20, ipady=8)

    def _on_preset_change(self, *_):
        p = PRESETS[self.preset_name.get()]
        is_custom = self.preset_name.get() == "Custom..."
        self.format_var.set(p["format"])
        self.width_var.set(str(p["size"][0]))
        self.height_var.set(str(p["size"][1]))
        self.quality_var.set(str(p["quality"] or 85))
        self.alpha_var.set(p["keep_alpha"])
        self.desc_label.config(text=p["desc"])

    def _pick_input(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta de entrada")
        if folder:
            self.input_folder.set(folder)
            if not self.output_folder.get():
                self.output_folder.set(os.path.join(folder, "optimized"))

    def _pick_output(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta de salida")
        if folder:
            self.output_folder.set(folder)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")

    def _run(self):
        if not self.input_folder.get():
            messagebox.showerror("Error", "Selecciona una carpeta de entrada.")
            return
        self.btn.config(state="disabled", text="Procesando...")
        threading.Thread(target=self._process, daemon=True).start()

    def _process(self):
        src = self.input_folder.get()
        dst = self.output_folder.get() or os.path.join(src, "optimized")
        os.makedirs(dst, exist_ok=True)

        fmt = self.format_var.get()
        w = int(self.width_var.get())
        h = int(self.height_var.get())
        quality = int(self.quality_var.get())
        keep_alpha = self.alpha_var.get()
        overwrite = self.overwrite_var.get()
        fit_mode = self.fit_mode_var.get()

        ext_map = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}
        out_ext = ext_map[fmt]

        files = [f for f in os.listdir(src)
                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp", ".tga", ".tif", ".tiff"))]

        if not files:
            self._log("⚠️  No se encontraron imágenes en la carpeta.")
            self.btn.config(state="normal", text="▶  Convertir imágenes")
            return

        self._log(f"📁 {len(files)} imágenes encontradas → {dst}")
        ok = 0
        skip = 0

        for fname in files:
            stem = os.path.splitext(fname)[0]
            out_path = os.path.join(dst, stem + out_ext)

            if not overwrite and os.path.exists(out_path):
                self._log(f"  ⏭  {fname} (ya existe, omitido)")
                skip += 1
                continue

            try:
                img = Image.open(os.path.join(src, fname))
                img = self._smart_resize(img, w, h, fit_mode)

                # Gestión de alpha
                if fmt == "JPEG":
                    if img.mode in ("RGBA", "LA", "P"):
                        bg = Image.new("RGB", img.size, (255, 255, 255))
                        if img.mode == "P":
                            img = img.convert("RGBA")
                        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                        img = bg
                    else:
                        img = img.convert("RGB")
                    img.save(out_path, "JPEG", quality=quality, optimize=True)
                elif fmt == "WEBP":
                    img.save(out_path, "WEBP", quality=quality,
                             lossless=keep_alpha, method=6)
                else:  # PNG
                    if keep_alpha and img.mode not in ("RGBA", "LA"):
                        img = img.convert("RGBA")
                    elif not keep_alpha:
                        img = img.convert("RGB")
                    img.save(out_path, "PNG", optimize=True)

                size_kb = os.path.getsize(out_path) / 1024
                self._log(f"  ✅ {fname} → {stem+out_ext} ({size_kb:.0f} KB)")
                ok += 1

            except Exception as e:
                self._log(f"  ❌ {fname}: {e}")

        self._log(f"\n✅ {ok} convertidas, {skip} omitidas.")
        self.btn.config(state="normal", text="▶  Convertir imágenes")

    def _smart_resize(self, img, target_w, target_h, mode):
        """
        Redimensiona una imagen a (target_w, target_h) según el modo elegido,
        sin distorsionar proporciones salvo que el usuario pida 'Estirar'.
        """
        img = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
        src_w, src_h = img.size

        if mode.startswith("Estirar"):
            return img.resize((target_w, target_h), Image.LANCZOS)

        # Ratio para que la imagen quepa (Fit) o llene (Fill) el recuadro
        ratio_fill = max(target_w / src_w, target_h / src_h)
        ratio_fit = min(target_w / src_w, target_h / src_h)
        ratio = ratio_fill if mode.startswith("Fill") else ratio_fit

        new_w = max(1, round(src_w * ratio))
        new_h = max(1, round(src_h * ratio))
        resized = img.resize((new_w, new_h), Image.LANCZOS)

        if mode.startswith("Fill"):
            # Recorta el sobrante desde el centro para llenar el recuadro exacto
            left = (new_w - target_w) // 2
            top = (new_h - target_h) // 2
            return resized.crop((left, top, left + target_w, top + target_h))
        else:
            # Fit: centra la imagen completa dentro del recuadro, dejando bordes
            if mode.endswith("fondo blanco"):
                canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
                if resized.mode == "RGBA":
                    canvas.paste(resized, ((target_w-new_w)//2, (target_h-new_h)//2), resized)
                else:
                    canvas.paste(resized, ((target_w-new_w)//2, (target_h-new_h)//2))
            else:
                canvas = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 0))
                canvas.paste(resized, ((target_w-new_w)//2, (target_h-new_h)//2),
                            resized if resized.mode == "RGBA" else None)
            return canvas

if __name__ == "__main__":
    app = ImageOptimizer()
    app.mainloop()
