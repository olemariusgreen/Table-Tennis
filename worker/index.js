// NPPU on Cloudflare Workers.
//
// Static files are served by the assets binding; this only handles /api/*.
// The rules are a direct port of the Python in src/table_tennis/ - point ->
// game -> match, elo once per match, ratings per table, codes per person.

// Lives in worker/, not website/, so it is never served as a public static file.
import ADMIN_PAGE from "./admin.html";

export const TABLES = ["Matteland", "Valgrinda", "Stripa", "Kjelhuset", "Realfagsbygget"];

const MAX_GAMES = 9;    // best-of-9 is already generous
const MAX_POINTS = 99;
const MAX_NAME = 40;
const MAX_BODY = 4096;

// --- rules (ports of scoring/game.py, scoring/match.py, rating/) -------------

// Identity key: without this "Ola", "ola" and "OLA" are three players, which
// both defeats the code and lets someone play themselves for free elo.
export function canonicalName(name) {
  return name.trim().split(/\s+/).join(" ").toLowerCase();
}

export function displayName(name) {
  return name.trim().split(/\s+/).join(" ");
}

// A game is first to 11, win by 2. Rejects impossible scores like 12-9, which
// could never occur because the game would have ended at 11-9.
export function gameFinished(a, b) {
  const hi = Math.max(a, b), lo = Math.min(a, b);
  return (hi === 11 && lo <= 9) || (hi > 11 && hi - lo === 2);
}

// A match is won by whoever wins more games. No fixed best-of-N; a tie is not
// a finished match.
export function matchResult(scores) {
  let wonA = 0, wonB = 0;
  for (const [a, b] of scores) (a > b ? wonA++ : wonB++);
  return { wonA, wonB, winnerIsA: wonA > wonB, drawn: wonA === wonB };
}

export function kFactor(gamesPlayed) {
  if (gamesPlayed < 10) return 40;
  if (gamesPlayed < 20) return 20;
  return 10;
}

// Elo, applied once per match. The margin is deliberately ignored: only who won.
export function eloChange(eloA, eloB, kA, kB, aWon) {
  const expA = 1 / (1 + 10 ** ((eloB - eloA) / 400));
  const expB = 1 / (1 + 10 ** ((eloA - eloB) / 400));
  const sA = aWon ? 1 : 0;
  return [eloA + kA * (sA - expA), eloB + kB * ((1 - sA) - expB)];
}

// --- request validation -----------------------------------------------------

class BadRequest extends Error {}

function cleanNames(payload) {
  const names = [];
  for (const key of ["player_a", "player_b"]) {
    const name = payload[key];
    if (typeof name !== "string" || !name.trim()) throw new BadRequest(`${key} is required`);
    if (name.trim().length > MAX_NAME) throw new BadRequest(`${key} is too long`);
    names.push(displayName(name));
  }
  if (canonicalName(names[0]) === canonicalName(names[1])) {
    throw new BadRequest("the two players must be different");
  }
  return names;
}

function cleanScores(payload) {
  const games = payload.games;
  if (!Array.isArray(games) || games.length === 0) throw new BadRequest("at least one game is required");
  if (games.length > MAX_GAMES) throw new BadRequest(`at most ${MAX_GAMES} games`);
  return games.map((pair, i) => {
    const n = i + 1;
    if (!Array.isArray(pair) || pair.length !== 2) throw new BadRequest(`game ${n}: need two scores`);
    for (const s of pair) {
      if (!Number.isInteger(s) || s < 0 || s > MAX_POINTS) {
        throw new BadRequest(`game ${n}: scores must be whole numbers`);
      }
    }
    if (!gameFinished(pair[0], pair[1])) {
      throw new BadRequest(`game ${n}: ${pair[0]}-${pair[1]} is not a finished game`);
    }
    return pair;
  });
}

function validCode(code) {
  return typeof code === "string" && /^[0-9]{4}$/.test(code);
}

// --- storage ----------------------------------------------------------------

