// ==========================================
// HisseRadar TypeScript Tip Tanımlamaları
// ==========================================

// Hisse Bilgileri
export interface Stock {
  symbol: string;
  name: string;
  sector?: string;
  current_price?: number;
  change?: number;
  change_percent?: number;
  volume?: number;
  market_cap?: number;
}

export interface StockListResponse {
  stocks: Stock[];
  total: number;
  updated_at: string;
}

// Fiyat Verileri
export interface OHLCV {
  timestamp: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandleData {
  time: number;
  open: number;
  high: number;
  low: number;
  close: number;
}

export interface VolumeData {
  time: number;
  value: number;
  color: string;
}

export interface PriceResponse {
  symbol: string;
  period: string;
  interval: string;
  data: OHLCV[];
  candles?: CandleData[];
  volumes?: VolumeData[];
}

// Teknik Analiz
export interface RSIData {
  time: number;
  value: number;
}

export interface MACDData {
  time: number;
  macd: number;
  signal: number;
  histogram: number;
}

export interface BollingerData {
  time: number;
  upper: number;
  middle: number;
  lower: number;
}

export interface MAData {
  time: number;
  sma_20?: number;
  sma_50?: number;
  sma_200?: number;
  ema_12?: number;
  ema_26?: number;
}

export interface TechnicalSummary {
  symbol: string;
  current_price: number;
  indicators: {
    rsi: { value: number; signal: string };
    macd: { histogram: number; signal: string };
    bollinger: { upper: number; middle: number; lower: number; position: string };
    trend: string;
  };
  signals: Array<{ indicator: string; signal: string; reason: string }>;
  overall_signal: string;
  buy_signals: number;
  sell_signals: number;
  neutral_signals: number;
}

// Temel Analiz
export interface FundamentalData {
  symbol: string;
  company_name: string;
  sector?: string;
  industry?: string;
  current_price?: number;

  // Değerleme
  pe_ratio?: number;
  pb_ratio?: number;
  ps_ratio?: number;
  peg_ratio?: number;

  // Piyasa
  market_cap?: number;
  enterprise_value?: number;

  // Kârlılık
  profit_margin?: number;
  operating_margin?: number;
  roe?: number;
  roa?: number;

  // Temettü
  dividend_yield?: number;
  dividend_rate?: number;

  // Bilanço
  total_revenue?: number;
  total_debt?: number;
  total_cash?: number;
  debt_to_equity?: number;

  // 52 Hafta
  week_52_high?: number;
  week_52_low?: number;

  // Beta
  beta?: number;

