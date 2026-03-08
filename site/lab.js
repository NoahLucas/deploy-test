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

bindToken();
bindDailyBrief();
bindDecisionJournal();
bindAppleTools();
