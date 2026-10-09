# Table Tennis

In this project we try to implement a functioning scoring system, with buttons connected to Arduino/ESP32.

Ratings are kept **per table**: a player has a separate elo at Matteland, Valgrinda,
Stripa, Kjelhuset and Realfagsbygget. Elo changes once per **match**, never per game.
You record the final point score of each game — never individual points.

## Running it

```bash
python run.py                  # then open http://127.0.0.1:8000
```

This is a server: it keeps running and holds that terminal until you press `ctrl-c`.
That is normal, not a hang. If you need to type other commands while the site is up,
open a second terminal.

`run.py` works from any directory and needs no install. Do not use
`python -m table_tennis.server` unless the package is installed: this repo relies on
`PYTHONPATH=src`, a *relative* path that only resolves when your shell happens to be
in the repo root.

The terminal CLI is still there for point-by-point scoring:

```bash
python -m table_tennis.main    # asks which table, then A/B per point
```

Tests: `python -m pytest`

## Running on a Raspberry Pi

This puts the scoreboard on the club network so anyone can record a match from
their phone.

**1. Install and clone** (Raspberry Pi OS Bookworm or newer; needs Python 3.10+):

```bash
sudo apt update && sudo apt install -y git python3
git clone <this repo> /home/pi/Table-Tennis
cd /home/pi/Table-Tennis
python3 run.py --host 0.0.0.0        # ctrl-c once you have seen it start
```

`--host 0.0.0.0` is what makes it reachable from other devices; the default
`127.0.0.1` only allows the Pi itself.

**2. Check another device can reach it** before going further. From your phone on the
same wifi, open `http://<pi-ip>:8000` (`hostname -I` on the Pi gives the address).
If that fails, see *If phones cannot reach it* below.

**3. Start on boot:**

```bash
sudo cp deploy/table-tennis.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now table-tennis
systemctl status table-tennis        # should say active (running)
```

Edit `User=` and the paths in the unit file first if you cloned elsewhere. Logs:
`journalctl -u table-tennis -f`.

**4. Give people a URL.** `http://raspberrypi.local:8000` works from iPhones, Macs and
Windows 11, but **many Android phones do not resolve `.local`**, so also write the raw
IP on a sign by the table. Reserve that IP in the router's DHCP settings, or it will
change and the sign will go stale.

### If phones cannot reach it

Most likely **client isolation**: eduroam and many campus networks deliberately block
devices from talking to each other, which no amount of configuration on the Pi will
fix. Test by pinging the Pi's IP from a laptop on the same wifi. If that is the case,
put the Pi on its own router or phone hotspot and have people join that - or set up
*Public access with Cloudflare Tunnel* below, which avoids the problem entirely by
having the Pi dial out rather than be dialled into.

### Worth knowing

- **No login.** Anyone who can reach the page can record matches, including made-up
  ones, under any name. Ratings cannot be deleted through the site, but they can be
  polluted. Fine for a club on its own network, not for anything public.
- **`data/` is gitignored and is the only copy of the ratings.** SD cards die. Copy
  `data/` off the Pi now and then:
  `rsync -a pi@raspberrypi.local:Table-Tennis/data/ ./backup/`
- **Port 80** removes the `:8000` from the URL; see the comment in
  `deploy/table-tennis.service`.

### Public access with Cloudflare Tunnel

Puts the site on a real address like `https://pingpong.wilhelbr.com`, reachable off
campus, with no port forwarding and no public IP on the Pi. It also sidesteps campus
client isolation, because the Pi makes an outbound connection instead of accepting
inbound ones.

You need a domain in your Cloudflare account first. Subdomains are free and unlimited
once you own one, so a single domain covers this and anything you build later.

**On the Pi** (`dpkg --print-architecture` tells you `arm64` or `armhf`):

```bash
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64.deb -o cloudflared.deb
sudo dpkg -i cloudflared.deb

cloudflared tunnel login                                   # opens a browser, pick the domain
cloudflared tunnel create pingpong                         # prints a tunnel id - keep it
cloudflared tunnel route dns pingpong pingpong.wilhelbr.com
```

Write `~/.cloudflared/config.yml`, pasting in the tunnel id from above:

```yaml
tunnel: pingpong
credentials-file: /home/pi/.cloudflared/<tunnel-id>.json

ingress:
  - hostname: pingpong.wilhelbr.com
    service: http://localhost:8000
  - service: http_status:404
```

