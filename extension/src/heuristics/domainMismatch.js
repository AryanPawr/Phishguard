(function initDomainMismatch() {
  window.PhishGuard = window.PhishGuard || {};

  const BRAND_DOMAINS = {
    amazon: ["amazon.com"],
    apple: ["apple.com", "icloud.com"],
    chase: ["chase.com"],
    dhl: ["dhl.com"],
    docusign: ["docusign.com", "docusign.net"],
    dropbox: ["dropbox.com"],
    github: ["github.com"],
    google: ["google.com", "gmail.com"],
    linkedin: ["linkedin.com"],
    microsoft: ["microsoft.com", "office.com", "outlook.com", "live.com"],
    netflix: ["netflix.com"],
    paypal: ["paypal.com"],
    slack: ["slack.com"],
    stripe: ["stripe.com"],
    ups: ["ups.com"]
  };

  function senderDomain(sender) {
    return String(sender || "").split("@").pop().toLowerCase().replace(/^www\./, "");
  }

  function mentionedBrands(text) {
    const normalized = String(text || "").toLowerCase();
    return Object.keys(BRAND_DOMAINS).filter((brand) => normalized.includes(brand));
  }

  function isVerified(brand, domain) {
    return (BRAND_DOMAINS[brand] || []).some((known) => domain === known || domain.endsWith(`.${known}`));
  }

  function analyze(payload) {
    const domain = senderDomain(payload.sender_email || payload.domain);
    const text = `${payload.display_name || ""} ${payload.subject || ""}`;
    const brands = mentionedBrands(text);
    const mismatched = brands.filter((brand) => !isVerified(brand, domain));
    const reasons = [];
    if (mismatched.length) {
      reasons.push("Sender identity references a brand from an unverified domain");
    }
    return {
      score: mismatched.length ? 0.28 : 0,
      reasons,
      features: {
        sender_domain: domain,
        brand_mentions: brands,
        mismatched_brands: mismatched
      }
    };
  }

  window.PhishGuard.domainMismatch = { analyze };
})();

