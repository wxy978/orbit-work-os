import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export function BrandLogo({ compact = false, className }: { compact?: boolean; className?: string }) {
  return <div className={cn("flex items-center gap-2.5", className)}><div className="grid size-9 place-items-center rounded-xl bg-slate-950 text-white shadow-sm"><Sparkles className="size-4" /></div>{!compact && <span className="text-[15px] font-bold tracking-tight">Orbit Work OS</span>}</div>;
}
