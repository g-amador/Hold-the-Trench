# 🎖️ Hold the Trench

> **A single-player procedural WWI defense roguelite.**

Build barracks, establish machine-gun nests, and deploy artillery positions to defend your territory against a continuous enemy assault.

Protect your bunker, manage your supplies, and destroy the enemy bunker to secure victory. Then decide:

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
8. [🗂️ Project Architecture](#project-architecture)
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

The animated .gif bellow illustrates running the current game alpha.
![Game Alpha](https://raw.githubusercontent.com/g-amador//Hold-the-Trench/main/assets/Hold-the-trench-alpha.gif)


[Back to Table of Contents](#toc)

---

## ✨ <a name="features">Features

* 🪖 **Single-player experience**
* 🌍 **Procedurally generated battlefields**
* 🕳️ **Procedurally generated trench networks**
* 🔫 **Deploy machine-gun nests**
* 💥 **Call in artillery support**
* 🧱 **Construct defensive bunkers**
* 🪖 **Recruit friendly infantry**
* 🏭 **Enemy barracks continuously spawn infantry**
* ⚔️ **Real-time infantry combat**
* 🪙 **Collect supplies from defeated enemies**
* 🎯 **Destroy the enemy bunker to win**
* 🌧️ **Random weather conditions**
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
Continuous Enemy Assault
(Enemy Barracks Spawn Infantry)
        ↓
Defend Your Bunker
(Eliminate Enemies and Collect Supplies)
        ↓
Destroy Enemy Bunker
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
| 🏭 Barracks                | Recruit or spawn infantry          |
| 🔫 MG Nest                 | Anti-infantry fire support         |
| 💥 Artillery Position      | Long-range bombardment             |

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

Your primary objective is to destroy the enemy bunker while protecting your own.

* 🏭 Enemy barracks continuously spawn enemy infantry.
* 🪖 Friendly infantry engage enemy troops with rifle fire at range and in close combat.
* 🔫 Machine-gun nests and artillery provide defensive fire support.
* 🪙 Defeated enemies can drop supplies that you can collect.
* 🧱 Build and maintain defenses to protect your bunker.

Victory: Destroy the enemy bunker.

Defeat: Lose your bunker.

Victory grants you a choice:

* ▶️ Continue fighting
* 🔄 Generate a new battlefield
* 🏠 Return to the main menu
* ❌ Exit the game

[Back to Table of Contents](#toc)

---

## 🎮 <a name="controls">Controls

### General

| Key           | Action                                  |
| ------------- | --------------------------------------- |
| `SPACE`       | Pause / Resume (primary)                |
| `ESC`         | Pause / Resume (secondary)              |
| `WASD` / Arrows | Move player                           |
| `Left Click`  | Build / Select                          |
| `G`           | Toggle sprite / block graphics mode     |
| `ENTER`       | Start battle (main menu)                |
| `R`           | Restart after victory or defeat         |
| `Q`           | Quit the game                           |

[Back to Table of Contents](#toc)

---

## 🗂️ <a name="project-architecture">Project Architecture

- `systems/` for combat, economy, faction rules, spawning, and wave management.
- `ui/` for HUD, menus, tooltips, and overlays.
- `config.py` 

```text
hold_the_trench/
├── assets/
├── src
│   ├── engine/
│   ├── entities/               # for units, buildings, projectiles, and pickups.
│   ├── graphics/               # for sprite generation, animation helpers, and rendering-related utilities where appropriate.
│   ├── states/                 # for menus, battles, victory, defeat, and other game screens.
│   ├── systems/                # for combat, economy, faction rules, spawning, and wave management.
│   ├── ui/                     # for HUD, menus, tooltips, and overlays.
│   ├── utils/
│   └── world/                  # for map generation, tiles, terrain, and battlefield configuration.
├── AI.md                       # Playbook for expanding the game
├── ARCHITECTURE.md             # Detailed project architecture & directory structure
├── LICENSE                     # License details
└── README.md                   # Main project documentation
```

For a complete, file-by-file breakdown of the repository, see [ARCHITECTURE.md](https://github.com/g-amador/Hold-the-Trench/blob/main/ARCHITECTURE.md).

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

Starting a new game creates a procedurally generated WWI battlefield and trenches with randomized terrain, weather conditions, and enemy strength.

No two battles are exactly alike.

### Step 2: Prepare Your Defenses

Use your available supplies to construct defensive positions, including:

* 🔫 Machine-gun nests
* 🧱 Bunkers
* 💥 Artillery positions

Friendly barracks can recruit infantry to help defend your position

### Step 3: Defend your position

Enemy barracks continuously spawn infantry. Enemy troops will engage your friendly infantry and advance toward your bunker when no friendly infantry remain.

Your machine-gun nests and artillery provide supporting fire against enemy infantry.

### Step 4: Collect Supplies

Defeated enemies can drop supplies. Collect them to help fund additional defenses.

### Step 5: Destroy the Enemy Bunker

Advance your defenses and eliminate enemy forces while protecting your own bunker.

Destroy the enemy bunker to win. If your bunker is destroyed, the battle is lost.

### Step 6: Decide Your Fate

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
py -3.11 -m venv venv
```

Activate the environment:

**Windows**

```bash
.\venv\Scripts\activate
```

**Linux/macOS**

```bash
source venv/bin/activate
```

Install dependencies:

```bash
(venv) pip install -r requirements.txt
```

Run the game:

```bash
(venv) python src/main.py
```

[Back to Table of Contents](#toc)

---

## 🧭 <a name="development-roadmap">Development Roadmap

### ✅ Vertical Slice V1

* [x] Machine-gun nests
* [x] Bunkers
* [x] Artillery positions
* [x] Continuous enemy infantry spawning
* [x] Enemy bunker destruction objective
* [x] Post-battle decisions
* [x] Victory and defeat states
* [x] Pause and resume

### 🚧 Planned Improvements

* [ ] Procedural scenarios
* [ ] Additional enemy types
* [ ] Better pathfinding
* [ ] Visual effects
* [ ] Sound effects
* [ ] Music
* [ ] Weather system
* [ ] Campaign progression
* [ ] Save/load support
* [ ] Gameplay balancing

### 📌 Future Features

* [ ] Tanks
* [ ] Cavalry
* [ ] Difficulty modifiers

### 📝 TODO (Planned — awaiting assets and design)

* [ ] Distinct victory and defeat screens — dedicated images for the win and game-over screens (currently both reuse the menu background)
* [ ] Faction selection on the main menu — choose **Axis or Allies** to start a battle instead of a plain "start game"
* [ ] Unit selection that follows the chosen faction (available units change per side)
* [ ] Post-battle faction choice — after a victory or defeat, play the same faction again or switch sides for the next battle

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

> Built with ❤️, Python, Pygame, a sprinkle of AI magic... and a determination to survive one more assault.
