const TOKEN_KEY = "lab_admin_token";

function $(id) {
  return document.getElementById(id);
}

function toLines(value) {
  return String(value || "")
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function pretty(el, data) {
  if (el) el.textContent = JSON.stringify(data, null, 2);
}

function getToken() {
  return localStorage.getItem(TOKEN_KEY) || "";
}

function headers(withAdmin = false) {
  const base = { "Content-Type": "application/json" };
  if (withAdmin) {
    const token = getToken();
    if (token) base["X-Admin-Token"] = token;
  }
  return base;
}

async function postJson(path, payload, withAdmin = false) {
  const res = await fetch(path, {
    method: "POST",
    headers: headers(withAdmin),
    body: JSON.stringify(payload)
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

async function getJson(path, withAdmin = false) {
  const res = await fetch(path, {
    method: "GET",
    headers: withAdmin ? headers(true) : undefined
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

function bindToken() {
  const input = $("admin-token");
  const btn = $("save-token");
  if (!input || !btn) return;

  input.value = getToken();
  btn.addEventListener("click", () => {
    localStorage.setItem(TOKEN_KEY, input.value.trim());
    btn.textContent = "Saved";
    setTimeout(() => {
      btn.textContent = "Save Token";
    }, 1200);
  });
}

function bindDailyBrief() {
  const form = $("daily-brief-form");
  const output = $("daily-brief-output");
  if (!form || !output) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        priorities: toLines($("priorities")?.value),
        risks: toLines($("risks")?.value),
        context: $("brief-context")?.value || ""
      };
      const data = await postJson("/api/v1/lab/daily-brief", payload, true);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });
}

function bindDecisionJournal() {
  const form = $("decision-form");
  const output = $("decision-output");
  const refresh = $("load-decisions");
  if (!form || !output || !refresh) return;

  const load = async () => {
    try {
      const data = await getJson("/api/v1/lab/decision-journal", true);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  };

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        title: $("decision-title")?.value || "",
        context: $("decision-context")?.value || "",
        options: toLines($("decision-options")?.value),
        chosen_option: $("decision-chosen")?.value || "",
        rationale: $("decision-rationale")?.value || "",
        follow_up_date: ($("decision-follow-up")?.value || "").trim() || null
      };
      const data = await postJson("/api/v1/lab/decision-journal", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  refresh.addEventListener("click", load);
}

function bindWeeklySnapshot() {
  const refresh = $("refresh-weekly");
  const output = $("weekly-output");
  if (!refresh || !output) return;

  const load = async () => {
    try {
      const data = await getJson("/api/v1/lab/weekly-snapshot", true);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  };

  refresh.addEventListener("click", load);
  load();
}

function bindAppleTools() {
  const verifyIdentityBtn = $("verify-identity");
  const challengeBtn = $("attest-challenge");
  const verifyAttestationBtn = $("verify-attestation");
  const output = $("apple-output");

  if (!verifyIdentityBtn || !challengeBtn || !verifyAttestationBtn || !output) return;

  verifyIdentityBtn.addEventListener("click", async () => {
    try {
      const payload = {
        identity_token: $("apple-identity-token")?.value || "",
        nonce: ($("apple-identity-nonce")?.value || "").trim() || null
      };
      const data = await postJson("/api/v1/apple/identity/verify", payload, false);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  challengeBtn.addEventListener("click", async () => {
    try {
      const payload = { device_id: $("attest-device-id")?.value || "" };
      const data = await postJson("/api/v1/apple/app-attest/challenge", payload, false);
      const challengeInput = $("attest-challenge-value");
      if (challengeInput) challengeInput.value = data.challenge || "";
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  verifyAttestationBtn.addEventListener("click", async () => {
    try {
      const payload = {
        device_id: $("attest-device-id")?.value || "",
        key_id: $("attest-key-id")?.value || "",
        bundle_id: $("attest-bundle-id")?.value || "",
        challenge: $("attest-challenge-value")?.value || "",
        attestation_object_b64: $("attest-object")?.value || "",
        client_data_hash_b64: $("attest-client-hash")?.value || ""
      };
      const data = await postJson("/api/v1/apple/app-attest/verify", payload, false);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });
}

function bindAutobiographer() {
  const output = $("autobio-output");
  const initForm = $("autobio-init-form");
  const refreshBtn = $("autobio-refresh-chapters");
  const eventForm = $("autobio-event-form");
  const generateForm = $("autobio-generate-form");
  const generateYearBtn = $("autobio-generate-year-chapter");
  const publishYearBtn = $("autobio-publish-year");
  const publishBtn = $("autobio-publish-live");
  if (!output || !initForm || !refreshBtn || !eventForm || !generateForm || !generateYearBtn || !publishYearBtn || !publishBtn) return;

  const yearInput = $("autobio-year");
  const personaInput = $("autobio-persona");
  const styleInput = $("autobio-style");
  const generateYearInput = $("autobio-generate-year");
  const generateMonthInput = $("autobio-generate-month");
  const forceInput = $("autobio-force");

  const load = async () => {
    try {
      const year = Number(generateYearInput?.value || yearInput?.value || new Date().getFullYear());
      const [months, years] = await Promise.all([
        getJson(`/api/v1/lab/autobiographer/chapters?year=${year}`, true),
        getJson("/api/v1/lab/autobiographer/year-chapters?limit=12", true)
      ]);
      pretty(output, { monthly: months, yearly: years });
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  };

  initForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        year: Number(yearInput?.value || new Date().getFullYear()),
        persona_label: personaInput?.value || "founder-biographer",
        style_brief: styleInput?.value || "Narrative nonfiction in a Walter Isaacson-inspired mode: warm, observant, specific, psychologically perceptive, and grounded in real scenes."
      };
      const data = await postJson("/api/v1/lab/autobiographer/chapters/initialize-year", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  eventForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const tags = String($("autobio-event-tags")?.value || "")
        .split(",")
        .map((v) => v.trim())
        .filter(Boolean);
      const payload = {
        source: $("autobio-event-source")?.value || "manual-journal",
        title: $("autobio-event-title")?.value || "",
        detail: $("autobio-event-detail")?.value || "",
        tags,
        event_at: ($("autobio-event-at")?.value || "").trim() || undefined
      };
      const data = await postJson("/api/v1/lab/autobiographer/events", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  generateForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
      const payload = {
        year: Number(generateYearInput?.value || new Date().getFullYear()),
        month: Number(generateMonthInput?.value || new Date().getMonth() + 1),
        persona_label: personaInput?.value || "founder-biographer",
        style_brief: styleInput?.value || "Narrative nonfiction in a Walter Isaacson-inspired mode: warm, observant, specific, psychologically perceptive, and grounded in real scenes.",
        include_private_context: true,
        force_regenerate: String(forceInput?.value || "false") === "true"
      };
      const data = await postJson("/api/v1/lab/autobiographer/chapters/generate", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  refreshBtn.addEventListener("click", load);
  generateYearBtn.addEventListener("click", async () => {
    try {
      const payload = {
        year: Number(generateYearInput?.value || yearInput?.value || new Date().getFullYear()),
        persona_label: personaInput?.value || "founder-biographer",
        style_brief: styleInput?.value || "Narrative nonfiction in a Walter Isaacson-inspired mode: warm, observant, specific, psychologically perceptive, and grounded in real scenes.",
        include_private_context: true
      };
      const data = await postJson("/api/v1/lab/autobiographer/year-chapters/generate", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });
  publishYearBtn.addEventListener("click", async () => {
    try {
      const payload = {
        year: Number(generateYearInput?.value || yearInput?.value || new Date().getFullYear()),
        persona_label: personaInput?.value || "founder-biographer",
        style_brief: styleInput?.value || "Narrative nonfiction in a Walter Isaacson-inspired mode: warm, observant, specific, psychologically perceptive, and grounded in real scenes.",
        include_private_context: true,
        force_regenerate: String(forceInput?.value || "false") === "true",
        subdir: "notes-drafts"
      };
      const data = await postJson("/api/v1/lab/autobiographer/publish-year-note", payload, true);
      pretty(output, data);
      await load();
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });
  publishBtn.addEventListener("click", async () => {
    try {
      const payload = {
        year: Number(generateYearInput?.value || yearInput?.value || new Date().getFullYear()),
        month: Number(generateMonthInput?.value || new Date().getMonth() + 1),
        persona_label: personaInput?.value || "founder-biographer",
        style_brief: styleInput?.value || "Narrative nonfiction in a Walter Isaacson-inspired mode: warm, observant, specific, psychologically perceptive, and grounded in real scenes.",
        include_private_context: true,
        force_regenerate: false,
        subdir: "notes-drafts"
      };
      const data = await postJson("/api/v1/lab/autobiographer/publish-live-note", payload, true);
      pretty(output, data);
    } catch (err) {
      pretty(output, { error: String(err) });
    }
  });

  load();
}

bindToken();
bindDailyBrief();
bindWeeklySnapshot();
bindDecisionJournal();
bindAutobiographer();
bindAppleTools();
