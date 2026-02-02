/**
 * HisseRadar API İstemcisi
 * ========================
 * Backend API'leri ile iletişim kurar
 */

import type {
  Stock,
  StockListResponse,
  PriceResponse,
  CandleData,
  VolumeData,
  TechnicalSummary,
  FundamentalData,
  Period,
  Interval
} from '@/types';

// API Base URL
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Genel API istek fonksiyonu
 */
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: 'API hatası' }));
      throw new Error(error.detail || error.error || `HTTP ${response.status}`);
    }

    return response.json();
  } catch (error) {
    console.error(`API Hatası (${endpoint}):`, error);
    throw error;
  }
}

// ==========================================
// HİSSE API'LERİ
// ==========================================

/**
 * Tüm hisseleri getir
 */
export async function getStocks(sector?: string, search?: string): Promise<StockListResponse> {
  const params = new URLSearchParams();
  if (sector) params.append('sector', sector);
  if (search) params.append('search', search);
  
  const query = params.toString();
  return fetchAPI<StockListResponse>(`/api/stocks${query ? `?${query}` : ''}`);
}

/**
 * Sektörleri getir
 */
export async function getSectors(): Promise<{ sectors: string[]; total: number }> {
  return fetchAPI('/api/stocks/sectors');
}

/**
 * Tek bir hissenin bilgilerini getir
 */
export async function getStockInfo(symbol: string): Promise<Stock> {
  return fetchAPI<Stock>(`/api/stocks/${symbol}`);
}

/**
 * Hisse ara
 */
export async function searchStocks(query: string): Promise<StockListResponse> {
  return fetchAPI<StockListResponse>(`/api/stocks?search=${encodeURIComponent(query)}`);
}

// ==========================================
// FİYAT API'LERİ
// ==========================================

/**
 * Fiyat geçmişini getir
 */
export async function getPriceHistory(
  symbol: string,
  period: Period = '3mo',
  interval: Interval = '1d'
): Promise<PriceResponse> {
  return fetchAPI<PriceResponse>(
    `/api/price/${symbol}?period=${period}&interval=${interval}`
  );
}

/**
 * TradingView mum verilerini getir
 */
export async function getCandleData(
  symbol: string,
  period: Period = '3mo',
  interval: Interval = '1d'
): Promise<{ symbol: string; candles: CandleData[] }> {
  return fetchAPI(`/api/price/${symbol}/candles?period=${period}&interval=${interval}`);
}

/**
 * Hacim verilerini getir
 */
export async function getVolumeData(
  symbol: string,
  period: Period = '3mo',
  interval: Interval = '1d'
): Promise<{ symbol: string; volumes: VolumeData[] }> {
  return fetchAPI(`/api/price/${symbol}/volume?period=${period}&interval=${interval}`);
}

/**
 * Güncel fiyatı getir
 */
export async function getLatestPrice(symbol: string): Promise<{
  symbol: string;
  current_price: number;
  previous_close: number;
  change: number;
  change_percent: number;
  volume: number;
}> {
  return fetchAPI(`/api/price/${symbol}/latest`);
}

// ==========================================
// TEKNİK ANALİZ API'LERİ
// ==========================================

/**
 * Tüm teknik göstergeleri getir
 */
export async function getTechnicalIndicators(
  symbol: string,
  period: Period = '6mo',
  interval: Interval = '1d'
) {
  return fetchAPI(`/api/technical/${symbol}?period=${period}&interval=${interval}`);
}

/**
 * RSI göstergesini getir
 */
export async function getRSI(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/technical/${symbol}/rsi?period=${period}`);
}

/**
 * MACD göstergesini getir
 */
export async function getMACD(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/technical/${symbol}/macd?period=${period}`);
}

/**
 * Bollinger Bands getir
 */
export async function getBollinger(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/technical/${symbol}/bollinger?period=${period}`);
}

/**
 * Hareketli ortalamaları getir
 */
export async function getMovingAverages(symbol: string, period: Period = '1y') {
  return fetchAPI(`/api/technical/${symbol}/ma?period=${period}`);
}

/**
 * Teknik analiz özeti
 */
export async function getTechnicalSummary(symbol: string): Promise<TechnicalSummary> {
  return fetchAPI<TechnicalSummary>(`/api/technical/${symbol}/summary`);
}

// ==========================================
// TEMEL ANALİZ API'LERİ
// ==========================================

/**
 * Kapsamlı temel analiz verilerini getir
 */
export async function getFundamentalData(symbol: string): Promise<FundamentalData> {
  return fetchAPI<FundamentalData>(`/api/fundamental/${symbol}`);
}

/**
 * Değerleme oranlarını getir
 */
export async function getValuationRatios(symbol: string) {
  return fetchAPI(`/api/fundamental/${symbol}/valuation`);
}

/**
 * Kârlılık oranlarını getir
 */
export async function getProfitabilityRatios(symbol: string) {
  return fetchAPI(`/api/fundamental/${symbol}/profitability`);
}

/**
 * Temettü bilgilerini getir
 */
export async function getDividendInfo(symbol: string) {
  return fetchAPI(`/api/fundamental/${symbol}/dividend`);
}

/**
 * Bilanço özetini getir
 */
export async function getBalanceSheet(symbol: string) {
  return fetchAPI(`/api/fundamental/${symbol}/balance`);
}

/**
 * Temel analiz özeti
 */
export async function getFundamentalSummary(symbol: string) {
  return fetchAPI(`/api/fundamental/${symbol}/summary`);
}

// ==========================================
// YARDIMCI FONKSİYONLAR
// ==========================================

/**
 * Sayıyı para formatına çevir
 */
export function formatCurrency(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-';
  return new Intl.NumberFormat('tr-TR', {
    style: 'currency',
    currency: 'TRY',
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

/**
 * Büyük sayıları formatla
 */
export function formatLargeNumber(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-';
  
  if (value >= 1e12) return `${(value / 1e12).toFixed(2)}T`;
  if (value >= 1e9) return `${(value / 1e9).toFixed(2)}B`;
  if (value >= 1e6) return `${(value / 1e6).toFixed(2)}M`;
  if (value >= 1e3) return `${(value / 1e3).toFixed(2)}K`;
  
  return value.toFixed(2);
}

/**
 * Yüzde formatla
 */
export function formatPercent(value: number | undefined | null): string {
  if (value === undefined || value === null) return '-';
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(2)}%`;
}

