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
│   │   ├── artillery.py            # artillery building; art keyed by FACTION (allies unit_cannon_fr / axis unit_heavy_howitzer_ger), GREY block fallback
│   │   ├── barracks.py
│   │   ├── bullet.py
│   │   ├── bunker.py
│   │   ├── enemy.py
│   │   ├── friendly_infantry.py
│   │   ├── gold_pickup.py
│   │   ├── mg_nest.py
│   │   ├── player.py
│   │   ├── static_building.py      # free player-side statics: AirField (map 'F') / TankFactory (map 'K') — scene-variant art, 3x3, no combat yet
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
│   │   ├── economy_system.py
│   │   └── factions.py             # single source of truth for sides: nation pools (units/buildings), coin art by nation, menu/victory/defeat backgrounds, and the other()/roll helpers
│   ├── ui/                         # for HUD, menus, tooltips, and overlays.
│   │   └── hud.py
│   ├── utils/
│   │   └── image_loader.py
│   ├── world/                      # for map generation, tiles, terrain, and battlefield configuration.
│   │   ├── tilemap.py              # tile grid + ground texture; draw(..., view_rect=None) culls ground/tiles/buildings/outlines to the CLOSE viewport
│   │   └── trench_generator.py     # ASCII battlefield; F = air field, K = tank factory (free statics), spots + build candidates
│   ├── config.py                   # for shared constants and carefully chosen global settings.
│   └── main.py
├── AI.md                           # Prompts for expanding the game
├── ARCHITECTURE.md                 # Detailed project architecture & directory structure
├── LICENSE                         # License details
├── README.md                       # Main project documentation
└── requirements.txt
```