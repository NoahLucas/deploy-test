(function () {
  var TAB_PATH = '/fusion-engine';
  var TAB_LABEL = 'Fusion Engine';

  function isFusionPath() {
    return window.location.pathname === TAB_PATH || window.location.pathname.indexOf(TAB_PATH + '/') === 0;
  }

  function setActive(el, activeClass) {
    if (!el) {
      return;
    }
    if (isFusionPath()) {
      el.classList.add(activeClass);
      var link = el.querySelector('a');
      if (link) {
        link.setAttribute('aria-current', 'page');
      }
    }
  }

  function buildDesktopItem() {
    var item = document.createElement('div');
    item.className = 'header-nav-item header-nav-item--collection';

    var link = document.createElement('a');
    link.href = TAB_PATH;
    link.textContent = TAB_LABEL;
    link.setAttribute('data-animation-role', 'header-element');

    item.appendChild(link);
    setActive(item, 'header-nav-item--active');
    return item;
  }

  function buildMobileItem() {
    var item = document.createElement('div');
    item.className = 'container header-menu-nav-item header-menu-nav-item--collection';

    var link = document.createElement('a');
    link.href = TAB_PATH;

    var content = document.createElement('div');
    content.className = 'header-menu-nav-item-content';
    content.textContent = TAB_LABEL;

    link.appendChild(content);
    item.appendChild(link);
    setActive(item, 'header-menu-nav-item--active');
    return item;
  }

  function hasLink(container) {
    return Boolean(container.querySelector('a[href="' + TAB_PATH + '"]'));
  }

  function ensureDesktopNav() {
    var navLists = document.querySelectorAll('.header-nav-list');
    navLists.forEach(function (list) {
      if (hasLink(list)) {
        return;
      }
      list.appendChild(buildDesktopItem());
    });
  }

  function ensureMobileNav() {
    var wrappers = document.querySelectorAll('.header-menu-nav-wrapper');
    wrappers.forEach(function (wrapper) {
      if (hasLink(wrapper)) {
        return;
      }
      wrapper.appendChild(buildMobileItem());
    });
  }

  function apply() {
    ensureDesktopNav();
    ensureMobileNav();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', apply);
  } else {
    apply();
  }

  var observer = new MutationObserver(function () {
    apply();
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
  });
})();
