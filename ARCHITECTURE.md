# 🗂️ Project Architecture

```text
hold_the_trench/
├── assets/
│   ├── images/                     # game art — NOT in the repo: download the free WW1 2D Assets Pack (gnpa, itch.io) and place it here; missing art falls back to block drawing
│   ├── sounds/
│   └── music/
├── src
│   ├── engine/
│   │   └── game.py
│   ├── entities/                   # for units, buildings, projectiles, and pickups
│   │   ├── artillery.py            # artillery building; art keyed by FACTION (allies artillery_fr / axis artillery_ger), GREY block fallback
│   │   ├── airplane.py             # factory-produced plane (air fields): flies, dive-shoots infantry in one straight pass then moves on, MGs planes, bombs tanks/buildings one target at a time; flies off the map when no targets remain
│   │   ├── barracks.py
│   │   ├── bullet.py
│   │   ├── bunker.py
│   │   ├── damage.py               # shared take_damage flavors: RawSubtractDamage / GuardedRawDamage (units) and FlooredDamage (buildings, friendly side)
│   │   ├── enemy.py
│   │   ├── friendly_infantry.py
│   │   ├── gold_pickup.py
│   │   ├── mg_nest.py
│   │   ├── player.py
│   │   ├── static_building.py      # free player-side statics: AirField (map 'F') / TankFactory (map 'K') — scene-variant art, 7x7 per config BUILD_FOOTPRINTS, spawn tanks/planes
│   │   └── tank.py                 # factory tanks (tank factories): committed 2D drive to the nearest opposing target, halt-and-shoot in gun range, building stand-off (never touch a building), armor damage rule
│   ├── graphics/                   # for sprite generation, animation helpers, rendering utilities, and the graphics toggle.
│   │   ├── sprite_generator.py     # unit frame loading/animation/flipping
│   │   ├── render_mode.py          # global SPRITES/BLOCKS graphics toggle state (G key)
│   │   └── block_drawer.py         # block-mode rendering used by the toggle and as missing-asset fallback
│   ├── states/                     # for menus, battles, victory, defeat, and other game screens.
│   │   ├── assault_phase.py
│   │   ├── end_screen.py           # shared EndScreenState base: R/S/Q restart flow, banner text, faction-keyed background
│   │   ├── game_over.py
│   │   ├── main_menu.py
│   │   └── win_state.py
│   ├── systems/                    # for combat, economy, and faction rules (shared pools/rolls live in factions.py).
│   │   ├── audio.py               # mixer wiring: looping menu music, the per-press select sting, national end themes (all no-op-safe without an audio device)
│   │   ├── building_query.py
│   │   ├── bullet_resolution.py    # unified per-direction bullet collision pass (units -> buildings/bunkers -> planes), called twice from the battle
│   │   ├── economy_system.py
│   │   └── factions.py             # single source of truth for sides: nation pools (single-nation right now — FR vs GER; future nations rejoin by widening the lists), coin art, menu/victory/defeat backgrounds, day/night scene rolling + ground fallback, and the other()/roll helpers
│   ├── ui/                         # for HUD, menus, tooltips, and overlays.
│   │   ├── hud.py
│   │   └── pause_overlay.py        # PAUSED panel: dim layer + centered text stack, built once per battle
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