"use client";

import { ReactNode, useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/lib/auth-context";
import { clsx } from "clsx";
import {
  DocumentTextIcon,
  BuildingOfficeIcon,
  UserGroupIcon,
  TruckIcon,
  Cog6ToothIcon,
  BellIcon,
  ArrowRightStartOnRectangleIcon,
} from "@heroicons/react/24/outline";
import * as api from "@/lib/api";
import type { Notification } from "@/lib/types";

export default function AppShell({ orgId, children }: { orgId: string; children: ReactNode }) {
  const { user, memberships, logout, loading } = useAuth();
  const pathname = usePathname();
  const router = useRouter();
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [showNotifs, setShowNotifs] = useState(false);

  const currentOrg = memberships.find((m) => m.organization.id === orgId);

  useEffect(() => {
    api.getNotifications(false).then((r) => setNotifications(r.results)).catch(() => {});
  }, [pathname]);

  if (loading) return <div className="flex min-h-screen items-center justify-center">Loading...</div>;
  if (!user) { router.replace("/login"); return null; }

  const nav = [
    { label: "Invoices", href: `/orgs/${orgId}/invoices`, icon: DocumentTextIcon },
    { label: "Suppliers", href: `/orgs/${orgId}/suppliers`, icon: TruckIcon },
    { label: "Members", href: `/orgs/${orgId}/members`, icon: UserGroupIcon },
    { label: "Settings", href: `/orgs/${orgId}/settings`, icon: Cog6ToothIcon },
  ];

  const handleMarkAllRead = async () => {
    await api.markAllNotificationsRead();
    setNotifications([]);
    setShowNotifs(false);
  };

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="flex w-56 flex-col border-r border-gray-200 bg-white">
        <div className="flex h-14 items-center border-b border-gray-200 px-4">
          <Link href="/dashboard" className="text-lg font-bold text-gray-900">Inflow</Link>
        </div>

        {/* Org selector */}
        <div className="border-b border-gray-200 p-3">
          <select
            value={orgId}
            onChange={(e) => router.push(`/orgs/${e.target.value}/invoices`)}
            className="w-full rounded-md border border-gray-300 bg-white px-2 py-1.5 text-sm font-medium text-gray-900"
          >
            {memberships.map((m) => (
              <option key={m.organization.id} value={m.organization.id}>
                {m.organization.name}
              </option>
            ))}
          </select>
        </div>

        <nav className="flex-1 space-y-1 p-3">
          {nav.map((item) => {
            const active = pathname.startsWith(item.href);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={clsx(
                  "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium",
                  active ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-100"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-gray-200 p-3">
          <div className="mb-2 truncate text-xs text-gray-500">{user.email}</div>
          <button onClick={logout} className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900">
            <ArrowRightStartOnRectangleIcon className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      {/* Main area */}
      <div className="flex flex-1 flex-col">
        {/* Top bar */}
        <header className="flex h-14 items-center justify-between border-b border-gray-200 bg-white px-6">
          <div className="text-sm text-gray-500">
            {currentOrg?.organization.name} &middot; {currentOrg?.role.toLowerCase()}
          </div>
          <div className="relative">
            <button onClick={() => setShowNotifs(!showNotifs)} className="relative rounded-md p-1.5 text-gray-500 hover:bg-gray-100">
              <BellIcon className="h-5 w-5" />
              {notifications.length > 0 && (
                <span className="absolute -right-0.5 -top-0.5 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] font-bold text-white">
                  {notifications.length}
                </span>
              )}
            </button>
            {showNotifs && (
              <div className="absolute right-0 top-10 z-50 w-80 rounded-lg border border-gray-200 bg-white shadow-lg">
                <div className="flex items-center justify-between border-b border-gray-100 px-4 py-2">
                  <span className="text-sm font-medium">Notifications</span>
                  {notifications.length > 0 && (
                    <button onClick={handleMarkAllRead} className="text-xs text-blue-600 hover:text-blue-500">
                      Mark all read
                    </button>
                  )}
                </div>
                <div className="max-h-64 overflow-y-auto">
                  {notifications.length === 0 ? (
                    <p className="p-4 text-center text-sm text-gray-400">No new notifications</p>
                  ) : (
                    notifications.map((n) => (
                      <div key={n.id} className="border-b border-gray-50 px-4 py-2.5 text-sm text-gray-700 last:border-0">
                        {n.title}
                        <div className="mt-0.5 text-xs text-gray-400">
                          {new Date(n.created_at).toLocaleDateString()}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
