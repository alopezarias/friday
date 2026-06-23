# Skill: Stock de alimentos

Gestiona el inventario de alimentos que el usuario tiene en casa. Los datos viven en la tabla `alimentos` de `data/friday.db`.

## Schema

```sql
CREATE TABLE IF NOT EXISTS alimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    ubicacion TEXT,        -- 'nevera' | 'congelador' | 'estanteria'
    cantidad REAL,
    unidad TEXT,           -- 'g', 'ml', 'unidades', 'latas', etc.
    calorias REAL,         -- por 100g o 100ml
    proteinas REAL,        -- por 100g o 100ml
    carbohidratos REAL,    -- por 100g o 100ml
    grasas REAL,           -- por 100g o 100ml
    notas TEXT,
    actualizado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(nombre, ubicacion)
);
```

Crea la tabla si no existe antes de cualquier operación de escritura.

## Flujo al recibir una foto

1. Identifica todos los alimentos visibles en la imagen.
2. Si la ubicación no es obvia (no se ve si es nevera, congelador o estantería), pregunta.
3. Si la cantidad no es clara, pregunta. Si el usuario no lo sabe, deja NULL.
4. Haz upsert por `(nombre, ubicacion)`:

```python
import sqlite3, datetime
con = sqlite3.connect("data/friday.db")
con.execute("""
    INSERT INTO alimentos (nombre, ubicacion, cantidad, unidad, calorias, proteinas, carbohidratos, grasas, notas, actualizado_en)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(nombre, ubicacion) DO UPDATE SET
        cantidad=excluded.cantidad,
        unidad=excluded.unidad,
        calorias=excluded.calorias,
        proteinas=excluded.proteinas,
        carbohidratos=excluded.carbohidratos,
        grasas=excluded.grasas,
        notas=excluded.notas,
        actualizado_en=excluded.actualizado_en
""", (nombre, ubicacion, cantidad, unidad, calorias, proteinas, carbohidratos, grasas, notas, datetime.datetime.now().isoformat()))
con.commit()
con.close()
```

5. Confirma brevemente lo que guardaste: nombre, ubicación, cantidad.

## Macros

- Siempre por 100g o 100ml (estándar industria).
- Si el usuario da macros por porción, convierte antes de guardar.
- Si no conoce las macros, deja esos campos en NULL y continúa — no bloquees el flujo.

## Consultas

Responde con datos de la tabla cuando el usuario pregunte:
- qué tiene en casa / en la nevera / en el congelador
- cuánto queda de un alimento
- macros de un alimento
- cualquier pregunta sobre su stock

## Consistencia de nombres

El campo `nombre` debe ser estable y consistente (ej: siempre "pollo" no a veces "pechuga de pollo" y otras "pollo"). Las skills de recetas y lista de la compra harán JOIN por este campo.
