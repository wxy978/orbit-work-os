"use client";
import Link from "next/link";
import { FormEvent, useState } from "react";
import { useRouter } from "next/navigation";
import { ArrowRight } from "lucide-react";
import { BrandLogo } from "@/components/brand-logo";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, type User } from "@/lib/api";
import { useAuth } from "@/components/auth-provider";

export default function RegisterPage() {
  const [form, setForm] = useState({ display_name: "", email: "", password: "" }); const [error, setError] = useState(""); const [busy, setBusy] = useState(false); const router = useRouter(); const { setSession } = useAuth();
  async function submit(e: FormEvent) { e.preventDefault(); setBusy(true); setError(""); try { const data = await api<{access_token:string;user:User}>("/auth/register", {method:"POST", body:JSON.stringify(form)}); setSession(data.access_token,data.user); router.push("/dashboard"); } catch(e) { setError(e instanceof Error ? e.message : "注册失败"); } finally { setBusy(false); } }
  return <main className="grid min-h-screen place-items-center bg-slate-50 px-5"><div className="w-full max-w-md rounded-2xl border bg-white p-8 surface-shadow"><BrandLogo /><div className="mt-9"><h1 className="text-2xl font-bold">创建工作空间</h1><p className="mt-2 text-sm text-slate-500">开始使用会议总结、智能日报与知识问答</p></div><form onSubmit={submit} className="mt-7 space-y-4"><div><label className="mb-2 block text-sm font-medium">姓名</label><Input value={form.display_name} onChange={e=>setForm({...form,display_name:e.target.value})} placeholder="你的姓名" required /></div><div><label className="mb-2 block text-sm font-medium">邮箱</label><Input value={form.email} onChange={e=>setForm({...form,email:e.target.value})} type="email" placeholder="name@company.com" required /></div><div><label className="mb-2 block text-sm font-medium">密码</label><Input value={form.password} onChange={e=>setForm({...form,password:e.target.value})} type="password" minLength={8} placeholder="至少 8 位字符" required /></div>{error&&<p className="rounded-lg bg-rose-50 px-3 py-2 text-sm text-rose-600">{error}</p>}<Button disabled={busy} className="h-11 w-full">{busy?"正在创建…":"创建账号"}<ArrowRight className="size-4" /></Button></form><p className="mt-6 text-center text-sm text-slate-500">已有账号？ <Link href="/login" className="font-semibold text-indigo-600">返回登录</Link></p></div></main>;
}
