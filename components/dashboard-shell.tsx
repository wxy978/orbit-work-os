"use client";

import { useState } from "react";
import { Bell, Menu, Search } from "lucide-react";
import { AppSidebar } from "@/components/app-sidebar";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth-provider";
import { useEffect } from "react";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const { user, loading } = useAuth();
  useEffect(() => { if (!loading && !user) window.location.replace("/login"); }, [loading, user]);
  if (loading) return <div className="grid min-h-screen place-items-center bg-slate-50"><div className="text-center"><div className="mx-auto size-8 animate-spin rounded-full border-2 border-indigo-200 border-t-indigo-600" /><p className="mt-3 text-sm text-slate-500">正在验证工作空间…</p></div></div>;
  if (!user) return <div className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">正在返回登录页…</div>;
  return <div className="min-h-screen bg-slate-50/70">
    <AppSidebar collapsed={collapsed} mobileOpen={mobileOpen} onToggle={() => setCollapsed(!collapsed)} onMobileClose={() => setMobileOpen(false)} />
    <div className={cn("transition-[margin] duration-200", collapsed ? "lg:ml-[76px]" : "lg:ml-[248px]")}>
      <header className="sticky top-0 z-30 flex h-[72px] items-center gap-3 border-b bg-white/90 px-4 backdrop-blur-xl sm:px-6 lg:px-8">
        <Button aria-label="打开导航" variant="ghost" size="icon" className="lg:hidden" onClick={() => setMobileOpen(true)}><Menu className="size-5" /></Button>
        <div className="relative hidden max-w-sm flex-1 md:block"><Search className="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-slate-400" /><input className="h-10 w-full rounded-lg border-0 bg-slate-100 pl-9 pr-3 text-sm outline-none ring-indigo-500/20 placeholder:text-slate-400 focus:ring-4" placeholder="搜索会议、文档或提问…" /></div>
        <div className="ml-auto flex items-center gap-2"><Button variant="ghost" size="icon" className="relative text-slate-500"><Bell className="size-5" /><span className="absolute right-2 top-2 size-2 rounded-full border-2 border-white bg-rose-500" /></Button><div className="hidden h-6 w-px bg-slate-200 sm:block" /><div className="hidden items-center gap-2.5 pl-1 sm:flex"><div className="grid size-9 place-items-center rounded-lg bg-indigo-600 text-xs font-semibold text-white">{user.display_name.slice(0, 2).toUpperCase()}</div><div><p className="text-sm font-medium">{user.display_name}</p><p className="text-xs text-slate-400">{user.email}</p></div></div></div>
      </header>
      <main className="p-4 sm:p-6 lg:p-8">{children}</main>
    </div>
  </div>;
}
