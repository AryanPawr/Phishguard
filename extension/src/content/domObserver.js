(function initDomObserver() {
  window.PhishGuard = window.PhishGuard || {};

  function observe(callback) {
    let timer = null;
    const schedule = () => {
      window.clearTimeout(timer);
      timer = window.setTimeout(callback, 600);
    };
    const observer = new MutationObserver(schedule);
    observer.observe(document.body || document.documentElement, {
      childList: true,
      subtree: true,
      characterData: false
    });
    window.addEventListener("hashchange", schedule);
    window.addEventListener("popstate", schedule);
    const interval = window.setInterval(schedule, 2000);
    schedule();
    return {
      disconnect() {
        observer.disconnect();
        window.clearInterval(interval);
        window.removeEventListener("hashchange", schedule);
        window.removeEventListener("popstate", schedule);
      }
    };
  }

  window.PhishGuard.domObserver = { observe };
})();
