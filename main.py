import tkinter as tk
from tkinter import ttk, messagebox, font, simpledialog
from PIL import Image, ImageTk
import json

class GardenTool:
    def __init__(self, number, name, location, page=0, borrowed_by=None):
        self.number = number
        self.name = name
        self.location = location
        self.page = page
        self.borrowed_by = borrowed_by

    def __str__(self):
        return f"{self.number}: {self.name}"

    def to_dict(self):
        return {
            "número": self.number,
            "nombre": self.name,
            "ubicación": self.location,
            "página": self.page,
            "quien_se_la_lleva": self.borrowed_by
        }

    @classmethod
    def from_dict(cls, data):
        key_map = {
            "número": "number",
            "nombre": "name",
            "ubicación": "location",
            "página": "page",
            "quien_se_la_lleva": "borrowed_by"
        }
        data = {key_map.get(k, k): v for k, v in data.items()}
        print(f"Debug: translated data - {data}")
        if "page" not in data:
            data["page"] = 0
        required_keys = ["number", "name", "location", "page", "borrowed_by"]
        for key in required_keys:
            if key not in data:
                raise KeyError(f"Missing required key: {key}")
        return cls(data["number"], data["name"], tuple(data["location"]), data["page"], data["borrowed_by"])

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

class MainApplication:
    def __init__(self, root):
        self.root = root
        self.root.title("Inventario de Herramientas")
        self.root.geometry("1024x600")

        self.inventory = []
        self.current_tool = None
        self.current_page = 0

        self.canvas = None
        self.image_reference = None

        self.create_widgets()
        self.load_inventory()

        if self.canvas:
            self.refresh_tool_markers()

        self.move_mode = False

    def create_widgets(self):
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        left_frame = ttk.Frame(self.root)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.canvas = tk.Canvas(left_frame)
        self.canvas.pack(expand=True, fill=tk.BOTH)
        self.update_page()

        right_frame = ttk.Frame(self.root)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.create_right_panel(right_frame)

        nav_frame = ttk.Frame(self.root)
        nav_frame.grid(row=1, column=0, columnspan=2, sticky="e", padx=10, pady=10)

        prev_button = ttk.Button(nav_frame, text="← Anterior", command=self.previous_page)
        prev_button.grid(row=0, column=0, padx=5)

        next_button = ttk.Button(nav_frame, text="Siguiente →", command=self.next_page)
        next_button.grid(row=0, column=1, padx=5)

    def load_image(self, page_index):
        workshop_image = Image.open(f"workshop_{page_index}.jpg")
        exif = workshop_image._getexif()
        if exif:
            orientation = exif.get(274)
            if orientation == 3:
                workshop_image = workshop_image.rotate(180, expand=True)
            elif orientation == 6:
                workshop_image = workshop_image.rotate(270, expand=True)
            elif orientation == 8:
                workshop_image = workshop_image.rotate(90, expand=True)

        desired_width = 512
        scale_factor = desired_width / workshop_image.width
        new_height = int(workshop_image.height * scale_factor)
        workshop_image = workshop_image.resize((desired_width, new_height), Image.Resampling.LANCZOS)

        self.scale_x = scale_factor
        self.scale_y = scale_factor

        return workshop_image

    def create_left_panel(self, page_index):
        workshop_image = self.load_image(page_index)
        self.image_reference = ImageTk.PhotoImage(workshop_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image_reference)
        self.canvas.image_reference = self.image_reference
        self.canvas.bind("<Button-1>", self.on_image_click)

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_page()

    def next_page(self):
        if self.current_page < 2:
            self.current_page += 1
            self.update_page()

    def update_page(self):
        self.canvas.delete("all")
        self.create_left_panel(self.current_page)
        self.refresh_tool_markers()

    def create_right_panel(self, parent):
        right_panel = ttk.Frame(parent)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=10, pady=10)

        self.number_var = tk.StringVar()
        self.name_var = tk.StringVar()
        self.location_var = tk.StringVar()
        self.borrower_var = tk.StringVar()
        large_font = font.Font(size=18)
        ttk.Label(right_panel, text="Número:", font=large_font).grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(right_panel, textvariable=self.number_var, font=large_font).grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(right_panel, text="Nombre:", font=large_font).grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(right_panel, textvariable=self.name_var, font=large_font).grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(right_panel, text="Ubicación:", font=large_font).grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Label(right_panel, textvariable=self.location_var, font=large_font).grid(row=2, column=1, padx=5, pady=5, sticky="ew")
        ttk.Label(right_panel, text="Quien Se La Lleva:", font=large_font).grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(right_panel, textvariable=self.borrower_var, font=large_font).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        
        button_style = ttk.Style()
        button_style.configure('TButton', font=('calibri', 24, 'bold'), padding=15)
        ttk.Button(right_panel, text="Agregar/Actualizar Herramienta", command=self.add_or_update_tool, style='TButton').grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Eliminar Herramienta", command=self.delete_tool, style='TButton').grid(row=5, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Prestar Herramienta", command=self.lend_tool, style='TButton').grid(row=6, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Devolver Herramienta", command=self.return_tool, style='TButton').grid(row=7, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Buscar Herramienta", command=self.find_tool, style='TButton').grid(row=8, column=0, columnspan=2, pady=10, sticky="ew")
        ttk.Button(right_panel, text="Limpiar", command=self.clear_entries, style='TButton').grid(row=10, column=0, columnspan=2, pady=10, sticky="ew")
        right_panel.grid_columnconfigure(1, weight=1)

    def on_image_click(self, event):
        self.clear_highlight()
        x = int(event.x / self.scale_x)
        y = int(event.y / self.scale_y)
        if self.move_mode and self.current_tool:
            self.current_tool.location = (x, y)
            self.current_tool.page = self.current_page
            self.location_var.set(f"({x}, {y})")
            self.refresh_tool_markers()
            self.move_mode = False
            self.save_inventory()
        elif not self.move_mode:
            self.location_var.set(f"({x}, {y})")

    def add_or_update_tool(self):
        try:
            number = int(self.number_var.get())
            name = self.name_var.get()
            location_str = self.location_var.get()
            
            if not name or not location_str:
                raise ValueError("Nombre y ubicación no pueden estar vacíos")
            
            location = tuple(map(int, location_str.strip('()').split(',')))

            if self.current_tool:
                self.current_tool.number = number
                self.current_tool.name = name
                self.current_tool.location = location
                self.current_tool.page = self.current_page
            else:
                tool = GardenTool(number, name, location, self.current_page)
                self.inventory.append(tool)
            
            self.refresh_tool_markers()
            self.save_inventory()
            self.clear_entries()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def delete_tool(self):
        if self.current_tool:
            confirm = messagebox.askyesno("Confirmar Borrado", f"Estás seguro de que quieres borrar la herramienta {self.current_tool.number}: {self.current_tool.name}?")
            if confirm:
                self.inventory.remove(self.current_tool)
                self.refresh_tool_markers()
                self.save_inventory()
                self.clear_entries()
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta para borrar")

    def lend_tool(self):
        if self.current_tool:
            borrower = self.borrower_var.get()
            if borrower:
                self.current_tool.borrowed_by = borrower
                self.refresh_tool_markers()
                self.save_inventory()
            else:
                messagebox.showwarning("Advertencia", "Por favor, introduce el nombre de la persona que se lleva la herramienta")
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta")

    def return_tool(self):
        if self.current_tool:
            self.current_tool.borrowed_by = None
            self.borrower_var.set("")
            self.refresh_tool_markers()
            self.save_inventory()
        else:
            messagebox.showwarning("Advertencia", "Por favor, selecciona una herramienta")

    def find_tool(self):
        self.clear_highlight()
        self.move_mode = False
        dialog = CustomDialog(self.root, "Buscar Herramienta", "Introduce el nombre o el número de la herramienta:")
        search_term = dialog.result
        if search_term:
            for tool in self.inventory:
                if str(tool.number) == search_term or tool.name.lower() == search_term.lower():
                    if tool.page != self.current_page:  # Cambia a la página de la herramienta si es diferente
                        self.current_page = tool.page
                        self.update_page()
                    self.select_tool(tool)
                    x, y = tool.location
                    x = int(x * self.scale_x)
                    y = int(y * self.scale_y)
                    self.canvas.create_oval(x-15, y-15, x+15, y+15, outline="yellow", width=5, tags="highlight")
                    return
            messagebox.showinfo("Herramienta no encontrada", f"No se ha encontrado ninguna herramienta con el nombre o número: {search_term}")

    def refresh_tool_markers(self):
        self.canvas.delete("tool_marker")
        for tool in self.inventory:
            if tool.location and tool.page == self.current_page:
                x = int(tool.location[0] * self.scale_x)
                y = int(tool.location[1] * self.scale_y)
                color = "red" if tool.borrowed_by else "green"
                self.canvas.create_oval(x-10, y-10, x+10, y+10, fill=color, tags=("tool_marker", f"tool_{tool.number}"))
                self.canvas.create_text(x, y-25, text=str(tool.number), font=('calibri', 14, 'bold'), tags=("tool_marker", f"tool_{tool.number}"))
        self.canvas.tag_bind("tool_marker", "<Button-1>", self.on_marker_click)

    def on_marker_click(self, event):
        self.clear_highlight()
        x, y = event.x, event.y
        items = self.canvas.find_overlapping(x-20, y-20, x+20, y+20)
        for item in items:
            tags = self.canvas.gettags(item)
            for tag in tags:
                if tag.startswith("tool_") and tag != "tool_marker":
                    try:
                        tool_number = int(tag.split("_")[1])
                        tool = next((t for t in self.inventory if t.number == tool_number), None)
                        if tool:
                            self.select_tool(tool)
                            x, y = tool.location
                            self.canvas.create_oval(x-15, y-15, x+15, y+15, outline="yellow", width=5, tags="highlight")
                            return
                    except ValueError:
                        continue
        self.clear_entries()

    def select_tool(self, tool):
        self.current_tool = tool
        self.number_var.set(str(tool.number))
        self.name_var.set(tool.name)
        self.location_var.set(f"({tool.location[0]}, {tool.location[1]})")
        self.borrower_var.set(tool.borrowed_by if tool.borrowed_by else "")

    def clear_entries(self):
        self.clear_highlight()
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

    def clear_highlight(self):
        self.canvas.delete("highlight")

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApplication(root)
    root.mainloop()
