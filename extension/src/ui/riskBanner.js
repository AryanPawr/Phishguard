(function initRiskBanner() {
  window.PhishGuard = window.PhishGuard || {};

  const BANNER_ID = "phishguard-risk-banner";
  const STYLE_ID = "phishguard-risk-style";

  function ensureStyle() {
    if (document.getElementById(STYLE_ID)) {
      return;
    }
    const style = document.createElement("style");
    style.id = STYLE_ID;
    style.textContent = `
      #${BANNER_ID} {
        position: fixed;
        top: 12px;
        right: 12px;
        z-index: 2147483647;
        width: min(420px, calc(100vw - 24px));
        border: 1px solid #d4d4d4;
        border-radius: 8px;
        background: #ffffff;
        color: #171717;
        box-shadow: 0 14px 36px rgba(0,0,0,.18);
        font: 14px/1.45 system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }
      #${BANNER_ID} .pg-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 12px;
        padding: 12px 14px;
        border-bottom: 1px solid #e5e5e5;
      }
      #${BANNER_ID} .pg-title {
        font-weight: 700;
      }
      #${BANNER_ID} .pg-score {
        font-variant-numeric: tabular-nums;
        font-weight: 700;
      }
      #${BANNER_ID} .pg-body {
        padding: 12px 14px;
      }
      #${BANNER_ID} .pg-meta {
        margin-top: 2px;
        color: #525252;
        font-size: 12px;
      }
      #${BANNER_ID} .pg-reasons {
        margin: 8px 0 0;
        padding-left: 18px;
      }
      #${BANNER_ID} .pg-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 12px;
      }
      #${BANNER_ID} button {
        border: 1px solid #262626;
        border-radius: 6px;
        background: #262626;
        color: #fff;
        cursor: pointer;
        padding: 6px 9px;
      }
      #${BANNER_ID} button.pg-secondary {
        background: #fff;
        color: #262626;
      }
      #${BANNER_ID} button:disabled {
        cursor: default;
        opacity: .65;
      }
      #${BANNER_ID} .pg-feedback-status {
        margin-top: 8px;
        min-height: 18px;
        color: #525252;
        font-size: 12px;
      }
      #${BANNER_ID}[data-risk="safe"] { border-top: 5px solid #159947; }
      #${BANNER_ID}[data-risk="suspicious"] { border-top: 5px solid #d97706; }
      #${BANNER_ID}[data-risk="phishing"] { border-top: 5px solid #dc2626; }
      #${BANNER_ID}[data-risk="error"] { border-top: 5px solid #737373; }
    `;
    document.documentElement.appendChild(style);
  }

  function headline(result) {
    if (result.classification === "phishing") {
      return "Phishing risk detected";
    }
    if (result.classification === "suspicious") {
      return "Suspicious message";
    }
    if (result.classification === "safe") {
      return "No phishing indicators found";
    }
    return "PhishGuard unavailable";
  }

  function render(result) {
    if (!["suspicious", "phishing"].includes(result.classification)) {
      hide();
      window.PhishGuard.badge.setPageBadge(result.classification || "unknown");
      return;
    }

    ensureStyle();
    hide();
    const banner = document.createElement("section");
    banner.id = BANNER_ID;
    banner.dataset.risk = result.classification || "error";
    banner.setAttribute("role", "status");
    banner.setAttribute("aria-live", "polite");

    const reasons = (result.reasons || []).slice(0, 4);
    banner.innerHTML = `
      <div class="pg-header">
          <div>
            <div class="pg-title">PhishGuard</div>
            <div>${headline(result)}</div>
            <div class="pg-meta">Sender: ${escapeHtml(result.domain || "unknown domain")}</div>
          </div>
        <div class="pg-score">${Math.round(Number(result.risk_score || 0) * 100)}%</div>
        <button type="button" data-pg-dismiss aria-label="Dismiss PhishGuard banner">Close</button>
      </div>
      <div class="pg-body">
        <div>Confidence: ${result.confidence || "low"}</div>
        ${
          reasons.length
            ? `<ul class="pg-reasons">${reasons.map((reason) => `<li>${escapeHtml(reason)}</li>`).join("")}</ul>`
            : ""
        }
        <div class="pg-actions" aria-label="PhishGuard feedback">
          <button type="button" class="pg-secondary" data-pg-feedback="mark_not_risky">Mark not risky</button>
          <button type="button" data-pg-feedback="report_risky">Report risky</button>
        </div>
        <div class="pg-feedback-status" aria-live="polite"></div>
      </div>
    `;
    banner.querySelector("[data-pg-dismiss]").addEventListener("click", () => banner.remove());
    banner.querySelectorAll("[data-pg-feedback]").forEach((button) => {
      button.addEventListener("click", () => {
        const userFeedback = button.getAttribute("data-pg-feedback");
        updateFeedbackStatus("Sending feedback for review...");
        banner.querySelectorAll("[data-pg-feedback]").forEach((item) => {
          item.disabled = true;
        });
        window.dispatchEvent(
          new CustomEvent("phishguard:feedback", {
            detail: {
              user_feedback: userFeedback,
              result
            }
          })
        );
      });
    });
    document.documentElement.appendChild(banner);
    window.PhishGuard.badge.setPageBadge(result.classification);
  }

  function renderError(message) {
    hide();
    window.PhishGuard.badge.setPageBadge("error");
    if (window.PhishGuard.logger) {
      window.PhishGuard.logger.warn(message || "Analysis service unavailable");
    }
  }

  function updateFeedbackStatus(message, isError = false) {
    const banner = document.getElementById(BANNER_ID);
    if (!banner) {
      return;
    }
    const status = banner.querySelector(".pg-feedback-status");
    if (!status) {
      return;
    }
    status.textContent = message || "";
    status.style.color = isError ? "#b91c1c" : "#525252";
    if (isError) {
      banner.querySelectorAll("[data-pg-feedback]").forEach((item) => {
        item.disabled = false;
      });
    }
  }

  function hide() {
    const existing = document.getElementById(BANNER_ID);
    if (existing) {
      existing.remove();
    }
  }

  function escapeHtml(value) {
    return String(value)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }

  window.PhishGuard.riskBanner = { render, renderError, updateFeedbackStatus, hide };
})();
