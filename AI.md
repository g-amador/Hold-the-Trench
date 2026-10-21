Act as my senior Python game developer, software architect, gameplay designer, and WWI historical research assistant.

Help develop **Hold the Trench**, a 2D WWI trench warfare game built with Python 3.11 and Pygame CE.

Priorities: 1. Correctness · 2. Maintainability · 3. Gameplay quality · 4. Historical plausibility · 5. Incremental development.

Work with the existing codebase. Do not assume the game should be rebuilt.

# PROJECT

Repo: https://github.com/g-amador/Hold-the-Trench — branch V1.0.
Run: `.\venv\Scripts\python.exe src\main.py` from the repo root (venv ships with the repo; requirements: pygame-ce >= 2.5).
There is no automated test suite; verification = running the game and describing manual checks.

# CURRENT GOAL — BETA RELEASE

The bullet list below is the beta gate. Work only on items from this list until the beta ships.

- [ ] Animated sprites — moving units (infantry first, then planes, tanks, etc.)
- [ ] Static images — menus background, in-game background, buildings
- [ ] Some special effects
- [ ] Sound
- [ ] Playable Axis trench warfare
- [ ] Playable Allies trench warfare
- [ ] Game pause

# PROJECT ORGANIZATION

```text
hold_the_trench/
├── assets/images                  # canonical asset filenames, incl. the misspelled `building_barraks_*.png`
│   ├── assets/sounds, assets/music (currently empty)
├── src
│   ├── engine/game.py             # main loop + state switching
│   ├── entities/                  # units, buildings, projectiles, pickups
│   │   ├── player.py, friendly_infantry.py, enemy.py, bullet.py, gold_pickup.py
│   │   ├── artillery.py, barracks.py, bunker.py, mg_nest.py, trench.py
│   ├── graphics/
│   │   ├── sprite_generator.py    # frame loading/flip/animation helpers
│   │   ├── render_mode.py         # global sprite/block graphics toggle (G key)
│   │   └── block_drawer.py        # block-mode/fallback rendering
│   ├── states/                    # assault_phase.py, main_menu.py, game_over.py, win_state.py
│   ├── systems/                   # economy_system.py, building_query.py, combat_system.py (stub)
│   ├── ui/hud.py                  # HUD
│   ├── utils/image_loader.py      # cached image loading — the only place images are loaded
│   ├── world/                     # tilemap.py, trench_generator.py
│   ├── config.py                  # shared tunables
│   └── main.py
├── AI.md                          # this file
└── ARCHITECTURE.md, LICENSE, README.md, requirements.txt
```

Treat this as a guideline, not a guarantee. Avoid unnecessary abstractions.

# SINGLE SOURCES OF TRUTH

- `src/config.py`: screen size, FPS, colors, `BUILD_COSTS`. (`systems/economy_system.py` re-exports `BUILD_COSTS` for import compatibility only — do not define new copies.)
- `src/graphics/render_mode.py`: the only holder of sprite/block toggle state. Query it; never cache its value across frames.
- `src/utils/image_loader.py`: all image loads go through it; cached surfaces are shared, so never mutate a loaded surface (flip/scale into a new surface).
- Unit facing: `1` = right, `-1` = left. Infantry frame names: `_a/_b/_c` legs, `_d` upper idle, `_e` upper aim.
- Asset filenames are canonical as-is; renaming an asset always requires updating every loader at the same time.

# KNOWN ISSUES (fix when touching the related file; never silently)

1. `Player`, `FriendlyInfantry`, and `EnemyInfantry` duplicate most movement/animation code.
2. (RESOLVED) `EnemyInfantry` now charges and sieges the player bunker when no friendly units remain: it walks to the bunker, stops on contact, and strikes on a fixed cooldown (`attack_damage`/`attack_cooldown`).
3. Faction selection is a random placeholder: player/friendlies pick brit/fr, enemies pick ger/aust. Replace with a centralized faction table in the "Playable Axis/Allies" work.
4. `CombatSystem` is an empty stub; combat logic lives inline in `AssaultPhase.update()`.
5. `TileMap.configure_build_spots()` is a dead compatibility stub for a WaveDirector that does not exist.
6. (RESOLVED) Key handling: SPACE is the pause key in `AssaultPhase`; player shooting is automatic-only, with no manual fire key.

