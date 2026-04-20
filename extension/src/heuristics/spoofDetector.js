(function initSpoofDetector() {
  window.PhishGuard = window.PhishGuard || {};

  const HOMOGLYPH_RE = /[аекоорсхіΙΟ]/;
  const SPOOF_TERMS = ["secure", "login", "verify", "support", "account", "billing", "update", "password"];

  function analyze(payload) {
    const domain = String(payload.domain || payload.sender_email || "").toLowerCase();
    const reasons = [];
    let score = 0;
    if (domain.includes("xn--") || HOMOGLYPH_RE.test(domain)) {
      score += 0.3;
      reasons.push("Sender domain contains punycode or homoglyph indicators");
    }
    const spoofTerms = SPOOF_TERMS.filter((term) => domain.includes(term));
    if (spoofTerms.length >= 2) {
      score += 0.16;
      reasons.push("Sender domain combines multiple spoofing terms");
    }
    if ((domain.match(/-/g) || []).length >= 3) {
      score += 0.08;
      reasons.push("Sender domain contains excessive hyphenation");
    }
    return {
      score: Math.min(score, 1),
      reasons,
      features: {
        spoofTerms
      }
    };
  }

  window.PhishGuard.spoofDetector = { analyze };
})();