  // Analiz Özeti
  analysis_summary?: {
    valuation: string;
    profitability: string;
    growth: string;
    dividend: string;
    overall: string;
    notes: string[];
  };
}

// API Yanıt Tipleri
export interface ApiError {
  error: string;
  detail?: string;
  code?: number;
}

// Period ve Interval
export type Period = '1d' | '5d' | '1mo' | '3mo' | '6mo' | '1y' | '2y' | '5y' | 'max';
export type Interval = '1m' | '5m' | '15m' | '30m' | '1h' | '1d' | '1wk' | '1mo';

export const PERIODS: Record<Period, string> = {
  '1d': '1 Gün',
  '5d': '5 Gün',
  '1mo': '1 Ay',
  '3mo': '3 Ay',
  '6mo': '6 Ay',
  '1y': '1 Yıl',
  '2y': '2 Yıl',
  '5y': '5 Yıl',
  'max': 'Tümü'
};

export const INTERVALS: Record<Interval, string> = {
  '1m': '1 Dk',
  '5m': '5 Dk',
  '15m': '15 Dk',
  '30m': '30 Dk',
  '1h': '1 Saat',
  '1d': '1 Gün',
  '1wk': '1 Hafta',
  '1mo': '1 Ay'
};

// ==========================================
// PRO ANALİZ TİPLERİ
// ==========================================

// Ichimoku Cloud
export interface IchimokuData {
  tenkan_sen: number;
  kijun_sen: number;
  senkou_span_a: number;
  senkou_span_b: number;
  chikou_span: number;
  cloud_top: number;
  cloud_bottom: number;
  cloud_color: string;
  cloud_thickness_pct: number;
  signal: string;
  trend: string;
  strength: number;
  price_vs_cloud: string;
  tk_cross: string;
}

// VWAP
export interface VWAPData {
  vwap: number;
  upper_band_1: number;
  upper_band_2: number;
  lower_band_1: number;
  lower_band_2: number;
  deviation_pct: number;
  signal: string;
  zone: string;
  trend: string;
}

// Volume Profile
export interface VolumeProfileData {
  poc: number;
  value_area_high: number;
  value_area_low: number;
  profile: Array<{ price: number; volume: number }>;
  hvn_levels: number[];
  lvn_levels: number[];
}

// Candlestick Patterns
export interface CandlestickPattern {
  pattern: string;
  pattern_tr: string;
  type: 'bullish' | 'bearish' | 'neutral';
  reliability: 'high' | 'medium' | 'low';
  index: number;
  description: string;
}

export interface CandlestickAnalysis {
  patterns: {
    patterns: CandlestickPattern[];
    pattern_count: number;
    signal: string;
    strength: number;
  };
  last_candle: {
    type: string;
    direction: string;
    body_percent: number;
    change_percent: number;
  };
  candle_trend: {
    trend: string;
    bullish_candles: number;
    bearish_candles: number;
    strength: number;
  };
  volatility: {
    level: string;
    atr: number;
    atr_percent: number;
  };
  overall_signal: string;
  signal_strength: number;
  recent_patterns: CandlestickPattern[];
}

// Divergence
export interface DivergenceData {
  rsi_divergence: { divergence: string; signal: string; strength: number; description?: string };
  macd_divergence: { divergence: string; signal: string; strength: number; description?: string };
}

// SuperTrend
export interface SuperTrendData {
  supertrend: number;
  direction: string;
  signal: string;
  trend: string;
  trend_changed: boolean;
  distance_pct: number;
}

// Risk Metrics
export interface RiskMetrics {
  risk_score: number;
  sharpe_ratio: { sharpe_ratio: number; annualized_return_pct: number; annualized_volatility_pct: number; interpretation: string };
  sortino_ratio: { sortino_ratio: number; downside_deviation_pct: number; interpretation: string };
  max_drawdown: { max_drawdown_pct: number; current_drawdown_pct: number; interpretation: string; in_drawdown: boolean };
  var_95: { var_pct: number; cvar_pct: number; explanation: string };
  var_99: { var_pct: number; cvar_pct: number; explanation: string };
  calmar_ratio: { calmar_ratio: number; interpretation: string };
  beta_analysis: { beta: number; interpretation: string };
  volatility: { daily_pct: number; annualized_pct: number; level: string; trend: string };
  risk_level: string;
  recommendation: string;
}

export interface PositionSizing {
  kelly_fraction: number;
  kelly_position: number;
  fixed_risk_position: number;
  volatility_adjusted_position: number;
  recommended_position: number;
  max_position: number;
}

export interface RiskReport {
  symbol: string;
  metrics: RiskMetrics;
  position_sizing: PositionSizing;
  risk_summary: {
    overall_risk: string;
    notes: string[];
    recommendation: string;
  };
}

// Market Overview
export interface MarketBreadth {
  advancing: number;
  declining: number;
  unchanged: number;
  total: number;
  ad_ratio: number;
  ad_line: number;
  ad_percent: number;
  volume_ad_ratio: number;
  breadth: string;
  market_signal: string;
  bullish_percent: number;
  bearish_percent: number;
  // Legacy fields for compatibility
  new_highs?: number;
  new_lows?: number;
  percent_above_sma20?: number;
  percent_above_sma50?: number;
  percent_above_sma200?: number;
  breadth_signal?: string;
}

export interface FearGreedIndex {
  value: number;
  status: 'extreme_fear' | 'fear' | 'neutral' | 'greed' | 'extreme_greed';
  status_tr: string;
  components: {
    market_momentum: number;
    market_breadth: number;
    volatility: number;
    safe_haven: number;
    put_call_ratio: number;
  };
}

export interface SectorPerformance {
  sector: string;
  // Backend fields
  avg_change_pct?: number;
  stock_count?: number;
  total_volume?: number;
  advancing?: number;
  declining?: number;
  breadth_pct?: number;
  strength_score?: number;
  stocks?: string[];
  // Frontend expected fields (may be calculated)
  performance_1d?: number;
  performance_1w?: number;
  performance_1m?: number;
  relative_strength?: number;
  rotation_phase?: 'leading' | 'weakening' | 'lagging' | 'improving' | string;
  phase_tr?: string;
}

export interface OverallSignal {
  signal: string;
  score: number;
  recommendation: string;
}

export interface MarketOverview {
  breadth?: MarketBreadth;
  market_breadth?: MarketBreadth;
  fear_greed?: FearGreedIndex;
  sentiment?: {
    fear_greed_index: number;
    sentiment: string;
    signal: string;
    color: string;
    components: Record<string, number>;
    interpretation: string;
  };
  sectors?: SectorPerformance[];
  sector_analysis?: {
    sectors: SectorPerformance[];
    leading_sectors: SectorPerformance[];
    lagging_sectors: SectorPerformance[];
    rotation_phase: string;
    rotation_signal: string;
    market_cycle: string;
  };
  market_regime?: string;
  overall_signal: OverallSignal | string;
  stocks_analyzed?: number;
  analysis_timestamp?: string;
}

// AI Signals
export interface AISignal {
  combined_signal: string;
  score: number;
  confidence: number;
  signal_strength: string;
  signal_agreement: number;
  market_condition: string;
  signal_count: number;
  bullish_signals: number;
  bearish_signals: number;
  neutral_signals: number;
  breakdown: Array<{ indicator: string; signal: string; strength: number; weight: number; contribution: number }>;
  risk_level: string;
  entry_timing: string;
  recommendation: string;
  news_impact_bonus?: number;
}

// Pro Analysis (Combined)
export interface ProAnalysis {
  symbol: string;
  name: string;
  sector: string;
  current_price: number;
  analysis_timestamp: string;
  ai_signal: AISignal;
  news_impact?: {
    has_data: boolean;
    sentiment_score: number;
    sentiment_label: string;
    news_count: number;
    positive_count?: number;
    negative_count?: number;
    neutral_count?: number;
    strong_positive_count?: number;
    strong_negative_count?: number;
    impact_summary: string;
    recent_news?: Array<{
      title: string;
      date: string;
      category: string;
      sentiment_score: number;
      impact: string;
      impact_icon: string;
      url: string;
    }>;
  };
  pro_indicators: {
    ichimoku: IchimokuData;
    vwap: VWAPData;
    volume_profile: VolumeProfileData;
    supertrend: SuperTrendData;
    market_regime: {
      regime: string;
      confidence: number;
      trend_strength: number;
      trend_direction: string;
      volatility_pct: number;
      volume_trend: string;
      suggested_strategy: string;
    };
  };
  divergence_analysis: DivergenceData;
  candlestick_analysis: CandlestickAnalysis;
  advanced_indicators: {
    adx: { adx: number; plus_di: number; minus_di: number; trend_strength: string; trend_direction: string };
    fibonacci: { levels: Record<string, number>; current_zone: string; high: number; low: number };
    obv: { obv: number; obv_sma: number; obv_signal: string; divergence: string };
    support_resistance: { supports: number[]; resistances: number[]; nearest_support: number; nearest_resistance: number; support_distance_pct: number; resistance_distance_pct: number };
  };
  chart_patterns: Array<{ pattern: string; signal: string; strength: string; description: string; target: number }>;
  risk_analysis: RiskMetrics;
  position_advice: {
    suggested_position_pct: number;
    advice: string;
    suggested_stop_loss: number;
    suggested_target: number;
    risk_reward_ratio: number;
    risk_level: string;
  };
  // Eski uyumluluk için alias'lar
  ichimoku?: IchimokuData;
  vwap?: VWAPData;
  supertrend?: SuperTrendData;
  divergence?: DivergenceData;
  candlestick?: CandlestickAnalysis;
  risk?: RiskMetrics;
}
