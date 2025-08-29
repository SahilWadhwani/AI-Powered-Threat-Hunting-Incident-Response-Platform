"use client";
import { useParams, useRouter } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/store/auth";
import { apiGet, apiPost } from "@/lib/api";
import { toast } from "sonner";
import Link from "next/link";
import { createCase } from "@/lib/cases";

type EvidenceEvent = {
  id: number;
  timestamp: string;
  event_module: string;
  event_action: string;
  src_ip?: string | null;
  user?: string | null;
  http_path?: string | null;
  country?: string | null;
};

type DetectionDetail = {
  id: number;
  created_at: string;
  rule_id?: string | null;
  kind: string;
  severity: string;
  title: string;
  summary?: string | null;
  status: string;
  tags?: string[];
  event_ids?: number[];
  evidence_events: EvidenceEvent[];
};

export default function DetectionDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { accessToken } = useAuth();
  const router = useRouter();
  const qc = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["detection", id, accessToken],
    queryFn: () => apiGet<DetectionDetail>(`/detections/${id}`, accessToken || undefined),
    enabled: !!accessToken && !!id,
  });

  const srcIp = data?.evidence_events?.find(e => e.src_ip)?.src_ip;

  const blockMut = useMutation({
    mutationFn: (vars: { ip: string }) =>
      apiPost(`/respond/block_ip?ip=${encodeURIComponent(vars.ip)}&reason=${encodeURIComponent(`from detection ${id}`)}&ttl_minutes=60`, {}, accessToken || undefined),
    onSuccess: () => {
      toast.success("IP blocked for 60 minutes");
      qc.invalidateQueries({ queryKey: ["blocklist"] });
    },
    onError: (err: any) => {
      toast.error("Failed to block IP", { description: err.message });
    },
  });

  const createCaseMut = useMutation({
  mutationFn: () =>
    createCase(accessToken || "", {
      title: data?.title ? `[Det ${id}] ${data.title}` : `Detection #${id}`,
      description: data?.summary || "",
      severity: data?.severity || "medium",
      detection_ids: [id],
    }),
  onSuccess: (res) => {
    toast.success("Case created");
    router.push(`/cases/${res.id}`);
  },
  onError: (e: any) => toast.error("Failed to create case", { description: e.message }),
});

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Detection #{id}</h1>
        <Link href="/detections" className="text-indigo-600 hover:underline">← Back</Link>
      </div>

      {isLoading && <p className="text-sm">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load detection.</p>}

      {data && (
        <div className="grid gap-6 md:grid-cols-3">
          <section className="md:col-span-2 space-y-3">
            <div className="rounded-lg border bg-white p-4">
              <h2 className="font-medium">{data.title}</h2>
              <p className="text-sm text-neutral-600 mt-1">{data.summary}</p>
              <div className="mt-3 text-sm space-x-2">
                <Badge label="Rule" value={data.rule_id || "-"} />
                <Badge label="Severity" value={data.severity} />
                <Badge label="Status" value={data.status} />
                <Badge label="Created" value={new Date(data.created_at).toLocaleString()} />
              </div>
            </div>

            <div className="rounded-lg border bg-white">
              <div className="border-b px-4 py-2 font-medium">Evidence events</div>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead className="bg-neutral-50">
                    <tr>
                      <th className="text-left px-4 py-2">ID</th>
                      <th className="text-left px-4 py-2">Time</th>
                      <th className="text-left px-4 py-2">Module</th>
                      <th className="text-left px-4 py-2">Action</th>
                      <th className="text-left px-4 py-2">Src IP</th>
                      <th className="text-left px-4 py-2">User</th>
                      <th className="text-left px-4 py-2">Path</th>
                      <th className="text-left px-4 py-2">Country</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.evidence_events.map(ev => (
                      <tr key={ev.id} className="border-t hover:bg-neutral-50/60">
                        <td className="px-4 py-2">{ev.id}</td>
                        <td className="px-4 py-2">{new Date(ev.timestamp).toLocaleString()}</td>
                        <td className="px-4 py-2">{ev.event_module}</td>
                        <td className="px-4 py-2">{ev.event_action}</td>
                        <td className="px-4 py-2">{ev.src_ip || "-"}</td>
                        <td className="px-4 py-2">{ev.user || "-"}</td>
                        <td className="px-4 py-2">{ev.http_path || "-"}</td>
                        <td className="px-4 py-2">{ev.country || "-"}</td>
                      </tr>
                    ))}
                    {data.evidence_events.length === 0 && (
                      <tr><td colSpan={8} className="px-4 py-8 text-center text-neutral-500">No evidence events.</td></tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </section>

          <aside className="space-y-3">
            <div className="rounded-lg border bg-white p-4">
              <h3 className="font-medium mb-2">Respond</h3>
              <div className="text-sm text-neutral-600 mb-3">
                {srcIp ? <>Primary source IP detected: <span className="font-medium">{srcIp}</span></> : "No source IP found on evidence"}
              </div>

              <div className="rounded-lg border bg-white p-4">
                <h3 className="font-medium mb-2">Case</h3>
                <button
                    onClick={() => createCaseMut.mutate()}
                    className="w-full px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-black mb-3"
                >
                {createCaseMut.isPending ? "Creating…" : "Open case"}
                </button>
                </div>
              <button
                disabled={!srcIp || blockMut.isPending}
                onClick={() => srcIp && blockMut.mutate({ ip: srcIp })}
                className={`w-full px-3 py-2 rounded-md ${srcIp ? "bg-red-600 text-white hover:bg-red-700" : "bg-neutral-200 text-neutral-500 cursor-not-allowed"}`}
              >
                {blockMut.isPending ? "Blocking…" : "Block IP (60m)"}
              </button>
            </div>
          </aside>
        </div>
      )}
    </main>
  );
}

function Badge({ label, value }: { label: string; value: string }) {
  return (
    <span className="inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-xs">
      <span className="text-neutral-500">{label}:</span>
      <span className="font-medium">{value}</span>
    </span>
  );
}

