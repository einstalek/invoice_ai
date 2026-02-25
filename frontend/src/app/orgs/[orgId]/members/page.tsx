"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/app-shell";
import * as api from "@/lib/api";
import type { Membership } from "@/lib/types";

const roleBadge: Record<string, string> = {
  OWNER: "bg-purple-100 text-purple-800",
  ACCOUNTANT: "bg-blue-100 text-blue-800",
};

const statusBadge: Record<string, string> = {
  ACTIVE: "bg-green-100 text-green-800",
  PENDING: "bg-yellow-100 text-yellow-800",
  DEACTIVATED: "bg-gray-100 text-gray-500",
};

export default function MembersPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const [members, setMembers] = useState<Membership[]>([]);
  const [loading, setLoading] = useState(true);
  const [inviteEmail, setInviteEmail] = useState("");
  const [inviteRole, setInviteRole] = useState<"OWNER" | "ACCOUNTANT">("ACCOUNTANT");
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchMembers = async () => {
    setLoading(true);
    try {
      const data = await api.getMembers(orgId);
      setMembers(data.results);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchMembers(); }, [orgId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleInvite = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!inviteEmail.trim()) return;
    setInviting(true);
    setError("");
    setSuccess("");
    try {
      await api.inviteMember(orgId, inviteEmail.trim(), inviteRole);
      setSuccess(`Invitation sent to ${inviteEmail}`);
      setInviteEmail("");
      fetchMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to invite member");
    } finally {
      setInviting(false);
    }
  };

  const handleDeactivate = async (memberId: string) => {
    if (!confirm("Deactivate this member?")) return;
    try {
      await api.deactivateMember(orgId, memberId);
      fetchMembers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to deactivate member");
    }
  };

  return (
    <AppShell orgId={orgId}>
      <h1 className="mb-6 text-xl font-bold text-gray-900">Members</h1>

      {/* Invite form */}
      <form onSubmit={handleInvite} className="mb-6 flex items-end gap-3 rounded-lg border border-gray-200 bg-white p-4">
        <div className="flex-1">
          <label className="mb-1 block text-sm font-medium text-gray-700">Email address</label>
          <input
            type="email"
            value={inviteEmail}
            onChange={(e) => setInviteEmail(e.target.value)}
            placeholder="colleague@company.com"
            required
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
          />
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-700">Role</label>
          <select
            value={inviteRole}
            onChange={(e) => setInviteRole(e.target.value as "OWNER" | "ACCOUNTANT")}
            className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
          >
            <option value="ACCOUNTANT">Accountant</option>
            <option value="OWNER">Owner</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={inviting}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {inviting ? "Inviting..." : "Invite"}
        </button>
      </form>

      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {success && <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</div>}

      {/* Members table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">User</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Role</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Joined</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={5} className="py-8 text-center text-sm text-gray-400">Loading...</td></tr>
            ) : members.length === 0 ? (
              <tr><td colSpan={5} className="py-8 text-center text-sm text-gray-400">No members</td></tr>
            ) : (
              members.map((m) => (
                <tr key={m.id}>
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-gray-900">
                      {m.user ? m.user.full_name || m.user.email : m.invited_email}
                    </div>
                    {m.user && m.user.full_name && (
                      <div className="text-xs text-gray-500">{m.user.email}</div>
                    )}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${roleBadge[m.role] || ""}`}>
                      {m.role.toLowerCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-flex rounded-full px-2 py-0.5 text-xs font-medium ${statusBadge[m.status] || ""}`}>
                      {m.status.toLowerCase()}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">
                    {new Date(m.created_at).toLocaleDateString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    {m.status === "ACTIVE" && m.role !== "OWNER" && (
                      <button
                        onClick={() => handleDeactivate(m.id)}
                        className="text-sm text-red-600 hover:text-red-500"
                      >
                        Deactivate
                      </button>
                    )}
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
