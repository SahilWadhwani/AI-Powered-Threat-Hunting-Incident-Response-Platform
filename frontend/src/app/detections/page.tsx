"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useAuth } from "@/store/auth";
import { apiGet } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { useHydrateUser } from "@/hooks/useHydrateUser";

type Detection = {
  id: number;
  created_at: string;
  rule_id: string | null;
  kind: string;
  severity: "low" | "medium" | "high" | "critical" | string;
  title: string;
  summary: string | null;
  status: "open" | "closed" | "triaged" | string;
  tags?: string[];
  event_ids?: number[];
  features?: Record<string, any> | null; // <--- added
};

export default function DetectionsPage() {
  useHydrateUser();
  const { accessToken, user } = useAuth();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["detections", accessToken],
    queryFn: () =>
      apiGet<Detection[]>(
        "/detections?kind=rule&limit=100",
        accessToken || undefined
      ),
    enabled: !!accessToken,
  });

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold">Detections</h1>
          <p className="text-sm text-neutral-600">
            {user ? (
              <>
                Signed in as{" "}
                <span className="font-medium">{user.email}</span>
              </>
            ) : (
              "Not signed in"
            )}
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50"
        >
          Refresh
        </button>
      </div>

      {isLoading && <p className="text-sm">Loading…</p>}
      {error && (
        <p className="text-sm text-red-600">Failed to load detections.</p>
      )}

      <div className="overflow-x-auto rounded-lg border bg-white">
        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-neutral-700">
            <tr>
              <th className="text-left px-4 py-2">ID</th>
              <th className="text-left px-4 py-2">Title</th>
              <th className="text-left px-4 py-2">Rule</th>
              <th className="text-left px-4 py-2">Severity</th>
              <th className="text-left px-4 py-2">Status</th>
              <th className="text-left px-4 py-2">Created</th>
              <th className="px-4 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {data?.map((d) => (
              <tr key={d.id} className="border-t hover:bg-neutral-50/60">
                <td className="px-4 py-2">{d.id}</td>
                <td className="px-4 py-2">
                  {d.title}
                  {d.features?.anomaly_score !== undefined && (
                    <span className="ml-2 text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-700">
                      ML
                    </span>
                  )}
                </td>
                <td className="px-4 py-2 text-neutral-600">
                  {d.rule_id || "-"}
                </td>
                <td className="px-4 py-2">
                  <SeverityBadge level={d.severity} />
                </td>
                <td className="px-4 py-2">
                  <Badge variant="outline" className="capitalize">
                    {d.status}
                  </Badge>
                </td>
                <td className="px-4 py-2">
                  {new Date(d.created_at).toLocaleString()}
                </td>
                <td className="px-4 py-2">
                  <Link
                    href={`/detections/${d.id}`}
                    className="text-indigo-600 hover:underline"
                  >
                    View
                  </Link>
                </td>
              </tr>
            ))}
            {data?.length === 0 && (
              <tr>
                <td
                  colSpan={7}
                  className="px-4 py-8 text-center text-neutral-500"
                >
                  No detections yet. Generate some via the ingest script, then
                  run rules.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </main>
  );
}

function SeverityBadge({ level }: { level: string }) {
  const lv = level?.toLowerCase();
  let cls = "bg-neutral-200 text-neutral-800";
  if (lv === "low") cls = "bg-emerald-100 text-emerald-800";
  else if (lv === "medium") cls = "bg-yellow-100 text-yellow-800";
  else if (lv === "high") cls = "bg-orange-100 text-orange-800";
  else if (lv === "critical") cls = "bg-red-100 text-red-800";
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${cls}`}
    >
      {level}
    </span>
  );
}