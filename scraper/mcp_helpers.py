"""Shared helpers for the scraper MCP server — HTML cleaning, fetching, product parsing."""

from __future__ import annotations

import json as _json
import re

import httpx

FETCH_PAGE_MAX_CHARS = 15_000


def _extract_links(html: str, base_url: str) -> list[dict]:
    """Extract <a href> links from HTML, resolved against base_url.
    Returns [{text, href}] — deduped, skipping anchors/js/mailto."""
    from urllib.parse import urljoin, urlparse

    base_parsed = urlparse(base_url)
    raw = re.findall(r'<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)

    seen: set[str] = set()
    links: list[dict] = []
    for href, text in raw:
        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue
        resolved = urljoin(base_url, href)
        parsed = urlparse(resolved)
        # Only same-domain links
        if parsed.netloc and parsed.netloc != base_parsed.netloc:
            continue
        if resolved in seen:
            continue
        seen.add(resolved)
        # Clean link text: replace tags with spaces (preserves word boundaries),
        # then decode HTML entities
        clean_text = re.sub(r"<[^>]+>", " ", text).strip()
        clean_text = clean_text.replace("&yen;", "¥").replace("&amp;", "&")
        clean_text = clean_text.replace("&lt;", "<").replace("&gt;", ">")
        clean_text = clean_text.replace("&nbsp;", " ").replace("&#39;", "'")
        clean_text = re.sub(r"\s+", " ", clean_text)[:120]
        if clean_text:
            links.append({"text": clean_text, "href": resolved})
    return links


def _extract_image_urls(html: str, limit: int = 30) -> list[str]:
    """Extract product image URLs from <img> tags before HTML is stripped."""
    # Match src attributes on img tags
    imgs = re.findall(
        r'<img[^>]+src=["\']([^"\']+)["\']',
        html, re.IGNORECASE,
    )
    seen: set[str] = set()
    result: list[str] = []
    for url in imgs:
        # Skip tiny icons, tracking pixels, SVGs, base64
        if any(skip in url.lower() for skip in (
            "data:image", ".svg", "1x1", "pixel", "spacer", "blank",
            "icon", "logo", "badge", "flag", "arrow", "spinner",
        )):
            continue
        # Normalize protocol-relative URLs
        if url.startswith("//"):
            url = "https:" + url
        if url not in seen:
            seen.add(url)
            result.append(url)
        if len(result) >= limit:
            break
    return result


def _clean_html(html: str) -> str:
    """Strip scripts, styles, tags, and collapse whitespace from HTML.
    Preserves product image URLs in a [images] section at the end."""
    # Extract images before stripping tags
    images = _extract_image_urls(html)

    html = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<noscript[^>]*>.*?</noscript>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<!--.*?-->", "", html, flags=re.DOTALL)
    html = re.sub(r"<svg[^>]*>.*?</svg>", "", html, flags=re.DOTALL | re.IGNORECASE)
    html = re.sub(r"<[^>]+>", " ", html)
    html = html.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    html = html.replace("&nbsp;", " ").replace("&#39;", "'").replace("&quot;", '"')
    html = re.sub(r"\s+", " ", html).strip()

    if images:
        html += "\n\n[images]\n" + "\n".join(images)

    return html


def _fetch_with_fallback(url: str):
    """Fetch a URL with httpx, fall back to curl_cffi for bot-protected sites."""
    _headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                      "AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/131.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/json",
        "Accept-Language": "en-US,en;q=0.9",
    }
    try:
        with httpx.Client(
            timeout=15.0, follow_redirects=True, headers=_headers,
        ) as client:
            resp = client.get(url)
            resp.raise_for_status()
            if _is_bot_challenge(resp.text):
                raise httpx.HTTPError("Bot challenge detected, falling back")
            return resp
    except (httpx.HTTPError, httpx.TimeoutException):
        pass

    try:
        from curl_cffi import requests as cffi_requests
        resp = cffi_requests.get(url, impersonate="chrome", timeout=15)
        if resp.status_code >= 400:
            resp.raise_for_status()
        if _is_bot_challenge(resp.text):
            raise Exception(f"Bot challenge not bypassable for {url}")
        return resp
    except ImportError:
        raise httpx.HTTPError(
            f"httpx blocked by bot protection and curl_cffi not installed for {url}"
        )


