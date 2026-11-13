const state = { projects: [], staff: [], resources: {} };
let toastTimer = 0;
let loadSequence = 0;
let loadedOnce = false;
const resourceIds = [
  "projects", "expenses", "tasks", "staff", "shifts", "revenue",
  "assets", "releases", "audio_zones",
];
const currency = new Intl.NumberFormat(undefined, { style: "currency", currency: "USD" });
const allocationLabels = {
  infrastructure_reserve: "Infrastructure reserve",
  core_engineering: "Core engineering",
  environment_art: "Environment art",
  live_operations: "Live operations",
};

function localDateString() {
  const now = new Date();
  now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
  return now.toISOString().slice(0, 10);
}

function showToast(message, error = false) {
  const toast = document.querySelector("#toast");
  toast.textContent = message;
  toast.classList.toggle("error", error);
  toast.classList.add("show");
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => toast.classList.remove("show"), 3600);
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(path, {
      ...options,
      headers: { "Content-Type": "application/json", ...options.headers },
    });
  } catch {
    throw new Error("Cannot reach the local Ledger server. Check that it is running, then retry.");
  }
  let result;
  try {
    result = await response.json();
  } catch {
    throw new Error("The Ledger server returned an unreadable response. Check the server log.");
  }
  if (!response.ok) throw new Error(result.error || `Request failed (${response.status})`);
  return result;
}

function projectName(id) {
  return state.projects.find((project) => project.id === id)?.name || "Unknown project";
}

function staffName(id) {
  return state.staff.find((member) => member.id === id)?.display_name || "Unknown contributor";
}

function addCell(row, value) {
  const cell = document.createElement("td");
  cell.textContent = value === null || value === undefined || value === "" ? "—" : String(value);
  row.append(cell);
  return cell;
}

function addHeaderCell(row, value) {
  const cell = document.createElement("th");
  cell.scope = "col";
  cell.textContent = value;
  row.append(cell);
}

function renderTable(containerId, headers, rows, emptyMessage) {
  const container = document.getElementById(containerId);
  container.replaceChildren();
  if (!rows.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = emptyMessage;
    container.append(empty);
    return null;
  }
  const table = document.createElement("table");
  table.setAttribute("aria-label", headers.join(", "));
  const head = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const header of headers) addHeaderCell(headerRow, header);
  head.append(headerRow);
  const body = document.createElement("tbody");
  table.append(head, body);
  container.append(table);
  return body;
}

function renderProjects() {
  const body = renderTable("projects-list", ["Project", "Platform", "Budget / month", "Status"],
    state.projects, "Create a project to start your ledger.");
  if (body) for (const project of state.projects) {
    const row = document.createElement("tr");
    addCell(row, project.name);
    addCell(row, project.platform);
    addCell(row, currency.format(project.monthly_budget));
    addCell(row, project.status);
    body.append(row);
  }
}

function renderExpenses() {
  const rows = state.resources.expenses || [];
  const body = renderTable("expenses-list", ["Vendor", "Project", "Category", "Amount", "Cycle"],
    rows, "No expenses recorded.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.vendor);
    addCell(row, projectName(item.project_id));
    addCell(row, item.category);
    addCell(row, currency.format(item.amount));
    addCell(row, item.billing_cycle.replace("_", " "));
    body.append(row);
  }
}

function renderTasks() {
  const rows = state.resources.tasks || [];
  const body = renderTable("tasks-list", ["Task", "Track", "Assignee", "Status", "Due"],
    rows, "Add a milestone to populate the production board.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.title);
    addCell(row, item.track);
    addCell(row, item.assignee);
    const statusCell = document.createElement("td");
    const select = document.createElement("select");
    select.setAttribute("aria-label", `Status for ${item.title}`);
    for (const status of ["todo", "in_progress", "blocked", "done"]) {
      const option = document.createElement("option");
      option.value = status;
      option.textContent = status.replace("_", " ");
      option.selected = item.status === status;
      select.append(option);
    }
    select.addEventListener("change", async () => {
      try {
        await request(`/api/tasks/${encodeURIComponent(item.id)}`, {
          method: "PATCH",
          body: JSON.stringify({ status: select.value }),
        });
        await loadData();
        showToast("Task status updated.");
      } catch (error) {
        showToast(error.message, true);
        try {
          await loadData();
        } catch (refreshError) {
          showToast(`Could not reload task status. ${refreshError.message}`, true);
        }
      }
    });
    statusCell.append(select);
    row.append(statusCell);
    addCell(row, item.due_date);
    body.append(row);
  }
}

