"use client";
import { useState } from "react";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useAuth } from "@/store/auth";
import { fetchEvents, EventRow } from "@/lib/events";

export default function EventsPage() {
  const { accessToken } = useAuth();

  // filters
  const [event_module, setModule] = useState<string>("");
  const [event_action, setAction] = useState<string>("");
  const [src_ip, setSrcIp] = useState<string>("");
  const [user, setUser] = useState<string>("");
  const [start, setStart] = useState<string>(""); // ISO 8601
  const [end, setEnd] = useState<string>("");     // ISO 8601
  const [limit, setLimit] = useState<number>(50);
  const [offset, setOffset] = useState<number>(0);

  const {
    data = [],                 // default to empty array -> safe for map/length
    isLoading,
    error,
    refetch,
  } = useQuery<EventRow[]>({
    queryKey: ["events", accessToken, event_module, event_action, src_ip, user, start, end, limit, offset],
    queryFn: () =>
      fetchEvents(accessToken || "", {
        event_module,
        event_action,
        src_ip,
        user,
        start,
        end,
        limit,
        offset,
      }),
    enabled: !!accessToken,
    placeholderData: keepPreviousData, // v5 replacement for keepPreviousData option
  });

  function applyFilters() {
    setOffset(0);
    refetch();
  }

  return (
    <main className="p-6 space-y-4">
      <h1 className="text-2xl font-semibold">Events</h1>

      <div className="rounded-lg border bg-white p-4">
        <div className="grid md:grid-cols-3 gap-3">
          <TextField label="Module" value={event_module} onChange={setModule} placeholder="auth / nginx / cloudtrail ..." />
          <TextField label="Action" value={event_action} onChange={setAction} placeholder="ssh_login_failed ..." />
          <TextField label="Src IP" value={src_ip} onChange={setSrcIp} placeholder="203.0.113.77" />
          <TextField label="User" value={user} onChange={setUser} placeholder="alice" />
          <TextField label="Start (ISO)" value={start} onChange={setStart} placeholder="2025-08-27T00:00:00Z" />
          <TextField label="End (ISO)" value={end} onChange={setEnd} placeholder="2025-08-28T00:00:00Z" />
        </div>
        <div className="mt-3 flex items-center gap-2">
          <button onClick={applyFilters} className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50">Apply</button>
          <button
            onClick={() => {
              setModule("");
              setAction("");
              setSrcIp("");
              setUser("");
              setStart("");
              setEnd("");
              setOffset(0);
              refetch();
            }}
            className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50"
          >
            Reset
          </button>
        </div>
      </div>

      <div className="overflow-x-auto rounded-lg border bg-white">
        {isLoading && <p className="p-4 text-sm">Loading…</p>}
        {error && <p className="p-4 text-sm text-red-600">Failed to load.</p>}

        <table className="w-full text-sm">
          <thead className="bg-neutral-50 text-neutral-700">
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
            {data.map((e) => (
              <tr key={e.id} className="border-t hover:bg-neutral-50/60">
                <td className="px-4 py-2">{e.id}</td>
                <td className="px-4 py-2">{new Date(e.timestamp).toLocaleString()}</td>
                <td className="px-4 py-2">{e.event_module}</td>
                <td className="px-4 py-2">{e.event_action}</td>
                <td className="px-4 py-2">{e.src_ip || "-"}</td>
                <td className="px-4 py-2">{e.user || "-"}</td>
                <td className="px-4 py-2">{e.http_path || "-"}</td>
                <td className="px-4 py-2">{e.country || "-"}</td>
              </tr>
            ))}
            {data.length === 0 && (
              <tr>
                <td colSpan={8} className="px-4 py-8 text-center text-neutral-500">
                  No events.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setOffset(Math.max(0, offset - limit))}
          disabled={offset === 0}
          className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50 disabled:opacity-50"
        >
          Prev
        </button>
        <button
          onClick={() => setOffset(offset + limit)}
          className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50"
        >
          Next
        </button>
        <span className="text-sm text-neutral-600">offset {offset}</span>
      </div>
    </main>
  );
}

function TextField({
  label,
  value,
  onChange,
  placeholder,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="space-y-1">
      <label className="text-neutral-600 text-xs">{label}</label>
      <input
        className="w-full rounded-md border px-3 py-2 text-sm"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
      />
    </div>
  );
}