import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from '@/components/layout/Layout';
import AdminLayout from '@/components/layout/AdminLayout';
import HomePage from '@/pages/HomePage';
import BrandsPage from '@/pages/BrandsPage';
import BrandDetailPage from '@/pages/BrandDetailPage';
import RetailersPage from '@/pages/RetailersPage';
import BuyGuidePage from '@/pages/BuyGuidePage';
import NotFoundPage from '@/pages/NotFoundPage';
import AdminItemsPage from '@/pages/admin/AdminItemsPage';
import AdminScrapeJobsPage from '@/pages/admin/AdminScrapeJobsPage';
import AdminFlaggedPage from '@/pages/admin/AdminFlaggedPage';
import AdminItemDetailPage from '@/pages/admin/AdminItemDetailPage';
import AdminAgentPage from '@/pages/admin/AdminAgentPage';
import AdminAgentSessionPage from '@/pages/admin/AdminAgentSessionPage';
import AgentSnapshotPage from '@/pages/admin/AgentSnapshotPage';
import AgentComparePage from '@/pages/admin/AgentComparePage';

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<HomePage />} />
        <Route path="/brands" element={<BrandsPage />} />
        <Route path="/brands/:slug" element={<BrandDetailPage />} />
        <Route path="/retailers" element={<RetailersPage />} />
        <Route path="/buy-guide" element={<BuyGuidePage />} />
      </Route>
      <Route path="/admin" element={<AdminLayout />}>
        <Route index element={<Navigate to="/admin/items" replace />} />
        <Route path="items" element={<AdminItemsPage />} />
        <Route path="items/:id" element={<AdminItemDetailPage />} />
        <Route path="scrape-jobs" element={<AdminScrapeJobsPage />} />
        <Route path="agent" element={<AdminAgentPage />} />
        <Route path="agent/compare" element={<AgentComparePage />} />
        <Route path="agent/:id" element={<AdminAgentSessionPage />} />
        <Route path="agent/:id/products" element={<AgentSnapshotPage />} />
        <Route path="flagged" element={<AdminFlaggedPage />} />
      </Route>
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
