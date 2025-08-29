import { apiGet, apiPost } from "./api";

export type CaseRow = {
  id: number; title: string; severity: string; status: string; assignee: string | null; updated_at: string;
};

export type CaseDetail = {
  id: number; title: string; description?: string | null; severity: string; status: string; assignee: string | null;
  detection_ids: number[]; created_at: string; updated_at: string;
  comments: { id: number; author: string; created_at: string; body: string }[];
};

export async function fetchCases(token: string) {
  return apiGet<CaseRow[]>("/cases", token);
}
export async function fetchCase(token: string, id: number) {
  return apiGet<CaseDetail>(`/cases/${id}`, token);
}
export async function createCase(token: string, payload: {
  title: string; description?: string; severity?: string;
  detection_ids?: number[]; assignee?: string | null;
}) {
  return apiPost<{ id: number; title: string; severity: string; status: string; assignee: string | null }>(
    "/cases", payload, token
  );
}
export async function setStatus(token: string, id: number, newStatus: string) {
  return apiPost(`/cases/${id}/status?new_status=${encodeURIComponent(newStatus)}`, {}, token);
}
export async function setAssignee(token: string, id: number, assignee: string) {
  return apiPost(`/cases/${id}/assignee?assignee=${encodeURIComponent(assignee)}`, {}, token);
}
export async function addComment(token: string, id: number, body: string) {
  return apiPost(`/cases/${id}/comment`, { body }, token); // backend expects raw body
}