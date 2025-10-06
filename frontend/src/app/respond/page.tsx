"use client";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useAuth } from "@/store/auth";
import { fetchBlocks, unblock, BlockRule } from "@/lib/respond";
import { toast } from "sonner";
import RoleGate from "@/components/role-gate";

export default function RespondPage() {
  const { accessToken } = useAuth();

  const { data = [], isLoading, error, refetch } = useQuery<BlockRule[]>({
    queryKey: ["blocks", accessToken],
    queryFn: () => fetchBlocks(accessToken || ""),
    enabled: !!accessToken,
  });

  const unblockMut = useMutation({
    mutationFn: (id: number) => unblock(accessToken || "", id),
    onSuccess: () => {
      toast.success("IP unblocked");
      refetch();
    },
    onError: (e: any) =>
      toast.error("Failed to unblock", { description: e.message }),
  });

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Respond</h1>
        <button
          onClick={() => refetch()}
          className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50"
        >
          Refresh
        </button>
      </div>

      {isLoading && <p>Loading…</p>}
      {error && <p className="text-red-600">Failed to load blocklist.</p>}

      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-neutral-700">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">IP</th>
              <th className="text-left px-4 py-2">Reason</th>
              <th className="text-left px-4 py-2">Active</th>
              <th className="text-left px-4 py-2">Created</th>
              <th className="text-left px-4 py-2">Expires</th>
              <th className="px-4 py-2">Action</th>
            </tr>
          </thead>
          <tbody>
            {data.map((r) => (
              <tr key={r.id} className="border-t">
                <td className="px-4 py-2">{r.id}</td>
                <td className="px-4 py-2">{r.ip}</td>
                <td className="px-4 py-2">{r.reason || "-"}</td>
                <td className="px-4 py-2">{r.active ? "yes" : "no"}</td>
                <td className="px-4 py-2">
                  {new Date(r.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-2">
                  {r.expires_at
                    ? new Date(r.expires_at).toLocaleString()
                    : "-"}
                </td>
                <td className="px-4 py-2">
                  <RoleGate allow={["analyst", "admin"]}>
                    {r.active && (
                      <button
                        onClick={() => unblockMut.mutate(r.id)}
                        disabled={unblockMut.isPending}
                        className="px-2 py-1 rounded-md border bg-white hover:bg-neutral-50 disabled:opacity-50"
                      >
                        {unblockMut.isPending ? "Unblocking…" : "Unblock"}
                      </button>
                    )}
                  </RoleGate>
                </td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No block rules yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}