The three commands above each finish and return your prompt - the site does not need
to be running for any of them. Only the two below keep hold of a terminal.

Test it, then make it permanent:

```bash
cloudflared tunnel run pingpong     # blocks, like run.py. check the url, then ctrl-c
sudo cloudflared service install    # runs it in the background from here on
```

After `service install` the tunnel needs no terminal at all, so `python run.py` is the
only thing left to start by hand. Until then you need two terminals: one per process.

Cloudflare terminates TLS, so the url is `https://` with no certificate to manage and no
`:8000` on the end.

The `--host 0.0.0.0` in the service unit stays useful: the tunnel only needs
`127.0.0.1`, but keeping `0.0.0.0` means the club can still reach the Pi directly on
the LAN if the internet is down. Tighten it to `127.0.0.1` if you would rather the site
be reachable *only* through the tunnel.

#### From a Windows PC instead of a Pi

The tunnel works the same from any machine. Install with
`winget install --id Cloudflare.cloudflared`, then run the same three
`cloudflared tunnel ...` commands above.

Two things differ:

- The config file lives at `%USERPROFILE%\.cloudflared\config.yml`, and
  `credentials-file` points at `C:\Users\<you>\.cloudflared\<tunnel-id>.json`.
  Everything else in the yaml is identical.
- There is no systemd. Run `cloudflared service install` from an **administrator**
  prompt to start the tunnel on boot, and use Task Scheduler ("At log on", action
  `python C:\path\to\Table-Tennis\run.py`) if you want the site itself to come back
  automatically too.

Both `run.py` and the tunnel have to be running for the url to work. **The site is only
up while that PC is on** - closing the laptop takes the leaderboard down. That is the
one real advantage a Pi has: it sits plugged in and stays up. Everything else about
this setup is the same.

**Add a login before you share the url.** There is no authentication in this app, so
anyone who finds a public address can record matches under any name. Cloudflare Access
(free for small teams) puts an email or Google login in front of the tunnel without any
code change - do that, or keep the site on the LAN.

## Deploying to Cloudflare Workers

The site runs on Cloudflare's machines, so nothing of yours has to stay on. No
`run.py`, no tunnel, no laptop. Storage is D1 (Cloudflare's SQLite), which
replaces `data/*.json` and `pins.json`.

```bash
npx wrangler login                      # once
npx wrangler d1 create nppu             # prints a database_id
```

Paste that id into `wrangler.toml`, then create the tables and deploy:

```bash
npx wrangler d1 execute nppu --remote --file=worker/schema.sql
npx wrangler deploy
```

Point `pingpong.wilhelbr.com` at it under Workers & Pages -> nppu -> Settings ->
Domains & Routes -> Add custom domain. That replaces the tunnel entirely: delete
the old `pingpong` CNAME first if it is still there.

### Working on it locally

```bash
npx wrangler d1 execute nppu --local --file=worker/schema.sql   # once
npx wrangler dev --local                                        # http://localhost:8787
```

`--local` uses a SQLite file on disk and never touches the deployed database.

### Reading and resetting codes

Codes live in the `codes` table instead of `pins.json`, so `admin.py` does not
reach them any more. Use SQL:

```bash
npx wrangler d1 execute nppu --remote --command "SELECT display, code FROM codes ORDER BY display"
npx wrangler d1 execute nppu --remote --command "DELETE FROM codes WHERE name_key = 'ola'"
```

The second one is the reset: they pick a new code on their next match, and their
elo and history are untouched. `name_key` is the name lowercased with spacing
collapsed.

### What the Python is still for

`run.py` and `src/table_tennis/` are the original implementation and still work
(`python run.py`). The Worker is a port of the same rules - the elo maths was
diff-tested against the Python across 990 rating/k-factor combinations and is
identical to 9 decimal places. Keep the Python for the terminal CLI and the test
suite, or delete it once the Worker has proven itself.

## Layout

```
run.py                     start the site
src/table_tennis/
  server.py                stdlib http.server: serves website/ and POST /api/match
  main.py                  terminal CLI
  scoring/game.py          one game to 11
  scoring/match.py         a match is a list of games
  rating/elo.py            elo, applied once per match
  rating/json_helpers.py   per-table storage, atomic writes; TABLES lives here
website/                   index (table picker), leaderboard, record
data/<table>/              players.json, matches.json, elo_ranking.json  (gitignored)
```

Adding a table is one line: `TABLES` in `src/table_tennis/rating/json_helpers.py`.
