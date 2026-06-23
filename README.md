# F·R·I·D·A·Y

> *"Good morning. I've already reviewed your schedule, optimized your nutrition targets, and catalogued everything in your fridge. Shall we begin?"*

**Friday** is a personal AI agent that lives in your Telegram. It connects to a large language model via [openai-codex](https://github.com/openai/codex) and gives you a single, persistent chat interface to manage your life — from your fridge inventory to your training plan.

Think J.A.R.V.I.S., but running on your machine, with your data, talking the way you want it to talk.

---

## Why Friday?

Most AI assistants are stateless. Ask them something, get an answer, conversation ends — next time they've forgotten everything.

Friday is different:

- **Persistent memory** — everything lives in a local SQLite database. Friday remembers what you have in the fridge, your macros, your goals.
- **Vision-capable** — send a photo of your fridge and Friday will catalogue the contents, ask what it can't figure out, and update the database.
- **Skill-based** — Friday's capabilities are defined in plain Markdown files. Drop a new `.md` into `skills/` and Friday knows how to do something new on the next restart.
- **Your personality, your rules** — edit `soul/FRIDAY.md` to shape how Friday talks and what it prioritizes.
- **Zero cloud dependency for your data** — your database never leaves your machine.

---

## Architecture

```
friday/
│
├── friday.py           # Bot core — Telegram ↔ Codex bridge
├── start.sh            # Process keeper (auto-restart on crash)
│
├── soul/
│   └── FRIDAY.md       # Agent identity, tone, hard limits
│
├── skills/             # Capability definitions (loaded at startup)
│   ├── sqlite.md       # DB access rules — always loaded first
│   ├── stock.md        # Food inventory management
│   └── trainer.md      # Personal trainer & nutrition
│
├── data/
│   └── friday.db       # SQLite — the agent's persistent memory
│
├── .env                # TELEGRAM_TOKEN, MODEL
└── requirements.txt
```

### How it works

```
Telegram message / photo
        │
        ▼
  friday.py handler
        │
        ▼
  openai-codex thread  ←── soul/FRIDAY.md  (developer_instructions)
        │                └── skills/*.md   (base_instructions)
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

Skills are Markdown files in `skills/`. Each one tells Friday what it can do, what the database schema looks like, and when to act.

### `sqlite.md` — Database access
The foundation. Defines the rules for reading and writing `data/friday.db`. Loaded first, always present.

### `stock.md` — Food inventory
Send a photo of your fridge, freezer, or pantry shelf. Friday identifies every visible item, asks for location and quantity if unclear, and stores everything — including macros per 100g — in the `alimentos` table. Query it anytime:

> *"What do I have in the fridge?"*
> *"How much protein is in my current stock?"*
> *"Do I have eggs?"*

Schema: `alimentos(id, nombre, ubicacion, cantidad, unidad, calorias, proteinas, carbohidratos, grasas, notas, actualizado_en)`

### `trainer.md` — Personal trainer
Builds your nutritional profile using the **Mifflin-St Jeor** formula for BMR and the **Mike Mentzer Heavy Duty** philosophy as a training reference. First time you mention nutrition, Friday will ask for your stats and set up your targets.

> *"How many calories should I eat today?"*
> *"I want to start a cut."*
> *"Update my weight to 84kg."*

Schema: `perfil_usuario(id, peso_kg, altura_cm, edad, sexo, nivel_actividad, objetivo, tmb, tdee, calorias_objetivo, proteinas_g, carbohidratos_g, grasas_g, actualizado_en)`

### Adding a new skill

Create `skills/your-skill.md` describing:
- What Friday should do and when
- The database schema (table name, columns, types)
- Any rules or constraints

Restart the bot. Done.

---

## Quickstart

### 1. Clone and install

```bash
git clone <your-repo>
cd friday
pip install -r requirements.txt
```

### 2. Get a Telegram bot token

Talk to [@BotFather](https://t.me/BotFather) on Telegram:
```
/newbot
```
Copy the token it gives you.

### 3. Configure

```bash
cp .env.example .env   # or create .env manually
```

```env
TELEGRAM_TOKEN=your_token_here
MODEL=gpt-5.4
```

### 4. Run

```bash
./start.sh
```

The bot will auto-restart if it crashes. Open Telegram and start talking.

---

## Configuration

| Variable         | Default    | Description                                      |
|-----------------|------------|--------------------------------------------------|
| `TELEGRAM_TOKEN` | —          | Required. From @BotFather.                      |
| `MODEL`          | `gpt-5.4`  | Codex model to use.                             |

---

## Customizing Friday's personality

Edit `soul/FRIDAY.md`. This file is loaded as `developer_instructions` — the highest-trust instruction channel. It defines who Friday is, how it speaks, and what it refuses to do. The current default: concise, direct, no filler, no invented facts. If it doesn't know something, it says so.

---

## Roadmap

Skills planned or in progress:

- [ ] **recipes.md** — suggest recipes based on current stock
- [ ] **shopping.md** — generate a shopping list based on missing ingredients and nutritional goals
- [ ] **training.md** — log workouts, track volume, apply Mentzer HIT principles
- [ ] **journal.md** — daily notes and reflections, searchable

---

## Requirements

- Python 3.11+
- `openai-codex` — agentic LLM runtime
- `python-telegram-bot` — Telegram interface
- `python-dotenv` — environment config

---

## License

MIT — do whatever you want with it.

---

<p align="center">
  <i>Built with <a href="https://github.com/openai/codex">openai-codex</a> · Runs on Telegram · Data stays local</i>
</p>
