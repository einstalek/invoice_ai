"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import * as api from "@/lib/api";
import type { PendingInvite } from "@/lib/types";
import Link from "next/link";

export default function DashboardPage() {
  const { user, memberships, loading, refreshMemberships } = useAuth();
  const router = useRouter();
  const [pendingInvites, setPendingInvites] = useState<PendingInvite[]>([]);
  const [acceptingId, setAcceptingId] = useState<string | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!loading && !user) router.replace("/login");
  }, [loading, user, router]);

  useEffect(() => {
    if (!loading && user) {
      api.getMyPendingInvites().then(setPendingInvites).catch(() => {});
    }
  }, [loading, user]);

  useEffect(() => {
    // Auto-redirect to first org if user has exactly one and no pending invites
    if (!loading && memberships.length === 1 && pendingInvites.length === 0) {
      router.replace(`/orgs/${memberships[0].organization.id}/invoices`);
    }
  }, [loading, memberships, pendingInvites, router]);

  const handleAccept = async (invite: PendingInvite) => {
    setAcceptingId(invite.id);
    setError("");
    try {
      await api.acceptInvite(invite.organization.id);
      setPendingInvites((prev) => prev.filter((i) => i.id !== invite.id));
      await refreshMemberships();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to accept invite");
    } finally {
      setAcceptingId(null);
    }
  };

  if (loading) return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
  if (!user) return null;

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 px-4">
      <div className="w-full max-w-md">
        <h1 className="mb-2 text-2xl font-bold text-gray-900">Welcome, {user.full_name || user.email}</h1>
        <p className="mb-6 text-sm text-gray-500">Select an organization or create a new one.</p>

        {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

        {pendingInvites.length > 0 && (
          <div className="mb-6">
            <h2 className="mb-2 text-sm font-semibold text-gray-900">Pending Invites</h2>
            <div className="space-y-2">
              {pendingInvites.map((invite) => (
                <div
                  key={invite.id}
                  className="flex items-center justify-between rounded-lg border border-blue-200 bg-blue-50 p-4"
                >
                  <div>
                    <div className="font-medium text-gray-900">{invite.organization.name}</div>
                    <div className="text-xs text-gray-500">Invited as {invite.role.toLowerCase()}</div>
                  </div>
                  <button
                    onClick={() => handleAccept(invite)}
                    disabled={acceptingId === invite.id}
                    className="rounded-md bg-blue-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
                  >
                    {acceptingId === invite.id ? "Joining..." : "Accept"}
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {memberships.length > 0 && (
          <div className="space-y-2">
            {memberships.map((m) => (
              <Link
                key={m.organization.id}
                href={`/orgs/${m.organization.id}/invoices`}
                className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-4 hover:border-blue-300 hover:shadow-sm"
              >
                <div>
                  <div className="font-medium text-gray-900">{m.organization.name}</div>
                  <div className="text-xs text-gray-500">{m.role.toLowerCase()}</div>
                </div>
                <span className="text-gray-400">&rarr;</span>
              </Link>
            ))}
          </div>
        )}

        <Link
          href="/orgs/new"
          className="mt-4 flex w-full items-center justify-center rounded-lg border-2 border-dashed border-gray-300 bg-white p-4 text-sm font-medium text-gray-600 hover:border-blue-400 hover:text-blue-600"
        >
          + Create new organization
        </Link>
      </div>
    </div>
  );
}
