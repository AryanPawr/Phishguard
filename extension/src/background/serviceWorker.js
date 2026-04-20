/* global PhishGuardApiClient */
importScripts("apiClient.js");

const apiClient = new PhishGuardApiClient();
const extensionApi = typeof browser !== "undefined" ? browser : chrome;

extensionApi.runtime.onInstalled.addListener(() => {
  extensionApi.storage.local.set({
    phishguardSettings: apiClient.defaultSettings()
  });
});

extensionApi.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (!message || !["PHISHGUARD_ANALYZE", "PHISHGUARD_FEEDBACK"].includes(message.type)) {
    return false;
  }

  const action =
    message.type === "PHISHGUARD_FEEDBACK"
      ? apiClient.submitFeedback(message.payload)
      : apiClient.analyze(message.payload, message.cacheKey, { bypassCache: Boolean(message.bypassCache) });

  if (typeof browser !== "undefined") {
    return action
      .then((result) => ({ ok: true, result }))
      .catch((error) => ({
        ok: false,
        error: {
          message: error.message,
          retryAfterSeconds: error.retryAfterSeconds || null
        }
      }));
  }

  action
    .then((result) => sendResponse({ ok: true, result }))
    .catch((error) => {
      sendResponse({
        ok: false,
        error: {
          message: error.message,
          retryAfterSeconds: error.retryAfterSeconds || null
        }
      });
    });

  return true;
});
