"use client";
import { useEffect } from "react";

export default function Home() {
  useEffect(() => { window.location.replace("/dashboard/"); }, []);
  return <div className="grid min-h-screen place-items-center text-sm text-slate-500">正在打开 Orbit Work OS…</div>;
}
