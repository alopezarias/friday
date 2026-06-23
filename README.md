# F·R·I·D·A·Y

> *"Good morning. I've already reviewed your schedule, optimized your nutrition targets, and catalogued everything in your fridge. Shall we begin?"*

**Friday** is a personal AI agent that lives in your Telegram. It connects to a large language model via [openai-codex](https://github.com/openai/codex) and gives you a single, persistent chat interface to manage your life — from your fridge inventory to your weekly meal plan.

Think J.A.R.V.I.S., but running on your machine, with your data, talking the way you want it to talk.

---

## Why Friday?

Most AI assistants are stateless. Ask them something, get an answer, conversation ends — next time they've forgotten everything.

Friday is different:

- **Persistent memory** — everything lives in a local SQLite database. Friday remembers what you have in the fridge, your macros, your saved recipes, your shopping list.
- **Vision-capable** — send a photo of your fridge and Friday will catalogue the contents, ask what it can't figure out, and update the database.
- **Skill-based** — Friday's capabilities are defined in plain Markdown files. Drop a new `.md` into `skills/` and Friday knows how to do something new on the next restart.
- **Dependency-ordered skills** — skills are prefixed with a number (`1.`, `2.`, `3.`) reflecting their dependency level. Level 1 has no dependencies, level 2 builds on level 1, and so on. Friday always loads them in the right order.
- **Your personality, your rules** — edit `soul/FRIDAY.md` to shape how Friday talks and what it prioritizes.
- **Zero cloud dependency for your data** — your database and photos never leave your machine.

---

## Architecture

```
friday/
│
├── friday.py               # Bot core — Telegram ↔ Codex bridge
├── start.sh                # Process keeper (auto-restart on crash)
│
├── soul/
│   └── FRIDAY.md           # Agent identity, tone, hard limits
│
├── skills/                 # Capability definitions (loaded in order at startup)
│   ├── 1.sqlite.md         # DB access rules
│   ├── 1.stock.md          # Food inventory
│   ├── 2.recipes.md        # Recipe management (depends on stock)
│   ├── 2.shopping.md       # Shopping list (depends on stock + recipes)
│   └── 3.trainer.md        # Personal trainer — orchestrates everything
│
├── data/
│   ├── friday.db           # SQLite — the agent's persistent memory
│   └── photos/
│       └── recipes/        # Recipe photos (persisted locally)
│
├── .env                    # TELEGRAM_TOKEN, MODEL
└── requirements.txt
```

### How it works

```
Telegram message / photo
        │
        ▼
  friday.py handler
        │  (photos saved to data/photos/recipes/ before sending)
        ▼
  openai-codex thread  ←── soul/FRIDAY.md        (developer_instructions)
        │                └── skills/1.* 2.* 3.*  (base_instructions, ordered)
        │
        ▼
  LLM reasons + executes Python/SQL against data/friday.db
        │
        ▼
  Response streamed back to Telegram
```

The LLM has direct access to the filesystem (`cwd = project root`) and executes Python code to read/write SQLite. No hand-written ORM, no API wrappers — Friday uses the stdlib.

---

## Skills

Skills are Markdown files in `skills/`. Each one tells Friday what it can do, what the database schema looks like, and when to act. The numeric prefix defines load order and documents which skills depend on which.

---

### `1.sqlite.md` — Database access
The foundation. Defines the rules for reading and writing `data/friday.db`. Loaded first, always present. All other skills inherit these rules.

---

### `1.stock.md` — Food inventory

Send a photo of your fridge, freezer, or pantry shelf. Friday identifies every visible item, asks for location and quantity if unclear, and stores everything — including macros per 100g — in the `alimentos` table. Query it anytime:

> *"What do I have in the fridge?"*
> *"How much protein is in my current stock?"*
> *"Do I have eggs?"*

**Table:** `alimentos(id, nombre, ubicacion, cantidad, unidad, calorias, proteinas, carbohidratos, grasas, notas, actualizado_en)`

`ubicacion` values: `nevera` · `congelador` · `estanteria`

---

### `2.recipes.md` — Recipe management

Depends on: `1.stock`

Manages the personal recipe book. Friday can propose recipes based on what's in the fridge (and what could be bought within a budget), or save recipes you describe. Every saved recipe includes full ingredients with quantities, step-by-step instructions, macros per serving, and a photo.

**Photo rules:**
- You send a photo → saved to `data/photos/recipes/`
- Friday proposes a recipe → it fetches a representative image from the web automatically
- You can update any recipe's photo at any time: *"Update the photo for [recipe name]"*

> *"What can I make with what I have?"*
> *"Suggest something with chicken and rice, budget under €8"*
> *"Save this recipe"*
> *"Show me the recipe for pasta carbonara"*

**Tables:**
- `recetas(id, nombre, descripcion, instrucciones, porciones, tiempo_prep_min, calorias_porcion, proteinas_porcion, carbohidratos_porcion, grasas_porcion, foto_path, fuente, presupuesto_estimado, creado_en)`
- `receta_ingredientes(id, receta_id, nombre, cantidad, unidad)`

Recipes are only saved with explicit confirmation — Friday always asks before writing.

---

### `2.shopping.md` — Shopping list

Depends on: `1.stock` · `2.recipes`

Manages the shopping list with three states, designed for real-time use at the supermarket:

| State | Meaning | How to trigger |
|-------|---------|----------------|
| `pendiente` | On the list, not picked up yet | Default |
| `en_carrito` | Grabbed from the shelf, in the cart | *"I picked up the chicken"* / *"everything's in the cart"* |
| `comprado` | Paid, at home | *"Done, I've paid"* / *"all bought"* |

When items are marked as `comprado`, Friday asks whether to update the stock in `alimentos`.

> *"What do I need to buy?"*
> *"I picked up the eggs"*
> *"Mark everything as bought"*
> *"Add olive oil to the list"*
> *"Clear the bought items"*

**Table:** `lista_compra(id, nombre, cantidad_necesaria, cantidad_en_stock, cantidad_a_comprar, unidad, motivo, estado, creado_en)`

---

### `3.trainer.md` — Personal trainer

Depends on: `1.stock` · `2.recipes` · `2.shopping`

The orchestrator. Builds your nutritional profile, calculates your targets, plans weekly menus, keeps your stock in sync after meals, and generates shopping lists automatically.

**Methodology:** [Mifflin-St Jeor](https://en.wikipedia.org/wiki/Basal_metabolic_rate) for BMR · Mike Mentzer's Heavy Duty philosophy for caloric strategy · ISSN guidelines for macros.

**Nutritional profile:**
- Collects weight, height, age, sex, activity level, goal
- Calculates BMR → TDEE → daily caloric target → protein / carbs / fat breakdown
- Goals: `hipertrofia` · `definicion` · `mantenimiento` · `recomposicion`

**Menu planning:**
- Plans N days of meals hitting your daily targets (±5% calories, protein ≥ target)
- Prioritizes recipes that use existing stock
- Fills gaps with recipes requiring purchases
- Saves the plan to `menu_diario`
- Auto-generates the shopping list for missing ingredients

**Stock sync:**
When you tell Friday you've eaten a meal, it deducts the exact ingredient quantities from `alimentos` automatically.

> *"Plan my meals for the next 5 days"*
> *"How many calories should I eat today?"*
> *"I ate lunch"*
> *"Update my weight to 84kg"*
> *"Switch my goal to cutting"*

**Tables:**
- `perfil_usuario(id, peso_kg, altura_cm, edad, sexo, nivel_actividad, objetivo, tmb, tdee, calorias_objetivo, proteinas_g, carbohidratos_g, grasas_g, actualizado_en)`
- `menu_diario(id, fecha, tipo_comida, receta_id, nombre_libre, calorias, proteinas, carbohidratos, grasas, consumido)`

---

## Adding a new skill

1. Create `skills/N.your-skill.md` where `N` is the dependency level (1 = no deps, 2 = depends on level 1, etc.)
2. Describe: what Friday should do and when, the DB schema, any rules
3. Restart the bot

Done.

---

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo>
cd friday
pip install -r requirements.txt
```

### 2. Get a Telegram bot token

Talk to [@BotFather](https://t.me/BotFather) on Telegram → `/newbot` → copy the token.

### 3. Configure

```bash
cp .env.example .env
```

```env
TELEGRAM_TOKEN=your_token_here
MODEL=gpt-5.4
```

### 4. Run

```bash
./start.sh
```

The bot auto-restarts on crash. Open Telegram and start talking.

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | — | Required. From @BotFather. |
| `MODEL` | `gpt-5.4` | Codex model to use. |

---

## Customizing Friday's personality

Edit `soul/FRIDAY.md`. This file is loaded as `developer_instructions` — the highest-trust instruction channel. It defines who Friday is, how it speaks, and what it refuses to do.

Current defaults: concise, direct, no filler, no invented facts. If it doesn't know something, it says so.

---

## Roadmap

- [ ] **training.md** — log workouts, track volume, apply Mentzer HIT principles to recovery scheduling
- [ ] **journal.md** — daily notes and reflections, searchable
- [ ] **reminders.md** — scheduled nudges (drink water, meal time, check-in)

---

## Requirements

- Python 3.11+
- `openai-codex` — agentic LLM runtime
- `python-telegram-bot` — Telegram interface
- `python-dotenv` — environment config

---

<p align="center">
  <i>Built with <a href="https://github.com/openai/codex">openai-codex</a> · Runs on Telegram · Data stays local</i>
</p>
