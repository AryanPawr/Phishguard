class PhishGuardApiClient {
  constructor() {
    this.extensionApi = this.getExtensionApi();
    this.cacheVersion = "v3";
  }

  getExtensionApi() {
    if (typeof browser !== "undefined" && browser.storage?.local) {
      return browser;
    }
    if (typeof chrome !== "undefined" && chrome.storage?.local) {
      return chrome;
    }
    return null;
  }

  async analyze(payload, cacheKey, options = {}) {
    const settings = await this.getSettings();
    const cached = options.bypassCache
      ? null
      : await this.getCachedResult(cacheKey, settings.cacheTtlMinutes);
    if (cached) {
      return cached;
    }

    const response = await fetch(`${settings.apiBaseUrl}/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-PhishGuard-Client": "extension-mv3"
      },
      body: JSON.stringify(payload),
      credentials: "omit",
      cache: "no-store"
    });

    if (response.status === 429) {
      const retryAfterSeconds = Number(response.headers.get("Retry-After") || "60");
      const error = new Error("Rate limit exceeded");
      error.retryAfterSeconds = retryAfterSeconds;
      throw error;
    }

    if (!response.ok) {
      throw new Error(`Backend analysis failed with status ${response.status}`);
    }

    const result = await response.json();
    await this.cacheResult(cacheKey, result);
    return result;
  }

  async submitFeedback(payload) {
    const settings = await this.getSettings();
    const response = await fetch(`${settings.apiBaseUrl}/feedback`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-PhishGuard-Client": "extension-mv3"
      },
      body: JSON.stringify(payload),
      credentials: "omit",
      cache: "no-store"
    });
    if (!response.ok) {
      throw new Error(`Feedback submission failed with status ${response.status}`);
    }
    return response.json();
  }

  async getSettings() {
    const stored = await this.storageGet("phishguardSettings");
    return {
      apiBaseUrl: "http://localhost:8000/api",
      suspiciousThreshold: 0.28,
      cacheTtlMinutes: 60,
      ...(stored.phishguardSettings || {})
    };
  }

  async getCachedResult(cacheKey, ttlMinutes) {
    if (!cacheKey) {
      return null;
    }
    const storageKey = this.cacheKey(cacheKey);
    const stored = await this.storageGet(storageKey);
    const entry = stored[storageKey];
    if (!entry) {
      return null;
    }
    const ageMs = Date.now() - entry.createdAt;
    if (ageMs > ttlMinutes * 60 * 1000) {
      await this.storageRemove(storageKey);
      return null;
    }
    return entry.result;
  }

  async cacheResult(cacheKey, result) {
    if (!cacheKey) {
      return;
    }
    await this.storageSet({
      [this.cacheKey(cacheKey)]: {
        createdAt: Date.now(),
        result
      }
    });
  }

  cacheKey(cacheKey) {
    return `phishguardCache:${this.cacheVersion}:${cacheKey}`;
  }

  storageGet(key) {
    if (!this.extensionApi?.storage?.local) {
      return Promise.resolve({});
    }
    try {
      const result = this.extensionApi.storage.local.get(key);
      if (result && typeof result.then === "function") {
        return result.catch(() => ({}));
      }
      return new Promise((resolve) => this.extensionApi.storage.local.get(key, resolve));
    } catch (_error) {
      return Promise.resolve({});
    }
  }

  storageSet(value) {
    if (!this.extensionApi?.storage?.local) {
      return Promise.resolve();
    }
    try {
      const result = this.extensionApi.storage.local.set(value);
      if (result && typeof result.then === "function") {
        return result.catch(() => undefined);
      }
      return new Promise((resolve) => this.extensionApi.storage.local.set(value, resolve));
    } catch (_error) {
      return Promise.resolve();
    }
  }

  storageRemove(key) {
    if (!this.extensionApi?.storage?.local) {
      return Promise.resolve();
    }
    try {
      const result = this.extensionApi.storage.local.remove(key);
      if (result && typeof result.then === "function") {
        return result.catch(() => undefined);
      }
      return new Promise((resolve) => this.extensionApi.storage.local.remove(key, resolve));
    } catch (_error) {
      return Promise.resolve();
    }
  }
}
