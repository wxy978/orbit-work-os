"use client";

import { FormEvent, useEffect, useState } from "react";
import { CheckCircle2, Eye, EyeOff, KeyRound, LoaderCircle, PlugZap, Save, ShieldCheck, Trash2 } from "lucide-react";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type KeyStatus = { configured: boolean; key_hint: string | null; provider: string; base_url: string; model: string };
const defaults: KeyStatus = { configured: false, key_hint: null, provider: "OpenAI Compatible", base_url: "https://api.openai.com/v1", model: "gpt-5.5" };

export default function SettingsPage() {
  const [status, setStatus] = useState(defaults);
  const [form, setForm] = useState({ api_key: "", base_url: defaults.base_url, model: defaults.model });
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => { api<KeyStatus>("/settings/api-key").then(result => { setStatus(result); setForm(current => ({ ...current, base_url: result.base_url, model: result.model })); }); }, []);
  const payload = () => ({ ...form, api_key: form.api_key.trim() });

  async function testConnection() {
    setBusy("test"); setMessage("");
    try { const result = await api<{message:string}>("/settings/api-key/test", { method: "POST", body: JSON.stringify(payload()) }); setMessage(result.message); }
    catch (error) { setMessage(error instanceof Error ? error.message : "连接失败"); }
    finally { setBusy(""); }
  }
  async function save(e: FormEvent) {
    e.preventDefault(); setBusy("save"); setMessage("");
    try { const result = await api<KeyStatus>("/settings/api-key", { method: "PUT", body: JSON.stringify(payload()) }); setStatus(result); setForm(current => ({ ...current, api_key: "" })); setMessage("自定义 AI 接口已加密保存，所有新任务都会使用此配置"); }
    catch (error) { setMessage(error instanceof Error ? error.message : "保存失败"); }
    finally { setBusy(""); }
  }
  async function remove() { setBusy("delete"); setStatus(await api<KeyStatus>("/settings/api-key", { method: "DELETE" })); setMessage("自定义接口已移除"); setBusy(""); }

  return <div className="mx-auto max-w-4xl space-y-6">
    <div><p className="text-sm font-semibold text-indigo-600">AI 服务</p><h1 className="mt-1 text-3xl font-bold">自定义模型接口</h1><p className="mt-2 text-sm text-slate-500">只需填写密钥、接口地址和模型名称，所有 AI 功能统一使用该模型。</p></div>
    {message && <div className="flex items-center gap-2 rounded-xl border border-indigo-100 bg-indigo-50 px-4 py-3 text-sm text-indigo-700"><CheckCircle2 className="size-4 shrink-0" />{message}</div>}
    <Card className="shadow-none"><CardHeader><div className="flex items-center justify-between gap-3"><div className="flex items-center gap-3"><div className="grid size-10 place-items-center rounded-xl bg-indigo-50 text-indigo-600"><PlugZap className="size-5" /></div><div><CardTitle>OpenAI Compatible API</CardTitle><CardDescription>配置密钥、服务地址以及各项 AI 模型</CardDescription></div></div><Badge className={status.configured ? "bg-emerald-50 text-emerald-700" : "bg-slate-100 text-slate-500"}>{status.configured ? `已连接 ${status.key_hint ?? ""}` : "未配置"}</Badge></div></CardHeader>
      <CardContent><div className="mb-6 flex items-start gap-3 rounded-xl bg-slate-50 p-4"><ShieldCheck className="mt-0.5 size-5 shrink-0 text-emerald-600" /><div><p className="text-sm font-medium">仅在本机加密保存</p><p className="mt-1 text-xs leading-5 text-slate-500">API Key 不会显示或回传到页面。接口地址需要包含版本路径，例如 https://api.openai.com/v1。</p></div></div>
        <form onSubmit={save} className="grid gap-4 sm:grid-cols-2">
          <div className="sm:col-span-2"><label className="mb-2 block text-sm font-medium">API Key</label><div className="relative"><Input type={show ? "text" : "password"} value={form.api_key} onChange={e => setForm({...form, api_key:e.target.value})} placeholder={status.configured ? "输入新 Key 以更新当前配置" : "sk-... 或第三方服务密钥"} required /><button type="button" onClick={() => setShow(!show)} className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400">{show ? <EyeOff className="size-4" /> : <Eye className="size-4" />}</button></div></div>
          <div className="sm:col-span-2"><label className="mb-2 block text-sm font-medium">API Base URL</label><Input value={form.base_url} onChange={e => setForm({...form, base_url:e.target.value})} placeholder="https://api.openai.com/v1" required /></div>
          <div className="sm:col-span-2"><label className="mb-2 block text-sm font-medium">模型名称</label><Input value={form.model} onChange={e => setForm({...form, model:e.target.value})} placeholder="例如 gpt-5.5" required /><p className="mt-2 text-xs text-slate-400">填写服务商提供的模型 ID，例如 gpt-5.5、deepseek-chat 或自定义模型名。</p></div>
          <div className="flex items-end gap-2 sm:col-span-2"><Button type="button" variant="outline" onClick={testConnection} disabled={!!busy}>{busy === "test" ? <LoaderCircle className="size-4 animate-spin" /> : <PlugZap className="size-4" />}测试连接</Button><Button disabled={!!busy}>{busy === "save" ? <LoaderCircle className="size-4 animate-spin" /> : <Save className="size-4" />}保存配置</Button></div>
          {status.configured && <div className="sm:col-span-2"><Button type="button" variant="outline" onClick={remove} disabled={!!busy} className="text-rose-600"><Trash2 className="size-4" />移除自定义接口</Button></div>}
        </form>
      </CardContent></Card>
  </div>;
}
