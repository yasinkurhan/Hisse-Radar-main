'use client';

import React from 'react';
import type { SectorPerformance } from '@/types';

interface SectorRotationProps {
  sectors: SectorPerformance[];
}

export default function SectorRotation({ sectors }: SectorRotationProps) {
  const getPhaseColor = (phase: string) => {
    switch (phase) {
      case 'leading': return 'bg-up/10 border-up/20 text-up';
      case 'weakening': return 'bg-yellow-500/10 border-yellow-500/20 text-yellow-400';
      case 'lagging': return 'bg-down/10 border-down/20 text-down';
      case 'improving': return 'bg-blue-500/10 border-blue-500/20 text-blue-400';
      default: return 'bg-card text-muted';
    }
  };

  const getPhaseIcon = (phase: string) => {
    switch (phase) {
      case 'leading': return '🚀';
      case 'weakening': return '📉';
      case 'lagging': return '🐢';
      case 'improving': return '📈';
      default: return '❓';
    }
  };

  const sortedSectors = [...sectors].sort((a, b) => b.relative_strength - a.relative_strength);

  // Group by phase
  const groupedSectors = {
    leading: sectors.filter(s => s.rotation_phase === 'leading'),
    improving: sectors.filter(s => s.rotation_phase === 'improving'),
    weakening: sectors.filter(s => s.rotation_phase === 'weakening'),
    lagging: sectors.filter(s => s.rotation_phase === 'lagging'),
  };

  return (
    <div className="bg-surface rounded-lg p-6">
      <h3 className="text-xl font-semibold mb-4 flex items-center gap-2">
        <span>🔄</span> Sektör Rotasyonu
      </h3>

      {/* Phase Summary */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {Object.entries(groupedSectors).map(([phase, sectorList]) => (
          <div 
            key={phase}
            className={`p-3 rounded-lg border ${getPhaseColor(phase)}`}
          >
            <div className="flex items-center gap-2 mb-1">
              <span>{getPhaseIcon(phase)}</span>
              <span className="font-medium capitalize">
                {phase === 'leading' ? 'Lider' :
                 phase === 'improving' ? 'Yükselen' :
                 phase === 'weakening' ? 'Zayıflayan' : 'Geride'}
              </span>
            </div>
            <div className="text-2xl font-bold">{sectorList.length}</div>
            <div className="text-xs opacity-75">sektör</div>
          </div>
        ))}
      </div>

      {/* Rotation Matrix */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-muted mb-3">Rotasyon Matrisi</h4>
        <div className="relative h-64 bg-card rounded-lg p-4">
          {/* Axes */}
          <div className="absolute left-1/2 top-0 bottom-0 w-px bg-border" />
          <div className="absolute top-1/2 left-0 right-0 h-px bg-border" />
          
          {/* Quadrant Labels */}
          <div className="absolute top-2 right-2 text-xs text-up">Lider</div>
          <div className="absolute top-2 left-2 text-xs text-blue-400">Yükselen</div>
          <div className="absolute bottom-2 left-2 text-xs text-down">Geride</div>
          <div className="absolute bottom-2 right-2 text-xs text-yellow-400">Zayıflayan</div>
          
          {/* Axis Labels */}
          <div className="absolute -bottom-6 left-1/2 transform -translate-x-1/2 text-xs text-muted">
            Göreli Güç →
          </div>
          <div className="absolute top-1/2 -left-6 transform -rotate-90 -translate-y-1/2 text-xs text-muted">
            Momentum →
          </div>
          
          {/* Sector Points */}
          {sectors.slice(0, 10).map((sector, idx) => {
            // Calculate position based on relative strength and performance
            const rs = sector.relative_strength ?? 0;
            const perf = sector.performance_1w ?? 0;
            const x = 50 + (rs * 40); // -1 to 1 => 10% to 90%
            const y = 50 - (perf * 2); // Inverted because CSS y is top-down
            
            return (
              <div
                key={sector.sector}
                className={`absolute w-3 h-3 rounded-full cursor-pointer transition-transform hover:scale-150 ${
                  sector.rotation_phase === 'leading' ? 'bg-up' :
                  sector.rotation_phase === 'improving' ? 'bg-blue-400' :
                  sector.rotation_phase === 'weakening' ? 'bg-yellow-400' : 'bg-down'
                }`}
                style={{ 
                  left: `${Math.min(95, Math.max(5, x))}%`, 
                  top: `${Math.min(95, Math.max(5, y))}%`,
                  transform: 'translate(-50%, -50%)'
                }}
                title={`${sector.sector}: RS ${rs.toFixed(2)}, 1H ${perf.toFixed(1)}%`}
              />
            );
          })}
        </div>
      </div>

      {/* Sector Performance Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-muted border-b border-border">
              <th className="pb-2 pr-4">Sektör</th>
              <th className="pb-2 pr-4 text-right">1 Gün</th>
              <th className="pb-2 pr-4 text-right">1 Hafta</th>
              <th className="pb-2 pr-4 text-right">1 Ay</th>
              <th className="pb-2 pr-4 text-right">RS</th>
              <th className="pb-2">Faz</th>
            </tr>
          </thead>
          <tbody>
            {sortedSectors.map((sector) => (
              <tr key={sector.sector} className="border-b border-border/50 hover:bg-card/50">
                <td className="py-2 pr-4 font-medium">{sector.sector}</td>
                <td className={`py-2 pr-4 text-right ${
                  sector.performance_1d > 0 ? 'text-up' : 
                  sector.performance_1d < 0 ? 'text-down' : 'text-muted'
                }`}>
                  {sector.performance_1d > 0 ? '+' : ''}{sector.performance_1d.toFixed(2)}%
                </td>
                <td className={`py-2 pr-4 text-right ${
                  sector.performance_1w > 0 ? 'text-up' : 
                  sector.performance_1w < 0 ? 'text-down' : 'text-muted'
                }`}>
                  {sector.performance_1w > 0 ? '+' : ''}{sector.performance_1w.toFixed(2)}%
                </td>
                <td className={`py-2 pr-4 text-right ${
                  sector.performance_1m > 0 ? 'text-up' : 
                  sector.performance_1m < 0 ? 'text-down' : 'text-muted'
                }`}>
                  {sector.performance_1m > 0 ? '+' : ''}{sector.performance_1m.toFixed(2)}%
                </td>
                <td className={`py-2 pr-4 text-right font-mono ${
                  sector.relative_strength > 0 ? 'text-up' : 
                  sector.relative_strength < 0 ? 'text-down' : 'text-muted'
                }`}>
                  {sector.relative_strength.toFixed(2)}
                </td>
                <td className="py-2">
                  <span className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs ${getPhaseColor(sector.rotation_phase)}`}>
                    {getPhaseIcon(sector.rotation_phase)}
                    {sector.phase_tr}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Legend */}
      <div className="mt-6 p-4 bg-card rounded-lg">
        <h4 className="font-semibold mb-3">📖 Sektör Rotasyonu Rehberi</h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-sm">
          <div className="flex items-start gap-2">
            <span className="text-up">🚀</span>
            <div>
              <strong className="text-up">Lider:</strong>
              <span className="text-muted"> Güçlü performans, pozitif momentum</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-yellow-400">📉</span>
            <div>
              <strong className="text-yellow-400">Zayıflayan:</strong>
              <span className="text-muted"> Güçlü ama momentum düşüyor</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-down">🐢</span>
            <div>
              <strong className="text-down">Geride:</strong>
              <span className="text-muted"> Zayıf performans, negatif momentum</span>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-blue-400">📈</span>
            <div>
              <strong className="text-blue-400">Yükselen:</strong>
              <span className="text-muted"> Zayıf ama momentum artıyor</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
