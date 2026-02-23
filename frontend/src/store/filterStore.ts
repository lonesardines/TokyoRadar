import { create } from 'zustand';

interface FilterState {
  search: string;
  style_tag: string;
  price_range: string;
  shipping_tier: string;
  page: number;
  per_page: number;
  setSearch: (search: string) => void;
  setStyleTag: (tag: string) => void;
  setPriceRange: (range: string) => void;
  setShippingTier: (tier: string) => void;
  setPage: (page: number) => void;
  reset: () => void;
}

const initialState = {
  search: '',
  style_tag: '',
  price_range: '',
  shipping_tier: '',
  page: 1,
  per_page: 24,
};

export const useFilterStore = create<FilterState>((set) => ({
  ...initialState,
  setSearch: (search) => set({ search, page: 1 }),
  setStyleTag: (style_tag) => set({ style_tag, page: 1 }),
  setPriceRange: (price_range) => set({ price_range, page: 1 }),
  setShippingTier: (shipping_tier) => set({ shipping_tier, page: 1 }),
  setPage: (page) => set({ page }),
  reset: () => set(initialState),
}));
