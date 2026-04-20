(function initGmailExtractor() {
  window.PhishGuard = window.PhishGuard || {};
  window.PhishGuard.extractors = window.PhishGuard.extractors || [];

  function canHandle() {
    return location.hostname === "mail.google.com";
  }

  function isVisible(element) {
    if (!element) {
      return false;
    }
    const style = window.getComputedStyle(element);
    if (style.display === "none" || style.visibility === "hidden" || Number(style.opacity) === 0) {
      return false;
    }
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0 && rect.bottom > 0 && rect.top < window.innerHeight;
  }

  function textOf(element) {
    return (element?.innerText || element?.textContent || "").trim();
  }

  function findEmail(value) {
    return String(value || "").match(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/i)?.[0] || "";
  }

  function extractLinks(root) {
    return Array.from(root.querySelectorAll("a[href]"))
      .filter((link) => !String(link.href).startsWith("mailto:"))
      .map((link) => ({
        href: link.href,
        anchor_text: textOf(link) || link.href
      }));
  }

  function visibleMessageContainers() {
    return Array.from(document.querySelectorAll("[role='main'] div.adn.ads, [role='main'] div.adn"))
      .filter((container) => isVisible(container))
      .map((container) => {
        const body = Array.from(container.querySelectorAll(".a3s, .ii.gt, .ii"))
          .filter(isVisible)
          .sort((left, right) => textOf(right).length - textOf(left).length)[0];
        const sender = container.querySelector(".gD[email], [email][name], .go span[email]");
        const rect = container.getBoundingClientRect();
        return {
          container,
          body,
          sender,
          score: textOf(body).length + (sender ? 200 : 0) + Math.max(0, window.innerHeight - Math.abs(rect.top))
        };
      })
      .filter((candidate) => candidate.body && textOf(candidate.body).length > 0)
      .sort((left, right) => right.score - left.score);
  }

  function senderEmailFrom(container, sender) {
    return (
      sender?.getAttribute("email") ||
      sender?.getAttribute("data-hovercard-id") ||
      findEmail(sender?.getAttribute("title")) ||
      findEmail(sender?.getAttribute("aria-label")) ||
      findEmail(container?.textContent)
    );
  }

  function extract() {
    const active = visibleMessageContainers()[0];
    if (!active) {
      return null;
    }
    const messageRoot = active.body;
    const sender = active.sender;
    const subject = document.querySelector("h2.hP, h2[data-thread-perm-id]");
    const senderEmail = senderEmailFrom(active.container, sender);
    return {
      source: "gmail",
      sender_email: senderEmail,
      display_name: sender?.getAttribute("name") || textOf(sender),
      subject: textOf(subject) || document.title.replace(" - Gmail", ""),
      body_text: textOf(messageRoot),
      html: null,
      links: extractLinks(messageRoot),
      domain: senderEmail.includes("@") ? senderEmail.split("@").pop().toLowerCase() : "",
      message_id: [
        location.hash,
        senderEmail,
        textOf(subject),
        textOf(messageRoot).slice(0, 120)
      ].join("|")
    };
  }

  window.PhishGuard.extractors.push({ name: "gmail", canHandle, extract });
})();
