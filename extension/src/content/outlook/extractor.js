(function initOutlookExtractor() {
  window.PhishGuard = window.PhishGuard || {};
  window.PhishGuard.extractors = window.PhishGuard.extractors || [];

  function canHandle() {
    return /outlook\.(live|office|office365)\.com$/.test(location.hostname);
  }

  function extractLinks(root) {
    return Array.from(root.querySelectorAll("a[href]")).map((link) => ({
      href: link.href,
      anchor_text: link.innerText || link.textContent || link.href
    }));
  }

  function findSender() {
    const candidates = Array.from(document.querySelectorAll("[title*='@'], [aria-label*='@'], a[href^='mailto:']"));
    const value = candidates
      .map((node) => node.getAttribute("title") || node.getAttribute("aria-label") || node.getAttribute("href") || "")
      .find((text) => text.includes("@"));
    return String(value || "").replace(/^mailto:/, "").match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || "";
  }

  function extract() {
    const messageRoot = document.querySelector("[role='main'] [aria-label='Message body'], [role='main'] div[dir='ltr']");
    if (!messageRoot) {
      return null;
    }
    const subject =
      document.querySelector("[aria-label='Message subject'], [role='heading'][aria-level='2']")?.textContent ||
      document.title;
    const senderEmail = findSender();
    return {
      source: "outlook",
      sender_email: senderEmail,
      display_name: document.querySelector("[data-testid='RecipientWell']")?.textContent || "",
      subject,
      body_text: messageRoot.innerText || "",
      html: null,
      links: extractLinks(messageRoot),
      domain: senderEmail.includes("@") ? senderEmail.split("@").pop() : ""
    };
  }

  window.PhishGuard.extractors.push({ name: "outlook", canHandle, extract });
})();

