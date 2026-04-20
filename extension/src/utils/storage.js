(function initStorage() {
  window.PhishGuard = window.PhishGuard || {};

  function getExtensionApi() {
    if (typeof browser !== "undefined" && browser.storage?.local) {
      return browser;
    }
    if (typeof chrome !== "undefined" && chrome.storage?.local) {
      return chrome;
    }
    return null;
  }

  function storageGet(key) {
    const extensionApi = getExtensionApi();
    if (!extensionApi) {
      return Promise.resolve({});
    }
    try {
      const result = extensionApi.storage.local.get(key);
      if (result && typeof result.then === "function") {
        return result.catch(() => ({}));
      }
      return new Promise((resolve) => extensionApi.storage.local.get(key, resolve));
    } catch (_error) {
      return Promise.resolve({});
    }
  }

  window.PhishGuard.storage = {
    async getSettings() {
      const stored = await storageGet("phishguardSettings");
      return {
        suspiciousThreshold: 0.28,
        ...(stored.phishguardSettings || {})
      };
    }
  };
})();
