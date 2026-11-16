"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Copy,
  Pause,
  Play,
  Rocket,
  Terminal,
} from "lucide-react";

interface Deployment {
  id: string;
  name: string;
  model: string;
  engine: "vLLM" | "SGLang" | "TensorRT-LLM";
  tensorParallel: number;
  gpuType: string;
  port: number;
  maxModelLen: number;
  kvCacheUsage: number;
  qps: number;
  status: "running" | "stopped" | "scaling";
  replicas: number;
}

const initialDeployments: Deployment[] = [
  {
    id: "dep-101",
    name: "prod-llama-70b-vllm",
    model: "meta-llama/Llama-3.3-70B-Instruct",
    engine: "vLLM",
    tensorParallel: 4,
    gpuType: "NVIDIA H100 80GB SXM5",
    port: 8000,
    maxModelLen: 32768,
    kvCacheUsage: 78.4,
    qps: 184.2,
    status: "running",
    replicas: 1,
  },
  {
    id: "dep-102",
    name: "prod-deepseek-r1-sglang",
    model: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    engine: "SGLang",
    tensorParallel: 2,
    gpuType: "NVIDIA H100 80GB SXM5",
    port: 8001,
    maxModelLen: 16384,
    kvCacheUsage: 64.2,
    qps: 92.6,
    status: "running",
    replicas: 1,
  },
  {
    id: "dep-103",
    name: "prod-mistral-small",
    model: "mistralai/Mistral-Small-24B-Instruct-2501",
    engine: "vLLM",
    tensorParallel: 1,
    gpuType: "NVIDIA H100 80GB SXM5",
    port: 8002,
    maxModelLen: 32768,
    kvCacheUsage: 45.1,
    qps: 64.1,
    status: "running",
    replicas: 1,
  },
  {
    id: "dep-104",
    name: "staging-qwen-coder",
    model: "Qwen/Qwen2.5-Coder-32B-Instruct",
    engine: "TensorRT-LLM",
    tensorParallel: 1,
    gpuType: "NVIDIA H100 80GB SXM5",
    port: 8003,
    maxModelLen: 16384,
    kvCacheUsage: 82.0,
    qps: 38.0,
    status: "scaling",
    replicas: 2,
  },
];

