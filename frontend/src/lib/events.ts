import { apiGet } from "./api";

export type EventRow = {
  id: number;
  timestamp: string;
  event_module: string;
  event_action: string;
  src_ip?: string | null;
  user?: string | null;
  http_path?: string | null;
  country?: string | null;
};

export async function fetchEvents(
  token: string,
  params: Record<string, string | number | undefined>
) {
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") q.set(k, String(v));
  }
  return apiGet<EventRow[]>(`/events?${q.toString()}`, token);
}