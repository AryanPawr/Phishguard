(function initLocalScorer() {
  window.PhishGuard = window.PhishGuard || {};

  function combine(results) {
    const score =
      results.keyword.score * 0.25 +
      results.link.score * 0.35 +
      results.domain.score * 0.25 +
      results.spoof.score * 0.15;
    return Math.min(Math.max(score, 0), 1);
  }

  function analyze(payload) {
    const keyword = window.PhishGuard.keywordEngine.analyze(payload);
    const link = window.PhishGuard.linkAnalyzer.analyze(payload.links);
    const domain = window.PhishGuard.domainMismatch.analyze(payload);
    const spoof = window.PhishGuard.spoofDetector.analyze(payload);
    const results = { keyword, link, domain, spoof };
    return {
      score: Number(combine(results).toFixed(4)),
      reasons: [...keyword.reasons, ...link.reasons, ...domain.reasons, ...spoof.reasons],
      features: results
    };
  }

  window.PhishGuard.localScorer = { analyze };
})();

