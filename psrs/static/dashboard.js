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
    try {
      const params = new URLSearchParams(new FormData(form));
      const result = await getJson(`/api/route?${params.toString()}`);
      resultElement.className = `route-result ${result.feasible ? "success" : "error"}`;
      resultElement.textContent = result.feasible
        ? `Feasible route: ${result.nodes.join(" → ")} · ${result.distance} synthetic distance units · ${result.travel_time} estimated travel-time units.`
        : `No feasible route: ${result.reason}. Choose another destination in the fictional network.`;
    } catch (error) {
      resultElement.className = "route-result error";
      resultElement.textContent = error.message;
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
  loadDashboard();
  $("#route-form").addEventListener("change", loadRoute);
})();
