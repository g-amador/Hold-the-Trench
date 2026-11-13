"""
Shared damage/death flavors for the entity roster.

The entity classes carried near-identical take_damage bodies (review
finding: 9 copies in 3 shapes). The shape that matters is HOW damage
interacts with death, and exactly two observable behaviors exist:

RawSubtractDamage — subtract straight into hp (hp may go negative);
hp <= 0 flips the dead flag the unit-list filters read. Used by the
ENEMY units, whose filters/pickups expect the historical raw path.

FlooredDamage — dead units ignore further hits, hp floors at 0, and
dead = hp <= 0. Used by the destructible BUILDINGS and the friendly
side. (Bunker historically lacked the dead-return guard; with the hp
floor clamped at 0 the extra guard is provably unobservable — repeated
hits keep hp at 0 and dead already True — so bunker shares this one.)

Per-entity death CASCADES stay on the entities (gold spawn, expired
lists); this module only owns the hp arithmetic.
"""


class RawSubtractDamage:
    """Damage flavor: raw hp subtraction, dead at <= 0 (no re-hit guard)."""

    def take_damage(self, dmg):
        """Subtract hp; hp <= 0 flips the dead flag used by all filters."""
        self.hp -= dmg
        if self.hp <= 0:
            self.dead = True


class GuardedRawDamage(RawSubtractDamage):
    """Raw flavor plus a dead guard: re-hits after death are no-ops.

    The planes use this so a post-mortem bullet/bomb in the same frame
    cannot keep subtracting hp below what already killed the plane.
    """

    def take_damage(self, dmg):
        if self.dead:
            return
        RawSubtractDamage.take_damage(self, dmg)


class FlooredDamage:
    """Damage flavor: re-hit guarded, hp floors at 0, dead = hp <= 0."""

    def take_damage(self, dmg):
        """Apply damage; hp floors at 0 so `is_destroyed` reads true once."""
        if self.dead:
            return
        self.hp = max(0, self.hp - dmg)
        self.dead = self.hp <= 0
