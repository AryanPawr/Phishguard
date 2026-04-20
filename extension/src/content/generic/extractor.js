(function initGenericExtractor() {
  window.PhishGuard = window.PhishGuard || {};
  window.PhishGuard.extractors = window.PhishGuard.extractors || [];

  function canHandle() {
    if (location.hostname === "mail.google.com" || location.hostname.includes("outlook.")) {
      return false;
    }
    const text = document.body?.innerText?.slice(0, 4000) || "";
    return /(^|\n)\s*(from|sender|subject|to):/i.test(text) || document.querySelector("a[href^='mailto:']");
  }

  function extractSender(text) {
    const mailto = document.querySelector("a[href^='mailto:']")?.getAttribute("href") || "";
    const found = mailto.match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i) || text.match(/from:\s*.*?([A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,})/i);
    return found?.[1] || found?.[0] || "";
  }

  function extractLinks(root) {
    return Array.from(root.querySelectorAll("a[href]")).map((link) => ({
      href: link.href,
      anchor_text: link.innerText || link.textContent || link.href
    }));
  }

  function extract() {
    const root = document.querySelector("article, [role='main'], main") || document.body;
    if (!root) {
      return null;
    }
    const text = root.innerText || "";
    const senderEmail = extractSender(text);
    const subjectLine = text.match(/subject:\s*(.+)/i)?.[1] || document.querySelector("h1")?.textContent || document.title;
    return {
      source: "generic",
      sender_email: senderEmail,
      display_name: text.match(/from:\s*(.+)/i)?.[1] || "",
      subject: subjectLine,
      body_text: text,
      html: null,
      links: extractLinks(root),
      domain: senderEmail.includes("@") ? senderEmail.split("@").pop() : location.hostname
    };
  }

  window.PhishGuard.extractors.push({ name: "generic", canHandle, extract });
})();

