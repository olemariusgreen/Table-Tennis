// Shared by table.html, leaderboard.html and record.html:
// which table are we on, its photo, its data, and the top tab bar.

function tableSlug(name) {
  // must match table_dir() in rating/json_helpers.py
  return name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
}

// Stand-in until every table has been photographed.
const FALLBACK_PHOTO = "/assets/tentative-picture.jpg";

// Returns a background-image with the table's own photo layered ON TOP of the
// stand-in. A table with no file of its own simply does not paint its layer,
// so the stand-in shows through - and the moment you drop
// assets/tables/<slug>.jpg in, it takes over with no other change.
function tablePhoto(table) {
  return `url("/assets/tables/${tableSlug(table)}.jpg"), url("${FALLBACK_PHOTO}")`;
}

// Reads ?table= and checks it against the server's own list, so a hand-edited
// or stale url cannot point at a table that does not exist.
async function requireTable() {
  const wanted = new URLSearchParams(location.search).get("table");
  let tables;
  try {
    ({ tables } = await fetch("/api/tables", { cache: "no-store" }).then(r => r.json()));
  } catch {
    document.querySelector("main").innerHTML =
      '<p class="error">Could not reach the server. Is it running?</p>';
    return null;
  }
  if (!tables.includes(wanted)) {
    document.querySelector("main").innerHTML =
      '<p class="error">Unknown table. <a href="index.html">Pick one</a>.</p>';
    return null;
  }
  return wanted;
}

// Points the tab bar's links at this table and underlines the current page.
// The markup is static in each page so the bar paints immediately.
// Omit `active` on the table landing page: none of the tabs is that page,
// and the hero already names where you are.
function setupNav(table, active) {
  const query = "?table=" + encodeURIComponent(table);
  for (const [name, href] of [
    ["nav-board", "leaderboard.html" + query],
    ["nav-record", "record.html" + query],
  ]) {
    const link = document.getElementById(name);
    if (!link) continue;
    link.href = href;
    if (name === "nav-" + active) link.classList.add("active");
  }
}

// The leaderboard and the match list are queries now, not stored files.
async function apiGet(path, table) {
  try {
    const url = `/api/${path}?table=${encodeURIComponent(table)}`;
    const response = await fetch(url, { cache: "no-store" });
    return response.ok ? await response.json() : null;
  } catch {
    return null;
  }
}

