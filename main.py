import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
from PIL import Image, ImageTk
import json
import os
import re
import difflib

class GardenTool:
    def __init__(self, number, name, location, borrowed_by=None):
        self.number = number
        self.name = name
        self.location = location
        self.borrowed_by = borrowed_by

    def __str__(self):
        return f"{self.number}: {self.name}"

    def to_dict(self):
        return {
            "número": self.number,
            "nombre": self.name,
            "ubicación": self.location,
            "quien_se_la_lleva": self.borrowed_by
        }

    @classmethod
    def from_dict(cls, data):
        key_map = {
            "número": "number",
            "nombre": "name",
            "ubicación": "location",
            "quien_se_la_lleva": "borrowed_by"
        }
        data = {key_map.get(k, k): v for k, v in data.items()}
        return cls(data["number"], data["name"], data["location"], data["borrowed_by"])

class CustomDialog(simpledialog.Dialog):
    def __init__(self, parent, title, prompt):
        self.prompt = prompt
        super().__init__(parent, title=title)

    def body(self, master):
        ttk.Label(master, text=self.prompt, font=('calibri', 18)).grid(row=0, pady=10, padx=10)
        self.entry = ttk.Entry(master, font=('calibri', 18))
        self.entry.grid(row=1, pady=10, padx=10)
        return self.entry

    def apply(self):
        self.result = self.entry.get()

