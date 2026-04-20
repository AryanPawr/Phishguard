(function initBadge() {
  window.PhishGuard = window.PhishGuard || {};

  function setPageBadge(classification) {
    document.documentElement.dataset.phishguardRisk = classification || "unknown";
  }

  window.PhishGuard.badge = { setPageBadge };
})();

