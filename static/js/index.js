// static/js/index.js

document.addEventListener('DOMContentLoaded', () => {
  const btn = document.querySelector('.get-started-btn');
  if (btn) {
    btn.addEventListener('click', () => {
      window.location.href = '/login';
    });
  }

  const moodSliders = document.querySelectorAll('.mood-slider');

  moodSliders.forEach(slider => {
    slider.addEventListener('input', updateBackgroundGlow);
  });

  function updateBackgroundGlow() {
    // Retrieve slider values
    const happy = parseInt(document.getElementById('happy-slider').value);
    const sad = parseInt(document.getElementById('sad-slider').value);
    const excited = parseInt(document.getElementById('excited-slider').value);
    const motivated = parseInt(document.getElementById('motivated-slider').value);
    const chill = parseInt(document.getElementById('chill-slider').value);
    const angry = parseInt(document.getElementById('angry-slider').value);

    // Mood glow colors with stronger opacity
    const glows = [
      `rgba(255, 215, 0, ${happy / 100})`,       // happy (gold)
      `rgba(65, 105, 225, ${sad / 100})`,        // sad (blue)
      `rgba(255, 69, 0, ${excited / 100})`,      // excited (orange-red)
      `rgba(50, 205, 50, ${motivated / 100})`,   // motivated (green)
      `rgba(147, 112, 219, ${chill / 50})`,     // chill (purple)
      `rgba(220, 20, 60, ${angry / 50})`        // angry (crimson)
    ];

    // Glow gradients positioned around the screen
    const gradient = `
      radial-gradient(circle at 20% 30%, ${glows[0]} 0%, transparent 50%),
      radial-gradient(circle at 80% 30%, ${glows[1]} 0%, transparent 50%),
      radial-gradient(circle at 50% 50%, ${glows[2]} 0%, transparent 50%),
      radial-gradient(circle at 30% 70%, ${glows[3]} 0%, transparent 50%),
      radial-gradient(circle at 70% 80%, ${glows[4]} 0%, transparent 50%),
      radial-gradient(circle at 50% 90%, ${glows[5]} 0%, transparent 50%)
    `;

    // Apply layered background with glow + dark base
    document.body.style.backgroundImage = `
      linear-gradient(135deg, var(--gradient-primary), var(--gradient-secondary)),
      ${gradient}
    `;
    document.body.style.backgroundBlendMode = "screen";
  }

  updateBackgroundGlow();
});
