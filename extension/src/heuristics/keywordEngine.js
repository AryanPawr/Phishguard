(function initKeywordEngine() {
  window.PhishGuard = window.PhishGuard || {};

  const URGENCY = [
    "urgent",
    "immediately",
    "final notice",
    "within 24 hours",
    "limited time",
    "account suspended",
    "locked",
    "action required"
  ];
  const CREDENTIALS = [
    "verify your account",
    "confirm your identity",
    "reset your password",
    "update your password",
    "sign in to continue",
    "re-enter your password"
  ];
  const FINANCIAL = [
    "payment failed",
    "invoice overdue",
    "wire transfer",
    "refund pending",
    "billing issue"
  ];

  function countMatches(text, phrases) {
    const normalized = String(text || "").toLowerCase();
    return phrases.filter((phrase) => normalized.includes(phrase)).length;
  }

  function analyze(payload) {
    const text = `${payload.subject || ""} ${payload.body_text || ""}`;
    const urgency = countMatches(text, URGENCY);
    const credentials = countMatches(text, CREDENTIALS);
    const financial = countMatches(text, FINANCIAL);
    const reasons = [];
    if (urgency) reasons.push("Urgent language detected");
    if (credentials) reasons.push("Credential request language detected");
    if (financial) reasons.push("Financial pressure language detected");
    return {
      score: Math.min(1, urgency * 0.08 + credentials * 0.18 + financial * 0.1),
      reasons,
      features: {
        urgency,
        credentials,
        financial
      }
    };
  }

  window.PhishGuard.keywordEngine = { analyze };
})();

