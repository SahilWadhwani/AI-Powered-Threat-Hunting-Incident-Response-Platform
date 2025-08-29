import Link from "next/link";
import { Button } from "@/components/ui/button";

export default function Home() {
  return (
    <main className="grid place-items-center min-h-[70vh]">
      <div className="max-w-md text-center space-y-4">
        <h1 className="text-3xl font-semibold">SentinelX</h1>
        <p className="text-sm text-neutral-600">
          AI-powered threat hunting & incident response
        </p>
        <Button asChild>
          <Link href="/login">Go to Login</Link>
        </Button>
      </div>
    </main>
  );
}