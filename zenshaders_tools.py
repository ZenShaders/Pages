"""
ZenShaders Tools
App unificada: Image Optimizer + GIF Maker, con pestañas.
Requiere: pip install pillow
Para empaquetar como .exe: pip install pyinstaller
                            pyinstaller --onefile --windowed --name "ZenShaders Tools" zenshaders_tools.py
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import re
import threading

# ─────────────────────────────────────────────────────────────────────────────
# PRESETS (Image Optimizer)
# ─────────────────────────────────────────────────────────────────────────────
PRESETS = {
    "Gallery Scrollbar (PNG, 512×512)": {
        "format": "PNG", "size": (512, 512), "keep_alpha": True, "quality": None,
        "desc": "Esferas y assets para los scrollbars y carrusel de 4 filas.\nMantiene fondo transparente (alpha)."
    },
    "Fade Slider Renders (JPG, 1404×790)": {
        "format": "JPEG", "size": (1404, 790), "keep_alpha": False, "quality": 85,
        "desc": "Renders cinemáticos para el slider con fade.\nFormato JPG, sin transparencia, calidad 85%."
    },
    "Software Icons (PNG, 128×128)": {
        "format": "PNG", "size": (128, 128), "keep_alpha": True, "quality": None,
        "desc": "Iconos de Blender, Substance, ZBrush, 4K, etc.\nMantiene fondo transparente (alpha)."
    },
    "Category Icons (PNG, 104×104)": {
        "format": "PNG", "size": (104, 104), "keep_alpha": True, "quality": None,
        "desc": "Iconos de categoría (Materials, Brushes, Tools...).\nMantiene fondo transparente (alpha)."
    },
    "Title Cards (PNG, 614×176)": {
        "format": "PNG", "size": (614, 176), "keep_alpha": True, "quality": None,
        "desc": "Imágenes de título de las tarjetas de categoría.\nMantiene fondo transparente (alpha)."
    },
    "Custom...": {
        "format": "PNG", "size": (512, 512), "keep_alpha": True, "quality": 85,
        "desc": "Configura manualmente el formato, tamaño y calidad."
    },
}

DARK_BG = "#1a1a1a"
FG = "#e0e0e0"


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS DE ESTILO COMPARTIDOS
# ─────────────────────────────────────────────────────────────────────────────
def make_label(parent, text, size=11, bold=False, color=FG, bg=DARK_BG):
    font = ("Arial", size, "bold" if bold else "normal")
    return tk.Label(parent, text=text, font=font, bg=bg, fg=color)

def make_entry(parent, var, width=20, bg=DARK_BG):
    return tk.Entry(parent, textvariable=var, width=width,
                    bg="#2d2d2d", fg=FG, insertbackground=FG,
                    relief="flat", font=("Arial", 10))

def make_button(parent, text, command, bg="#333333", fg="#ffffff"):
    return tk.Button(parent, text=text, command=command, bg=bg, fg=fg,
                     relief="flat", font=("Arial", 9), cursor="hand2")

def make_log(parent):
    log = tk.Text(parent, height=6, bg="#111111", fg="#aaaaaa",
                  font=("Courier", 9), relief="flat", state="disabled")
    return log

def log_write(log_widget, msg):
    log_widget.config(state="normal")
    log_widget.insert("end", msg + "\n")
    log_widget.see("end")
    log_widget.config(state="disabled")
    log_widget.update()


# ─────────────────────────────────────────────────────────────────────────────
# RESIZE INTELIGENTE (compartido)
# ─────────────────────────────────────────────────────────────────────────────
def smart_resize(img, target_w, target_h, mode):
    img = img.convert("RGBA") if img.mode in ("RGBA", "LA", "P") else img.convert("RGB")
    src_w, src_h = img.size

    if mode.startswith("Estirar"):
        return img.resize((target_w, target_h), Image.LANCZOS)

    ratio_fill = max(target_w / src_w, target_h / src_h)
    ratio_fit = min(target_w / src_w, target_h / src_h)
    ratio = ratio_fill if mode.startswith("Fill") else ratio_fit

    new_w = max(1, round(src_w * ratio))
    new_h = max(1, round(src_h * ratio))
    resized = img.resize((new_w, new_h), Image.LANCZOS)

    if mode.startswith("Fill"):
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))
    else:
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


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 1: IMAGE OPTIMIZER
# ─────────────────────────────────────────────────────────────────────────────
class OptimizerTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)

        self.input_folder = tk.StringVar()
        self.output_folder = tk.StringVar()
        self.preset_name = tk.StringVar(value=list(PRESETS.keys())[0])
        self.format_var = tk.StringVar(value="PNG")
        self.width_var = tk.StringVar(value="512")
        self.height_var = tk.StringVar(value="512")
        self.quality_var = tk.StringVar(value="85")
        self.alpha_var = tk.BooleanVar(value=True)
        self.overwrite_var = tk.BooleanVar(value=False)
        self.fit_mode_var = tk.StringVar(value="Fill (recorta, sin bordes)")

        self._build_ui()
        self._on_preset_change()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        make_label(self, "Carpeta de entrada", bold=True).pack(anchor="w", **pad)
        f1 = tk.Frame(self, bg=DARK_BG); f1.pack(fill="x", padx=20, pady=2)
        make_entry(f1, self.input_folder, width=46).pack(side="left", ipady=4)
        make_button(f1, "Buscar", self._pick_input).pack(side="left", padx=(8,0), ipady=4, ipadx=6)

        make_label(self, "Carpeta de salida", bold=True).pack(anchor="w", **pad)
        f2 = tk.Frame(self, bg=DARK_BG); f2.pack(fill="x", padx=20, pady=2)
        make_entry(f2, self.output_folder, width=46).pack(side="left", ipady=4)
        make_button(f2, "Buscar", self._pick_output).pack(side="left", padx=(8,0), ipady=4, ipadx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        make_label(self, "Preset", bold=True).pack(anchor="w", **pad)
        preset_menu = ttk.Combobox(self, textvariable=self.preset_name,
                                   values=list(PRESETS.keys()), state="readonly",
                                   font=("Arial", 10), width=42)
        preset_menu.pack(anchor="w", padx=20, pady=2)
        preset_menu.bind("<<ComboboxSelected>>", self._on_preset_change)

        self.desc_label = tk.Label(self, text="", font=("Arial", 9), bg=DARK_BG,
                                   fg="#888888", justify="left", wraplength=580)
        self.desc_label.pack(anchor="w", padx=20, pady=(4, 8))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=4)

        make_label(self, "Parámetros", bold=True).pack(anchor="w", **pad)
        params = tk.Frame(self, bg=DARK_BG); params.pack(fill="x", padx=20, pady=4)

        tk.Label(params, text="Formato:", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=0, column=0, sticky="w", padx=(0,8), pady=4)
        ttk.Combobox(params, textvariable=self.format_var, values=["PNG","JPEG","WEBP"],
                    state="readonly", font=("Arial", 10), width=8).grid(row=0, column=1, sticky="w", pady=4)

        tk.Label(params, text="Ancho:", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=0, column=2, sticky="w", padx=(20,8), pady=4)
        make_entry(params, self.width_var, width=6).grid(row=0, column=3, sticky="w", pady=4)
        tk.Label(params, text="px", bg=DARK_BG, fg="#888888", font=("Arial", 10)).grid(row=0, column=4, sticky="w", padx=(2,20))

        tk.Label(params, text="Alto:", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=0, column=5, sticky="w", padx=(0,8), pady=4)
        make_entry(params, self.height_var, width=6).grid(row=0, column=6, sticky="w", pady=4)
        tk.Label(params, text="px", bg=DARK_BG, fg="#888888", font=("Arial", 10)).grid(row=0, column=7, sticky="w", padx=2)

        tk.Label(params, text="Calidad (JPG/WEBP):", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=1, column=0, columnspan=2, sticky="w", pady=4)
        make_entry(params, self.quality_var, width=4).grid(row=1, column=2, sticky="w", padx=(20,4), pady=4)
        tk.Label(params, text="(1-100)", bg=DARK_BG, fg="#888888", font=("Arial", 9)).grid(row=1, column=3, sticky="w")

        tk.Label(params, text="Encaje al recuadro:", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(10,4))
        ttk.Combobox(params, textvariable=self.fit_mode_var,
                    values=["Fill (recorta, sin bordes)","Fit (contiene, con bordes)",
                            "Fit + fondo blanco","Estirar (deforma)"],
                    state="readonly", font=("Arial", 10), width=26).grid(row=2, column=2, columnspan=4, sticky="w", pady=(10,4))

        tk.Label(params, text="Fill: llena el recuadro entero, recorta el sobrante desde el centro (recomendado).\n"
                              "Fit: la imagen entera cabe dentro, puede dejar huecos transparentes/blancos.",
                font=("Arial", 8), bg=DARK_BG, fg="#777777", justify="left").grid(row=3, column=0, columnspan=7, sticky="w", pady=(0,4))

        tk.Checkbutton(params, text="Mantener canal alpha (transparencia)", variable=self.alpha_var,
                      bg=DARK_BG, fg=FG, selectcolor="#2d2d2d", activebackground=DARK_BG,
                      font=("Arial", 10)).grid(row=4, column=0, columnspan=5, sticky="w", pady=4)

        tk.Checkbutton(params, text="Sobreescribir archivos existentes", variable=self.overwrite_var,
                      bg=DARK_BG, fg=FG, selectcolor="#2d2d2d", activebackground=DARK_BG,
                      font=("Arial", 10)).grid(row=5, column=0, columnspan=5, sticky="w", pady=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        self.log = make_log(self)
        self.log.pack(fill="x", padx=20, pady=(0, 10))

        self.btn = tk.Button(self, text="▶  Convertir imágenes", command=self._run,
                             bg="#2d5a2d", fg="#ffffff", font=("Arial", 12, "bold"),
                             relief="flat", cursor="hand2", activebackground="#3d7a3d")
        self.btn.pack(pady=(0, 20), ipadx=20, ipady=8)

    def _on_preset_change(self, *_):
        p = PRESETS[self.preset_name.get()]
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
        w, h = int(self.width_var.get()), int(self.height_var.get())
        quality = int(self.quality_var.get())
        keep_alpha = self.alpha_var.get()
        overwrite = self.overwrite_var.get()
        fit_mode = self.fit_mode_var.get()

        ext_map = {"PNG": ".png", "JPEG": ".jpg", "WEBP": ".webp"}
        out_ext = ext_map[fmt]

        files = [f for f in os.listdir(src)
                 if f.lower().endswith((".png",".jpg",".jpeg",".webp",".tga",".tif",".tiff"))]

        if not files:
            log_write(self.log, "⚠️  No se encontraron imágenes en la carpeta.")
            self.btn.config(state="normal", text="▶  Convertir imágenes")
            return

        log_write(self.log, f"📁 {len(files)} imágenes encontradas → {dst}")
        ok, skip = 0, 0

        for fname in files:
            stem = os.path.splitext(fname)[0]
            out_path = os.path.join(dst, stem + out_ext)

            if not overwrite and os.path.exists(out_path):
                log_write(self.log, f"  ⏭  {fname} (ya existe, omitido)")
                skip += 1
                continue

            try:
                img = Image.open(os.path.join(src, fname))
                img = smart_resize(img, w, h, fit_mode)

                if fmt == "JPEG":
                    if img.mode in ("RGBA", "LA", "P"):
                        bg = Image.new("RGB", img.size, (255,255,255))
                        if img.mode == "P": img = img.convert("RGBA")
                        bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
                        img = bg
                    else:
                        img = img.convert("RGB")
                    img.save(out_path, "JPEG", quality=quality, optimize=True)
                elif fmt == "WEBP":
                    img.save(out_path, "WEBP", quality=quality, lossless=keep_alpha, method=6)
                else:
                    if keep_alpha and img.mode not in ("RGBA","LA"):
                        img = img.convert("RGBA")
                    elif not keep_alpha:
                        img = img.convert("RGB")
                    img.save(out_path, "PNG", optimize=True)

                size_kb = os.path.getsize(out_path) / 1024
                log_write(self.log, f"  ✅ {fname} → {stem+out_ext} ({size_kb:.0f} KB)")
                ok += 1
            except Exception as e:
                log_write(self.log, f"  ❌ {fname}: {e}")

        log_write(self.log, f"\n✅ {ok} convertidas, {skip} omitidas.")
        self.btn.config(state="normal", text="▶  Convertir imágenes")


# ─────────────────────────────────────────────────────────────────────────────
# PESTAÑA 2: GIF MAKER
# ─────────────────────────────────────────────────────────────────────────────
class GifMakerTab(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent, bg=DARK_BG)

        self.source_mode = tk.StringVar(value="Carpeta de imágenes")
        self.input_folder = tk.StringVar()
        self.input_video = tk.StringVar()
        self.output_path = tk.StringVar()
        self.width_var = tk.StringVar(value="500")
        self.delay_var = tk.StringVar(value="120")
        self.loop_var = tk.BooleanVar(value=True)
        self.bounce_var = tk.BooleanVar(value=False)
        self.max_colors_var = tk.StringVar(value="256")
        self.video_fps_var = tk.StringVar(value="10")
        self.video_start_var = tk.StringVar(value="0")
        self.video_end_var = tk.StringVar(value="")

        self._build_ui()
        self._on_source_change()

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        make_label(self, "Origen de los frames", bold=True).pack(anchor="w", **pad)
        src_menu = ttk.Combobox(self, textvariable=self.source_mode,
                                values=["Carpeta de imágenes", "Archivo de vídeo"],
                                state="readonly", font=("Arial", 10), width=30)
        src_menu.pack(anchor="w", padx=20, pady=2)
        src_menu.bind("<<ComboboxSelected>>", self._on_source_change)

        # Contenedor único donde se dibuja SOLO la sección activa (imágenes o vídeo)
        self.source_container = tk.Frame(self, bg=DARK_BG)
        self.source_container.pack(fill="x")

        make_label(self, "Guardar GIF como", bold=True).pack(anchor="w", **pad)
        f2 = tk.Frame(self, bg=DARK_BG); f2.pack(fill="x", padx=20, pady=2)
        make_entry(f2, self.output_path, width=42).pack(side="left", ipady=4)
        make_button(f2, "Buscar", self._pick_output).pack(side="left", padx=(8,0), ipady=4, ipadx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        make_label(self, "Parámetros del GIF", bold=True).pack(anchor="w", **pad)
        params = tk.Frame(self, bg=DARK_BG); params.pack(fill="x", padx=20, pady=4)

        tk.Label(params, text="Ancho (px):", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=6)
        make_entry(params, self.width_var, width=8).grid(row=0, column=1, sticky="w", padx=(8,20))

        tk.Label(params, text="Delay entre frames (ms):", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=6)
        make_entry(params, self.delay_var, width=8).grid(row=1, column=1, sticky="w", padx=(8,20))

        tk.Label(params, text="Colores máx. (8-256):", bg=DARK_BG, fg=FG, font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=6)
        make_entry(params, self.max_colors_var, width=8).grid(row=2, column=1, sticky="w", padx=(8,20))

        tk.Checkbutton(params, text="Loop infinito", variable=self.loop_var, bg=DARK_BG, fg=FG,
                      selectcolor="#2d2d2d", activebackground=DARK_BG, font=("Arial", 10)
                      ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        tk.Checkbutton(params, text="Efecto bounce (ida y vuelta, sin salto en el loop)",
                      variable=self.bounce_var, bg=DARK_BG, fg=FG, selectcolor="#2d2d2d",
                      activebackground=DARK_BG, font=("Arial", 10)
                      ).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        self.log = make_log(self)
        self.log.pack(fill="x", padx=20, pady=(0, 10))

        self.btn = tk.Button(self, text="▶  Generar GIF", command=self._run,
                             bg="#2d5a2d", fg="#ffffff", font=("Arial", 12, "bold"),
                             relief="flat", cursor="hand2", activebackground="#3d7a3d")
        self.btn.pack(pady=(0, 20), ipadx=20, ipady=8)

    def _build_folder_source(self, parent):
        pad = {"padx": 20, "pady": 6}
        make_label(parent, "Carpeta con las imágenes", bold=True).pack(anchor="w", **pad)
        f1 = tk.Frame(parent, bg=DARK_BG); f1.pack(fill="x", padx=20, pady=2)
        make_entry(f1, self.input_folder, width=42).pack(side="left", ipady=4)
        make_button(f1, "Buscar", self._pick_input_folder).pack(side="left", padx=(8,0), ipady=4, ipadx=6)

    def _build_video_source(self, parent):
        pad = {"padx": 20, "pady": 6}
        make_label(parent, "Archivo de vídeo", bold=True).pack(anchor="w", **pad)
        v1 = tk.Frame(parent, bg=DARK_BG); v1.pack(fill="x", padx=20, pady=2)
        make_entry(v1, self.input_video, width=42).pack(side="left", ipady=4)
        make_button(v1, "Buscar", self._pick_input_video).pack(side="left", padx=(8,0), ipady=4, ipadx=6)

        video_params = tk.Frame(parent, bg=DARK_BG)
        video_params.pack(fill="x", padx=20, pady=(8,4))

        tk.Label(video_params, text="FPS a extraer:", bg=DARK_BG, fg=FG,
                font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=4)
        make_entry(video_params, self.video_fps_var, width=6).grid(row=0, column=1, sticky="w", padx=(8,20))
        tk.Label(video_params, text="(fotogramas por segundo a capturar del vídeo)",
                bg=DARK_BG, fg="#777777", font=("Arial", 8)).grid(row=0, column=2, sticky="w")

        tk.Label(video_params, text="Inicio (seg):", bg=DARK_BG, fg=FG,
                font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=4)
        make_entry(video_params, self.video_start_var, width=6).grid(row=1, column=1, sticky="w", padx=(8,20))

        tk.Label(video_params, text="Fin (seg, vacío = hasta el final):", bg=DARK_BG, fg=FG,
                font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=4)
        make_entry(video_params, self.video_end_var, width=6).grid(row=2, column=1, sticky="w", padx=(8,20))



    def _on_source_change(self, *_):
        # Vaciar el contenedor y reconstruir solo la sección activa
        for widget in self.source_container.winfo_children():
            widget.destroy()

        if self.source_mode.get() == "Archivo de vídeo":
            self._build_video_source(self.source_container)
        else:
            self._build_folder_source(self.source_container)

    def _pick_input_folder(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta con las imágenes")
        if folder:
            self.input_folder.set(folder)
            if not self.output_path.get():
                self.output_path.set(os.path.join(folder, "output.gif"))

    def _pick_input_video(self):
        path = filedialog.askopenfilename(title="Selecciona el archivo de vídeo",
                                          filetypes=[("Vídeo", "*.mp4 *.mov *.avi *.mkv *.webm")])
        if path:
            self.input_video.set(path)
            if not self.output_path.get():
                self.output_path.set(os.path.splitext(path)[0] + ".gif")

    def _pick_output(self):
        path = filedialog.asksaveasfilename(title="Guardar GIF como", defaultextension=".gif",
                                            filetypes=[("GIF", "*.gif")])
        if path:
            self.output_path.set(path)

    def _natural_key(self, s):
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

    def _run(self):
        is_video = self.source_mode.get() == "Archivo de vídeo"
        if is_video and not self.input_video.get():
            messagebox.showerror("Error", "Selecciona un archivo de vídeo.")
            return
        if not is_video and not self.input_folder.get():
            messagebox.showerror("Error", "Selecciona una carpeta con imágenes.")
            return
        if not self.output_path.get():
            messagebox.showerror("Error", "Indica dónde guardar el GIF.")
            return
        self.btn.config(state="disabled", text="Procesando...")
        threading.Thread(target=self._process, daemon=True).start()

    def _extract_video_frames(self):
        """Extrae frames de un vídeo usando OpenCV según el FPS objetivo y el rango elegido."""
        import cv2

        path = self.input_video.get()
        cap = cv2.VideoCapture(path)
        if not cap.isOpened():
            raise RuntimeError("No se pudo abrir el vídeo. ¿Formato soportado?")

        src_fps = cap.get(cv2.CAP_PROP_FPS) or 30
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        duration = total_frames / src_fps if src_fps else 0

        target_fps = float(self.video_fps_var.get())
        start_sec = float(self.video_start_var.get() or 0)
        end_str = self.video_end_var.get().strip()
        end_sec = float(end_str) if end_str else duration

        log_write(self.log, f"🎥 Vídeo: {src_fps:.1f} fps origen, {duration:.1f}s de duración")
        log_write(self.log, f"   Extrayendo de {start_sec:.1f}s a {end_sec:.1f}s a {target_fps} fps")

        step = max(1, round(src_fps / target_fps))
        start_frame = int(start_sec * src_fps)
        end_frame = int(end_sec * src_fps)

        frames = []
        idx = 0
        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
        current = start_frame

        while current < end_frame:
            ok, frame = cap.read()
            if not ok:
                break
            if idx % step == 0:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                frames.append(Image.fromarray(frame_rgb))
            idx += 1
            current += 1

        cap.release()
        log_write(self.log, f"   {len(frames)} frames extraídos")
        return frames

    def _process(self):
        is_video = self.source_mode.get() == "Archivo de vídeo"
        out = self.output_path.get()

        try:
            width = int(self.width_var.get())
            delay = int(self.delay_var.get())
            max_colors = min(256, max(8, int(self.max_colors_var.get())))
        except ValueError:
            log_write(self.log, "❌ Parámetros inválidos.")
            self.btn.config(state="normal", text="▶  Generar GIF")
            return

        try:
            if is_video:
                raw_frames = self._extract_video_frames()
            else:
                src = self.input_folder.get()
                files = [f for f in os.listdir(src) if f.lower().endswith((".png",".jpg",".jpeg",".webp"))]
                files.sort(key=self._natural_key)
                if not files:
                    log_write(self.log, "⚠️  No se encontraron imágenes en la carpeta.")
                    self.btn.config(state="normal", text="▶  Generar GIF")
                    return
                log_write(self.log, f"📁 {len(files)} imágenes encontradas, en orden:")
                for f in files[:10]:
                    log_write(self.log, f"   {f}")
                if len(files) > 10:
                    log_write(self.log, f"   ... y {len(files)-10} más")
                raw_frames = [Image.open(os.path.join(src, f)) for f in files]
        except ImportError:
            log_write(self.log, "❌ Falta la librería 'opencv-python'. Instálala con:\n   pip install opencv-python")
            self.btn.config(state="normal", text="▶  Generar GIF")
            return
        except Exception as e:
            log_write(self.log, f"❌ Error leyendo el origen: {e}")
            self.btn.config(state="normal", text="▶  Generar GIF")
            return

        if not raw_frames:
            log_write(self.log, "⚠️  No se obtuvieron frames.")
            self.btn.config(state="normal", text="▶  Generar GIF")
            return

        frames = []
        for img in raw_frames:
            img = img.convert("RGBA")
            ratio = width / img.width
            new_size = (width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

            bg = Image.new("RGBA", img.size, (255,255,255,255))
            bg.paste(img, mask=img.split()[-1])
            img = bg.convert("RGB")
            img = img.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
            frames.append(img)

        if self.bounce_var.get():
            frames = frames + frames[-2:0:-1]
            log_write(self.log, f"🔁 Efecto bounce aplicado: {len(frames)} frames totales")

        log_write(self.log, f"\n🎬 Generando GIF ({width}px ancho, {delay}ms/frame, {max_colors} colores)...")

        frames[0].save(out, save_all=True, append_images=frames[1:],
                       duration=delay, loop=0 if self.loop_var.get() else 1, optimize=True)

        size_kb = os.path.getsize(out) / 1024
        log_write(self.log, f"\n✅ GIF guardado: {out}")
        log_write(self.log, f"   Peso: {size_kb:.0f} KB")
        if size_kb > 3000:
            log_write(self.log, "   ⚠️  Es un GIF pesado para email — considera reducir ancho, colores o nº de frames.")

        self.btn.config(state="normal", text="▶  Generar GIF")


# ─────────────────────────────────────────────────────────────────────────────
# APP PRINCIPAL CON PESTAÑAS
# ─────────────────────────────────────────────────────────────────────────────
class ZenShadersTools(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZenShaders Tools")
        self.geometry("660x780")
        self.minsize(660, 650)
        self.configure(bg=DARK_BG)

        # Header
        tk.Label(self, text="ZenShaders Tools", font=("Arial", 16, "bold"),
                 bg=DARK_BG, fg="#ffffff").pack(pady=(18, 2))
        tk.Label(self, text="Herramientas internas para preparar assets de la landing page",
                 font=("Arial", 9), bg=DARK_BG, fg="#888888").pack(pady=(0, 12))

        # Estilo de pestañas oscuro
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=DARK_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background="#2d2d2d", foreground="#aaaaaa",
                        padding=[16, 8], font=("Arial", 10, "bold"))
        style.map("TNotebook.Tab", background=[("selected", DARK_BG)],
                 foreground=[("selected", "#ffffff")])

        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0,10))

        tab1 = OptimizerTab(notebook)
        tab2 = GifMakerTab(notebook)

        notebook.add(tab1, text="🖼  Image Optimizer")
        notebook.add(tab2, text="🎞  GIF Maker")


if __name__ == "__main__":
    app = ZenShadersTools()
    app.mainloop()
