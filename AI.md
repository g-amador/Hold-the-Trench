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
- [x] Playable Axis trench warfare — faction selection + faction-driven art/coins/screens
- [x] Playable Allies trench warfare — same system, opposite side
- [x] Game pause
- [x] Static images — menu/result screens done; the in-game mid-battle background art is still open

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
│   │   ├── (units store `self.nation` at ctor for faction art + coin drops)
│   ├── graphics/
│   │   ├── sprite_generator.py    # frame loading/flip/animation helpers
│   │   ├── render_mode.py         # global sprite/block graphics toggle (G key)
│   │   └── block_drawer.py        # block-mode/fallback rendering
│   ├── states/                    # assault_phase.py, main_menu.py, game_over.py, win_state.py
│   ├── systems/                   # factions.py, economy_system.py, building_query.py, combat_system.py (stub)
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

- `src/config.py`: screen size, FPS, colors, `BUILD_COSTS`, `BULLET_RANGE_PX` (max bullet flight; every engagement range must stay below it — player 300, infantry 200, MG 220, artillery 400). (`systems/economy_system.py` re-exports `BUILD_COSTS` for import compatibility only — do not define new copies.)
- `src/graphics/render_mode.py`: the only holder of sprite/block toggle state. Query it; never cache its value across frames.
- `src/utils/image_loader.py`: all image loads go through it; cached surfaces are shared, so never mutate a loaded surface (flip/scale into a new surface).
- Unit facing: `1` = right, `-1` = left. Infantry frame names: `_a/_b/_c` legs, `_d` upper idle, `_e` upper aim.
- Asset filenames are canonical as-is; renaming an asset always requires updating every loader at the same time.

# KNOWN ISSUES (fix when touching the related file; never silently)

1. `Player`, `FriendlyInfantry`, and `EnemyInfantry` duplicate most movement/animation code.
2. (RESOLVED) `EnemyInfantry` now charges and sieges the player bunker when no friendly units remain: it walks to the bunker, stops on contact, and strikes on a fixed cooldown (`attack_damage`/`attack_cooldown`).
3. (RESOLVED in `systems/factions.py`) Faction selection was a random placeholder; there is now one central faction table that the menu, both deployment sides, and every entity's art/coin choice consume. Remaining headroom (NOT bugs): faction balance modifiers (all 1.0 — table currently carries no modifier field) and per-faction unit rosters.
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

## Build prompt (near-spot cost ledger)
- `get_nearby_build_spot` only returns EMPTY player-purchasable spots (mg/barracks/artillery). Standing near enemy defenses, the player bunker, or any placed building shows NO prompt and no cost — the cost ledger (PAID/OWES/HAVE) appears only next to an empty player spot.

## HUD force counts panel
- Two columns under the top bar: player forces on the left, enemy on the right (right-aligned). One row each: Infantry / Barracks / MG Nest / Artillery.
- Shown ONLY while paused (rendered over the pause overlay); the live battle view stays clean. The battle state computes all rows (`AssaultPhase._collect_force_rows`); the HUD only renders.
- Player Infantry = live unit count. Player buildables show X/Y where Y = total build spots of that type on the map and X = spots holding a building (replaces the old mixed `count_buildings` legend).
- Enemy Infantry = live count; enemy buildings are placed free at battle start, so they show plain counts.

## Render layout (world vs HUD strip)
- `AssaultPhase.render` draws the world 1:1 onto a pre-allocated `world_surface` sized to the static map strip (`tilemap.width/height * TILE_SIZE`), then scales it to fit between `config.HUD_BAR_HEIGHT` and the screen bottom. The full battlefield is always visible below the HUD bar; no tile/unit is hidden by it.
- Movement limits come from the map itself: `Player._clamp_to_bounds(tilemap)` clamps x/y to the tilemap's pixel extents — there is no window-based or hardcoded bound (the old `max(40, ...)` HUD margin and `max_world_x` are gone). Map edges read as walls; the top row is reachable.
- HUD (top bar, build prompt, pause overlay, force panel) draws in screen space after the world blit.

