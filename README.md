# dppb2 game server

Docker Compose setup for hosting a **Digital Paint: Paintball 2** dedicated server.

## Important network note

This game server uses **UDP** (default port `27910`), not HTTP.

- For players, the main thing is: `dppb.anatoliy.ch` must resolve to your server IP.
- Open/forward `27910/udp` on firewall/router to the host with Docker.
- HTTP reverse proxy config (`server { location / { ... } }`) will not work for this traffic.

## Files

- `docker-compose.yml` - starts container `dppb2` and exposes `27910/udp`.
- `pball/myserver.cfg` - your custom game server config.

## Run

```bash
docker compose up -d
docker compose logs -f dppb2
```

## Player connection

In Paintball 2 client console:

```text
connect dppb.anatoliy.ch:27910
```

## If you really need nginx in front

Use `stream` (UDP), not `http`. Domain-based routing is not available for this protocol, so route by port.

```nginx
stream {
    upstream dppb2_upstream {
        server dppb2:27910;
    }

    server {
        listen 27910 udp;
        proxy_pass dppb2_upstream;
    }
}
```

## Sources

- Official site: [digitalpaint.org](http://digitalpaint.org)
- Server docs: [Digital Paint - Servers](http://digitalpaint.org/v2/docs/server.html)
- Docker image discussion: [Digital Paint forum thread](https://forums.digitalpaint.org/index.php?topic=28768.0)

## Push to private GitHub repository

```bash
git init
git add .
git commit -m "Initial Paintball 2 dedicated server setup"
git branch -M main
git remote add origin git@github.com:<your-user>/<your-private-repo>.git
git push -u origin main
```
