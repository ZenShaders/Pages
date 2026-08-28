"""
ZenShaders GIF Maker
Convierte una secuencia de imágenes (PNG/JPG) en un GIF animado.
Requiere: pip install pillow
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os
import re

class GifMaker(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ZenShaders GIF Maker")
        self.geometry("560x560")
        self.minsize(560, 500)
        self.resizable(True, True)
        self.configure(bg="#1a1a1a")

        self.input_folder = tk.StringVar()
        self.output_path = tk.StringVar()
        self.width_var = tk.StringVar(value="500")
        self.delay_var = tk.StringVar(value="120")
        self.loop_var = tk.BooleanVar(value=True)
        self.bounce_var = tk.BooleanVar(value=False)
        self.max_colors_var = tk.StringVar(value="256")

        self._build_ui()

    def _label(self, parent, text, size=11, bold=False, color="#e0e0e0"):
        font = ("Arial", size, "bold" if bold else "normal")
        return tk.Label(parent, text=text, font=font, bg="#1a1a1a", fg=color)

    def _entry(self, parent, var, width=20):
        return tk.Entry(parent, textvariable=var, width=width,
                        bg="#2d2d2d", fg="#e0e0e0", insertbackground="#e0e0e0",
                        relief="flat", font=("Arial", 10))

    def _build_ui(self):
        pad = {"padx": 20, "pady": 6}

        tk.Label(self, text="ZenShaders GIF Maker", font=("Arial", 15, "bold"),
                 bg="#1a1a1a", fg="#ffffff").pack(pady=(20, 4))
        tk.Label(self, text="Convierte una secuencia de imágenes en un GIF animado",
                 font=("Arial", 10), bg="#1a1a1a", fg="#888888").pack(pady=(0, 16))

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=4)

        # Carpeta entrada
        self._label(self, "Carpeta con las imágenes", bold=True).pack(anchor="w", **pad)
        f1 = tk.Frame(self, bg="#1a1a1a")
        f1.pack(fill="x", padx=20, pady=2)
        self._entry(f1, self.input_folder, width=42).pack(side="left", ipady=4)
        tk.Button(f1, text="Buscar", command=self._pick_input,
                  bg="#333333", fg="#ffffff", relief="flat", font=("Arial", 9),
                  cursor="hand2").pack(side="left", padx=(8, 0), ipady=4, ipadx=6)

        self._label(self, "Guardar GIF como", bold=True).pack(anchor="w", **pad)
        f2 = tk.Frame(self, bg="#1a1a1a")
        f2.pack(fill="x", padx=20, pady=2)
        self._entry(f2, self.output_path, width=42).pack(side="left", ipady=4)
        tk.Button(f2, text="Buscar", command=self._pick_output,
                  bg="#333333", fg="#ffffff", relief="flat", font=("Arial", 9),
                  cursor="hand2").pack(side="left", padx=(8, 0), ipady=4, ipadx=6)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        # Parámetros
        self._label(self, "Parámetros", bold=True).pack(anchor="w", **pad)
        params = tk.Frame(self, bg="#1a1a1a")
        params.pack(fill="x", padx=20, pady=4)

        tk.Label(params, text="Ancho (px):", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=0, column=0, sticky="w", pady=6)
        self._entry(params, self.width_var, width=8).grid(row=0, column=1, sticky="w", padx=(8,20))

        tk.Label(params, text="Delay entre frames (ms):", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=1, column=0, sticky="w", pady=6)
        self._entry(params, self.delay_var, width=8).grid(row=1, column=1, sticky="w", padx=(8,20))

        tk.Label(params, text="Colores máx. (8-256):", bg="#1a1a1a", fg="#e0e0e0",
                 font=("Arial", 10)).grid(row=2, column=0, sticky="w", pady=6)
        self._entry(params, self.max_colors_var, width=8).grid(row=2, column=1, sticky="w", padx=(8,20))

        tk.Checkbutton(params, text="Loop infinito", variable=self.loop_var,
                       bg="#1a1a1a", fg="#e0e0e0", selectcolor="#2d2d2d",
                       activebackground="#1a1a1a", font=("Arial", 10)
                       ).grid(row=3, column=0, columnspan=2, sticky="w", pady=4)

        tk.Checkbutton(params, text="Efecto bounce (ida y vuelta, sin salto en el loop)",
                       variable=self.bounce_var, bg="#1a1a1a", fg="#e0e0e0",
                       selectcolor="#2d2d2d", activebackground="#1a1a1a",
                       font=("Arial", 10)).grid(row=4, column=0, columnspan=2, sticky="w", pady=4)

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=10)

        self.log = tk.Text(self, height=6, bg="#111111", fg="#aaaaaa",
                           font=("Courier", 9), relief="flat", state="disabled")
        self.log.pack(fill="x", padx=20, pady=(0, 10))

        self.btn = tk.Button(self, text="▶  Generar GIF", command=self._run,
                             bg="#2d5a2d", fg="#ffffff", font=("Arial", 12, "bold"),
                             relief="flat", cursor="hand2", activebackground="#3d7a3d")
        self.btn.pack(pady=(0, 20), ipadx=20, ipady=8)

    def _pick_input(self):
        folder = filedialog.askdirectory(title="Selecciona carpeta con las imágenes")
        if folder:
            self.input_folder.set(folder)
            if not self.output_path.get():
                self.output_path.set(os.path.join(folder, "output.gif"))

    def _pick_output(self):
        path = filedialog.asksaveasfilename(title="Guardar GIF como", defaultextension=".gif",
                                            filetypes=[("GIF", "*.gif")])
        if path:
            self.output_path.set(path)

    def _log(self, msg):
        self.log.config(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.config(state="disabled")
        self.update()

    def _natural_key(self, s):
        # Ordena "img2" antes que "img10" correctamente
        return [int(t) if t.isdigit() else t.lower() for t in re.split(r'(\d+)', s)]

    def _run(self):
        if not self.input_folder.get():
            messagebox.showerror("Error", "Selecciona una carpeta con imágenes.")
            return
        if not self.output_path.get():
            messagebox.showerror("Error", "Indica dónde guardar el GIF.")
            return
        self.btn.config(state="disabled", text="Procesando...")
        self._process()
        self.btn.config(state="normal", text="▶  Generar GIF")

    def _process(self):
        src = self.input_folder.get()
        out = self.output_path.get()

        files = [f for f in os.listdir(src)
                 if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))]
        files.sort(key=self._natural_key)

        if not files:
            self._log("⚠️  No se encontraron imágenes en la carpeta.")
            return

        self._log(f"📁 {len(files)} imágenes encontradas, en orden:")
        for f in files[:10]:
            self._log(f"   {f}")
        if len(files) > 10:
            self._log(f"   ... y {len(files)-10} más")

        try:
            width = int(self.width_var.get())
            delay = int(self.delay_var.get())
            max_colors = min(256, max(8, int(self.max_colors_var.get())))
        except ValueError:
            self._log("❌ Parámetros inválidos (ancho/delay/colores deben ser números).")
            return

        frames = []
        for fname in files:
            path = os.path.join(src, fname)
            img = Image.open(path).convert("RGBA")

            # Redimensionar manteniendo proporción
            ratio = width / img.width
            new_size = (width, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)

            # Componer sobre fondo blanco si tiene alpha (los GIF no soportan alpha real)
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            bg.paste(img, mask=img.split()[-1])
            img = bg.convert("RGB")

            # Reducir a paleta de colores para menor peso
            img = img.convert("P", palette=Image.ADAPTIVE, colors=max_colors)
            frames.append(img)

        if self.bounce_var.get():
            frames = frames + frames[-2:0:-1]
            self._log(f"🔁 Efecto bounce aplicado: {len(frames)} frames totales")

        self._log(f"\n🎬 Generando GIF ({width}px ancho, {delay}ms/frame, {max_colors} colores)...")

        frames[0].save(
            out,
            save_all=True,
            append_images=frames[1:],
            duration=delay,
            loop=0 if self.loop_var.get() else 1,
            optimize=True
        )

        size_kb = os.path.getsize(out) / 1024
        self._log(f"\n✅ GIF guardado: {out}")
        self._log(f"   Peso: {size_kb:.0f} KB")
        if size_kb > 3000:
            self._log("   ⚠️  Es un GIF pesado para email — considera reducir ancho, colores o nº de frames.")

if __name__ == "__main__":
    app = GifMaker()
    app.mainloop()
