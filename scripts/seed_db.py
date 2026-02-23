import json
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tokyoradar_shared.database import Base
from tokyoradar_shared.models import Brand, Category, ProxyService, Retailer
from tokyoradar_shared.config import settings


def load_json(filename):
    filepath = os.path.join(os.path.dirname(__file__), '..', 'data', filename)
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def seed_categories(session: Session):
    data = load_json('categories_seed.json')
    count = 0
    for item in data:
        existing = session.query(Category).filter_by(slug=item['slug']).first()
        if not existing:
            session.add(Category(**item))
            count += 1
    session.commit()
    print(f"  Categories: {count} inserted, {len(data) - count} skipped (already exist)")


def seed_brands(session: Session):
    data = load_json('brands_seed.json')
    count = 0
    for item in data:
        existing = session.query(Brand).filter_by(slug=item['slug']).first()
        if not existing:
            brand = Brand(
                slug=item['slug'],
                name_en=item['name'],
                name_ja=item.get('name_ja'),
                designer=item.get('founder'),
                founded_year=item.get('founded_year'),
                headquarters=item.get('headquarters'),
                website_jp=item.get('website'),
                price_range=item.get('price_range'),
                description_en=item.get('description'),
                shipping_tier=item.get('shipping_tier'),
                buy_guide=item.get('buy_guide'),
                style_tags=[item['category_slug']] if item.get('category_slug') else None,
            )
            session.add(brand)
            count += 1
    session.commit()
    print(f"  Brands: {count} inserted, {len(data) - count} skipped (already exist)")


def seed_retailers(session: Session):
    data = load_json('retailers_seed.json')
    count = 0
    for item in data:
        existing = session.query(Retailer).filter_by(slug=item['slug']).first()
        if not existing:
            retailer = Retailer(
                slug=item['slug'],
                name=item['name'],
                website=item.get('website'),
                country=item.get('country'),
                ships_to_us=item.get('ships_to_us', False),
                shipping_tier=item.get('shipping_tier'),
                supported_proxies=item.get('supported_proxies'),
                payment_methods=item.get('payment_methods'),
                description_en=item.get('description_en'),
            )
            session.add(retailer)
            count += 1
    session.commit()
    print(f"  Retailers: {count} inserted, {len(data) - count} skipped (already exist)")


def seed_proxy_services(session: Session):
    data = load_json('proxy_services_seed.json')
    count = 0
    for item in data:
        existing = session.query(ProxyService).filter_by(slug=item['slug']).first()
        if not existing:
            # Parse delivery days range to get average
            delivery_str = item.get('estimated_delivery_days', '7-14')
            parts = delivery_str.split('-')
            avg_days = (int(parts[0]) + int(parts[-1])) // 2

            proxy = ProxyService(
                slug=item['slug'],
                name=item['name'],
                website=item.get('website'),
                service_type=item.get('service_type'),
                fee_structure=item.get('fee_structure'),
                supported_retailers=item.get('supported_sites'),
                shipping_methods=item.get('shipping_methods'),
                avg_delivery_days_us=avg_days,
                pros=item.get('pros'),
                cons=item.get('cons'),
                description_en=item.get('description_en'),
            )
            session.add(proxy)
            count += 1
    session.commit()
    print(f"  Proxy Services: {count} inserted, {len(data) - count} skipped (already exist)")


def main():
    print("TokyoRadar Database Seeder")
    print("=" * 40)

    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as session:
        print("\nSeeding database...")
        seed_categories(session)
        seed_brands(session)
        seed_retailers(session)
        seed_proxy_services(session)

    print("\n" + "=" * 40)
    print("Seeding complete!")


if __name__ == '__main__':
    main()