function renderStaff() {
  const rows = state.staff;
  const body = renderTable("staff-list", ["Contributor", "Role", "Rate / hour", "Active"],
    rows, "Add contributors to your roster.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.display_name);
    addCell(row, item.role);
    addCell(row, currency.format(item.rate_per_hour));
    addCell(row, item.active ? "Yes" : "No");
    body.append(row);
  }
}

function renderShifts() {
  const rows = state.resources.shifts || [];
  const body = renderTable("shifts-list", ["Date", "Contributor", "Project", "Hours", "Tips", "Status"],
    rows, "No shifts recorded.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.date);
    addCell(row, staffName(item.staff_id));
    addCell(row, projectName(item.project_id));
    addCell(row, item.hours);
    addCell(row, currency.format(item.tips));
    addCell(row, item.status);
    body.append(row);
  }
}

function renderRevenue() {
  const rows = state.resources.revenue || [];
  const body = renderTable("revenue-list", ["Date", "Source", "Project", "Gross", "Fees", "Net"],
    rows, "No revenue recorded.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.date);
    addCell(row, item.source);
    addCell(row, projectName(item.project_id));
    addCell(row, currency.format(item.gross));
    addCell(row, currency.format(item.fees));
    addCell(row, currency.format(item.gross - item.fees));
    body.append(row);
  }
}

function renderAssets() {
  const rows = state.resources.assets || [];
  const body = renderTable("assets-list", ["Asset", "Creator", "Track", "License", "Credited"],
    rows, "No assets registered.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.name);
    addCell(row, item.creator);
    addCell(row, item.track);
    addCell(row, item.license);
    addCell(row, item.credited ? "Yes" : "Review");
    body.append(row);
  }
}

function renderReleases() {
  const rows = state.resources.releases || [];
  const body = renderTable("releases-list", ["Version", "Project", "Target", "Status", "Notes"],
    rows, "No releases recorded.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.version);
    addCell(row, projectName(item.project_id));
    addCell(row, item.target);
    addCell(row, item.status);
    addCell(row, item.notes);
    body.append(row);
  }
}

function renderAudioZones() {
  const rows = state.resources.audio_zones || [];
  const body = renderTable("audio_zones-list", ["Zone", "Project", "Near", "Far", "Strategy"],
    rows, "No spatial audio zones recorded.");
  if (body) for (const item of rows) {
    const row = document.createElement("tr");
    addCell(row, item.name);
    addCell(row, projectName(item.project_id));
    addCell(row, `${item.near_distance} m`);
    addCell(row, `${item.far_distance} m`);
    addCell(row, item.strategy);
    body.append(row);
  }
}

function renderSelectOptions() {
  for (const select of document.querySelectorAll("select[data-projects]")) {
    const previous = select.value;
    select.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = state.projects.length ? "Select project" : "Create a project first";
    select.append(placeholder);
    for (const project of state.projects) {
      const option = document.createElement("option");
      option.value = project.id;
      option.textContent = project.name;
      select.append(option);
    }
    if (state.projects.some((project) => project.id === previous)) select.value = previous;
  }
  for (const select of document.querySelectorAll('select[name="staff_id"]')) {
    const previous = select.value;
    const activeStaff = state.staff.filter((person) => person.active);
    select.replaceChildren();
    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = activeStaff.length ? "Select contributor" : "Add an active contributor first";
    select.append(placeholder);
    for (const member of activeStaff) {
      const option = document.createElement("option");
      option.value = member.id;
      option.textContent = `${member.display_name} · ${member.role}`;
      select.append(option);
    }
    if (state.staff.some((person) => person.id === previous)) select.value = previous;
  }
}

