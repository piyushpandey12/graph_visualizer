// --- Predefined graphs ---
const defaultGraph = {
  nodes: ["A", "B", "C"],
  edges: [
    { source: "A", target: "B", weight: 6 },
    { source: "B", target: "C", weight: 4 },
    { source: "A", target: "C", weight: 10 }
  ]
};

const negativeEdgeGraph = {
  nodes: ["A", "B", "C"],
  edges: [
    { source: "A", target: "B", weight: 4 },
    { source: "B", target: "C", weight: -2 },
    { source: "A", target: "C", weight: 5 }
  ]
};

// --- Helpers ---
function parseNodes(text) {
  const nodes = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const parts = line.split(",").map(s => s.trim());
    const name = (parts[0] || "").toUpperCase();
    if (!name) continue;
    if (parts.length >= 3 && parts[1] !== "" && parts[2] !== "") {
      const x = Number(parts[1]);
      const y = Number(parts[2]);
      if (!Number.isNaN(x) && !Number.isNaN(y)) {
        nodes.push({ name, x, y });
        continue;
      }
    }
    nodes.push({ name });
  }
  return nodes;
}

function parseEdges(text) {
  const edges = [];
  for (const raw of text.split(/\r?\n/)) {
    const line = raw.trim();
    if (!line) continue;
    const [u, v, w] = line.split(",").map(s => s.trim());
    if (!u || !v) continue;
    const weight = Number(w ?? "1");
    edges.push({
      u: u.toUpperCase(),
      v: v.toUpperCase(),
      w: Number.isNaN(weight) ? 1 : weight
    });
  }
  return edges;
}

// --- Graph Mode Loader (for debug/logging) ---
function loadGraph(mode) {
  let graph;
  if (mode === "default") {
    graph = defaultGraph;
  } else if (mode === "negative_demo") {
    graph = negativeEdgeGraph;
  } else {
    graph = {
      nodes: parseNodes(document.getElementById("nodes").value),
      edges: parseEdges(document.getElementById("edges").value)
    };
  }
  console.log("Graph loaded:", graph);
  return graph;
}

// --- Run algorithm ---
async function run() {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  const algo = document.getElementById("algo").value;
  const src = document.getElementById("src").value.trim();
  const dst = document.getElementById("dst").value.trim();

  const payload = { mode, algo, src, dst };

  if (mode === "custom") {
    payload.nodes = parseNodes(document.getElementById("nodes").value);
    payload.edges = parseEdges(document.getElementById("edges").value);
  } 
  else if (mode === "default") {
    payload.nodes = [
      { name: "A" }, { name: "B" }, { name: "C" },
      { name: "D" }, { name: "E" }, { name: "F" }
    ];
    payload.edges = [
      { u: "A", v: "B", w: 2 },
      { u: "A", v: "D", w: 4 },
      { u: "B", v: "C", w: 2 },
      { u: "B", v: "E", w: 5 },
      { u: "C", v: "F", w: 3 },
      { u: "D", v: "E", w: 1 },
      { u: "E", v: "F", w: 2 }
    ];
  } 
  else if (mode === "negative_demo") {
    payload.nodes = [
      { name: "A" }, { name: "B" }, { name: "C" }, { name: "D" }
    ];
    payload.edges = [
      { u: "A", v: "B", w: 4 },
      { u: "A", v: "C", w: 5 },
      { u: "B", v: "C", w: -3 },
      { u: "C", v: "D", w: 2 },
      { u: "D", v: "B", w: 1 }
    ];
  }

  const resEl = document.getElementById("output");
  resEl.textContent = "Running...";

  try {
    const resp = await fetch("/api/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });

    const data = await resp.json();
    resEl.textContent = "";

    if (!resp.ok) {
      resEl.textContent = JSON.stringify(data, null, 2);
      return;
    }

    // Show image if present
    if (data.image) {
      const img = document.createElement("img");
      img.src = "data:image/png;base64," + data.image;
      img.style.width = "600px";
      img.style.maxWidth = "100%";
      img.style.height = "auto";
      img.style.display = "block";
      img.style.margin = "0 auto";
      resEl.appendChild(img);
    }

    // Show path + cost
    if (data.path) {
      let formatted = `${data.algo} Path: ${JSON.stringify(data.path)} cost = ${data.cost}.0`;
      const p = document.createElement("pre");
      p.textContent = formatted;
      resEl.appendChild(p);
    }

  } catch (err) {
    resEl.textContent = String(err);
  }
}

// --- UI Hooks ---
function toggleCustomSection() {
  const mode = document.querySelector('input[name="mode"]:checked').value;
  document.getElementById("customSection").style.display =
    (mode === "custom") ? "grid" : "none";
}

document.querySelectorAll("input[name=mode]").forEach(radio => {
  radio.addEventListener("change", (e) => {
    toggleCustomSection();
    loadGraph(e.target.value); // log for debug
  });
});

toggleCustomSection();
document.getElementById("runBtn").addEventListener("click", run);
