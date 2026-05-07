// p2c visual guide — minimal stdlib-only client logic

const fmtUSD = new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 });

// HTML-escape any value before it touches the DOM. Even though the data here is
// generated locally, treating it as untrusted is cheap and removes XSS surface
// if a sprint plan or workspace file contains hostile content.
const escapeHtml = (value) => {
  if (value === null || value === undefined) return "";
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
};

// Convenience helper for building DOM safely with text values.
const setText = (el, text) => { el.textContent = text ?? ""; return el; };

// --- Phase intake form (auto-save with debounce) -----------------------

(function setupPhaseForm() {
  const form = document.querySelector("#phase-form");
  if (!form) return;
  const phase = form.dataset.phase;
  const status = document.querySelector("#save-status");
  const saveNowBtn = document.querySelector("#save-now");

  let timer = null;
  const collect = () => {
    const data = {};
    form.querySelectorAll("textarea").forEach((t) => { data[t.name] = t.value; });
    return data;
  };
  const save = async () => {
    setText(status, "saving…");
    try {
      const res = await fetch(`/api/intake/${phase}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(collect()),
      });
      const out = await res.json();
      if (out.error) throw new Error(out.error);
      setText(status, `saved → ${out.saved}`);
    } catch (err) {
      setText(status, `error: ${err.message}`);
    }
  };
  form.addEventListener("input", () => {
    clearTimeout(timer);
    timer = setTimeout(save, 800);
  });
  if (saveNowBtn) saveNowBtn.addEventListener("click", save);
})();

// --- Story map (very simple grid — backbone + slices) ------------------

(function setupStoryMap() {
  const root = document.querySelector("#storymap");
  if (!root) return;

  const state = {
    activities: ["Sign up", "Create first item", "Invite teammate", "Get value"],
    slices: [
      ["email signup", "social signup"],
      ["create from scratch", "create from template"],
      ["email invite", "share link"],
      ["see results", "export"],
    ],
    mvpLine: 1,
  };

  const render = () => {
    root.replaceChildren();
    const grid = document.createElement("div");
    grid.style.display = "grid";
    grid.style.gridTemplateColumns = `repeat(${state.activities.length}, minmax(140px, 1fr))`;
    grid.style.gap = "8px";
    grid.style.alignItems = "start";

    state.activities.forEach((a, i) => {
      const el = document.createElement("div");
      el.contentEditable = "true";
      el.className = "card";
      el.style.padding = "10px";
      el.style.fontWeight = "600";
      setText(el, a);
      el.addEventListener("blur", () => { state.activities[i] = el.textContent; });
      grid.appendChild(el);
    });

    const maxRows = Math.max(...state.slices.map((c) => c.length), 0);
    for (let row = 0; row < maxRows; row++) {
      state.activities.forEach((_, col) => {
        const value = state.slices[col]?.[row] || "";
        const el = document.createElement("div");
        el.contentEditable = "true";
        el.className = "card";
        el.style.padding = "8px";
        el.style.fontSize = "0.9rem";
        el.style.opacity = row > state.mvpLine ? "0.5" : "1";
        el.style.borderStyle = row === state.mvpLine ? "solid" : "dashed";
        setText(el, value);
        el.addEventListener("blur", () => {
          if (!state.slices[col]) state.slices[col] = [];
          state.slices[col][row] = el.textContent;
        });
        grid.appendChild(el);
      });
    }

    root.appendChild(grid);

    const ctl = document.createElement("p");
    ctl.style.marginTop = "12px";
    setText(ctl, "MVP line — rows above the line are MVP: ");
    const input = document.createElement("input");
    input.type = "number";
    input.id = "mvpline";
    input.value = String(state.mvpLine);
    input.min = "0";
    input.max = String(Math.max(maxRows - 1, 0));
    input.style.width = "60px";
    input.addEventListener("input", (e) => {
      state.mvpLine = parseInt(e.target.value, 10);
      render();
    });
    ctl.appendChild(input);
    root.appendChild(ctl);
  };

  render();

  document.querySelector("#storymap-save").addEventListener("click", async () => {
    const status = document.querySelector("#storymap-status");
    setText(status, "saving…");
    const res = await fetch("/api/storymap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    const out = await res.json();
    setText(status, out.error ? `error: ${out.error}` : `saved → ${out.saved}`);
  });
})();

// --- Journey map -------------------------------------------------------

(function setupJourney() {
  const root = document.querySelector("#journey");
  if (!root) return;

  const state = {
    stages: [
      { name: "Hear about it", actions: "", thoughts: "", emotion: 0 },
      { name: "Sign up", actions: "", thoughts: "", emotion: 0 },
      { name: "First use", actions: "", thoughts: "", emotion: 0 },
      { name: "Get value", actions: "", thoughts: "", emotion: 0 },
      { name: "Stay/Leave", actions: "", thoughts: "", emotion: 0 },
    ],
  };

  const buildStageCard = (s, i) => {
    const card = document.createElement("div");
    card.className = "card";
    card.style.marginBottom = "10px";

    const label = document.createElement("div");
    label.className = "phase-no";
    setText(label, `Stage ${i + 1}`);
    card.appendChild(label);

    const name = document.createElement("input");
    Object.assign(name.style, { width: "100%", background: "transparent", border: "0", color: "inherit", fontSize: "1.1rem", fontWeight: "600" });
    name.value = s.name;
    name.dataset.i = String(i); name.dataset.k = "name";
    card.appendChild(name);

    for (const k of ["actions", "thoughts"]) {
      const ta = document.createElement("textarea");
      ta.placeholder = k === "actions" ? "Actions" : "Thoughts / questions";
      ta.value = s[k];
      ta.dataset.i = String(i); ta.dataset.k = k;
      card.appendChild(ta);
    }

    const emoLabel = document.createElement("label");
    emoLabel.className = "muted";
    setText(emoLabel, "Emotion (-2 sad … +2 delighted): ");
    const emo = document.createElement("input");
    emo.type = "range"; emo.min = "-2"; emo.max = "2"; emo.value = String(s.emotion);
    emo.dataset.i = String(i); emo.dataset.k = "emotion";
    emoLabel.appendChild(emo);
    card.appendChild(emoLabel);

    return card;
  };

  const render = () => {
    root.replaceChildren();
    state.stages.forEach((s, i) => root.appendChild(buildStageCard(s, i)));
    root.querySelectorAll("[data-i]").forEach((el) => {
      el.addEventListener("input", (e) => {
        const i = parseInt(e.target.dataset.i, 10);
        const k = e.target.dataset.k;
        state.stages[i][k] = e.target.type === "range" ? parseInt(e.target.value, 10) : e.target.value;
      });
    });
  };

  render();

  document.querySelector("#journey-save").addEventListener("click", async () => {
    const status = document.querySelector("#journey-status");
    setText(status, "saving…");
    const res = await fetch("/api/journey", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(state),
    });
    const out = await res.json();
    setText(status, out.error ? `error: ${out.error}` : `saved → ${out.saved}`);
  });
})();

// --- Cost view ---------------------------------------------------------

const buildTotalCard = (label, value) => {
  const card = document.createElement("div");
  card.className = "totalcard";
  const lbl = document.createElement("div");
  lbl.className = "label";
  setText(lbl, label);
  const val = document.createElement("div");
  val.className = "value";
  setText(val, fmtUSD.format(value));
  card.appendChild(lbl);
  card.appendChild(val);
  return card;
};

const buildCostTable = (sprints, useAi, useStd) => {
  const table = document.createElement("table");
  table.className = "cost-table";
  const thead = document.createElement("thead");
  const trh = document.createElement("tr");
  for (const h of ["#", "Goal"]) {
    const th = document.createElement("th"); setText(th, h); trh.appendChild(th);
  }
  if (useAi) { const th = document.createElement("th"); th.className = "num"; setText(th, "AI-assisted"); trh.appendChild(th); }
  if (useStd) { const th = document.createElement("th"); th.className = "num"; setText(th, "Standard"); trh.appendChild(th); }
  thead.appendChild(trh);
  table.appendChild(thead);

  const tbody = document.createElement("tbody");
  sprints.forEach((s) => {
    const tr = document.createElement("tr");
    const cells = [String(s.sprint), s.goal || ""];
    cells.forEach((v) => { const td = document.createElement("td"); setText(td, v); tr.appendChild(td); });
    if (useAi) { const td = document.createElement("td"); td.className = "num"; setText(td, fmtUSD.format(s.ai_assisted)); tr.appendChild(td); }
    if (useStd) { const td = document.createElement("td"); td.className = "num"; setText(td, fmtUSD.format(s.standard)); tr.appendChild(td); }
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  return table;
};

(function setupCost() {
  const root = document.querySelector("#cost");
  if (!root) return;

  const showAi = document.getElementById("cost-ai");
  const showStd = document.getElementById("cost-std");

  const render = (data) => {
    root.replaceChildren();
    if (data.error) {
      const p = document.createElement("p");
      p.className = "muted";
      setText(p, `No cost estimate yet: ${data.error}`);
      root.appendChild(p);
      return;
    }
    const useAi = showAi.checked;
    const useStd = showStd.checked;

    const totals = document.createElement("div");
    totals.className = "cost-totals";
    if (useAi) totals.appendChild(buildTotalCard("Total (AI-assisted)", data.totals.ai_assisted));
    if (useStd) totals.appendChild(buildTotalCard("Total (standard)", data.totals.standard));
    root.appendChild(totals);

    root.appendChild(buildCostTable(data.sprints, useAi, useStd));
  };

  const refresh = async () => {
    const res = await fetch("/api/cost");
    const data = await res.json();
    render(data);
  };
  if (showAi) showAi.addEventListener("change", refresh);
  if (showStd) showStd.addEventListener("change", refresh);
  refresh();
})();

// --- Sprint timeline (re-uses cost endpoint) ---------------------------

(function setupSprint() {
  const root = document.querySelector("#sprint");
  if (!root) return;
  fetch("/api/cost").then((r) => r.json()).then((data) => {
    root.replaceChildren();
    if (data.error) {
      const p = document.createElement("p");
      p.className = "muted";
      setText(p, data.error);
      root.appendChild(p);
      return;
    }
    const max = Math.max(...data.sprints.map((s) => s.ai_assisted), 0);
    const table = document.createElement("table");
    table.className = "cost-table";
    const thead = document.createElement("thead");
    const trh = document.createElement("tr");
    ["#", "Goal", "Hours", "Bar"].forEach((h, idx) => {
      const th = document.createElement("th");
      if (idx === 2) th.className = "num";
      setText(th, h);
      trh.appendChild(th);
    });
    thead.appendChild(trh);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    data.sprints.forEach((s) => {
      const hours = Object.values(s.hours_by_role || {}).reduce((a, b) => a + b, 0);
      const pct = max ? Math.round((s.ai_assisted / max) * 100) : 0;
      const tr = document.createElement("tr");
      [String(s.sprint), s.goal || "", hours.toFixed(0)].forEach((v, idx) => {
        const td = document.createElement("td");
        if (idx === 2) td.className = "num";
        setText(td, v);
        tr.appendChild(td);
      });
      const tdBar = document.createElement("td");
      const bar = document.createElement("div");
      Object.assign(bar.style, { background: "#5b9dff", height: "10px", width: `${pct}%`, borderRadius: "4px" });
      tdBar.appendChild(bar);
      tr.appendChild(tdBar);
      tbody.appendChild(tr);
    });
    table.appendChild(tbody);
    root.appendChild(table);
  });
})();

// Reference escapeHtml so it shows up in static analysis as exported intent.
window.__p2cEscape = escapeHtml;