/**
 * Değişim rengini belirle
 */
export function getChangeColor(value: number | undefined | null): string {
  if (value === undefined || value === null) return 'text-gray-500';
  if (value > 0) return 'text-up';
  if (value < 0) return 'text-down';
  return 'text-gray-500';
}

// ==========================================
// PRO ANALİZ API'LERİ
// ==========================================

/**
 * Tam profesyonel analiz getir
 */
export async function getProAnalysis(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/pro/analysis/${symbol}?period=${period}`);
}

/**
 * Ichimoku Cloud verilerini getir
 */
export async function getIchimoku(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/pro/ichimoku/${symbol}?period=${period}`);
}

/**
 * VWAP verilerini getir
 */
export async function getVWAP(symbol: string, period: Period = '1mo') {
  return fetchAPI(`/api/pro/vwap/${symbol}?period=${period}`);
}

/**
 * Mum formasyonlarını getir
 */
export async function getCandlestickPatterns(symbol: string, period: Period = '3mo') {
  return fetchAPI(`/api/pro/candlestick/${symbol}?period=${period}`);
}

/**
 * Diverjans verilerini getir
 */
export async function getDivergence(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/pro/divergence/${symbol}?period=${period}`);
}

/**
 * SuperTrend verilerini getir
 */
export async function getSuperTrend(symbol: string, period: Period = '6mo') {
  return fetchAPI(`/api/pro/supertrend/${symbol}?period=${period}`);
}

/**
 * Risk raporu getir
 */
export async function getRiskReport(symbol: string, period: Period = '1y') {
  return fetchAPI(`/api/pro/risk-report/${symbol}?period=${period}`);
}

/**
 * Piyasa genel görünümü getir
 */
export async function getMarketOverview() {
  return fetchAPI('/api/pro/market-overview');
}

/**
 * Sektör rotasyonu getir
 */
export async function getSectorRotation() {
  return fetchAPI('/api/pro/sector-rotation');
}

/**
 * Fear & Greed endeksi getir
 */
export async function getFearGreedIndex() {
  return fetchAPI('/api/pro/fear-greed');
}

/**
 * Çoklu hisse karşılaştırma
 */
export async function compareStocks(symbols: string[]) {
  return fetchAPI('/api/pro/compare', {
    method: 'POST',
    body: JSON.stringify({ symbols })
  });
}

/**
 * Güçlü sinyalli hisseleri getir
 */
export async function getStrongSignals(minConfidence: number = 70) {
  return fetchAPI(`/api/pro/signals/strong?min_confidence=${minConfidence}`);
}

/**
 * Pro gösterge bilgileri
 */
export async function getProIndicatorsInfo() {
  return fetchAPI('/api/pro/indicators-info');
}

// ==========================================
// AI TAHMİN API'LERİ
// ==========================================

/**
 * AI fiyat tahmini al
 */
export async function getAIPrediction(symbol: string, days: number = 7, model: string = 'ensemble') {
  return fetchAPI(`/api/ai/predict/${symbol}?days=${days}&model=${model}`);
}

/**
 * AI al/sat sinyali al
 */
export async function getAISignal(symbol: string) {
  return fetchAPI(`/api/ai/signal/${symbol}`);
}

/**
 * Toplu AI sinyalleri
 */
export async function getBatchAISignals(symbols: string[]) {
  return fetchAPI(`/api/ai/batch-signals?symbols=${symbols.join(',')}`);
}

/**
 * AI model bilgileri
 */
export async function getAIModelInfo() {
  return fetchAPI('/api/ai/model-info');
}

// ==========================================
// GELİŞMİŞ TEMEL ANALİZ API'LERİ
// ==========================================

/**
 * Kapsamlı temel analiz
 */
export async function getAdvancedFundamental(symbol: string) {
  return fetchAPI(`/api/fundamental/analysis/${symbol}`);
}

/**
 * Hızlı temel analiz
 */
export async function getQuickFundamental(symbol: string) {
  return fetchAPI(`/api/fundamental/quick/${symbol}`);
}

/**
 * Bilanço grafik verileri
 */
export async function getFundamentalCharts(symbol: string) {
  return fetchAPI(`/api/fundamental/charts/${symbol}`);
}

/**
 * Temel analiz karşılaştırma
 */
export async function compareFundamentals(symbols: string[]) {
  return fetchAPI(`/api/fundamental/compare?symbols=${symbols.join(',')}`);
}
