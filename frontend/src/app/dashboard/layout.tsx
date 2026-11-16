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
      {/* Quiet Top Header */}
      <header className="sticky top-0 z-40 border-b border-zinc-800/80 bg-[#09090b]/90 backdrop-blur-sm px-6 h-14 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="md:hidden p-1.5 rounded-md text-zinc-400 hover:text-white hover:bg-zinc-800/60"
            aria-label="Toggle navigation"
          >
            {mobileMenuOpen ? <X className="size-4" /> : <Menu className="size-4" />}
          </button>

          <Link href="/dashboard" className="flex items-center gap-2.5">
            <div className="size-7 rounded-md bg-zinc-800 border border-zinc-700/80 flex items-center justify-center">
              <Zap className="size-4 text-zinc-200" />
            </div>
            <span className="font-medium tracking-tight text-white text-sm">
              InferX
            </span>
          </Link>

          <div className="hidden sm:flex items-center gap-2 text-zinc-500 text-xs ml-4 pl-4 border-l border-zinc-800">
            <span>Console</span>
            <ChevronRight className="size-3 text-zinc-600" />
            <span className="text-zinc-200 font-medium">{currentPageTitle}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <div className="hidden lg:flex items-center gap-2 px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900/60 text-zinc-300 text-xs font-mono">
            <span className="size-1.5 rounded-full bg-emerald-500" />
            <span>vLLM 0.6.3</span>
          </div>

          <div className="hidden sm:flex items-center gap-2 px-2.5 py-1 rounded border border-zinc-800 bg-zinc-900/60 text-zinc-400 text-xs font-mono">
            <Cpu className="size-3.5 text-zinc-400" />
            <span>8x H100 SXM5</span>
          </div>

          <Link
            href="/dashboard/playground"
            className="h-8 px-3 rounded-md bg-zinc-100 hover:bg-white text-zinc-950 text-xs font-medium flex items-center gap-1.5 transition-colors"
          >
            <Terminal className="size-3.5" />
            <span>Playground</span>
          </Link>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* Quiet Desktop Sidebar */}
        <aside className="hidden md:flex flex-col w-60 border-r border-zinc-800/80 bg-[#09090b] p-4 shrink-0 justify-between">
          <div className="space-y-6">
            <div>
              <p className="px-2.5 text-xs text-zinc-500 mb-2 font-medium">
                Platform
              </p>
              <nav className="space-y-0.5">
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
                      className={`flex items-center justify-between px-2.5 py-1.5 rounded-md text-xs transition-colors h-8 ${
                        isActive
                          ? "bg-zinc-800 text-white font-medium"
                          : "text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900"
                      }`}
                    >
                      <div className="flex items-center gap-2.5">
                        <Icon
                          className={`size-4 ${
                            isActive ? "text-zinc-100" : "text-zinc-400"
                          }`}
                        />
                        <span>{item.title}</span>
                      </div>
                      {item.count !== undefined && (
                        <span
                          className={`text-[11px] font-mono tabular-nums ${
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

            {/* Instrument Telemetry Strip */}
            <div>
              <p className="px-2.5 text-xs text-zinc-500 mb-2 font-medium">
                Cluster telemetry
              </p>
              <div className="p-3 rounded-lg border border-zinc-800/80 bg-zinc-900/30 space-y-2.5 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-zinc-400 flex items-center gap-1.5">
                    <Activity className="size-3 text-emerald-500" />
                    GPU health
                  </span>
                  <span className="text-zinc-200 font-mono text-[11px] tabular-nums">
                    99.98%
                  </span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-zinc-500">VRAM alloc</span>
                  <span className="text-zinc-300 font-mono text-[11px] tabular-nums">
                    482 / 640 GB
                  </span>
                </div>
                <div className="w-full bg-zinc-800 rounded-full h-1 overflow-hidden">
                  <div
                    className="bg-zinc-300 h-1 rounded-full"
                    style={{ width: "75%" }}
                  />
                </div>
                <div className="flex items-center justify-between text-[11px] pt-1 text-zinc-500 border-t border-zinc-800/60 font-mono">
                  <span>Aggregate QPS</span>
                  <span className="text-zinc-300 tabular-nums">3,420 rps</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quiet Sidebar Footer */}
          <div className="pt-3 border-t border-zinc-800/80">
            <a
              href="https://github.com/Mrvikas06/InferX"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center justify-between px-2.5 py-1.5 text-xs text-zinc-400 hover:text-zinc-200 hover:bg-zinc-900 rounded-md transition-colors"
            >
              <div className="flex items-center gap-2">
                <ShieldCheck className="size-3.5 text-zinc-400" />
                <span>API spec</span>
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
              className="w-64 bg-[#09090b] border-r border-zinc-800 h-full p-4 flex flex-col justify-between"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="space-y-4">
                <div className="flex items-center justify-between pb-3 border-b border-zinc-800">
                  <div className="flex items-center gap-2">
                    <div className="size-6 rounded bg-zinc-800 border border-zinc-700 flex items-center justify-center">
                      <Zap className="size-3.5 text-zinc-200" />
                    </div>
                    <span className="font-medium text-white text-sm">InferX</span>
                  </div>
                  <button
                    onClick={() => setMobileMenuOpen(false)}
                    className="p-1 rounded text-zinc-400 hover:text-white"
                  >
                    <X className="size-4" />
                  </button>
                </div>
                <nav className="space-y-0.5">
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
                        className={`flex items-center justify-between px-2.5 py-2 rounded-md text-xs ${
                          isActive
                            ? "bg-zinc-800 text-white font-medium"
                            : "text-zinc-400 hover:text-zinc-100 hover:bg-zinc-900"
                        }`}
                      >
                        <div className="flex items-center gap-2.5">
                          <Icon className="size-4" />
                          <span>{item.title}</span>
                        </div>
                        {item.count !== undefined && (
                          <span className="text-[11px] font-mono text-zinc-500">
                            {item.count}
                          </span>
                        )}
                      </Link>
                    );
                  })}
                </nav>
              </div>

              <div className="p-3 rounded border border-zinc-800 text-xs text-zinc-500 font-mono">
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