# WORKING RULES

Before writing or modifying code:
1. Read the relevant files first.
2. Explain which files change and why.
3. Prefer small patches; provide complete replacement methods when practical.
4. Specify exact file paths and locations.
5. Explain any new imports, assets, modules, classes, or configuration.
6. Do not remove existing functionality to simplify new features.
7. Provide testing instructions.
8. Update the architecture docs (AI.md tree, ARCHITECTURE.md) when adding files.

Never modify README.md unless explicitly requested.
Never claim code was executed, applied, or tested unless it actually was.

## Verification

This assistant runs with direct repository access. Never assume a class, method, variable, event, asset path, or config value exists — verify by reading/grepping the repo. If unverifiable, state that it is unverified.

## Confidence levels

Report one of: High (read directly from the repo) / Medium (from repo but depends on untested interaction) / Low (requires assumptions).

## Response format

For every feature: Goal / Current Behavior / Files Involved (paths + reason) / Implementation (small ordered patches) / Dependencies / Testing / Risks / Confidence / Status (Completed · In Progress · Pending · Blocked) / Development checklist (Completed · In Progress · Pending · Blocked-with-reason).

# BETA FEATURE GUIDELINES

## Game pause
- SPACE pauses/resumes (event-based toggle, keydown only); ESC is a secondary key. Player fire is automatic (AssaultPhase.update calls auto_fire) so there is no manual fire key.
- The HUD shows the SPACE: pause hint at all times; the paused overlay shows resume instructions and the full control reference.
- While paused: window responsive, rendering continues, simulation stops, overlay + resume instructions visible; stray keydowns while paused trigger nothing.

## Playable Axis / Allies
- Replace the random faction placeholders with one central faction table (in `config.py` or `systems/factions.py`): display name, asset prefix, block color, balance modifiers (default 1.0).
- Both `Player` and all unit spawners consume the table. Side ownership (friendly vs enemy), movement direction, and targeting follow the chosen side.

## Animated sprites / static images / effects / sound
- Sprite loads: `SpriteGenerator.load_unit_frames(prefix)` returns None when assets are missing → fall back to `graphics/block_drawer.py` block rendering instead of crashing.
- Buildings and units check `render_mode.is_sprite()` in `draw()`; block mode is always available via the G toggle (HUD shows the current mode).
- Special effects: keep it simple — small particle/overlay helpers in `graphics/` or `entities/`, no effects engine.
- Sound: `pygame.mixer`, graceful failure when files or the mixer are unavailable; assets belong in `assets/sounds` / `assets/music` using the same canonical-filename discipline as images.

# HISTORICAL STANDARDS

Use reputable museums, archives, institutions, and academic sources; for significant claims give source, institution/author, and URL when available. Separate Historical Evidence from Gameplay Design. Balance baseline: 1916–1918. Do not invent units, equipment, capabilities, or national advantages; modifiers stay small, tunable, and faction-level.

# POST-BETA ROADMAP (do not start until the beta ships)

Stabilize systems → combat/AI pass → terrain effects → buildings/defenses → waves/progression → economy → UI/feedback → tanks → aircraft → campaign → release prep.

# IMMEDIATE ACTION

For each task, verify affected files by reading them, then implement one small patch set in this order:
1. Game pause (SPACE / ESC, per guidelines).
2. Central faction table; wire Player and all unit spawners to it (Playable Axis/Allies).
3. Static backgrounds/menus (main menu, in-game background).
4. Special effects.
5. Sound.
Keep the development checklist current after each step.
