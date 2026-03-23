'use client';

import { useState, useEffect, useCallback } from 'react';

interface MacroHeadline {
  title: string;
  summary: string;
  source: string;
  date: string;
  url: string;
  category: string;
  icon: string;
  age_hours: number;
  bist_impact_score: number;
  impact_label: string;
  impact_color: string;
  matched_keywords: string[];
}

interface CategorySummary {
  avg_score: number;
  direction: 'positive' | 'negative' | 'neutral';
  count: number;
  explanation: string;
  top_headlines: { title: string; source: string; date: string; impact: string }[];
  icon: string;
}

interface MacroSentimentData {
  macro_score: number;
  macro_label: string;
  macro_color: string;
  bist_impact: 'positive' | 'negative' | 'neutral';
  confidence: number;
  recommendation: string;
  risk_factors: MacroHeadline[];
  positive_factors: MacroHeadline[];
  neutral_factors: MacroHeadline[];
  by_category: Record<string, CategorySummary>;
  total_headlines: number;
  analyzed_at: string;
  cache_valid_until: string;
}

const DIRECTION_COLORS: Record<string, { bg: string; border: string; text: string; badge: string }> = {
  positive: {
    bg: 'bg-emerald-500/10',
    border: 'border-emerald-500/30',
    text: 'text-emerald-400',
    badge: 'bg-emerald-500/20 text-emerald-300',
  },
  negative: {
    bg: 'bg-red-500/10',
    border: 'border-red-500/30',
    text: 'text-red-400',
    badge: 'bg-red-500/20 text-red-300',
  },
  neutral: {
    bg: 'bg-slate-700/40',
    border: 'border-slate-600/30',
    text: 'text-slate-400',
    badge: 'bg-slate-600/40 text-slate-300',
  },
};

function ScoreGauge({ score }: { score: number }) {
  // score: -1..+1, mapped to 0..180 degrees
  const clamp = Math.max(-1, Math.min(1, score));
  const angle = ((clamp + 1) / 2) * 180; // 0Â° = full left, 180Â° = full right
  const rad = ((angle - 90) * Math.PI) / 180;
  const r = 52;
  const cx = 70;
  const cy = 68;
  const nx = cx + r * Math.sin(rad);
  const ny = cy - r * Math.cos(rad);

  let gaugeColor = '#6b7280'; // gray
  if (clamp >= 0.4) gaugeColor = '#10b981';
  else if (clamp >= 0.15) gaugeColor = '#34d399';
  else if (clamp <= -0.4) gaugeColor = '#ef4444';
  else if (clamp <= -0.15) gaugeColor = '#f97316';

  return (
    <svg viewBox="0 0 140 80" className="w-36 h-20">
      {/* Background arc segments (red â†’ orange â†’ gray â†’ green â†’ emerald) */}
      <path d="M 18 68 A 52 52 0 0 1 122 68" fill="none" stroke="#1f2937" strokeWidth="10" strokeLinecap="round" />
      {/* Colored zone arcs */}
      <path d="M 18 68 A 52 52 0 0 1 40 28" fill="none" stroke="#ef4444" strokeWidth="8" strokeLinecap="butt" opacity="0.6" />
      <path d="M 40 28 A 52 52 0 0 1 70 16" fill="none" stroke="#f97316" strokeWidth="8" strokeLinecap="butt" opacity="0.5" />
      <path d="M 70 16 A 52 52 0 0 1 100 28" fill="none" stroke="#6b7280" strokeWidth="8" strokeLinecap="butt" opacity="0.4" />
      <path d="M 100 28 A 52 52 0 0 1 122 68" fill="none" stroke="#10b981" strokeWidth="8" strokeLinecap="butt" opacity="0.6" />
      {/* Needle */}
      <line x1={cx} y1={cy} x2={nx} y2={ny} stroke={gaugeColor} strokeWidth="2.5" strokeLinecap="round" />
      <circle cx={cx} cy={cy} r="4" fill={gaugeColor} />
    </svg>
  );
}

