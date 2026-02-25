"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import AppShell from "@/components/app-shell";
import StatusBadge from "@/components/status-badge";
import * as api from "@/lib/api";
import type { InvoiceListItem, InvoiceStatus } from "@/lib/types";

const STATUS_OPTIONS: { label: string; value: string }[] = [
  { label: "All", value: "" },
  { label: "Processing", value: "PROCESSING" },
  { label: "Failed", value: "EXTRACTION_FAILED" },
  { label: "Pending Review", value: "PENDING_REVIEW" },
  { label: "Approved", value: "APPROVED" },
  { label: "Booked", value: "BOOKED" },
];

export default function InvoicesPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const router = useRouter();
  const [invoices, setInvoices] = useState<InvoiceListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("");
  const [search, setSearch] = useState("");
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchInvoices = useCallback(async () => {
    setLoading(true);
    try {
      const params: Record<string, string> = {};
      if (statusFilter) params.status = statusFilter;
      if (search) params.search = search;
      const data = await api.getInvoices(orgId, params);
      setInvoices(data.results);
      setTotal(data.count);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [orgId, statusFilter, search]);

  useEffect(() => { fetchInvoices(); }, [fetchInvoices]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploading(true);
    try {
      const inv = await api.uploadInvoice(orgId, file);
      router.push(`/orgs/${orgId}/invoices/${inv.id}`);
    } catch {
      alert("Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <AppShell orgId={orgId}>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">Invoices</h1>
          <p className="text-sm text-gray-500">{total} total</p>
        </div>
        <div>
          <input ref={fileRef} type="file" accept=".pdf" onChange={handleUpload} className="hidden" id="upload" />
          <label
            htmlFor="upload"
            className="inline-flex cursor-pointer items-center rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
          >
            {uploading ? "Uploading..." : "Upload Invoice"}
          </label>
        </div>
      </div>

      {/* Filters */}
      <div className="mb-4 flex gap-3">
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm"
        >
          {STATUS_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
        <input
          type="text"
          placeholder="Search invoices..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="rounded-md border border-gray-300 px-3 py-1.5 text-sm"
        />
      </div>

      {/* Table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Invoice #</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Status</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Supplier</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Amount</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Date</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Uploaded</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="py-8 text-center text-sm text-gray-400">Loading...</td></tr>
            ) : invoices.length === 0 ? (
              <tr><td colSpan={6} className="py-8 text-center text-sm text-gray-400">No invoices found</td></tr>
            ) : (
              invoices.map((inv) => (
                <tr key={inv.id} className="cursor-pointer hover:bg-gray-50" onClick={() => router.push(`/orgs/${orgId}/invoices/${inv.id}`)}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{inv.invoice_number || "—"}</td>
                  <td className="px-4 py-3"><StatusBadge status={inv.status} /></td>
                  <td className="px-4 py-3 text-sm text-gray-600">{inv.supplier_name || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">
                    {inv.total_amount ? `${inv.total_amount} ${inv.currency || ""}` : "—"}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-600">{inv.invoice_date || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{new Date(inv.created_at).toLocaleDateString()}</td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </AppShell>
  );
}
