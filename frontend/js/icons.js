/* =============================================================================
 *  Icones - pose les glyphes Reicon (vendor/reicon-icons.js) dans la page.
 *
 *  Contrat : un element portant data-icon="<nom>" devient un <svg> en
 *  currentColor, qui garde ses classes, son style et son id. Un <svg> deja
 *  rendu dont data-icon change (bascule du theme) est redessine en place.
 *  Un nom inconnu est signale en console et laisse l'element vide, jamais
 *  remplace par un autre glyphe.
 *
 *  Appel : Icons.render() apres chaque injection de HTML contenant des icones.
 * ========================================================================== */
(function () {
  "use strict";

  var SVG_NS = "http://www.w3.org/2000/svg";
  var glyphs = window.REICON_ICONS || {};

  function build(node, name) {
    var svg = node.namespaceURI === SVG_NS ? node : document.createElementNS(SVG_NS, "svg");
    if (svg !== node) {
      Array.prototype.forEach.call(node.attributes, function (attr) {
        svg.setAttribute(attr.name, attr.value);
      });
    }
    svg.setAttribute("xmlns", SVG_NS);
    svg.setAttribute("viewBox", "0 0 24 24");
    svg.setAttribute("fill", "none");
    svg.setAttribute("width", "24");
    svg.setAttribute("height", "24");
    svg.setAttribute("aria-hidden", "true");
    svg.innerHTML = glyphs[name];
    return svg;
  }

  function render(root) {
    var scope = root || document;
    scope.querySelectorAll("[data-icon]").forEach(function (node) {
      var name = node.getAttribute("data-icon");
      if (!Object.prototype.hasOwnProperty.call(glyphs, name)) {
        console.error("Icons : glyphe inconnu", name);
        return;
      }
      if (node.dataset.iconDrawn === name) return;
      var svg = build(node, name);
      svg.dataset.iconDrawn = name;
      if (svg !== node) node.replaceWith(svg);
    });
  }

  window.Icons = { render: render };
})();
