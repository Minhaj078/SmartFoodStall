// ===== SMART FOOD STALL - MAIN.JS =====

// Auto-dismiss alerts after 5 seconds
document.addEventListener('DOMContentLoaded', () => {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.animation = 'slideOut 0.3s ease forwards';
            setTimeout(() => alert.remove(), 300);
        }, 5000);
    });
});

// Toggle mobile nav
function toggleMenu() {
    const navLinks = document.querySelector('.nav-links');
    navLinks.classList.toggle('open');
}

// Close nav on outside click
document.addEventListener('click', (e) => {
    const nav = document.querySelector('.nav-links');
    const toggle = document.querySelector('.nav-toggle');
    if (nav && nav.classList.contains('open') && !nav.contains(e.target) && !toggle.contains(e.target)) {
        nav.classList.remove('open');
    }
});

// Animate numbers on scroll (for KPI cards)
function animateCounter(el, target, duration = 1000) {
    let start = 0;
    const step = (timestamp) => {
        if (!start) start = timestamp;
        const progress = Math.min((timestamp - start) / duration, 1);
        el.textContent = Math.floor(progress * target);
        if (progress < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
}

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const el = entry.target;
            const target = parseInt(el.textContent);
            if (!isNaN(target) && target > 0) {
                animateCounter(el, target);
            }
            observer.unobserve(el);
        }
    });
}, { threshold: 0.5 });

document.querySelectorAll('.kpi-value, .hero-stat-num').forEach(el => {
    if (!isNaN(parseInt(el.textContent))) observer.observe(el);
});

// Form auto-style: add 'focused' class for floating labels
document.querySelectorAll('.form-group input, .form-group textarea, .form-group select').forEach(el => {
    el.addEventListener('focus', () => el.parentElement.classList.add('focused'));
    el.addEventListener('blur', () => el.parentElement.classList.remove('focused'));
});

// Tooltip helper
document.querySelectorAll('[title]').forEach(el => {
    el.style.cursor = 'help';
});

// CSS animation for slide out
const style = document.createElement('style');
style.textContent = `
@keyframes slideOut {
    to { transform: translateX(100%); opacity: 0; }
}
`;
document.head.appendChild(style);

function toggleDropdown() {
    document.getElementById("dropdownMenu").classList.toggle("show");
}

document.addEventListener("click", function (event) {
    const menu = document.getElementById("userMenu");
    if (!menu.contains(event.target)) {
        document.getElementById("dropdownMenu").classList.remove("show");
    }
});