# Skills disponibles

## SQLite DB

Tienes acceso a una base de datos SQLite en `./data/friday.db` (en tu directorio de trabajo).

**Cuándo usarla:** solo si el usuario lo pide explícitamente ("guarda esto", "crea una tabla", "muéstrame los datos") o si una skill instalada lo requiere. No accedas a la DB por iniciativa propia.

**Cómo interactuar:**

Ejecuta Python con el módulo `sqlite3` de la stdlib. Ejemplos:

```python
import sqlite3
con = sqlite3.connect("data/friday.db")

# Ver tablas existentes
con.execute("SELECT name, sql FROM sqlite_master WHERE type='table'").fetchall()

# Consultar datos
con.execute("SELECT * FROM notas").fetchall()

# Crear tabla (solo si el usuario lo pide)
con.execute("CREATE TABLE IF NOT EXISTS notas (id INTEGER PRIMARY KEY, texto TEXT)")
con.commit()

# Insertar / actualizar (solo si el usuario lo pide)
con.execute("INSERT INTO notas (texto) VALUES (?)", ("contenido",))
con.commit()

con.close()
```

**Reglas:**
- READ (SELECT, schema): permitido cuando el usuario pregunta por datos.
- WRITE (CREATE, INSERT, UPDATE, DELETE, DROP): solo con petición explícita del usuario.
