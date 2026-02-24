import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link } from 'react-router-dom';
import { Search, Package } from 'lucide-react';
import { getItems } from '@/api/items';

export default function AdminItemsPage() {
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [brandSlug, setBrandSlug] = useState('');
  const [seasonCode, setSeasonCode] = useState('');
  const perPage = 25;

  const { data, isLoading } = useQuery({
    queryKey: ['admin-items', { page, search, brandSlug, seasonCode }],
    queryFn: () =>
      getItems({
        page,
        per_page: perPage,
        search: search || undefined,
        brand_slug: brandSlug || undefined,
        season_code: seasonCode || undefined,
      }),
  });

  const totalPages = data ? Math.ceil(data.total / perPage) : 0;

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-neutral-900">Items</h1>
          <p className="text-sm text-neutral-500 mt-1">
            {data ? `${data.total} items total` : 'Loading...'}
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-6">
        <div className="relative flex-1 max-w-xs">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-neutral-400" />
          <input
            type="text"
            placeholder="Search items..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-9 pr-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900"
          />
        </div>
        <input
          type="text"
          placeholder="Brand slug"
          value={brandSlug}
          onChange={(e) => { setBrandSlug(e.target.value); setPage(1); }}
          className="px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 w-36"
        />
        <input
          type="text"
          placeholder="Season (e.g. 26SS)"
          value={seasonCode}
          onChange={(e) => { setSeasonCode(e.target.value); setPage(1); }}
          className="px-3 py-2 text-sm border border-neutral-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-neutral-900 w-36"
        />
      </div>

      {/* Table */}
      <div className="bg-white rounded-lg border border-neutral-200 overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-100 bg-neutral-50">
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Image</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Name</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Type</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Price</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Season</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">Stock</th>
              <th className="text-left px-4 py-3 text-xs font-medium text-neutral-500 uppercase tracking-wider">SKU</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-neutral-100">
            {isLoading ? (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-neutral-400">Loading...</td></tr>
            ) : data?.data.length === 0 ? (
              <tr>
                <td colSpan={7} className="px-4 py-12 text-center">
                  <Package size={32} className="mx-auto text-neutral-300 mb-2" />
                  <p className="text-neutral-400">No items found</p>
                </td>
              </tr>
            ) : (
              data?.data.map((item) => (
                <tr key={item.id} className="hover:bg-neutral-50 transition-colors">
                  <td className="px-4 py-3">
                    {item.primary_image_url ? (
                      <img
                        src={item.primary_image_url}
                        alt={item.name_en}
                        className="w-10 h-10 object-cover rounded"
                      />
                    ) : (
                      <div className="w-10 h-10 bg-neutral-100 rounded flex items-center justify-center">
                        <Package size={14} className="text-neutral-300" />
                      </div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <Link
                      to={`/admin/items/${item.id}`}
                      className="font-medium text-neutral-900 hover:underline"
                    >
                      {item.name_en}
                    </Link>
                    {item.vendor && (
                      <p className="text-xs text-neutral-400 mt-0.5">{item.vendor}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-neutral-600">{item.item_type || '—'}</td>
                  <td className="px-4 py-3 text-neutral-600">
                    {item.price_usd ? `$${Number(item.price_usd).toFixed(2)}` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    {item.season_code ? (
                      <span className="inline-block px-2 py-0.5 text-xs font-medium bg-neutral-100 text-neutral-700 rounded">
                        {item.season_code}
                      </span>
                    ) : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block w-2 h-2 rounded-full ${item.in_stock ? 'bg-green-500' : 'bg-red-400'}`} />
                  </td>
                  <td className="px-4 py-3 text-xs text-neutral-400 font-mono">{item.sku || '—'}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4">
          <p className="text-xs text-neutral-400">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg disabled:opacity-30 hover:bg-neutral-50"
            >
              Previous
            </button>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-3 py-1.5 text-xs border border-neutral-200 rounded-lg disabled:opacity-30 hover:bg-neutral-50"
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
