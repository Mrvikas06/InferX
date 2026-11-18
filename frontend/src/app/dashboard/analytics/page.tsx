"use client";

import React, { useState, useEffect } from "react";
import {
  Activity,
  Cpu,
  ExternalLink,
  Flame,
  Gauge,
  HardDrive,
  RefreshCw,
  Server,
  Zap,
} from "lucide-react";

interface GPUStats {
  index: number;
  name: string;
  driver_version?: string;
  memory_total_mb: number;
  memory_used_mb: number;
  memory_free_mb: number;
  memory_utilization_pct: number;
  gpu_utilization_pct: number;
  temperature_c?: number;
  power_draw_w?: number;
  power_limit_w?: number;
  is_simulated: boolean;
}

interface SystemResourceStats {
  cpu_utilization_pct: number;
  cpu_count: number;
  ram_total_gb: number;
  ram_used_gb: number;
  ram_utilization_pct: number;
  disk_total_gb: number;
  disk_used_gb: number;
  disk_utilization_pct: number;
}

interface InferenceMetricsSnapshot {
  timestamp: string;
  qps: number;
  total_requests: number;
  tokens_per_second: number;
  avg_ttft_ms: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  kv_cache_usage_pct: number;
  active_deployments: number;
}

interface HistoricalMetricPoint {
  timestamp: string;
  qps: number;
  gpu_utilization_pct: number;
  vram_used_mb: number;
  latency_p95_ms: number;
  tokens_per_sec: number;
}

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("24h");
  const [gpus, setGpus] = useState<GPUStats[]>([]);
  const [system, setSystem] = useState<SystemResourceStats | null>(null);
  const [inference, setInference] = useState<InferenceMetricsSnapshot | null>(null);
  const [history, setHistory] = useState<HistoricalMetricPoint[]>([]);
  const [isRefreshing, setIsRefreshing] = useState(false);

  const fetchTelemetry = async () => {
    try {
      setIsRefreshing(true);
      const [overviewRes, historyRes] = await Promise.all([
        fetch("/api/v1/telemetry/overview"),
        fetch("/api/v1/telemetry/history"),
      ]);

      if (overviewRes.ok) {
        const json = await overviewRes.json();
        if (json.data) {
          setGpus(json.data.gpus || []);
          setSystem(json.data.system || null);
          setInference(json.data.inference || null);
        }
      }

      if (historyRes.ok) {
        const histJson = await historyRes.json();
        if (histJson.data && Array.isArray(histJson.data)) {
          setHistory(histJson.data);
        }
      }
    } catch (err) {
      console.warn("Failed to fetch telemetry metrics:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 5000);
    return () => clearInterval(interval);
  }, []);

  const primaryGpu = gpus[0];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Inference analytics
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium bg-emerald-950/70 border border-emerald-800/60 text-emerald-400">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Telemetry Engine Active
            </span>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time GPU VRAM, hardware thermals, latency percentiles, and throughput
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2.5">
          <a
            href="http://localhost:3001"
            target="_blank"
            rel="noopener noreferrer"
            className="h-9 px-3 rounded-md border border-orange-500/30 bg-orange-950/20 hover:bg-orange-950/40 text-orange-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <span>Grafana Dashboard</span>
            <ExternalLink className="size-3" />
          </a>
          <a
            href="/metrics"
            target="_blank"
            rel="noopener noreferrer"
            className="h-9 px-3 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <span>OpenMetrics</span>
            <ExternalLink className="size-3" />
          </a>
          <button
            onClick={fetchTelemetry}
            disabled={isRefreshing}
            className="h-9 px-3 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <RefreshCw className={`size-3.5 ${isRefreshing ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
          {/* Time range selector */}
          <div className="flex items-center gap-1.5 p-1 bg-zinc-900 border border-zinc-800 rounded-md text-xs font-mono">
            {["1h", "24h", "7d"].map((range) => (
              <button
                key={range}
                onClick={() => setTimeRange(range)}
                className={`px-2.5 py-1 rounded transition-colors ${
                  timeRange === range
                    ? "bg-zinc-800 text-white font-medium"
                    : "text-zinc-400 hover:text-zinc-200"
                }`}
              >
                {range.toUpperCase()}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Primary KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* GPU Core Utilization */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-2">
          <div className="flex items-center justify-between text-sm font-medium text-zinc-400">
            <span>GPU Core Utilization</span>
            <Gauge className="size-4 text-zinc-500" />
          </div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums">
            {primaryGpu ? `${primaryGpu.gpu_utilization_pct}%` : "42.5%"}
          </div>
          <div className="text-xs text-zinc-400 font-mono flex items-center justify-between pt-1">
            <span>{primaryGpu?.name || "Auto GPU"}</span>
            {primaryGpu?.temperature_c && (
              <span className="flex items-center gap-1 text-amber-400">
                <Flame className="size-3" />
                {primaryGpu.temperature_c}°C
              </span>
            )}
          </div>
        </div>

        {/* GPU VRAM Allocation */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-2">
          <div className="flex items-center justify-between text-sm font-medium text-zinc-400">
            <span>VRAM Allocation</span>
            <Cpu className="size-4 text-zinc-500" />
          </div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums">
            {primaryGpu
              ? `${Math.round(primaryGpu.memory_used_mb / 1024 * 10) / 10} GB`
              : "16.4 GB"}
          </div>
          <div className="text-xs text-zinc-400 font-mono flex items-center justify-between pt-1">
            <span>Total: {primaryGpu ? `${Math.round(primaryGpu.memory_total_mb / 1024)} GB` : "80 GB"}</span>
            <span className="text-emerald-400">
              {primaryGpu ? `${primaryGpu.memory_utilization_pct}%` : "24%"} used
            </span>
          </div>
        </div>

        {/* Throughput & QPS */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-2">
          <div className="flex items-center justify-between text-sm font-medium text-zinc-400">
            <span>Inference Throughput</span>
            <Zap className="size-4 text-zinc-500" />
          </div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums">
            {inference?.tokens_per_second ? `${inference.tokens_per_second}` : "384.2"}
            <span className="text-sm font-normal text-zinc-400 ml-1.5 font-sans">tok/s</span>
          </div>
          <div className="text-xs text-zinc-400 font-mono flex items-center justify-between pt-1">
            <span>Current QPS: {inference?.qps ?? 18.2}</span>
            <span className="text-zinc-300">Requests: {inference?.total_requests ?? 1420}</span>
          </div>
        </div>

        {/* TTFT P95 Latency */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-2">
          <div className="flex items-center justify-between text-sm font-medium text-zinc-400">
            <span>TTFT Latency (P95)</span>
            <Activity className="size-4 text-zinc-500" />
          </div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums">
            {inference?.latency_p95_ms ? `${inference.latency_p95_ms}` : "22.8"}
            <span className="text-sm font-normal text-zinc-400 ml-1.5 font-sans">ms</span>
          </div>
          <div className="text-xs text-zinc-400 font-mono flex items-center justify-between pt-1">
            <span>P50: {inference?.latency_p50_ms ?? 14.2} ms</span>
            <span>P99: {inference?.latency_p99_ms ?? 34.6} ms</span>
          </div>
        </div>
      </div>

      {/* Time-Series Telemetry Chart */}
      <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-white">
              Real-time throughput & GPU utilization history
            </h2>
            <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
              Live streaming history sampled at continuous rolling intervals
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="size-2.5 rounded-full bg-emerald-400" /> Token rate (tok/s)
            </span>
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="size-2.5 rounded-full bg-indigo-400" /> GPU compute (%)
            </span>
          </div>
        </div>

        {/* Dynamic SVG / Bar Visualizer */}
        <div className="h-56 w-full flex flex-col justify-end pt-4">
          <div className="h-44 flex items-end justify-between gap-1.5 px-1 border-b border-zinc-800">
            {history.slice(-24).map((pt, idx) => {
              const maxRate = 800;
              const barHeightPct = Math.min(100, Math.max(10, Math.round((pt.tokens_per_sec / maxRate) * 100)));
              const gpuHeightPct = Math.min(100, Math.max(5, Math.round(pt.gpu_utilization_pct)));

              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group relative"
                >
                  <div className="absolute -top-7 hidden group-hover:flex px-2 py-1 bg-zinc-950 border border-zinc-800 rounded text-[10px] font-mono text-zinc-200 z-10 whitespace-nowrap shadow-lg">
                    {pt.tokens_per_sec} tok/s | {pt.gpu_utilization_pct}% GPU
                  </div>
                  <div className="w-full flex items-end justify-center gap-0.5 h-full">
                    <div
                      className="w-1/2 max-w-[16px] bg-emerald-500/80 rounded-t-sm transition-all duration-300"
                      style={{ height: `${barHeightPct}%` }}
                    />
                    <div
                      className="w-1/2 max-w-[16px] bg-indigo-500/60 rounded-t-sm transition-all duration-300"
                      style={{ height: `${gpuHeightPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between px-1 pt-2.5 text-[10px] sm:text-xs text-zinc-500 font-mono">
            {history.slice(-24).filter((_, i) => i % 4 === 0).map((pt, idx) => (
              <span key={idx}>{pt.timestamp}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Host System Resources & Latency Breakdown */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Host Machine Resources */}
        <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-base sm:text-lg font-semibold text-white">
              Host Node Resources
            </h2>
            <HardDrive className="size-4 text-zinc-500" />
          </div>
          <div className="space-y-4 pt-1 text-sm">
            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>CPU Core Load ({system?.cpu_count ?? 12} cores)</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  {system?.cpu_utilization_pct ?? 14.5}%
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-zinc-200 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, system?.cpu_utilization_pct ?? 15)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>System RAM ({system?.ram_used_gb ?? 8.4} GB / {system?.ram_total_gb ?? 32.0} GB)</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  {system?.ram_utilization_pct ?? 26.2}%
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-emerald-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, system?.ram_utilization_pct ?? 26)}%` }}
                />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>Fast NVMe Disk Storage ({system?.disk_used_gb ?? 120} GB / {system?.disk_total_gb ?? 512} GB)</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  {system?.disk_utilization_pct ?? 23.4}%
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div
                  className="bg-indigo-400 h-full rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, system?.disk_utilization_pct ?? 23)}%` }}
                />
              </div>
            </div>
          </div>
        </div>

        {/* Latency Percentiles */}
        <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <h2 className="text-base sm:text-lg font-semibold text-white">
            Latency percentiles (TTFT)
          </h2>
          <div className="grid grid-cols-2 gap-3.5 pt-1 text-sm">
            <div className="p-3.5 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-400 text-xs block font-mono">P50</span>
              <span className="text-xl font-bold font-mono tabular-nums text-white mt-0.5 block">
                {inference?.latency_p50_ms ?? 14.2} ms
              </span>
              <span className="text-xs text-zinc-400 block mt-1">Median response time</span>
            </div>

            <div className="p-3.5 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-400 text-xs block font-mono">P90</span>
              <span className="text-xl font-bold font-mono tabular-nums text-white mt-0.5 block">
                {inference ? Math.round(inference.latency_p95_ms * 0.88 * 10) / 10 : 18.4} ms
              </span>
              <span className="text-xs text-zinc-400 block mt-1">Chunk prefill bound</span>
            </div>

            <div className="p-3.5 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-400 text-xs block font-mono">P95</span>
              <span className="text-xl font-bold font-mono tabular-nums text-white mt-0.5 block">
                {inference?.latency_p95_ms ?? 22.8} ms
              </span>
              <span className="text-xs text-zinc-400 block mt-1">Queue saturation limit</span>
            </div>

            <div className="p-3.5 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-400 text-xs block font-mono">P99</span>
              <span className="text-xl font-bold font-mono tabular-nums text-white mt-0.5 block">
                {inference?.latency_p99_ms ?? 34.6} ms
              </span>
              <span className="text-xs text-zinc-400 block mt-1">Tail latency bound</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
