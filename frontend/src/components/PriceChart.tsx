"use client";

import {
  CandlestickSeries,
  createChart,
  HistogramSeries,
  type IChartApi,
  LineStyle,
} from "lightweight-charts";
import { useEffect, useRef } from "react";
import type { OhlcvBar, Signal } from "@/lib/api";

interface Props {
  ohlcv: OhlcvBar[];
  signals?: Signal[];
  height?: number;
}

export function PriceChart({ ohlcv, signals = [], height = 400 }: Props) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const chartRef = useRef<IChartApi | null>(null);

  useEffect(() => {
    const el = containerRef.current;
    if (!el || ohlcv.length === 0) return;

    const chart = createChart(el, {
      width: el.clientWidth,
      height,
      layout: {
        background: { color: "#09090b" }, // zinc-950
        textColor: "#a1a1aa", // zinc-400
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.04)" },
        horzLines: { color: "rgba(255,255,255,0.04)" },
      },
      rightPriceScale: { borderColor: "rgba(255,255,255,0.1)" },
      timeScale: {
        borderColor: "rgba(255,255,255,0.1)",
        timeVisible: false,
      },
      crosshair: { mode: 1 },
    });
    chartRef.current = chart;

    const candles = chart.addSeries(CandlestickSeries, {
      upColor: "#10b981",
      downColor: "#f43f5e",
      borderUpColor: "#10b981",
      borderDownColor: "#f43f5e",
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
    });
    candles.setData(
      ohlcv.map((b) => ({
        time: b.date,
        open: b.open,
        high: b.high,
        low: b.low,
        close: b.close,
      })),
    );

    const volume = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "vol",
      color: "rgba(148, 163, 184, 0.4)",
    });
    chart.priceScale("vol").applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });
    volume.setData(
      ohlcv.map((b) => ({
        time: b.date,
        value: b.volume,
        color: b.close >= b.open ? "rgba(16, 185, 129, 0.45)" : "rgba(244, 63, 94, 0.45)",
      })),
    );

    // Entry / target / stop horizontal price lines for active signals.
    for (const s of signals) {
      candles.createPriceLine({
        price: s.entry,
        color: "#e5e7eb",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: `${s.strategy} entry`,
      });
      candles.createPriceLine({
        price: s.target,
        color: "#10b981",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: "target",
      });
      candles.createPriceLine({
        price: s.stop,
        color: "#f43f5e",
        lineWidth: 1,
        lineStyle: LineStyle.Dashed,
        axisLabelVisible: true,
        title: "stop",
      });
    }

    chart.timeScale().fitContent();

    const ro = new ResizeObserver(() => {
      if (chartRef.current && el) {
        chartRef.current.applyOptions({ width: el.clientWidth });
      }
    });
    ro.observe(el);

    return () => {
      ro.disconnect();
      chart.remove();
      chartRef.current = null;
    };
  }, [ohlcv, signals, height]);

  return <div ref={containerRef} style={{ width: "100%", height }} />;
}
