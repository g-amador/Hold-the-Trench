# 🗂️ Project Architecture

```text
hold_the_trench/
├── assets/
│   ├── images/
│   ├── sounds/
│   └── music/
├── src
│   ├── engine/
│   │   └── game.py
│   ├── entities/                   # for units, buildings, projectiles, and pickups
│   │   ├── artillery.py
│   │   ├── barracks.py
│   │   ├── bullet.py
│   │   ├── bunker.py
│   │   ├── enemy.py
│   │   ├── friendly_infantry.py
│   │   ├── gold_pickup.py
│   │   ├── mg_nest.py
│   │   ├── player.py
│   │   └── trench.py
│   ├── graphics/                   # for sprite generation, animation helpers, rendering utilities, and the graphics toggle.
│   │   ├── sprite_generator.py                  # unit frame loading/animation/flipping
│   │   ├── render_mode.py                        # global SPRITES/BLOCKS graphics toggle state (G key)
│   │   └── block_drawer.py                       # block-mode rendering used by the toggle and as missing-asset fallback
│   ├── states/                     # for menus, battles, victory, defeat, and other game screens.
│   │   ├── assault_phase.py
│   │   ├── game_over.py
│   │   ├── main_menu.py
│   │   └── win_state.py
│   ├── systems/                    # for combat, economy, faction rules, spawning, and wave management.
│   │   ├── building_query.py
│   │   ├── combat_system.py
│   │   └── economy_system.py
│   ├── ui/                         # for HUD, menus, tooltips, and overlays.
│   │   └── hud.py
│   ├── utils/
│   │   └── image_loader.py
│   ├── world/                      # for map generation, tiles, terrain, and battlefield configuration.
│   │   ├── tilemap.py
│   │   └── trench_generator.py
│   ├── config.py                   # for shared constants and carefully chosen global settings.
│   └── main.py
├── AI.md                           # Prompts for expanding the game
├── ARCHITECTURE.md                 # Detailed project architecture & directory structure
├── LICENSE                         # License details
├── README.md                       # Main project documentation
└── requirements.txt
```