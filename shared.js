// shared.js — inject sidebar + check session on every protected page
(function() {
  // ── Auth check ──────────────────────────────────────────────────────────────
  fetch('/api/me', { credentials: 'include' })
    .then(r => r.json())
    .then(d => {
      if (!d.logged_in) { window.location.href = '/login.html'; return; }
      const uname = d.username || 'Owner';
      const avatar = document.getElementById('avatar-char');
      const userDisplay = document.getElementById('user-display');
      if (avatar) avatar.textContent = uname[0].toUpperCase();
      if (userDisplay) userDisplay.textContent = uname;
    })
    .catch(() => {});

  // ── Active nav highlight ────────────────────────────────────────────────────
  const path = window.location.pathname.split('/').pop() || 'home.html';
  document.querySelectorAll('.nav-item').forEach(el => {
    const href = el.getAttribute('href') || '';
    if (href === path || href.includes(path)) {
      el.classList.add('active');
    }
  });
})();
