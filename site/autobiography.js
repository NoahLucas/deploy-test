function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function renderMarkdown(markdown) {
  const safe = String(markdown || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
  return safe
    .replace(/^### (.*)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/^- (.*)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/gs, "<ul>$1</ul>")
    .replace(/\n\n/g, "</p><p>");
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

async function loadAutobiography() {
  try {
    const res = await fetch("/api/v1/public/autobiography/live", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("autobiography unavailable");
    const data = await res.json();
    setText("autobio-summary", data.summary || "Living chapter loaded.");
    setText("autobio-slug", data.slug || "autobiography-live");
    setText("autobio-updated", formatDate(data.generated_at));
    const host = document.getElementById("autobio-content");
    if (host) {
      host.classList.remove("autobio-empty");
      host.innerHTML = `<p>${renderMarkdown(data.body_markdown)}</p>`;
    }
  } catch (_) {
    setText("autobio-summary", "The living autobiography is not available yet.");
    setText("autobio-slug", "Unavailable");
    setText("autobio-updated", "Unavailable");
  }
}

loadAutobiography();
