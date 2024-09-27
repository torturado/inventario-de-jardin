# Changelog

### Añadido
- Importación del módulo `difflib` para búsquedas por similitud.
- Función `show_multiple_matches()` para mostrar múltiples resultados de búsqueda.
- Búsqueda por coincidencia parcial en nombres de herramientas.
- Búsqueda por número exacto de herramienta.
- Búsqueda por similitud cuando no hay coincidencias exactas o parciales.
- Ventana de selección para múltiples coincidencias en la búsqueda.
- Doble clic y tecla Enter para seleccionar herramienta en la ventana de múltiples coincidencias.

### Modificado
- Función `find_tool()` mejorada para manejar múltiples tipos de búsqueda.
- Inicialización de la ventana principal para que se abra maximizada (`self.root.state('zoomed')`).
- Tamaño de la ventana de selección de herramientas aumentado a 400x500.
- Tamaño de fuente en la lista de selección de herramientas aumentado a 14.

### Optimizado
- Lógica de búsqueda para priorizar coincidencias exactas, luego parciales y finalmente por similitud.

### UI/UX
- Mejora en la presentación de resultados de búsqueda múltiple.
- Interacción más intuitiva en la selección de herramientas (doble clic, Enter).
