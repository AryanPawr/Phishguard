(async function initInjector() {
  const pg = window.PhishGuard;
  if (!pg || window.__phishguardLoaded) {
    return;
  }
  window.__phishguardLoaded = true;

  let lastCacheKey = "";
  let activeViewKey = "";
  let lastAnalysis = null;
  let analyzing = false;
  const recentViewChecks = new Map();
  const VIEW_COOLDOWN_MS = 30000;

  function selectExtractor() {
    return (pg.extractors || []).find((extractor) => extractor.canHandle());
  }

  function getRuntime() {
    try {
      if (typeof browser !== "undefined" && browser.runtime?.sendMessage) {
        return { runtime: browser.runtime, promiseBased: true };
      }
      if (typeof chrome !== "undefined" && chrome.runtime?.id && chrome.runtime?.sendMessage) {
        return { runtime: chrome.runtime, promiseBased: false };
      }
    } catch (_error) {
      return null;
    }
    return null;
  }

  function sendRuntimeMessage(message) {
    const runtimeInfo = getRuntime();
    if (!runtimeInfo) {
      return Promise.reject(new Error("Extension context is not available. Reload PhishGuard from the Extensions page."));
    }
    const { runtime, promiseBased } = runtimeInfo;
    try {
      if (promiseBased) {
        return runtime.sendMessage(message);
      }
      return new Promise((resolve, reject) => {
        runtime.sendMessage(message, (response) => {
          const lastError = typeof chrome !== "undefined" ? chrome.runtime?.lastError : null;
          if (lastError) {
            reject(new Error(lastError.message));
            return;
          }
          resolve(response);
        });
      });
    } catch (error) {
      return Promise.reject(error);
    }
  }

  function markSafe() {
    pg.riskBanner.hide();
    pg.badge.setPageBadge("safe");
  }

  async function extractCurrentContext() {
    const extractor = selectExtractor();
    if (!extractor) {
      return null;
    }
    const extracted = extractor.extract();
    if (!extracted || (!extracted.body_text && !extracted.links?.length)) {
      return null;
    }
    pg.logger.debug("extractor selected", extractor.name, {
      sender: extracted.sender_email,
      subject: extracted.subject,
      bodyLength: (extracted.body_text || "").length,
      links: (extracted.links || []).length
    });

    const viewKey = [
      location.href,
      extracted.message_id || "",
      extracted.source || "",
      extracted.sender_email || "",
      extracted.subject || ""
    ].join("|");
    if (viewKey !== activeViewKey) {
      activeViewKey = viewKey;
      pg.riskBanner.hide();
    }

    const local = pg.localScorer.analyze(extracted);
    const maskedPayload = pg.privacy.maskPayload({
      ...extracted,
      heuristic_score: local.score,
      client_reasons: local.reasons
    });
    const cacheKey = await pg.privacy.hashObject(maskedPayload);

    return { extractor, extracted, viewKey, local, maskedPayload, cacheKey };
  }

  function cleanupRecentChecks() {
    for (const [key, timestamp] of recentViewChecks.entries()) {
      if (Date.now() - timestamp > 5 * 60 * 1000) {
        recentViewChecks.delete(key);
      }
    }
  }

  async function analyzeCurrentEmail(options = {}) {
    const { force = false, render = true } = options;
    const context = await extractCurrentContext();
    if (!context) {
      return null;
    }

    if (analyzing) {
      return null;
    }

    const previousViewCheck = recentViewChecks.get(context.viewKey);
    if (!force && previousViewCheck && Date.now() - previousViewCheck < VIEW_COOLDOWN_MS) {
      pg.logger.debug("skipping recent message view", context.viewKey);
      return lastAnalysis?.viewKey === context.viewKey ? lastAnalysis.result : null;
    }

    if (!force && context.cacheKey === lastCacheKey) {
      return lastAnalysis?.viewKey === context.viewKey ? lastAnalysis.result : null;
    }

    lastCacheKey = context.cacheKey;
    recentViewChecks.set(context.viewKey, Date.now());
    cleanupRecentChecks();

    const settings = await pg.storage.getSettings();
    if (!force && context.local.score < settings.suspiciousThreshold && !context.maskedPayload.links.length) {
      markSafe();
      return {
        risk_score: context.local.score,
        classification: "safe",
        confidence: "low",
        reasons: context.local.reasons,
        domain: context.maskedPayload.domain,
        source: context.maskedPayload.source
      };
    }

    analyzing = true;
    pg.logger.debug("sending analysis to backend", {
      cacheKey: context.cacheKey,
      heuristicScore: context.local.score,
      domain: context.maskedPayload.domain
    });
    try {
      const response = await sendRuntimeMessage({
        type: "PHISHGUARD_ANALYZE",
        payload: context.maskedPayload,
        cacheKey: context.cacheKey,
        bypassCache: force
      });
      if (!response?.ok) {
        if (render) {
          pg.riskBanner.renderError(response?.error?.message || "Analysis service unavailable");
        }
        return null;
      }
      const result = response.result;
      lastAnalysis = { viewKey: context.viewKey, result };
      if (activeViewKey !== context.viewKey) {
        pg.logger.debug("discarding stale analysis result", context.viewKey);
        return result;
      }
      if (render) {
        if (result?.classification === "safe") {
          markSafe();
        } else {
          pg.riskBanner.render(result);
        }
      }
      return result;
    } catch (error) {
      if (render) {
        pg.riskBanner.renderError(error.message);
      }
      return null;
    } finally {
      analyzing = false;
    }
  }

  async function submitFeedbackForResult(result, userFeedback) {
    if (!result?.sample_hash || !userFeedback) {
      throw new Error("Feedback could not be sent: missing sample id.");
    }
    const response = await sendRuntimeMessage({
      type: "PHISHGUARD_FEEDBACK",
      payload: {
        sample_hash: result.sample_hash,
        domain: result.domain || "",
        source: result.source || "extension",
        current_risk_score: Number(result.risk_score || 0),
        current_classification: result.classification || "unknown",
        user_feedback: userFeedback,
        reasons: result.reasons || []
      }
    });
    if (!response?.ok) {
      throw new Error(response?.error?.message || "Feedback service unavailable");
    }
    return response.result;
  }

  async function currentOrFreshResult(render = false) {
    const context = await extractCurrentContext();
    if (context && lastAnalysis?.viewKey === context.viewKey && lastAnalysis.result?.sample_hash) {
      return lastAnalysis.result;
    }
    return analyzeCurrentEmail({ force: true, render });
  }

  async function handlePopupMessage(message) {
    if (message.type === "PHISHGUARD_POPUP_ANALYZE") {
      const result = await analyzeCurrentEmail({ force: true, render: true });
      return { ok: Boolean(result), result };
    }
    if (message.type === "PHISHGUARD_POPUP_REPORT_RISKY") {
      const result = await currentOrFreshResult(false);
      if (!result) {
        return { ok: false, error: "No open email could be analyzed." };
      }
      const feedback = await submitFeedbackForResult(result, "report_risky");
      return { ok: true, result, feedback };
    }
    if (message.type === "PHISHGUARD_POPUP_MARK_NOT_RISKY") {
      const result = await currentOrFreshResult(false);
      if (!result) {
        return { ok: false, error: "No open email could be analyzed." };
      }
      const feedback = await submitFeedbackForResult(result, "mark_not_risky");
      return { ok: true, result, feedback };
    }
    return { ok: false, error: "Unsupported popup action." };
  }

  function registerPopupListener() {
    const runtimeInfo = getRuntime();
    if (!runtimeInfo?.runtime?.onMessage) {
      return;
    }
    runtimeInfo.runtime.onMessage.addListener((message, sender, sendResponse) => {
      if (
        !message ||
        ![
          "PHISHGUARD_POPUP_ANALYZE",
          "PHISHGUARD_POPUP_REPORT_RISKY",
          "PHISHGUARD_POPUP_MARK_NOT_RISKY"
        ].includes(message.type)
      ) {
        return false;
      }

      const action = handlePopupMessage(message);
      if (runtimeInfo.promiseBased) {
        return action;
      }
      action.then(sendResponse).catch((error) => {
        sendResponse({ ok: false, error: error.message || "Popup action failed." });
      });
      return true;
    });
  }

  async function handleFeedback(event) {
    const detail = event.detail || {};
    const result = detail.result || {};
    try {
      await submitFeedbackForResult(result, detail.user_feedback);
      pg.riskBanner.updateFeedbackStatus("Feedback saved for manual review.");
    } catch (error) {
      pg.riskBanner.updateFeedbackStatus(error.message || "Feedback could not be sent.", true);
    }
  }

  registerPopupListener();
  window.addEventListener("phishguard:feedback", handleFeedback);
  pg.domObserver.observe(analyzeCurrentEmail);
})();
