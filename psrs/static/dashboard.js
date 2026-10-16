(() => {
  const $ = (selector) => document.querySelector(selector);
  const notice = (message, tone = "info") => {
    const element = $("#notice");
    element.className = `notice ${tone}`;
    element.innerHTML = `<span class="notice-icon" aria-hidden="true">${tone === "error" ? "!" : "i"}</span><span>${message}</span>`;
  };

  const formatNumber = (value) => new Intl.NumberFormat().format(value);

  function renderChart(predictions) {
    const chart = $("#forecast-chart");
    const line = $("#forecast-line");
    const area = $("#forecast-area");
    const points = $("#forecast-points");
    const labels = $("#chart-labels");
    const width = 720;
    const left = 48;
    const right = 700;
    const top = 28;
    const bottom = 202;
    const maximum = Math.max(...predictions, 1) * 1.2;
    const step = predictions.length > 1 ? (right - left) / (predictions.length - 1) : 0;
    const pointList = predictions.map((value, index) => ({
      x: left + step * index,
      y: bottom - (value / maximum) * (bottom - top),
      value,
    }));
    const path = pointList.map((point, index) => `${index ? "L" : "M"} ${point.x.toFixed(1)} ${point.y.toFixed(1)}`).join(" ");
    line.setAttribute("d", path);
    area.setAttribute("d", `${path} L ${pointList.at(-1).x} ${bottom} L ${pointList[0].x} ${bottom} Z`);
    points.innerHTML = pointList.map((point) => `<circle cx="${point.x}" cy="${point.y}" r="4"><title>${point.value} units</title></circle>`).join("");
    labels.innerHTML = pointList.map((point, index) => `<text x="${point.x}" y="222" text-anchor="middle">Day ${index + 1}</text>`).join("");
    $("#chart-description").textContent = `Forecast values: ${predictions.join(", ")} units.`;
    $("#forecast-empty").hidden = true;
  }

  function renderInventory(estimates) {
    const list = $("#inventory-list");
    if (!estimates.length) {
      list.innerHTML = '<div class="list-row"><span>No inventory estimates available</span><span>—</span></div>';
      return;
    }
    const sorted = [...estimates].sort((a, b) => a.estimated_stock - b.estimated_stock).slice(0, 4);
    const total = estimates.reduce((sum, estimate) => sum + estimate.estimated_stock, 0);
    const uncertain = estimates.filter((estimate) => estimate.lower_bound !== estimate.upper_bound).length;
    $("#inventory-coverage").textContent = `${Math.round((1 - uncertain / estimates.length) * 100)}%`;
    $("#inventory-status").textContent = uncertain ? "Review uncertainty flags" : "Stable estimates";
    $("#inventory-caption").textContent = `${uncertain} of ${estimates.length} series carry evidence gaps.`;
    list.innerHTML = sorted.map((estimate) => `
      <div class="list-row">
        <span><strong>${estimate.location_id}</strong> · ${estimate.item_id}</span>
        <span>${formatNumber(estimate.estimated_stock)} units</span>
      </div>
    `).join("");
    $("#inventory-events").title = `Total estimated stock: ${formatNumber(total)} units`;
  }


  // The map is deliberately schematic: coordinates and edges mirror the
  // committed fictional GeoJSON network, not real-world geography.
  const networkNodes = [
    { id: "LOC-01", name: "Hub A", x: 0, y: 0 },
    { id: "LOC-02", name: "Point B", x: 4, y: 2 },
    { id: "LOC-03", name: "Point C", x: 2, y: 6 },
    { id: "LOC-04", name: "Point D", x: 8, y: 3 },
    { id: "LOC-05", name: "Point E", x: 7, y: 8 },
    { id: "LOC-06", name: "Point F", x: 11, y: 6 },
  ];
  const networkEdges = [
    ["LOC-01", "LOC-02"], ["LOC-01", "LOC-03"], ["LOC-02", "LOC-04"],
    ["LOC-03", "LOC-05"], ["LOC-04", "LOC-05"], ["LOC-05", "LOC-06"],
  ];
  let networkMap = null;
  let edgeLayers = [];
  let nodeLayers = new Map();

  function initNetworkMap() {
    const mapElement = $("#route-map");
    if (!mapElement || !window.L) {
      if (mapElement) mapElement.innerHTML = '<p class="map-fallback">Map library unavailable. Use the route selectors below to calculate a route.</p>';
      return;
    }
    networkMap = L.map(mapElement, {
      crs: L.CRS.Simple,
      minZoom: -1.5,
      maxZoom: 2,
      zoomControl: true,
      attributionControl: false,
      scrollWheelZoom: false,
    });
    const bounds = [[-1, -1], [9, 12]];
    L.rectangle(bounds, { color: "#dce5ee", weight: 1, fillColor: "#f7f9fc", fillOpacity: .2, interactive: false }).addTo(networkMap);
    // Light grid is visual scaffolding only; it does not imply real roads.
    for (let y = 0; y <= 8; y += 2) {
      L.polyline([[y, -0.5], [y, 11.5]], { color: "#e5ebf2", weight: 1, interactive: false }).addTo(networkMap);
    }
    for (let x = 0; x <= 10; x += 2) {
      L.polyline([[-0.5, x], [8.5, x]], { color: "#e5ebf2", weight: 1, interactive: false }).addTo(networkMap);
    }
    networkEdges.forEach(([from, to]) => {
      const a = networkNodes.find((node) => node.id === from);
      const b = networkNodes.find((node) => node.id === to);
      const layer = L.polyline([[a.y, a.x], [b.y, b.x]], { color: "#9aabba", weight: 3, opacity: .9, lineCap: "round" }).addTo(networkMap);
      layer.bindTooltip(`${from} ↔ ${to}`, { className: "psrs-label", direction: "center", sticky: true });
      edgeLayers.push({ from, to, layer });
    });
    networkNodes.forEach((node) => {
      const icon = L.divIcon({ className: "", html: `<span class="psrs-node-icon" aria-hidden="true">${node.id.slice(-2)}</span>`, iconSize: [31, 31], iconAnchor: [15, 15] });
      const marker = L.marker([node.y, node.x], { icon, title: `${node.id} · ${node.name}`, alt: `${node.id}, ${node.name}` }).addTo(networkMap);
      marker.bindTooltip(`${node.id} · ${node.name}`, { className: "psrs-label", direction: "top", offset: [0, -12] });
      marker.on("click", () => {
        const origin = $("#origin");
        const destination = $("#destination");
        const nextPick = origin.dataset.nextPick || "origin";
        if (nextPick === "origin") {
          origin.value = node.id;
          origin.dataset.nextPick = "destination";
          $("#route-result").className = "route-result";
          $("#route-result").innerHTML = "<strong>Starting point selected</strong><span>Now click a destination on the map, or choose one below.</span>";
        } else {
          destination.value = node.id;
          origin.dataset.nextPick = "origin";
          loadRoute();
        }
      });
      nodeLayers.set(node.id, marker);
    });
    networkMap.fitBounds(bounds, { padding: [12, 12] });
    $("#fit-network")?.addEventListener("click", () => networkMap.fitBounds(bounds, { padding: [12, 12] }));
  }

  function updateMapRoute(routeNodes) {
    if (!networkMap) return;
    const selected = new Set();
    for (let index = 0; index < routeNodes.length - 1; index += 1) {
      selected.add([routeNodes[index], routeNodes[index + 1]].sort().join("|"));
    }
    edgeLayers.forEach(({ from, to, layer }) => {
      const isSelected = selected.has([from, to].sort().join("|"));
      layer.setStyle({ color: isSelected ? "#245ea8" : "#9aabba", weight: isSelected ? 5 : 3, opacity: isSelected ? 1 : .78 });
      if (isSelected) layer.bringToFront();
    });
    networkNodes.forEach((node) => {
      const element = nodeLayers.get(node.id)?.getElement()?.querySelector(".psrs-node-icon");
      if (!element) return;
      element.classList.toggle("is-origin", routeNodes[0] === node.id);
      element.classList.toggle("is-destination", routeNodes.at(-1) === node.id && routeNodes.length > 1);
    });
    if (routeNodes.length) {
      const points = routeNodes.map((id) => networkNodes.find((node) => node.id === id)).filter(Boolean).map((node) => [node.y, node.x]);
      if (points.length) networkMap.fitBounds(L.latLngBounds(points), { padding: [42, 42], maxZoom: 0.5 });
    }
  }

  async function getJson(url) {
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Request failed");
    return payload;
  }

  async function loadSummary() {
    const summary = await getJson("/api/summary");
    $("#dataset").textContent = summary.dataset_available ? "Ready" : "Missing";
    $("#dataset-meta").textContent = summary.dataset_available ? "Synthetic workspace online" : "Generate data to continue";
    $("#demand-rows").textContent = formatNumber(summary.demand_rows);
    $("#inventory-events").textContent = formatNumber(summary.inventory_events);
    $("#dimensions").textContent = `${summary.locations} / ${summary.items}`;
    return summary;
  }

  async function loadForecast() {
    const form = $("#forecast-form");
    const button = form.querySelector("button");
    button.disabled = true;
    button.innerHTML = "Calculating…";
    try {
      const params = new URLSearchParams(new FormData(form));
      const result = await getJson(`/api/forecast?${params.toString()}&horizon=7`);
      $("#forecast-model").textContent = result.model.replaceAll("_", " ");
      $("#forecast-mae").textContent = result.ml_mae === null ? "Not available" : result.ml_mae.toFixed(2);
      renderChart(result.predictions);
      notice("Forecast refreshed from historical synthetic demand. Review model assumptions before planning.", "success");
    } catch (error) {
      notice(error.message, "error");
      $("#forecast-model").textContent = "Unavailable";
      $("#forecast-mae").textContent = "—";
    } finally {
      button.disabled = false;
      button.innerHTML = 'Run forecast <span aria-hidden="true">→</span>';
    }
  }

  async function loadRoute() {
    const form = $("#route-form");
    const resultElement = $("#route-result");
    const button = $("#check-route");
    const origin = $("#origin").value;
    const destination = $("#destination").value;
    const weatherFactor = Number($("#weather-factor").value);

    if (!origin || !destination) {
      resultElement.className = "route-result error";
      resultElement.innerHTML = "<strong>Choose both locations</strong><span>Select a starting point and destination before checking the route.</span>";
      updateMapRoute([]);
      return;
    }
    if (origin === destination) {
      resultElement.className = "route-result error";
      resultElement.innerHTML = "<strong>Pick two different locations</strong><span>The starting point and destination cannot be the same.</span>";
      updateMapRoute([]);
      return;
    }
    if (!Number.isFinite(weatherFactor) || weatherFactor < 1 || weatherFactor > 10) {
      resultElement.className = "route-result error";
      resultElement.innerHTML = "<strong>Check the weather impact</strong><span>Enter a number from 1 to 10. Use 1 for normal conditions.</span>";
      updateMapRoute([]);
      return;
    }

    const originalButtonText = button ? button.innerHTML : "";
    if (button) {
      button.disabled = true;
      button.innerHTML = '<span class="button-spinner" aria-hidden="true"></span> Checking route…';
    }
    resultElement.className = "route-result loading";
    resultElement.innerHTML = "<strong>Checking your route…</strong><span>Looking for a connected path and estimating travel time.</span>";
    try {
      const params = new URLSearchParams(new FormData(form));
      const result = await getJson(`/api/route?${params.toString()}`);
      if (result.feasible && Array.isArray(result.nodes) && result.nodes.length) {
        const readableNodes = result.nodes.map((id) => {
          const node = networkNodes.find((item) => item.id === id);
          return node ? node.name : id;
        });
        resultElement.className = "route-result success";
        resultElement.innerHTML = "";
        const heading = document.createElement("strong");
        heading.textContent = "A route is available";
        const details = document.createElement("span");
        details.textContent = readableNodes.join(" → ");
        const metrics = document.createElement("span");
        metrics.textContent = `Sample distance: ${result.distance} units · Estimated travel time: ${result.travel_time} time units.`;
        resultElement.append(heading, details, metrics);
        updateMapRoute(result.nodes);
      } else {
        resultElement.className = "route-result error";
        resultElement.innerHTML = "";
        const heading = document.createElement("strong");
        heading.textContent = "No route found";
        const details = document.createElement("span");
        details.textContent = `${result.reason || "These locations are not connected in the sample network."} Try a different destination.`;
        resultElement.append(heading, details);
        updateMapRoute([]);
      }
    } catch (error) {
      resultElement.className = "route-result error";
      resultElement.innerHTML = "";
      const heading = document.createElement("strong");
      heading.textContent = "Could not check this route";
      const details = document.createElement("span");
      details.textContent = `${error.message || "The route service did not respond."} Check that the app is running and try again.`;
      resultElement.append(heading, details);
      updateMapRoute([]);
    } finally {
      if (button) {
        button.disabled = false;
        button.innerHTML = originalButtonText;
      }
    }
  }

  async function loadPlanning() {
    const form = $("#planning-form");
    const button = form.querySelector("button");
    const resultElement = $("#planning-result");
    button.disabled = true;
    button.innerHTML = "Running…";
    resultElement.innerHTML = '<span class="result-placeholder">Comparing nominal and adverse synthetic conditions…</span>';
    try {
      const forecastForm = $("#forecast-form");
      const routeForm = $("#route-form");
      const params = new URLSearchParams({
        location_id: forecastForm.location_id.value,
        item_id: forecastForm.item_id.value,
        origin: routeForm.origin.value,
        destination: routeForm.destination.value,
        capacity_limit: form.capacity_limit.value,
        horizon: "7",
      });
      const result = await getJson(`/api/planning?${params.toString()}`);
      const nominalScenario = (result.scenarios || []).find((scenario) => scenario.scenario === "nominal") || {};
      const adverseScenario = (result.scenarios || []).find((scenario) => scenario.scenario === "adverse_synthetic") || {};
      const nominal = nominalScenario.simulation || {};
      const adverse = adverseScenario.simulation || {};
      const plan = nominalScenario.candidate_plan?.evaluation || {};
      const feasible = plan.feasible !== false;
      resultElement.innerHTML = `
        <div class="result-status ${feasible ? "" : "warning"}">${feasible ? "✓ Feasible candidate plan" : "! Review plan constraints"}</div>
        <div class="result-summary">
          <div class="result-stat"><span>Nominal unmet demand</span><strong>${formatNumber(nominal.unmet_demand ?? 0)}</strong></div>
          <div class="result-stat"><span>Adverse unmet demand</span><strong>${formatNumber(adverse.unmet_demand ?? 0)}</strong></div>
          <div class="result-stat"><span>Route distance</span><strong>${plan.distance ?? "—"}</strong></div>
          <div class="result-stat"><span>Capacity used</span><strong>${plan.capacity_used ?? "—"} / ${plan.capacity_limit ?? "—"}</strong></div>
        </div>`;
      notice("Planning scenario completed. Treat the result as synthetic decision support, not an automatic instruction.", "success");
    } catch (error) {
      resultElement.innerHTML = `<span class="result-placeholder">${error.message}</span>`;
      notice(error.message, "error");
    } finally {
      button.disabled = false;
      button.innerHTML = 'Run scenario <span aria-hidden="true">→</span>';
    }
  }

  async function loadDashboard() {
    try {
      const summary = await loadSummary();
      if (!summary.dataset_available) {
        notice("Generate the synthetic dataset with `python scripts/generate_synthetic_data.py` to activate forecasting and inventory views.");
        $("#forecast-empty").hidden = false;
        return;
      }
      const [inventory] = await Promise.all([getJson("/api/inventory"), loadForecast()]);
      renderInventory(inventory.estimates);
      await loadRoute();
    } catch (error) {
      notice(error.message, "error");
    }
  }

  $("#forecast-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadForecast();
  });
  $("#route-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadRoute();
  });
  $("#planning-form").addEventListener("submit", (event) => {
    event.preventDefault();
    loadPlanning();
  });
  initNetworkMap();
  loadDashboard();
  $("#route-form").addEventListener("change", () => {
    const resultElement = $("#route-result");
    resultElement.className = "route-result";
    resultElement.innerHTML = "<strong>Route settings changed</strong><span>Press “Check route” to update the route and its travel-time estimate.</span>";
    updateMapRoute([]);
  });
})();