// Checks both codes, then returns the spelling each player is registered under.
// All-or-nothing: everyone existing is verified before anyone new is written,
// so a rejected match never leaves a code behind for a name never used.
async function resolvePlayers(db, names, codes) {
  names.forEach((name, i) => {
    if (!validCode(codes[i])) throw new BadRequest(`${name} needs a 4-digit code`);
  });

  const keys = names.map(canonicalName);
  const rows = await db.prepare(
    "SELECT name_key, display, code FROM codes WHERE name_key IN (?1, ?2)"
  ).bind(keys[0], keys[1]).all();
  const existing = new Map(rows.results.map(r => [r.name_key, r]));

  for (let i = 0; i < names.length; i++) {
    const row = existing.get(keys[i]);
    if (row && row.code !== codes[i]) throw new BadRequest(`wrong code for ${names[i]}`);
  }

  const registered = new Date().toISOString();
  const inserts = [];
  const display = [];
  for (let i = 0; i < names.length; i++) {
    const row = existing.get(keys[i]);
    if (row) {
      display.push(row.display);
    } else {
      display.push(names[i]);
      inserts.push(db.prepare(
        "INSERT INTO codes (name_key, display, code, registered) VALUES (?, ?, ?, ?)"
      ).bind(keys[i], names[i], codes[i], registered));
    }
  }
  if (inserts.length) await db.batch(inserts);
  return display;
}

async function loadPlayer(db, table, display) {
  const key = canonicalName(display);
  const row = await db.prepare(
    "SELECT display, elo, k_fac, games_played FROM players WHERE table_name = ? AND name_key = ?"
  ).bind(table, key).first();
  return row ?? { display, elo: 1000, k_fac: 40, games_played: 0 };
}

// --- routes -----------------------------------------------------------------

function json(body, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8", "Cache-Control": "no-store" },
  });
}

function requireTable(url) {
  const table = url.searchParams.get("table");
  if (!TABLES.includes(table)) throw new BadRequest("pick one of the tables");
  return table;
}

// change_24h sums each player's elo_change over matches in the last 24 hours,
// null when they have not played in that window. played_at is ISO-8601 UTC,
// so comparing strings compares times.
async function getLeaderboard(db, table) {
  const since = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString();
  const { results } = await db.prepare(
    `SELECT p.display, p.elo, p.games_played,
            (SELECT SUM(CASE WHEN m.player_a = p.display THEN m.elo_change_a ELSE m.elo_change_b END)
               FROM matches m
              WHERE m.table_name = p.table_name AND m.played_at >= ?2
                AND (m.player_a = p.display OR m.player_b = p.display)) AS change_24h
       FROM players p WHERE p.table_name = ?1 ORDER BY p.elo DESC, p.display ASC`
  ).bind(table, since).all();
  return results.map((r, i) => ({
    rank: i + 1,
    name: r.display,
    elo: Math.round(r.elo * 100) / 100,
    games_played: r.games_played,
    change_24h: r.change_24h == null ? null : Math.round(r.change_24h * 100) / 100,
  }));
}

// h2h_a / h2h_b are each side's all-time match wins against the other at this
// table, as it stands now (not as it stood when the match was played).
async function getMatches(db, table, limit = 10) {
  const wins = side => `(SELECT COUNT(*) FROM matches x
              WHERE x.table_name = m.table_name AND x.winner = m.${side}
                AND ((x.player_a = m.player_a AND x.player_b = m.player_b)
                  OR (x.player_a = m.player_b AND x.player_b = m.player_a)))`;
  const { results } = await db.prepare(
    `SELECT player_a, player_b, winner, games_won_a, games_won_b, games, played_at,
            ${wins("player_a")} AS h2h_a, ${wins("player_b")} AS h2h_b
       FROM matches m WHERE table_name = ? ORDER BY id DESC LIMIT ?`
  ).bind(table, limit).all();
  return results.map(r => ({ ...r, games: JSON.parse(r.games) }));
}

