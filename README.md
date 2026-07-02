# 🎖️ Hold the Trench

> **A single-player procedural WWI defense roguelite.**

Build trench networks, establish machine-gun nests, and hold the line against increasingly desperate enemy assaults.

Defeat all enemy assault waves to secure victory, then decide:

**Will you continue to the next battlefield, or leave the front?**

---

## 📑 <a name="toc">Table of Contents

1. [📸 Overview](#overview)
2. [✨ Features](#features)
3. [🎮 Gameplay Loop](#gameplay-loop)
4. [🛡️ Buildable Defenses](#buildable-defenses)
5. [⚔️ Enemy Types](#enemy-types)
6. [🎯 Objectives](#objectives)
7. [🎮 Controls](#controls)
8. [🗂️ Project Structure](#project-structure)
9. [🚀 Installation](#installation)
10. [🪖 How to Play](#how-to-play)
11. [🔒 Running in an Isolated Environment](#isolated-environment)
12. [🧭 Development Roadmap](#development-roadmap)
13. [🎨 Inspiration](#inspiration)
14. [📬 License, Usage & Contact](#contact)

---

## 📸 <a name="overview">Overview

**Hold the Trench** is a session-based tactical defense game inspired by wave survival and procedural strategy games.

Each battle takes place on a **newly generated WWI battlefield**, forcing players to adapt their defenses, manage supplies, and make difficult tactical decisions.

[Back to Table of Contents](#toc)

---

## ✨ <a name="features">Features

* 🪖 **Single-player experience**
* 🌍 **Procedurally generated battlefields**
* 🕳️ **Build and expand trench networks**
* 🔫 **Deploy machine-gun nests**
* 💥 **Call in artillery support**
* 🧱 **Construct defensive bunkers**
* 🧠 **Enemy pathfinding and tactical assaults**
* 🌧️ **Random weather conditions**
* 📈 **Escalating wave difficulty**
* ⏸️ **Pause and resume at any time**
* 🔄 **Generate a new defense scenario after each victory**
* 🚪 **Choose to continue fighting or leave after each completed level**

[Back to Table of Contents](#toc)

---

## 🎮 <a name="gameplay-loop">Gameplay Loop

```text
Generate Battlefield
        ↓
Preparation Phase
(Build Defenses)
        ↓
Enemy Assaults
(Defeat All Waves)
        ↓
Victory or Defeat
        ↓
Choose:
• Continue
• Generate New Scenario
• Quit to Menu
• Exit Game
```

[Back to Table of Contents](#toc)

---

## 🛡️ <a name="buildable-defenses">Buildable Defenses

| Structure                  | Purpose                            |
| -------------------------- | ---------------------------------- |
| 🕳️ Trench                  | Basic defensive position           |
| 🔫 MG Nest                 | Anti-infantry fire support         |
| 🧱 Bunker                  | Durable defensive strongpoint      |
| 💥 Artillery Position      | Long-range bombardment             |
| 📦 Supply Tent *(planned)* | Resource generation                |

[Back to Table of Contents](#toc)

---

## ⚔️ <a name="enemy-types">Enemy Types

### Current

| Enemy | Description |
|--------|-------------|
| 🚶 Infantry | Standard assault troops |

### Planned

| Enemy | Description |
|--------|-------------|
| ⚡ Shock Troopers | Fast assault infantry |
| 🔥 Flamethrowers | Anti-entrenchment troops |
| 🎯 Mortar Teams | Indirect fire support |
| 🚜 Tanks | Armored breakthrough units |

[Back to Table of Contents](#toc)

---

## 🎯 <a name="objectives">Objectives

Hold your position until all required enemy assaults have been defeated.

Each scenario has a **randomized number of waves**, ensuring that no two battles play exactly the same.

Victory grants you a choice:

* ▶️ Continue fighting
* 🔄 Generate a new battlefield
* 🏠 Return to the main menu
* ❌ Exit the game

---

## 🎮 <a name="controls">Controls

### General

| Key           | Action           |
| ------------- | ---------------- |
| `ESC`         | Pause / Resume   |
| `Left Click`  | Build / Select   |

### Construction

| Key | Structure    |
| --- | ------------ |
| `1` | 🕳️ Trench    |
| `2` | 🔫 MG Nest   |
| `3` | 🧱 Bunker    |
| `4` | 💥 Artillery |

[Back to Table of Contents](#toc)

---

## 🗂️ <a name="project-structure">Project Structure

```text
hold_the_trench/
│
├── main.py
├── config.py
├── requirements.txt
├── README.md
│
├── assets/
│   ├── images/
│   ├── sounds/
│   └── music/
│
├── engine/
│   ├── game.py
│   ├── renderer.py
│   └── asset_manager.py
│
├── states/
│   ├── main_menu.py
│   ├── prep_phase.py
│   ├── assault_phase.py
│   ├── post_battle_state.py
│   └── game_over_state.py
│
├── systems/
│   ├── economy_system.py
│   ├── building_system.py
│   ├── building_query.py
│   ├── combat_system.py
│   ├── wave_director.py
│   ├── scenario_generator.py
│   ├── pathfinding.py
│   ├── progression_system.py
│   ├── weather_system.py
│   └── save_system.py
│
├── entities/
│   ├── enemy.py
│   ├── trench.py
│   ├── mg_nest.py
│   ├── bunker.py
│   └── artillery.py
│
├── world/
│   ├── map_generator.py
│   ├── tile.py
│   └── tilemap.py
│
│
└── saves/
```

[Back to Table of Contents](#toc)

---

## 🚀 <a name="installation">Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/hold-the-trench.git
cd hold-the-trench
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Launch the game

```bash
python main.py
```

[Back to Table of Contents](#toc)

---

## 🪖 <a name="how-to-play">How to Play

### Step 1: Generate a Battlefield

Starting a new game creates a procedurally generated WWI battlefield with randomized terrain, weather conditions, enemy strength, and assault duration.

No two battles are exactly alike.

### Step 2: Prepare Your Defenses

During the preparation phase, use your available supplies to construct defensive positions:

* 🕳️ Trench networks
* 🔫 Machine-gun nests
* 🧱 Bunkers
* 💥 Artillery positions

Careful planning is essential, as supplies are limited.

### Step 3: Begin the Assault

Once your defenses are ready, the enemy assault begins.

Enemy forces attack in multiple waves while your defensive structures automatically engage hostile units.

### Step 4: Hold the Line

Defeat all enemy assault waves to achieve victory.

If your defenses collapse and the battlefield is overrun, the battle is lost.

### Step 5: Decide Your Fate

After each successful defense, you may choose to:

* ▶️ Continue fighting
* 🔄 Generate a new battlefield
* 🏠 Return to the main menu
* ❌ Exit the game

Every new battlefield is procedurally generated, creating a unique campaign experience each time.

[Back to Table of Contents](#toc)

---

## 🔒 <a name="isolated-environment">Running Hold the Trench in an Isolated Environment

Because Hold the Trench is a fully offline single-player game, it can easily be executed in a Python Virtual Environment.

Create an isolated Python environment:

```bash
python -m venv venv
```

Activate the environment:

**Windows**

```bash
venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the game:

```bash
python main.py
```

[Back to Table of Contents](#toc)

---

## 🧭 <a name="development-roadmap">Development Roadmap

### ✅ Vertical Slice V1

* [x] Procedural scenarios
* [x] Wave-based assaults
* [x] Trench construction
* [x] Machine-gun nests
* [x] Bunkers
* [x] Artillery positions
* [x] Weather system
* [x] Campaign progression
* [x] Save/load support
* [x] Pause and resume
* [x] Post-battle decisions
* [x] Victory and defeat states

### 🚧 Planned Improvements

* [ ] Additional enemy types
* [ ] Improved battlefield generation
* [ ] Better pathfinding
* [ ] Visual effects
* [ ] Sound effects
* [ ] Music
* [ ] Gameplay balancing

### 📌 Future Features

* [ ] Tanks
* [ ] Mortar teams
* [ ] Supply tents
* [ ] Difficulty modifiers
* [ ] Steam achievements

[Back to Table of Contents](#toc)

---

## 🎨 <a name="inspiration">Inspiration

While **Hold the Trench** aims to establish its own identity, it draws inspiration from:

* Tactical defense games
* Procedural roguelites
* Historical WWI trench warfare

[Back to Table of Contents](#toc)

---

## 📬 <a name="contact">License, Usage & Contact

Hold the Trench is released under the MIT License, which allows you to freely use, modify, distribute, and build upon the project, including creating your own scenarios, game modes, assets, tools, ports, or derivative works.

You may not claim authorship of Hold the Trench or misrepresent modified versions as the original project.

For full legal details, refer to the **[LICENSE](https://github.com/g-amador/Hold-the-Trench/blob/main/LICENSE)** file included with this repository.

If you have questions, suggestions, bug reports, or wish to share your own battlefield stories and modifications, feel free to get in touch:

📧 **[g.n.p.amador@gmail.com](mailto:g.n.p.amador@gmail.com)**

Good luck, Commander, and hold the line.

[Back to Table of Contents](#toc)

---

> Built with ❤️, Python, Pygame, a sprinkle of Copilot magic... and a determination to survive one more assault.
