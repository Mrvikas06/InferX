"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  Filter,
  Play,
  Plus,
  Rocket,
  Search,
} from "lucide-react";

interface ModelRecord {
  id: string;
  name: string;
  repoId: string;
  architecture: string;
  parameters: string;
  contextWindow: string;
  quantization: "FP16" | "BF16" | "FP8" | "AWQ" | "GPTQ";
  sizeOnDisk: string;
  minGpuVram: string;
  status: "ready" | "downloading" | "remote";
  tags: string[];
}

const initialModels: ModelRecord[] = [
  {
    id: "m-1",
    name: "Llama 3.3 70B Instruct",
    repoId: "meta-llama/Llama-3.3-70B-Instruct",
    architecture: "LlamaForCausalLM",
    parameters: "70B",
    contextWindow: "128k",
    quantization: "FP8",
    sizeOnDisk: "72.4 GB",
    minGpuVram: "2x 80GB H100",
    status: "ready",
    tags: ["Chat", "Reasoning", "Code"],
  },
  {
    id: "m-2",
    name: "DeepSeek R1 Distill Qwen 32B",
    repoId: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    architecture: "Qwen2ForCausalLM",
    parameters: "32B",
    contextWindow: "64k",
    quantization: "BF16",
    sizeOnDisk: "65.1 GB",
    minGpuVram: "1x 80GB H100",
    status: "ready",
    tags: ["Math", "CoT", "Reasoning"],
  },
  {
    id: "m-3",
    name: "Mistral Small 24B Instruct",
    repoId: "mistralai/Mistral-Small-24B-Instruct-2501",
    architecture: "MistralForCausalLM",
    parameters: "24B",
    contextWindow: "32k",
    quantization: "AWQ",
    sizeOnDisk: "14.2 GB",
    minGpuVram: "1x 40GB A100",
    status: "ready",
    tags: ["Fast", "Multilingual"],
  },
  {
    id: "m-4",
    name: "Qwen 2.5 Coder 32B Instruct",
    repoId: "Qwen/Qwen2.5-Coder-32B-Instruct",
    architecture: "Qwen2ForCausalLM",
    parameters: "32B",
    contextWindow: "128k",
    quantization: "BF16",
    sizeOnDisk: "64.8 GB",
    minGpuVram: "1x 80GB H100",
    status: "ready",
    tags: ["Code", "Agent", "Tool Calling"],
  },
  {
    id: "m-5",
    name: "Gemma 2 27B IT",
    repoId: "google/gemma-2-27b-it",
    architecture: "Gemma2ForCausalLM",
    parameters: "27B",
    contextWindow: "8k",
    quantization: "FP8",
    sizeOnDisk: "29.2 GB",
    minGpuVram: "1x 40GB A100",
    status: "downloading",
    tags: ["General", "Instruction"],
  },
  {
    id: "m-6",
    name: "BGE M3 Multilingual Embedding",
    repoId: "BAAI/bge-m3",
    architecture: "XLMRobertaModel",
    parameters: "560M",
    contextWindow: "8k",
    quantization: "FP16",
    sizeOnDisk: "2.2 GB",
    minGpuVram: "1x 8GB",
    status: "ready",
    tags: ["Embeddings", "RAG"],
  },
];

