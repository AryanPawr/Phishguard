(function initPopup() {
  const extensionApi = typeof browser !== "undefined" ? browser : chrome;
  const status = document.getElementById("status");
  const resultBox = document.getElementById("result");
  const riskScore = document.getElementById("riskScore");
  const classification = document.getElementById("classification");
  const domain = document.getElementById("domain");
  const reasons = document.getElementById("reasons");
  const buttons = Array.from(document.querySelectorAll("button"));

  document.getElementById("analyze").addEventListener("click", () => runAction("PHISHGUARD_POPUP_ANALYZE"));
  document.getElementById("reportRisky").addEventListener("click", () => runAction("PHISHGUARD_POPUP_REPORT_RISKY"));
  document.getElementById("markNotRisky").addEventListener("click", () => runAction("PHISHGUARD_POPUP_MARK_NOT_RISKY"));

  async function runAction(type) {
    setBusy(true);
    setStatus(statusFor(type));
    try {
      const response = await sendToActiveTab({ type });
      if (!response?.ok) {
        throw new Error(response?.error || "The current page did not return an email analysis.");
      }
      renderResult(response.result);
      if (type === "PHISHGUARD_POPUP_REPORT_RISKY") {
        setStatus("Reported as risky for manual review.");
      } else if (type === "PHISHGUARD_POPUP_MARK_NOT_RISKY") {
        setStatus("Marked not risky for manual review.");
      } else {
        setStatus("Analysis complete.");
      }
    } catch (error) {
      setStatus(error.message || "Action failed.");
    } finally {
      setBusy(false);
    }
  }

  function sendToActiveTab(message) {
    return queryActiveTab().then((tabs) => {
      const tabId = tabs?.[0]?.id;
      if (!tabId) {
        throw new Error("No active tab found.");
      }
      return sendTabMessage(tabId, message);
    });
  }

  function queryActiveTab() {
    try {
      const result = extensionApi.tabs.query({ active: true, currentWindow: true });
      if (result && typeof result.then === "function") {
        return result;
      }
    } catch (_error) {
      // Chrome callback mode is handled below.
    }
    return new Promise((resolve, reject) => {
      extensionApi.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const lastError = typeof chrome !== "undefined" ? chrome.runtime?.lastError : null;
        if (lastError) {
          reject(new Error(lastError.message));
          return;
        }
        resolve(tabs);
      });
    });
  }

  function sendTabMessage(tabId, message) {
    try {
      const result = extensionApi.tabs.sendMessage(tabId, message);
      if (result && typeof result.then === "function") {
        return result;
      }
    } catch (_error) {
      // Chrome callback mode is handled below.
    }
    return new Promise((resolve, reject) => {
      extensionApi.tabs.sendMessage(tabId, message, (response) => {
        const lastError = typeof chrome !== "undefined" ? chrome.runtime?.lastError : null;
        if (lastError) {
          reject(new Error("Open a Gmail or Outlook email, then try again."));
          return;
        }
        resolve(response);
      });
    });
  }

  function renderResult(result = {}) {
    resultBox.hidden = false;
    riskScore.textContent = `${Math.round(Number(result.risk_score || 0) * 100)}%`;
    classification.textContent = result.classification || "unknown";
    domain.textContent = result.domain || "unknown";
    reasons.textContent = "";
    (result.reasons || []).slice(0, 5).forEach((reason) => {
      const item = document.createElement("li");
      item.textContent = reason;
      reasons.appendChild(item);
    });
  }

  function statusFor(type) {
    if (type === "PHISHGUARD_POPUP_REPORT_RISKY") {
      return "Analyzing and reporting this email...";
    }
    if (type === "PHISHGUARD_POPUP_MARK_NOT_RISKY") {
      return "Submitting not-risky feedback...";
    }
    return "Analyzing current email...";
  }

  function setStatus(message) {
    status.textContent = message;
  }

  function setBusy(isBusy) {
    buttons.forEach((button) => {
      button.disabled = isBusy;
    });
  }
})();
