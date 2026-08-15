MythicTrackDjango
==================

A Django/DRF port of [MythicTrack](../MythicTrack) — same personal Commander
(EDH) stats API, same Postgres schema, rebuilt as a learning project. This is
a separate, self-contained copy: its own Postgres container, its own copy of
`AllGames.json` and the retired-decks/Moxfield config under `data/`. Nothing
here touches the original Node project.

Stack: Python, Django, Django REST Framework, PostgreSQL, dockerized (app + db).

Quick start
-----------
1. `cp .env.example .env` (defaults work fine for local use).
2. `docker compose up -d --build` — starts Postgres (host port 5433) and the
   API (host port 8000; the Node version uses 5432/3000, so both can run at
   the same time).
3. Run migrations and import your data:
   ```
   docker compose exec app python manage.py migrate
   docker compose exec app python manage.py import_games
   docker compose exec app python manage.py import_retired_decks
   docker compose exec app python manage.py import_moxfield_decks
   ```
4. `curl localhost:8000/health`

Re-importing a fresh export
----------------------------
Drop the new export at `data/AllGames.json` (replacing the copy already
there) and re-run `import_games` — it's idempotent (upserts by the source
app's own UUIDs via Postgres `ON CONFLICT ... DO UPDATE`, same as the Node
version's Knex upserts) and never deletes existing rows.

Player identity
----------------
Same mechanism as the Node version: `data/player-merges.json` (already
copied over). Add `{"aliasId": "<uuid>", "canonicalId": "<uuid>"}` entries
and re-run `import_games`.

Project layout
---------------
- `config/` — the Django project package (settings, urls, the DRF error
  handler that reshapes `{"detail": ...}` into `{"error": ...}` to match the
  Node app's error shape). Not to be confused with the Node project's
  top-level `config/` folder of data files — that content lives in `data/`
  here instead, since the name was already taken.
- `players/`, `commanders/`, `games/`, `decks/` — one Django app per
  domain, each with `models.py` (schema), `services.py` (query logic,
  mirroring the Node `*.repository.ts` files), `serializers.py`, `views.py`,
  `urls.py`. `decks/` covers both `retired_decks` and `deck_cards`, same
  grouping as the Node `src/domain/decks/` folder.
- `stats/` — no models; `services.py` is a straight port of
  `stats.service.ts`, aggregating in Python over ORM querysets rather than
  in SQL (kept that way on purpose, to mirror the original). `collation.py`
  works around a real difference from the port: Python's default string
  sort is codepoint-based, while JS's `localeCompare` is locale-aware, so
  accented names (e.g. "Éowyn") sorted in the wrong place until this was
  added as a tiebreak key.
- `imports/management/commands/` — `import_games`, `import_retired_decks`,
  `import_moxfield_decks`, one-to-one with `src/import/*.ts`.
- `data/` — `AllGames.json`, `player-merges.json`, `moxfield-decks.json`,
  `decklists/`, `retired_decks.json`, `retired/` — copied from the Node
  project at the time this port was created. Update independently going
  forward.

API overview
------------
Identical routes and query params to the Node API (see the Node project's
README for the full table) — same base path `/api/v1`, same endpoints under
`/players`, `/commanders`, `/games`, `/players/:id/retired-decks`,
`/players/:id/decks/*`, `/players/:id/streaks`, `/players/:id/summary`,
`/reports/yearly`.

Two differences from the Node app, both intentional:
- Django admin is enabled at `/admin/` (`python manage.py createsuperuser`
  to get in) — a browsable view over every table, which the Node app never
  had.
- `USE_TZ = False` project-wide: the source export's `createdOn` timestamps
  carry no timezone info, and the Node version stores them as-is with no
  conversion (`created_on` is `timestamp without time zone` in Postgres).
  Keeping Django naive too avoids it silently reinterpreting those
  timestamps as UTC.
