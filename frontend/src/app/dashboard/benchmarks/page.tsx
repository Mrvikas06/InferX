"use client";

import React, { useState } from "react";
import {
  Flame,
  Gauge,
  Layers,
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
    name: "Llama-70B FP8 High Concurrency",
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
    name: "DeepSeek-R1 Distill SGLang Radix",
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
        return prev + 15;
      });
    }, 400);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            Inference Benchmarking Suite
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Evaluate TTFT, inter-token latency, serving throughput, and concurrency scaling curves.
          </p>
        </div>
      </div>

      {/* Benchmark Launch Form & Real-time Progress */}
      <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
          <h2 className="text-base font-semibold text-white flex items-center gap-2">
            <Gauge className="size-4 text-cyan-400" />
            Synthetic Load Configuration
          </h2>
          <span className="text-xs text-zinc-400 font-mono">
            Mode: Poisson Request Distribution
          </span>
        </div>

        <form onSubmit={handleStartBenchmark} className="space-y-4 text-xs">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div>
              <label className="block text-zinc-300 font-medium mb-1">
                Target Model
              </label>
              <select
                value={targetModel}
                onChange={(e) => setTargetModel(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
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
              <label className="block text-zinc-300 font-medium mb-1">
                Serving Engine
              </label>
              <select
                value={targetEngine}
                onChange={(e) =>
                  setTargetEngine(
                    e.target.value as "vLLM" | "SGLang" | "TensorRT-LLM"
                  )
                }
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
              >
                <option value="vLLM">vLLM (Chunked Prefill)</option>
                <option value="SGLang">SGLang (Radix Attention)</option>
                <option value="TensorRT-LLM">TensorRT-LLM (In-Flight Batching)</option>
              </select>
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">
                Concurrency Users ({concurrency})
              </label>
              <input
                type="range"
                min="1"
                max="128"
                step="1"
                value={concurrency}
                onChange={(e) => setConcurrency(Number(e.target.value))}
                className="w-full accent-cyan-500 h-2 bg-zinc-800 rounded-lg cursor-pointer mt-2"
              />
            </div>

            <div>
              <label className="block text-zinc-300 font-medium mb-1">
                Prompt / Output Tokens
              </label>
              <div className="flex items-center gap-2">
                <input
                  type="number"
                  value={inputLen}
                  onChange={(e) => setInputLen(Number(e.target.value))}
                  placeholder="Input"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1.5 text-zinc-200 font-mono text-center"
                />
                <span className="text-zinc-500 font-mono">/</span>
                <input
                  type="number"
                  value={outputLen}
                  onChange={(e) => setOutputLen(Number(e.target.value))}
                  placeholder="Output"
                  className="w-1/2 bg-zinc-950 border border-zinc-800 rounded-lg px-2 py-1.5 text-zinc-200 font-mono text-center"
                />
              </div>
            </div>
          </div>

          {/* Progress Bar when running */}
          {isRunning && (
            <div className="p-3 rounded-lg bg-zinc-950 border border-cyan-800/60 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-cyan-400 font-medium flex items-center gap-1.5">
                  <Flame className="size-3.5 animate-spin" />
                  Simulating synthetic client traffic ({concurrency} parallel streams)...
                </span>
                <span className="text-zinc-400 font-mono">{progress}%</span>
              </div>
              <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                <div
                  className="bg-cyan-500 h-1.5 rounded-full transition-all duration-300"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>
          )}

          <div className="flex items-center justify-end gap-3 pt-2">
            <button
              type="submit"
              disabled={isRunning}
              className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-50 text-white font-medium flex items-center gap-2 transition shadow-sm"
            >
              <Play className="size-3.5" />
              <span>{isRunning ? "Benchmarking..." : "Execute Stress Test"}</span>
            </button>
          </div>
        </form>
      </div>

      {/* Benchmark History & Results Table */}
      <div className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base font-semibold text-white flex items-center gap-2">
              <Layers className="size-4 text-cyan-400" />
              Benchmark Execution History & Results
            </h2>
            <p className="text-xs text-zinc-400 mt-0.5">
              Comparative latency and throughput metrics from recent runs.
            </p>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead>
              <tr className="border-b border-zinc-800 text-zinc-400 font-mono">
                <th className="pb-3 font-medium">Run Name / Model</th>
                <th className="pb-3 font-medium">Engine</th>
                <th className="pb-3 font-medium">Concurrency</th>
                <th className="pb-3 font-medium">Throughput (Tok/s)</th>
                <th className="pb-3 font-medium">TTFT (P50 / P99)</th>
                <th className="pb-3 font-medium">ITL (P50)</th>
                <th className="pb-3 font-medium">Peak VRAM</th>
                <th className="pb-3 font-medium">Timestamp</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-zinc-800/60 font-mono">
              {benchmarks.map((bm) => (
                <tr key={bm.id} className="hover:bg-zinc-800/30 transition">
                  <td className="py-3 pr-4 font-sans">
                    <div className="font-medium text-white">{bm.name}</div>
                    <div className="text-[11px] text-zinc-500 font-mono truncate max-w-xs">
                      {bm.model}
                    </div>
                  </td>
                  <td className="py-3 pr-4">
                    <span className="px-2 py-0.5 rounded bg-zinc-800 text-zinc-300 border border-zinc-700/60 text-[11px]">
                      {bm.engine}
                    </span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {bm.concurrency} users
                  </td>
                  <td className="py-3 pr-4 text-cyan-400 font-bold">
                    {bm.throughput.toLocaleString()}
                  </td>
                  <td className="py-3 pr-4 text-emerald-400">
                    {bm.ttftP50}ms / <span className="text-zinc-500">{bm.ttftP99}ms</span>
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {bm.itlP50}ms
                  </td>
                  <td className="py-3 pr-4 text-zinc-300">
                    {bm.vramPeak} GB
                  </td>
                  <td className="py-3 text-zinc-500 font-sans text-[11px]">
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
