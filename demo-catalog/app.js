// Shared helpers for the demo catalog.

// Deterministic gradient per item, so each card gets a consistent color.
const GRADIENTS = [
  ["#6ea8fe", "#a06bff"],
  ["#3fb950", "#2dd4bf"],
  ["#f2c14e", "#f97362"],
  ["#f97362", "#a06bff"],
  ["#2dd4bf", "#6ea8fe"],
  ["#a06bff", "#f2c14e"],
];

function gradientFor(id) {
  let h = 0;
  for (let i = 0; i < id.length; i++) h = (h * 31 + id.charCodeAt(i)) >>> 0;
  const [a, b] = GRADIENTS[h % GRADIENTS.length];
  return `linear-gradient(135deg, ${a}, ${b})`;
}

function initials(name) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0])
    .join("")
    .toUpperCase();
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function getItem(id) {
  return (window.CATALOG_ITEMS || []).find((it) => it.id === id);
}

// ---------- Index page ----------
function renderIndex() {
  const grid = document.getElementById("grid");
  if (!grid) return;

  const items = window.CATALOG_ITEMS || [];
  const categories = ["All", ...Array.from(new Set(items.map((i) => i.category)))];

  const filterBar = document.getElementById("filters");
  const searchInput = document.getElementById("search");

  let activeCategory = "All";
  let query = "";

  // Build category chips
  filterBar.innerHTML = categories
    .map(
      (c) =>
        `<div class="chip${c === "All" ? " active" : ""}" data-cat="${escapeHtml(
          c
        )}">${escapeHtml(c)}</div>`
    )
    .join("");

  filterBar.addEventListener("click", (e) => {
    const chip = e.target.closest(".chip");
    if (!chip) return;
    activeCategory = chip.dataset.cat;
    filterBar.querySelectorAll(".chip").forEach((c) => c.classList.remove("active"));
    chip.classList.add("active");
    draw();
  });

  searchInput.addEventListener("input", () => {
    query = searchInput.value.trim().toLowerCase();
    draw();
  });

  function matches(item) {
    if (activeCategory !== "All" && item.category !== activeCategory) return false;
    if (!query) return true;
    const hay = [item.name, item.author, item.category, item.short, (item.tags || []).join(" ")]
      .join(" ")
      .toLowerCase();
    return hay.includes(query);
  }

  function draw() {
    const visible = items.filter(matches);
    if (visible.length === 0) {
      grid.innerHTML = `<div class="empty">Geen resultaten gevonden.</div>`;
      return;
    }
    grid.innerHTML = visible.map(cardHtml).join("");
  }

  function cardHtml(item) {
    const tags = (item.tags || [])
      .slice(0, 3)
      .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
      .join("");
    return `
      <a class="card" href="item.html?id=${encodeURIComponent(item.id)}">
        <div class="card-top">
          <div class="thumb" style="background:${gradientFor(item.id)}">${escapeHtml(
      initials(item.name)
    )}</div>
          <div>
            <h3>${escapeHtml(item.name)}</h3>
            <div class="meta">${escapeHtml(item.category)} · ${escapeHtml(item.author)}</div>
          </div>
        </div>
        <p class="desc">${escapeHtml(item.short)}</p>
        <div class="card-tags">${tags}</div>
        <div class="card-foot">
          <span class="rating">★ ${item.rating.toFixed(1)}</span>
          <span class="badge-free">${escapeHtml(item.price)}</span>
        </div>
      </a>`;
  }

  draw();
}

// ---------- Detail page ----------
function renderDetail() {
  const root = document.getElementById("detail");
  if (!root) return;

  const params = new URLSearchParams(location.search);
  const item = getItem(params.get("id"));

  if (!item) {
    root.innerHTML = `
      <a class="back-link" href="index.html">← Terug naar overzicht</a>
      <div class="empty">Dit item bestaat niet.</div>`;
    return;
  }

  document.title = `${item.name} — Demo Catalog`;

  const tags = (item.tags || [])
    .map((t) => `<span class="tag">${escapeHtml(t)}</span>`)
    .join(" ");

  root.innerHTML = `
    <a class="back-link" href="index.html">← Terug naar overzicht</a>
    <div class="detail-head">
      <div class="thumb" style="background:${gradientFor(item.id)}">${escapeHtml(
    initials(item.name)
  )}</div>
      <div>
        <h1>${escapeHtml(item.name)}</h1>
        <div class="sub">${escapeHtml(item.category)} · door ${escapeHtml(
    item.author
  )} · <span class="rating">★ ${item.rating.toFixed(1)}</span></div>
      </div>
      <div class="detail-actions">
        <button class="btn primary" onclick="alert('Dit is een demo — er wordt niets gedownload.')">Bekijk</button>
        <button class="btn" onclick="alert('Toegevoegd aan je favorieten (demo).')">♡ Bewaar</button>
      </div>
    </div>

    <div class="detail-grid">
      <div class="panel">
        <h2>Beschrijving</h2>
        <p>${escapeHtml(item.description)}</p>
        <div class="card-tags">${tags}</div>
      </div>
      <div class="panel">
        <h2>Informatie</h2>
        <div class="spec-row"><span class="k">Versie</span><span class="v">${escapeHtml(
          item.version
        )}</span></div>
        <div class="spec-row"><span class="k">Bijgewerkt</span><span class="v">${escapeHtml(
          item.updated
        )}</span></div>
        <div class="spec-row"><span class="k">Categorie</span><span class="v">${escapeHtml(
          item.category
        )}</span></div>
        <div class="spec-row"><span class="k">Auteur</span><span class="v">${escapeHtml(
          item.author
        )}</span></div>
        <div class="spec-row"><span class="k">Downloads</span><span class="v">${item.downloads.toLocaleString(
          "nl-NL"
        )}</span></div>
        <div class="spec-row"><span class="k">Prijs</span><span class="v badge-free">${escapeHtml(
          item.price
        )}</span></div>
      </div>
    </div>

    <p class="notice">Dit is een demonstratiepagina met fictieve, legale voorbeeld-inhoud.
    Er wordt geen software gehost of gedownload.</p>
  `;
}

document.addEventListener("DOMContentLoaded", () => {
  renderIndex();
  renderDetail();
});
