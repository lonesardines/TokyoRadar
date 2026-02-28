"""Scraper MCP Server — exposes scraping tools via Streamable HTTP."""

from __future__ import annotations

import re

from mcp.server.fastmcp import FastMCP

from scraper.mcp_helpers import (
    FETCH_PAGE_MAX_CHARS,
    _build_href_image_map,
    _clean_html,
    _extract_image_urls,
    _extract_jsonld_products,
    _extract_links,
    _fetch_with_fallback,
    _is_bot_challenge,
    _products_to_csv,
)
from scraper.sources.registry import (
    SCRAPER_REGISTRY,
    get_scraper,
    list_supported_brands,
)

from mcp.server.fastmcp.server import TransportSecuritySettings

mcp = FastMCP(
    "TokyoRadar Scraper",
    host="0.0.0.0",
    port=8001,
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=False,
    ),
)


@mcp.tool()
def scrape_shopify_store(domain: str) -> dict:
    """Scrape products from a Shopify store via products.json API.
    ONLY for scraper_type='shopify' stores. Returns compact CSV: name|sku|price|material|sizes|in_stock.
    Do NOT use for non-Shopify sites — use fetch_page instead."""
    from scraper.sources.shopify import ShopifyBrandScraper

    with ShopifyBrandScraper(domain=domain) as scraper:
        products = scraper.scrape_products()

    compact = [
        {
            "name": p.name,
            "sku": p.sku or "",
            "price_usd": str(p.price_usd) if p.price_usd else "",
            "material": p.material or "",
            "sizes": p.sizes,
            "in_stock": p.in_stock,
        }
        for p in products
    ]

    csv_data = _products_to_csv(
        compact, ["name", "sku", "price_usd", "material", "sizes", "in_stock"]
    )

    return {
        "domain": domain,
        "count": len(products),
        "products_csv": csv_data,
    }


@mcp.tool()
def fetch_page(url: str) -> dict:
    """Fetch a single URL and return cleaned text + product data + discovered links.
    For broad product scraping across multiple pages, prefer crawl_products instead.
    Returns max 15K chars of cleaned text, plus a [links] section with same-domain hrefs."""
    try:
        resp = _fetch_with_fallback(url)

        content_type = resp.headers.get("content-type", "")
        raw_body = resp.text

        if "html" in content_type:
            json_ld_blocks = re.findall(
                r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
                raw_body, re.DOTALL | re.IGNORECASE,
            )
            products_csv = _extract_jsonld_products(json_ld_blocks)
            cleaned = _clean_html(raw_body)

            # Extract navigation links for agent to discover sub-pages
            links = _extract_links(raw_body, url)
            # Filter to likely product/category links, limit to 30
            interesting_links = [
                lk for lk in links
                if any(kw in lk["href"].lower() for kw in (
                    "/product", "/item", "/collection", "/categor",
                    "/shop", "/brand", "/all", "/new", "/sale",
                ))
            ][:30]

            parts = []
            if products_csv:
                parts.append(f"[products found: CSV]\n{products_csv}")
            parts.append(f"[page text]\n{cleaned}")
            if interesting_links:
                link_lines = [f'{lk["text"]} → {lk["href"]}' for lk in interesting_links]
                parts.append("[links]\n" + "\n".join(link_lines))

            body = "\n\n".join(parts)
        else:
            body = raw_body

        body = body[:FETCH_PAGE_MAX_CHARS]

        return {
            "url": url,
            "status": resp.status_code,
            "body": body,
        }
    except Exception as exc:
        return {"url": url, "error": str(exc)}


