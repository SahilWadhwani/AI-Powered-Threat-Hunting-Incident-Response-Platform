"use client";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@/store/auth";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchCase, setStatus, setAssignee, addComment, CaseDetail } from "@/lib/cases";
import { toast } from "sonner";
import { useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Input } from "@/components/ui/input";
import Link from "next/link";

export default function CaseDetailPage() {
  const params = useParams<{ id: string }>();
  const id = Number(params.id);
  const { accessToken, user } = useAuth();
  const qc = useQueryClient();
  const router = useRouter();

  const { data, isLoading, error } = useQuery({
    queryKey: ["case", id, accessToken],
    queryFn: () => fetchCase(accessToken || "", id),
    enabled: !!accessToken && !!id,
  });

  const [assignee, setAssigneeInput] = useState(user?.email || "");
  const [newComment, setNewComment] = useState("");

  const statusMut = useMutation({
    mutationFn: (s: string) => setStatus(accessToken || "", id, s),
    onSuccess: () => { toast.success("Status updated"); qc.invalidateQueries({ queryKey: ["case", id, accessToken] }); },
    onError: (e: any) => toast.error("Failed to update status", { description: e.message })
  });

  const assigneeMut = useMutation({
    mutationFn: () => setAssignee(accessToken || "", id, assignee),
    onSuccess: () => { toast.success("Assignee updated"); qc.invalidateQueries({ queryKey: ["case", id, accessToken] }); },
    onError: (e: any) => toast.error("Failed to set assignee", { description: e.message })
  });

  const commentMut = useMutation({
    mutationFn: () => addComment(accessToken || "", id, newComment),
    onSuccess: () => { toast.success("Comment added"); setNewComment(""); qc.invalidateQueries({ queryKey: ["case", id, accessToken] }); },
    onError: (e: any) => toast.error("Failed to add comment", { description: e.message })
  });

  return (
    <main className="p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Case #{id}</h1>
        <Link href="/cases" className="text-indigo-600 hover:underline">← Back</Link>
      </div>

      {isLoading && <p className="text-sm">Loading…</p>}
      {error && <p className="text-sm text-red-600">Failed to load case.</p>}

      {data && <CaseContent data={data} assignee={assignee} setAssigneeInput={setAssigneeInput}
                            statusMut={statusMut} assigneeMut={assigneeMut}
                            newComment={newComment} setNewComment={setNewComment} commentMut={commentMut} />}
    </main>
  );
}

function CaseContent({
  data, assignee, setAssigneeInput,
  statusMut, assigneeMut, newComment, setNewComment, commentMut
}: {
  data: CaseDetail;
  assignee: string;
  setAssigneeInput: (v: string) => void;
  statusMut: any; assigneeMut: any; newComment: string; setNewComment: (v: string) => void; commentMut: any;
}) {
  return (
    <div className="grid gap-6 md:grid-cols-3">
      <section className="md:col-span-2 space-y-3">
        <div className="rounded-lg border bg-white p-4">
          <h2 className="font-medium">{data.title}</h2>
          <p className="text-sm text-neutral-600 mt-1">{data.description || "—"}</p>
          <div className="mt-3 text-sm space-x-2">
            <Badge label="Severity" value={data.severity} />
            <Badge label="Status" value={data.status} />
            <Badge label="Assignee" value={data.assignee || "—"} />
            <Badge label="Updated" value={new Date(data.updated_at).toLocaleString()} />
          </div>
          {data.detection_ids.length > 0 && (
            <div className="mt-3 text-sm">
              Linked detections:{" "}
              {data.detection_ids.map((d, i) => (
                <Link key={d} className="text-indigo-600 hover:underline mr-2" href={`/detections/${d}`}>#{d}</Link>
              ))}
            </div>
          )}
        </div>

        <div className="rounded-lg border bg-white">
          <div className="border-b px-4 py-2 font-medium">Comments</div>
          <div className="p-4 space-y-4">
            {data.comments.length === 0 && <p className="text-sm text-neutral-500">No comments yet.</p>}
            {data.comments.map(cm => (
              <div key={cm.id} className="text-sm">
                <div className="font-medium">{cm.author} <span className="text-neutral-500 text-xs">({new Date(cm.created_at).toLocaleString()})</span></div>
                <div className="whitespace-pre-wrap">{cm.body}</div>
              </div>
            ))}

            <div className="pt-2 border-t">
              <Textarea value={newComment} onChange={e => setNewComment(e.target.value)} placeholder="Add a comment…" />
              <div className="mt-2">
                <button
                  onClick={() => newComment.trim() && commentMut.mutate()}
                  disabled={commentMut.isPending || !newComment.trim()}
                  className="px-3 py-2 rounded-md bg-neutral-900 text-white hover:bg-black"
                >
                  {commentMut.isPending ? "Posting…" : "Post comment"}
                </button>
              </div>
            </div>
          </div>
        </div>
      </section>

      <aside className="space-y-3">
        <div className="rounded-lg border bg-white p-4">
          <h3 className="font-medium mb-2">Update</h3>
          <div className="text-sm space-y-2">
            <div className="space-y-1">
              <label className="text-neutral-600 text-xs">Assignee</label>
              <Input value={assignee} onChange={e => setAssigneeInput(e.target.value)} placeholder="email" />
              <button onClick={() => assigneeMut.mutate()} className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50">Set assignee</button>
            </div>
            <div className="space-y-1">
              <label className="text-neutral-600 text-xs">Status</label>
              <div className="flex gap-2">
                {["open","triaged","closed"].map(s => (
                  <button key={s} onClick={() => statusMut.mutate(s)}
                    className="px-3 py-2 rounded-md border bg-white hover:bg-neutral-50 capitalize">{s}</button>
                ))}
              </div>
            </div>
          </div>
        </div>
      </aside>
    </div>
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