export default function ModelsRegistryPage() {
  const [models, setModels] = useState<ModelRecord[]>(initialModels);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedQuant, setSelectedQuant] = useState<string>("ALL");
  const [showAddModal, setShowAddModal] = useState(false);
  const [newRepoId, setNewRepoId] = useState("");
  const [newQuant, setNewQuant] = useState<"FP16" | "BF16" | "FP8" | "AWQ">("BF16");

  const filteredModels = models.filter((model) => {
    const matchesSearch =
      model.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.repoId.toLowerCase().includes(searchQuery.toLowerCase()) ||
      model.tags.some((t) => t.toLowerCase().includes(searchQuery.toLowerCase()));

    const matchesQuant =
      selectedQuant === "ALL" || model.quantization === selectedQuant;

    return matchesSearch && matchesQuant;
  });

  const handleAddModel = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newRepoId.trim()) return;

    const brandName = newRepoId.split("/")[1] || newRepoId;
    const newModelItem: ModelRecord = {
      id: `m-${Date.now()}`,
      name: brandName.replace(/-/g, " "),
      repoId: newRepoId.trim(),
      architecture: "AutoModelForCausalLM",
      parameters: "Custom",
      contextWindow: "32k",
      quantization: newQuant,
      sizeOnDisk: "-",
      minGpuVram: "1x GPU",
      status: "downloading",
      tags: ["Imported", "Custom"],
    };

    setModels([newModelItem, ...models]);
    setNewRepoId("");
    setShowAddModal(false);
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
            Model registry
          </h1>
          <p className="text-sm text-zinc-400 mt-1">
            Weights catalog, architectures, and precision checkpoints
          </p>
        </div>

        <button
          onClick={() => setShowAddModal(true)}
          className="h-9 px-4 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium flex items-center gap-2 transition-colors self-start sm:self-auto"
        >
          <Plus className="size-4" />
          <span>Register model</span>
        </button>
      </div>

      {/* Filter and Search Bar */}
      <div className="flex flex-col sm:flex-row gap-3 items-stretch sm:items-center justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="size-4 text-zinc-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Filter models by name or HuggingFace ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-zinc-900/60 border border-zinc-800 rounded-md pl-9 pr-3.5 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700"
          />
        </div>

        <div className="flex items-center gap-2">
          <Filter className="size-3.5 text-zinc-400 shrink-0" />
          <span className="text-xs text-zinc-400 shrink-0 font-medium">Precision:</span>
          {["ALL", "FP8", "BF16", "FP16", "AWQ"].map((quant) => (
            <button
              key={quant}
              onClick={() => setSelectedQuant(quant)}
              className={`text-xs px-3 py-1.5 rounded font-mono transition-colors shrink-0 ${
                selectedQuant === quant
                  ? "bg-zinc-800 text-white font-medium border border-zinc-700"
                  : "bg-zinc-900/60 text-zinc-400 border border-zinc-800/80 hover:text-zinc-200"
              }`}
            >
              {quant}
            </button>
          ))}
        </div>
      </div>

      {/* Model Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        {filteredModels.map((model) => (
          <div
            key={model.id}
            className="p-5 rounded-lg border border-zinc-800/80 bg-zinc-900/40 flex flex-col justify-between space-y-4"
          >
            <div>
              <div className="flex items-start justify-between gap-2">
                <div>
                  <h3 className="font-semibold text-white text-base">
                    {model.name}
                  </h3>
                  <p className="text-xs text-zinc-400 font-mono mt-1 break-all">
                    {model.repoId}
                  </p>
                </div>
                <span className="text-xs font-mono text-zinc-300 px-2 py-0.5 rounded border border-zinc-800 bg-zinc-900">
                  {model.status === "ready" ? "Cached" : "Downloading"}
                </span>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-1.5 mt-3.5">
                {model.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2.5 py-0.5 rounded border border-zinc-800 bg-zinc-900/80 text-zinc-400"
                  >
                    {tag}
                  </span>
                ))}
                <span className="text-xs px-2.5 py-0.5 rounded border border-zinc-800 bg-zinc-900 font-mono text-zinc-300 font-medium">
                  {model.quantization}
                </span>
              </div>

              {/* Specs Grid */}
              <div className="grid grid-cols-2 gap-3 mt-4 pt-3.5 border-t border-zinc-800/80 text-sm">
                <div>
                  <span className="text-xs text-zinc-400 block mb-0.5">Parameters</span>
                  <div className="text-zinc-200 font-mono tabular-nums font-medium">
                    {model.parameters}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-zinc-400 block mb-0.5">Context</span>
                  <div className="text-zinc-200 font-mono tabular-nums font-medium">
                    {model.contextWindow}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-zinc-400 block mb-0.5">Size</span>
                  <div className="text-zinc-200 font-mono tabular-nums font-medium">
                    {model.sizeOnDisk}
                  </div>
                </div>
                <div>
                  <span className="text-xs text-zinc-400 block mb-0.5">Min GPU</span>
                  <div className="text-zinc-200 font-mono font-medium">
                    {model.minGpuVram}
                  </div>
                </div>
              </div>
            </div>

            {/* Actions */}
            <div className="pt-3.5 border-t border-zinc-800/80 flex items-center justify-between gap-2.5">
              <Link
                href="/dashboard/deployments"
                className="flex-1 h-9 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors"
              >
                <Rocket className="size-3.5" />
                <span>Deploy</span>
              </Link>
              <Link
                href="/dashboard/playground"
                className="h-9 px-4 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-sm font-medium flex items-center justify-center gap-1.5 transition-colors"
              >
                <Play className="size-3.5 text-zinc-400" />
                <span>Test</span>
              </Link>
            </div>
          </div>
        ))}
      </div>

      {/* Register Model Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-md bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="font-semibold text-white text-base">
                Register HuggingFace model
              </h3>
              <button
                onClick={() => setShowAddModal(false)}
                className="text-zinc-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddModel} className="space-y-4 text-sm">
              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Repository ID
                </label>
                <input
                  type="text"
                  placeholder="meta-llama/Llama-3.3-70B-Instruct"
                  value={newRepoId}
                  onChange={(e) => setNewRepoId(e.target.value)}
                  required
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3.5 py-2 text-sm text-zinc-200 placeholder-zinc-500 focus:outline-none focus:border-zinc-700 font-mono"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-zinc-300 mb-1.5">
                  Precision format
                </label>
                <select
                  value={newQuant}
                  onChange={(e) =>
                    setNewQuant(
                      e.target.value as "FP16" | "BF16" | "FP8" | "AWQ"
                    )
                  }
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3.5 py-2 text-sm text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono"
                >
                  <option value="BF16">BF16</option>
                  <option value="FP16">FP16</option>
                  <option value="FP8">FP8</option>
                  <option value="AWQ">AWQ</option>
                </select>
              </div>

              <div className="flex items-center justify-end gap-3 pt-3">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="px-4 py-2 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium transition-colors"
                >
                  Queue download
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
