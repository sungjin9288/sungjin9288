# CLI RPG

A **feature-complete, single‑player CLI RPG** built in Python.

This project started as a simple synchronous console game and evolved into a **fully structured RPG** with region conquest, crafting‑driven progression, meta systems, save/load persistence, and a hidden **True Ending** — all implemented **without introducing unnecessary systems**, focusing instead on clean rules and player experience.

> Status: **Feature Complete (Final Version)**

---

## 🎮 Game Overview

The player starts from a small **village** and explores increasingly dangerous regions:

**Village → Grassland → Cave → Ruins → Deep Ruins (Boss)**

Each region has:

* Unique monsters and materials
* Distinct risk–reward characteristics
* A miniboss whose defeat permanently alters the world

The journey culminates in a confrontation with **The Ruin King**, a symbol of decay and collapse. Players who fully understand and conquer the world may unlock a **hidden True Ending**.

---

## 🧱 Core Systems

### Combat

* Turn‑based combat
* Player actions: Attack / Guard / Potion / Run
* Guard introduces tactical depth and counter‑play
* Status effects:

  * **Bleed** (damage over time)
  * **Stun** (limited, reduced effectiveness on bosses)

### Boss Design

* Main boss: **The Ruin King**
* Pattern‑based behavior:

  * Charging attacks
  * Defensive stance
  * Enrage phase
* **True Ending Phase (Phase 2)**:

  * HP / ATK scaled ×1.3
  * Enhanced patterns
  * Increased resistance to status effects

---

## 🗺️ Regions & Conquest Rules

Each region can be **conquered** by defeating its miniboss for the first time.

### Region Conquest Effects

* Conquest is recorded once via `LogBook`
* After conquest, the region permanently changes

### Conquest Bonus Materials

| Region    | Bonus Material        |
| --------- | --------------------- |
| Grassland | Essence of the Plains |
| Cave      | Deep Ore              |
| Ruins     | Core of Corruption    |

**Drop Rule**

* Before conquest: bonus material never drops
* After conquest: added to the region drop pool at a **fixed 15% chance**
* No depth / build / item modifiers

These materials are **fully consumable** and used only for crafting:

* Tier 2 advanced equipment
* Tier 3 (final) equipment as secondary ingredients

---

## ⚒️ Equipment & Crafting

### Build Tags

All equipment belongs to one of three build archetypes:

* **OFFENSE** – damage focused
* **DEFENSE** – survivability focused
* **EXPLORER** – exploration and drop efficiency

### Equipment Tiers

* **Tier 1–2**

  * Can appear in shops (random rotation)
  * Craftable
* **Tier 3 (Final Equipment)**

  * **Crafting only**
  * Always requires at least one boss material
  * Never sold in shops

Tier 3 equipment includes short lore descriptions to reinforce narrative identity.

---

## 🏪 Shop & Economy

### Village Shop

* Buy / sell potions, materials, and equipment
* Equipment selling:

  * 50% of list price if sold by the shop
  * Otherwise derived from crafting recipe material value
  * Auto‑unequip if the item is currently equipped

### Shop Rotation

* On each village visit, shop equipment rotates
* Rotation rules:

  * One item per build (OFFENSE / DEFENSE / EXPLORER)
  * Randomly selected
  * **Tier 1–2 only**

This creates a soft incentive to revisit the village and adapt builds.

---

## 📜 Meta Systems (Log‑Driven)

All progression and meta systems are driven by a unified **LogBook**.

### Quest System

* Run‑based quests
* Observes combat and exploration logs
* Rewards: gold, materials, or records (no stat bonuses)

### Achievements

* Permanent records
* No gameplay bonuses

### Collection (Dex)

* Material Dex
* Equipment Dex
* (Optional) Monster / Boss records
* Discovery is logged via system markers
* Dex progress persists through save/load

---

## 💾 Save & Load

* JSON‑based persistence
* Save / load available only in the village (safe checkpoint)
* Persisted state:

  * Player stats
  * Inventory & equipment
  * Achievements
  * Collection progress
* Quests reset per run by design

---

## 🏁 Endings

### Normal Ending

* Defeat the Ruin King
* Ending text reflects playstyle

### True Ending (Hidden)

**Unlock Conditions** (all required):

* All regions conquered
* Collection completion ≥ 80%
* Ruin King defeated at least once

**Trigger**

* Re‑enter Deep Ruins after meeting conditions
* Player choice: proceed or withdraw

**True Ending Battle**

* Phase 2 Ruin King (scaled stats + enhanced patterns)

**Records**

* `TRUE_ENDING_UNLOCKED`
* `TRUE_ENDING_CLEAR`

The True Ending represents the final purification of the world.

---

## 🧪 Testing

```bash
python -m unittest discover -s tests
```

* Core rules, economy logic, conquest behavior, and endings are covered
* Log output during tests is intentional where noted

---

## 🎯 Design Philosophy

* Prefer **clear rules over complex systems**
* Avoid stat inflation
* Reuse existing structures instead of adding new layers
* Let player decisions shape the narrative outcome

This project emphasizes **completeness, coherence, and restraint**.

---

## 📌 Project Status

This project is considered **final and complete**.

Future work, if any, would be pursued as **separate projects** (e.g., combat simulators or balance analysis tools) rather than extending the core game.
