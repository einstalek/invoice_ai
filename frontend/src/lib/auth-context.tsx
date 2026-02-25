"use client";

import { createContext, useContext, useEffect, useState, useCallback, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { User, UserMembership } from "./types";
import * as api from "./api";

interface AuthState {
  user: User | null;
  memberships: UserMembership[];
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  googleLogin: (code: string) => Promise<void>;
  logout: () => void;
  refreshMemberships: () => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [memberships, setMemberships] = useState<UserMembership[]>([]);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  const refreshMemberships = useCallback(async () => {
    try {
      const m = await api.getMyMemberships();
      setMemberships(m);
    } catch {
      setMemberships([]);
    }
  }, []);

  // Check for existing session on mount
  useEffect(() => {
    if (!api.isLoggedIn()) {
      setLoading(false);
      return;
    }
    (async () => {
      try {
        const me = await api.getMe();
        setUser(me);
        await refreshMemberships();
      } catch {
        api.logout();
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshMemberships]);

  const login = async (email: string, password: string) => {
    const u = await api.login(email, password);
    setUser(u);
    await refreshMemberships();
    router.push("/dashboard");
  };

  const register = async (email: string, password: string, fullName: string) => {
    const u = await api.register(email, password, fullName);
    setUser(u);
    await refreshMemberships();
    router.push("/dashboard");
  };

  const googleLogin = async (code: string) => {
    const u = await api.googleLogin(code);
    setUser(u);
    await refreshMemberships();
    router.push("/dashboard");
  };

  const logout = () => {
    api.logout();
    setUser(null);
    setMemberships([]);
    router.push("/login");
  };

  return (
    <AuthContext.Provider value={{ user, memberships, loading, login, register, googleLogin, logout, refreshMemberships }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
