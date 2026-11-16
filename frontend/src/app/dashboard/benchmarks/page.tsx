"use client";

import React, { useState } from "react";
import {
  Gauge,
  Play,
} from "lucide-react";

interface BenchmarkResult {
  id: string;
  name: string;
  engine: "vLLM" | "SGLang" | "TensorRT-LLM";
  model: string;
  concurrency: number;
  inputTokens: number;
  outputTokens: number;
  throughput: number; // tok/s
  ttftP50: number; // ms
  ttftP99: number; // ms
  itlP50: number; // ms
  vramPeak: number; // GB
  date: string;
}

const pastBenchmarks: BenchmarkResult[] = [
  {
    id: "bm-01",
    name: "Llama-70B FP8 Concurrency Sweep",
    engine: "vLLM",
    model: "meta-llama/Llama-3.3-70B-Instruct",
    concurrency: 64,
    inputTokens: 512,
    outputTokens: 256,
    throughput: 4850,
    ttftP50: 16.2,
    ttftP99: 34.5,
    itlP50: 8.4,
    vramPeak: 68.4,
    date: "Today, 14:20",
  },
  {
    id: "bm-02",
    name: "DeepSeek-R1 Distill Radix Sweep",
    engine: "SGLang",
    model: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    concurrency: 64,
    inputTokens: 1024,
    outputTokens: 512,
    throughput: 5210,
    ttftP50: 12.1,
    ttftP99: 26.8,
    itlP50: 6.9,
    vramPeak: 61.2,
    date: "Today, 12:05",
  },
  {
    id: "bm-03",
    name: "Mistral-24B AWQ Single GPU",
    engine: "vLLM",
    model: "mistralai/Mistral-Small-24B-Instruct-2501",
    concurrency: 32,
    inputTokens: 256,
    outputTokens: 128,
    throughput: 2940,
    ttftP50: 9.8,
    ttftP99: 18.2,
    itlP50: 5.1,
    vramPeak: 22.8,
    date: "Yesterday",
  },
];

