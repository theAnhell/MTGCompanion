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
1. Replace `data/AllGames.json` with the new export (same filename, same
   path — this is `GAMES_EXPORT_PATH` in `.env`).
2. Re-run the import:
   ```
   docker compose exec app python manage.py import_games
   ```
3. Check the summary line it prints (games/game_players/players/commanders
   upserted) to confirm the new games came through.

It's idempotent (upserts by the source app's own UUIDs via Postgres
`ON CONFLICT ... DO UPDATE`, same as the Node version's Knex upserts) and
never deletes existing rows, so it's always safe to re-run — no need to
restart or rebuild the containers first.

Running tests
-------------
```
docker compose exec app python manage.py test
```
With coverage:
```
docker compose exec app coverage run --source='.' manage.py test
docker compose exec app coverage report -m
```
`.coveragerc` omits migrations, `manage.py`, and the WSGI/ASGI entry points.
Each app's tests live under `<app>/tests/` (`test_services.py`/`test_views.py`,
matching the `services.py`/`views.py` split). External HTTP calls (EDHREC,
Scryfall) are mocked — the suite never makes real network requests.
Not covered: the thinner management-command wrappers
(`import_retired_decks`, `import_moxfield_decks`, `sync_edhrec_stats`'s CLI
layer) beyond `import_games`, since they're mostly shells over
already-tested service functions.

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
