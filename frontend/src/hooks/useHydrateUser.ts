"use client";
import { useEffect } from "react";
import { useAuth } from "@/store/auth";
import { apiGet } from "@/lib/api";

export function useHydrateUser() {
  const { accessToken, user, setUser } = useAuth();
  useEffect(() => {
    (async () => {
      if (accessToken && !user) {
        try {
          const me = await apiGet<{ id:number; email:string; role:string }>("/auth/me", accessToken);
          setUser(me);
        } catch {
          /* noop - token may be stale */
        }
      }
    })();
  }, [accessToken, user, setUser]);
}