export default function BenchmarksPage() {
  const [isRunning, setIsRunning] = useState(false);
  const [targetModel, setTargetModel] = useState("meta-llama/Llama-3.3-70B-Instruct");
  const [targetEngine, setTargetEngine] = useState<"vLLM" | "SGLang" | "TensorRT-LLM">("vLLM");
  const [concurrency, setConcurrency] = useState(32);
  const [inputLen, setInputLen] = useState(512);
  const [outputLen, setOutputLen] = useState(256);
  const [progress, setProgress] = useState(0);

  const [benchmarks, setBenchmarks] = useState<BenchmarkResult[]>(pastBenchmarks);

  const handleStartBenchmark = (e: React.FormEvent) => {
    e.preventDefault();
    setIsRunning(true);
    setProgress(0);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setIsRunning(false);

          const newResult: BenchmarkResult = {
            id: `bm-${Date.now()}`,
            name: `${targetModel.split("/")[1]} Sweep (C=${concurrency})`,
            engine: targetEngine,
            model: targetModel,
            concurrency: concurrency,
            inputTokens: inputLen,
            outputTokens: outputLen,
            throughput: Math.floor(3800 + Math.random() * 1500),
            ttftP50: parseFloat((11 + Math.random() * 6).toFixed(1)),
            ttftP99: parseFloat((24 + Math.random() * 12).toFixed(1)),
            itlP50: parseFloat((6 + Math.random() * 4).toFixed(1)),
            vramPeak: 64.5,
            date: "Just now",
          };

          setBenchmarks([newResult, ...benchmarks]);
          return 100;
        }
        return prev + 20;
      });
    }, 300);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">
            Benchmarks
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Synthetic load tests measuring TTFT, ITL, and tokens per second
          </p>
        </div>
      </div>

      {/* Configuration Form */}
      <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-800/80">
          <h2 className="text-sm font-medium text-white flex items-center gap-2">
            <Gauge className="size-3.5 text-zinc-400" />
            <span>Load test profile</span>
          </h2>
          <span className="text-xs text-zinc-500 font-mono">
            Poisson request distribution
          </span>
        </div>

        <form onSubmit={handleStartBenchmark} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-zinc-400 mb-1">
                Model
              </label>
              <select
                value={targetModel}
                onChange={(e) => setTargetModel(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-2.5 py-1.5 text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
              >
                <option value="meta-llama/Llama-3.3-70B-Instruct">
                  Llama 3.3 70B Instruct
                </option>
                <option value="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B">
                  DeepSeek R1 Distill Qwen 32B
                </option>
                <option value="mistralai/Mistral-Small-24B-Instruct-2501">
                  Mistral Small 24B Instruct
                </option>
              </select>
            </div>

            <div>
              <label className="block text-zinc-400 mb-1">
                Engine
              </label>
              <select
                value={targetEngine}
                onChange={(e) =>
                  setTargetEngine(
                    e.target.value as "vLLM" | "SGLang" | "TensorRT-LLM"
                  )
                }
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-2.5 py-1.5 text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
              >
                <option value="vLLM">vLLM (Chunked prefill)</option>
                <option value="SGLang">SGLang (Radix attention)</option>
                <option value="TensorRT-LLM">TensorRT-LLM (In-flight batching)</option>
              </select>
            </div>

            <div>
              <div className="flex justify-between text-zinc-400 mb-1">
                <span>Concurrency</span>
                <span className="font-mono tabular-nums text-zinc-200">{concurrency} users</span>
              </div>
              <input
                type="range"
                min="1"
                max="128"
                step="1"
                value={concurrency}
                onChange={(e) => setConcurrency(Number(e.target.value))}
                className="w-full accent-zinc-200 h-1 bg-zinc-800 rounded cursor-pointer mt-2"
              />
            </div>

            <div>
              <label className="block text-zinc-400 mb-1">
                Input / output tokens
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={inputLen}
                  onChange={(e) => setInputLen(Number(e.target.value))}
                  placeholder="Input"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-zinc-200 font-mono text-center tabular-nums"
                />
                <span className="text-zinc-600 font-mono">/</span>
                <input
                  type="number"
                  value={outputLen}
                  onChange={(e) => setOutputLen(Number(e.target.value))}
                  placeholder="Output"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-md px-2 py-1.5 text-zinc-200 font-mono text-center tabular-nums"
                />
              </div>
            </div>
          </div>

          {isRunning && (
            <div className="p-3 rounded-md bg-zinc-950 border border-zinc-800 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-300 font-mono">
                  Executing workload ({concurrency} concurrent streams)...
                </span>
                <span className="text-zinc-400 font-mono tabular-nums">{progress}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-1 overflow-hidden">
                <div
                  className="bg-zinc-200 h-1 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end pt-2">
            <button
              type="submit"
              disabled={isRunning}
              className="h-8 px-4 rounded-md bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 font-medium flex items-center gap-1.5 transition-colors"
            >
              <Play className="size-3.5" />
              <span>{isRunning ? "Running..." : "Run benchmark"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Results Table */}
      <div className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4">
        <div>
          <h2 className="text-sm font-medium text-white">
            Run history
          </h2>
          <p className="text-xs text-zinc-500 mt-0.5">
            Measured percentiles and throughput from completed executions
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-500 font-mono">
                <th className="pb-2.5 font-normal">Workload / model</th>
                <th className="pb-2.5 font-normal">Engine</th>
                <th className="pb-2.5 font-normal">Concurrency</th>
                <th className="pb-2.5 font-normal">Throughput</th>
                <th className="pb-2.5 font-normal">TTFT (p50 / p99)</th>
                <th className="pb-2.5 font-normal">ITL (p50)</th>
                <th className="pb-2.5 font-normal">VRAM peak</th>
                <th className="pb-2.5 font-normal">Time</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono tabular-nums">
              {benchmarks.map((bm) => (
                <tr key={bm.id} className="hover:bg-zinc-800/20 transition-colors">
                  <td className="py-2.5 pr-4 font-sans">
                    <div className="font-medium text-white">{bm.name}</div>
                    <div className="text-[11px] text-zinc-500 font-mono truncate max-w-xs">
                      {bm.model}
                    </div>
                  </td>
                  <td className="py-2.5 pr-4">
                    <span className="px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 text-[11px]">
                      {bm.engine}
                    </span>
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-400">
                    {bm.concurrency}
                  </td>
                  <td className="py-2.5 pr-4 text-white font-medium">
                    {bm.throughput.toLocaleString()} tok/s
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-200">
                    {bm.ttftP50}ms / <span className="text-zinc-500">{bm.ttftP99}ms</span>
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-300">
                    {bm.itlP50}ms
                  </td>
                  <td className="py-2.5 pr-4 text-zinc-400">
                    {bm.vramPeak} GB
                  </td>
                  <td className="py-2.5 text-zinc-500 font-sans text-[11px]">
                    {bm.date}
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
