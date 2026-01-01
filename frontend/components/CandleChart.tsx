// Candlestick Chart Component
'use client';

import { useMemo } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine
} from 'recharts';
import { MarketCandle, Indicator } from '@/types/api';
import { formatDateTime } from '@/utils/api';

interface CandleChartProps {
  candles: MarketCandle[];
  indicators: Indicator[];
}

export default function CandleChart({ candles, indicators }: CandleChartProps) {
  const chartData = useMemo(() => {
    return candles.map(candle => ({
      timestamp: new Date(candle.timestamp).getTime(),
      date: new Date(candle.timestamp).toLocaleDateString(),
      time: new Date(candle.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      open: candle.open,
      high: candle.high,
      low: candle.low,
      close: candle.close,
      volume: candle.volume,
    })).reverse(); // Reverse to show chronological order
  }, [candles]);

  const supportResistanceLevels = useMemo(() => {
    const latestIndicators = indicators
      .filter(ind => ind.indicator_type === 'support_resistance')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
    
    if (!latestIndicators?.value) return { supports: [], resistances: [] };
    
    return {
      supports: latestIndicators.value.supports || [],
      resistances: latestIndicators.value.resistances || []
    };
  }, [indicators]);

  const regressionLine = useMemo(() => {
    const latestIndicators = indicators
      .filter(ind => ind.indicator_type === 'linear_regression')
      .sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime())[0];
    
    if (!latestIndicators?.value?.points) return null;
    
    return latestIndicators.value.points;
  }, [indicators]);

  if (candles.length === 0) {
    return (
      <div className="h-96 flex items-center justify-center text-gray-500">
        <div className="text-center">
          <p className="text-lg font-medium">No chart data available</p>
          <p className="text-sm">Market data will appear here once the bot starts running</p>
        </div>
      </div>
    );
  }

  const priceRange = {
    min: Math.min(...candles.map(c => c.low)),
    max: Math.max(...candles.map(c => c.high))
  };

  return (
    <div className="h-96">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 20 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="time"
            tick={{ fontSize: 12 }}
            interval="preserveStartEnd"
          />
          <YAxis 
            domain={[priceRange.min * 0.99, priceRange.max * 1.01]}
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.toFixed(2)}
          />
          <Tooltip 
            content={({ active, payload, label }) => {
              if (active && payload && payload.length) {
                const data = payload[0].payload;
                return (
                  <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
                    <p className="font-medium">{data.date} {data.time}</p>
                    <div className="grid grid-cols-2 gap-2 text-sm mt-2">
                      <div>Open: ${data.open.toFixed(2)}</div>
                      <div>High: ${data.high.toFixed(2)}</div>
                      <div>Low: ${data.low.toFixed(2)}</div>
                      <div>Close: ${data.close.toFixed(2)}</div>
                      <div className="col-span-2">Volume: {data.volume.toLocaleString()}</div>
                    </div>
                  </div>
                );
              }
              return null;
            }}
          />
          
          {/* Support levels */}
          {supportResistanceLevels.supports.map((support: any, index: number) => (
            <ReferenceLine 
              key={`support-${index}`}
              y={support.price}
              stroke="#10B981"
              strokeDasharray="2 2"
              label={{ value: `S${index + 1}`, position: "insideTopRight" }}
            />
          ))}
          
          {/* Resistance levels */}
          {supportResistanceLevels.resistances.map((resistance: any, index: number) => (
            <ReferenceLine 
              key={`resistance-${index}`}
              y={resistance.price}
              stroke="#EF4444"
              strokeDasharray="2 2"
              label={{ value: `R${index + 1}`, position: "insideBottomRight" }}
            />
          ))}
          
          {/* Close price line */}
          <Line 
            type="monotone" 
            dataKey="close" 
            stroke="#3B82F6" 
            strokeWidth={2}
            dot={false}
            name="Close Price"
          />
          
          {/* Volume on separate axis */}
          <Line 
            type="monotone" 
            dataKey="volume" 
            stroke="#6B7280" 
            strokeWidth={1}
            dot={false}
            name="Volume"
            yAxisId="volume"
          />
          
          {/* Secondary Y-axis for volume */}
          <YAxis 
            yAxisId="volume"
            orientation="right"
            tick={{ fontSize: 12 }}
            tickFormatter={(value) => value.toLocaleString()}
          />
        </LineChart>
      </ResponsiveContainer>
      
      {/* Chart legend */}
      <div className="mt-4 flex flex-wrap gap-4 text-sm">
        <div className="flex items-center gap-2">
          <div className="w-4 h-0.5 bg-blue-600"></div>
          <span>Close Price</span>
        </div>
        {supportResistanceLevels.supports.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-green-500 border-dashed" style={{ borderTop: '2px dashed #10B981' }}></div>
            <span>Support Levels</span>
          </div>
        )}
        {supportResistanceLevels.resistances.length > 0 && (
          <div className="flex items-center gap-2">
            <div className="w-4 h-0.5 bg-red-500 border-dashed" style={{ borderTop: '2px dashed #EF4444' }}></div>
            <span>Resistance Levels</span>
          </div>
        )}
      </div>
    </div>
  );
}