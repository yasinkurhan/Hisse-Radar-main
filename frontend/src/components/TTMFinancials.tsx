'use client';

/**
 * TTM Finansallar Bileşeni
 * =========================
 * Son 12 Ay (Trailing Twelve Months) finansal tablolar
 */

import { useEffect, useState } from 'react';
import { BarChart3, TrendingUp, Banknote, AlertCircle, Loader2, ChevronDown, ChevronUp } from 'lucide-react';
import { getTTMFinancials, getUFRSFinancials } from '@/lib/api';

interface TTMFinancialsProps {
  symbol: string;
}

export default function TTMFinancials({ symbol }: TTMFinancialsProps) {
  const [ttmData, setTtmData] = useState<any>(null);
  const [ufrsData, setUfrsData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [activeView, setActiveView] = useState<'ttm' | 'ufrs'>('ttm');
  const [expandedTable, setExpandedTable] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const [ttm, ufrs] = await Promise.all([
          getTTMFinancials(symbol).catch(() => null),
          getUFRSFinancials(symbol).catch(() => null),
        ]);
        setTtmData(ttm);
        setUfrsData(ufrs);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [symbol]);

  const formatNumber = (val: any) => {
    if (val === null || val === undefined) return '-';
    const num = Number(val);
    if (isNaN(num)) return String(val);
    if (Math.abs(num) >= 1e9) return `${(num / 1e9).toFixed(2)}B TL`;
    if (Math.abs(num) >= 1e6) return `${(num / 1e6).toFixed(2)}M TL`;
    if (Math.abs(num) >= 1e3) return `${(num / 1e3).toFixed(2)}K TL`;
    return num.toLocaleString('tr-TR');
  };

  const formatLabel = (key: string) => {
    const labels: Record<string, string> = {
      'TotalRevenue': 'Toplam Gelir',
      'Total Revenue': 'Toplam Gelir',
      'NetIncome': 'Net Kar',
      'Net Income': 'Net Kar',
      'GrossProfit': 'Brüt Kar',
      'Gross Profit': 'Brüt Kar',
      'OperatingIncome': 'Faaliyet Karı',
      'Operating Income': 'Faaliyet Karı',
      'EBITDA': 'FAVÖK',
      'TotalAssets': 'Toplam Varlıklar',
      'Total Assets': 'Toplam Varlıklar',
      'TotalLiab': 'Toplam Yükümlülükler',
      'Total Liabilities Net Minority Interest': 'Toplam Yükümlülükler',
      'TotalDebt': 'Toplam Borç',
      'Total Debt': 'Toplam Borç',
      'TotalEquity': 'Özsermaye',
      'Stockholders Equity': 'Özsermaye',
      'OperatingCashflow': 'Faaliyet Nakit Akışı',
      'Operating Cash Flow': 'Faaliyet Nakit Akışı',
      'FreeCashflow': 'Serbest Nakit Akışı',
      'Free Cash Flow': 'Serbest Nakit Akışı',
      'CapitalExpenditure': 'Yatırım Harcamaları',
      'Capital Expenditure': 'Yatırım Harcamaları',
      'CostOfRevenue': 'Satış Maliyeti',
      'Cost Of Revenue': 'Satış Maliyeti',
      'OperatingExpense': 'Faaliyet Giderleri',
      'Operating Expense': 'Faaliyet Giderleri',
      'InterestExpense': 'Faiz Gideri',
      'Interest Expense': 'Faiz Gideri',
      'TaxProvision': 'Vergi Karşılığı',
      'Tax Provision': 'Vergi Karşılığı',
      'CurrentAssets': 'Dönen Varlıklar',
      'Current Assets': 'Dönen Varlıklar',
      'CurrentLiabilities': 'Kısa Vadeli Yükümlülükler',
      'Current Liabilities': 'Kısa Vadeli Yükümlülükler',
      'Cash And Cash Equivalents': 'Nakit ve Nakit Benzerleri',
      'Research And Development': 'Ar-Ge Giderleri',
      'Diluted EPS': 'Seyreltilmiş HBK',
      'Basic EPS': 'Temel HBK',
    };
    return labels[key] || key.replace(/([A-Z])/g, ' $1').trim();
  };

  const renderFinancialTable = (data: any, title: string, icon: React.ReactNode, tableKey: string) => {
    if (!data) return null;
    
    const isExpanded = expandedTable === tableKey;
    
    // Data might be {column: {row: value}} format from pandas to_dict()
    let rows: Array<{ label: string; values: Array<{ period: string; value: any }> }> = [];
    
    if (typeof data === 'object' && !Array.isArray(data)) {
      const columns = Object.keys(data);
      
      if (columns.length > 0 && typeof data[columns[0]] === 'object') {
        // Pandas-style: {row_name: {col_name: value}}
        const allRows = new Set<string>();
        const allCols: string[] = [];
        
        for (const rowKey of columns) {
          if (typeof data[rowKey] === 'object') {
            allCols.push(rowKey);
            Object.keys(data[rowKey]).forEach(col => allRows.add(col));
          }
        }
        
        // If columns look like dates or periods, treat as periods
        rows = Array.from(allRows).map(rowName => ({
          label: formatLabel(rowName),
          values: allCols.map(col => ({
            period: String(col).substring(0, 10),
            value: data[col]?.[rowName],
          }))
        }));
      }
    }
    
    const displayRows = isExpanded ? rows : rows.slice(0, 8);
    const periods = displayRows.length > 0 ? displayRows[0].values.map(v => v.period) : [];

    if (rows.length === 0) return null;

    return (
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <button
          onClick={() => setExpandedTable(isExpanded ? null : tableKey)}
          className="w-full flex items-center justify-between p-4 bg-gray-50 hover:bg-gray-100 transition-colors"
        >
          <div className="flex items-center gap-2">
            {icon}
            <h4 className="font-medium text-gray-900 text-sm">{title}</h4>
            <span className="text-xs text-gray-400">({rows.length} kalem)</span>
          </div>
          {isExpanded ? <ChevronUp className="w-4 h-4 text-gray-500" /> : <ChevronDown className="w-4 h-4 text-gray-500" />}
        </button>
        
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-gray-200 bg-gray-50/50">
                <th className="text-left py-2 px-3 text-gray-600 font-medium text-xs min-w-[200px]">Kalem</th>
                {periods.map((p, i) => (
                  <th key={i} className="text-right py-2 px-3 text-gray-600 font-medium text-xs min-w-[120px]">
                    {p}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {displayRows.map((row, idx) => (
                <tr key={idx} className="border-b border-gray-100 hover:bg-gray-50">
                  <td className="py-2 px-3 text-gray-700 font-medium text-xs">{row.label}</td>
                  {row.values.map((v, i) => (
                    <td key={i} className={`py-2 px-3 text-right font-mono text-xs ${
                      typeof v.value === 'number' && v.value < 0 ? 'text-red-600' : 'text-gray-800'
                    }`}>
                      {formatNumber(v.value)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {rows.length > 8 && !isExpanded && (
          <button 
            onClick={() => setExpandedTable(tableKey)}
            className="w-full text-center py-2 text-xs text-blue-600 hover:text-blue-800 bg-gray-50"
          >
            Tümünü göster ({rows.length} kalem)
          </button>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">Gelişmiş Finansallar</h3>
        </div>
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
          <span className="ml-2 text-gray-500 text-sm">Yükleniyor...</span>
        </div>
      </div>
    );
  }

  const hasTTM = ttmData?.has_data;
  const hasUFRS = ufrsData?.has_data;

  if (!hasTTM && !hasUFRS) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">Gelişmiş Finansallar</h3>
        </div>
        <p className="text-gray-500 text-sm py-4">
          Bu hisse için TTM/UFRS finansal verisi bulunamadı.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm p-6">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-purple-600" />
          <h3 className="font-semibold text-gray-900">Gelişmiş Finansallar</h3>
        </div>
      </div>

      {/* Tab Switch */}
      <div className="flex gap-2 mb-4">
        {hasTTM && (
          <button
            onClick={() => setActiveView('ttm')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeView === 'ttm'
                ? 'bg-purple-600 text-white shadow-md'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            �` TTM (Son 12 Ay)
          </button>
        )}
        {hasUFRS && (
          <button
            onClick={() => setActiveView('ufrs')}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
              activeView === 'ufrs'
                ? 'bg-indigo-600 text-white shadow-md'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            🏦 UFRS (Banka)
          </button>
        )}
      </div>

      {/* Content */}
      {activeView === 'ttm' && hasTTM && (
        <div className="space-y-4">
          <p className="text-xs text-gray-500 mb-2">
            Son 12 aylık (TTM) toplam finansal veriler. Çeyreklik raporların toplamıdır.
          </p>
          {renderFinancialTable(
            ttmData.ttm_income_stmt,
            'TTM Gelir Tablosu',
            <TrendingUp className="w-4 h-4 text-green-600" />,
            'ttm_income'
          )}
          {renderFinancialTable(
            ttmData.ttm_balance_sheet,
            'TTM Bilanço',
            <Banknote className="w-4 h-4 text-blue-600" />,
            'ttm_balance'
          )}
          {renderFinancialTable(
            ttmData.ttm_cashflow,
            'TTM Nakit Akış',
            <BarChart3 className="w-4 h-4 text-orange-600" />,
            'ttm_cashflow'
          )}
        </div>
      )}

      {activeView === 'ufrs' && hasUFRS && (
        <div className="space-y-4">
          <div className="bg-indigo-50 border border-indigo-200 rounded-lg p-3 mb-2">
            <p className="text-xs text-indigo-700">
              🏦 UFRS (Uluslararası Finansal Raporlama Standartları) formatında tablolar. 
              Bankacılık sektörü hisseleri için daha detaylı ve doğru finansal veriler sunar.
            </p>
          </div>
          {renderFinancialTable(
            ufrsData.ufrs_income_stmt,
            'UFRS Gelir Tablosu',
            <TrendingUp className="w-4 h-4 text-green-600" />,
            'ufrs_income'
          )}
          {renderFinancialTable(
            ufrsData.ufrs_balance_sheet,
            'UFRS Bilanço',
            <Banknote className="w-4 h-4 text-blue-600" />,
            'ufrs_balance'
          )}
          {renderFinancialTable(
            ufrsData.ufrs_cashflow,
            'UFRS Nakit Akış',
            <BarChart3 className="w-4 h-4 text-orange-600" />,
            'ufrs_cashflow'
          )}
        </div>
      )}
    </div>
  );
}
