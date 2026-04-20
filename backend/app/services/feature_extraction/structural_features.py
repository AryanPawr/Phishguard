from __future__ import annotations

from bs4 import BeautifulSoup


def extract_structural_features(html: str | None, body_text: str | None) -> dict[str, float]:
    html_value = html or ""
    text_value = body_text or ""
    if html_value:
        soup = BeautifulSoup(html_value, "html.parser")
        visible_text = soup.get_text(" ", strip=True)
        form_count = len(soup.find_all("form"))
        hidden_count = len(
            soup.select(
                "[hidden], [aria-hidden='true'], input[type='hidden'], "
                "[style*='display:none'], [style*='display: none'], [style*='visibility:hidden']"
            )
        )
    else:
        visible_text = text_value
        form_count = 0
        hidden_count = 0

    html_to_text_ratio = len(html_value) / max(len(visible_text or text_value), 1)
    return {
        "html_to_text_ratio": round(html_to_text_ratio, 4),
        "form_tag_presence": 1.0 if form_count else 0.0,
        "hidden_element_count": float(hidden_count),
    }
