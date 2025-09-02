"use client";
import { useAuth } from "@/store/auth";
import { useQuery, useMutation } from "@tanstack/react-query";
import { apiGet, apiPost } from "@/lib/api";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import { toast } from "sonner";
import { useRouter } from "next/navigation";

type Summary = {
  events_last_24h: number;
  detections_open: number;
  detections_by_severity: Record<string, number>;
  blocklist_active: number;
  events_hourly_24h: { ts: string; count: number }[];
  now: string;
};

export default function DashboardPage() {
  const { accessToken } = useAuth();
  const router = useRouter();

  const { data, isLoading, error, refetch } = useQuery<Summary>({
    queryKey: ["metrics", accessToken],
    queryFn: () => apiGet<Summary>("/metrics/summary", accessToken || undefined),
    enabled: !!accessToken,
  });

  const genMut = useMutation({
    mutationFn: () =>
      apiPost<{ ok: boolean; source_ip: string }>(
        "/demo/generate",
        {},
        accessToken || undefined
      ),
    onSuccess: (res) => {
      toast.success("Demo data generated", {
        description: `Brute-force from ${res.source_ip}`,
      });
      refetch();           // refresh metrics
      // router.push("/detections"); // uncomment if you want to jump there
    },
    onError: (e: any) => {
      toast.error("Failed to generate demo data", { description: e.message });
    },
  });

  return (
    <main className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Dashboard</h1>
        <div className="flex gap-2">
          <button
            onClick={() => genMut.mutate()}
            className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-black"
          >
            {genMut.isPending ? "Generating…" : "Generate demo data"}
          </button>
          <button
            onClick={() => refetch()}
            className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50"
          >
            Refresh
          </button>
        </div>
      </div>

      {isLoading && <p className="text-sm">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load metrics.</p>}

      {data && (
        <>
          <section className="grid md:grid-cols-4 gap-4">
            <StatCard label="Events (24h)" value={data.events_last_24h} />
            <StatCard label="Open detections" value={data.detections_open} />
            <StatCard label="Active blocks" value={data.blocklist_active} />
            <StatCard label="Now (UTC)" value={new Date(data.now).toLocaleString()} />
          </section>

          <section className="rounded-lg border bg-white p-4">
            <div className="font-medium mb-2">Events last 24h</div>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={data.events_hourly_24h}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="ts" tickFormatter={(t) => new Date(t).getHours().toString()} />
                  <YAxis allowDecimals={false} />
                  <Tooltip labelFormatter={(t) => new Date(t as string).toLocaleString()} />
                  <Line type="monotone" dataKey="count" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </section>

          <section className="rounded-lg border bg-white p-4">
            <div className="font-medium mb-2">Detections by severity</div>
            <div className="flex flex-wrap gap-2 text-sm">
              {Object.entries(data.detections_by_severity).map(([sev, n]) => (
                <span key={sev} className="inline-flex items-center gap-2 rounded-md border px-2 py-1">
                  <span className="capitalize">{sev}</span>
                  <span className="font-medium">{n}</span>
                </span>
              ))}
              {Object.keys(data.detections_by_severity).length === 0 && (
                <span className="text-neutral-500">No detections yet.</span>
              )}
            </div>
          </section>
        </>
      )}
    </main>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-lg border bg-white p-4">
      <div className="text-xs text-neutral-600">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}