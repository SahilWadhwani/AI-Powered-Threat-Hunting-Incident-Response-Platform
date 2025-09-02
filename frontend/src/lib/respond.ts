import { apiGet, apiPost } from "./api";

export type BlockRule = {
  id: number;
  ip: string;                 // <-- changed from src_ip
  reason?: string;
  active: boolean;
  created_at: string;
  expires_at?: string | null;
};

export async function fetchBlocks(token: string) {
  return apiGet<BlockRule[]>("/respond/blocks", token);
}

export async function unblock(token: string, id: number) {
  return apiPost(`/respond/blocks/${id}/unblock`, {}, token);
}