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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">
            Cluster overview
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Real-time inference serving metrics and engine status
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={handleRefresh}
            className="p-1.5 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-400 hover:text-white transition-colors"
            title="Refresh metrics"
          >
            <RefreshCw
              className={`size-3.5 ${isRefreshing ? "animate-spin text-zinc-200" : ""}`}
            />
          </button>

          <Link
            href="/dashboard/deployments"
            className="h-8 px-3 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Plus className="size-3.5" />
            <span>Deploy model</span>
          </Link>
        </div>
      </div>

      {/* Unslopped Stat Cards (Numbers First, Quiet Labels, No Decorative Icon Boxes) */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Serving throughput</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            5,420 <span className="text-xs text-zinc-500 font-sans">tok/s</span>
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1 flex items-center gap-1">
            <span className="text-emerald-400">+14.2%</span>
            <span>vs 24h ago</span>
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Time to first token (p50)</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            14.8 <span className="text-xs text-zinc-500 font-sans">ms</span>
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1">
            p99: 34.2 ms • itl: 6.8 ms
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">Active deployments</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            4 <span className="text-xs text-zinc-500 font-sans">instances</span>
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1 flex items-center gap-1.5">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            <span>8x H100 SXM5 allocated</span>
          </div>
        </div>

        <div className="p-4 rounded-lg border border-zinc-800/80 bg-zinc-900/40">
          <div className="text-xs text-zinc-400">KV cache hit rate</div>
          <div className="text-2xl font-medium text-white font-mono tabular-nums mt-1.5">
            88.4%
          </div>
          <div className="text-[11px] text-zinc-500 font-mono mt-1">
            RadixAttention reuse
          </div>
        </div>
      </div>

      {/* Main Throughput Chart & GPU Memory Pool */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-sm font-medium text-white">
                Generation throughput
              </h2>
              <p className="text-xs text-zinc-500 mt-0.5">
                Output token generation rate (tok/s) across active engines
              </p>
            </div>
            <span className="text-xs text-zinc-400 font-mono">
              Peak: 6,100 tok/s
            </span>
          </div>

          {/* Clean Solid Monochromatic Chart */}
          <div className="h-48 flex flex-col justify-end pt-4">
            <div className="h-36 flex items-end justify-between gap-3 px-1 border-b border-zinc-800">
              {hourlyThroughput.map((item, idx) => {
                const heightPercent = Math.round((item.tokens / 6500) * 100);
                return (
                  <div
                    key={idx}
                    className="flex-1 flex flex-col items-center gap-1.5 h-full justify-end group"
                  >
                    <span className="text-[10px] text-zinc-500 opacity-0 group-hover:opacity-100 transition-opacity font-mono tabular-nums">
                      {item.tokens}
                    </span>
                    <div
                      className="w-full max-w-[40px] bg-zinc-700 hover:bg-zinc-500 rounded-t-sm transition-colors"
                      style={{ height: `${heightPercent}%` }}
                    />
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between px-1 pt-2 text-[11px] text-zinc-500 font-mono">
              {hourlyThroughput.map((item, idx) => (
                <span key={idx}>{item.hour}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Memory Pool Breakdown */}
        <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-medium text-white">GPU memory pool</h2>
              <span className="text-xs font-mono text-zinc-500">640 GB total</span>
            </div>
            <p className="text-xs text-zinc-500 mt-0.5">
              Weights allocation, KV block manager, and free buffer
            </p>
          </div>

          <div className="space-y-3 text-xs">
            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>Model weights</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  248 GB (38.7%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-200 h-full rounded-full" style={{ width: "38.7%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>KV cache block manager</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  234 GB (36.5%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-400 h-full rounded-full" style={{ width: "36.5%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>Free overhead buffer</span>
                <span className="font-mono tabular-nums text-zinc-300">
                  158 GB (24.8%)
                </span>
              </div>
              <div className="w-full bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                <div className="bg-zinc-700 h-full rounded-full" style={{ width: "24.8%" }} />
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-zinc-800 text-xs flex items-center justify-between text-zinc-400">
            <span>PagedAttention active</span>
            <Link
              href="/dashboard/analytics"
              className="text-zinc-200 hover:text-white flex items-center gap-1 font-medium"
            >
              <span>Detailed view</span>
              <ChevronRight className="size-3" />
            </Link>
          </div>
        </div>
      </div>

      {/* Active Deployments Table */}
      <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-sm font-medium text-white">
              Active serving deployments
            </h2>
            <p className="text-xs text-zinc-500 mt-0.5">
              Engines currently responding to production completions
            </p>
          </div>
          <Link
            href="/dashboard/deployments"
            className="text-xs text-zinc-300 hover:text-white font-medium"
          >
            Manage all &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500 font-mono">
                <th className="pb-2.5 font-normal">Deployment</th>
                <th className="pb-2.5 font-normal">Engine</th>
                <th className="pb-2.5 font-normal">Hardware</th>
                <th className="pb-2.5 font-normal">Throughput</th>
                <th className="pb-2.5 font-normal">TTFT</th>
                <th className="pb-2.5 font-normal">Status</th>
                <th className="pb-2.5 font-normal text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {activeDeployments.map((dep) => (
                <tr key={dep.id} className="hover:bg-zinc-800/20 transition-colors">
                  <td className="py-2.5 pr-4 font-sans">
                    <div className="font-medium text-white">{dep.name}</div>
                    <div className="text-[11px] text-zinc-500 font-mono truncate max-w-xs">
                      {dep.model}
                    </div>
                  </td>
                  <td className="py-2.5 pr-4">
                    <span className="px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 text-[11px]">
                      {dep.engine}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-400 text-[11px]">
                    {dep.gpus}
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-300 tabular-nums">
                    {dep.qps} rps
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-200 tabular-nums">
                    {dep.ttft}
                  </td>
                  <td className="py-2.5 pr-4 font-sans">
                    <span className="inline-flex items-center gap-1.5 text-[11px]">
                      <span
                        className={`size-1.5 rounded-full ${
                          dep.status === "healthy" ? "bg-emerald-500" : "bg-amber-500"
                        }`}
                      />
                      <span className="text-zinc-400">{dep.status}</span>
                    </span>
                  </td>
                  <td className="py-2.5 text-right font-sans">
                    <Link
                      href="/dashboard/playground"
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-xs transition-colors"
                    >
                      <Play className="size-3 text-zinc-400" />
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