def _is_bot_challenge(html: str) -> bool:
    """Detect common bot challenge pages (Akamai, Cloudflare, etc.)."""
    markers = [
        "sec-if-cpt-container",
        "cf-browser-verification",
        "challenge-platform",
        "Powered and protected by",
    ]
    lower = html[:3000].lower()
    return any(m.lower() in lower for m in markers)


def _extract_jsonld_products(json_ld_blocks: list[str]) -> str | None:
    """Parse JSON-LD blocks and extract Product entries as compact CSV."""
    products = []
    for block in json_ld_blocks:
        try:
            data = _json.loads(block)
        except (ValueError, TypeError):
            continue

        if not isinstance(data, dict):
            continue
        if data.get("@type") != "Product":
            continue

        name = data.get("name", "")
        offers = data.get("offers", {})
        if isinstance(offers, list):
            offers = offers[0] if offers else {}

        price = offers.get("price", "")
        currency = offers.get("priceCurrency", "USD")
        avail = offers.get("availability", "")
        in_stock = "InStock" in str(avail)
        url = offers.get("url") or data.get("url", "")
        product_id = data.get("productID") or data.get("sku", "")

        products.append({
            "name": name,
            "id": str(product_id),
            "price": f"{price} {currency}" if price else "",
            "in_stock": str(in_stock),
            "url": url,
        })

    if not products:
        return None

    return _products_to_csv(products, ["name", "id", "price", "in_stock", "url"])


def _build_href_image_map(html: str, base_url: str) -> dict[str, str]:
    """Scan all <a> tags containing <img> tags and build {resolved_href: image_url}.

    Handles the common Japanese e-commerce pattern where the image and text
    are in sibling <a> tags sharing the same href:
        <a href="/item/123"><img src="product.jpg"></a>
        <a href="/item/123">Product Name ¥55,000</a>
    """
    from urllib.parse import urljoin

    # Match <a href="...">...<img ...src="...">...</a> (image inside link)
    pattern = re.compile(
        r'<a[^>]+href=["\']([^"\'#]+)["\'][^>]*>'
        r'(?:(?!</a>).)*?'
        r'<img[^>]+src=["\']([^"\']+)["\']'
        r'(?:(?!</a>).)*?'
        r'</a>',
        re.DOTALL | re.IGNORECASE,
    )

    skip_keywords = (
        "data:image", ".svg", "1x1", "pixel", "spacer", "blank",
        "icon", "logo", "badge", "flag", "arrow", "spinner",
    )

    href_map: dict[str, str] = {}
    for href, img_src in pattern.findall(html):
        if href.startswith(("javascript:", "mailto:", "tel:")):
            continue
        img_lower = img_src.lower()
        if any(kw in img_lower for kw in skip_keywords):
            continue

        resolved_href = urljoin(base_url, href)
        if resolved_href in href_map:
            continue  # keep first image per href

        if img_src.startswith("//"):
            img_src = "https:" + img_src
        elif not img_src.startswith("http"):
            img_src = urljoin(base_url, img_src)

        href_map[resolved_href] = img_src

    return href_map


def _products_to_csv(products: list[dict], fields: list[str]) -> str:
    """Serialize products as compact CSV text (40-50% fewer tokens than JSON)."""
    lines = ["|".join(fields)]
    for p in products:
        row = []
        for f in fields:
            val = p.get(f)
            if val is None:
                row.append("")
            elif isinstance(val, list):
                row.append(",".join(str(v) for v in val))
            else:
                row.append(str(val))
        lines.append("|".join(row))
    return "\n".join(lines)
