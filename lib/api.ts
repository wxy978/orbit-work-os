export const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

export type User = { id: string; email: string; display_name: string };
export type Meeting = { id: string; title: string; filename: string; status: string; transcript?: string; summary?: Record<string, unknown>; error_message?: string; created_at: string };
export type Report = { id: string; report_date: string; status: string; content: Record<string, unknown>; created_at: string };
export type KnowledgeDocument = { id: string; title: string; filename: string; mime_type: string; file_size: number; status: string; error_message?: string; created_at: string };
export type ChatMessage = { id: string; role: "user" | "assistant"; content: string; citations?: Array<{ document_id: string; quote: string; score: number }>; created_at: string };

export function getToken() { return typeof window === "undefined" ? null : localStorage.getItem("orbit_token"); }

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(init.headers);
  if (!(init.body instanceof FormData)) headers.set("Content-Type", "application/json");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_URL}${path}`, { ...init, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.detail ?? "请求失败，请稍后重试");
  return data as T;
}

export function upload<T>(path: string, form: FormData) { return api<T>(path, { method: "POST", body: form }); }
