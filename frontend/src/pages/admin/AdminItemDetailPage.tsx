import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { ArrowLeft, ExternalLink, Package } from 'lucide-react';
import { getItem } from '@/api/items';

export default function AdminItemDetailPage() {
  const { id } = useParams<{ id: string }>();
  const itemId = Number(id);

  const { data: item, isLoading, isError } = useQuery({
    queryKey: ['admin-item', itemId],
    queryFn: () => getItem(itemId),
    enabled: !isNaN(itemId),
  });

  if (isLoading) {
    return <div className="py-12 text-center text-neutral-400">Loading...</div>;
  }

  if (isError || !item) {
    return (
      <div className="py-12 text-center">
        <p className="text-neutral-400">Item not found</p>
        <Link to="/admin/items" className="text-sm text-neutral-500 hover:underline mt-2 inline-block">
          Back to items
        </Link>
      </div>
    );
  }

  return (
    <div>
      <Link
        to="/admin/items"
        className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 mb-6 transition-colors"
      >
        <ArrowLeft size={14} />
        Back to items
      </Link>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Images */}
        <div className="lg:col-span-1">
          {item.primary_image_url ? (
            <img
              src={item.primary_image_url}
              alt={item.name_en}
              className="w-full rounded-lg border border-neutral-200"
            />
          ) : (
            <div className="w-full aspect-square bg-neutral-100 rounded-lg flex items-center justify-center">
              <Package size={48} className="text-neutral-300" />
            </div>
          )}
        </div>

        {/* Details */}
        <div className="lg:col-span-2 space-y-6">
          <div>
            <h1 className="text-2xl font-bold text-neutral-900">{item.name_en}</h1>
            {item.vendor && (
              <p className="text-sm text-neutral-500 mt-1">{item.vendor}</p>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <DetailField label="Price (USD)" value={item.price_usd ? `$${Number(item.price_usd).toFixed(2)}` : null} />
            <DetailField label="Compare at" value={item.compare_at_price_usd ? `$${Number(item.compare_at_price_usd).toFixed(2)}` : null} />
            <DetailField label="Type" value={item.item_type} />
            <DetailField label="Product Type (raw)" value={item.product_type_raw} />
            <DetailField label="Season" value={item.season_code} />
            <DetailField label="SKU" value={item.sku} mono />
            <DetailField label="External ID" value={item.external_id} mono />
            <DetailField label="Handle" value={item.handle} mono />
            <DetailField label="In Stock" value={item.in_stock ? 'Yes' : 'No'} />
            <DetailField label="Material" value={item.material} />
          </div>

          {item.sizes && item.sizes.length > 0 && (
            <div>
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">Sizes</p>
              <div className="flex flex-wrap gap-2">
                {item.sizes.map((s) => (
                  <span key={s} className="px-2.5 py-1 text-xs bg-neutral-100 text-neutral-700 rounded">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          )}

          {item.tags && item.tags.length > 0 && (
            <div>
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">Tags</p>
              <div className="flex flex-wrap gap-1.5">
                {item.tags.map((t) => (
                  <span key={t} className="px-2 py-0.5 text-[10px] bg-neutral-50 text-neutral-500 border border-neutral-200 rounded">
                    {t}
                  </span>
                ))}
              </div>
            </div>
          )}

          {item.colors && item.colors.length > 0 && (
            <div>
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">Colors</p>
              <div className="flex flex-wrap gap-2">
                {item.colors.map((c) => (
                  <span key={c} className="px-2.5 py-1 text-xs bg-neutral-100 text-neutral-700 rounded capitalize">
                    {c}
                  </span>
                ))}
              </div>
            </div>
          )}

          {item.source_url && (
            <a
              href={item.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 text-sm text-neutral-500 hover:text-neutral-900 transition-colors"
            >
              <ExternalLink size={14} />
              View on store
            </a>
          )}

          {/* Body HTML */}
          {item.body_html_raw && (
            <div>
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">Product Description (raw HTML)</p>
              <div
                className="prose prose-sm max-w-none bg-neutral-50 p-4 rounded-lg border border-neutral-200"
                dangerouslySetInnerHTML={{ __html: item.body_html_raw }}
              />
            </div>
          )}

          {/* Raw Shopify data */}
          {item.shopify_data && (
            <div>
              <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">Raw Shopify Data</p>
              <pre className="text-xs bg-neutral-900 text-green-400 p-4 rounded-lg overflow-auto max-h-96">
                {JSON.stringify(item.shopify_data, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DetailField({ label, value, mono }: { label: string; value: string | null | undefined; mono?: boolean }) {
  return (
    <div>
      <p className="text-xs font-medium text-neutral-500 uppercase tracking-wider">{label}</p>
      <p className={`text-sm text-neutral-900 mt-0.5 ${mono ? 'font-mono text-xs' : ''}`}>
        {value || <span className="text-neutral-300">—</span>}
      </p>
    </div>
  );
}
