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
- [x] Static images — menu/result backgrounds + the in-game ground floor texture (map.png, G-bound) done; artillery building art still open
- [ ] Some special effects
- [ ] Sound
- [x] Playable Axis trench warfare — faction selection + faction-driven art/coins/screens
- [x] Playable Allies trench warfare — same system, opposite side
- [x] Game pause
- [x] Static images — menu/result screens + in-game ground floor texture (map.png) done

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

- `src/config.py`: screen size, FPS, colors, `BUILD_COSTS`, `BUILD_FOOTPRINTS` (tiles per building kind; MG = 4x4, anchor = marker tile = footprint top-left; others 1x1 until the MG pass is signed off, target 3x3), `BULLET_RANGE_PX` (max bullet flight; every engagement range must stay below it — player 300, infantry 200, MG 220, artillery 400). (`systems/economy_system.py` re-exports `BUILD_COSTS` for import compatibility only — do not define new copies.)
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

## Battle scene variants for building art (a/b/c/d)
- One scene is rolled ONCE PER BATTLE (`factions.roll_scene()` at `AssaultPhase.__init__`) touching everything scene-linked in it; suffix letters: a = summer day, b = summer night, c = winter day, d = winter night.
- ACTIVE POOL = `SCENE_VARIANTS = ("a", "c")` per user request: only the art-complete letters roll (a/c have full map + MG nest + bunker art). b/d rejoin the tuple when their art lands. TEST MODE is OFF (`SCENE_VARIANT_TEST = None`, random roll active); set it to "a"/"c" to pin the roll for artwork debugging.
- ONE LETTER FOR THE WHOLE BATTLEFIELD ("If _a then all 3 must be _a"): the roll also drives the GROUND — `factions.ground_texture_filename()` -> `map1<letter>.jpeg`, and `AssaultPhase.__init__` calls `tilemap.reload_ground()` right after `roll_scene()` (the menu builds the TileMap BEFORE the battle rolls, so the rebinding in battle init is what keeps ground == buildings; never load the ground texture construction-time-only).
- Loading goes through the fallback chain `building_variant_filenames()` (factions.py) + `utils/image_loader.load_first_image()`: scene-suffix file -> `_a` file -> unsuffixed base art — buildings without their variant images silently keep summer-day art, never crash (a silent fallback breaks scene purity only for kinds still missing their variant art).
- WIRED: MG nest, bunker, and barracks all load via the chain (`building_variant_filenames` + `load_first_image`, None-art falls back to block drawing). Barracks art/block scale with its 4x4 footprint. Artillery art is keyed by FACTION, not nation/scene (`factions.ARTILLERY_IMAGE`: allies = `unit_cannon_fr.png`, axis = `unit_heavy_howitzer_ger.png`; no scene suffixes for these unit images) and is table-driven like the others: 4x2 footprint (user), art scaled to it (128x64), fire origin = FOOTPRINT CENTER (MG rule, not the marker tile), BLOCK mode = grey block over the full footprint with facing marker, and `footprint_tiles` present for viewport culling. Air field and tank factory (statics) ride the scene chain and DO vary a/c with the scene roll. NOTE: assets must follow the suffix scheme; a building whose base AND `_a` file are missing renders as a block.

