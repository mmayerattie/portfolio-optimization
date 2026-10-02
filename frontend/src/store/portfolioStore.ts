import { create } from 'zustand';
import axios from 'axios';
import type {
  AppTab,
  PortfolioAnalysis,
  PortfolioInput,
  Position,
  UserPreferences,
} from '../types/portfolio';

const STORAGE_KEY = 'portfolio-optimizer-state-v4';

const DEFAULT_POSITIONS: Position[] = [
  { ticker: 'BRK.B', shares: 2.97564, cost_basis: 480.43 },
  { ticker: 'SMH', shares: 1.1845, cost_basis: 337.18 },
  { ticker: 'XLU', shares: 9.9104, cost_basis: 44.90 },
  { ticker: 'DLR', shares: 2.11446, cost_basis: 162.29 },
  { ticker: 'COIN', shares: 1.65804, cost_basis: 220.68 },
  { ticker: 'SKM', shares: 8.45771, cost_basis: 30.15 },
];

const DEFAULT_PREFERENCES: UserPreferences = {
  investment_horizon_years: 5,
  max_drawdown_tolerance: 0.20,
  risk_profile: 'moderate',
  rebalance_frequency: 'quarterly',
  include_tax_optimization: false,
  benchmark: 'SPY',
};

interface SavedState {
  positions: Position[];
  preferences: UserPreferences;
}

function loadSaved(): SavedState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as SavedState;
      if (Array.isArray(parsed.positions) && parsed.positions.length > 0) {
        return parsed;
      }
    }
  } catch {
    // Corrupted storage — fall through to defaults
  }
  return { positions: DEFAULT_POSITIONS, preferences: DEFAULT_PREFERENCES };
}

function persist(positions: Position[], preferences: UserPreferences): void {
  try {
    const data: SavedState = { positions, preferences };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  } catch {
    // Storage full or unavailable — silently ignore
  }
}

interface PortfolioState {
  // Input state
  positions: Position[];
  preferences: UserPreferences;

  // Analysis state
  analysis: PortfolioAnalysis | null;
  isLoading: boolean;
  error: string | null;

  // UI state
  activeTab: AppTab;

  // Actions
  setPositions: (positions: Position[]) => void;
  addPosition: () => void;
  removePosition: (index: number) => void;
  updatePosition: (index: number, field: keyof Position, value: string | number | undefined) => void;
  setPreferences: (prefs: Partial<UserPreferences>) => void;
  setActiveTab: (tab: AppTab) => void;
  analyzePortfolio: () => Promise<void>;
  clearAnalysis: () => void;
}

const saved = loadSaved();

export const usePortfolioStore = create<PortfolioState>((set, get) => ({
  positions: saved.positions,
  preferences: saved.preferences,
  analysis: null,
  isLoading: false,
  error: null,
  activeTab: 'input',

  setPositions: (positions) => {
    set({ positions });
    persist(positions, get().preferences);
  },

  addPosition: () =>
    set((state) => {
      const positions = [...state.positions, { ticker: '', shares: 0 }];
      persist(positions, state.preferences);
      return { positions };
    }),

  removePosition: (index) =>
    set((state) => {
      const positions = state.positions.filter((_, i) => i !== index);
      persist(positions, state.preferences);
      return { positions };
    }),

  updatePosition: (index, field, value) =>
    set((state) => {
      const positions = [...state.positions];
      positions[index] = { ...positions[index], [field]: value };
      persist(positions, state.preferences);
      return { positions };
    }),

  setPreferences: (prefs) =>
    set((state) => {
      const preferences = { ...state.preferences, ...prefs };
      persist(state.positions, preferences);
      return { preferences };
    }),

  setActiveTab: (tab) => set({ activeTab: tab }),

  analyzePortfolio: async () => {
    const { positions, preferences } = get();

    const validPositions = positions.filter(
      (p) => p.ticker.trim() !== '' && p.shares > 0
    );

    if (validPositions.length < 1) {
      set({ error: 'Add at least 1 position with a valid ticker and shares.' });
      return;
    }

    const input: PortfolioInput = {
      positions: validPositions.map((p) => ({
        ticker: p.ticker.trim().toUpperCase(),
        shares: p.shares,
        cost_basis: p.cost_basis,
      })),
      preferences,
    };

    set({ isLoading: true, error: null });

    try {
      const response = await axios.post<PortfolioAnalysis>(
        '/api/portfolio/analyze',
        input,
      );
      set({
        analysis: response.data,
        isLoading: false,
        activeTab: 'diagnostic',
      });
    } catch (err) {
      let message = 'Analysis failed. Please try again.';
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        message = err.response.data.detail;
      }
      set({ error: message, isLoading: false });
    }
  },

  clearAnalysis: () => set({ analysis: null, error: null }),
}));
