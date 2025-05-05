/**
 * login.js
 * Handles the interactive spotlight effect for background tiles on the login page.
 * Loaded with defer so it runs after HTML parsing.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Select all background tile elements
  const boxes = document.querySelectorAll('.box');

  boxes.forEach(box => {
    // On mouse move within each box, update CSS vars for --x and --y
    box.addEventListener('mousemove', e => {
      const rect = box.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;

      // Set custom properties so CSS pseudo-element can position the spotlight
      box.style.setProperty('--x', `${x}px`);
      box.style.setProperty('--y', `${y}px`);
    });
  });
});