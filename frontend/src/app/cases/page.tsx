"use client";
import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { useAuth } from "@/store/auth";
import { fetchCases, CaseRow } from "@/lib/cases";
import { useHydrateUser } from "@/hooks/useHydrateUser";

export default function CasesPage() {
    useHydrateUser();
  const { accessToken } = useAuth();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["cases", accessToken],
    queryFn: () => fetchCases(accessToken || ""),
    enabled: !!accessToken,
  });

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Cases</h1>
        <button onClick={() => refetch()} className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50">Refresh</button>
      </div>

      {isLoading && <p className="text-sm">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load.</p>}

      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-neutral-700">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">Title</th>
              <th className="text-left px-4 py-2">Severity</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Assignee</th>
              <th className="text-left px-4 py-2">Updated</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {data?.map((c: CaseRow) => (
              <tr key={c.id} className="border-t hover:bg-neutral-50/60">
                <td className="px-4 py-2">{c.id}</td>
                <td className="px-4 py-2">{c.title}</td>
                <td className="px-4 py-2 capitalize">{c.severity}</td>
                <td className="px-4 py-2 capitalize">{c.status}</td>
                <td className="px-4 py-2">{c.assignee || "-"}</td>
                <td className="px-4 py-2">{new Date(c.updated_at).toLocaleString()}</td>
                <td className="px-4 py-2">
                  <Link href={`/cases/${c.id}`} className="text-indigo-600 hover:underline">Open</Link>
                </td>
              </tr>
            ))}
            {data?.length === 0 && (
              <tr><td colSpan={7} className="px-4 py-8 text-center text-neutral-500">No cases yet.</td></tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}