export default function DeploymentsPage() {
  const [deployments, setDeployments] = useState<Deployment[]>(initialDeployments);
  const [showDeployModal, setShowDeployModal] = useState(false);
  const [copiedId, setCopiedId] = useState<string | null>(null);

  // New deployment form fields
  const [depName, setDepName] = useState("");
  const [depModel, setDepModel] = useState("meta-llama/Llama-3.3-70B-Instruct");
  const [depEngine, setDepEngine] = useState<"vLLM" | "SGLang" | "TensorRT-LLM">("vLLM");
  const [depTP, setDepTP] = useState<number>(2);
  const [depPort, setDepPort] = useState<number>(8004);
  const [depMaxLen, setDepMaxLen] = useState<number>(16384);

  const handleToggleStatus = (id: string) => {
    setDeployments((prev) =>
      prev.map((d) => {
        if (d.id === id) {
          const nextStatus = d.status === "running" ? "stopped" : "running";
          return { ...d, status: nextStatus };
        }
        return d;
      })
    );
  };

  const handleCopyEndpoint = (port: number, id: string) => {
    const url = `http://localhost:${port}/v1/chat/completions`;
    navigator.clipboard?.writeText(url);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const handleCreateDeployment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!depName.trim()) return;

    const newDep: Deployment = {
      id: `dep-${Date.now()}`,
      name: depName.trim(),
      model: depModel,
      engine: depEngine,
      tensorParallel: depTP,
      gpuType: "NVIDIA H100 80GB SXM5",
      port: depPort,
      maxModelLen: depMaxLen,
      kvCacheUsage: 12.0,
      qps: 0,
      status: "running",
      replicas: 1,
    };

    setDeployments([newDep, ...deployments]);
    setDepName("");
    setShowDeployModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-2 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-white flex items-center gap-2">
            Inference Deployments
          </h1>
          <p className="text-zinc-400 text-sm mt-1">
            Production serving endpoints running vLLM, SGLang, and TensorRT-LLM runtimes.
          </p>
        </div>

        <button
          onClick={() => setShowDeployModal(true)}
          className="px-3.5 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-1.5 transition shadow-sm self-start sm:self-auto"
        >
          <Rocket className="size-3.5" />
          <span>Launch Serving Instance</span>
        </button>
      </div>

      {/* Deployments List */}
      <div className="space-y-4">
        {deployments.map((dep) => (
          <div
            key={dep.id}
            className="p-5 rounded-xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition space-y-4"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-white text-base">
                    {dep.name}
                  </h3>
                  <span
                    className={`inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium font-mono ${
                      dep.status === "running"
                        ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                        : dep.status === "scaling"
                        ? "bg-amber-500/10 text-amber-400 border border-amber-500/20"
                        : "bg-zinc-800 text-zinc-400 border border-zinc-700"
                    }`}
                  >
                    <span
                      className={`size-1.5 rounded-full ${
                        dep.status === "running"
                          ? "bg-emerald-400 animate-pulse"
                          : dep.status === "scaling"
                          ? "bg-amber-400 animate-ping"
                          : "bg-zinc-500"
                      }`}
                    />
                    {dep.status.toUpperCase()}
                  </span>

                  <span className="text-[10px] px-2 py-0.5 rounded bg-zinc-800 text-cyan-400 border border-zinc-700 font-mono font-medium">
                    {dep.engine}
                  </span>
                </div>
                <p className="text-xs text-zinc-400 font-mono">
                  {dep.model}
                </p>
              </div>

              {/* Endpoint Quick Copy & Test */}
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleCopyEndpoint(dep.port, dep.id)}
                  className="px-2.5 py-1.5 rounded-lg bg-zinc-950 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-xs font-mono flex items-center gap-1.5 transition"
                  title="Copy OpenAI-compatible URL"
                >
                  <Copy className="size-3 text-zinc-500" />
                  <span>:{dep.port}/v1</span>
                  {copiedId === dep.id && (
                    <span className="text-[10px] text-emerald-400 font-sans ml-1">
                      Copied!
                    </span>
                  )}
                </button>

                <Link
                  href="/dashboard/playground"
                  className="px-3 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-200 text-xs font-medium flex items-center gap-1.5 transition"
                >
                  <Terminal className="size-3 text-cyan-400" />
                  <span>Playground</span>
                </Link>

                <button
                  onClick={() => handleToggleStatus(dep.id)}
                  className={`p-1.5 rounded-lg text-xs transition border ${
                    dep.status === "running"
                      ? "bg-amber-500/10 text-amber-400 border-amber-500/20 hover:bg-amber-500/20"
                      : "bg-emerald-500/10 text-emerald-400 border-emerald-500/20 hover:bg-emerald-500/20"
                  }`}
                  title={dep.status === "running" ? "Pause Serving" : "Start Serving"}
                >
                  {dep.status === "running" ? (
                    <Pause className="size-4" />
                  ) : (
                    <Play className="size-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Metrics & Parameters Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-3 pt-3 border-t border-zinc-800/80 text-xs">
              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">Tensor Parallel</span>
                <span className="text-zinc-200 font-mono font-medium">
                  TP = {dep.tensorParallel} GPUs
                </span>
              </div>

              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">GPU Hardware</span>
                <span className="text-zinc-200 font-mono font-medium truncate">
                  {dep.gpuType}
                </span>
              </div>

              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">Max Context Len</span>
                <span className="text-zinc-200 font-mono font-medium">
                  {dep.maxModelLen.toLocaleString()} tokens
                </span>
              </div>

              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">KV Cache Usage</span>
                <span className="text-zinc-200 font-mono font-medium">
                  {dep.kvCacheUsage}%
                </span>
              </div>

              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">Current QPS</span>
                <span className="text-zinc-200 font-mono font-medium">
                  {dep.qps} req/s
                </span>
              </div>

              <div className="flex flex-col">
                <span className="text-[11px] text-zinc-500">Active Workers</span>
                <span className="text-zinc-200 font-mono font-medium">
                  {dep.replicas} instance
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Launch Deployment Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <h3 className="font-semibold text-white text-base flex items-center gap-2">
                <Rocket className="size-4 text-cyan-400" />
                Launch InferX Serving Engine
              </h3>
              <button
                onClick={() => setShowDeployModal(false)}
                className="text-zinc-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDeployment} className="space-y-4 text-xs">
              <div>
                <label className="block text-zinc-300 font-medium mb-1">
                  Deployment Name
                </label>
                <input
                  type="text"
                  placeholder="e.g. prod-llama-3-3-70b"
                  value={depName}
                  onChange={(e) => setDepName(e.target.value)}
                  required
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-zinc-300 font-medium mb-1">
                    Model Weights
                  </label>
                  <select
                    value={depModel}
                    onChange={(e) => setDepModel(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono text-[11px]"
                  >
                    <option value="meta-llama/Llama-3.3-70B-Instruct">
                      meta-llama/Llama-3.3-70B-Instruct
                    </option>
                    <option value="deepseek-ai/DeepSeek-R1-Distill-Qwen-32B">
                      deepseek-ai/DeepSeek-R1-Distill-Qwen-32B
                    </option>
                    <option value="mistralai/Mistral-Small-24B-Instruct-2501">
                      mistralai/Mistral-Small-24B-Instruct-2501
                    </option>
                    <option value="Qwen/Qwen2.5-Coder-32B-Instruct">
                      Qwen/Qwen2.5-Coder-32B-Instruct
                    </option>
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-300 font-medium mb-1">
                    Serving Engine
                  </label>
                  <select
                    value={depEngine}
                    onChange={(e) =>
                      setDepEngine(
                        e.target.value as "vLLM" | "SGLang" | "TensorRT-LLM"
                      )
                    }
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value="vLLM">vLLM (PagedAttention, Chunked Prefill)</option>
                    <option value="SGLang">SGLang (RadixAttention, Fast Router)</option>
                    <option value="TensorRT-LLM">TensorRT-LLM (NVIDIA Optimized)</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-zinc-300 font-medium mb-1">
                    Tensor Parallel (TP)
                  </label>
                  <select
                    value={depTP}
                    onChange={(e) => setDepTP(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                  >
                    <option value={1}>1 GPU</option>
                    <option value={2}>2 GPUs</option>
                    <option value={4}>4 GPUs</option>
                    <option value={8}>8 GPUs</option>
                  </select>
                </div>

                <div>
                  <label className="block text-zinc-300 font-medium mb-1">
                    Port
                  </label>
                  <input
                    type="number"
                    value={depPort}
                    onChange={(e) => setDepPort(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-zinc-300 font-medium mb-1">
                    Max Tokens
                  </label>
                  <input
                    type="number"
                    value={depMaxLen}
                    onChange={(e) => setDepMaxLen(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-3 py-2 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono"
                  />
                </div>
              </div>

              <div className="p-3 rounded-lg bg-zinc-950 border border-zinc-800/80 text-[11px] text-zinc-400 space-y-1">
                <span className="text-zinc-200 font-medium">Automatic OpenAI API Compatibility:</span>
                <p>
                  Serves standard endpoints: <code className="text-cyan-400">/v1/chat/completions</code>,{" "}
                  <code className="text-cyan-400">/v1/completions</code>, and <code className="text-cyan-400">/v1/models</code>.
                </p>
              </div>

              <div className="flex items-center justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowDeployModal(false)}
                  className="px-3 py-2 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium"
                >
                  Start Engine
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
