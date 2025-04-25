document.addEventListener('DOMContentLoaded', () => {

    const cards = document.querySelectorAll('.mood-card');
  
    // Float effect on mouse move
    cards.forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
  
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
  
        const rotateX = (y - centerY) / 12;
        const rotateY = (x - centerX) / 12;
  
        card.style.transform = `rotateX(${-rotateX}deg) rotateY(${rotateY}deg) scale(1.05)`;
      });
  
      card.addEventListener('mouseleave', () => {
        card.style.transform = 'rotateX(0) rotateY(0) scale(1)';
      });
  
      // Change background color based on mood
      card.addEventListener('click', () => {
        const moodName = card.querySelector('h3').innerText.toLowerCase();
  
        switch (moodName) {
          case 'happy':
            document.body.style.background = 'linear-gradient(180deg, #ffde7d, #ff9a8b)';
            break;
          case 'sad':
            document.body.style.background = 'linear-gradient(180deg, #4e54c8, #8f94fb)';
            break;
          case 'chill':
            document.body.style.background = 'linear-gradient(180deg, #00c9ff, #92fe9d)';
            break;
          case 'energetic':
            document.body.style.background = 'linear-gradient(180deg, #ff6e7f, #bfe9ff)';
            break;
          case 'nolstalgic':
            document.body.style.background = 'linear-gradient(180deg, #667eea, #764ba2)';
            break;
          default:
            document.body.style.background = 'linear-gradient(180deg,rgb(5, 67, 20), #1c0130)';
        }
      });
    });
  
    // Scroll functionality
    const scrollContainer = document.querySelector('.mood-cards-scroll');
    const leftButton = document.getElementById('scroll-left');
    const rightButton = document.getElementById('scroll-right');
  
    if (leftButton && rightButton && scrollContainer) {
      leftButton.addEventListener('click', () => {
        scrollContainer.scrollBy({ left: -300, behavior: 'smooth' });
      });
  
      rightButton.addEventListener('click', () => {
        scrollContainer.scrollBy({ left: 300, behavior: 'smooth' });
      });
    }
  
  });
  