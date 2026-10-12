/* pxEnrich frontend — vanilla JS, no build step.
   Talks to the read-only API; renders evidence cards whose labels open into
   "receipts" showing the exact supporting text, source, scope, and confidence. */

(function () {
  "use strict";

  const $ = (sel, el) => (el || document).querySelector(sel);
  const state = { q: "", audience: "plain", topics: [] };

  const FIELD_NAMES = {
    disease_context: "disease",
    subtype: "subtype",
    er_status: "ER",
    pr_status: "PR",
    her2_status: "HER2",
    sample_type: "sample",
    organism_context: "source material",
    treatment_context: "treatment",
  };

  const STATUS_PHRASE = {
    asserted: v => v,
    unknown: () => "unknown",
    mixed: v => "mixed: " + v,
    conflicting: () => "conflicting",
    abstained: () => "not labeled (see why)",
    not_evaluable: () => "not applicable",
  };

  function esc(s) {
    const d = document.createElement("div");
    d.textContent = s == null ? "" : String(s);
    return d.innerHTML;
  }

  async function getJSON(url) {
    const r = await fetch(url);
    if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error || r.statusText);
    return r.json();
  }

  /* ---------- topics ---------- */
  async function loadTopics() {
    try {
      const data = await getJSON("/api/topics");
      const holder = $("#topic-chips");
      holder.innerHTML = "";
      data.topics
        .filter(t => t.count > 0)
        .forEach(t => {
          const b = document.createElement("button");
          b.className = "chip";
          b.innerHTML = esc(t.topic.replace(/-/g, " ")) +
            ' <span class="n">' + t.count + "</span>";
          b.addEventListener("click", () => {
            state.topics = [t.topic];
            state.q = "";
            $("#q").value = "";
            runSearch();
          });
          holder.appendChild(b);
        });
    } catch (e) { /* topics are progressive enhancement */ }
  }

  /* ---------- search ---------- */
  async function runSearch() {
    const results = $("#results");
    results.hidden = false;
    $("#answer-card").innerHTML = '<p class="loading">Searching the evidence index…</p>';
    $("#cards").innerHTML = "";
    results.scrollIntoView({ behavior: "smooth", block: "start" });

    const params = new URLSearchParams();
    if (state.q) params.set("q", state.q);
    if (state.topics.length) params.set("topics", state.topics.join(","));
    params.set("audience", state.audience);
    params.set("limit", "12");

    try {
      const data = await getJSON("/api/search?" + params.toString());
      renderAnswer(data);
      renderCards(data.records);
    } catch (e) {
      $("#answer-card").innerHTML =
        "<p>Search didn’t complete: " + esc(e.message) +
        ". Check that the API server is running, then try again.</p>";
    }
  }

  function renderAnswer(data) {
    const a = data.answer;
    const card = $("#answer-card");
    card.classList.toggle("empty", a.status !== "ok");
    let html = "<p>" + esc(a.answer) + "</p>";
    if (a.status === "ok") {
      html += '<p class="answer-meta">' + data.total_matches +
        " matching dataset" + (data.total_matches === 1 ? "" : "s") +
        " · answer mode: " +
        (a.mode === "llm_grounded" ? "AI narrative grounded in the records below"
                                   : "built directly from the records below") +
        "</p>";
    }
    card.innerHTML = html;
    $("#answer-title").textContent =
      state.q ? "Answer" : "Browsing: " + state.topics.join(", ").replace(/-/g, " ");
  }

  /* ---------- evidence cards ---------- */
  function renderCards(records) {
    const holder = $("#cards");
    holder.innerHTML = "";
    records.forEach(rec => holder.appendChild(datasetCard(rec)));
  }

  function datasetCard(rec) {
    const card = document.createElement("article");
    card.className = "ds-card";

    const year = (rec.announce_date || "").slice(0, 4);
    card.innerHTML =
      '<h3 class="ds-title"><a href="' + esc(rec.px_link) +
      '" rel="noopener" target="_blank">' + esc(rec.title) + "</a></h3>" +
      '<p class="ds-meta">' + esc(rec.accession) +
      '<span class="sep">·</span>' + esc(rec.repository) +
      (year ? '<span class="sep">·</span>' + esc(year) : "") +
      (rec.instrument ? '<span class="sep">·</span>' + esc(rec.instrument) : "") +
      "</p>";

    const labels = document.createElement("div");
    labels.className = "labels";

    const order = ["organism_context", "sample_type", "subtype", "er_status",
                   "pr_status", "her2_status", "treatment_context", "disease_context"];
    const asserts = (rec.assertions || []).slice()
      .sort((x, y) => order.indexOf(x.field) - order.indexOf(y.field));

    asserts.forEach(a => {
      // keep cards scannable: hide unknowns except for the headline fields
      const headline = ["subtype", "sample_type", "organism_context"];
      if (a.status === "unknown" && !headline.includes(a.field)) return;

      const btn = document.createElement("button");
      btn.className = "label st-" + a.status;
      const phrase = STATUS_PHRASE[a.status] || (v => v);
      btn.innerHTML = "<span>" + esc(FIELD_NAMES[a.field] || a.field) + ": " +
        esc(phrase(a.value)) + "</span>";
      btn.setAttribute("aria-expanded", "false");
      btn.addEventListener("click", () => toggleReceipt(card, btn, rec, a));
      labels.appendChild(btn);
    });
    card.appendChild(labels);

    const links = document.createElement("p");
    links.className = "ds-links";
    let lh = '<a href="' + esc(rec.px_link) + '" rel="noopener" target="_blank">ProteomeXchange record</a>';
    if (rec.repo_link) lh += '<a href="' + esc(rec.repo_link) + '" rel="noopener" target="_blank">' + esc(rec.repository) + " record</a>";
    if (rec.pubmed_ids) {
      const pm = String(rec.pubmed_ids).split(";")[0].trim();
      lh += '<a href="https://pubmed.ncbi.nlm.nih.gov/' + esc(pm) + '/" rel="noopener" target="_blank">publication</a>';
    }
    links.innerHTML = lh;
    card.appendChild(links);
    return card;
  }

  function toggleReceipt(card, btn, rec, a) {
    const existing = card.querySelector(".receipt");
    const wasOpen = btn.classList.contains("open");
    card.querySelectorAll(".label.open").forEach(b => {
      b.classList.remove("open");
      b.setAttribute("aria-expanded", "false");
    });
    if (existing) existing.remove();
    if (wasOpen) return;

    btn.classList.add("open");
    btn.setAttribute("aria-expanded", "true");

    const r = document.createElement("div");
    r.className = "receipt";
    let html = "";
    if (a.evidence_text) {
      html += "<blockquote>" + esc(a.evidence_text) + "</blockquote>";
    }
    if (a.note) html += '<p class="r-row">' + esc(a.note) + "</p>";
    html += '<p class="r-row"><strong>Where this comes from:</strong> ' +
      esc(a.source_type || "no source recorded") +
      (a.scope === "study_focus"
        ? " — describes what the study is about, not a cohort status"
        : " — applies to the " + esc(a.scope).replace("_", " ")) + "</p>";
    html += '<p class="r-row"><strong>Extraction:</strong> ' + esc(a.extracted_by) +
      " · confidence " + Number(a.confidence).toFixed(2) + "</p>";
    if (!a.evidence_text && !a.note) {
      html = "<p class='r-row'>No statement about this was found in the public " +
        "record. Unknown means exactly that — not yes, not no.</p>" + html;
    }
    r.innerHTML = html;
    btn.closest(".ds-card").appendChild(r);
  }

  /* ---------- wiring ---------- */
  $("#search-form").addEventListener("submit", e => {
    e.preventDefault();
    const v = $("#q").value.trim();
    state.q = v || $("#q").placeholder;
    state.topics = [];
    runSearch();
  });

  document.querySelectorAll(".prompt").forEach(p => {
    p.addEventListener("click", () => {
      $("#q").value = p.textContent;
      state.q = p.textContent;
      state.topics = [];
      runSearch();
    });
  });

  document.querySelectorAll(".aud-btn").forEach(b => {
    b.addEventListener("click", () => {
      document.querySelectorAll(".aud-btn").forEach(x => x.classList.remove("active"));
      b.classList.add("active");
      state.audience = b.dataset.aud;
      if (state.q || state.topics.length) runSearch();
    });
  });

  loadTopics();
})();
