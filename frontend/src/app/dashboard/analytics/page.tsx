"use client";

import React, { useState } from "react";
import {
  BarChart3,
  Cpu,
  Flame,
  PieChart,
  Sparkles,
  TrendingUp,
  Zap,
} from "lucide-react";

const tokenHistory = [
  { time: "00:00", promptTokens: 320, completionTokens: 680 },
  { time: "04:00", promptTokens: 210, completionTokens: 490 },
  { time: "08:00", promptTokens: 640, completionTokens: 1420 },
  { time: "12:00", promptTokens: 980, completionTokens: 2100 },
  { time: "16:00", promptTokens: 1120, completionTokens: 2450 },
  { time: "20:00", promptTokens: 890, completionTokens: 1850 },
  { time: "Now", promptTokens: 940, completionTokens: 1980 },
];

export default function AnalyticsPage() {
  const [timeRange, setTimeRange] = useState("24h");

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            Inference Telemetry & Analytics
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Token consumption volume, prompt/completion ratios, latency percentiles, and GPU utilization.
          </p>
        </div>

        {/* Time range selector */}
        <div className="flex items-center gap-1.5 p-1 bg-zinc-900 border border-zinc-800 rounded-lg text-xs self-start sm:self-auto">
          {["1h", "24h", "7d", "30d"].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded-md transition font-mono ${
                timeRange === range
                  ? "bg-cyan-600 text-white font-medium"
                  : "text-zinc-400 hover:text-zinc-200"
              }`}
            >
              {range.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-1">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase">Total Tokens</span>
            <Sparkles className="size-4 text-cyan-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">142.8M</div>
          <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-1">
            <span>Prompt: 48.2M</span>
            <span>Completion: 94.6M</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-1">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase">Avg P95 TTFT</span>
            <Zap className="size-4 text-emerald-400" />
          </div>
          <div className="text-2xl font-bold text-emerald-400 font-mono">15.4 ms</div>
          <div className="flex items-center justify-between text-[11px] text-zinc-400 pt-1">
            <span>P50: 12.1ms</span>
            <span>P99: 28.6ms</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-1">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase">Cache Hit Rate</span>
            <Flame className="size-4 text-purple-400" />
          </div>
          <div className="text-2xl font-bold text-white font-mono">89.4%</div>
          <div className="text-[11px] text-zinc-400 pt-1">
            <span>Prefix Caching / Radix Tree Reuse</span>
          </div>
        </div>

        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-1">
          <div className="flex items-center justify-between text-zinc-400">
            <span className="text-xs font-mono uppercase">Compute MFU</span>
            <Cpu className="size-4 text-indigo-400" />
          </div>
          <div className="text-2xl font-bold text-indigo-400 font-mono">82.6%</div>
          <div className="text-[11px] text-zinc-400 pt-1">
            <span>Model FLOPs Utilization</span>
          </div>
        </div>
      </div>

      {/* Main Visual: Token Consumption Over Time */}
      <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <TrendingUp className="size-4 text-cyan-400" />
              Token Generation Breakdown (Tokens in Thousands)
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Input context prompt tokens vs generated completion tokens over the selected window.
            </p>
          </div>

          <div className="flex items-center gap-3 text-xs">
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="size-2 rounded-full bg-cyan-500" /> Completion Tokens
            </span>
            <span className="flex items-center gap-1.5 text-zinc-300">
              <span className="size-2 rounded-full bg-indigo-500" /> Prompt Tokens
            </span>
          </div>
        </div>

        {/* Stacked Chart Visualization */}
        <div className="h-60 w-full flex flex-col justify-end pt-6">
          <div className="h-48 flex items-end justify-between gap-3 px-2 border-b border-zinc-800">
            {tokenHistory.map((item, idx) => {
              const total = item.promptTokens + item.completionTokens;
              const totalHeight = Math.min(100, Math.round((total / 3600) * 100));
              const promptPct = Math.round((item.promptTokens / total) * 100);
              const compPct = 100 - promptPct;

              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-2 h-full justify-end group"
                >
                  <div className="text-[10px] text-zinc-400 opacity-0 group-hover:opacity-100 transition font-mono">
                    {total}k
                  </div>
                  <div
                    className="w-full max-w-[54px] rounded-t-md overflow-hidden flex flex-col-reverse group-hover:opacity-90 transition"
                    style={{ height: `${totalHeight}%` }}
                  >
                    <div
                      className="w-full bg-indigo-600 transition"
                      style={{ height: `${promptPct}%` }}
                      title={`Prompt: ${item.promptTokens}k`}
                    />
                    <div
                      className="w-full bg-cyan-500 transition"
                      style={{ height: `${compPct}%` }}
                      title={`Completion: ${item.completionTokens}k`}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between px-2 pt-2 text-[11px] text-zinc-500 font-mono">
            {tokenHistory.map((item, idx) => (
              <span key={idx}>{item.time}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Secondary Metrics: Model Distribution & Latency Percentiles */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Distribution */}
        <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <PieChart className="size-4 text-cyan-400" />
            Model Serving Share & Cost
          </h2>
          <div className="space-y-3 pt-2 text-xs">
            <div>
              <div className="flex justify-between text-zinc-300 mb-1">
                <span>meta-llama/Llama-3.3-70B-Instruct</span>
                <span className="font-mono text-zinc-400">54.2% (77.4M tok)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full rounded-full" style={{ width: "54.2%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1">
                <span>deepseek-ai/DeepSeek-R1-Distill-Qwen-32B</span>
                <span className="font-mono text-zinc-400">31.8% (45.4M tok)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-indigo-500 h-full rounded-full" style={{ width: "31.8%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1">
                <span>mistralai/Mistral-Small-24B-Instruct-2501</span>
                <span className="font-mono text-zinc-400">14.0% (20.0M tok)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-purple-500 h-full rounded-full" style={{ width: "14.0%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Latency Percentiles Breakdown */}
        <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <BarChart3 className="size-4 text-emerald-400" />
            Inference Latency Percentiles (TTFT)
          </h2>
          <div className="grid grid-cols-2 gap-3 pt-2 text-xs">
            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <span className="text-zinc-500 text-[11px] block">P50 (Median)</span>
              <span className="text-xl font-bold font-mono text-white">12.1 ms</span>
              <span className="text-[10px] text-emerald-400 block mt-1">Excellent responsiveness</span>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <span className="text-zinc-500 text-[11px] block">P90</span>
              <span className="text-xl font-bold font-mono text-white">18.4 ms</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Stable chunk prefill</span>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <span className="text-zinc-500 text-[11px] block">P95</span>
              <span className="text-xl font-bold font-mono text-white">22.8 ms</span>
              <span className="text-[10px] text-zinc-400 block mt-1">Under high queue depth</span>
            </div>

            <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800">
              <span className="text-zinc-500 text-[11px] block">P99</span>
              <span className="text-xl font-bold font-mono text-white">34.2 ms</span>
              <span className="text-[10px] text-amber-400 block mt-1">Tail latency bound</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
