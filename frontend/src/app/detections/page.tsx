"use client";
import { useAuth } from "@/store/auth";
import Link from "next/link";

export default function DetectionsPage() {
  const { user } = useAuth();
  return (
    <main className="p-6 space-y-2">
      <h1 className="text-2xl font-semibold">Detections</h1>
      <p className="text-sm text-neutral-600">
        {user ? <>Signed in as <span className="font-medium">{user.email}</span> ({user.role})</> : "Not signed in"}
      </p>
      <p className="text-sm">
        We’ll render the table here next. Go to <Link href="/">home</Link>.
      </p>
    </main>
  );
}