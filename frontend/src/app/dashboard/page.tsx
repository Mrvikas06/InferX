"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Activity,
  ArrowUpRight,
  CheckCircle2,
  Clock,
  Cpu,
  Flame,
  Gauge,
  Layers,
  Play,
  Plus,
  RefreshCw,
  Server,
  Sparkles,
  Zap,
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
  { hour: "00:00", tokens: 2400, rps: 90 },
  { hour: "04:00", tokens: 1800, rps: 68 },
  { hour: "08:00", tokens: 3600, rps: 140 },
  { hour: "12:00", tokens: 5200, rps: 210 },
  { hour: "16:00", tokens: 6100, rps: 245 },
  { hour: "20:00", tokens: 4900, rps: 195 },
  { hour: "Now", tokens: 5420, rps: 220 },
];

export default function DashboardOverviewPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = () => {
    setIsRefreshing(true);
    setTimeout(() => setIsRefreshing(false), 600);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner / Hero */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 pb-2 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            Inference Cluster Overview
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Real-time status, serving metrics, and health telemetry for deployed models.
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={handleRefresh}
            className="p-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-400 hover:text-white hover:bg-zinc-800 transition"
            title="Refresh metrics"
          >
            <RefreshCw
              className={`size-4 ${isRefreshing ? "animate-spin text-cyan-400" : ""}`}
            />
          </button>

          <Link
            href="/dashboard/benchmarks"
            className="px-3 py-2 rounded-lg bg-zinc-900 border border-zinc-800 text-zinc-300 hover:text-white text-xs font-medium flex items-center gap-1.5 transition"
          >
            <Gauge className="size-3.5 text-zinc-400" />
            <span>Benchmark Run</span>
          </Link>

          <Link
            href="/dashboard/deployments"
            className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 transition shadow-sm"
          >
            <Plus className="size-3.5" />
            <span>Deploy Model</span>
          </Link>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Stat 1 */}
        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition relative overflow-hidden group">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium tracking-wide uppercase font-mono">
              Serving Throughput
            </span>
            <div className="p-1.5 rounded-lg bg-cyan-500/10 text-cyan-400">
              <Zap className="size-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">5,420</span>
            <span className="text-xs text-zinc-400 font-mono">tokens/sec</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-emerald-400 mt-2">
            <ArrowUpRight className="size-3" />
            <span>+14.2% peak surge</span>
            <span className="text-zinc-500 ml-auto font-mono">P99: 42 tok/s</span>
          </div>
        </div>

        {/* Stat 2 */}
        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition relative overflow-hidden group">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium tracking-wide uppercase font-mono">
              TTFT (P50 Latency)
            </span>
            <div className="p-1.5 rounded-lg bg-indigo-500/10 text-indigo-400">
              <Clock className="size-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">14.8</span>
            <span className="text-xs text-zinc-400 font-mono">ms</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-emerald-400 mt-2">
            <ArrowUpRight className="size-3" />
            <span>2.4ms faster with SGLang</span>
            <span className="text-zinc-500 ml-auto font-mono">ITL: 7.2ms</span>
          </div>
        </div>

        {/* Stat 3 */}
        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition relative overflow-hidden group">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium tracking-wide uppercase font-mono">
              Active Endpoints
            </span>
            <div className="p-1.5 rounded-lg bg-emerald-500/10 text-emerald-400">
              <Server className="size-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">4 / 4</span>
            <span className="text-xs text-zinc-400 font-mono">healthy</span>
          </div>
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-400 mt-2">
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>8x H100 (80GB) utilized</span>
            <span className="text-zinc-500 ml-auto font-mono">75.3% VRAM</span>
          </div>
        </div>

        {/* Stat 4 */}
        <div className="p-4 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition relative overflow-hidden group">
          <div className="flex items-center justify-between text-zinc-400 mb-2">
            <span className="text-xs font-medium tracking-wide uppercase font-mono">
              KV Cache Hit Rate
            </span>
            <div className="p-1.5 rounded-lg bg-purple-500/10 text-purple-400">
              <Flame className="size-4" />
            </div>
          </div>
          <div className="flex items-baseline gap-2">
            <span className="text-2xl font-bold text-white font-mono">88.4%</span>
            <span className="text-xs text-zinc-400 font-mono">radix attention</span>
          </div>
          <div className="flex items-center gap-1 text-[11px] text-cyan-400 mt-2">
            <Sparkles className="size-3" />
            <span>Prefix caching active</span>
            <span className="text-zinc-500 ml-auto font-mono">Chunked Prefill</span>
          </div>
        </div>
      </div>

      {/* Throughput & Cluster Activity Chart Card */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
            <div>
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Activity className="size-4 text-cyan-400" />
                Aggregated Generation Throughput
              </h2>
              <p className="text-xs text-zinc-400 mt-0.5">
                Output token generation rate (tok/s) across all inference workers
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1 text-xs text-zinc-400 bg-zinc-950 px-2.5 py-1 rounded border border-zinc-800">
                <span className="size-2 rounded-full bg-cyan-400" /> Tok/s
              </span>
              <span className="inline-flex items-center gap-1 text-xs text-zinc-400 bg-zinc-950 px-2.5 py-1 rounded border border-zinc-800">
                <span className="size-2 rounded-full bg-indigo-400" /> RPS
              </span>
            </div>
          </div>

          {/* Custom SVG Bar/Area Chart */}
          <div className="h-56 w-full flex flex-col justify-end pt-4">
            <div className="h-44 flex items-end justify-between gap-2 sm:gap-4 px-2 border-b border-zinc-800">
              {hourlyThroughput.map((item, idx) => {
                const heightPercent = Math.round((item.tokens / 6500) * 100);
                return (
                  <div
                    key={idx}
                    className="flex-1 flex flex-col items-center gap-2 h-full justify-end group"
                  >
                    <div className="text-[10px] text-zinc-400 opacity-0 group-hover:opacity-100 transition font-mono">
                      {item.tokens}
                    </div>
                    <div className="w-full max-w-[48px] bg-zinc-800 group-hover:bg-cyan-500/30 rounded-t-md transition-all relative overflow-hidden flex flex-col justify-end" style={{ height: `${heightPercent}%` }}>
                      <div
                        className="w-full bg-gradient-to-t from-cyan-500 to-indigo-500 rounded-t-md group-hover:from-cyan-400 group-hover:to-indigo-400 transition"
                        style={{ height: "100%" }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
            <div className="flex justify-between px-2 pt-2 text-[11px] text-zinc-500 font-mono">
              {hourlyThroughput.map((item, idx) => (
                <span key={idx}>{item.hour}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Cluster Hardware & VRAM Allocation */}
        <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Cpu className="size-4 text-indigo-400" />
                GPU Memory Pool
              </h2>
              <span className="text-xs font-mono text-zinc-400">80GB H100 x8</span>
            </div>
            <p className="text-xs text-zinc-400 mt-1">
              Real-time VRAM allocation, model weights, and KV Cache reserves.
            </p>
          </div>

          <div className="space-y-3.5 my-2">
            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-300">Model Weights (FP8 / FP16)</span>
                <span className="text-zinc-400 font-mono">248 GB (38.7%)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-cyan-500 h-full rounded-full" style={{ width: "38.7%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-300">KV Cache Block Manager</span>
                <span className="text-zinc-400 font-mono">234 GB (36.5%)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-indigo-500 h-full rounded-full" style={{ width: "36.5%" }} />
              </div>
            </div>

            <div>
              <div className="flex justify-between text-xs mb-1">
                <span className="text-zinc-300">Free / Overhead Buffer</span>
                <span className="text-zinc-400 font-mono">158 GB (24.8%)</span>
              </div>
              <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                <div className="bg-zinc-700 h-full rounded-full" style={{ width: "24.8%" }} />
              </div>
            </div>
          </div>

          <div className="pt-3 border-t border-zinc-800 text-xs text-zinc-400 flex items-center justify-between">
            <span className="flex items-center gap-1.5">
              <CheckCircle2 className="size-3.5 text-emerald-400" />
              PagedAttention Enabled
            </span>
            <Link
              href="/dashboard/analytics"
              className="text-cyan-400 hover:text-cyan-300 text-xs font-medium"
            >
              Detailed Metrics &rarr;
            </Link>
          </div>
        </div>
      </div>

      {/* Active Deployments Table */}
      <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="size-4 text-cyan-400" />
              Active Model Deployments
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Serving engines currently handling production inference requests.
            </p>
          </div>
          <Link
            href="/dashboard/deployments"
            className="text-xs text-cyan-400 hover:text-cyan-300 font-medium self-start sm:self-auto"
          >
            Manage Deployments &rarr;
          </Link>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-mono">
                <th className="pb-3 font-medium">Deployment / Model</th>
                <th className="pb-3 font-medium">Engine</th>
                <th className="pb-3 font-medium">Hardware</th>
                <th className="pb-3 font-medium">Throughput</th>
                <th className="pb-3 font-medium">TTFT</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60">
              {activeDeployments.map((dep) => (
                <tr key={dep.id} className="hover:bg-zinc-800/30 transition">
                  <td className="py-3 pr-4">
                    <div className="font-medium text-white">{dep.name}</div>
                    <div className="text-[11px] text-zinc-400 font-mono truncate max-w-xs">
                      {dep.model}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="px-2 py-0.5 rounded-md bg-zinc-800 text-zinc-300 font-mono border border-zinc-700/60 text-[11px]">
                      {dep.engine}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-300 font-mono text-[11px]">
                    {dep.gpus}
                  </td>
                  <td className="py-3 pr-4 text-zinc-300 font-mono">
                    {dep.qps} rps
                  </td>
                  <td className="py-3 pr-4 text-emerald-400 font-mono">
                    {dep.ttft}
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium ${
                        dep.status === "healthy"
                          ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                          : "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                      }`}
                    >
                      <span
                        className={`size-1.5 rounded-full ${
                          dep.status === "healthy" ? "bg-emerald-400" : "bg-amber-400"
                        }`}
                      />
                      {dep.status}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <Link
                      href="/dashboard/playground"
                      className="inline-flex items-center gap-1 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs transition"
                    >
                      <Play className="size-3 text-cyan-400" />
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
