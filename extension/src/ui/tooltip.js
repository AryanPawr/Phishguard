(function initTooltip() {
  window.PhishGuard = window.PhishGuard || {};

  function reasonList(reasons) {
    if (!reasons || !reasons.length) {
      return "No high-risk indicators detected.";
    }
    return reasons.slice(0, 5).join("\n");
  }

  window.PhishGuard.tooltip = { reasonList };
})();

