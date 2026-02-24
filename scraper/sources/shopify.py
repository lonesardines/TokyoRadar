import logging
import re
from decimal import Decimal

from scraper.sources.base import BrandScraper, RawProduct

logger = logging.getLogger(__name__)

# Regex for season codes like 26SS, 25AW, 25FW
SEASON_CODE_RE = re.compile(r"\b(\d{2}(?:SS|AW|FW|PF))\b", re.IGNORECASE)

# Color keywords to extract from tags/title
COLOR_KEYWORDS = {
    "black", "white", "navy", "blue", "red", "green", "grey", "gray",
    "beige", "brown", "olive", "khaki", "cream", "charcoal", "orange",
    "yellow", "pink", "purple", "burgundy", "tan", "indigo", "camel",
}


class ShopifyBrandScraper(BrandScraper):
    """Scraper for Shopify-based brand stores using the public products.json API."""

    def scrape_products(self) -> list[RawProduct]:
        products: list[RawProduct] = []
        page = 1

        while True:
            resp = self.client.get(
                "/products.json",
                params={"limit": 250, "page": page},
            )
            resp.raise_for_status()
            data = resp.json()

            batch = data.get("products", [])
            if not batch:
                break

            for p in batch:
                raw = self._parse_product(p)
                if raw:
                    products.append(raw)

            if len(batch) < 250:
                break
            page += 1

        logger.info("Scraped %d products from %s", len(products), self.domain)
        return products

    def _parse_product(self, p: dict) -> RawProduct | None:
        product_id = str(p.get("id", ""))
        title = p.get("title", "").strip()
        if not product_id or not title:
            return None

        variants = p.get("variants", [])
        images = p.get("images", [])
        tags = [t.strip() for t in p.get("tags", []) if t.strip()]

        # Price from first variant
        price_usd = None
        compare_at = None
        sku = None
        if variants:
            v0 = variants[0]
            if v0.get("price"):
                price_usd = Decimal(str(v0["price"]))
            if v0.get("compare_at_price"):
                compare_at = Decimal(str(v0["compare_at_price"]))
            sku = v0.get("sku")

        # Sizes from variant options
        sizes = self._extract_sizes(variants)

        # Stock: true if any variant is available
        in_stock = any(v.get("available", False) for v in variants)

        # Season code from tags or title
        season_code = self._extract_season_code(tags, title)

        # Colors from tags
        colors = self._extract_colors(tags, title)

        # Material from body_html
        body_html = p.get("body_html", "")
        material = self._extract_material(body_html)

        # Images
        image_urls = [img.get("src", "") for img in images if img.get("src")]
        primary_image = image_urls[0] if image_urls else None

        return RawProduct(
            external_id=product_id,
            name=title,
            handle=p.get("handle"),
            vendor=p.get("vendor"),
            product_type=p.get("product_type"),
            tags=tags,
            colors=colors,
            sizes=sizes,
            price_usd=price_usd,
            compare_at_price_usd=compare_at,
            material=material,
            body_html=body_html,
            season_code=season_code,
            sku=sku,
            in_stock=in_stock,
            primary_image_url=primary_image,
            image_urls=image_urls,
            source_url=f"https://{self.domain}/products/{p.get('handle', '')}",
            raw_data=p,
        )

    def _extract_sizes(self, variants: list[dict]) -> list[str]:
        sizes: list[str] = []
        seen: set[str] = set()
        for v in variants:
            # Shopify stores size in option1, option2, or option3
            for opt_key in ("option1", "option2", "option3"):
                val = v.get(opt_key, "")
                if not val:
                    continue
                val_upper = val.upper()
                if val_upper in ("XS", "S", "M", "L", "XL", "XXL", "XXXL",
                                  "F", "FREE", "ONE SIZE") or val_upper.isdigit():
                    if val not in seen:
                        sizes.append(val)
                        seen.add(val)
        return sizes

    def _extract_season_code(self, tags: list[str], title: str) -> str | None:
        # Check tags first
        for tag in tags:
            m = SEASON_CODE_RE.search(tag)
            if m:
                return m.group(1).upper()
        # Then title
        m = SEASON_CODE_RE.search(title)
        if m:
            return m.group(1).upper()
        return None

    def _extract_colors(self, tags: list[str], title: str) -> list[str]:
        colors: list[str] = []
        text = " ".join(tags).lower() + " " + title.lower()
        for kw in COLOR_KEYWORDS:
            if kw in text and kw not in colors:
                colors.append(kw)
        return colors

    def _extract_material(self, body_html: str) -> str | None:
        if not body_html:
            return None
        # Look for common material keywords in the body
        material_keywords = [
            "cotton", "nylon", "polyester", "wool", "gore-tex", "goretex",
            "cordura", "pertex", "coolmax", "silk", "linen", "cashmere",
            "leather", "down", "fleece", "mesh",
        ]
        html_lower = body_html.lower()
        found = [kw for kw in material_keywords if kw in html_lower]
        if found:
            return ", ".join(found)
        return None
