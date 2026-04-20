(function initPrivacyUtils() {
  window.PhishGuard = window.PhishGuard || {};

  const EMAIL_RE = /\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b/gi;
  const PHONE_RE = /(?<!\d)(?:\+?\d[\d\s().-]{7,}\d)(?!\d)/g;
  const TOKEN_RE = /\b[A-Za-z0-9_-]{32,}\b/g;
  const NOREPLY_RE = /^(no-?reply|do-?not-?reply|donotreply)$/i;
  const NOTIFICATION_RE = /^(notification|notifications|alert|alerts|updates?)$/i;
  const SUPPORT_RE = /^(support|help|service|customer-service|callsupport)$/i;

  function maskText(value) {
    return String(value || "")
      .replace(EMAIL_RE, "[email]")
      .replace(PHONE_RE, "[phone]")
      .replace(TOKEN_RE, "[token]")
      .slice(0, 50000);
  }

  function maskSender(value) {
    const sender = String(value || "");
    if (!sender.includes("@")) {
      return maskText(sender);
    }
    const domain = sender.split("@").pop().toLowerCase();
    return `[local]@${domain}`;
  }

  function senderLocalCategory(value) {
    const sender = String(value || "");
    if (!sender.includes("@")) {
      return "unknown";
    }
    const local = sender.split("@")[0].trim().toLowerCase();
    if (NOREPLY_RE.test(local)) return "noreply";
    if (NOTIFICATION_RE.test(local)) return "notification";
    if (SUPPORT_RE.test(local)) return "support";
    return "unknown";
  }

  function stableStringify(value) {
    if (Array.isArray(value)) {
      return `[${value.map(stableStringify).join(",")}]`;
    }
    if (value && typeof value === "object") {
      return `{${Object.keys(value)
        .sort()
        .map((key) => `${JSON.stringify(key)}:${stableStringify(value[key])}`)
        .join(",")}}`;
    }
    return JSON.stringify(value);
  }

  async function sha256(value) {
    const encoded = new TextEncoder().encode(value);
    const digest = await crypto.subtle.digest("SHA-256", encoded);
    return Array.from(new Uint8Array(digest))
      .map((byte) => byte.toString(16).padStart(2, "0"))
      .join("");
  }

  async function hashObject(value) {
    return sha256(stableStringify(value));
  }

  function maskPayload(payload) {
    return {
      sender_email: maskSender(payload.sender_email),
      display_name: maskText(payload.display_name).slice(0, 256),
      subject: maskText(payload.subject).slice(0, 512),
      body_text: maskText(payload.body_text),
      html: null,
      links: (payload.links || []).slice(0, 200).map((link) => ({
        href: String(link.href || "").slice(0, 2048),
        anchor_text: maskText(link.anchor_text).slice(0, 512)
      })),
      domain: String(payload.domain || "").slice(0, 255),
      sender_local_category: senderLocalCategory(payload.sender_email),
      heuristic_score: Number(payload.heuristic_score || 0),
      client_reasons: (payload.client_reasons || []).slice(0, 25),
      source: payload.source || "generic"
    };
  }

  window.PhishGuard.privacy = {
    maskText,
    maskSender,
    senderLocalCategory,
    maskPayload,
    hashObject
  };
})();