@mcp.tool()
def scrape_sitemap(domain: str, brand_name: str) -> dict:
    """Scrape a website's XML sitemap to find product URLs for a brand.
    Use for bot-protected sites (Akamai, Cloudflare) where fetch_page fails.
    Sitemaps bypass bot detection. Returns product URLs matching the brand name."""
    try:
        from curl_cffi import requests as cffi_requests
    except ImportError:
        return {"error": "curl_cffi not installed"}

    brand_lower = brand_name.lower()
    product_urls: list[str] = []

    try:
        r = cffi_requests.get(
            f"https://{domain}/sitemap.xml",
            impersonate="chrome", timeout=15,
        )
        if r.status_code != 200:
            return {"error": f"Sitemap returned {r.status_code}"}
    except Exception as exc:
        return {"error": f"Failed to fetch sitemap: {exc}"}

    sub_sitemaps = re.findall(r"<loc>(.*?)</loc>", r.text)

    if "<sitemapindex" in r.text:
        for sm_url in sub_sitemaps:
            try:
                sr = cffi_requests.get(sm_url, impersonate="chrome", timeout=15)
                if sr.status_code != 200:
                    continue
                urls = re.findall(r"<loc>(.*?)</loc>", sr.text)
                matches = [u for u in urls if brand_lower in u.lower()]
                product_urls.extend(matches)
            except Exception:
                continue
    else:
        product_urls = [u for u in sub_sitemaps if brand_lower in u.lower()]

    products = []
    for url in product_urls:
        parts = url.rstrip("/").split("/")
        name = parts[-2] if len(parts) >= 2 else parts[-1]
        name = name.replace("-", " ").title()
        products.append({"name": name, "url": url})

    csv_data = _products_to_csv(products, ["name", "url"]) if products else ""

    return {
        "domain": domain,
        "brand": brand_name,
        "count": len(product_urls),
        "products_csv": csv_data,
    }


@mcp.tool()
def scrape_brand(brand_slug: str) -> dict:
    """High-level: scrape a brand using its registered scraper config.
    Looks up the brand in the scraper registry, runs the appropriate scraper,
    and returns product data as compact CSV."""
    config = SCRAPER_REGISTRY.get(brand_slug)
    if not config:
        return {"error": f"Brand '{brand_slug}' not in scraper registry"}

    try:
        scraper = get_scraper(brand_slug)
        with scraper:
            products = scraper.scrape_products()

        compact = [
            {
                "name": p.name,
                "sku": p.sku or "",
                "price_usd": str(p.price_usd) if p.price_usd else "",
                "material": p.material or "",
                "sizes": p.sizes,
                "in_stock": p.in_stock,
            }
            for p in products
        ]

        csv_data = _products_to_csv(
            compact, ["name", "sku", "price_usd", "material", "sizes", "in_stock"]
        )

        return {
            "brand_slug": brand_slug,
            "source": config.source,
            "count": len(products),
            "products_csv": csv_data,
        }
    except Exception as exc:
        return {"brand_slug": brand_slug, "error": str(exc)}


@mcp.tool()
def list_scraper_brands() -> dict:
    """List all brands supported by the scraper registry."""
    return {"brands": list_supported_brands()}


