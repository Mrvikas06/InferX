"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Code2,
  Copy,
  Send,
  Sliders,
  Terminal,
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
}

const sampleModels = [
  {
    id: "meta-llama/Llama-3.3-70B-Instruct",
    name: "Llama 3.3 70B Instruct",
    port: 8000,
    engine: "vLLM",
  },
  {
    id: "deepseek-ai/DeepSeek-R1-Distill-Qwen-32B",
    name: "DeepSeek R1 Distill Qwen 32B",
    port: 8001,
    engine: "SGLang",
  },
  {
    id: "mistralai/Mistral-Small-24B-Instruct-2501",
    name: "Mistral Small 24B Instruct",
    port: 8002,
    engine: "vLLM",
  },
];

export default function PlaygroundPage() {
  const [selectedModel, setSelectedModel] = useState(sampleModels[0].id);
  const [systemPrompt, setSystemPrompt] = useState(
    "You are an expert AI software engineer and systems architect using InferX high-performance inference engine. Provide clear, optimal, and concise responses."
  );
  const [temperature, setTemperature] = useState(0.7);
  const [topP, setTopP] = useState(0.95);
  const [maxTokens, setMaxTokens] = useState(1024);
  const [isStreaming, setIsStreaming] = useState(true);
  const [inputMessage, setInputMessage] = useState("");
  const [isGenerating, setIsGenerating] = useState(false);
  const [showCurlModal, setShowCurlModal] = useState(false);
  const [copiedSnippet, setCopiedSnippet] = useState(false);

  const [messages, setMessages] = useState<Message[]>([
    {
      role: "assistant",
      content:
        "Hello! I am connected to the InferX inference cluster. You can test generation speed, latency, prompt formatting, and multi-turn chat in this playground.",
    },
  ]);

  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isGenerating]);

  const handleSend = () => {
    if (!inputMessage.trim() || isGenerating) return;

    const userText = inputMessage.trim();
    setInputMessage("");
    setMessages((prev) => [...prev, { role: "user", content: userText }]);
    setIsGenerating(true);

    // Simulated LLM generation with metrics
    const simulatedResponse =
      `InferX served this response using ${selectedModel} via dynamic PagedAttention. ` +
      `Here is a demonstration of low-latency token streaming with optimized KV cache reuse and sub-20ms TTFT.`;

    const assistantMsg: Message = {
      role: "assistant",
      content: "",
      metrics: {
        ttft: 14.2,
        tokensPerSec: 108.5,
        totalTokens: 42,
      },
    };

    let charIndex = 0;
    const interval = setInterval(() => {
      charIndex += 4;
      if (charIndex >= simulatedResponse.length) {
        clearInterval(interval);
        assistantMsg.content = simulatedResponse;
        setMessages((prev) => [...prev.slice(0, -1), assistantMsg]);
        setIsGenerating(false);
      } else {
        assistantMsg.content = simulatedResponse.slice(0, charIndex);
        setMessages((prev) => {
          const lastMsg = prev[prev.length - 1];
          if (lastMsg && lastMsg.role === "assistant" && lastMsg.metrics) {
            return [...prev.slice(0, -1), { ...assistantMsg }];
          }
          return [...prev, { ...assistantMsg }];
        });
      }
    }, 30);
  };

  const handleClear = () => {
    setMessages([]);
  };

  const activeModelObj =
    sampleModels.find((m) => m.id === selectedModel) || sampleModels[0];

  const curlCode = `curl http://localhost:${activeModelObj.port}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer inferx_dev_key" \\
  -d '{
    "model": "${selectedModel}",
    "messages": [
      {"role": "system", "content": "${systemPrompt.replace(/"/g, '\\"')}"},
      {"role": "user", "content": "Explain KV Cache optimization in vLLM"}
    ],
    "temperature": ${temperature},
    "top_p": ${topP},
    "max_tokens": ${maxTokens},
    "stream": ${isStreaming}
  }'`;

  return (
    <div className="space-y-4">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-zinc-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            LLM Inference Playground
          </h1>
          <p className="text-zinc-400 text-xs mt-0.5">
            Test prompt execution, token generation speed, and API parameters in real time.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCurlModal(true)}
            className="px-3 py-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition"
          >
            <Code2 className="size-3.5 text-cyan-400" />
            <span>Export cURL</span>
          </button>
          <button
            onClick={handleClear}
            className="p-1.5 rounded-lg bg-zinc-900 border border-zinc-800 hover:border-zinc-700 text-zinc-400 hover:text-white transition"
            title="Clear Chat History"
          >
            <Trash2 className="size-4" />
          </button>
        </div>
      </div>

      {/* Main Grid: Settings Sidebar + Chat Viewport */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-13rem)] min-h-[550px]">
        {/* Left Parameters Sidebar */}
        <div className="lg:col-span-1 bg-zinc-900/60 border border-zinc-800 rounded-xl p-4 flex flex-col justify-between overflow-y-auto space-y-4 text-xs">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-zinc-300 font-semibold pb-2 border-b border-zinc-800">
              <Sliders className="size-4 text-cyan-400" />
              <span>Inference Parameters</span>
            </div>

            {/* Model Selector */}
            <div>
              <label className="block text-zinc-400 font-medium mb-1">
                Active Endpoint Model
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg px-2.5 py-1.5 text-zinc-200 focus:outline-none focus:border-cyan-500 font-mono text-xs"
              >
                {sampleModels.map((m) => (
                  <option key={m.id} value={m.id}>
                    {m.name} ({m.engine})
                  </option>
                ))}
              </select>
            </div>

            {/* System Prompt */}
            <div>
              <label className="block text-zinc-400 font-medium mb-1">
                System Prompt
              </label>
              <textarea
                rows={4}
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-lg p-2 text-zinc-200 text-xs focus:outline-none focus:border-cyan-500 font-mono resize-none"
              />
            </div>

            {/* Temperature */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Temperature</span>
                <span className="font-mono text-cyan-400">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 h-1 bg-zinc-800 rounded-lg cursor-pointer"
              />
            </div>

            {/* Top P */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Top P</span>
                <span className="font-mono text-cyan-400">{topP}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(parseFloat(e.target.value))}
                className="w-full accent-cyan-500 h-1 bg-zinc-800 rounded-lg cursor-pointer"
              />
            </div>

            {/* Max Output Tokens */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Max Output Tokens</span>
                <span className="font-mono text-cyan-400">{maxTokens}</span>
              </div>
              <input
                type="range"
                min="64"
                max="4096"
                step="64"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full accent-cyan-500 h-1 bg-zinc-800 rounded-lg cursor-pointer"
              />
            </div>

            {/* Stream Toggle */}
            <div className="flex items-center justify-between pt-2">
              <span className="text-zinc-400">Stream Output</span>
              <button
                type="button"
                onClick={() => setIsStreaming(!isStreaming)}
                className={`relative inline-flex h-5 w-9 items-center rounded-full transition-colors ${
                  isStreaming ? "bg-cyan-600" : "bg-zinc-800"
                }`}
              >
                <span
                  className={`inline-block size-3.5 transform rounded-full bg-white transition-transform ${
                    isStreaming ? "translate-x-4" : "translate-x-1"
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="p-2.5 rounded-lg bg-zinc-950 border border-zinc-800/80 text-[11px] text-zinc-500">
            <span className="text-zinc-400 font-medium block mb-0.5">
              Serving Node:
            </span>
            <span>Local Engine (Port {activeModelObj.port})</span>
          </div>
        </div>

        {/* Right Chat & Output Area */}
        <div className="lg:col-span-3 bg-zinc-900/60 border border-zinc-800 rounded-xl flex flex-col justify-between overflow-hidden">
          {/* Chat Messages Log */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.length === 0 && (
              <div className="h-full flex flex-col items-center justify-center text-center p-8 text-zinc-500">
                <Terminal className="size-10 text-zinc-600 mb-2" />
                <p className="text-sm font-medium text-zinc-300">
                  Ready to test inference
                </p>
                <p className="text-xs max-w-sm mt-1">
                  Type a prompt below to evaluate latency, throughput, and generation accuracy.
                </p>
              </div>
            )}

            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3 text-xs ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="size-7 rounded-lg bg-cyan-600/20 text-cyan-400 flex items-center justify-center shrink-0 border border-cyan-500/30">
                    <Bot className="size-4" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-xl px-4 py-2.5 space-y-2 ${
                    msg.role === "user"
                      ? "bg-cyan-600 text-white shadow-sm"
                      : "bg-zinc-950 border border-zinc-800/80 text-zinc-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </p>

                  {/* Telemetry pill */}
                  {msg.metrics && (
                    <div className="pt-2 border-t border-zinc-800/80 flex items-center gap-3 text-[10px] font-mono text-zinc-400">
                      <span className="flex items-center gap-1 text-emerald-400">
                        <Zap className="size-3" />
                        TTFT: {msg.metrics.ttft}ms
                      </span>
                      <span>Rate: {msg.metrics.tokensPerSec} tok/s</span>
                      <span>Total: {msg.metrics.totalTokens} tokens</span>
                    </div>
                  )}
                </div>

                {msg.role === "user" && (
                  <div className="size-7 rounded-lg bg-zinc-800 text-zinc-300 flex items-center justify-center shrink-0 border border-zinc-700">
                    <User className="size-4" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-3 bg-zinc-950/80 border-t border-zinc-800">
            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-xl px-3 py-2 focus-within:border-cyan-500 transition">
              <textarea
                rows={1}
                placeholder="Ask or prompt the model (Shift+Enter for new line)..."
                value={inputMessage}
                onChange={(e) => setInputMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
                className="flex-1 bg-transparent text-xs text-zinc-100 placeholder-zinc-500 focus:outline-none resize-none font-sans"
              />
              <button
                onClick={handleSend}
                disabled={!inputMessage.trim() || isGenerating}
                className="p-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 disabled:opacity-40 text-white transition shrink-0"
              >
                <Send className="size-3.5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Export cURL Modal */}
      {showCurlModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-zinc-900 border border-zinc-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <h3 className="font-semibold text-white text-base flex items-center gap-2">
                <Terminal className="size-4 text-cyan-400" />
                API Request Snippet (OpenAI Compatible)
              </h3>
              <button
                onClick={() => setShowCurlModal(false)}
                className="text-zinc-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div className="relative">
              <pre className="p-4 rounded-xl bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-300 font-mono overflow-x-auto leading-relaxed">
                {curlCode}
              </pre>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(curlCode);
                  setCopiedSnippet(true);
                  setTimeout(() => setCopiedSnippet(false), 2000);
                }}
                className="absolute top-2.5 right-2.5 px-2.5 py-1 rounded bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs flex items-center gap-1.5 transition font-sans"
              >
                <Copy className="size-3" />
                <span>{copiedSnippet ? "Copied!" : "Copy cURL"}</span>
              </button>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowCurlModal(false)}
                className="px-4 py-1.5 rounded-lg bg-zinc-800 hover:bg-zinc-700 text-zinc-300 text-xs font-medium"
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
