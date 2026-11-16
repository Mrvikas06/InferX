"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  ChevronRight,
  Play,
  Plus,
  RefreshCw,
} from "lucide-react";

interface DeploymentItem {
  id: string;
  name: string;
  model: string;
  engine: "vLLM" | "SGLang" | "TensorRT-LLM";
  status: "healthy" | "scaling" | "degraded";
  gpus: string;
  qps: number;
  ttft: string;
  uptime: string;
}

const activeDeployments: DeploymentItem[] = [
  {
    id: "dep-1",
    name: "llama-3-3-70b-prod",
    model: "meta-llama/Llama-3.3-70B-Instruct",
    engine: "vLLM",
    status: "healthy",
    gpus: "4x H100 (TP=4)",
    qps: 184.2,
    ttft: "16.4 ms",
    uptime: "99.98%",
  },
  {
    id: "dep-2",
    name: "deepseek-r1-qwen-32b",
    model: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    engine: "SGLang",
    status: "healthy",
    gpus: "2x H100 (TP=2)",
    qps: 92.6,
    ttft: "12.8 ms",
    uptime: "100.0%",
  },
  {
    id: "dep-3",
    name: "mistral-small-24b",
    model: "mistralai/Mistral-Small-24B-Instruct-2501",
    engine: "vLLM",
    status: "healthy",
    gpus: "1x H100 (TP=1)",
    qps: 64.1,
    ttft: "9.2 ms",
    uptime: "99.94%",
  },
  {
    id: "dep-4",
    name: "qwen-2-5-coder-32b",
    model: "Qwen/Qwen2.5-Coder-32B-Instruct",
    engine: "TensorRT-LLM",
    status: "scaling",
    gpus: "1x H100 (TP=1)",
    qps: 38.0,
    ttft: "11.1 ms",
    uptime: "99.85%",
  },
];

const hourlyThroughput = [
  { hour: "00:00", tokens: 2400 },
  { hour: "04:00", tokens: 1800 },
  { hour: "08:00", tokens: 3600 },
  { hour: "12:00", tokens: 5200 },
  { hour: "16:00", tokens: 6100 },
  { hour: "20:00", tokens: 4900 },
  { hour: "Now", tokens: 5420 },
];