@mcp.tool()
def crawl_products(
    start_url: str,
    max_pages: int = 8,
) -> dict:
    """Crawl a brand store starting from a listing page, following pagination/category
    links to collect ALL products across multiple pages. Much more thorough than
    a single fetch_page call. Use for official stores or large retailer brand pages.

    Returns compact CSV: name|price|currency|image_url|product_url|in_stock.
    Automatically extracts products from JSON-LD, og:product, and link+price patterns."""
    from urllib.parse import urljoin, urlparse

    all_products: list[dict] = []
    visited: set[str] = set()
    queue: list[str] = [start_url]
    pages_fetched = 0
    errors: list[str] = []

    base_parsed = urlparse(start_url)
    base_domain = base_parsed.netloc
    # Track allowed domains (original + any redirect target)
    allowed_domains: set[str] = {base_domain, base_domain.removeprefix("www.")}

    # Patterns that indicate product listing / category / pagination pages
    listing_patterns = re.compile(
        r'(/collections/|/category/|/products/?$|/shop/|/items?/search'
        r'|/all/?$|[?&]page=\d|/page/\d|/c/|/brand/|/designers?/)',
        re.IGNORECASE,
    )
    # Patterns for individual product detail pages
    product_page_patterns = re.compile(
        r'(/products?/[^/?]+$|/items?/\d+\.html|/items?/[^/?]+$|/p/[^/?]+$|/detail/)',
        re.IGNORECASE,
    )
    # Price pattern in link text: ¥XX,XXX or $XX.XX
    price_in_text = re.compile(
        r'[¥￥]\s*([\d,]+)|[\$]\s*([\d,.]+)',
    )

    seen_names: set[str] = set()
    seen_urls: set[str] = set()  # deduplicate by URL path (ignoring query params)

    # Extract locale prefix from start_url (e.g. /en-us from SSENSE)
    _locale_match = re.match(r'^(/[a-z]{2}-[a-z]{2})/', urlparse(start_url).path)
    _locale_prefix = _locale_match.group(1) if _locale_match else ""

    def _fix_locale(product_url: str) -> str:
        """Inject locale prefix for same-domain URLs that are missing it."""
        if not _locale_prefix or not product_url:
            return product_url
        parsed = urlparse(product_url)
        # Only fix same-domain or relative URLs
        if parsed.netloc and parsed.netloc not in allowed_domains:
            return product_url
        if not parsed.path.startswith(_locale_prefix):
            product_url = product_url.replace(parsed.path, _locale_prefix + parsed.path, 1)
        return product_url

    while queue and pages_fetched < max_pages:
        url = queue.pop(0)
        if url in visited:
            continue
        visited.add(url)

        try:
            resp = _fetch_with_fallback(url)
        except Exception as exc:
            errors.append(f"{url}: {exc}")
            continue
        pages_fetched += 1

        # Track redirect domain
        final_url = str(resp.url) if hasattr(resp, "url") else url
        final_domain = urlparse(final_url).netloc
        if final_domain:
            allowed_domains.add(final_domain)
            # Re-resolve links against final URL
            url = final_url

        raw_html = resp.text
        content_type = resp.headers.get("content-type", "") if hasattr(resp.headers, "get") else ""

        if "html" not in content_type and "html" not in raw_html[:200].lower():
            continue

        # Pre-build href→image map for this page
        href_image_map = _build_href_image_map(raw_html, url)

        # 1) Extract JSON-LD products
        json_ld_blocks = re.findall(
            r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
            raw_html, re.DOTALL | re.IGNORECASE,
        )
        for block in json_ld_blocks:
            try:
                data = __import__("json").loads(block)
            except (ValueError, TypeError):
                continue

            items = []
            if isinstance(data, dict):
                if data.get("@type") == "Product":
                    items = [data]
                elif data.get("@type") == "ItemList":
                    items = [
                        el.get("item", el) for el in data.get("itemListElement", [])
                        if isinstance(el, dict)
                    ]
            elif isinstance(data, list):
                items = [d for d in data if isinstance(d, dict) and d.get("@type") == "Product"]

            for item in items:
                name = item.get("name", "").strip()
                if not name or name.lower() in seen_names:
                    continue
                seen_names.add(name.lower())

                offers = item.get("offers", {})
                if isinstance(offers, list):
                    offers = offers[0] if offers else {}
                price = str(offers.get("price", ""))
                currency = offers.get("priceCurrency", "")
                avail = offers.get("availability", "")
                in_stock = "InStock" in str(avail)
                prod_url = offers.get("url") or item.get("url", "")
                if prod_url and not prod_url.startswith("http"):
                    prod_url = urljoin(url, prod_url)
                prod_url = _fix_locale(prod_url)
                image = ""
                img_field = item.get("image")
                if isinstance(img_field, str):
                    image = img_field
                elif isinstance(img_field, list) and img_field:
                    image = img_field[0] if isinstance(img_field[0], str) else img_field[0].get("url", "")
                elif isinstance(img_field, dict):
                    image = img_field.get("url", "")

                all_products.append({
                    "name": name,
                    "price": price,
                    "currency": currency,
                    "image_url": image,
                    "product_url": prod_url,
                    "in_stock": str(in_stock),
                })

        # 2) Extract products from HTML links (name + price in link text)
        #    Common on Japanese e-commerce: <a href="/item/123.html">BRAND NAME ¥55,000</a>
        links = _extract_links(raw_html, url)
        for link in links:
            href = link["href"]
            text = link["text"]
            if not product_page_patterns.search(href):
                continue
            price_match = price_in_text.search(text)
            if not price_match:
                continue
            # Deduplicate by URL path (ignore ?cid= etc.)
            url_path = urlparse(href).path
            if url_path in seen_urls:
                continue
            seen_urls.add(url_path)
            # Extract name (everything before the price symbol)
            name_part = re.split(r'[¥￥$]', text)[0].strip()
            # Strip common status prefixes
            name_part = re.sub(
                r'^(SOLD\s*OUT|RESTOCK|NEW|PRE\s*ORDER|COMING\s*SOON)\s*',
                '', name_part, flags=re.IGNORECASE,
            ).strip()
            if not name_part or len(name_part) < 3 or name_part.lower() in seen_names:
                continue
            seen_names.add(name_part.lower())

            jpy_str = price_match.group(1)
            usd_str = price_match.group(2)
            price_val = ""
            currency = ""
            if jpy_str:
                price_val = jpy_str.replace(",", "")
                currency = "JPY"
            elif usd_str:
                price_val = usd_str.replace(",", "")
                currency = "USD"

            # Find product image: primary from pre-built map, fallback by href path
            img_url = href_image_map.get(href, "")
            if not img_url:
                # Fallback: search raw HTML by href path (handles relative vs absolute mismatch)
                href_path = urlparse(href).path
                if href_path:
                    fallback_pattern = re.compile(
                        re.escape(href_path) + r'["\'][^>]*>'
                        r'(?:(?!</a>).)*?'
                        r'<img[^>]+src=["\']([^"\']+)["\']',
                        re.DOTALL | re.IGNORECASE,
                    )
                    fb_match = fallback_pattern.search(raw_html)
                    if fb_match:
                        img_url = fb_match.group(1)
                        if img_url.startswith("//"):
                            img_url = "https:" + img_url
                        elif not img_url.startswith("http"):
                            img_url = urljoin(url, img_url)

            all_products.append({
                "name": name_part,
                "price": price_val,
                "currency": currency,
                "image_url": img_url,
                "product_url": _fix_locale(href),
                "in_stock": "True",
            })

        # 3) Discover more listing links to crawl
        for link in links:
            href = link["href"]
            if href in visited:
                continue
            link_parsed = urlparse(href)
            # Must be same domain (allow both www and non-www)
            if link_parsed.netloc and link_parsed.netloc not in allowed_domains:
                continue
            # Queue listing/category pages (not individual product pages)
            if listing_patterns.search(href):
                queue.append(href)

        # 3) Find pagination: ?page=N or /page/N patterns
        page_links = re.findall(
            r'href=["\']([^"\']*(?:[?&]page=\d+|/page/\d+)[^"\']*)["\']',
            raw_html, re.IGNORECASE,
        )
        for pl in page_links:
            resolved = urljoin(url, pl)
            if resolved not in visited:
                queue.append(resolved)

    # Build CSV
    fields = ["name", "price", "currency", "image_url", "product_url", "in_stock"]
    csv_data = _products_to_csv(all_products, fields) if all_products else ""

    return {
        "start_url": start_url,
        "pages_fetched": pages_fetched,
        "products_found": len(all_products),
        "products_csv": csv_data,
        "errors": errors if errors else None,
    }


