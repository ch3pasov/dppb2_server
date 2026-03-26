# dppb2 game server

Docker Compose setup for a public **Digital Paint: Paintball 2** dedicated server.

The server is visible in the global PB2 server list and runs on UDP port `27910`.

## Project structure

- `docker-compose.yml` - starts services and exposes `27910/udp`.
- `config/server.cfg` - main server config (`hostname`, `website`, `e-mail`, slots, etc.).
- `config/motd.txt` - Message of the Day shown by compatible clients.
- `config/logins.txt` - dplogin operator list (`player_id op_level` per line); init copies it to `pball/configs/logins<port>.txt` using `set port` from `server.cfg` (required by PB2).
- `pball/maps/italy.bsp` - map file mounted into the container.
- `pball/textures/` - synced texture tree used by the server (`pball`, `sfx`, and Italy dependencies).
- `pball/gamei386.so` - server game module.

## How it works

Compose starts two services:

1. `dppb2_map_init` (one-shot init):
   - copies `gamei386.so` into local `pball/` if needed
   - downloads `italy.bsp` if missing
   - syncs base textures (`pball`, `sfx`) from image to local `pball/textures`
   - downloads Italy-specific missing textures from `dplogin/files/textures/*`
   - copies `config/server.cfg`, `config/motd.txt`, and `config/logins.txt` (when present) into `pball/configs/` (operators land in `logins<port>.txt` per `set port`)
2. `dppb2` (main server):
   - runs dedicated PB2 server
   - executes `server.cfg`
   - starts map `italy`

## Run

```bash
docker compose up -d
docker compose logs -f dppb2
```

Stop:

```bash
docker compose down
```

Restart after config changes:

```bash
docker compose restart dppb2
```

## Configuration

Edit `config/server.cfg`.

Common fields:

```cfg
set hostname "Anatoliy Ch. PB2 server [@ch_an]"
set website "https://anatoliy.ch" s
set e-mail "pb2@anatoliy.ch" s
set maxclients 16
set port 27910
set motdfile pball/configs/motd.txt
```

Edit MOTD text in `config/motd.txt`.

### Login operators (optional)

Edit **`config/logins.txt`** only (no port in the filename). On `dppb2_map_init`, it is copied to **`pball/configs/logins<port>.txt`**, where `<port>` is taken from `set port` in `server.cfg`—that is what PB2 loads. Each line is `<dplogin_player_id> <op_level>` (see [Display Players](https://dplogin.com/index.php?action=displaymembers) on dplogin for IDs). Example: `212130 200` grants full op to dplogin user **volked** (player id `212130`) when that account is used in-game. After changing port or `logins.txt`, re-run init (`docker compose run --rm dppb2_map_init`) or `docker compose up` so the target file is updated.

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
