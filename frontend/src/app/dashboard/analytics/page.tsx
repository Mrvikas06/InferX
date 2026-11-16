"use client";

import React, { useState } from "react";

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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">
            Inference analytics
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Token volume, prompt ratios, latency percentiles, and GPU utilization
          </p>
        </div>

        {/* Time range selector */}
        <div className="flex items-center gap-1 p-0.5 bg-zinc-900 border border-zinc-800 rounded-md text-xs self-start sm:self-auto font-mono">
          {["1h", "24h", "7d", "30d"].map((range) => (
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

      {/* KPI Cards (No decorative icon boxes) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Total tokens</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            142.8M
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1 flex justify-between">
            <span>Prompt: 48.2M</span>
            <span>Completion: 94.6M</span>
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Time to first token (p95)</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            15.4 <span className="text-xs text-zinc-500 font-sans">ms</span>
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1 flex justify-between">
            <span>p50: 12.1 ms</span>
            <span>p99: 28.6 ms</span>
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Cache hit rate</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            89.4%
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1">
            Prefix caching reuse
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Compute efficiency</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            82.6%
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1">
            Model FLOPs utilization
          </div>
        </div>
      </div>

      {/* Token Generation Breakdown Chart */}
      <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h2 className="text-sm font-medium text-white">
              Token volume (thousands)
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Input prompt tokens vs output completion tokens
            </p>
          </div>

          <div className="flex items-center gap-4 text-xs font-mono">
            <span className="flex items-center gap-1.5 text-zinc-400">
              <span className="size-2 rounded-full bg-zinc-300" /> Completion
            </span>
            <span className="flex items-center gap-1.5 text-zinc-400">
              <span className="size-2 rounded-full bg-zinc-600" /> Prompt
            </span>
          </div>
        </div>

        {/* Stacked Monochrome Chart */}
        <div className="h-52 w-full flex flex-col justify-end pt-4">
          <div className="h-40 flex items-end justify-between gap-3 px-1 border-b border-zinc-800">
            {tokenHistory.map((item, idx) => {
              const total = item.promptTokens + item.completionTokens;
              const totalHeight = Math.min(100, Math.round((total / 3600) * 100));
              const promptPct = Math.round((item.promptTokens / total) * 100);
              const compPct = 100 - promptPct;

              return (
                <div
                  key={idx}
                  className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group"
                >
                  <span className="text-[10px] text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity font-mono tabular-nums">
                    {total}k
                  </span>
                  <div
                    className="w-full max-w-[44px] rounded-t-sm overflow-hidden flex flex-col-reverse"
                    style={{ height: `${totalHeight}%` }}
                  >
                    <div
                      className="w-full bg-zinc-600"
                      style={{ height: `${promptPct}%` }}
                    />
                    <div
                      className="w-full bg-zinc-300"
                      style={{ height: `${compPct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
          <div className="flex justify-between px-1 pt-2 text-[11px] text-zinc-500 font-mono">
            {tokenHistory.map((item, idx) => (
              <span key={idx}>{item.time}</span>
            ))}
          </div>
        </div>
      </div>

      {/* Secondary Metrics */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Model Distribution */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <h2 className="text-sm font-medium text-white">
            Model token share
          </h2>
          <div className="space-y-3 pt-1 text-xs">
            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>meta-llama/Llama-3.3-70B-Instruct</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  54.2% (77.4M)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-200 h-full rounded-full" style={{ width: "54.2%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>deepseek-ai/DeepSeek-R1-Distill-Qwen-32B</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  31.8% (45.4M)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-400 h-full rounded-full" style={{ width: "31.8%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>mistralai/Mistral-Small-24B-Instruct-2501</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  14.0% (20.0M)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-600 h-full rounded-full" style={{ width: "14.0%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Latency Percentiles */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <h2 className="text-sm font-medium text-white">
            Latency percentiles (TTFT)
          </h2>
          <div className="grid grid-cols-2 gap-3 pt-1 text-xs">
            <div className="p-3 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-500 text-[11px] block font-mono">p50</span>
              <span className="text-lg font-medium font-mono tabular-nums text-white">
                12.1 ms
              </span>
              <span className="text-[11px] text-zinc-500 block mt-1">median response</span>
            </div>

            <div className="p-3 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-500 text-[11px] block font-mono">p90</span>
              <span className="text-lg font-medium font-mono tabular-nums text-white">
                18.4 ms
              </span>
              <span className="text-[11px] text-zinc-500 block mt-1">chunk prefill bound</span>
            </div>

            <div className="p-3 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-500 text-[11px] block font-mono">p95</span>
              <span className="text-lg font-medium font-mono tabular-nums text-white">
                22.8 ms
              </span>
              <span className="text-[11px] text-zinc-500 block mt-1">queue saturation</span>
            </div>

            <div className="p-3 rounded border border-zinc-800/80 bg-zinc-950/60">
              <span className="text-zinc-500 text-[11px] block font-mono">p99</span>
              <span className="text-lg font-medium font-mono tabular-nums text-white">
                34.2 ms
              </span>
              <span className="text-[11px] text-zinc-500 block mt-1">tail latency bound</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
