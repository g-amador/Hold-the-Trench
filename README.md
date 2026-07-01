# 🎖️ Hold the Trench

> **A single-player procedural WWI defense roguelite.**

Build trench networks, establish machine-gun nests, and hold the line against increasingly desperate enemy assaults.

Defeat all enemy assault waves to secure victory, then decide:

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

---

## 🛡️ Buildable Defenses

| Structure                  | Purpose                            |
| -------------------------- | ---------------------------------- |
| 🕳️ Trench                  | Basic defensive position           |
| 🔫 MG Nest                 | Anti-infantry fire support         |
| 🧱 Bunker                  | Durable defensive strongpoint      |
| 💥 Artillery Position      | Long-range bombardment             |
| 📦 Supply Tent *(planned)* | Resource generation                |

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
| `1` | 🕳️ Trench    |
| `2` | 🔫 MG Nest   |
| `3` | 🧱 Bunker    |
| `4` | 💥 Artillery |

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

## 🪖 How to Play

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

---

## 🔒 Running Hold the Trench in an Isolated Environment

Because Hold the Trench is a fully offline single-player game, it can easily be executed in isolated environments.

### Option 1: Python Virtual Environment (Recommended)

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

---

### Option 2: Docker Container

Create a Docker image:

```bash
docker build -t hold-the-trench .
```

Run the game:

```bash
docker run hold-the-trench
```

This keeps all dependencies isolated from the host operating system.

> Note:
> Running pygame applications inside Docker requires graphical display
> forwarding (X11, Wayland, WSLg, or similar technologies).
> For most players, a Python virtual environment or virtual machine is
> the simpler option.

---

### Option 3: Virtual Machine

For complete operating-system isolation, run Hold the Trench inside a virtual machine using:

* VirtualBox
* VMware
* Hyper-V
* KVM/QEMU

Install Python and the game normally inside the guest operating system.

---

### Option 4: Air-Gapped Systems

Hold the Trench requires no internet connection and can be played on:

* Disconnected computers
* Isolated networks
* Sandboxed environments
* Offline development workstations

---

## 🧭 Development Roadmap

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

### 🎖️ *"Hold the line. Defeat the assault. Decide when your war ends."*
