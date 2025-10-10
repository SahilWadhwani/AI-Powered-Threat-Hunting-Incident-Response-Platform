"use client";
import Link from "next/link";
import RoleGate from "@/components/role-gate";
import { useAuth } from "@/store/auth";

function Card({
  title,
  desc,
  href,
  disabled,
}: {
  title: string;
  desc: string;
  href: string;
  disabled?: boolean;
}) {
  const cx = [
    "rounded-xl border bg-white p-5 shadow-sm",
    disabled ? "opacity-60 pointer-events-none" : "hover:shadow",
  ].join(" ");
  return (
    <Link href={href} className={cx}>
      <div className="font-semibold">{title}</div>
      <p className="text-sm text-neutral-600 mt-1">{desc}</p>
    </Link>
  );
}

export default function Home() {
  const { user } = useAuth();

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-2xl font-semibold">Welcome to SentinelX</h1>
        <p className="text-sm text-neutral-600">
          End-to-end SOC console with rule & ML detections, cases, and response.
        </p>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card
          title="Dashboard"
          desc="Overview of detections and traffic patterns."
          href="/dashboard"
        />
        <Card
          title="Detections"
          desc="All rule & ML detections with evidence."
          href="/detections"
        />
        <Card
          title="Events"
          desc="Normalized event stream for investigations."
          href="/events"
        />
        <Card
          title="Cases"
          desc="Open and track investigations."
          href="/cases"
        />

        {/* Respond tile: only enabled for analyst/admin */}
        <RoleGate allow={["analyst", "admin"]}>
          <Card
            title="Respond"
            desc="Block IPs temporarily and review actions."
            href="/respond"
          />
        </RoleGate>

        {/* For viewers, show disabled Respond card */}
        {user && user.role === "viewer" && (
          <Card
            title="Respond (restricted)"
            desc="Requires analyst or admin role."
            href="/respond"
            disabled
          />
        )}
      </div>
    </div>
  );
}