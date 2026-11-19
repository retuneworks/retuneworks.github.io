const toggle = document.querySelector('.menu-toggle');
const nav = document.querySelector('.site-nav');

if (toggle && nav) {
  toggle.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') === 'true';
    toggle.setAttribute('aria-expanded', String(!open));
    nav.classList.toggle('open', !open);
  });
  nav.addEventListener('click', (event) => {
    if (event.target.closest('a')) {
      toggle.setAttribute('aria-expanded', 'false');
      nav.classList.remove('open');
    }
  });
}

// Keep the shared Japanese navigation current without duplicating every page template.
if (document.documentElement.lang === 'ja') {
  const navList = document.querySelector('.site-nav .nav-list');
  if (navList && !navList.querySelector('a[href="/buy/"]')) {
    const aiItem = navList.querySelector('a[href="/ai/"]')?.closest('li');
    if (aiItem) {
      const buyItem = document.createElement('li');
      buyItem.innerHTML = '<a href="/buy/">買取</a>';
      navList.insertBefore(buyItem, aiItem);
    }
  }

  document.querySelectorAll('a[href="/contact/"]').forEach((link) => {
    link.href = '/#contact';
  });

  const footer = document.querySelector('.site-footer');
  if (footer && !footer.querySelector('a[href="/buy/"]')) {
    const footerLists = [...footer.querySelectorAll('.footer-links')];
    const list = footerLists.find((candidate) => candidate.querySelector('a[href="/#contact"]')) || footerLists[0];
    if (list) {
      const item = document.createElement('li');
      item.innerHTML = '<a href="/buy/">買取のご案内</a>';
      const contactItem = list.querySelector('a[href="/#contact"]')?.closest('li');
      list.insertBefore(item, contactItem || list.firstElementChild);
    }
  }
}
