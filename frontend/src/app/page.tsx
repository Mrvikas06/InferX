import Link from "next/link";
import { ArrowRight, Cpu, Gauge, Server, Terminal, Zap } from "lucide-react";

export default function Home() {
  return (
    <div className="min-h-screen bg-[#09090b] text-zinc-100 font-sans flex flex-col antialiased">
      {/* Quiet Navigation */}
      <header className="border-b border-zinc-800/80 px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="size-7 rounded-md bg-zinc-800 border border-zinc-700/80 flex items-center justify-center">
            <Zap className="size-4 text-zinc-200" />
          </div>
          <span className="font-medium tracking-tight text-white text-sm">
            InferX
          </span>
          <span className="text-[11px] font-mono text-zinc-500 pl-2 border-l border-zinc-800">
            v0.4.2
          </span>
        </div>

        <nav className="flex items-center gap-6 text-xs">
          <Link
            href="/dashboard/models"
            className="text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            Models
          </Link>
          <Link
            href="/dashboard/benchmarks"
            className="text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            Benchmarks
          </Link>
          <Link
            href="/dashboard/playground"
            className="text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            Playground
          </Link>
          <Link
            href="/dashboard"
            className="h-8 px-3 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 font-medium flex items-center gap-1.5 transition-colors"
          >
            <span>Launch console</span>
            <ArrowRight className="size-3.5" />
          </Link>
        </nav>
      </header>

      {/* Main Hero & Live Product Preview */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-6 py-16 space-y-16">
        <div className="max-w-3xl space-y-5">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900/60 text-xs font-mono text-zinc-400">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            <span>Engine ready • vLLM 0.6.3</span>
          </div>

          <h1 className="text-3xl sm:text-5xl font-semibold tracking-tight text-white leading-[1.15]">
            Self-hosted serving, continuous batching, and GPU instrumentation
          </h1>

          <p className="text-zinc-400 text-sm sm:text-base leading-relaxed max-w-2xl">
            A unified control plane to deploy open-weights LLMs across GPU clusters, route
            OpenAI-compatible chat completions, execute synthetic load benchmarks, and monitor
            KV cache allocations.
          </p>

          <div className="flex items-center gap-3 pt-2">
            <Link
              href="/dashboard"
              className="h-9 px-4 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 font-medium text-xs flex items-center gap-1.5 transition-colors"
            >
              <span>Open dashboard</span>
              <ArrowRight className="size-3.5" />
            </Link>

            <Link
              href="/dashboard/playground"
              className="h-9 px-4 rounded-md bg-zinc-900 hover:bg-zinc-800 border border-zinc-800 text-zinc-300 font-medium text-xs flex items-center gap-1.5 transition-colors"
            >
              <Terminal className="size-3.5 text-zinc-400" />
              <span>Inference playground</span>
            </Link>
          </div>
        </div>

        {/* Real Product Telemetry Preview */}
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/40 p-5 space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-3 border-b border-zinc-800/80 text-xs font-mono">
            <div className="flex items-center gap-2 text-zinc-300">
              <span className="size-2 rounded-full bg-emerald-500" />
              <span className="font-medium text-white">cluster-node-01</span>
              <span className="text-zinc-500">8x NVIDIA H100 80GB SXM5</span>
            </div>
            <div className="flex items-center gap-4 text-zinc-400">
              <span>Driver: 550.54.14</span>
              <span>CUDA: 12.4</span>
              <span>Memory: 482 / 640 GB</span>
            </div>
          </div>

          {/* Precision Metrics Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60">
              <div className="text-xs text-zinc-500">Serving throughput</div>
              <div className="text-xl font-medium text-white font-mono tabular-nums mt-1">
                5,420 <span className="text-xs text-zinc-500 font-sans">tok/s</span>
              </div>
              <div className="text-[11px] text-zinc-400 font-mono mt-1">
                p99: 42 tok/s
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60">
              <div className="text-xs text-zinc-500">Time to first token</div>
              <div className="text-xl font-medium text-white font-mono tabular-nums mt-1">
                14.8 <span className="text-xs text-zinc-500 font-sans">ms</span>
              </div>
              <div className="text-[11px] text-zinc-400 font-mono mt-1">
                itl: 6.8 ms
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60">
              <div className="text-xs text-zinc-500">Active deployments</div>
              <div className="text-xl font-medium text-white font-mono tabular-nums mt-1">
                4 <span className="text-xs text-zinc-500 font-sans">instances</span>
              </div>
              <div className="text-[11px] text-zinc-400 font-mono mt-1">
                tp=4 • vLLM + SGLang
              </div>
            </div>

            <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-950/60">
              <div className="text-xs text-zinc-500">KV cache hit rate</div>
              <div className="text-xl font-medium text-white font-mono tabular-nums mt-1">
                88.4%
              </div>
              <div className="text-[11px] text-zinc-400 font-mono mt-1">
                prefix caching active
              </div>
            </div>
          </div>

          {/* Active Serving Process Row */}
          <div className="rounded-lg border border-zinc-800/80 bg-zinc-950/60 p-3 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs font-mono">
            <div className="space-y-0.5">
              <div className="text-white font-medium">
                meta-llama/Llama-3.3-70B-Instruct
              </div>
              <div className="text-zinc-500 text-[11px]">
                Port 8000 • FP8 • Tensor Parallel 4 • PagedAttention
              </div>
            </div>
            <div className="flex items-center gap-4 text-zinc-400">
              <span className="tabular-nums">184.2 req/s</span>
              <span className="text-emerald-400">healthy</span>
              <Link
                href="/dashboard/playground"
                className="text-zinc-200 hover:text-white underline underline-offset-4"
              >
                test endpoint &rarr;
              </Link>
            </div>
          </div>
        </div>

        {/* Technical Architecture Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-4">
          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white text-sm font-medium">
              <Server className="size-4 text-zinc-400" />
              <span>Multi-engine runtimes</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Coordinate vLLM, SGLang, and TensorRT-LLM processes. Configure tensor
              parallelism, KV cache block size, and chunked prefill per model.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white text-sm font-medium">
              <Gauge className="size-4 text-zinc-400" />
              <span>Controlled benchmarks</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Run synthetic client sweeps across concurrency levels (1–128). Measure TTFT,
              inter-token latency, and tokens per second under Poisson distributions.
            </p>
          </div>

          <div className="space-y-2">
            <div className="flex items-center gap-2 text-white text-sm font-medium">
              <Cpu className="size-4 text-zinc-400" />
              <span>Hardware telemetry</span>
            </div>
            <p className="text-xs text-zinc-400 leading-relaxed">
              Real-time monitoring of GPU compute utilization, VRAM allocations,
              temperature, power draw, and memory bandwidth via NVIDIA DCGM.
            </p>
          </div>
        </div>
      </main>

      {/* Quiet Footer */}
      <footer className="border-t border-zinc-800/80 px-6 py-6 text-center text-xs text-zinc-500 font-mono">
        InferX • Self-hosted LLM inference control plane
      </footer>
    </div>
  );
}
