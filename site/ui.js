function setYear() {
  const year = document.getElementById("year");
  if (year) year.textContent = String(new Date().getFullYear());
}

function setupReveal() {
  const nodes = Array.from(document.querySelectorAll(".reveal"));
  if (!nodes.length || !("IntersectionObserver" in window)) return;
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) entry.target.classList.add("in");
    });
  }, { threshold: 0.15 });

  nodes.forEach((node, i) => {
    node.style.transitionDelay = `${Math.min(i * 70, 280)}ms`;
    io.observe(node);
  });
}

setYear();
setupReveal();