function renderSummary(summary) {
  const cards = [
    ["ACTIVE PROJECTS", summary.projects, "Portfolio in this workspace"],
    ["MONTHLY RUN RATE", currency.format(summary.monthly_recurring_cost), "Recurring costs across projects"],
    ["NET REVENUE · MTD", currency.format(summary.month_to_date_net_revenue), "After recorded platform fees"],
    ["OPEN WORK ITEMS", summary.open_tasks, `${summary.uncredited_assets} assets need attribution`],
  ];
  const container = document.querySelector("#summary-cards");
  container.replaceChildren();
  for (const [label, value, note] of cards) {
    const card = document.createElement("div");
    card.className = "stat-card";
    const eyebrow = document.createElement("p");
    eyebrow.className = "eyebrow";
    eyebrow.textContent = label;
    const figure = document.createElement("strong");
    figure.className = "stat-value";
    figure.textContent = String(value);
    const detail = document.createElement("span");
    detail.className = "stat-note";
    detail.textContent = note;
    card.append(eyebrow, figure, detail);
    container.append(card);
  }
  const budgetList = document.querySelector("#budget-list");
  budgetList.replaceChildren();
  if (!summary.projects_by_budget.length) {
    budgetList.textContent = "Create a project to view budget utilization.";
    budgetList.className = "budget-list empty";
  } else {
    budgetList.className = "budget-list";
    for (const project of summary.projects_by_budget) {
      const row = document.createElement("div");
      row.className = "budget-row";
      const name = document.createElement("span");
      name.className = "budget-name";
      name.textContent = project.name;
      const track = document.createElement("div");
      track.className = "progress-track";
      track.setAttribute("role", "progressbar");
      track.setAttribute("aria-label", `Monthly budget used by ${project.name}`);
      const fill = document.createElement("div");
      const ratio = project.monthly_budget > 0
        ? Math.min(100, (project.monthly_cost / project.monthly_budget) * 100)
        : (project.monthly_cost > 0 ? 100 : 0);
      track.setAttribute("aria-valuemin", "0");
      track.setAttribute("aria-valuemax", "100");
      track.setAttribute("aria-valuenow", String(Math.round(ratio)));
      track.setAttribute(
        "aria-valuetext",
        `${currency.format(project.monthly_cost)} of ${currency.format(project.monthly_budget)} monthly budget`,
      );
      fill.className = `progress-fill${project.monthly_cost > project.monthly_budget ? " over" : ""}`;
      fill.style.width = `${ratio}%`;
      track.append(fill);
      const values = document.createElement("span");
      values.className = "budget-values";
      values.textContent = `${currency.format(project.monthly_cost)} / ${currency.format(project.monthly_budget)}`;
      row.append(name, track, values);
      budgetList.append(row);
    }
  }
  const allocation = document.querySelector("#allocation-list");
  allocation.replaceChildren();
  for (const [key, percentage] of Object.entries(summary.revenue_allocation_percent)) {
    const item = document.createElement("div");
    const strong = document.createElement("strong");
    strong.textContent = `${percentage}%`;
    const label = document.createElement("span");
    label.textContent = allocationLabels[key] || key;
    item.append(strong, label);
    allocation.append(item);
  }
}

function renderAll(summary) {
  renderSelectOptions();
  renderProjects();
  renderExpenses();
  renderTasks();
  renderStaff();
  renderShifts();
  renderRevenue();
  renderAssets();
  renderReleases();
  renderAudioZones();
  renderSummary(summary);
}

function setAppStatus(message, { visible = true, retry = false, busy = false } = {}) {
  const status = document.querySelector("#app-status");
  document.querySelector("#app-status-message").textContent = message;
  document.querySelector("#retry-load").hidden = !retry;
  status.setAttribute("aria-busy", String(busy));
  status.hidden = !visible;
}

async function loadData() {
  const sequence = ++loadSequence;
  const main = document.querySelector("#main-content");
  const refresh = document.querySelector("#refresh-data");
  main.setAttribute("aria-busy", "true");
  refresh.disabled = true;
  refresh.setAttribute("aria-busy", "true");
  if (!loadedOnce) setAppStatus("Loading your local ledger…", { busy: true });
  try {
    const [summary, ...resources] = await Promise.all([
      request("/api/summary"),
      ...resourceIds.map((resource) => request(`/api/${resource}`)),
    ]);
    if (sequence !== loadSequence) return;
    state.resources = Object.fromEntries(resourceIds.map((resource, index) => [resource, resources[index]]));
    state.projects = state.resources.projects;
    state.staff = state.resources.staff;
    renderAll(summary);
    loadedOnce = true;
    setAppStatus("", { visible: false });
  } catch (error) {
    if (sequence === loadSequence) {
      setAppStatus(
        loadedOnce
          ? `Could not refresh the ledger. Previously loaded data may be out of date. ${error.message}`
          : `Could not load the ledger. ${error.message}`,
        { retry: true },
      );
    }
    throw error;
  } finally {
    if (sequence === loadSequence) {
      main.setAttribute("aria-busy", "false");
      refresh.disabled = false;
      refresh.setAttribute("aria-busy", "false");
    }
  }
}

