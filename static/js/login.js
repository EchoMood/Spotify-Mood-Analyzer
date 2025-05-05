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

// Flash message fade-out and close functionality
document.addEventListener('DOMContentLoaded', () => {
  const flashMessages = document.querySelectorAll('.flash-message');

  flashMessages.forEach(msg => {
    // Auto fade-out after 5 seconds
    setTimeout(() => {
      msg.classList.add('fade-out');
    }, 5000);

    // Manually dismiss on click of close icon
    const closeBtn = msg.querySelector('.flash-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', () => {
      // Add fade-out animation
      msg.classList.add('fade-out');

      // Wait for the animation to complete before removing from DOM
      setTimeout(() => {
        msg.remove();
      }, 500); // Match this duration to your CSS transition (500ms)
    });
    }
  });
});