"use client";

import React, { useState, useEffect } from "react";
import {
  AlertCircle,
  BarChart3,
  CheckCircle2,
  Clock,
  Gauge,
  Play,
  RefreshCw,
  Trash2,
  X,
  Zap,
} from "lucide-react";

interface DeploymentItem {
  id: string;
  name: string;
  model?: { repo_id: string; name: string };
  engine: string;
  status: string;
}

interface BenchmarkItem {
  id: string;
  name: string;
  deployment_id: string;
  model_id?: string;
  model_name?: string;
  deployment_name?: string;
  status: string;
  engine: string;
  concurrency: number;
  num_prompts: number;
  input_tokens: number;
  output_tokens: number;
  rps: number;
  tokens_per_sec: number;
  p50_latency_ms: number;
  p95_latency_ms: number;
  p99_latency_ms: number;
  p50_ttft_ms: number;
  p99_ttft_ms: number;
  mean_tpot_ms: number;
  vram_peak_gb: number;
  error_count: number;
  results_json: any;
  created_at: string;
}

export default function BenchmarksPage() {
  const [deployments, setDeployments] = useState<DeploymentItem[]>([]);
  const [benchmarks, setBenchmarks] = useState<BenchmarkItem[]>([]);
  const [selectedDeploymentId, setSelectedDeploymentId] = useState<string>("");
  const [name, setName] = useState<string>("");
  const [concurrency, setConcurrency] = useState<number>(16);
  const [numPrompts, setNumPrompts] = useState<number>(32);
  const [inputLen, setInputLen] = useState<number>(256);
  const [outputLen, setOutputLen] = useState<number>(128);
  const [isRunning, setIsRunning] = useState<boolean>(false);
  const [activeBenchmarkId, setActiveBenchmarkId] = useState<string | null>(null);
  const [selectedBenchmark, setSelectedBenchmark] = useState<BenchmarkItem | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  // Fetch deployments and benchmark history
  const loadData = async () => {
    try {
      setIsLoading(true);
      const [depsRes, bmsRes] = await Promise.all([
        fetch("/api/v1/deployments"),
        fetch("/api/v1/benchmarks?limit=50"),
      ]);

      if (depsRes.ok) {
        const json = await depsRes.json();
        const items: DeploymentItem[] = json.data?.items || json.data || [];
        setDeployments(items);
        if (items.length > 0 && !selectedDeploymentId) {
          const running = items.find((d) => d.status === "running") || items[0];
          setSelectedDeploymentId(running.id);
          setName(`${running.name} Concurrency Sweep`);
        }
      }

      if (bmsRes.ok) {
        const json = await bmsRes.json();
        const items: BenchmarkItem[] = json.data?.items || [];
        setBenchmarks(items);
      }
    } catch (err) {
      console.warn("Failed loading benchmark data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  // Poll active benchmark if running
  useEffect(() => {
    if (!activeBenchmarkId) return;

    const interval = setInterval(async () => {
      try {
        const res = await fetch(`/api/v1/benchmarks/${activeBenchmarkId}`);
        if (res.ok) {
          const json = await res.json();
          const bm: BenchmarkItem = json.data;
          if (bm.status === "completed" || bm.status === "failed") {
            setIsRunning(false);
            setActiveBenchmarkId(null);
            loadData();
          }
        }
      } catch {
        // Continue polling
      }
    }, 1500);

    return () => clearInterval(interval);
  }, [activeBenchmarkId]);

  const handleStartBenchmark = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDeploymentId || isRunning) return;

    setIsRunning(true);
    const activeDep = deployments.find((d) => d.id === selectedDeploymentId);
    const benchName = name.trim() || `${activeDep?.name || "Deployment"} Sweep`;

    try {
      const res = await fetch("/api/v1/benchmarks", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: benchName,
          deployment_id: selectedDeploymentId,
          concurrency,
          num_prompts: numPrompts,
          input_tokens: inputLen,
          output_tokens: outputLen,
        }),
      });

      if (res.ok) {
        const json = await res.json();
        const created: BenchmarkItem = json.data;
        setActiveBenchmarkId(created.id);
        setBenchmarks((prev) => [created, ...prev]);
      } else {
        setIsRunning(false);
      }
    } catch (err) {
      console.error("Error starting benchmark:", err);
      setIsRunning(false);
    }
  };

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      const res = await fetch(`/api/v1/benchmarks/${id}`, { method: "DELETE" });
      if (res.ok) {
        setBenchmarks((prev) => prev.filter((b) => b.id !== id));
        if (selectedBenchmark?.id === id) {
          setSelectedBenchmark(null);
        }
      }
    } catch (err) {
      console.error("Failed to delete benchmark:", err);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Inference benchmarks
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium bg-emerald-950/70 border border-emerald-800/60 text-emerald-400">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Benchmark Runner Active
            </span>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Automated synthetic load tests measuring TTFT, ITL (TPOT), and tokens per second throughput
          </p>
        </div>

        <button
          onClick={loadData}
          disabled={isLoading}
          className="h-9 px-3 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 self-start sm:self-auto transition-colors"
        >
          <RefreshCw className={`size-3.5 ${isLoading ? "animate-spin" : ""}`} />
          <span>Refresh Runs</span>
        </button>
      </div>

      {/* Configuration Form Card */}
      <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-5">
        <div className="flex items-center justify-between pb-3 border-b border-zinc-800/80">
          <h2 className="text-base sm:text-lg font-semibold text-white flex items-center gap-2.5">
            <Gauge className="size-4 text-zinc-400" />
            <span>Load test profile</span>
          </h2>
          <span className="text-xs sm:text-sm text-zinc-400 font-mono">
            Concurrent request pool distribution
          </span>
        </div>

        <form onSubmit={handleStartBenchmark} className="space-y-5">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
            {/* Target Deployment */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Target Deployment
              </label>
              <select
                value={selectedDeploymentId}
                onChange={(e) => {
                  setSelectedDeploymentId(e.target.value);
                  const dep = deployments.find((d) => d.id === e.target.value);
                  if (dep) setName(`${dep.name} Concurrency Sweep`);
                }}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
              >
                {deployments.map((d) => (
                  <option key={d.id} value={d.id}>
                    {d.name} ({d.engine} : {d.status})
                  </option>
                ))}
              </select>
            </div>

            {/* Benchmark Name */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Benchmark Run Label
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Llama-8B Concurrency 32 Sweep"
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
              />
            </div>

            {/* Concurrency */}
            <div>
              <div className="flex justify-between text-sm text-zinc-300 mb-1.5">
                <span className="font-medium">Concurrency</span>
                <span className="font-mono tabular-nums text-zinc-200">{concurrency} users</span>
              </div>
              <input
                type="range"
                min="1"
                max="64"
                step="1"
                value={concurrency}
                onChange={(e) => setConcurrency(Number(e.target.value))}
                className="w-full accent-zinc-200 h-1.5 bg-zinc-800 rounded cursor-pointer mt-2.5"
              />
            </div>

            {/* Input / Output Tokens */}
            <div>
              <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                Input / Output Tokens
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={inputLen}
                  onChange={(e) => setInputLen(Number(e.target.value))}
                  placeholder="Input"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 font-mono text-center tabular-nums"
                />
                <span className="text-zinc-500 font-mono">/</span>
                <input
                  type="number"
                  value={outputLen}
                  onChange={(e) => setOutputLen(Number(e.target.value))}
                  placeholder="Output"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 font-mono text-center tabular-nums"
                />
              </div>
            </div>
          </div>

          {/* Running progress bar indicator */}
          {isRunning && (
            <div className="p-4 rounded-md bg-zinc-950 border border-zinc-800 space-y-2.5">
              <div className="flex justify-between text-sm">
                <span className="text-zinc-300 font-mono flex items-center gap-2">
                  <RefreshCw className="size-3.5 animate-spin text-emerald-400" />
                  Executing workload ({concurrency} concurrent workers, {numPrompts} prompts)...
                </span>
                <span className="text-emerald-400 font-mono font-medium">Running</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div className="bg-emerald-400 h-1.5 rounded-full animate-pulse w-full" />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end pt-2">
            <button
              type="submit"
              disabled={isRunning || deployments.length === 0}
              className="h-9 px-5 rounded-md bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 text-sm font-medium flex items-center gap-2 transition-colors"
            >
              <Play className="size-4" />
              <span>{isRunning ? "Running sweep..." : "Run benchmark"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results Table */}
      <div className="p-5 sm:p-6 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div>
          <h2 className="text-base sm:text-lg font-semibold text-white">
            Run history
          </h2>
          <p className="text-xs sm:text-sm text-zinc-400 mt-0.5">
            Measured latency percentiles, throughput, and peak memory from completed executions
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-mono text-xs uppercase tracking-wider">
                <th className="pb-3 font-medium">Benchmark run / model</th>
                <th className="pb-3 font-medium">Engine</th>
                <th className="pb-3 font-medium">Concurrency</th>
                <th className="pb-3 font-medium">Throughput</th>
                <th className="pb-3 font-medium">TTFT (p50 / p99)</th>
                <th className="pb-3 font-medium">ITL (TPOT)</th>
                <th className="pb-3 font-medium">Status</th>
                <th className="pb-3 font-medium text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono tabular-nums">
              {benchmarks.map((bm) => (
                <tr
                  key={bm.id}
                  onClick={() => setSelectedBenchmark(bm)}
                  className="hover:bg-zinc-800/20 cursor-pointer transition-colors"
                >
                  <td className="py-3 pr-4 font-sans">
                    <div className="font-medium text-white text-sm">{bm.name}</div>
                    <div className="text-xs text-zinc-400 font-mono truncate max-w-xs mt-0.5">
                      {bm.model_name || bm.deployment_name || "Inference Engine"}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 text-xs">
                      {bm.engine}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {bm.concurrency} users
                  </td>
                  <td className="py-3 pr-4 text-white font-medium">
                    {bm.tokens_per_sec > 0 ? `${bm.tokens_per_sec} tok/s` : "-"}
                  </td>
                  <td className="py-3 pr-4 text-zinc-200">
                    {bm.p50_ttft_ms > 0 ? `${bm.p50_ttft_ms} ms / ` : "-"}
                    <span className="text-zinc-400">{bm.p99_ttft_ms > 0 ? `${bm.p99_ttft_ms} ms` : ""}</span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {bm.mean_tpot_ms > 0 ? `${bm.mean_tpot_ms} ms` : "-"}
                  </td>
                  <td className="py-3 pr-4">
                    <span
                      className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium border ${
                        bm.status === "completed"
                          ? "bg-emerald-950/70 border-emerald-800/60 text-emerald-400"
                          : bm.status === "running"
                          ? "bg-amber-950/70 border-amber-800/60 text-amber-400"
                          : bm.status === "failed"
                          ? "bg-rose-950/70 border-rose-800/60 text-rose-400"
                          : "bg-zinc-800 border-zinc-700 text-zinc-300"
                      }`}
                    >
                      {bm.status === "completed" && <CheckCircle2 className="size-3" />}
                      {bm.status === "running" && <RefreshCw className="size-3 animate-spin" />}
                      {bm.status === "failed" && <AlertCircle className="size-3" />}
                      {bm.status}
                    </span>
                  </td>
                  <td className="py-3 text-right">
                    <button
                      onClick={(e) => handleDelete(bm.id, e)}
                      className="p-1.5 rounded hover:bg-zinc-800 text-zinc-500 hover:text-zinc-300 transition-colors"
                      title="Delete benchmark"
                    >
                      <Trash2 className="size-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Latency & Histogram Detail Modal */}
      {selectedBenchmark && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <div>
                <h3 className="font-semibold text-white text-base">
                  {selectedBenchmark.name}
                </h3>
                <p className="text-xs text-zinc-400 font-mono mt-0.5">
                  Concurrency: {selectedBenchmark.concurrency} | Engine: {selectedBenchmark.engine}
                </p>
              </div>
              <button
                onClick={() => setSelectedBenchmark(null)}
                className="text-zinc-400 hover:text-white text-sm"
              >
                <X className="size-5" />
              </button>
            </div>

            {/* Metrics Breakdown Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
              <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                <span className="text-xs text-zinc-400 font-mono block">Throughput</span>
                <span className="text-lg font-bold font-mono text-white mt-0.5 block">
                  {selectedBenchmark.tokens_per_sec} tok/s
                </span>
              </div>
              <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                <span className="text-xs text-zinc-400 font-mono block">RPS</span>
                <span className="text-lg font-bold font-mono text-white mt-0.5 block">
                  {selectedBenchmark.rps} req/s
                </span>
              </div>
              <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                <span className="text-xs text-zinc-400 font-mono block">P50 Latency</span>
                <span className="text-lg font-bold font-mono text-white mt-0.5 block">
                  {selectedBenchmark.p50_latency_ms} ms
                </span>
              </div>
              <div className="p-3 rounded bg-zinc-950 border border-zinc-800">
                <span className="text-xs text-zinc-400 font-mono block">P95 Latency</span>
                <span className="text-lg font-bold font-mono text-white mt-0.5 block">
                  {selectedBenchmark.p95_latency_ms} ms
                </span>
              </div>
            </div>

            {/* Percentile Histogram */}
            <div className="p-4 rounded bg-zinc-950 border border-zinc-800 space-y-3">
              <span className="text-xs font-semibold text-zinc-300 font-mono block">
                Latency Percentile Histogram
              </span>
              <div className="space-y-2 text-xs font-mono">
                {selectedBenchmark.results_json?.latency_histogram &&
                  Object.entries(selectedBenchmark.results_json.latency_histogram).map(
                    ([pct, val]: [string, any]) => (
                      <div key={pct} className="flex justify-between items-center text-zinc-400">
                        <span className="uppercase">{pct}</span>
                        <div className="flex-1 mx-3 bg-zinc-800 h-1.5 rounded-full overflow-hidden">
                          <div
                            className="bg-emerald-400 h-full rounded-full"
                            style={{
                              width: `${Math.min(
                                100,
                                (val / (selectedBenchmark.p99_latency_ms || 1)) * 100
                              )}%`,
                            }}
                          />
                        </div>
                        <span className="text-zinc-200 tabular-nums">{val} ms</span>
                      </div>
                    )
                  )}
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                onClick={() => setSelectedBenchmark(null)}
                className="px-4 py-2 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800"
              >
                Close Report
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
