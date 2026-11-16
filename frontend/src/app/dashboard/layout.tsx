"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Box,
  Server,
  Terminal,
  Gauge,
  LineChart,
  Zap,
  Cpu,
  Menu,
  X,
  ChevronRight,
  ExternalLink,
  ShieldCheck,
  Activity,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  badge?: string;
}

const navItems: NavItem[] = [
  {
    title: "Overview",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    title: "Models",
    href: "/dashboard/models",
    icon: Box,
    badge: "12",
  },
  {
    title: "Deployments",
    href: "/dashboard/deployments",
    icon: Server,
    badge: "Active",
  },
  {
    title: "Playground",
    href: "/dashboard/playground",
    icon: Terminal,
  },
  {
    title: "Benchmarks",
    href: "/dashboard/benchmarks",
    icon: Gauge,
  },
  {
    title: "Analytics",
    href: "/dashboard/analytics",
    icon: LineChart,
  },
];

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const currentPageTitle =
    navItems.find((item) =>
      item.href === "/dashboard"
        ? pathname === "/dashboard"
        : pathname.startsWith(item.href)
    )?.title || "Dashboard";

  return (
    <div className="min-h-screen bg-zinc-950 text-zinc-100 flex flex-col antialiased">
      {/* Top Header */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur-md px-4 sm:px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-lg text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>

          <Link href="/dashboard" className="flex items-center gap-2 group">
            <div className="size-8 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <Zap className="size-4 text-white font-bold" />
            </div>
            <div className="flex flex-col">
              <span className="font-bold tracking-tight text-white flex items-center gap-1.5 text-base">
                Infer<span className="text-cyan-400">X</span>
                <span className="text-[10px] font-mono px-1.5 py-0.5 rounded bg-zinc-800 text-zinc-400 border border-zinc-700/50">
                  v0.4.2
                </span>
              </span>
            </div>
          </Link>

          <div className="hidden sm:flex items-center gap-2 text-zinc-500 text-sm ml-4 pl-4 border-l border-zinc-800">
            <span>Console</span>
            <ChevronRight className="size-3.5 text-zinc-600" />
            <span className="text-zinc-200 font-medium">{currentPageTitle}</span>
          </div>
        </div>

        <div className="flex items-center gap-3 sm:gap-4">
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-mono">
            <span className="size-1.5 rounded-full bg-emerald-400 animate-pulse" />
            <span>Engine: vLLM 0.6.3 (Online)</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded-full bg-zinc-900 border border-zinc-800 text-zinc-300 text-xs">
            <Cpu className="size-3.5 text-cyan-400" />
            <span>8x H100 SXM5</span>
          </div>

          <Link
            href="/dashboard/playground"
            className="text-xs px-3 py-1.5 rounded-lg bg-cyan-600 hover:bg-cyan-500 text-white font-medium transition shadow-sm flex items-center gap-1.5"
          >
            <Terminal className="size-3.5" />
            <span className="hidden sm:inline">Open</span> Playground
          </Link>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Sidebar Desktop */}
        <aside className="hidden md:flex flex-col w-64 border-r border-zinc-800/80 bg-zinc-950/60 p-4 shrink-0 justify-between">
          <div className="space-y-6">
            <div>
              <p className="px-3 text-[11px] font-semibold tracking-wider uppercase text-zinc-500 mb-2 font-mono">
                Platform
              </p>
              <nav className="space-y-1">
                {navItems.map((item) => {
                  const isActive =
                    item.href === "/dashboard"
                      ? pathname === "/dashboard"
                      : pathname.startsWith(item.href);
                  const Icon = item.icon;

                  return (
                    <Link
                      key={item.href}
                      href={item.href}
                      className={`flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                        isActive
                          ? "bg-zinc-800 text-cyan-400 shadow-sm"
                          : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon
                          className={`size-4 ${
                            isActive ? "text-cyan-400" : "text-zinc-400"
                          }`}
                        />
                        <span>{item.title}</span>
                      </div>
                      {item.badge && (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-full font-mono ${
                            isActive
                              ? "bg-cyan-950 text-cyan-300 border border-cyan-800/60"
                              : "bg-zinc-900 text-zinc-400 border border-zinc-800"
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>

            <div>
              <p className="px-3 text-[11px] font-semibold tracking-wider uppercase text-zinc-500 mb-2 font-mono">
                System Health
              </p>
              <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800/80 space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400 flex items-center gap-1.5">
                    <Activity className="size-3.5 text-emerald-400" />
                    GPU Cluster
                  </span>
                  <span className="text-emerald-400 font-mono text-[11px]">99.98%</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">VRAM Alloc</span>
                  <span className="text-zinc-200 font-mono">482 / 640 GB</span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-gradient-to-r from-cyan-500 to-indigo-500 h-1.5 rounded-full"
                    style={{ width: "75%" }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] pt-1 text-zinc-400 border-t border-zinc-800/60">
                  <span>Inference QPS</span>
                  <span className="text-zinc-200 font-mono font-medium">3,420 rps</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="pt-4 border-t border-zinc-800/80 flex flex-col gap-2">
            <a
              href="https://github.com"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 rounded-lg transition"
            >
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-zinc-400" />
                <span>API Docs & Spec</span>
              </div>
              <ExternalLink className="size-3 text-zinc-500" />
            </a>
          </div>
        </aside>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm md:hidden flex"
            onClick={() => setMobileMenuOpen(false)}
          >
            <div
              className="w-72 bg-zinc-950 border-r border-zinc-800 h-full p-4 flex flex-col justify-between"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                  <div className="flex items-center gap-2">
                    <div className="size-7 rounded-lg bg-gradient-to-tr from-cyan-500 to-indigo-500 flex items-center justify-center">
                      <Zap className="size-3.5 text-white" />
                    </div>
                    <span className="font-bold text-white text-base">InferX</span>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1 rounded text-zinc-400 hover:text-white"
                  >
                    <X className="size-5" />
                  </button>
                </div>
                <nav className="space-y-1">
                  {navItems.map((item) => {
                    const isActive =
                      item.href === "/dashboard"
                        ? pathname === "/dashboard"
                        : pathname.startsWith(item.href);
                    const Icon = item.icon;

                    return (
                      <Link
                        key={item.href}
                        href={item.href}
                        onClick={() => setMobileMenuOpen(false)}
                        className={`flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium ${
                          isActive
                            ? "bg-zinc-800 text-cyan-400"
                            : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="size-4" />
                          <span>{item.title}</span>
                        </div>
                        {item.badge && (
                          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-zinc-900 text-zinc-400 border border-zinc-800 font-mono">
                            {item.badge}
                          </span>
                        )}
                      </Link>
                    );
                  })}
                </nav>
              </div>

              <div className="p-3 rounded-lg bg-zinc-900/60 border border-zinc-800 text-xs text-zinc-400">
                <p className="font-medium text-zinc-200">Cluster Status</p>
                <p className="text-[11px] text-emerald-400 mt-1 flex items-center gap-1.5">
                  <span className="size-1.5 rounded-full bg-emerald-400" />
                  Healthy • 8x H100 SXM5
                </p>
              </div>
            </div>
          </div>
        )}

        {/* Main Content Viewport */}
        <main className="flex-1 overflow-y-auto bg-zinc-950 p-4 sm:p-6 lg:p-8">
          <div className="max-w-7xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
