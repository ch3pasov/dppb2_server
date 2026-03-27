# dppb2 game server

Docker Compose setup for a public **Digital Paint: Paintball 2** dedicated server.

The server is visible in the global PB2 server list and runs on UDP port `27910`.

## Project structure

- `docker-compose.yml` - builds a thin layer on top of `nukla/paintball2` and starts services.
- `Dockerfile` - adds **Python 3 + PyYAML** and copies `scripts/render_config.py` / `apply-config.sh` (the base image has no YAML stack).
- `config.yaml` (repo root) - **single source of truth** for server cvars, MOTD, and dplogin operators; rendered into `pball/configs/` on every game container start.
- `scripts/render_config.py` - reads `config.yaml` and writes `server.cfg`, `motd.txt`, and `logins<port>.txt`.
- `scripts/apply-config.sh` - wrapper used by Compose entrypoints.
- `pball/maps/italy.bsp` - map file mounted into the container.
- `pball/textures/` - synced texture tree used by the server (`pball`, `sfx`, and Italy dependencies).
- `pball/gamei386.so` - server game module.

## How it works

Both **`dppb2_map_init`** and **`dppb2`** use the same image **`dppb2-server:local`** built from this repo’s **`Dockerfile`** (extends `nukla/paintball2:latest`).

1. `dppb2_map_init` (one-shot init):
   - copies `gamei386.so` into local `pball/` if needed
   - downloads `italy.bsp` if missing
   - syncs base textures (`pball`, `sfx`) from image to local `pball/textures`
   - downloads Italy-specific missing textures from `dplogin/files/textures/*`
   - seeds `default.cfg` / `rotation.txt` / `commands.txt` if missing
   - runs **`apply-config.sh`** → **`render_config.py`** so `pball/configs/` matches **`config.yaml`**
2. `dppb2` (main server):
   - on **each start** (including `docker compose restart dppb2`): **`apply-config.sh`** then `start.sh +exec server.cfg +map italy`
   - `config.yaml` is mounted read-only at `/config/config.yaml`; `pball/configs/` is writable so generated files land on the host tree the server reads

**First run / after pulling:** build the image once (Compose does this on `up` if missing):

```bash
docker compose build
docker compose up -d
```

## Run

```bash
docker compose up -d
docker compose logs -f dppb2
```

Stop:

```bash
docker compose down
```

Restart after **editing `config.yaml`**:

```bash
docker compose restart dppb2
```

**After you change `docker-compose.yml` or `Dockerfile`**, recreate containers:

```bash
docker compose up -d --build --force-recreate
```

If `/scripts/render_config.py` is missing inside the container, you are on an old image—run **`docker compose build`** and recreate **`dppb2`**.

You only need **`dppb2_map_init`** again for assets it owns (`gamei386.so`, `italy.bsp`, texture sync, seeding default configs when missing)—not for routine edits to **`config.yaml`**.

## Configuration (`config.yaml`)

Edit **`config.yaml`**. On start, the renderer produces:

| Output | Source in YAML |
|--------|----------------|
| `pball/configs/server.cfg` | Named blocks (see below), merged in fixed order. A **`//` banner** at the top states the file is auto-generated — edit **`config.yaml`** instead; `#` comments in YAML are not copied into cfg lines. If **`motd`** has text, the renderer also emits **`set motdfile`** for the generated `motd.txt`. |
| `pball/configs/motd.txt` | Root **`motd`** or **`server.motd`** (multiline, use `\|`). Omitted or whitespace-only → no file and no `set motdfile` line. |
| `pball/configs/logins<port>.txt` | **`server.operators`**; `<port>` is **`server.listing.port`**. |

**Layout** (`schema_version: 4`): root **`motd`** (optional). **`server.listing`**: `listed_in_browser`, `master_server`, **`port`**, nested **`identity`** (`hostname`, nested **`contact`**). **`server.operators`** optional. **`gameplay`**: **`maxplayers`** (emitted as engine cvar **`maxclients`**), **`elim`**, nested **`bots`**. The renderer supports **this shape only**; older config layouts need to be migrated.

Example (abbreviated):

```yaml
schema_version: 4

motd: |
  First line of MOTD
  ...

server:
  listing:
    listed_in_browser: true
    master_server: dplogin.com
    port: 27910
    identity:
      hostname: "My PB2 server"
      contact:
        website: https://example.com
        e-mail: admin@example.com
  operators:
    - id: 212130
      op_level: 200

gameplay:
  maxplayers: 16
  elim: 15
  bots:
    bot_min_players: 4
    bot_min_bots: 0
    bots_vs_humans: 0
```

Omit **`operators`** (or use `operators: []`) if you do not want a `logins*.txt` file generated.

### Local render (without Docker)

```bash
apt install python3-yaml   # or: pip install -r scripts/requirements.txt
python3 scripts/render_config.py --config config.yaml --dest pball/configs
```

### Elimination respawn (`elim`)

Set **`gameplay.elim`** (seconds) before re-entry ([basic server docs](http://digitalpaint.org/docs/server_cvars_basic.txt)); stock game default is **60**. Use **`0`** to stay out until the **round** ends.

**Team-size scaling** is not available as a stock formula; see earlier notes on **`elim_inc`** / **`elim_increases`** in game docs and news.

### Bots

Use **`gameplay.bots`** for `bot_min_players`, `bot_min_bots`, `bots_vs_humans` (Build 46+, [Digital Paint news](https://digitalpaint.org/news.php)).

### Login operators

Under **`operators`**, each entry needs **`id`** (dplogin player id) and **`op_level`** (or alias **`level`**). Lookup: [Display Players](https://dplogin.com/index.php?action=displaymembers) on dplogin.

## Network requirements

- UDP port `27910` must be open/forwarded to the Docker host.
- HTTP reverse proxy is not required.

## Quick checks

Container status:

```bash
docker ps --filter name=dppb2
```

Logs:

```bash
docker logs --tail 100 dppb2
```

Local UDP status probe:

```bash
python3 - <<'PY'
import socket
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.settimeout(2)
s.sendto(b'\xff\xff\xff\xffstatus\n', ('127.0.0.1', 27910))
print(s.recvfrom(8192)[0].decode('latin1', 'ignore'))
PY
```

## Sources

- Official site: [digitalpaint.org](http://digitalpaint.org)
- Server docs: [Digital Paint - Servers](http://digitalpaint.org/v2/docs/server.html)
- Docker image thread: [Digital Paint forum](https://forums.digitalpaint.org/index.php?topic=28768.0)