@mcp.tool()
def detect_platform(domain: str) -> dict:
    """Detect what e-commerce platform a domain runs on.
    Checks Shopify products.json API first, then HTML for cdn.shopify.com markers.
    Returns {domain, platform: "shopify"|"generic"|"blocked", note?}.
    Use this to decide which scraper tool to call for an unknown domain."""
    import httpx as _httpx

    domain = domain.strip().rstrip("/")
    if domain.startswith(("http://", "https://")):
        domain = domain.split("//", 1)[1].split("/")[0]

    # 1) Try Shopify products.json endpoint
    try:
        with _httpx.Client(timeout=10.0, follow_redirects=True) as client:
            resp = client.get(f"https://{domain}/products.json?limit=1")
            if resp.status_code == 200:
                data = resp.json()
                if "products" in data:
                    return {
                        "domain": domain,
                        "platform": "shopify",
                        "note": "Confirmed via /products.json API",
                    }
    except Exception:
        pass

    # 2) Fetch homepage and check for Shopify markers / bot protection
    try:
        resp = _fetch_with_fallback(f"https://{domain}/")
        html = resp.text[:5000]

        if _is_bot_challenge(html):
            return {
                "domain": domain,
                "platform": "blocked",
                "note": "Bot protection detected (Akamai/Cloudflare). Use scrape_sitemap instead.",
            }

        shopify_markers = ["cdn.shopify.com", "Shopify.theme", "shopify-section"]
        if any(marker in html for marker in shopify_markers):
            return {
                "domain": domain,
                "platform": "shopify",
                "note": "Detected Shopify via HTML markers (cdn.shopify.com)",
            }

        return {
            "domain": domain,
            "platform": "generic",
            "note": "Not Shopify. Use crawl_products(start_url) to scrape product listings. Do NOT use fetch_page for listing pages.",
        }
    except Exception as exc:
        return {
            "domain": domain,
            "platform": "blocked",
            "note": f"Could not fetch homepage: {exc}. Try scrape_sitemap.",
        }


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
