"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Bot,
  Code2,
  Copy,
  Send,
  Sliders,
  Trash2,
  User,
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
    "You are an AI inference systems engineer using InferX. Provide clear, concise, and technically accurate responses."
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
        "Connected to InferX serving cluster. Test model completions, token streaming rate, and latency metrics.",
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

    const simulatedResponse =
      `InferX served this response using ${selectedModel} via dynamic continuous batching. ` +
      `PagedAttention KV cache allocation achieved sub-20ms TTFT with zero memory fragmentation.`;

    const assistantMsg: Message = {
      role: "assistant",
      content: "",
      metrics: {
        ttft: 14.2,
        tokensPerSec: 108.5,
        totalTokens: 38,
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
    }, 25);
  };

  const handleClear = () => {
    setMessages([]);
  };

  const activeModelObj =
    sampleModels.find((m) => m.id === selectedModel) || sampleModels[0];

  const curlCode = `curl http://localhost:${activeModelObj.port}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
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
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-zinc-800/80">
        <div>
          <h1 className="text-xl font-semibold text-white tracking-tight">
            Inference playground
          </h1>
          <p className="text-xs text-zinc-400 mt-0.5">
            Evaluate prompt completions, token streaming rates, and parameters
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setShowCurlModal(true)}
            className="h-8 px-3 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Code2 className="size-3.5 text-zinc-400" />
            <span>Export cURL</span>
          </button>
          <button
            onClick={handleClear}
            className="h-8 w-8 rounded-md border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-400 hover:text-white flex items-center justify-center transition-colors"
            title="Clear history"
          >
            <Trash2 className="size-3.5" />
          </button>
        </div>
      </div>

      {/* Grid: Parameters + Chat */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4 h-[calc(100vh-14rem)] min-h-[520px]">
        {/* Parameters Panel */}
        <div className="lg:col-span-1 border border-zinc-800/80 bg-zinc-900/40 rounded-lg p-4 flex flex-col justify-between overflow-y-auto space-y-4 text-xs">
          <div className="space-y-4">
            <div className="flex items-center gap-2 text-white font-medium pb-2 border-b border-zinc-800/80">
              <Sliders className="size-3.5 text-zinc-400" />
              <span>Parameters</span>
            </div>

            {/* Model */}
            <div>
              <label className="block text-zinc-400 mb-1">
                Model endpoint
              </label>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md px-2.5 py-1.5 text-zinc-200 focus:outline-none focus:border-zinc-700 font-mono text-xs"
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
              <label className="block text-zinc-400 mb-1">
                System instructions
              </label>
              <textarea
                rows={3}
                value={systemPrompt}
                onChange={(e) => setSystemPrompt(e.target.value)}
                className="w-full bg-zinc-950 border border-zinc-800 rounded-md p-2 text-zinc-200 text-xs focus:outline-none focus:border-zinc-700 font-mono resize-none"
              />
            </div>

            {/* Temperature */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Temperature</span>
                <span className="font-mono tabular-nums text-zinc-200">{temperature}</span>
              </div>
              <input
                type="range"
                min="0"
                max="2"
                step="0.05"
                value={temperature}
                onChange={(e) => setTemperature(parseFloat(e.target.value))}
                className="w-full accent-zinc-200 h-1 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Top P */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Top P</span>
                <span className="font-mono tabular-nums text-zinc-200">{topP}</span>
              </div>
              <input
                type="range"
                min="0"
                max="1"
                step="0.05"
                value={topP}
                onChange={(e) => setTopP(parseFloat(e.target.value))}
                className="w-full accent-zinc-200 h-1 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Max Tokens */}
            <div className="space-y-1">
              <div className="flex justify-between text-zinc-400">
                <span>Max tokens</span>
                <span className="font-mono tabular-nums text-zinc-200">{maxTokens}</span>
              </div>
              <input
                type="range"
                min="64"
                max="4096"
                step="64"
                value={maxTokens}
                onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                className="w-full accent-zinc-200 h-1 bg-zinc-800 rounded cursor-pointer"
              />
            </div>

            {/* Stream */}
            <div className="flex items-center justify-between pt-1">
              <span className="text-zinc-400">Stream tokens</span>
              <button
                type="button"
                onClick={() => setIsStreaming(!isStreaming)}
                className={`relative inline-flex h-4 w-8 items-center rounded-full transition-colors ${
                  isStreaming ? "bg-zinc-200" : "bg-zinc-800"
                }`}
              >
                <span
                  className={`inline-block size-3 transform rounded-full transition-transform ${
                    isStreaming ? "translate-x-4 bg-zinc-950" : "translate-x-0.5 bg-zinc-400"
                  }`}
                />
              </button>
            </div>
          </div>

          <div className="text-[11px] text-zinc-500 font-mono">
            localhost:{activeModelObj.port}
          </div>
        </div>

        {/* Chat Area */}
        <div className="lg:col-span-3 border border-zinc-800/80 bg-zinc-900/40 rounded-lg flex flex-col justify-between overflow-hidden">
          {/* Messages */}
          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {messages.map((msg, index) => (
              <div
                key={index}
                className={`flex gap-3 text-xs ${
                  msg.role === "user" ? "justify-end" : "justify-start"
                }`}
              >
                {msg.role === "assistant" && (
                  <div className="size-6 rounded bg-zinc-800 border border-zinc-700/80 text-zinc-300 flex items-center justify-center shrink-0">
                    <Bot className="size-3.5" />
                  </div>
                )}

                <div
                  className={`max-w-[85%] rounded-lg px-3.5 py-2.5 space-y-2 ${
                    msg.role === "user"
                      ? "bg-zinc-800 border border-zinc-700/80 text-white"
                      : "bg-zinc-950 border border-zinc-800/80 text-zinc-200"
                  }`}
                >
                  <p className="whitespace-pre-wrap leading-relaxed">
                    {msg.content}
                  </p>

                  {/* Telemetry pill */}
                  {msg.metrics && (
                    <div className="pt-2 border-t border-zinc-800/80 flex items-center gap-3 text-[10px] font-mono text-zinc-500">
                      <span className="text-zinc-300 tabular-nums">
                        TTFT: {msg.metrics.ttft}ms
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
                  <div className="size-6 rounded bg-zinc-800 border border-zinc-700/80 text-zinc-300 flex items-center justify-center shrink-0">
                    <User className="size-3.5" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </div>

          {/* Input Box */}
          <div className="p-3 bg-zinc-950/60 border-t border-zinc-800/80">
            <div className="flex items-center gap-2 bg-zinc-900 border border-zinc-800 rounded-md px-3 py-2 focus-within:border-zinc-700 transition-colors">
              <textarea
                rows={1}
                placeholder="Submit prompt..."
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
                className="h-7 px-2.5 rounded bg-zinc-100 hover:bg-white disabled:opacity-40 text-zinc-950 text-xs font-medium flex items-center gap-1 transition-colors shrink-0"
              >
                <span>Send</span>
                <Send className="size-3" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* cURL Modal */}
      {showCurlModal && (
        <div className="fixed inset-0 z-50 bg-black/70 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="w-full max-w-xl bg-zinc-900 border border-zinc-800 rounded-lg p-5 space-y-4">
            <div className="flex items-center justify-between pb-2 border-b border-zinc-800">
              <h3 className="font-medium text-white text-sm">
                cURL request snippet
              </h3>
              <button
                onClick={() => setShowCurlModal(false)}
                className="text-zinc-400 hover:text-white text-xs"
              >
                ✕
              </button>
            </div>

            <div className="relative">
              <pre className="p-3.5 rounded bg-zinc-950 border border-zinc-800 text-[11px] text-zinc-300 font-mono overflow-x-auto leading-relaxed">
                {curlCode}
              </pre>
              <button
                onClick={() => {
                  navigator.clipboard?.writeText(curlCode);
                  setCopiedSnippet(true);
                  setTimeout(() => setCopiedSnippet(false), 1500);
                }}
                className="absolute top-2 right-2 px-2 py-1 rounded border border-zinc-800 bg-zinc-900 hover:bg-zinc-800 text-zinc-300 text-xs flex items-center gap-1 transition-colors"
              >
                <Copy className="size-3" />
                <span>{copiedSnippet ? "Copied" : "Copy"}</span>
              </button>
            </div>

            <div className="flex justify-end">
              <button
                onClick={() => setShowCurlModal(false)}
                className="px-3 py-1.5 rounded-md border border-zinc-800 bg-zinc-900 text-zinc-300 text-xs"
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
