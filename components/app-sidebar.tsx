"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, BookOpen, CalendarDays, FileText, LayoutDashboard, LogOut, MessageSquareText, PanelLeftClose, PanelLeftOpen, Settings, Users, X } from "lucide-react";
import { BrandLogo } from "@/components/brand-logo";
import { cn } from "@/lib/utils";
import { useAuth } from "@/components/auth-provider";

const mainNav = [
  { label: "工作台", href: "/dashboard", icon: LayoutDashboard },
  { label: "会议中心", href: "/meetings", icon: CalendarDays, badge: "3" },
  { label: "智能日报", href: "/reports", icon: FileText },
  { label: "知识库", href: "/knowledge", icon: BookOpen },
  { label: "AI 助手", href: "/assistant", icon: MessageSquareText },
];
const teamNav = [
  { label: "团队成员", href: "/team", icon: Users },
  { label: "数据洞察", href: "/analytics", icon: BarChart3 },
];

export function AppSidebar({ collapsed, mobileOpen, onToggle, onMobileClose }: { collapsed: boolean; mobileOpen: boolean; onToggle: () => void; onMobileClose: () => void }) {
  const pathname = usePathname();
  const { user, logout } = useAuth();
  const nav = (items: typeof mainNav) => items.map((item) => {
    const active = pathname === item.href;
    return <Link key={item.href} href={item.href} title={collapsed ? item.label : undefined} className={cn("group flex h-10 items-center gap-3 rounded-lg px-3 text-sm font-medium text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-950", active && "bg-indigo-50 text-indigo-700", collapsed && "justify-center px-0")}><item.icon className="size-[18px] shrink-0" />{!collapsed && <><span>{item.label}</span>{item.badge && <span className="ml-auto rounded-full bg-indigo-100 px-2 py-0.5 text-[11px] text-indigo-700">{item.badge}</span>}</>}</Link>;
  });

  return <>
    {mobileOpen && <button aria-label="关闭导航遮罩" className="fixed inset-0 z-40 bg-slate-950/30 backdrop-blur-sm lg:hidden" onClick={onMobileClose} />}
    <aside className={cn("fixed inset-y-0 left-0 z-50 flex flex-col border-r bg-white transition-all duration-200", collapsed ? "w-[76px]" : "w-[248px]", mobileOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0")}>
      <div className={cn("flex h-[72px] items-center border-b px-5", collapsed && "justify-center px-0")}><BrandLogo compact={collapsed} /><button className="ml-auto text-slate-400 lg:hidden" onClick={onMobileClose}><X className="size-5" /></button></div>
      <div className="flex-1 overflow-y-auto px-3 py-5">
        {!collapsed && <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">工作空间</p>}
        <nav className="space-y-1">{nav(mainNav)}</nav>
        <div className="my-5 border-t" />
        {!collapsed && <p className="mb-2 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-400">团队管理</p>}
        <nav className="space-y-1">{nav(teamNav)}</nav>
      </div>
      <div className="border-t p-3">
        <Link href="/settings" className={cn("flex h-10 items-center gap-3 rounded-lg px-3 text-sm text-slate-500 hover:bg-slate-100", collapsed && "justify-center px-0")}><Settings className="size-[18px]" />{!collapsed && "设置"}</Link>
        <button onClick={onToggle} className="mt-1 hidden h-10 w-full items-center gap-3 rounded-lg px-3 text-sm text-slate-500 hover:bg-slate-100 lg:flex">{collapsed ? <PanelLeftOpen className="mx-auto size-[18px]" /> : <><PanelLeftClose className="size-[18px]" />收起导航</>}</button>
        <div className={cn("mt-3 flex items-center gap-3 rounded-xl bg-slate-50 p-2", collapsed && "justify-center")}><div className="grid size-9 shrink-0 place-items-center rounded-lg bg-indigo-600 text-xs font-semibold text-white">{user?.display_name.slice(0,2).toUpperCase()??"AI"}</div>{!collapsed && <div className="min-w-0 flex-1"><p className="truncate text-sm font-semibold">{user?.display_name}</p><p className="truncate text-xs text-slate-400">{user?.email}</p></div>}{!collapsed && <button onClick={logout} title="退出登录"><LogOut className="size-4 text-slate-400" /></button>}</div>
      </div>
    </aside>
  </>;
}
