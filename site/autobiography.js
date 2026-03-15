function setText(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value;
}

function escapeHtml(value) {
  return String(value || "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;");
}

function formatInline(value) {
  return escapeHtml(value).replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdown(markdown) {
  const lines = String(markdown || "").split(/\r?\n/);
  const parts = [];
  let paragraph = [];
  let listItems = [];

  function flushParagraph() {
    if (!paragraph.length) return;
    parts.push(`<p>${formatInline(paragraph.join(" "))}</p>`);
    paragraph = [];
  }

  function flushList() {
    if (!listItems.length) return;
    parts.push(`<ul>${listItems.map((item) => `<li>${formatInline(item)}</li>`).join("")}</ul>`);
    listItems = [];
  }

  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }
    if (line.startsWith("### ")) {
      flushParagraph();
      flushList();
      parts.push(`<h3>${formatInline(line.slice(4))}</h3>`);
      continue;
    }
    if (line.startsWith("## ")) {
      flushParagraph();
      flushList();
      parts.push(`<h2>${formatInline(line.slice(3))}</h2>`);
      continue;
    }
    if (line.startsWith("# ")) {
      flushParagraph();
      flushList();
      parts.push(`<h1>${formatInline(line.slice(2))}</h1>`);
      continue;
    }
    if (line.startsWith("- ")) {
      flushParagraph();
      listItems.push(line.slice(2));
      continue;
    }
    flushList();
    paragraph.push(line);
  }

  flushParagraph();
  flushList();
  return parts.join("");
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  return date.toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

function cleanRenderedAutobiography(host) {
  if (!host) return;
  const firstHeading = host.querySelector("h1");
  if (firstHeading) firstHeading.remove();

  const firstParagraph = host.querySelector("p");
  if (
    firstParagraph &&
    /living chapter feed updated throughout the year/i.test(firstParagraph.textContent || "")
  ) {
    firstParagraph.remove();
  }
}

async function loadAutobiography() {
  try {
    const res = await fetch("/api/v1/public/autobiography/live", { headers: { Accept: "application/json" } });
    if (!res.ok) throw new Error("autobiography unavailable");
    const data = await res.json();
    setText("autobio-summary", data.summary || "Living chapter loaded.");
    setText("autobio-slug", data.slug || "autobiography-live");
    setText("autobio-updated", formatDate(data.generated_at));
    document.title = `${data.title || "Autobiography"} | Noah Lucas`;
    const host = document.getElementById("autobio-content");
    if (host) {
      host.classList.remove("autobio-empty");
      host.innerHTML = renderMarkdown(data.body_markdown);
      cleanRenderedAutobiography(host);
    }
  } catch (_) {
    setText("autobio-summary", "The living autobiography is not available yet.");
    setText("autobio-slug", "Unavailable");
    setText("autobio-updated", "Unavailable");
  }
}

loadAutobiography();
