# 🎖️ Hold the Trench

> **A single-player procedural WWI defense roguelite.**

Build trench networks, establish machine-gun nests, and hold the line against increasingly desperate enemy assaults.

Survive enough waves to secure victory, then decide:

**Will you continue to the next battlefield, or leave the front?**

---

## 📸 Overview

**Hold the Trench** is a session-based tactical defense game inspired by wave survival and procedural strategy games.

Each battle takes place on a **newly generated WWI battlefield**, forcing players to adapt their defenses, manage supplies, and make difficult tactical decisions.

---

## ✨ Features

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

---

## 🎮 Gameplay Loop

```text
Generate Battlefield
        ↓
Preparation Phase
(Build Defenses)
        ↓
Enemy Assaults
(Survive the Waves)
        ↓
Victory or Defeat
        ↓
Choose:
• Continue
• Generate New Scenario
• Quit to Menu
• Exit Game
```

---

## 🛡️ Buildable Defenses

| Structure                  | Purpose                            |
| -------------------------- | ---------------------------------- |
| 🕳️ Trench                 | Provides cover for troops          |
| 🔫 MG Nest                 | Suppresses and eliminates infantry |
| 💥 Artillery Position      | Delivers devastating area damage   |
| 🧱 Bunker                  | Durable defensive structure        |
| 📦 Supply Tent *(planned)* | Improves resource generation       |

---

## ⚔️ Enemy Types

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

---

## 🎯 Objective

Hold your position until all required enemy assaults have been defeated.

Each scenario has a **randomized number of waves**, ensuring that no two battles play exactly the same.

Victory grants you a choice:

* ▶️ Continue fighting
* 🔄 Generate a new battlefield
* 🏠 Return to the main menu
* ❌ Exit the game

---

## 🎮 Controls

### General

| Key           | Action           |
| ------------- | ---------------- |
| `ESC`         | Pause / Resume   |
| `Left Click`  | Build / Select   |

### Construction

| Key | Structure    |
| --- | ------------ |
| `1` | 🕳️ Trench   |
| `2` | 🔫 MG Nest   |
| `3` | 💥 Artillery |
| `4` | 🧱 Bunker    |

---

## 🗂️ Project Structure

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

---

## 🚀 Installation

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

---

## 🧭 Development Roadmap

### ✅ Prototype

* [x] Procedural scenarios
* [x] Wave-based assaults
* [x] Trench construction
* [x] Machine-gun nests
* [x] Pause and resume
* [x] Post-battle choices

### 🚧 In Development

* [ ] Artillery mechanics
* [ ] Dynamic weather effects
* [ ] Improved battlefield generation
* [ ] Additional enemy types
* [ ] Better visual effects
* [ ] Enhanced audio design

### 📌 Future Ideas

* [ ] Tanks
* [ ] Mortar teams
* [ ] New defensive structures
* [ ] Difficulty modifiers
* [ ] Steam achievements

---

## 🎨 Inspiration

While **Hold the Trench** aims to establish its own identity, it draws inspiration from:

* Tactical defense games
* Procedural roguelites
* Historical WWI trench warfare

---

## 📜 License

This project is currently under active development.

A license will be selected prior to public release.

---

### 🎖️ *"Hold the line. Survive the assault. Decide when your war ends."*