## Building footprints (TEST STEP: MG 4x4; target: everything 3x3)
- `config.BUILD_FOOTPRINTS` is the tile-count table; the map marker is the footprint's TOP-LEFT tile (grows right + down). USER SIZES: barracks = 4x4, MG = 4x4; artillery = 4x2; bunker = 6x6; air_field/tank_factory = 7x7. The user hand-edits this table (and BUILD_COSTS — re-read before assuming). ZERO-COST = AUTO-PLACE (user): any purchasable spot whose BUILD_COSTS entry is 0 is built at battle start in `AssaultPhase.place_zero_cost_buildings` — no gold, no prompt, no contact, same first-marker-wins rule as the marker placements. Currently ALL player costs are 0 (everything auto-builds); nonzero costs keep the walk-to-spot touch-and-pay path (`auto_place_if_possible`). My verifies pin prices locally where payment/empty-spot behavior must be exercised.
- Rendering: `TileMap.draw` paints the whole tile grid FIRST, every building AFTER (`_draw_buildings`, both graphics modes) so multi-tile footprints are never overpainted by neighbor tiles (`Tile.draw` no longer draws buildings). The green guide overlay is ONE rect spanning the whole footprint in BOTH modes (not one rect per tile) — and it is drawn ONLY for EMPTY spots: once a building is placed the guide lines are removed so occupied space reads as clean.
- Uniform footprint background (`MGNest.draw`): SPRITES mode blits the art DIRECTLY over the map ground — PNG transparency must reveal the battlefield floor (an earlier solid GREY underlay made transparencies "show background"; that is the bunker's behavior too, keep it). Uniform solid square applies ONLY to BLOCK mode: full-footprint BROWN, plain rect, no facing marker (no textures at all in block mode). Missing art also falls back to the block. Art scales to the footprint size (4x4 = 128x128). BUNKER follows the same rules per user request but keeps GREY: `Bunker` is now fully table-driven — `footprint_tiles` from `BUILD_FOOTPRINTS["bunker"]`, hitbox anchored at the marker top-left (the legacy hardcoded 2x3 up-sticking hitbox is gone), art scaled to the footprint, BLOCK mode = ONE plain uniform GREY rect (no facing marker; the GREY block_drawer path is retired for the bunker).
- Collision: `player._is_blocked_at` uses `tilemap.building_covering` (footprint-solid built buildings) and `tilemap.empty_spot_covering` (an EMPTY purchasable spot blocks its whole footprint pre-build — also prevents the player standing inside the footprint when construction completes and freezing). Both probe up-left anchors statelessly; the probe reach derives from the footprint table (biggest side), NOT a hardcoded 3 — keep that derivation when kinds grow. No bookkeeping is needed at the direct `tile.building = ...` assignment sites.
- Fire origin `MGNest.update` centers on the footprint, not the marker tile.

## Game pause
- SPACE pauses/resumes (event-based toggle, keydown only); ESC is a secondary key. Player fire is automatic (AssaultPhase.update calls auto_fire) so there is no manual fire key.
- The HUD shows the SPACE: pause hint at all times; the paused overlay shows resume instructions and the full control reference (incl. +/- zoom).
- While paused: window responsive, rendering continues, simulation stops, overlay + resume instructions visible; stray keydowns while paused trigger nothing (EXCEPT the view-zoom keys, which are a viewing aid and stay live).

## View zoom (+ / - keys, TWO views only)
- `+` (and `=`/KP_PLUS) zooms IN to config `VIEW_CLOSE`; `-` (KP_MINUS) zooms OUT to `VIEW_FULL`. Both set ABSOLUTE states (idempotent — no toggle flip-flop on key autorepeat) and work paused or live. Exactly these two views exist; no intermediate zoom steps.
- FULL = the whole battlefield via the uniform zoom (see Render layout); CLOSE = a player-centered window `CLOSE_VIEW_TILES` (10) tiles ACROSS, uniformly scaled so it OCCUPIES the whole visible strip (no bands): scale = SCREEN_WIDTH/(10*TILE_SIZE) = 4x at 1280x768, 128px screen tiles, ~5.7 tiles vertically, window vertically = visible_h/4 world px; camera clamped so the window never leaves the map. This still satisfies the user's "at most ~5 squares in each direction" cap.
- HUD hint shows `+/-: view FULL|CLOSE` right after the pause info; each battle starts at FULL. Camera for CLOSE reads the LIVE player position every frame.

## Build prompt (near-spot cost ledger)
- `get_nearby_build_spot` only returns EMPTY player-purchasable spots (mg/barracks/artillery). Standing near enemy defenses, the player bunker, or any placed building shows NO prompt and no cost — the cost ledger (PAID/OWES/HAVE) appears only next to an empty player spot.
- Both the prompt and the auto-place contact measure the spot's FULL footprint, not just the marker tile: touch ANY tile of the 4x4 (or nxn) footprint and payment triggers (`assault_phase.auto_place_if_possible` uses a footprint `Rect.colliderect`); the prompt's range is the distance from the player to the footprint RECT (0 anywhere on/inside, nearest edge when outside) — a center-based radius went blind on far 4x4 corner tiles, keep the edge-distance measure.

## HUD force counts panel
- Two columns under the top bar: player forces on the left, enemy on the right (right-aligned). One row each: Infantry / Barracks / MG Nest / Artillery.
- Shown ONLY while paused (rendered over the pause overlay); the live battle view stays clean. The battle state computes all rows (`AssaultPhase._collect_force_rows`); the HUD only renders.
- Player Infantry = live unit count. Player buildables show X/Y where Y = total build spots of that type on the map and X = spots holding a building (replaces the old mixed `count_buildings` legend).
- Enemy Infantry = live count; enemy buildings are placed free at battle start, so they show plain counts.

## Render layout (world vs HUD strip)
- UNIFORM-ZOOM CONTRACT: `AssaultPhase.render` draws the ENTIRE tilemap 1:1 onto a pre-allocated `world_surface` (full `tilemap.width/height * TILE_SIZE`), then scales it by ONE factor `min(SCREEN_WIDTH/world_w_px, (SCREEN_HEIGHT-HUD_BAR_HEIGHT)/world_h_px)` — never a per-axis stretch, so tiles/units stay SQUARE on any map. Per the user's spec the HUD bar is 40 (visible 728) and the map is the screen-DOUBLED 80x46 canvas (world 2560x1472): zoom ≈ 0.4946, view 1266x728, tiled-square pitch ~15.8px, leftover columns drawn as ~7px dark side bands (smooth_scale downscales, band area pre-filled each frame to avoid stale pixels). You can reshape the map freely; the zoom adapts.
- CAMERA: `self.camera_x = 0` always while the zoomed view shows the whole battlefield (any pan would crop parts); spawned/positioned world coordinates stay in full-map world px (player clamps to the 2560x1472 extents).
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

## In-game ground floor texture (IMPLEMENTED in `world/tilemap.py`)
- SPRITES mode: `TileMap.draw` blits `assets/images/map.png` scaled once (in `TileMap.__init__`, via `utils/image_loader.py`) to the full map strip (`width*32 x height*32`) as the ground floor; tiles are skipped, buildings draw over the texture, units/bullets/pickups after (battle state) — the texture IS the ground.
- BLOCKS mode (G): no textures at all — the original per-tile color palette, exactly as before.
- The mode is queried every frame from `graphics/render_mode.py` (never cached), so G flips textured floor <-> tile palette live.
- A missing `map.png` sets `ground_texture = None` in `__init__` and draw silently falls back to tile rendering (never crash on missing art).

# HISTORICAL STANDARDS

Use reputable museums, archives, institutions, and academic sources; for significant claims give source, institution/author, and URL when available. Separate Historical Evidence from Gameplay Design. Balance baseline: 1916–1918. Do not invent units, equipment, capabilities, or national advantages; modifiers stay small, tunable, and faction-level.

# POST-BETA ROADMAP (do not start until the beta ships)

Stabilize systems → combat/AI pass → terrain effects → buildings/defenses → waves/progression → economy → UI/feedback → tanks → aircraft → campaign → release prep.

# IMMEDIATE ACTION

For each task, verify affected files by reading them, then implement one small patch set in this order:
1. ~~Game pause (SPACE / ESC, per guidelines).~~ DONE.
2. ~~Central faction table; wire Player and all unit spawners to it (Playable Axis/Allies).~~ DONE — `systems/factions.py` + faction flow (menu selection, coins, screens, post-battle R/S).
3. ~~Static in-game background~~ DONE — `map.png` floor texture in `TileMap`, bound to the G sprite/block toggle, tile fallback in blocks mode / missing asset.
4. Special effects.
5. Sound.
6. ~~Building footprints~~ DONE — `config.BUILD_FOOTPRINTS` + footprint collision/rendering, all kinds table-driven (user sizes: MG 4x4, artillery 4x2, barracks 4x4, bunker 6x6, statics 7x7).
7. ~~Batch 6: viewport culling, FPS HUD, paused tile coords, air field + tank factory statics, artillery faction art~~ DONE.
8. ~~Zero-cost auto-place~~ DONE — `AssaultPhase.place_zero_cost_buildings`: FREE spots (BUILD_COSTS 0) build at battle start like markers; priced spots keep the touch-and-pay path.
Keep the development checklist current after each step.

## Viewport culling + FPS + paused tile coords (batch 6)
- CULLING (user rule: don't render textures not on screen; matters when zoomed in): `TileMap.draw(screen, camera_x, view_rect=None)` takes an optional world-px rect — CLOSE view passes the clamped player window (`SCREEN_WIDTH/(10*TILE_SIZE)` regime; FULL passes None = draw everything). When view_rect is set: the ground JPEG is blitted as ONE clipped region (source-rect blit), the BLOCK-mode tile loop slices to the visible rows/cols, `_draw_buildings` skips buildings whose footprint rect misses the view, and the green spot outlines skip off-view spots.
- Entity draws are culled at the battle level (`AssaultPhase.render`): enemies/gold/bullets/enemy bullets/friendlies in view only — helper `in_view(x, y)` vs `view_rect` + `CULL_MARGIN = 128` world px (covers sprite sizes; player is always drawn, the window is player-centered). The stale pixels left OUTSIDE the window on `world_surface` are never read: the CLOSE zoom subsamples exactly the window and the window region is fully repainted every frame (verify scripts must clear `world_surface` between passes to prove culling — stale-pixel false positives otherwise).
- FPS in the top bar: `AssaultPhase.fps` smoothed 0.9/0.1 from `1000/dt` (`dt` IS last frame's ms — engine always calls update, so the meter runs even while paused; measured at the very top of `update` BEFORE the pause gate). HUD draws `FPS: N` at x≈430 right after the gold (`hud.draw(..., fps=)`; None hides it). A screenshot-only `FPS: 0` means the harness never called update, not a bug.
- Paused overlay tile coords: `Player tile: X a | Y b`, 1-BASED per tile (`int(x // TILE_SIZE) + 1`), NW-most tile = (1, 1). Drawn under the resume hint at screen_h//3+96.
- AIR FIELD / TANK FACTORY (user-approved): new map legend letters 'F'/'K' (player side, static). Placed FREE at battle start like enemy markers (NOT in BUILDING_CLASSES/BUILD_COSTS-payable — never purchasable, never prompted), classes `AirField`/`TankFactory` in `src/entities/static_building.py` (`StaticBuilding` base: scene-variant art across the full footprint via the standard chain, BROWN block fallback in BLOCK mode, deliberate no-op `update()` — no combat behavior yet). SIZED per user (currently 7x7, after 6x6/7x7/9x9/10x10 tuning): air_field/tank_factory = 7x7 (barracks/MG 4x4, artillery 4x2, bunker 6x6) — statics + `Barracks`/`Bunker`/`Artillery` all read `footprint_tiles` from the table; art/blocks scale to it, collision covers the whole footprint (type strings in `player.BLOCKING_BUILDINGS`; `building_covering` proved every covering tile solid and free just past each edge). Units don't collide with buildings, so infantry still walks out of the barracks spawn point. NOTE for map editing: markers closer than a footprint's side overlap (first marker wins; a placed building blocks only its own anchor tile) — space markers at least one footprint side apart. The user's map now HAS real F/K/B markers (plus 2 I, 3 A) and boots clean across scenes a/b/c/d. USER also added placeholder BUILD_COSTS entries for air_field/tank_factory (inert until they join BUILDING_CLASSES — their decision for a later round). 
- BUGFIX (crash reported by user): `Barracks` referenced `load_first_image`/`building_variant_filenames` without importing them → NameError when the game auto-built a barracks; imports added (`entities/barracks.py`).
- SPAWN SAFETY (user rule: start OUTSIDE the bunker, never on top of anything): `AssaultPhase` spawn BFS now requires `spawn_ok` = walkable '.' AND `building_covering` None AND `empty_spot_covering` None (built buildings incl. the 4x4 bunker + statics, and empty spot footprints all block the spawn). BFS prefers the tile LEFT of the anchor (outside/front of the bunker) then up/down/right. Fallback default (3*TILE_SIZE, mid-row) stays as a last resort. Verified: spawn tile clear of every marker footprint and the player's own `_is_blocked_at` reads False there.
- ARTILLERY ART BY FACTION: `factions.ARTILLERY_IMAGE` = {"allies": "unit_cannon_fr.png", "axis": "unit_heavy_howitzer_ger.png"} + `artillery_filename(faction)`; `Artillery.__init__` loads it alpha=True scaled to the `footprint_tiles` size (4x2 = 128x64; blit-direct, no underlay), draw falls back to the GREY block (over the full footprint) in BLOCK mode/missing art. Both allied nations share the french cannon (user-directed).
- ARTILLERY NO-MAN'S-LAND BARRAGE (user design, replaces the old nearest-target bullet): `Artillery.update` never aims at units. Each shot lands on a random UNUSED tile in the gun's band — center column +14..+18 tiles toward the FRONT (player guns fire EAST, enemy guns WEST; the enemy 'a' guns are just mirrored), rows = gun center row ±5, clipped to map. Rules: no unit targeting; NO tile hit twice per gun (`used_tiles` per instance — exhausted band = gun stands down); splash = impact tile + its 8 neighbours, damage 20 ("half of an infantry unit" — infantry hp 40) to ANY standing unit there (per user choice; the player entity has no hp so it is unaffected by design); impact shows a brief RED dot (class `DOT_TIME` 0.5 s, `impacts` = [x_px, y_px, ttl] ticked in `update`). Red dots draw as their own `AssaultPhase.render` pass (`BuildingQuery` scan + `in_view` on the IMPACT position, so dots show even when their gun is culled); `Artillery.update` keeps its `(dt, enemies, bullets)` signature (`bullets` unused; shells are instant). Old `range/damage` attrs and the `Bullet` import are gone.
- Bunker a/c: bunker already followed the scene chain — verified (variants a/c), not re-wired. Artillery/static art verified across scenes a + c and both factions (art non-None each time).
- Verified: `Temp\opencode\verify_batch6.py` (artillery candidates via module-level loader recorder; statics placement/3x3/inert/unpurchasable; BLOCK-mode culling proof — inside window painted BROWN, outside NOT, and FULL still paints all; FPS measured + updates while paused; paused tile math; scenes a/c statics art) + all five regressions (zoom, square tiles, mg2x2, variant boot a/b/c/d both factions, scene random pool) PASS. Screenshots: batch6_close_sprites.png (winter CLOSE w/ air field + tank factory + both artilleries), batch6_paused_full.png (pause overlay, tile X/Y, force panel).
