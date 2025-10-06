"use client";
import { useAuth } from "@/store/auth";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function RoleGate({ allow, children }: { allow: Array<"viewer"|"analyst"|"admin">, children: React.ReactNode }) {
  const { user } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!user) return; // still hydrating
    const ok = allow.includes((user.role || "viewer") as any);
    if (!ok) router.replace("/dashboard?forbidden=1");
  }, [user, router, allow]);

  return <>{children}</>;
}