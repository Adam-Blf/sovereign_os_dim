/*
 * icons.js · jeu d'icones unique Icons8, servi depuis le poste.
 *
 * Remplace la bibliotheque Lucide et son CDN. Le markup ne bouge pas :
 * les elements <i data-lucide="nom" class="w-5 h-5 text-gh-teal"> sont
 * convertis en masques CSS. La couleur vient de currentColor, donc toutes
 * les classes de couleur et de taille existantes continuent de fonctionner,
 * en theme clair comme en theme sombre.
 *
 * L'API window.lucide.createIcons() est conservee : tous les appels deja
 * presents dans app.js et les vues continuent de marcher sans modification.
 *
 * Rapatriement des fichiers : python tools/vendor_icons.py
 */
(function () {
  'use strict';

  var BASE = 'icons/';
  var ATTR = 'data-lucide';
  var DONE = 'data-i8';

  function styleSheet() {
    if (document.getElementById('i8-style')) return;
    var css = [
      '.i8{display:inline-block;background-color:currentColor;',
      '-webkit-mask-repeat:no-repeat;mask-repeat:no-repeat;',
      '-webkit-mask-position:center;mask-position:center;',
      '-webkit-mask-size:contain;mask-size:contain;',
      'width:1.25rem;height:1.25rem;flex:none;vertical-align:middle}',
      '.i8[hidden]{display:none}'
    ].join('');
    var tag = document.createElement('style');
    tag.id = 'i8-style';
    tag.textContent = css;
    document.head.appendChild(tag);
  }

  function convert(element) {
    if (element.getAttribute(DONE) === '1') return;
    var name = element.getAttribute(ATTR);
    if (!name) return;

    var url = 'url("' + BASE + name + '.png")';
    element.style.webkitMaskImage = url;
    element.style.maskImage = url;
    element.classList.add('i8');
    element.setAttribute(DONE, '1');
    element.setAttribute('role', 'img');
    element.setAttribute('aria-hidden', 'true');
  }

  function createIcons() {
    styleSheet();
    var nodes = document.querySelectorAll('[' + ATTR + ']');
    for (var i = 0; i < nodes.length; i++) convert(nodes[i]);
  }

  // Les vues injectent du HTML apres coup : on repasse automatiquement.
  function observe() {
    if (!window.MutationObserver) return;
    var pending = false;
    var observer = new MutationObserver(function () {
      if (pending) return;
      pending = true;
      requestAnimationFrame(function () {
        pending = false;
        createIcons();
      });
    });
    observer.observe(document.documentElement, { childList: true, subtree: true });
  }

  window.lucide = { createIcons: createIcons };
  window.icons8 = { createIcons: createIcons, base: BASE };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      createIcons();
      observe();
    });
  } else {
    createIcons();
    observe();
  }
})();
