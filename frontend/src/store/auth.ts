import { create } from "zustand";

export type User = { id: number; email: string; role: string } | null;

type AuthState = {
  accessToken: string | null;
  refreshToken: string | null;
  user: User;
  setTokens: (a: string, r: string) => void;
  setUser: (u: User) => void;
  logout: () => void;
};

export const useAuth = create<AuthState>((set) => ({
  accessToken: null,
  refreshToken: null,
  user: null,
  setTokens: (a, r) => set({ accessToken: a, refreshToken: r }),
  setUser: (u) => set({ user: u }),
  logout: () => set({ accessToken: null, refreshToken: null, user: null }),
}));