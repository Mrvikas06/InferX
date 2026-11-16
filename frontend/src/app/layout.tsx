import Link from "next/link";

const navigation = [
  { name: "Overview", href: "/dashboard" },
  { name: "Models", href: "/dashboard/models" },
  { name: "Deployments", href: "/dashboard/deployments" },
  { name: "Playground", href: "/dashboard/playground" },
  { name: "Benchmarks", href: "/dashboard/benchmarks" },
  { name: "Analytics", href: "/dashboard/analytics" },
];

export default function DashboardLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <div className="min-h-screen bg-[#09090b] text-white">
      <aside className="fixed inset-y-0 left-0 w-64 border-r border-zinc-800 p-6">
        <h2 className="text-2xl font-bold tracking-tight">
          INFERX
        </h2>

        <p className="mt-1 text-xs text-zinc-500">
          LLM INFERENCE PLATFORM
        </p>

        <nav className="mt-10 space-y-2">
          {navigation.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="block rounded-lg px-4 py-3 text-sm text-zinc-400 transition hover:bg-zinc-800 hover:text-white"
            >
              {item.name}
            </Link>
          ))}
        </nav>
      </aside>

      <div className="ml-64">
        {children}
      </div>
    </div>
  );
}