(function initLogger() {
  window.PhishGuard = window.PhishGuard || {};
  window.PhishGuard.logger = {
    debug(...args) {
      if (window.localStorage.getItem("phishguardDebug") === "true") {
        console.debug("[PhishGuard]", ...args);
      }
    },
    warn(...args) {
      console.warn("[PhishGuard]", ...args);
    }
  };
})();

