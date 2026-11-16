"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  Box,
  ChevronRight,
  Cpu,
  ExternalLink,
  Gauge,
  LayoutDashboard,
  LineChart,
  Menu,
  Server,
  ShieldCheck,
  Terminal,
  X,
  Zap,
} from "lucide-react";

interface NavItem {
  title: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  count?: number;
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
    count: 6,
  },
  {
    title: "Deployments",
    href: "/dashboard/deployments",
    icon: Server,
    count: 4,
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
    <div className="min-h-screen bg-[#09090b] text-zinc-100 flex flex-col font-sans antialiased">
      {/* Top Header */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#09090b]/95 backdrop-blur-sm px-6 h-16 flex items-center justify-between">
        <div className="flex items-center gap-3.5">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-2 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="size-5" /> : <Menu className="size-5" />}
          </button>

          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="size-8 rounded-lg bg-zinc-800 border border-zinc-700/80 flex items-center justify-center">
              <Zap className="size-4 text-zinc-100" />
            </div>
            <span className="font-semibold tracking-tight text-white text-base">
              InferX
            </span>
          </Link>

          <div className="hidden sm:flex items-center gap-2 text-zinc-500 text-sm ml-4 pl-4 border-l border-zinc-800">
            <span>Console</span>
            <ChevronRight className="size-3.5 text-zinc-600" />
            <span className="text-zinc-200 font-medium">{currentPageTitle}</span>
          </div>
        </div>

        <div className="flex items-center gap-3.5">
          <div className="hidden lg:flex items-center gap-2 px-3 py-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 text-zinc-300 text-xs font-mono">
            <span className="size-2 rounded-full bg-emerald-500" />
            <span>vLLM 0.6.3 (Online)</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-md border border-zinc-800 bg-zinc-900/60 text-zinc-300 text-xs font-mono">
            <Cpu className="size-3.5 text-zinc-400" />
            <span>8x H100 SXM5</span>
          </div>

          <Link
            href="/dashboard/playground"
            className="h-9 px-3.5 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-sm font-medium flex items-center gap-2 transition-colors"
          >
            <Terminal className="size-4" />
            <span>Playground</span>
          </Link>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Desktop Sidebar */}
        <aside className="hidden md:flex flex-col w-64 border-r border-zinc-800/80 bg-[#09090b] p-4 shrink-0 justify-between">
          <div className="space-y-6">
            <div>
              <p className="px-3 text-xs font-medium text-zinc-500 mb-2 uppercase tracking-wider">
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
                      className={`flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors h-9 ${
                        isActive
                          ? "bg-zinc-800 text-white font-medium"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900/80"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <Icon
                          className={`size-4 ${
                            isActive ? "text-zinc-100" : "text-zinc-400"
                          }`}
                        />
                        <span>{item.title}</span>
                      </div>
                      {item.count !== undefined && (
                        <span
                          className={`text-xs font-mono tabular-nums ${
                            isActive ? "text-zinc-300" : "text-zinc-500"
                          }`}
                        >
                          {item.count}
                        </span>
                      )}
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Cluster Telemetry Strip */}
            <div>
              <p className="px-3 text-xs font-medium text-zinc-500 mb-2 uppercase tracking-wider">
                Cluster telemetry
              </p>
              <div className="p-3.5 rounded-lg border border-zinc-800/80 bg-zinc-900/30 space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400 flex items-center gap-2">
                    <Activity className="size-3.5 text-emerald-500" />
                    GPU health
                  </span>
                  <span className="text-zinc-200 font-mono text-xs tabular-nums font-medium">
                    99.98%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400">VRAM allocation</span>
                  <span className="text-zinc-200 font-mono text-xs tabular-nums">
                    482 / 640 GB
                  </span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-1.5 overflow-hidden">
                  <div
                    className="bg-zinc-200 h-1.5 rounded-full"
                    style={{ width: "75%" }}
                  />
                </div>
                <div className="flex items-center justify-between pt-1.5 text-zinc-400 border-t border-zinc-800/60 font-mono text-xs">
                  <span>Aggregate QPS</span>
                  <span className="text-zinc-200 font-medium tabular-nums">3,420 rps</span>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar Footer */}
          <div className="pt-3 border-t border-zinc-800/80">
            <a
              href="https://github.com/Mrvikas06/InferX"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between px-3 py-2 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 rounded-md transition-colors"
            >
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-4 text-zinc-400" />
                <span>API documentation</span>
              </div>
              <ExternalLink className="size-3.5 text-zinc-500" />
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
              className="w-72 bg-[#09090b] border-r border-zinc-800 h-full p-4 flex flex-col justify-between"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                  <div className="flex items-center gap-2.5">
                    <div className="size-7 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                      <Zap className="size-4 text-zinc-200" />
                    </div>
                    <span className="font-semibold text-white text-base">InferX</span>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1.5 rounded text-zinc-400 hover:text-white"
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
                        className={`flex items-center justify-between px-3 py-2.5 rounded-md text-sm ${
                          isActive
                            ? "bg-zinc-800 text-white font-medium"
                            : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                        }`}
                      >
                        <div className="flex items-center gap-3">
                          <Icon className="size-4" />
                          <span>{item.title}</span>
                        </div>
                        {item.count !== undefined && (
                          <span className="text-xs font-mono text-zinc-400">
                            {item.count}
                          </span>
                        )}
                      </Link>
                    );
                  })}
                </nav>
              </div>

              <div className="p-3 rounded border border-zinc-800 text-xs text-zinc-400 font-mono">
                cluster-01 • healthy
              </div>
            </div>
          </div>
        )}

        {/* Content Viewport */}
        <main className="flex-1 overflow-y-auto bg-[#09090b] p-6 lg:p-8">
          <div className="max-w-6xl mx-auto space-y-6">{children}</div>
        </main>
      </div>
    </div>
  );
}
