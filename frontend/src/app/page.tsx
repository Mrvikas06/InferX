import Link from "next/link";
import {
  Activity,
  ArrowRight,
  Flame,
  Gauge,
  Server,
  Terminal,
  Zap,
} from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col font-sans selection:bg-cyan-500 selection:text-black">
      {/* Top Navigation */}
      <header className="border-b border-zinc-800/80 bg-zinc-950/70 backdrop-blur-md sticky top-0 z-50 px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="size-9 rounded-xl bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Zap className="size-5 text-white" />
          </div>
          <span className="font-bold tracking-tight text-lg text-white flex items-center gap-2">
            Infer<span className="text-cyan-400">X</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-400">
              v0.4.2
            </span>
          </span>
        </div>

        <div className="flex items-center gap-4">
          <div className="hidden sm:flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-mono text-zinc-300">
            <span className="size-2 rounded-full bg-emerald-400 animate-pulse" />
            <span>vLLM Engine Ready</span>
          </div>

          <Link
            href="/dashboard"
            className="px-4 py-2 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white text-xs font-medium flex items-center gap-2 transition shadow-sm"
          >
            <span>Launch Console</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1 flex flex-col items-center justify-center px-6 py-20 text-center max-w-5xl mx-auto space-y-10">
        <div className="space-y-4">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-xs font-mono text-cyan-400">
            <Flame className="size-3.5" />
            <span>Continuous Batching & PagedAttention Orchestrator</span>
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-white leading-tight">
            Self-Hosted High-Performance <br className="hidden sm:inline" />
            <span className="bg-gradient-to-r from-cyan-400 via-indigo-400 to-purple-400 bg-clip-text text-transparent">
              LLM Inference Platform
            </span>
          </h1>

          <p className="max-w-2xl mx-auto text-zinc-400 text-sm sm:text-base leading-relaxed">
            A unified control plane to register models, manage multi-GPU serving instances,
            stream tokens via OpenAI-compatible endpoints, execute controlled load benchmarks,
            and monitor real-time KV cache telemetry.
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row items-center gap-3">
          <Link
            href="/dashboard"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-cyan-600 hover:bg-cyan-500 text-white font-medium text-sm flex items-center justify-center gap-2 transition shadow-lg shadow-cyan-900/20"
          >
            <span>Open Dashboard Console</span>
            <ArrowRight className="size-4" />
          </Link>

          <Link
            href="/dashboard/playground"
            className="w-full sm:w-auto px-6 py-3 rounded-xl bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-200 font-medium text-sm flex items-center justify-center gap-2 transition"
          >
            <Terminal className="size-4 text-cyan-400" />
            <span>Test in Playground</span>
          </Link>
        </div>

        {/* Core Architecture Matrix */}
        <div className="w-full grid grid-cols-1 md:grid-cols-3 gap-4 pt-12 text-left">
          <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition space-y-2.5">
            <div className="size-9 rounded-lg bg-cyan-500/10 text-cyan-400 flex items-center justify-center">
              <Server className="size-5" />
            </div>
            <h3 className="font-semibold text-white text-base">
              Multi-Engine Runtimes
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              First-class support for vLLM, SGLang, and TensorRT-LLM with automated
              tensor parallelism, chunked prefill, and dynamic memory allocation.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition space-y-2.5">
            <div className="size-9 rounded-lg bg-indigo-500/10 text-indigo-400 flex items-center justify-center">
              <Gauge className="size-5" />
            </div>
            <h3 className="font-semibold text-white text-base">
              Controlled Benchmarking
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Run synthetic load sweeps across concurrency tiers (1–128 clients).
              Accurately measure TTFT, ITL, P50/P99 latency, and tokens/sec throughput.
            </p>
          </div>

          <div className="p-5 rounded-2xl bg-zinc-900/60 border border-zinc-800 hover:border-zinc-700/80 transition space-y-2.5">
            <div className="size-9 rounded-lg bg-purple-500/10 text-purple-400 flex items-center justify-center">
              <Activity className="size-5" />
            </div>
            <h3 className="font-semibold text-white text-base">
              KV Cache & Telemetry
            </h3>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Monitor RadixAttention hit rates, GPU memory fragmentation, block manager
              allocations, and token consumption metrics in real-time.
            </p>
          </div>
        </div>

        {/* Lifecycle Flow */}
        <div className="w-full p-6 rounded-2xl bg-zinc-900/40 border border-zinc-800/80 text-left space-y-4">
          <p className="text-xs font-mono uppercase tracking-wider text-zinc-500">
            Engine Lifecycle Journey
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-4 lg:grid-cols-8 gap-2 text-center text-xs font-mono">
            {[
              "Register",
              "Configure",
              "Deploy",
              "Serve",
              "Stream",
              "Benchmark",
              "Monitor",
              "Analyze",
            ].map((step, idx) => (
              <div
                key={step}
                className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800 text-zinc-300 flex flex-col items-center justify-center gap-1"
              >
                <span className="text-[10px] text-cyan-400">0{idx + 1}</span>
                <span className="font-medium">{step}</span>
              </div>
            ))}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-zinc-800/80 py-6 px-6 text-center text-xs text-zinc-500">
        <p>InferX • Enterprise-Grade Self-Hosted LLM Inference Platform</p>
      </footer>
    </div>
  );
}
