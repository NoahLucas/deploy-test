function buildSelectionPrompt(text) {
  return [
    "You are Noah's private product intelligence copilot.",
    "",
    "Analyze the selected text and return:",
    "1) Strategic signal",
    "2) Execution risk",
    "3) Decision options (3)",
    "4) Recommended next action for this week",
    "",
    "Selected text:",
    text
  ].join("\n");
}

function setupRadarSelectionPrompt() {
  const tooltip = document.createElement("button");
  tooltip.type = "button";
  tooltip.textContent = "Copy AI Prompt";
  tooltip.style.position = "fixed";
  tooltip.style.zIndex = "9999";
  tooltip.style.display = "none";
  tooltip.style.border = "1px solid rgba(241,235,223,0.3)";
  tooltip.style.borderRadius = "999px";
  tooltip.style.padding = "0.4rem 0.7rem";
  tooltip.style.fontFamily = "IBM Plex Mono, monospace";
  tooltip.style.fontSize = "0.72rem";
  tooltip.style.background = "rgba(12,10,11,0.92)";
  tooltip.style.color = "#f7d994";
  document.body.appendChild(tooltip);

  let currentPrompt = "";

  const hide = () => {
    tooltip.style.display = "none";
    currentPrompt = "";
  };

  document.addEventListener("mouseup", () => {
    const selection = window.getSelection();
    const text = selection ? selection.toString().trim() : "";
    if (!text || text.length < 12) {
      hide();
      return;
    }
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    currentPrompt = buildSelectionPrompt(text);
    tooltip.style.left = `${Math.max(8, rect.left + rect.width / 2 - 55)}px`;
    tooltip.style.top = `${Math.max(8, rect.top - 38)}px`;
    tooltip.style.display = "inline-block";
  });

  document.addEventListener("mousedown", (event) => {
    if (!tooltip.contains(event.target)) hide();
  });

  tooltip.addEventListener("click", async () => {
    if (!currentPrompt) return;
    try {
      await navigator.clipboard.writeText(currentPrompt);
      tooltip.textContent = "Copied";
      setTimeout(() => {
        tooltip.textContent = "Copy AI Prompt";
        hide();
      }, 900);
    } catch (_) {
      hide();
    }
  });
}

setupRadarSelectionPrompt();