// Every match between two players at a table, newest first. Takes the
// registered display names (as the leaderboard lists them), which is what
// matches stores - same join getLeaderboard uses.
// ponytail: unbounded, fine while a pair has hundreds of matches, not millions
async function getHeadToHead(db, table, url) {
  const a = url.searchParams.get("a") ?? "";
  const b = url.searchParams.get("b") ?? "";
  if (!a || !b || a === b) throw new BadRequest("pick two different players");
  const { results } = await db.prepare(
    `SELECT player_a, player_b, winner, games_won_a, games_won_b, games, played_at
       FROM matches
      WHERE table_name = ?1
        AND ((player_a = ?2 AND player_b = ?3) OR (player_a = ?3 AND player_b = ?2))
      ORDER BY id DESC`
  ).bind(table, a, b).all();
  return results.map(r => ({ ...r, games: JSON.parse(r.games) }));
}

async function recordMatch(db, payload) {
  if (typeof payload !== "object" || payload === null || Array.isArray(payload)) {
    throw new BadRequest("expected a json object");
  }
  const table = payload.table;
  if (!TABLES.includes(table)) throw new BadRequest("pick one of the tables");

  const names = cleanNames(payload);
  const scores = cleanScores(payload);
  const { wonA, wonB, winnerIsA, drawn } = matchResult(scores);
  if (drawn) throw new BadRequest("the match is a draw, so there is no winner");

  // codes before anything is written, so a wrong one changes nothing
  const [displayA, displayB] = await resolvePlayers(db, names, [payload.pin_a, payload.pin_b]);

  const a = await loadPlayer(db, table, displayA);
  const b = await loadPlayer(db, table, displayB);
  const [newA, newB] = eloChange(a.elo, b.elo, a.k_fac, b.k_fac, winnerIsA);

  // games first, then k from the new count - so this match used the k they
  // came in with, and the new k applies to the next one
  const playedA = a.games_played + 1;
  const playedB = b.games_played + 1;
  const winner = winnerIsA ? displayA : displayB;

  const upsert = `
    INSERT INTO players (table_name, name_key, display, elo, k_fac, games_played)
    VALUES (?1, ?2, ?3, ?4, ?5, ?6)
    ON CONFLICT (table_name, name_key)
    DO UPDATE SET elo = ?4, k_fac = ?5, games_played = ?6`;

  await db.batch([
    db.prepare(upsert).bind(table, canonicalName(displayA), displayA, newA, kFactor(playedA), playedA),
    db.prepare(upsert).bind(table, canonicalName(displayB), displayB, newB, kFactor(playedB), playedB),
    db.prepare(
      `INSERT INTO matches
         (table_name, player_a, player_b, winner, games_won_a, games_won_b, games, played_at,
          elo_change_a, elo_change_b)
       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`
    ).bind(table, displayA, displayB, winner, wonA, wonB, JSON.stringify(scores),
           new Date().toISOString(), newA - a.elo, newB - b.elo),
  ]);

  return {
    table,
    winner,
    games_won: [wonA, wonB],
    elo: { [displayA]: Math.round(newA * 100) / 100, [displayB]: Math.round(newB * 100) / 100 },
  };
}

// --- announcements -----------------------------------------------------------

const MAX_ANNOUNCEMENT = 2000;

// /admin and everything under it sits behind HTTP Basic Auth: the browser asks
// once, then sends the login with every /admin/* request, so the page script
// never handles the password. Any username; the password is the ADMIN_PASSWORD
// secret (wrangler secret put ADMIN_PASSWORD). Hashing both sides gives equal
// lengths, which timingSafeEqual requires.
async function isAdmin(request, env) {
  const header = request.headers.get("Authorization") ?? "";
  if (!env.ADMIN_PASSWORD || !header.startsWith("Basic ")) return false;
  let given;
  try {
    const decoded = new TextDecoder().decode(
      Uint8Array.from(atob(header.slice(6)), c => c.charCodeAt(0)));
    given = decoded.slice(decoded.indexOf(":") + 1);
  } catch {
    return false;
  }
  const enc = new TextEncoder();
  const [a, b] = await Promise.all([given, env.ADMIN_PASSWORD].map(
    v => crypto.subtle.digest("SHA-256", enc.encode(v))));
  return crypto.subtle.timingSafeEqual(a, b);
}