function getRelativeTime(dateStr: string): string {
  if (!dateStr) return '';
  try {
    const date = new Date(dateStr.replace(' ', 'T'));
    const diffH = (Date.now() - date.getTime()) / 3_600_000;
    if (diffH < 1) return `${Math.floor(diffH * 60)} dk`;
    if (diffH < 24) return `${Math.floor(diffH)} sa`;
    return `${Math.floor(diffH / 24)} gün`;
  } catch { return dateStr; }
}

export default function MacroSentimentPanel() {
  const [data, setData] = useState<MacroSentimentData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'overview' | 'risks' | 'positive' | 'categories'>('overview');
  const [expandedCategory, setExpandedCategory] = useState<string | null>(null);

  const fetchData = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) setRefreshing(true);
      else setLoading(true);
      setError(null);

      const url = `http://localhost:8000/api/news/macro-sentiment${forceRefresh ? '?refresh=true' : ''}`;
      const resp = await fetch(url);
      if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
      const json: MacroSentimentData = await resp.json();
      setData(json);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Veri alınamadı');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { fetchData(); }, [fetchData]);

  if (loading) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-6 animate-pulse">
        <div className="h-5 bg-slate-700 rounded w-48 mb-4" />
        <div className="h-32 bg-slate-700/50 rounded-lg mb-3" />
        <div className="h-24 bg-slate-700/50 rounded-lg" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="bg-slate-800/60 border border-slate-700/50 rounded-xl p-5">
        <div className="flex items-center gap-2 text-slate-400 text-sm">
          <span>🌐</span>
          <span>Makro gündem yüklenemedi: {error}</span>
          <button
            onClick={() => fetchData()}
            className="ml-auto text-xs bg-slate-700 hover:bg-slate-600 px-3 py-1 rounded text-slate-300"
          >
            Yenile
          </button>
        </div>
      </div>
    );
  }

  const mainColor: Record<string, { border: string; bg: string; text: string; badge: string }> = {
    emerald: { border: 'border-emerald-500/40', bg: 'bg-emerald-500/10', text: 'text-emerald-400', badge: 'bg-emerald-500/20 text-emerald-300' },
    green:   { border: 'border-green-500/40',   bg: 'bg-green-500/10',   text: 'text-green-400',   badge: 'bg-green-500/20 text-green-300' },
    gray:    { border: 'border-slate-600/40',    bg: 'bg-slate-700/30',   text: 'text-slate-400',   badge: 'bg-slate-600/40 text-slate-300' },
    orange:  { border: 'border-orange-500/40',   bg: 'bg-orange-500/10',  text: 'text-orange-400',  badge: 'bg-orange-500/20 text-orange-300' },
    red:     { border: 'border-red-500/40',      bg: 'bg-red-500/10',     text: 'text-red-400',     badge: 'bg-red-500/20 text-red-300' },
  };
  const mc = mainColor[data.macro_color] ?? mainColor.gray;

  const tabs = [
    { id: 'overview',    label: 'Genel Bakış', count: null },
    { id: 'risks',       label: 'Riskler',     count: data.risk_factors.length },
    { id: 'positive',    label: 'Olumlu',      count: data.positive_factors.length },
    { id: 'categories',  label: 'Kategoriler', count: Object.keys(data.by_category).length },
  ] as const;

  return (
    <div className={`bg-slate-800/60 border ${mc.border} rounded-xl overflow-hidden`}>
      {/* Header */}
      <div className={`px-5 py-4 border-b border-slate-700/50 ${mc.bg}`}>
        <div className="flex items-center justify-between flex-wrap gap-3">
          <div className="flex items-center gap-3">
            <span className="text-xl">🌐</span>
            <div>
              <h3 className="text-sm font-semibold text-slate-100">Makro Gündem Analizi</h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {data.total_headlines} haber Â· {data.analyzed_at} Â· cache:{' '}
                <span className="text-slate-300">{data.cache_valid_until}'e kadar</span>
              </p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${mc.badge}`}>
              {data.macro_label}
            </span>
            <button
              onClick={() => fetchData(true)}
              disabled={refreshing}
              title="Yenile"
              className="text-slate-400 hover:text-slate-200 transition-colors disabled:opacity-50 p-1"
            >
              <svg className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
              </svg>
            </button>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-700/50 overflow-x-auto">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex items-center gap-1.5 px-4 py-2.5 text-xs font-medium whitespace-nowrap transition-colors ${
              activeTab === tab.id
                ? `${mc.text} border-b-2 ${mc.border.replace('border-', 'border-b-')}`
                : 'text-slate-400 hover:text-slate-200 border-b-2 border-transparent'
            }`}
          >
            {tab.label}
            {tab.count !== null && tab.count > 0 && (
              <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                tab.id === 'risks' ? 'bg-red-500/20 text-red-300' :
                tab.id === 'positive' ? 'bg-emerald-500/20 text-emerald-300' :
                'bg-slate-600/50 text-slate-300'
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="p-5">

        {/* ── GENEL BAKIŞ ── */}
        {activeTab === 'overview' && (
          <div className="space-y-5">
            {/* Gauge + Score */}
            <div className="flex items-center gap-5">
              <div className="flex flex-col items-center">
                <ScoreGauge score={data.macro_score} />
                <span className={`text-xl font-bold mt-1 ${mc.text}`}>
                  {data.macro_score > 0 ? '+' : ''}{data.macro_score.toFixed(2)}
                </span>
                <span className="text-xs text-slate-400">BIST Etki Skoru</span>
              </div>
              <div className="flex-1 min-w-0">
                {/* BIST Yönü */}
                <div className="flex items-center gap-2 mb-3">
                  <span className={`text-2xl font-bold ${mc.text}`}>
                    {data.bist_impact === 'positive' ? 'â–²' : data.bist_impact === 'negative' ? 'â–¼' : 'â€”'}
                  </span>
                  <div>
                    <p className={`text-sm font-semibold ${mc.text}`}>{data.macro_label}</p>
                    <p className="text-xs text-slate-400">
                      Güven: {Math.round(data.confidence * 100)}%
                    </p>
                  </div>
                </div>
                {/* Mini category bar */}
                <div className="flex flex-col gap-1.5">
                  {Object.entries(data.by_category).slice(0, 4).map(([cat, info]) => {
                    const dc = DIRECTION_COLORS[info.direction];
                    return (
                      <div key={cat} className="flex items-center gap-2">
                        <span className="text-sm w-5 text-center">{info.icon}</span>
                        <span className="text-xs text-slate-300 w-28 truncate">{cat}</span>
                        <div className="flex-1 h-1.5 bg-slate-700 rounded-full overflow-hidden">
                          <div
                            className={`h-full rounded-full ${
                              info.avg_score >= 0 ? 'bg-emerald-500' : 'bg-red-500'
                            }`}
                            style={{ width: `${Math.min(100, Math.abs(info.avg_score) * 100)}%` }}
                          />
                        </div>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${dc.badge} w-16 text-center`}>
                          {info.avg_score > 0 ? '+' : ''}{info.avg_score.toFixed(2)}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Öneri */}
            <div className={`rounded-lg border ${mc.border} ${mc.bg} p-4`}>
              <p className="text-xs font-semibold text-slate-300 mb-2 flex items-center gap-1.5">
                <span>��</span> Yatırımcı Notu
              </p>
              <p className="text-sm text-slate-200 leading-relaxed">{data.recommendation}</p>
            </div>

            {/* Top Riskler & Olumlu */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              {/* Riskler */}
              {data.risk_factors.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-red-400 mb-2 flex items-center gap-1">
                    <span>âš ï¸</span> Öne Çıkan Riskler
                  </p>
                  <div className="space-y-2">
                    {data.risk_factors.slice(0, 3).map((h, i) => (
                      <div key={i} className="bg-red-500/5 border border-red-500/15 rounded-lg p-3">
                        <p className="text-xs text-slate-200 leading-snug line-clamp-2">{h.title}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[10px] text-slate-400">{h.source}</span>
                          <span className="text-[10px] text-slate-500">Â·</span>
                          <span className="text-[10px] text-slate-400">{getRelativeTime(h.date)} önce</span>
                          <ImpactBar score={h.bist_impact_score} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Olumlu */}
              {data.positive_factors.length > 0 && (
                <div>
                  <p className="text-xs font-medium text-emerald-400 mb-2 flex items-center gap-1">
                    <span>✅</span> Olumlu Gelişmeler
                  </p>
                  <div className="space-y-2">
                    {data.positive_factors.slice(0, 3).map((h, i) => (
                      <div key={i} className="bg-emerald-500/5 border border-emerald-500/15 rounded-lg p-3">
                        <p className="text-xs text-slate-200 leading-snug line-clamp-2">{h.title}</p>
                        <div className="flex items-center gap-2 mt-1.5">
                          <span className="text-[10px] text-slate-400">{h.source}</span>
                          <span className="text-[10px] text-slate-500">Â·</span>
                          <span className="text-[10px] text-slate-400">{getRelativeTime(h.date)} önce</span>
                          <ImpactBar score={h.bist_impact_score} />
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* ── RİSKLER ── */}
        {activeTab === 'risks' && (
          <div className="space-y-2">
            {data.risk_factors.length === 0 ? (
              <p className="text-slate-400 text-sm text-center py-8">
                Şu an öne çıkan risk faktörü bulunamadı ✅
              </p>
            ) : data.risk_factors.map((h, i) => (
              <HeadlineCard key={i} headline={h} />
            ))}
          </div>
        )}

        {/* ── OLUMLU ── */}
        {activeTab === 'positive' && (
          <div className="space-y-2">
            {data.positive_factors.length === 0 ? (
              <p className="text-slate-400 text-sm text-center py-8">
                Şu an öne çıkan olumlu gelişme bulunamadı
              </p>
            ) : data.positive_factors.map((h, i) => (
              <HeadlineCard key={i} headline={h} />
            ))}
          </div>
        )}

        {/* ── KATEGORİLER ── */}
        {activeTab === 'categories' && (
          <div className="space-y-2">
            {Object.entries(data.by_category).map(([cat, info]) => {
              const dc = DIRECTION_COLORS[info.direction];
              const isExpanded = expandedCategory === cat;
              return (
                <div
                  key={cat}
                  className={`border ${dc.border} rounded-lg overflow-hidden`}
                >
                  <button
                    className={`w-full flex items-center gap-3 px-4 py-3 ${dc.bg} text-left hover:brightness-110 transition-all`}
                    onClick={() => setExpandedCategory(isExpanded ? null : cat)}
                  >
                    <span className="text-xl">{info.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-medium text-slate-100">{cat}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded ${dc.badge}`}>
                          {info.avg_score > 0 ? '+' : ''}{info.avg_score.toFixed(2)}
                        </span>
                        <span className="text-xs text-slate-400">{info.count} haber</span>
                      </div>
                      {!isExpanded && info.explanation && (
                        <p className="text-xs text-slate-400 mt-0.5 line-clamp-1">{info.explanation}</p>
                      )}
                    </div>
                    <svg
                      className={`w-4 h-4 text-slate-400 transition-transform flex-shrink-0 ${isExpanded ? 'rotate-180' : ''}`}
                      fill="none" viewBox="0 0 24 24" stroke="currentColor"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>
                  {isExpanded && (
                    <div className="px-4 py-3 bg-slate-800/50 space-y-3">
                      {info.explanation && (
                        <p className="text-xs text-slate-300 leading-relaxed border-l-2 border-slate-600 pl-3">
                          {info.explanation}
                        </p>
                      )}
                      {info.top_headlines.length > 0 && (
                        <div className="space-y-2">
                          <p className="text-[10px] text-slate-500 uppercase tracking-wider font-medium">
                            Son Haberler
                          </p>
                          {info.top_headlines.map((h, i) => (
                            <div key={i} className="flex items-start gap-2">
                              <div className="flex-1 min-w-0">
                                <p className="text-xs text-slate-200 leading-snug line-clamp-2">{h.title}</p>
                                <div className="flex items-center gap-2 mt-1">
                                  <span className="text-[10px] text-slate-400">{h.source}</span>
                                  <span className={`text-[10px] px-1.5 py-0.5 rounded ${
                                    h.impact === 'Olumlu' || h.impact === 'Hafif Olumlu'
                                      ? 'bg-emerald-500/20 text-emerald-300'
                                      : h.impact === 'Olumsuz' || h.impact === 'Hafif Olumsuz'
                                      ? 'bg-red-500/20 text-red-300'
                                      : 'bg-slate-600/40 text-slate-300'
                                  }`}>
                                    {h.impact}
                                  </span>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}

function HeadlineCard({ headline }: { headline: MacroHeadline }) {
  const isPos = headline.bist_impact_score >= 0;
  const coloring = isPos
    ? 'border-emerald-500/20 bg-emerald-500/5'
    : 'border-red-500/20 bg-red-500/5';

  return (
    <div className={`border ${coloring} rounded-lg p-3`}>
      <div className="flex items-start gap-2">
        <span className="text-base mt-0.5 flex-shrink-0">{headline.icon || '��'}</span>
        <div className="flex-1 min-w-0">
          {headline.url ? (
            <a
              href={headline.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-slate-100 hover:text-white leading-snug line-clamp-2 hover:underline"
            >
              {headline.title}
            </a>
          ) : (
            <p className="text-sm text-slate-100 leading-snug line-clamp-2">{headline.title}</p>
          )}
          {headline.summary && (
            <p className="text-xs text-slate-400 mt-1 line-clamp-2">{headline.summary}</p>
          )}
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <span className="text-[10px] text-slate-400">{headline.source}</span>
            <span className="text-[10px] text-slate-500">Â·</span>
            <span className="text-[10px] text-slate-400">{getRelativeTime(headline.date)} önce</span>
            <span className="text-[10px] text-slate-500">Â·</span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${
              isPos
                ? 'bg-emerald-500/20 text-emerald-300'
                : 'bg-red-500/20 text-red-300'
            }`}>
              {headline.impact_label}
            </span>
            <ImpactBar score={headline.bist_impact_score} />
          </div>
          {headline.matched_keywords.length > 0 && (
            <div className="flex flex-wrap gap-1 mt-1.5">
              {headline.matched_keywords.map((kw, i) => (
                <span
                  key={i}
                  className={`text-[9px] px-1.5 py-0.5 rounded ${
                    kw.startsWith('+')
                      ? 'bg-emerald-900/50 text-emerald-400'
                      : 'bg-red-900/50 text-red-400'
                  }`}
                >
                  {kw}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function ImpactBar({ score }: { score: number }) {
  const pct = Math.abs(score) * 100;
  const isPos = score >= 0;
  return (
    <div className="flex items-center gap-1.5 flex-1 min-w-[80px]">
      <span className={`text-[10px] w-8 text-right tabular-nums ${isPos ? 'text-emerald-400' : 'text-red-400'}`}>
        {isPos ? '+' : ''}{score.toFixed(2)}
      </span>
      <div className="flex-1 h-1 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full ${isPos ? 'bg-emerald-500' : 'bg-red-500'}`}
          style={{ width: `${Math.min(100, pct)}%` }}
        />
      </div>
    </div>
  );
}