function formPayload(form) {
  const payload = {};
  for (const field of form.elements) {
    if (!field.name) continue;
    if (field.type === "checkbox") payload[field.name] = field.checked;
    else if (field.value !== "") payload[field.name] = field.value;
  }
  return payload;
}

function setupForms() {
  for (const form of document.querySelectorAll("form[data-resource]")) {
    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const resource = form.dataset.resource;
      const submit = form.querySelector('button[type="submit"]');
      const originalLabel = submit.textContent;
      let saved = false;
      submit.disabled = true;
      submit.textContent = "Saving…";
      form.setAttribute("aria-busy", "true");
      try {
        await request(`/api/${resource}`, { method: "POST", body: JSON.stringify(formPayload(form)) });
        saved = true;
        form.reset();
        for (const dateField of form.querySelectorAll('input[type="date"]')) {
          if (dateField.required) dateField.value = localDateString();
        }
        showToast("Saved to your local ledger.");
        await loadData();
      } catch (error) {
        showToast(
          saved ? `Saved, but the dashboard could not refresh. ${error.message}` : error.message,
          true,
        );
      } finally {
        submit.disabled = false;
        submit.textContent = originalLabel;
        form.setAttribute("aria-busy", "false");
      }
    });
  }
}

function setupNavigation() {
  function navigate() {
    const view = location.hash.slice(1) || "overview";
    const selected = document.getElementById(`view-${view}`) ? view : "overview";
    for (const section of document.querySelectorAll(".view")) {
      section.classList.toggle("active", section.id === `view-${selected}`);
    }
    for (const link of document.querySelectorAll("[data-view]")) {
      const active = link.dataset.view === selected;
      link.classList.toggle("active", active);
      if (active) link.setAttribute("aria-current", "page");
      else link.removeAttribute("aria-current");
    }
  }
  for (const link of document.querySelectorAll("[data-view]")) {
    link.addEventListener("click", () => {
      const heading = document.querySelector(`#view-${link.dataset.view} h1`);
      if (heading) window.requestAnimationFrame(() => heading.focus({ preventScroll: true }));
    });
  }
  window.addEventListener("hashchange", navigate);
  navigate();
}

function setupChecklist() {
  const checks = document.querySelectorAll("[data-checklist]");
  let storageUnavailable = false;
  for (const check of checks) {
    const key = `ledger-suite-checklist-${check.dataset.checklist}`;
    try {
      check.checked = window.localStorage.getItem(key) === "true";
    } catch {
      storageUnavailable = true;
    }
    check.addEventListener("change", () => {
      try {
        window.localStorage.setItem(key, String(check.checked));
      } catch {
        showToast("Could not save checklist progress in this browser.", true);
      }
    });
  }
  if (storageUnavailable) {
    showToast("Browser storage is unavailable; release checklist progress will not persist.", true);
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  document.querySelector("#today").textContent = new Intl.DateTimeFormat(undefined, {
    weekday: "short", month: "short", day: "numeric", year: "numeric",
  }).format(new Date()).toUpperCase();
  setupNavigation();
  setupForms();
  setupChecklist();
  document.querySelector("#refresh-data").addEventListener("click", async () => {
    try {
      await loadData();
      showToast("Ledger refreshed.");
    } catch {
      showToast("Refresh failed. Use the message above to retry.", true);
    }
  });
  document.querySelector("#retry-load").addEventListener("click", async () => {
    try {
      await loadData();
    } catch (error) {
      showToast(error.message, true);
    }
  });
  for (const field of document.querySelectorAll('input[type="date"]')) {
    if (!field.value && (field.name === "date" || field.required)) {
      field.value = localDateString();
    }
  }
  try {
    await loadData();
  } catch (error) {
    showToast(error.message, true);
  }
});
