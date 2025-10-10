"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import RoleGate from "@/components/role-gate";

const NavLink = ({ href, label }: { href: string; label: string }) => {
  const pathname = usePathname();
  const active = pathname === href || pathname.startsWith(href + "/");
  return (
    <Link
      href={href}
      className={[
        "px-3 py-2 rounded-md text-sm",
        active
          ? "bg-neutral-900 text-white"
          : "text-neutral-700 hover:bg-neutral-200/60",
      ].join(" ")}
    >
      {label}
    </Link>
  );
};

export default function TopNav() {
  const { user, accessToken, logout } = useAuth();
  const router = useRouter();

  return (
    <header className="sticky top-0 z-40 border-b bg-white">
      <div className="mx-auto max-w-7xl px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Link href="/" className="font-semibold text-lg">
            SentinelX
          </Link>
          <nav className="ml-4 hidden md:flex items-center gap-1">
            <NavLink href="/dashboard" label="Dashboard" />
            <NavLink href="/detections" label="Detections" />
            <NavLink href="/events" label="Events" />
            {/* Respond is visible only to analyst/admin */}
            <RoleGate allow={["analyst", "admin"]}>
              <NavLink href="/respond" label="Respond" />
            </RoleGate>
            <NavLink href="/cases" label="Cases" />
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {!accessToken ? (
            <>
              <Link
                href="/login"
                className="px-3 py-2 rounded-md text-sm border bg-white hover:bg-neutral-50"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="px-3 py-2 rounded-md text-sm bg-neutral-900 text-white hover:bg-neutral-800"
              >
                Register
              </Link>
            </>
          ) : (
            <div className="flex items-center gap-3">
              <div className="text-sm text-neutral-600">
                {user?.email} <span className="uppercase">({user?.role})</span>
              </div>
              <button
                onClick={() => {
                  try { logout?.(); } catch {}
                  router.push("/login");
                }}
                className="px-3 py-2 rounded-md text-sm border bg-white hover:bg-neutral-50"
              >
                Logout
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}