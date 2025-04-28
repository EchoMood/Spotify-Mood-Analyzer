// Number of dots
const numDots = 36;
const box = document.querySelector('.box');

for (let i = 0; i < numDots; i++) {
  const dot = document.createElement('div');
  dot.classList.add('dot');
  dot.style.setProperty('--i', i);
  box.appendChild(dot);
}