export default function DashboardOverviewPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 400);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Cluster overview
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Real-time inference serving metrics, memory allocation, and engine status
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRefresh}
            className="p-2 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw
              className={`size-4 ${isRefreshing ? "animate-spin text-zinc-200" : ""}`}
            />
          </button>

          <Link
            href="/dashboard/deployments"
            className="h-9 px-4 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Plus className="size-4" />
            <span>Deploy model</span>
          </Link>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-sm font-medium text-zinc-400">Serving throughput</div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums mt-2">
            5,420 <span className="text-sm font-normal text-zinc-400 font-sans">tok/s</span>
          </div>
          <div className="text-xs text-zinc-400 font-mono mt-2 flex items-center gap-1.5">
            <span className="text-emerald-400 font-medium">+14.2%</span>
            <span>vs 24h ago</span>
          </div>
        </div>

        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-sm font-medium text-zinc-400">Time to first token (P50)</div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums mt-2">
            14.8 <span className="text-sm font-normal text-zinc-400 font-sans">ms</span>
          </div>
          <div className="text-xs text-zinc-400 font-mono mt-2">
            P99: 34.2 ms • ITL: 6.8 ms
          </div>
        </div>

        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-sm font-medium text-zinc-400">Active deployments</div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums mt-2">
            4 <span className="text-sm font-normal text-zinc-400 font-sans">instances</span>
          </div>
          <div className="text-xs text-zinc-400 font-mono mt-2 flex items-center gap-2">
            <span className="size-2 rounded-full bg-emerald-500" />
            <span>8x H100 SXM5 allocated</span>
          </div>
        </div>

        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-sm font-medium text-zinc-400">KV cache hit rate</div>
          <div className="text-3xl font-bold text-white font-mono tabular-nums mt-2">
            88.4%
          </div>
          <div className="text-xs text-zinc-400 font-mono mt-2">
            RadixAttention reuse active
          </div>
        </div>
      </div>

      {/* Main Throughput Chart & GPU Memory Pool */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-base sm:text-lg font-semibold text-white">
                Generation throughput
              </h2>
              <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
                Output token generation rate (tokens per second) across active engines
              </p>
            </div>
            <span className="text-xs sm:text-sm text-zinc-400 font-mono">
              Peak: 6,100 tok/s
            </span>
          </div>

          {/* Clean Solid Monochromatic Chart */}
          <div className="h-52 flex flex-col justify-end pt-4">
            <div className="h-40 flex items-end justify-between gap-3 px-1 border-b border-zinc-800">
              {hourlyThroughput.map((item, idx) => {
                const heightPercent = Math.round((item.tokens / 6500) * 100);
                return (
                  <div
                    key={idx}
                    className="flex-1 flex flex-col items-center gap-2 h-full justify-end group"
                  >
                    <span className="text-xs text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity font-mono tabular-nums">
                      {item.tokens}
                    </span>
                    <div
                      className="w-full max-w-[44px] bg-zinc-700 hover:bg-zinc-500 rounded-t-sm transition-colors"
                      style={{ height: `${heightPercent}%` }}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between px-1 pt-2.5 text-xs text-zinc-400 font-mono">
              {hourlyThroughput.map((item, idx) => (
                <span key={idx}>{item.hour}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Memory Pool Breakdown */}
        <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base sm:text-lg font-semibold text-white">GPU memory pool</h2>
              <span className="text-xs sm:text-sm font-mono text-zinc-400">640 GB total</span>
            </div>
            <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
              Weights allocation, KV block manager, and free buffer
            </p>
          </div>

          <div className="space-y-4 text-sm">
            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>Model weights</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  248 GB (38.7%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-zinc-200 h-full rounded-full" style={{ width: "38.7%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>KV cache block manager</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  234 GB (36.5%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-zinc-400 h-full rounded-full" style={{ width: "36.5%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-300 mb-1.5">
                <span>Free overhead buffer</span>
                <span className="font-mono tabular-nums text-zinc-200">
                  158 GB (24.8%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-zinc-700 h-full rounded-full" style={{ width: "24.8%" }} />
              </div>
            </div>
          </div>

          <div className="pt-3.5 border-t border-zinc-800 text-sm flex items-center justify-between text-zinc-400">
            <span>PagedAttention active</span>
            <Link
              href="/dashboard/analytics"
              className="text-zinc-200 hover:text-white flex items-center gap-1 font-medium"
            >
              <span>Detailed view</span>
              <ChevronRight className="size-3.5" />
            </Link>
          </div>
        </div>
      </div>

      {/* Active Deployments Table */}
      <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-semibold text-white">
              Active serving deployments
            </h2>
            <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
              Engines currently responding to production completions
            </p>
          </div>
          <Link
            href="/dashboard/deployments"
            className="text-sm text-zinc-300 hover:text-white font-medium"
          >
            Manage all &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-xs uppercase tracking-wider">
                <th className="pb-3 font-medium">Deployment</th>
                <th className="pb-3 font-medium">Engine</th>
                <th className="pb-3 font-medium">Hardware</th>
                <th className="pb-3 font-medium">Throughput</th>
                <th className="pb-3 font-medium">TTFT</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {activeDeployments.map((dep) => (
                <tr key={dep.id} className="hover:bg-zinc-800/20 transition-colors">
                  <td className="py-3 pr-4 font-sans">
                    <div className="font-medium text-white text-sm">{dep.name}</div>
                    <div className="text-xs text-zinc-400 font-mono truncate max-w-xs mt-0.5">
                      {dep.model}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 text-xs">
                      {dep.engine}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-400 text-xs">
                    {dep.gpus}
                  </td>
                  <td className="py-3 pr-4 text-zinc-200 tabular-nums">
                    {dep.qps} rps
                  </td>
                  <td className="py-3 pr-4 text-zinc-200 tabular-nums">
                    {dep.ttft}
                  </td>
                  <td className="py-3 pr-4 font-sans">
                    <span className="inline-flex items-center gap-2 text-xs">
                      <span
                        className={`size-2 rounded-full ${
                          dep.status === "healthy" ? "bg-emerald-500" : "bg-amber-500"
                        }`}
                      />
                      <span className="text-zinc-300">{dep.status}</span>
                    </span>
                  </td>
                  <td className="py-3 text-right font-sans">
                    <Link
                      href="/dashboard/playground"
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-xs font-medium transition-colors"
                    >
                      <Play className="size-3.5 text-zinc-400" />
                      <span>Test</span>
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
