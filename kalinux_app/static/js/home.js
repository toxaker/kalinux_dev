const toggleButton = document.getElementById('theme-toggle');
const app = document.getElementById('app');

toggleButton.addEventListener('click', () => {
  const currentTheme = document.documentElement.getAttribute('data-theme');
  if (currentTheme === 'light') {
    document.documentElement.removeAttribute('data-theme');
    toggleButton.textContent = 'Сменить тему';
  } else {
    document.documentElement.setAttribute('data-theme', 'light');
    toggleButton.textContent = 'Вернуть тему';
  }
});

// Fade-in Effect on Scroll
const sections = document.querySelectorAll('.section');
const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
      }
    });
  },
  { threshold: 0.1 }
);

sections.forEach((section) => {
  observer.observe(section);
});
