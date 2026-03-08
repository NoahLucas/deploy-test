const TOKEN_KEY = "lab_admin_token";

function $(id) {
  return document.getElementById(id);
}

function output(data) {
  const el = $("control-output");
  if (el) el.textContent = JSON.stringify(data, null, 2);
}

function token() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function headers() {
  const t = token();
  const h = { "Content-Type": "application/json" };
  if (t) h["X-Admin-Token"] = t;
  return h;
}

async function call(path, method = "GET", body = null) {
  const res = await fetch(path, {
    method,
    headers: headers(),
    body: body ? JSON.stringify(body) : undefined
  });
  const text = await res.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch (_) {
    data = { raw: text };
  }
  if (!res.ok) throw new Error(JSON.stringify(data));
  return data;
}

function saveToken() {
  const value = $("admin-token")?.value?.trim() || "";
  localStorage.setItem(TOKEN_KEY, value);
  output({ saved: true });
}

async function connectApple() {
  try {
    const data = await call("/api/v1/admin/apple/connect", "POST", {
      identity_token: $("apple-identity-token")?.value || "",
      nonce: ($("apple-nonce")?.value || "").trim() || null
    });
    output(data);
  } catch (err) {
    output({ error: String(err) });
  }
}

async function connectOpenAI() {
  try {
    const data = await call("/api/v1/admin/openai/connect", "POST", {
      api_key: $("openai-api-key")?.value || "",
      model: ($("openai-model")?.value || "").trim() || null
    });
    output(data);
  } catch (err) {
    output({ error: String(err) });
  }
}

async function refreshToggles() {
  const host = $("toggle-list");
  if (!host) return;

  try {
    const data = await call("/api/v1/admin/endpoints", "GET", null);
    const rows = data.items || [];
    host.innerHTML = rows
      .map((row) => `
        <label class="toggle-row">
          <span><strong>${row.platform.toUpperCase()}</strong> ${row.path}</span>
          <input type="checkbox" data-path="${row.path}" ${row.enabled ? "checked" : ""} />
        </label>
      `)
      .join("");

    host.querySelectorAll("input[type='checkbox']").forEach((checkbox) => {
      checkbox.addEventListener("change", async (event) => {
        const target = event.target;
        if (!(target instanceof HTMLInputElement)) return;
        const path = target.getAttribute("data-path") || "";
        try {
          const updated = await call("/api/v1/admin/endpoints/toggle", "POST", {
            path,
            enabled: target.checked
          });
          output(updated);
        } catch (err) {
          output({ error: String(err) });
          target.checked = !target.checked;
        }
      });
    });
  } catch (err) {
    output({ error: String(err) });
    host.innerHTML = "";
  }
}

async function dispatchChief() {
  const mission = $("chief-mission")?.value?.trim() || "";
  const context = $("chief-context")?.value?.trim() || "";
  const autoExecute = Boolean($("chief-auto-execute")?.checked);

  if (mission.length < 10) {
    output({ error: "Mission is required (min 10 chars)." });
    return;
  }

  try {
    const data = await call("/api/v1/agents/chief/dispatch", "POST", {
      mission,
      context,
      auto_execute: autoExecute,
      tasks: []
    });
    output(data);
    await refreshAgentRuns();
  } catch (err) {
    output({ error: String(err) });
  }
}

async function refreshAgentRuns() {
  const host = $("agent-runs-output");
  if (!host) return;
  try {
    const runs = await call("/api/v1/agents/runs", "GET", null);
    const items = runs.items || [];
    if (!items.length) {
      host.textContent = "No runs yet.";
      return;
    }
    const detail = await call(`/api/v1/agents/runs/${items[0].id}`, "GET", null);
    host.textContent = JSON.stringify({
      runs: items.slice(0, 8),
      latest: detail
    }, null, 2);
  } catch (err) {
    host.textContent = JSON.stringify({ error: String(err) }, null, 2);
  }
}

const adminTokenInput = $("admin-token");
if (adminTokenInput) {
  adminTokenInput.value = token();
}
$("save-admin-token")?.addEventListener("click", saveToken);
$("connect-apple")?.addEventListener("click", connectApple);
$("connect-openai")?.addEventListener("click", connectOpenAI);
$("refresh-toggles")?.addEventListener("click", refreshToggles);
$("dispatch-chief")?.addEventListener("click", dispatchChief);
$("refresh-agent-runs")?.addEventListener("click", refreshAgentRuns);

refreshToggles();
refreshAgentRuns();


async function refreshSquarespaceEvents() {
  const host = $("sq-events-output");
  if (!host) return;
  try {
    const data = await call("/api/v1/admin/squarespace/events", "GET", null);
    host.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    host.textContent = JSON.stringify({ error: String(err) }, null, 2);
  }
}

$("refresh-sq-events")?.addEventListener("click", refreshSquarespaceEvents);
