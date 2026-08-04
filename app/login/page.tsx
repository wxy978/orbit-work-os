"use client";

import { useEffect } from "react";

export default function LoginPage() {
  useEffect(() => { window.location.replace("/dashboard/"); }, []);
  return <main className="grid min-h-screen place-items-center bg-slate-50 text-sm text-slate-500">正在打开本地工作空间…</main>;
}
