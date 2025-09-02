(function() {
  const btn = document.getElementById('cartButton');
  const dropdown = document.getElementById('cartDropdown');
  if (!btn || !dropdown) return;

  let loaded = false;

  function openDropdown() {
    dropdown.classList.add('open');
    btn.setAttribute('aria-expanded', 'true');
    if (!loaded) {
      fetch("/shop/cart-preview", { credentials: 'same-origin' })
        .then(r => r.text())
        .then(html => {
          dropdown.innerHTML = html;
          loaded = true;
        })
        .catch(() => {
          dropdown.innerHTML = '<div class="cart-preview"><div class="empty">Unable to load cart.</div></div>';
        });
    }
  }

  function closeDropdown() {
    dropdown.classList.remove('open');
    btn.setAttribute('aria-expanded', 'false');
  }

  btn.addEventListener('click', (e) => {
    e.preventDefault();
    if (dropdown.classList.contains('open')) {
      closeDropdown();
    } else {
      openDropdown();
    }
  });

  document.addEventListener('click', (e) => {
    if (!dropdown.contains(e.target) && !btn.contains(e.target)) {
      closeDropdown();
    }
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeDropdown();
  });
})();
