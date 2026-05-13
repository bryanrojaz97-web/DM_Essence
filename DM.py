import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps
import mysql.connector
import base64
import io
import os
import subprocess

# --- CONFIGURACIÓN GLOBAL ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

def configurar_git_identidad():
    """Configura la identidad de Git localmente"""
    try:
        subprocess.run(['git', 'config', '--global', 'user.name', 'bryanrojaz97-web'], check=True)
        subprocess.run(['git', 'config', '--global', 'user.email', 'bryanrojaz97@gmail.com'], check=True)
    except:
        pass # Ignorar si Git no está instalado

class MainApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        configurar_git_identidad()
        self.title("Sistema DM Essence - Panel Profesional v2.0")
        self.geometry("1200x800")
        self.configure(fg_color="#0a0a0a")

        self.menu_expandido = True
        self.img_base64_temp = ""
        self.modulo_actual = "Dashboard"

        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#141414")
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="black")
        self.main_view.pack(side="right", fill="both", expand=True)

        self.crear_sidebar()
        self.show_dashboard()

    def crear_sidebar(self):
        self.btn_toggle = ctk.CTkButton(
            self.sidebar_frame, text="≡", width=40, height=40,
            fg_color="transparent", font=("Roboto", 28),
            command=self.toggle_menu, hover_color="#222"
        )
        self.btn_toggle.pack(pady=10, anchor="w", padx=10)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, text="DM ESSENCE",
            font=ctk.CTkFont(size=22, weight="bold", family="Roboto"),
            text_color="#3b8ed0"
        )
        self.logo_label.pack(pady=15)

        self.mod_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.mod_container.pack(fill="both", expand=True)

        menu_items = [
            ("Dashboard", "🏠", self.show_dashboard),
            ("Inventario", "📦", self.show_inventario),
            ("Productos", "🧴", self.show_productos),
            ("Ventas", "💰", self.show_ventas),
            ("Clientes", "👥", self.show_clientes),
            ("Pagos", "💳", self.show_pagos),
            ("Reportes", "📊", self.show_reportes)
        ]

        for texto, icono, comando in menu_items:
            btn = ctk.CTkButton(
                self.mod_container, text=f"{icono}  {texto}",
                anchor="w", fg_color="transparent", height=45,
                font=("Roboto", 15), text_color="#aaaaaa",
                hover_color="#222222", command=comando
            )
            btn.pack(fill="x", padx=10, pady=2)

    def toggle_menu(self):
        if self.menu_expandido:
            self.sidebar_frame.configure(width=65)
            self.logo_label.pack_forget()
            self.menu_expandido = False
        else:
            self.sidebar_frame.configure(width=240)
            self.logo_label.pack(pady=15)
            self.menu_expandido = True

    def conectar_db(self):
        try:
            return mysql.connector.connect(
                host="localhost", port=3306, user="root",
                password="Samuel", database="dm_essence"
            )
        except Exception as e:
            print(f"Error de conexión: {e}")
            return None

    def limpiar_vista(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

    def show_productos(self):
        self.limpiar_vista()
        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))
        ctk.CTkLabel(header, text="Gestión de Catálogo", font=("Roboto", 26, "bold"), text_color="white").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filtrar_productos())
        search_bar = ctk.CTkEntry(header, placeholder_text="🔍 Buscar...", width=350, height=40, textvariable=self.search_var)
        search_bar.pack(side="right", padx=10)

        actions = ctk.CTkFrame(self.main_view, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=10)
        ctk.CTkButton(actions, text="+ NUEVO", fg_color="#28a745", command=lambda: self.abrir_formulario()).pack(side="left", padx=5)
        
        self.tree = ttk.Treeview(self.main_view, columns=("ID", "PRODUCTO", "CASA", "VALOR", "STOCK"), show='headings')
        for col in self.tree["columns"]: self.tree.heading(col, text=col); self.tree.column(col, width=100)
        self.tree.pack(fill="both", expand=True, padx=30, pady=15)
        self.cargar_datos_tabla()

    def cargar_datos_tabla(self, query_extra=""):
        for item in self.tree.get_children(): self.tree.delete(item)
        db = self.conectar_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT id, producto, casa, valor, stock FROM productos" + query_extra)
            for row in cursor.fetchall(): self.tree.insert("", "end", values=row)
            db.close()

    def filtrar_productos(self):
        term = self.search_var.get()
        self.cargar_datos_tabla(f" WHERE producto LIKE '%{term}%' OR casa LIKE '%{term}%'")

    def abrir_formulario(self): # Simplificado para brevedad
        messagebox.showinfo("Info", "Formulario abierto")

    def show_dashboard(self):
        self.limpiar_vista()
        ctk.CTkLabel(self.main_view, text="Resumen General", font=("Roboto", 28, "bold")).pack(pady=40)

    def show_inventario(self): self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Inventario", font=("Roboto", 24)).pack(pady=50)
    def show_ventas(self): self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Ventas", font=("Roboto", 24)).pack(pady=50)
    def show_clientes(self): self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Clientes", font=("Roboto", 24)).pack(pady=50)
    def show_pagos(self): self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Pagos", font=("Roboto", 24)).pack(pady=50)
    def show_reportes(self): self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Reportes", font=("Roboto", 24)).pack(pady=50)

class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        configurar_git_identidad()
        self.title("DM Essence - Autenticación")
        self.geometry("450x650")
        self.configure(fg_color="#050505")

        # RUTA CORREGIDA: Busca el logo en la misma carpeta que el script
        self.logo_path = os.path.join(os.path.dirname(__file__), "Dm_logo.jpeg")
        
        try:
            raw_img = Image.open(self.logo_path).convert("RGBA")
            raw_img = ImageOps.fit(raw_img, (160, 160), centering=(0.5, 0.5))
            mask = Image.new('L', (160, 160), 0)
            draw = ImageDraw.Draw(mask)
            draw.ellipse((0, 0, 160, 160), fill=255)
            raw_img.putalpha(mask)
            self.logo_img = ctk.CTkImage(light_image=raw_img, dark_image=raw_img, size=(160, 160))
            ctk.CTkLabel(self, image=self.logo_img, text="").pack(pady=(40, 20))
        except:
            ctk.CTkLabel(self, text="DM LOGO", font=("Arial", 30, "bold"), text_color="#3b8ed0").pack(pady=60)

        self.u_entry = ctk.CTkEntry(self, placeholder_text="Usuario", width=300, height=45)
        self.u_entry.pack(pady=10)
        self.p_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=300, height=45)
        self.p_entry.pack(pady=10)

        ctk.CTkButton(self, text="ACCEDER", width=300, height=50, command=self.validar_login).pack(pady=30)

    def validar_login(self):
        if self.u_entry.get() == "admin" or self.u_entry.get() == "": # Bypass para pruebas
            self.destroy()
            MainApp().mainloop()

if __name__ == "__main__":
    app = LoginApp()
    app.mainloop()
