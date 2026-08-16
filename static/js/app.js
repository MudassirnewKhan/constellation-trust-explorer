const searchInput = document.getElementById("search-input");
const searchResults = document.getElementById("search-results");
const emptyState = document.getElementById("empty-state");
const userDetail = document.getElementById("user-detail");

let searchDebounce = null;

searchInput.addEventListener("input", () => {
  clearTimeout(searchDebounce);
  const q = searchInput.value.trim();
  if (q.length < 2) {
    searchResults.classList.remove("visible");
    return;
  }
  searchDebounce = setTimeout(() => runSearch(q), 200);
});

document.addEventListener("click", (e) => {
  if (!searchResults.contains(e.target) && e.target !== searchInput) {
    searchResults.classList.remove("visible");
  }
});

async function runSearch(q) {
  try {
    const res = await fetch(`/api/search?q=${encodeURIComponent(q)}`);
    const data = await res.json();
    if (data.error) {
      searchResults.innerHTML = `<div class="search-result-item">${escapeHtml(data.error)}</div>`;
      searchResults.classList.add("visible");
      return;
    }
    if (!data.results.length) {
      searchResults.innerHTML = `<div class="search-result-item">No matches.</div>`;
      searchResults.classList.add("visible");
      return;
    }
    searchResults.innerHTML = data.results
      .map(
        (u) => `<div class="search-result-item" data-id="${u.id}">
                   <span>${escapeHtml(u.name)}</span>
                   <span class="id">#${u.id}</span>
                 </div>`
      )
      .join("");
    searchResults.classList.add("visible");

    searchResults.querySelectorAll(".search-result-item[data-id]").forEach((el) => {
      el.addEventListener("click", () => {
        loadUser(el.dataset.id);
        searchResults.classList.remove("visible");
        searchInput.value = el.querySelector("span").textContent;
      });
    });
  } catch (err) {
    console.error(err);
  }
}

async function loadUser(userId) {
  try {
    const res = await fetch(`/api/user/${userId}`);
    const data = await res.json();
    if (data.error) {
      alert(data.error);
      return;
    }

    emptyState.classList.add("hidden");
    userDetail.classList.remove("hidden");

    document.getElementById("user-name").textContent = data.user.name;
    document.getElementById("user-id").textContent = `#${data.user.id}`;

    document.getElementById("trusts-count").textContent = data.trusts.length;
    document.getElementById("trusted-by-count").textContent = data.trusted_by.length;

    renderNodeList("trusts-list", data.trusts);
    renderNodeList("trusted-by-list", data.trusted_by);
    renderNodeList("suggestions-list", data.suggestions, true);
  } catch (err) {
    console.error(err);
  }
}

function renderNodeList(elId, items, showMutual = false) {
  const el = document.getElementById(elId);
  if (!items.length) {
    el.innerHTML = `<li style="cursor:default; opacity:0.6;">— none —</li>`;
    return;
  }
  el.innerHTML = items
    .map(
      (u) => `<li data-id="${u.id}">
                <span>${escapeHtml(u.name)}</span>
                ${showMutual && u.mutual_paths ? `<span class="mutual">${u.mutual_paths} mutual</span>` : ""}
              </li>`
    )
    .join("");
  el.querySelectorAll("li[data-id]").forEach((li) => {
    li.addEventListener("click", () => loadUser(li.dataset.id));
  });
}

// ---- Path tracing ----
const pathForm = document.getElementById("path-form");
const pathResult = document.getElementById("path-result");

pathForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const from = document.getElementById("path-from").value;
  const to = document.getElementById("path-to").value;

  pathResult.innerHTML = `<div class="path-empty">Tracing…</div>`;

  try {
    const res = await fetch(`/api/path?from=${from}&to=${to}`);
    const data = await res.json();

    if (data.error) {
      pathResult.innerHTML = `<div class="path-error">${escapeHtml(data.error)}</div>`;
      return;
    }
    if (!data.path) {
      pathResult.innerHTML = `<div class="path-empty">${escapeHtml(data.message || "No trust path found.")}</div>`;
      return;
    }

    const chain = data.path
      .map((n) => `<span class="path-node">${escapeHtml(n.name)}</span>`)
      .join(`<span class="path-link">✦→</span>`);

    pathResult.innerHTML = `
      <div class="path-chain">${chain}</div>
      <div class="path-hops">${data.hops} hop${data.hops === 1 ? "" : "s"} of trust</div>
    `;
  } catch (err) {
    pathResult.innerHTML = `<div class="path-error">Something went wrong tracing that path.</div>`;
  }
});

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}
