"use client";
import { createContext, useContext, useEffect, useState } from "react";
import { api, type User } from "@/lib/api";

type AuthContextType = { user: User | null; loading: boolean; setSession: (token: string, user: User) => void; logout: () => void };
const AuthContext = createContext<AuthContextType | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  useEffect(() => {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 4000);
    const openWorkspace = async () => {
      try {
        if (localStorage.getItem("orbit_token")) {
          setUser(await api<User>("/auth/me", { signal: controller.signal }));
          return;
        }
      } catch {
        localStorage.removeItem("orbit_token");
      }
      const session = await api<{ access_token: string; user: User }>("/auth/desktop-session", { method: "POST", signal: controller.signal });
      localStorage.setItem("orbit_token", session.access_token);
      setUser(session.user);
    };
    openWorkspace()
      .catch(() => setUser(null))
      .finally(() => { window.clearTimeout(timeout); setLoading(false); });
    return () => { window.clearTimeout(timeout); controller.abort(); };
  }, []);
  const setSession = (token: string, nextUser: User) => { localStorage.setItem("orbit_token", token); setUser(nextUser); };
  const logout = () => { localStorage.removeItem("orbit_token"); window.location.replace("/dashboard/"); };
  return <AuthContext.Provider value={{ user, loading, setSession, logout }}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