## Playable Axis / Allies (IMPLEMENTED as `systems/factions.py`)
- The central faction table lives in `src/systems/factions.py` — the ONLY place faction/nation rules are defined. New art decisions must derive from it, never hardcode a nation.
- Table contents: `FACTIONS` (label + `unit_nations` + `building_nations` pools: allies = brit/fr, axis = ger/aust units, ger-only buildings — there are no austrian building assets), `COIN_BY_NATION` (aust shares coin_ger.png), `MENU_BACKGROUND`, `VICTORY_BACKGROUND`/`DEFEAT_BACKGROUND`, helpers `other()`, `unit_prefix()`, `building_filename()`, `coin_texture()`.
- Selection: `Game.selected_faction` (engine default "allies") is set by the main menu on ENTER; `AssaultPhase` stores `player_faction` and derives `enemy_faction = other(player_faction)`, then passes factions to the player, its buildings, the player bunker, the enemy defenses, and the player.
- Art rules: soldier textures roll a random nation from the side's unit pool at ctor time (unit remembers `self.nation`); building textures roll from the side's building pool per building (axis is always ger because the pool holds only ger).
- Coin drops: dying ENEMY units drop their nation's coin (`spawn_gold` passes `texture=self.coin`; missing coin art falls back to the gold square).
- Screens: main menu = `Menu_Start.jpeg`; victory/defeat art keyed by the played faction (victory shows your banner, defeat shows the enemy's).
- STILL OPEN (post-faction headroom): faction balance modifiers (planned all 1.0, table has no field yet) and per-faction unit rosters/selection (e.g. axis-only vehicle spawners).

## Faction screens & controls
- Main menu: `Menu_Start.jpeg` background; W/UP selects Allies, S/DOWN selects Axis (number shortcuts 1/2 work too; picked line bright, the other dimmed); ENTER starts the battle as the picked side; Q quits. The choice is promoted to `Game.selected_faction` only on ENTER.
- Battle end (win or lose): R = play again with the SAME faction, S = switch to the other faction, Q = quit. Both R and S rebuild a fresh `TileMap` before entering the new `AssaultPhase`, so no buildings or economy carry over.
- WinState/GameOverState select their own backgrounds from the faction table at construction time — no faction parameters are threaded through `change_state`.

## Animated sprites / static images / effects / sound
- Infantry animation contract (Player, FriendlyInfantry, EnemyInfantry — all three must behave identically): the leg run-cycle timer advances on every frame the unit moves (`is_moving`), and the weapon-raised aim pose is a per-volley blip raised inside `_fire()` on the actual pull (0.18 s) and drained by the shared per-frame update afterward — the pose is never pinned for as long as a target stays in cone. (This fixed the bug where the enemy hunt path returned before the animation block ran: frozen legs, permanent aim pose.)
- Sprite loads: `SpriteGenerator.load_unit_frames(prefix)` returns None when assets are missing → fall back to `graphics/block_drawer.py` block rendering instead of crashing.
- Buildings and units check `render_mode.is_sprite()` in `draw()`; block mode is always available via the G toggle (HUD shows the current mode).
- Special effects: keep it simple — small particle/overlay helpers in `graphics/` or `entities/`, no effects engine.
- Sound: `pygame.mixer`, graceful failure when files or the mixer are unavailable; assets belong in `assets/sounds` / `assets/music` using the same canonical-filename discipline as images.

# TODO — DOCUMENTED PLANS (NOT STARTED; do not code until the user asks)

These are held as documentation only. No implementation, stubs, or scaffolding yet.

## In-game static background (needs assets later)
- The mid-battle battlefield still draws tiles only; add a proper static background image for the assault state once a suitable asset exists.
- Load paths must go through `utils/image_loader.py`; keep it below the HUD bar per the render-layout rules, never crash on missing art.

# HISTORICAL STANDARDS

Use reputable museums, archives, institutions, and academic sources; for significant claims give source, institution/author, and URL when available. Separate Historical Evidence from Gameplay Design. Balance baseline: 1916–1918. Do not invent units, equipment, capabilities, or national advantages; modifiers stay small, tunable, and faction-level.

# POST-BETA ROADMAP (do not start until the beta ships)

Stabilize systems → combat/AI pass → terrain effects → buildings/defenses → waves/progression → economy → UI/feedback → tanks → aircraft → campaign → release prep.

# IMMEDIATE ACTION

For each task, verify affected files by reading them, then implement one small patch set in this order:
1. ~~Game pause (SPACE / ESC, per guidelines).~~ DONE.
2. ~~Central faction table; wire Player and all unit spawners to it (Playable Axis/Allies).~~ DONE — `systems/factions.py` + faction flow (menu selection, coins, screens, post-battle R/S).
3. Static in-game background (the only static-image item left; menus/result screens are done).
4. Special effects.
5. Sound.
Keep the development checklist current after each step.
