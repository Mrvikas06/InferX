"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Copy,
  Pause,
  Play,
  Plus,
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
    setTimeout(() => setCopiedId(null), 1500);
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
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Serving deployments
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Active vLLM, SGLang, and TensorRT-LLM endpoints handling completions
          </p>
        </div>

        <button
          onClick={() => setShowDeployModal(true)}
          className="h-9 px-4 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <Plus className="size-4" />
          <span>Launch deployment</span>
        </button>
      </div>

      {/* Deployments List */}
      <div className="space-y-4">
        {deployments.map((dep) => (
          <div
            key={dep.id}
            className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 space-y-4"
          >
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-3">
              <div className="space-y-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-semibold text-white text-base">
                    {dep.name}
                  </h3>
                  <span className="inline-flex items-center gap-2 text-xs font-mono">
                    <span
                      className={`size-2 rounded-full ${
                        dep.status === "running"
                          ? "bg-emerald-500"
                          : dep.status === "scaling"
                          ? "bg-amber-500"
                          : "bg-zinc-600"
                      }`}
                    />
                    <span className="text-zinc-300 font-medium">{dep.status}</span>
                  </span>

                  <span className="text-xs px-2.5 py-0.5 rounded border border-zinc-800 bg-zinc-900 text-zinc-300 font-mono">
                    {dep.engine}
                  </span>
                </div>
                <p className="text-xs sm:text-sm text-zinc-400 font-mono mt-0.5">
                  {dep.model}
                </p>
              </div>

              {/* Endpoint Copy & Test Actions */}
              <div className="flex items-center gap-2.5">
                <button
                  onClick={() => handleCopyEndpoint(dep.port, dep.id)}
                  className="h-8 px-3 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-mono flex items-center gap-1.5 transition-colors"
                  title="Copy full endpoint URL"
                >
                  <Copy className="size-3.5 text-zinc-400" />
                  <span>localhost:{dep.port}/v1</span>
                  {copiedId === dep.id && (
                    <span className="text-xs text-emerald-400 font-sans ml-1">
                      copied
                    </span>
                  )}
                </button>

                <Link
                  href="/dashboard/playground"
                  className="h-8 px-3 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-xs font-medium flex items-center gap-1.5 transition-colors"
                >
                  <Terminal className="size-3.5 text-zinc-400" />
                  <span>Test</span>
                </Link>

                <button
                  onClick={() => handleToggleStatus(dep.id)}
                  className="h-8 w-8 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 hover:text-white flex items-center justify-center transition-colors"
                  title={dep.status === "running" ? "Pause serving" : "Start serving"}
                >
                  {dep.status === "running" ? (
                    <Pause className="size-4" />
                  ) : (
                    <Play className="size-4" />
                  )}
                </button>
              </div>
            </div>

            {/* Metrics Breakdown */}
            <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-6 gap-4 pt-3.5 border-t border-zinc-800/80 text-sm font-mono">
              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">Parallelism</span>
                <div className="text-zinc-200 font-medium">TP={dep.tensorParallel}</div>
              </div>

              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">Hardware</span>
                <div className="text-zinc-200 truncate">{dep.gpuType}</div>
              </div>

              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">Max context</span>
                <div className="text-zinc-200 tabular-nums">
                  {dep.maxModelLen.toLocaleString()} tok
                </div>
              </div>

              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">KV cache</span>
                <div className="text-zinc-200 tabular-nums">{dep.kvCacheUsage}%</div>
              </div>

              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">Throughput</span>
                <div className="text-zinc-200 tabular-nums">{dep.qps} rps</div>
              </div>

              <div>
                <span className="text-xs text-zinc-400 font-sans block mb-0.5">Replicas</span>
                <div className="text-zinc-200 tabular-nums">{dep.replicas} active</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Launch Deployment Modal */}
      {showDeployModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-lg bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="font-semibold text-white text-base">
                Launch serving engine
              </h3>
              <button
                onClick={() => setShowDeployModal(false)}
                className="text-zinc-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleCreateDeployment} className="space-y-4 text-sm">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Deployment name
                </label>
                <input
                  type="text"
                  placeholder="prod-llama-3-3-70b"
                  value={depName}
                  onChange={(e) => setDepName(e.target.value)}
                  required
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3.5 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                    Model
                  </label>
                  <select
                    value={depModel}
                    onChange={(e) => setDepModel(e.target.value)}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono text-xs"
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
                  <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                    Engine
                  </label>
                  <select
                    value={depEngine}
                    onChange={(e) =>
                      setDepEngine(
                        e.target.value as "vLLM" | "SGLang" | "TensorRT-LLM"
                      )
                    }
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                  >
                    <option value="vLLM">vLLM</option>
                    <option value="SGLang">SGLang</option>
                    <option value="TensorRT-LLM">TensorRT-LLM</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                    TP GPUs
                  </label>
                  <select
                    value={depTP}
                    onChange={(e) => setDepTP(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                  >
                    <option value={1}>1 GPU</option>
                    <option value={2}>2 GPUs</option>
                    <option value={4}>4 GPUs</option>
                    <option value={8}>8 GPUs</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                    Port
                  </label>
                  <input
                    type="number"
                    value={depPort}
                    onChange={(e) => setDepPort(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                    Max context
                  </label>
                  <input
                    type="number"
                    value={depMaxLen}
                    onChange={(e) => setDepMaxLen(Number(e.target.value))}
                    className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                  />
                </div>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowDeployModal(false)}
                  className="px-4 py-2 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium transition-colors"
                >
                  Start engine
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
