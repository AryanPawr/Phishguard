(function initLinkAnalyzer() {
  window.PhishGuard = window.PhishGuard || {};

  const DOMAIN_RE = /\b(?:[a-z0-9-]+\.)+[a-z]{2,}\b/gi;
  const SUSPICIOUS_TLDS = new Set(["zip", "mov", "top", "xyz", "icu", "click", "work", "support", "gq", "tk"]);

  function hostname(value) {
    try {
      return new URL(value).hostname.toLowerCase().replace(/^www\./, "");
    } catch (_error) {
      try {
        return new URL(`https://${value}`).hostname.toLowerCase().replace(/^www\./, "");
      } catch (_fallbackError) {
        return "";
      }
    }
  }

  function registeredDomain(host) {
    const parts = String(host || "").split(".").filter(Boolean);
    return parts.length > 2 ? parts.slice(-2).join(".") : parts.join(".");
  }

  function isIpHost(host) {
    return /^(\d{1,3}\.){3}\d{1,3}$/.test(host) || /^\[[a-f0-9:]+\]$/i.test(host);
  }

  function analyze(links) {
    const reasons = [];
    let score = 0;
    let mismatches = 0;
    let ipLinks = 0;
    let suspiciousTlds = 0;
    let encoded = 0;

    for (const link of links || []) {
      const host = hostname(link.href);
      const anchorDomains = String(link.anchor_text || "").match(DOMAIN_RE) || [];
      if (anchorDomains.length && anchorDomains.every((domain) => registeredDomain(domain) !== registeredDomain(host))) {
        mismatches += 1;
      }
      if (isIpHost(host)) {
        ipLinks += 1;
      }
      if (SUSPICIOUS_TLDS.has(host.split(".").pop())) {
        suspiciousTlds += 1;
      }
      encoded += (String(link.href || "").match(/%[0-9A-F]{2}/gi) || []).length;
    }

    if (mismatches) {
      score += 0.28;
      reasons.push("Link anchor text does not match destination domain");
    }
    if (ipLinks) {
      score += 0.22;
      reasons.push("Link uses an IP address destination");
    }
    if (suspiciousTlds) {
      score += 0.12;
      reasons.push("Link uses a high-risk top-level domain");
    }
    if (encoded > 4) {
      score += 0.08;
      reasons.push("Link contains heavy URL encoding");
    }

    return {
      score: Math.min(score, 1),
      reasons,
      features: {
        url_count: (links || []).length,
        mismatches,
        ipLinks,
        suspiciousTlds,
        encoded
      }
    };
  }

  window.PhishGuard.linkAnalyzer = {
    analyze,
    hostname,
    registeredDomain
  };
})();

