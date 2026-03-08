const aura = document.querySelector('.hybrid-aura');

if (aura) {
  window.addEventListener('pointermove', (event) => {
    const x = (event.clientX / window.innerWidth) * 100;
    const y = (event.clientY / window.innerHeight) * 100;
    aura.style.setProperty('--mx', `${x}%`);
    aura.style.setProperty('--my', `${y}%`);
  });
}

const observer = new IntersectionObserver((entries) => {
  entries.forEach((entry) => {
    if (entry.isIntersecting) entry.target.classList.add('in');
  });
}, { threshold: 0.18 });

document.querySelectorAll('.hybrid-work article, .notes-columns article, .hybrid-signal-strip article').forEach((node, index) => {
  node.style.transitionDelay = `${Math.min(index * 90, 360)}ms`;
  observer.observe(node);
});
