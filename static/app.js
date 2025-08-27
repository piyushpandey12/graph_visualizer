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

function getCustomGraph() {
  return {
    nodes: parseNodes(document.getElementById("nodes").value),
    edges: parseEdges(document.getElementById("edges").value)
  };
}

function loadGraph(mode) {
  let graph;
  if (mode === "default") {
    graph = defaultGraph;
  } else if (mode === "negative") {
    graph = negativeEdgeGraph;
  } else {
    graph = getCustomGraph();
  }
  console.log("Graph loaded:", graph);
}

async function run() {
  const mode = document.querySelector('input[name="mode"]:checked').value; 
  const algo = document.getElementById("algorithm").value; 
  const src = document.getElementById("source").value.trim();
  const dst = document.getElementById("target").value.trim();

  const payload = { mode, algo, src, dst };
  if (mode === "custom") {
    payload.nodes = parseNodes(document.getElementById("nodes").value);
    payload.edges = parseEdges(document.getElementById("edges").value);
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
    if (!resp.ok) {
      resEl.textContent = JSON.stringify(data, null, 2);
      return;
    }

    resEl.innerHTML = "";

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

    let formatted = `${data.algo} Path: ${JSON.stringify(data.path)} cost = ${data.cost}.0`;
    const p = document.createElement("pre");
    p.textContent = formatted;
    resEl.appendChild(p);

  } catch (err) {
    resEl.textContent = String(err);
  }
}

document.querySelectorAll("input[name=mode]").forEach(radio => {
  radio.addEventListener("change", (e) => {
    loadGraph(e.target.value);
  });
});

document.getElementById("runBtn").addEventListener("click", run);