function askForLogin() {
  return new Response("Password required", {
    status: 401,
    headers: { "WWW-Authenticate": 'Basic realm="NPPU admin", charset="UTF-8"', "Cache-Control": "no-store" },
  });
}

async function getAnnouncements(db) {
  const { results } = await db.prepare(
    "SELECT id, body, posted_at FROM announcements ORDER BY id DESC LIMIT 20"
  ).all();
  return results;
}

function cleanAnnouncement(payload) {
  const body = typeof payload?.body === "string" ? payload.body.trim() : "";
  if (!body) throw new BadRequest("write something first");
  if (body.length > MAX_ANNOUNCEMENT) throw new BadRequest("announcement too long");
  return body;
}

// Who plays where, with their code - for when someone forgets theirs.
// Codes are per person, so the same code shows under every table they play at.
async function getCodes(db) {
  const { results } = await db.prepare(
    `SELECT p.table_name, c.display, c.code FROM players p
       JOIN codes c ON c.name_key = p.name_key
      ORDER BY p.table_name, c.display COLLATE NOCASE`
  ).all();
  const tables = Object.fromEntries(TABLES.map(t => [t, []]));
  for (const r of results) tables[r.table_name]?.push({ name: r.display, code: r.code });
  return { tables };
}

async function handleAdmin(request, env, url) {
  if (!(await isAdmin(request, env))) return askForLogin();
  const db = env.DB;
  const path = url.pathname;
  const id = Number(url.searchParams.get("id"));

  if (request.method === "GET" && (path === "/admin" || path === "/admin/")) {
    return new Response(ADMIN_PAGE, {
      headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store",
                 "X-Robots-Tag": "noindex" },
    });
  }
  if (request.method === "GET" && path === "/admin/api/codes") {
    return json(await getCodes(db));
  }
  if (path === "/admin/api/announcements") {
    if (request.method === "POST") {
      const body = cleanAnnouncement(await readJson(request));
      await db.prepare("INSERT INTO announcements (body, posted_at) VALUES (?, ?)")
        .bind(body, new Date().toISOString()).run();
      return json({ ok: true });
    }
    if (request.method === "PUT") {
      const body = cleanAnnouncement(await readJson(request));
      await db.prepare("UPDATE announcements SET body = ? WHERE id = ?").bind(body, id).run();
      return json({ ok: true });
    }
    if (request.method === "DELETE") {
      await db.prepare("DELETE FROM announcements WHERE id = ?").bind(id).run();
      return json({ ok: true });
    }
  }
  return json({ error: "not found" }, 404);
}

async function readJson(request) {
  const raw = await request.text();
  if (raw.length > MAX_BODY) throw new BadRequest("request too large");
  try {
    return JSON.parse(raw);
  } catch {
    throw new BadRequest("body is not valid json");
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const isAdminPath = url.pathname === "/admin" || url.pathname.startsWith("/admin/");
    if (!isAdminPath && !url.pathname.startsWith("/api/")) {
      return env.ASSETS.fetch(request);   // static files
    }

    try {
      if (isAdminPath) return await handleAdmin(request, env, url);
      if (request.method === "GET" && url.pathname === "/api/tables") {
        return json({ tables: TABLES });
      }
      if (request.method === "GET" && url.pathname === "/api/leaderboard") {
        return json(await getLeaderboard(env.DB, requireTable(url)));
      }
      if (request.method === "GET" && url.pathname === "/api/matches") {
        return json({ matches: await getMatches(env.DB, requireTable(url)) });
      }
      if (request.method === "GET" && url.pathname === "/api/h2h") {
        return json({ matches: await getHeadToHead(env.DB, requireTable(url), url) });
      }
      if (request.method === "POST" && url.pathname === "/api/match") {
        return json(await recordMatch(env.DB, await readJson(request)));
      }
      if (request.method === "GET" && url.pathname === "/api/announcements") {
        return json({ announcements: await getAnnouncements(env.DB) });
      }
      return json({ error: "not found" }, 404);
    } catch (err) {
      if (err instanceof BadRequest) return json({ error: err.message }, 400);
      return json({ error: "something went wrong saving that" }, 500);
    }
  },
};
