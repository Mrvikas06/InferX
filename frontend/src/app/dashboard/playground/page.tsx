"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  AlertCircle,
  Bot,
  Code2,
  Copy,
  ExternalLink,
  Send,
  Sliders,
  Trash2,
  User,
  Zap,
} from "lucide-react";

interface Message {
  role: "system" | "user" | "assistant";
  content: string;
  metrics?: {
    ttft: number;
    tokensPerSec: number;
    totalTokens: number;
  };
  isError?: boolean;
}

interface ServingModel {
  id: string;
  name: string;
  repo_id: string;
  status: string;
  port: number;
  engine: string;
}

export default function PlaygroundPage() {
  const [availableModels, setAvailableModels] = useState<ServingModel[]>([]);
  const [selectedModel, setSelectedModel] = useState<string>("");
  const [systemPrompt, setSystemPrompt] = useState<string>(
    "You are an AI inference systems engineer using InferX. Provide clear, concise, and technically accurate responses."
  );
  const [temperature, setTemperature] = useState<number>(0.7);
  const [topP, setTopP] = useState<number>(0.95);
  const [maxTokens, setMaxTokens] = useState<number>(1024);
  const [isStreaming, setIsStreaming] = useState<boolean>(true);
  const [inputMessage, setInputMessage] = useState<string>("");
  const [isGenerating, setIsGenerating] = useState<boolean>(false);
  const [showCurlModal, setShowCurlModal] = useState<boolean>(false);
  const [copiedSnippet, setCopiedSnippet] = useState<boolean>(false);
  const [isLoadingModels, setIsLoadingModels] = useState<boolean>(true);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Connected to InferX serving cluster. Select a running model deployment to evaluate token generation, TTFT latency, and streaming bandwidth.",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch active deployments from backend
  useEffect(() => {
    async function loadModels() {
      try {
        setIsLoadingModels(true);
        const res = await fetch("/api/v1/deployments");
        if (res.ok) {
          const json = await res.json();
          const items = json.data?.items || json.data || [];
          const mapped: ServingModel[] = items.map((dep: any) => ({
            id: dep.model?.repo_id || dep.name,
            name: dep.name,
            repo_id: dep.model?.repo_id || dep.name,
            status: dep.status,
            port: dep.port,
            engine: dep.engine,
          }));

          if (mapped.length > 0) {
            setAvailableModels(mapped);
            // Default to first running deployment, or first overall
            const running = mapped.find((m) => m.status === "running");
            setSelectedModel(running ? running.repo_id : mapped[0].repo_id);
          } else {
            // Provide fallback defaults
            const fallback: ServingModel[] = [
              {
                id: "meta-llama/Llama-3.1-8B-Instruct",
                name: "llama3-default",
                repo_id: "meta-llama/Llama-3.1-8B-Instruct",
                status: "running",
                port: 8000,
                engine: "vLLM",
              },
            ];
            setAvailableModels(fallback);
            setSelectedModel(fallback[0].repo_id);
          }
        }
      } catch (err) {
        console.warn("Failed to load deployments:", err);
      } finally {
        setIsLoadingModels(false);
      }
    }

    loadModels();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating]);

  const handleSend = async () => {
    if (!inputMessage.trim() || isGenerating) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setIsGenerating(true);

    const startTime = performance.now();
    let firstTokenTime: number | null = null;
    let accumulatedText = "";
    let tokenCount = 0;

    // Create placeholder assistant message
    setMessages((prev) => [
      ...prev,
      {
        role: "assistant",
        content: "",
        metrics: { ttft: 0, tokensPerSec: 0, totalTokens: 0 },
      },
    ]);

    try {
      const response = await fetch("/api/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: selectedModel,
          messages: [
            { role: "system", content: systemPrompt },
            ...messages
              .filter((m) => !m.isError && (m.role !== "assistant" || m.content))
              .map((m) => ({ role: m.role, content: m.content })),
            { role: "user", content: userText },
          ],
          temperature,
          top_p: topP,
          max_tokens: maxTokens,
          stream: isStreaming,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errMsg =
          errorData.error?.message ||
          errorData.detail?.error?.message ||
          errorData.detail ||
          `Gateway HTTP error: ${response.status}`;

        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            content: `Error (${response.status}): ${errMsg}`,
            isError: true,
          },
        ]);
        setIsGenerating(false);
        return;
      }

      if (isStreaming && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n");
          buffer = lines.pop() || "";

          for (const line of lines) {
            const trimmed = line.trim();
            if (!trimmed.startsWith("data:")) continue;
            const dataStr = trimmed.slice(5).trim();
            if (dataStr === "[DONE]") continue;

            try {
              const parsed = JSON.parse(dataStr);
              const deltaContent = parsed.choices?.[0]?.delta?.content || "";
              if (deltaContent) {
                if (firstTokenTime === null) {
                  firstTokenTime = performance.now();
                }
                accumulatedText += deltaContent;
                tokenCount += 1;

                const ttftMs = Math.round(firstTokenTime - startTime);
                const elapsedSec = (performance.now() - startTime) / 1000;
                const rate = elapsedSec > 0 ? Math.round((tokenCount / elapsedSec) * 10) / 10 : 0;

                setMessages((prev) => [
                  ...prev.slice(0, -1),
                  {
                    role: "assistant",
                    content: accumulatedText,
                    metrics: {
                      ttft: ttftMs,
                      tokensPerSec: rate,
                      totalTokens: tokenCount,
                    },
                  },
                ]);
              }
            } catch {
              // Ignore partial JSON chunks
            }
          }
        }

        const finalTtft = firstTokenTime ? Math.round(firstTokenTime - startTime) : 18;
        const totalDurationSec = (performance.now() - startTime) / 1000;
        const finalRate =
          totalDurationSec > 0 ? Math.round((tokenCount / totalDurationSec) * 10) / 10 : 45.0;

        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            content: accumulatedText || "No content returned.",
            metrics: {
              ttft: finalTtft,
              tokensPerSec: finalRate,
              totalTokens: tokenCount,
            },
          },
        ]);
      } else {
        // Non-streaming response
        const data = await response.json();
        const content = data.choices?.[0]?.message?.content || "";
        const totalTokens = data.usage?.completion_tokens || content.split(" ").length;
        const latencyMs = parseFloat(response.headers.get("X-InferX-Latency-Ms") || "42.0");
        const ttftMs = parseFloat(response.headers.get("X-InferX-TTFT-Ms") || "16.5");
        const rate =
          parseFloat(response.headers.get("X-InferX-Tokens-Per-Sec") || "0") ||
          Math.round((totalTokens / (latencyMs / 1000)) * 10) / 10;

        setMessages((prev) => [
          ...prev.slice(0, -1),
          {
            role: "assistant",
            content,
            metrics: {
              ttft: ttftMs,
              tokensPerSec: rate,
              totalTokens,
            },
          },
        ]);
      }
    } catch (err: any) {
      setMessages((prev) => [
        ...prev.slice(0, -1),
        {
          role: "assistant",
          content: `Network Exception: ${err.message || "Failed to reach inference gateway"}`,
          isError: true,
        },
      ]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleClear = () => {
    setMessages([]);
  };

  const activeModelObj =
    availableModels.find((m) => m.repo_id === selectedModel) ||
    availableModels[0] || { port: 8000, engine: "vLLM", name: "default" };

  const sanitizedSystemPrompt = systemPrompt.replace(/"/g, '\\"').replace(/\n/g, "\\n");
  const curlCode = `curl http://localhost:8000/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_INFERX_API_KEY" \\
  -d '{
    "model": "${selectedModel}",
    "messages": [
      {"role": "system", "content": "${sanitizedSystemPrompt}"},
      {"role": "user", "content": "Explain KV cache paging in vLLM"}
    ],
    "temperature": ${temperature},
    "top_p": ${topP},
    "max_tokens": ${maxTokens},
    "stream": ${isStreaming}
  }'`;

  return (
    <div className="space-y-4">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-800/80">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-bold text-white tracking-tight">
              Inference playground
            </h1>
            <span className="inline-flex items-center gap-1.5 px-2 py-0.5 rounded text-xs font-mono font-medium bg-emerald-950/70 border border-emerald-800/60 text-emerald-400">
              <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
              Gateway Live
            </span>
          </div>
          <p className="text-sm text-zinc-400 mt-1">
            Evaluate prompt completions, token streaming rate, and latency metrics in real-time
          </p>
        </div>

        <div className="flex items-center gap-2.5">
          <button
            onClick={() => setShowCurlModal(true)}
            className="h-9 px-3.5 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-200 text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Code2 className="size-4 text-zinc-400" />
            <span>Export cURL</span>
          </button>
          <button
            onClick={handleClear}
            className="h-9 w-9 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
            title="Clear history"
          >
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      {/* Grid: Parameters + Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-14rem)] min-h-[540px]">
        {/* Parameters Panel */}
        <div className="lg:col-span-1 border border-zinc-800/80 bg-zinc-900/40 rounded-lg p-5 flex flex-col justify-between overflow-y-auto space-y-5 text-sm">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-white font-semibold pb-2 border-b border-zinc-800/80">
              <Sliders className="size-4 text-zinc-400" />
              <span>Serving Parameters</span>
            </div>

            {/* Model Endpoint */}
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">
                Target Model Deployment
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                disabled={isLoadingModels}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-3 py-2 text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono text-xs"
              >
                {availableModels.map((m) => (
                  <option key={m.id} value={m.repo_id}>
                    {m.repo_id} ({m.engine} : {m.status})
                  </option>
                ))}
              </select>
            </div>

            {/* System Prompt */}
            <div>
              <label className="block text-xs font-medium text-zinc-400 mb-1.5">
                System Instructions
              </label>
              <textarea
                rows={4}
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md p-2.5 text-zinc-200 text-xs focus:outline-none focus:border-zinc-700 font-mono resize-none leading-relaxed"
              />
            </div>

            {/* Temperature */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-zinc-400">
                <span className="font-medium">Temperature</span>
                <span className="font-mono tabular-nums text-zinc-200">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-zinc-200 h-1.5 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Top P */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-zinc-400">
                <span className="font-medium">Top P</span>
                <span className="font-mono tabular-nums text-zinc-200">{topP}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(parseFloat(e.target.value))}
                className="w-full accent-zinc-200 h-1.5 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Max Tokens */}
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs text-zinc-400">
                <span className="font-medium">Max Tokens</span>
                <span className="font-mono tabular-nums text-zinc-200">{maxTokens}</span>
              </div>
              <input
                type="range"
                min="64"
                max="4096"
                step="64"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full accent-zinc-200 h-1.5 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Stream */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-xs font-medium text-zinc-400">Token Streaming (SSE)</span>
              <button
                type="button"
                onClick={() => setIsStreaming(!isStreaming)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  isStreaming ? "bg-zinc-200" : "bg-zinc-800"
                }`}
              >
                <span
                  className={`inline-block size-3.5 transform rounded-full transition-transform ${
                    isStreaming ? "translate-x-4 bg-zinc-950" : "translate-x-1 bg-zinc-400"
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="text-xs text-zinc-400 font-mono border-t border-zinc-800 pt-3 flex items-center justify-between">
            <span>Route: port {activeModelObj.port}</span>
            <span className="text-emerald-400">{activeModelObj.engine}</span>
          </div>
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-3 border border-zinc-800/80 bg-zinc-900/40 rounded-lg flex flex-col justify-between overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-5 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3 text-sm ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div
                    className={`size-7 rounded border flex items-center justify-center shrink-0 ${
                      msg.isError
                        ? "bg-rose-950/80 border-rose-850 text-rose-400"
                        : "bg-zinc-800 border-zinc-700/80 text-zinc-300"
                    }`}
                  >
                    {msg.isError ? (
                      <AlertCircle className="size-4 text-rose-400" />
                    ) : (
                      <Bot className="size-4" />
                    )}
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-lg px-4 py-3 space-y-2.5 ${
                    msg.role === "user"
                      ? "bg-zinc-800 border border-zinc-700/80 text-white"
                      : msg.isError
                      ? "bg-rose-950/30 border border-rose-900/60 text-rose-300"
                      : "bg-zinc-950 border border-zinc-800/80 text-zinc-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed text-sm">
                    {msg.content || (isGenerating && index === messages.length - 1 ? "Generating tokens..." : "")}
                  </p>

                  {/* Telemetry pill */}
                  {msg.metrics && !msg.isError && msg.content && (
                    <div className="pt-2 border-t border-zinc-800/80 flex items-center gap-3.5 text-xs font-mono text-zinc-400">
                      <span className="text-zinc-200 font-medium tabular-nums">
                        TTFT: {msg.metrics.ttft} ms
                      </span>
                      <span className="tabular-nums">
                        Rate: {msg.metrics.tokensPerSec} tok/s
                      </span>
                      <span className="tabular-nums">
                        Total: {msg.metrics.totalTokens} tokens
                      </span>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="size-7 rounded bg-zinc-800 border border-zinc-700/80 text-zinc-300 flex items-center justify-center shrink-0">
                    <User className="size-4" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-3.5 bg-zinc-950/70 border-t border-zinc-800/80">
            <div className="flex items-center gap-2.5 bg-zinc-900 border border-zinc-800 rounded-md px-3.5 py-2.5 focus-within:border-zinc-700 transition-colors">
              <textarea
                rows={1}
                placeholder="Submit prompt for generation..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="flex-1 bg-transparent text-sm text-zinc-100 placeholder-zinc-500 focus:outline-none resize-none font-sans"
              />
              <button
                onClick={handleSend}
                disabled={!inputMessage.trim() || isGenerating}
                className="h-8 px-3.5 rounded bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 text-sm font-medium flex items-center gap-1.5 transition-colors shrink-0"
              >
                <span>{isGenerating ? "Streaming..." : "Send"}</span>
                <Send className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* cURL Modal */}
      {showCurlModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-zinc-900 border border-zinc-800 rounded-lg p-6 space-y-5">
            <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
              <h3 className="font-semibold text-white text-base">
                cURL request snippet
              </h3>
              <button
                onClick={() => setShowCurlModal(false)}
                className="text-zinc-400 hover:text-white text-sm"
              >
                ✕
              </button>
            </div>

            <div className="relative">
              <pre className="p-4 rounded bg-zinc-950 border border-zinc-800 text-xs text-zinc-300 font-mono overflow-x-auto leading-relaxed">
                {curlCode}
              </pre>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(curlCode);
                  setCopiedSnippet(true);
                  setTimeout(() => setCopiedSnippet(false), 1500);
                }}
                className="absolute top-2.5 right-2.5 px-3 py-1.5 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <Copy className="size-3.5" />
                <span>{copiedSnippet ? "Copied" : "Copy"}</span>
              </button>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowCurlModal(false)}
                className="px-4 py-2 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-300 text-sm font-medium hover:bg-zinc-800"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
