// static/js/index.js
// Listen for the page to be fully parsed before running scripts
document.addEventListener('DOMContentLoaded', () => {
  // Query the button that starts the login flow
  const btn = document.querySelector('.get-started-btn');
  if (btn) {
    // Attach a click handler to redirect to the login page
    btn.addEventListener('click', () => {
      window.location.href = '/login';
    });
  }
});