class ImageSelectionDialog(tk.Toplevel):
    def __init__(self, parent, images):
        super().__init__(parent)
        self.title("Seleccionar Imagen")
        self.geometry("800x600")
        self.images = images
        self.selected_image = None
        self.create_widgets()

    def create_widgets(self):
        self.canvas = tk.Canvas(self)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        self.frame = tk.Frame(self.canvas)
        self.canvas.create_window((0, 0), window=self.frame, anchor="nw")

        for i, img_path in enumerate(self.images):
            img = Image.open(img_path)
            img = self.rotate_image(img)
            img.thumbnail((400, 400))  # Resize image to fit in a 300x300 box
            photo = ImageTk.PhotoImage(img)
            btn = ttk.Button(self.frame, image=photo, command=lambda x=img_path: self.select_image(x))
            btn.image = photo
            btn.grid(row=i//3, column=i%3, padx=10, pady=10)

    def rotate_image(self, image):
        try:
            exif = image._getexif()
            if exif:
                orientation = exif.get(274, 1)  # 274 is the orientation tag
                if orientation == 3:
                    return image.rotate(180, expand=True)
                elif orientation == 6:
                    return image.rotate(270, expand=True)
                elif orientation == 8:
                    return image.rotate(90, expand=True)
        except (AttributeError, KeyError, IndexError):
            # No EXIF data or orientation not found, proceed without rotation
            pass
        return image

    def select_image(self, img_path):
        self.selected_image = img_path
        self.destroy()

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Herramientas")
        self.root.state('zoomed')  # Para Windows

        self.inventory = []
        self.current_tool = None
        self.locations = []
        self.location_images = {}

        # Configura un estilo global con una fuente más pequeña para la lista desplegable
        self.root.option_add('*TCombobox*Listbox*Font', 'Arial 16')

        self.canvas = None
        self.image_reference = None
        self.current_page = 0
        self.images = []

        self.create_widgets()
        self.load_inventory()
        self.load_locations()
        self.load_location_images()
        self.load_images()

    def create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_columnconfigure(2, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        left_frame = ttk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas = tk.Canvas(left_frame, width=400, height=400)  # Reducir el tamaño del canvas
        self.canvas.pack(expand=True, fill=tk.BOTH)

        middle_frame = ttk.Frame(self.root)
        middle_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.tool_list = tk.Listbox(middle_frame, font=('calibri', 18))
        self.tool_list.pack(expand=True, fill=tk.BOTH)
        self.tool_list.bind('<<ListboxSelect>>', self.on_tool_select)

        right_frame = ttk.Frame(self.root)
        right_frame.grid(row=0, column=2, sticky="nsew", padx=10, pady=10)
        self.create_right_panel(right_frame)

        nav_frame = ttk.Frame(self.root)
        nav_frame.grid(row=1, column=0, columnspan=3, sticky="ew", padx=10, pady=10)
        ttk.Button(nav_frame, text="Anterior", command=self.previous_image, style='Large.TButton').pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_frame, text="Siguiente", command=self.next_image, style='Large.TButton').pack(side=tk.RIGHT, padx=5)

    def create_right_panel(self, parent):
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.number_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.borrower_var = tk.StringVar()
        large_font = font.Font(size=14)  # Reducir el tamaño de la fuente
        ttk.Label(right_panel, text="Número:", font=large_font).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(right_panel, textvariable=self.number_var, font=large_font).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(right_panel, text="Nombre:", font=large_font).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(right_panel, textvariable=self.name_var, font=large_font).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(right_panel, text="Ubicación:", font=large_font).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        sorted_locations = sorted(self.locations, key=lambda x: int(x))
        self.location_combobox = ttk.Combobox(right_panel, textvariable=self.location_var, font=large_font, values=sorted_locations, height=10, state="readonly")
        self.location_combobox.grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        self.location_combobox.configure(style='Large.TCombobox')

        style = ttk.Style()
        style.configure('Large.TCombobox', arrowsize=20, padding=5, font=('calibri', 14))  # Ajustar tamaño de fuente y padding
        style.map('Large.TCombobox', fieldbackground=[('readonly', 'white')])
        ttk.Label(right_panel, text="Quien Se La Lleva:", font=large_font).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(right_panel, textvariable=self.borrower_var, font=large_font).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        button_style = ttk.Style()
        button_style.configure('Large.TButton', font=('calibri', 16, 'bold'), padding=5)  # Reducir tamaño de fuente y padding
        ttk.Button(right_panel, text="Agregar/Actualizar Herramienta", command=self.add_or_update_tool, style='Large.TButton').grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Eliminar Herramienta", command=self.delete_tool, style='Large.TButton').grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Prestar Herramienta", command=self.lend_tool, style='Large.TButton').grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Devolver Herramienta", command=self.return_tool, style='Large.TButton').grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Buscar Herramienta", command=self.find_tool, style='Large.TButton').grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Añadir Ubicación", command=self.add_location, style='Large.TButton').grid(row=9, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Limpiar", command=self.clear_entries, style='Large.TButton').grid(row=10, column=0, columnspan=2, pady=10, sticky="ew")
        right_panel.grid_columnconfigure(1, weight=1)

    def add_or_update_tool(self):
        try:
            name = self.name_var.get()
            location = self.location_var.get()
            
            if not name or not location:
                raise ValueError("Nombre y ubicación no pueden estar vacíos")
            
            if self.current_tool:
                self.current_tool.name = name
                self.current_tool.location = location
            else:
                number = self.get_next_available_number()
                tool = GardenTool(number, name, location)
                self.inventory.append(tool)
            
            self.save_inventory()
            self.clear_entries()
            self.update_tool_list()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_tool(self):
        selected = self.tool_list.curselection()
        if selected:
            index = selected[0]
            tool_str = self.tool_list.get(index)
            tool_number = int(tool_str.split(":")[0])
            tool = next((t for t in self.inventory if t.number == tool_number), None)
            if tool:
                confirm = messagebox.askyesno("Confirmar Borrado", f"Estás seguro de que quieres borrar la herramienta {tool.number}: {tool.name}?")
                if confirm:
                    self.inventory.remove(tool)
                    self.save_inventory()
                    self.clear_entries()
                    self.update_tool_list()
            else:
                messagebox.showwarning("Advertencia", "No se pudo encontrar la herramienta seleccionada")
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta para borrar")

    def get_next_available_number(self):
        used_numbers = set(tool.number for tool in self.inventory)
        for i in range(1, len(self.inventory) + 2):
            if i not in used_numbers:
                return i

    def lend_tool(self):
        if self.current_tool:
            borrower = self.borrower_var.get()
            if borrower:
                self.current_tool.borrowed_by = borrower
                self.save_inventory()
            else:
                messagebox.showwarning("Advertencia", "Por favor, introduce el nombre de la persona que se lleva la herramienta")
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta")

    def return_tool(self):
        if self.current_tool:
            self.current_tool.borrowed_by = None
            self.borrower_var.set("")
            self.save_inventory()
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta")

    def find_tool(self):
        dialog = CustomDialog(self.root, "Buscar Herramienta", "Introduce el nombre o el número de la herramienta:")
        search_term = dialog.result
        if search_term:
            # Búsqueda por coincidencia parcial
            partial_matches = [tool for tool in self.inventory if search_term.lower() in tool.name.lower()]
            
            # Búsqueda por número exacto
            number_match = next((tool for tool in self.inventory if str(tool.number) == search_term), None)
            
            if number_match:
                partial_matches.insert(0, number_match)
            
            if partial_matches:
                if len(partial_matches) == 1:
                    self.select_tool(partial_matches[0])
                    self.update_location_image()
                    self.update_tool_list()
                else:
                    self.show_multiple_matches(partial_matches)
                return

            # Si no hay coincidencias parciales, buscar por similitud
            similar_matches = []
            for tool in self.inventory:
                ratio = difflib.SequenceMatcher(None, search_term.lower(), tool.name.lower()).ratio()
                if ratio > 0.5:  # Ajusta este umbral según sea necesario
                    similar_matches.append((tool, ratio))

            if similar_matches:
                similar_matches.sort(key=lambda x: x[1], reverse=True)
                self.show_multiple_matches([match[0] for match in similar_matches])
                return

            messagebox.showinfo("Herramienta no encontrada", f"No se ha encontrado ninguna herramienta similar a: {search_term}")

    def show_multiple_matches(self, matches):
        dialog = tk.Toplevel(self.root)
        dialog.title("Seleccionar Herramienta")
        dialog.geometry("400x500")

        label = ttk.Label(dialog, text="¿Qué herramienta quieres buscar exactamente?", font=('calibri', 14))
        label.pack(pady=10)

        listbox = tk.Listbox(dialog, font=('calibri', 14))
        listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        for tool in matches:
            listbox.insert(tk.END, f"{tool.number}: {tool.name}")

        def on_select(event=None):
            selection = listbox.curselection()
            if selection:
                selected_tool = matches[selection[0]]
                self.select_tool(selected_tool)
                self.update_location_image()
                self.update_tool_list()
                dialog.destroy()

        listbox.bind('<Double-1>', on_select)
        listbox.bind('<Return>', on_select)

        select_button = ttk.Button(dialog, text="Seleccionar", command=on_select)
        select_button.pack(pady=10)

        dialog.bind('<Return>', on_select)
        
    def select_tool(self, tool):
        self.current_tool = tool
        self.number_var.set(str(tool.number))
        self.name_var.set(tool.name)
        self.location_var.set(tool.location)
        self.borrower_var.set(tool.borrowed_by if tool.borrowed_by else "")

    def clear_entries(self):
        self.current_tool = None
        self.number_var.set("")
        self.name_var.set("")
        self.location_var.set("")
        self.borrower_var.set("")

    def save_inventory(self):
        with open("inventory.json", "w") as f:
            json.dump([tool.to_dict() for tool in self.inventory], f)

    def load_inventory(self):
        try:
            with open("inventory.json", "r") as f:
                data = json.load(f)
                self.inventory = [GardenTool.from_dict(item) for item in data]
        except FileNotFoundError:
            self.inventory = []

    def add_location(self):
        dialog = CustomDialog(self.root, "Añadir Ubicación", "Introduce el nombre de la nueva ubicación:")
        new_location = dialog.result
        if new_location and new_location not in self.locations:
            self.locations.append(new_location)
            sorted_locations = sorted(self.locations, key=lambda x: int(x))
            self.location_combobox['values'] = sorted_locations
            self.save_locations()
            self.link_image_to_location(new_location)

    def save_locations(self):
        with open("locations.json", "w") as f:
            json.dump(self.locations, f)

    def load_locations(self):   
        try:
            with open("locations.json", "r") as f:
                self.locations = json.load(f)
            sorted_locations = sorted(self.locations, key=lambda x: int(x))
            self.location_combobox['values'] = sorted_locations
        except FileNotFoundError:
            self.locations = []

    def link_image_to_location(self, location):
        if not self.images:
            messagebox.showwarning("Advertencia", "No hay imágenes disponibles para enlazar.")
            return

        dialog = ImageSelectionDialog(self.root, self.images)
        self.root.wait_window(dialog)
        
        if dialog.selected_image:
            self.location_images[location] = dialog.selected_image
            self.save_location_images()
        else:
            messagebox.showwarning("Advertencia", "No se seleccionó ninguna imagen.")

    def save_location_images(self):
        with open("location_images.json", "w") as f:
            json.dump(self.location_images, f)

    def load_location_images(self):
        try:
            with open("location_images.json", "r") as f:
                self.location_images = json.load(f)
        except FileNotFoundError:
            self.location_images = {}

    def load_images(self):
        self.images = [f for f in os.listdir() if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp'))]
        # Ordenar las imágenes numéricamente
        self.images.sort(key=lambda x: int(re.search(r'\d+', x).group()))
        if self.images:
            self.show_current_image()

    def show_current_image(self):
        if self.images:
            image = Image.open(self.images[self.current_page])
            
            # Rotate image based on EXIF data
            try:
                exif = image._getexif()
                if exif:
                    orientation = exif.get(274, 1)  # 274 is the orientation tag
                    if orientation == 3:
                        image = image.rotate(180, expand=True)
                    elif orientation == 6:
                        image = image.rotate(270, expand=True)
                    elif orientation == 8:
                        image = image.rotate(90, expand=True)
            except (AttributeError, KeyError, IndexError):
                # No EXIF data or orientation not found, proceed without rotation
                pass

            width, height = image.size
            new_height = 800  # Reducir la altura máxima de la imagen
            new_width = int(width * (new_height / height))
            image = image.resize((new_width, new_height), Image.LANCZOS)
            self.image_reference = ImageTk.PhotoImage(image)
            self.canvas.delete("all")
            self.canvas.config(width=new_width, height=new_height)
            self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_reference)
            self.update_tool_list()

    def next_image(self):
        if self.images:
            self.current_page = (self.current_page + 1) % len(self.images)
            self.show_current_image()

    def previous_image(self):
        if self.images:
            self.current_page = (self.current_page - 1) % len(self.images)
            self.show_current_image()

    def update_location_image(self):
        location = self.location_var.get()
        if location in self.location_images:
            image_file = self.location_images[location]
            try:
                image = Image.open(image_file)
                
                # Rotate image based on EXIF data
                try:
                    exif = image._getexif()
                    if exif:
                        orientation = exif.get(274, 1)  # 274 is the orientation tag
                        if orientation == 3:
                            image = image.rotate(180, expand=True)
                        elif orientation == 6:
                            image = image.rotate(270, expand=True)
                        elif orientation == 8:
                            image = image.rotate(90, expand=True)
                except (AttributeError, KeyError, IndexError):
                    # No EXIF data or orientation not found, proceed without rotation
                    pass

                width, height = image.size
                new_height = 800  # Reducir la altura máxima de la imagen
                new_width = int(width * (new_height / height))
                image = image.resize((new_width, new_height), Image.LANCZOS)
                self.image_reference = ImageTk.PhotoImage(image)
                self.canvas.delete("all")
                self.canvas.config(width=new_width, height=new_height)
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_reference)
                if image_file in self.images:
                    self.current_page = self.images.index(image_file)
                self.update_tool_list()
            except FileNotFoundError:
                messagebox.showwarning("Advertencia", f"No se pudo encontrar la imagen para la ubicación '{location}'")
        else:
            self.canvas.delete("all")
            self.canvas.create_text(200, 200, text="No hay imagen disponible para esta ubicación", font=('calibri', 14))
            self.update_tool_list()

    def update_tool_list(self):
        self.tool_list.delete(0, tk.END)
        current_image = self.images[self.current_page] if self.images else None
        for tool in self.inventory:
            if tool.location in self.location_images and self.location_images[tool.location] == current_image:
                self.tool_list.insert(tk.END, f"{tool.number}: {tool.name}")

    def on_tool_select(self, event):
        selected = self.tool_list.curselection()
        if selected:
            index = selected[0]
            tool_str = self.tool_list.get(index)
            tool_number = int(tool_str.split(":")[0])
            tool = next((t for t in self.inventory if t.number == tool_number), None)
            if tool:
                self.select_tool(tool)

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
