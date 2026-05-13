import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import customtkinter as ctk
from PIL import Image, ImageDraw, ImageOps
import mysql.connector
import base64
import io
import os


# --- CONFIGURACIÓN GLOBAL ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class MainApp(ctk.CTk):
    """
    Clase principal que gestiona el panel de control y los módulos del sistema.
    """

    def __init__(self):
        super().__init__()
        self.title("Sistema DM Essence - Panel Profesional v2.0")
        self.geometry("1200x800")
        self.configure(fg_color="#0a0a0a")

        # Variables de estado
        self.menu_expandido = True
        self.img_base64_temp = ""
        self.modulo_actual = "Dashboard"

        # --- ESTRUCTURA BASE ---
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color="#141414")
        self.sidebar_frame.pack(side="left", fill="y")
        self.sidebar_frame.pack_propagate(False)

        self.main_view = ctk.CTkFrame(self, corner_radius=0, fg_color="black")
        self.main_view.pack(side="right", fill="both", expand=True)

        self.crear_sidebar()
        self.show_dashboard()

    # --- DISEÑO DE SIDEBAR ---
    def crear_sidebar(self):
        # Botón hamburguesa
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

        # Contenedor de botones
        self.mod_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        self.mod_container.pack(fill="both", expand=True)

        menu_items = [
            ("Dashboard", "                          🏠", self.show_dashboard),
            ("Inventario", "                         📦", self.show_inventario),
            ("Productos", "                          🧴", self.show_productos),
            ("Ventas", "                             💰", self.show_ventas),
            ("Clientes", "                           👥", self.show_clientes),
            ("Pagos", "                              💳", self.show_pagos),
            ("Reportes", "                           📊", self.show_reportes)
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

    # --- UTILIDADES DE BASE DE DATOS ---
    def conectar_db(self):
        try:
            conn = mysql.connector.connect(
                host="localhost", port=3306, user="root",
                password="Samuel", database="dm_essence"
            )
            return conn
        except Exception as e:
            print(f"Error de conexión: {e}")
            return None

    def limpiar_vista(self):
        for widget in self.main_view.winfo_children():
            widget.destroy()

    # --- MÓDULO PRODUCTOS (CORE) ---
    def show_productos(self):
        self.limpiar_vista()
        self.modulo_actual = "Productos"

        # Encabezado
        header = ctk.CTkFrame(self.main_view, fg_color="transparent")
        header.pack(fill="x", padx=30, pady=(30, 10))

        ctk.CTkLabel(
            header, text="Gestión de Catálogo",
            font=("Roboto", 26, "bold"), text_color="white"
        ).pack(side="left")

        # Buscador
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *args: self.filtrar_productos())

        search_bar = ctk.CTkEntry(
            header, placeholder_text="🔍 Buscar por nombre o casa...",
            width=350, height=40, textvariable=self.search_var
        )
        search_bar.pack(side="right", padx=10)

        # Barra de acciones
        actions = ctk.CTkFrame(self.main_view, fg_color="transparent")
        actions.pack(fill="x", padx=30, pady=10)

        ctk.CTkButton(
            actions, text="+ NUEVO PRODUCTO", fg_color="#28a745",
            hover_color="#1e7e34", width=160, height=35,
            command=lambda: self.abrir_formulario()
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            actions, text="🗑️ ELIMINAR", fg_color="#dc3545",
            hover_color="#a71d2a", width=120, height=35,
            command=self.eliminar_seleccionado
        ).pack(side="left", padx=5)

        # Tabla (Treeview)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview", background="#1a1a1a", foreground="white",
            fieldbackground="#1a1a1a", rowheight=40, borderwidth=0,
            font=("Roboto", 11)
        )
        style.configure("Treeview.Heading", background="#333", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', '#3b8ed0')])

        self.tree = ttk.Treeview(
            self.main_view,
            columns=("ID", "PRODUCTO", "CASA", "VALOR", "STOCK"),
            show='headings'
        )

        self.tree.heading("ID", text="ID")
        self.tree.heading("PRODUCTO", text="PRODUCTO")
        self.tree.heading("CASA", text="CASA / MARCA")
        self.tree.heading("VALOR", text="VALOR UNITARIO")
        self.tree.heading("STOCK", text="STOCK")

        self.tree.column("ID", width=80, anchor="center")
        self.tree.column("PRODUCTO", width=300, anchor="w")
        self.tree.column("CASA", width=200, anchor="w")
        self.tree.column("VALOR", width=150, anchor="center")
        self.tree.column("STOCK", width=100, anchor="center")

        self.tree.pack(fill="both", expand=True, padx=30, pady=15)

        # Evento de doble clic para editar
        self.tree.bind("<Double-1>", self.on_double_click)

        self.cargar_datos_tabla()

    def cargar_datos_tabla(self, query_extra=""):
        for item in self.tree.get_children():
            self.tree.delete(item)

        db = self.conectar_db()
        if db:
            cursor = db.cursor()
            sql = "SELECT id, producto, casa, valor, stock FROM productos" + query_extra
            cursor.execute(sql)
            for row in cursor.fetchall():
                self.tree.insert("", "end", values=row)
            db.close()

    def filtrar_productos(self):
        term = self.search_var.get()
        query = f" WHERE producto LIKE '%{term}%' OR casa LIKE '%{term}%'"
        self.cargar_datos_tabla(query)

    def on_double_click(self, event):
        item_id = self.tree.selection()
        if not item_id: return

        valores = self.tree.item(item_id[0], "values")
        self.abrir_formulario(modo_edicion=True, datos=valores)

    def abrir_formulario(self, modo_edicion=False, datos=None):
        self.modal = ctk.CTkToplevel(self)
        self.modal.title("Editor de Producto" if modo_edicion else "Nuevo Registro")
        self.modal.geometry("750x550")
        self.modal.grab_set()
        self.modal.resizable(False, False)

        self.img_base64_temp = ""  # Reset imagen temporal

        # Contenedor principal del modal
        main_cont = ctk.CTkFrame(self.modal, fg_color="transparent")
        main_cont.pack(fill="both", expand=True, padx=25, pady=25)

        # --- LADO IZQUIERDO: INPUTS ---
        left_p = ctk.CTkFrame(main_cont, fg_color="transparent")
        left_p.pack(side="left", fill="both", expand=True)

        ctk.CTkLabel(left_p, text="Información General", font=("Roboto", 18, "bold")).pack(pady=(0, 20), anchor="w")

        self.ent_prod = ctk.CTkEntry(left_p, placeholder_text="Nombre del Producto", width=280, height=40)
        self.ent_prod.pack(pady=10)

        self.ent_casa = ctk.CTkEntry(left_p, placeholder_text="Casa / Proveedor", width=280, height=40)
        self.ent_casa.pack(pady=10)

        self.ent_val = ctk.CTkEntry(left_p, placeholder_text="Precio de Venta (ej: 25000)", width=280, height=40)
        self.ent_val.pack(pady=10)

        self.ent_stock = ctk.CTkEntry(left_p, placeholder_text="Existencias en Stock", width=280, height=40)
        self.ent_stock.pack(pady=10)

        # --- LADO DERECHO: IMAGEN ---
        right_p = ctk.CTkFrame(main_cont, fg_color="#1a1a1a", corner_radius=15, width=300)
        right_p.pack(side="right", fill="y", padx=(20, 0))
        right_p.pack_propagate(False)

        ctk.CTkLabel(right_p, text="Imagen del Producto", font=("Roboto", 14)).pack(pady=15)

        self.lbl_preview = ctk.CTkLabel(
            right_p, text="📷\nSin Imagen",
            width=200, height=200, fg_color="#0a0a0a", corner_radius=10
        )
        self.lbl_preview.pack(pady=10)

        ctk.CTkButton(
            right_p, text="Seleccionar Archivo",
            fg_color="#3b8ed0", command=self.procesar_imagen
        ).pack(pady=10)

        # Si es edición, cargar datos
        if modo_edicion:
            self.ent_prod.insert(0, datos[1])
            self.ent_casa.insert(0, datos[2])
            self.ent_val.insert(0, datos[3])
            self.ent_stock.insert(0, datos[4])
            self.cargar_imagen_edicion(datos[0])

        # Botón guardar
        btn_txt = "ACTUALIZAR DATOS" if modo_edicion else "GUARDAR PRODUCTO"
        ctk.CTkButton(
            self.modal, text=btn_txt, height=50,
            fg_color="#28a745", font=("Roboto", 16, "bold"),
            command=lambda: self.validar_y_guardar(modo_edicion, datos[0] if datos else None)
        ).pack(side="bottom", fill="x", padx=25, pady=25)

    def cargar_imagen_edicion(self, pid):
        db = self.conectar_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT imagen_b64 FROM productos WHERE id = %s", (pid,))
            res = cursor.fetchone()
            if res and res[0]:
                self.img_base64_temp = res[0]
                self.mostrar_preview(res[0])
            db.close()

    def procesar_imagen(self):
        file = filedialog.askopenfilename(filetypes=[("Imagenes", "*.jpg *.png *.jpeg")])
        if file:
            with open(file, "rb") as image_file:
                encoded = base64.b64encode(image_file.read()).decode('utf-8')
                self.img_base64_temp = encoded
                self.mostrar_preview(encoded)

    def mostrar_preview(self, b64_data):
        try:
            raw_data = base64.b64decode(b64_data)
            img = Image.open(io.BytesIO(raw_data))
            img.thumbnail((200, 200))
            ctk_img = ctk.CTkImage(light_image=img, size=(200, 200))
            self.lbl_preview.configure(image=ctk_img, text="")
        except:
            self.lbl_preview.configure(text="Error al cargar")

    def validar_y_guardar(self, es_update, pid):
        p = self.ent_prod.get().strip()
        c = self.ent_casa.get().strip()
        v = self.ent_val.get().strip()
        s = self.ent_stock.get().strip()

        if not (p and c and v and s):
            messagebox.showwarning("Incompleto", "Todos los campos de texto son requeridos.")
            return

        # Validar numéricos
        try:
            val_f = float(v)
            stock_i = int(s)
        except ValueError:
            messagebox.showerror("Error", "Valor debe ser decimal y Stock debe ser entero.")
            return

        db = self.conectar_db()
        if not db: return
        cursor = db.cursor()

        try:
            if not es_update:
                # Verificar duplicados
                cursor.execute("SELECT id FROM productos WHERE producto = %s", (p,))
                if cursor.fetchone():
                    messagebox.showerror("Duplicado", f"Ya existe un producto llamado '{p}'.")
                    return

                sql = "INSERT INTO productos (producto, casa, valor, stock, imagen_b64) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(sql, (p, c, val_f, stock_i, self.img_base64_temp))
            else:
                sql = "UPDATE productos SET producto=%s, casa=%s, valor=%s, stock=%s, imagen_b64=%s WHERE id=%s"
                cursor.execute(sql, (p, c, val_f, stock_i, self.img_base64_temp, pid))

            db.commit()
            messagebox.showinfo("Exito", "Registro guardado correctamente.")
            self.modal.destroy()
            self.show_productos()
        except Exception as ex:
            messagebox.showerror("Error DB", str(ex))
        finally:
            db.close()

    def eliminar_seleccionado(self):
        item = self.tree.selection()
        if not item:
            messagebox.showwarning("Selección", "Elija un producto de la tabla.")
            return

        id_eliminar = self.tree.item(item[0], "values")[0]
        nombre = self.tree.item(item[0], "values")[1]

        if messagebox.askyesno("Confirmar", f"¿Eliminar permanentemente '{nombre}'?"):
            db = self.conectar_db()
            if db:
                cursor = db.cursor()
                cursor.execute("DELETE FROM productos WHERE id = %s", (id_eliminar,))
                db.commit()
                db.close()
                self.show_productos()

    # --- OTROS MÓDULOS (PLACEHOLDERS) ---
    def show_dashboard(self):
        self.limpiar_vista()
        self.modulo_actual = "Dashboard"
        ctk.CTkLabel(self.main_view, text="Resumen General", font=("Roboto", 28, "bold")).pack(pady=40)

        info_f = ctk.CTkFrame(self.main_view, fg_color="transparent")
        info_f.pack(fill="both", expand=True, padx=50)

        # Cards ficticias
        cards = [("Ventas Hoy", "$1,250.00"), ("Stock Bajo", "12 items"), ("Clientes", "450")]
        for tit, val in cards:
            f = ctk.CTkFrame(info_f, width=250, height=150, fg_color="#141414", corner_radius=15)
            f.pack(side="left", padx=20)
            f.pack_propagate(False)
            ctk.CTkLabel(f, text=tit, font=("Roboto", 14)).pack(pady=(20, 5))
            ctk.CTkLabel(f, text=val, font=("Roboto", 24, "bold"), text_color="#3b8ed0").pack()

    def show_inventario(self):
        self.limpiar_vista(); ctk.CTkLabel(self.main_view, text="Inventario Detallado", font=("Roboto", 24)).pack(
            pady=50)

    def show_ventas(self):
        self.limpiar_pantalla_simple("Registro de Ventas")

    def show_clientes(self):
        self.limpiar_pantalla_simple("Directorio de Clientes")

    def show_pagos(self):
        self.limpiar_pantalla_simple("Cuentas por Cobrar")

    def show_reportes(self):
        self.limpiar_pantalla_simple("Analítica y Reportes PDF")

    def limpiar_pantalla_simple(self, titulo):
        self.limpiar_vista()
        ctk.CTkLabel(self.main_view, text=titulo, font=("Roboto", 24)).pack(pady=50)


# --- CLASE LOGIN ---
class LoginApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("DM Essence - Autenticación")
        self.geometry("450x650")
        self.configure(fg_color="#050505")
        self.clave_maestra = "Breakup30*"

        # Logo Circular
        self.logo_path = r"C:\Users\andres.rojas\PycharmProjects\Dm\Dm_logo.jpeg"
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

        # UI Login
        self.u_entry = ctk.CTkEntry(self, placeholder_text="Usuario", width=300, height=45, corner_radius=10)
        self.u_entry.pack(pady=10)

        self.p_entry = ctk.CTkEntry(self, placeholder_text="Contraseña", show="*", width=300, height=45,
                                    corner_radius=10)
        self.p_entry.pack(pady=10)

        ctk.CTkButton(
            self, text="ACCEDER AL SISTEMA", width=300, height=50,
            corner_radius=10, font=("Roboto", 14, "bold"),
            command=self.validar_login
        ).pack(pady=30)

        self.create_btn = ctk.CTkButton(
            self, text="Crear Nuevo Administrador", fg_color="transparent",
            text_color="#3b8ed0", command=self.ventana_admin
        )
        self.create_btn.pack()

    def conectar_db(self):
        try:
            return mysql.connector.connect(host="localhost", user="root", password="Samuel", database="dm_essence")
        except:
            return None

    def validar_login(self):
        user = self.u_entry.get()
        passw = self.p_entry.get()

        db = self.conectar_db()
        if db:
            cursor = db.cursor()
            cursor.execute("SELECT * FROM usuarios WHERE user = %s AND password = %s", (user, passw))
            if cursor.fetchone():
                self.destroy()
                MainApp().mainloop()
            else:
                messagebox.showerror("Error", "Credenciales Incorrectas")
            db.close()
        else:
            # Bypass para test si no hay DB
            if user == "admin" and passw == "admin":
                self.destroy()
                MainApp().mainloop()

    def ventana_admin(self):
        prompt = ctk.CTkInputDialog(text="Ingrese Clave Maestra:", title="Seguridad")
        if prompt.get_input() == self.clave_maestra:
            # Lógica para insertar en DB (Omitido por brevedad, similar a productos)
            messagebox.showinfo("Autorizado", "Proceda a crear usuario en la DB.")


if __name__ == "__main__":
    # Iniciar aplicación
    app = LoginApp()
    app.mainloop()
