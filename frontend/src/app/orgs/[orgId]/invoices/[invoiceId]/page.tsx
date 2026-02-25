"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/app-shell";
import StatusBadge from "@/components/status-badge";
import * as api from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { Invoice } from "@/lib/types";

const EDITABLE_FIELDS: { key: string; label: string; group: string }[] = [
  { key: "invoice_number", label: "Invoice Number", group: "Invoice" },
  { key: "invoice_date", label: "Invoice Date", group: "Invoice" },
  { key: "invoice_due_date", label: "Due Date", group: "Invoice" },
  { key: "total_amount", label: "Total Amount", group: "Invoice" },
  { key: "currency", label: "Currency", group: "Invoice" },
  { key: "description_keyword", label: "Description", group: "Invoice" },
  { key: "vat_rates", label: "VAT Rates", group: "Invoice" },
  { key: "supply_type", label: "Supply Type", group: "Invoice" },
  { key: "service_category", label: "Service Category", group: "Invoice" },
  { key: "supplier_name", label: "Supplier Name", group: "Supplier" },
  { key: "supplier_address", label: "Address", group: "Supplier" },
  { key: "supplier_country", label: "Country", group: "Supplier" },
  { key: "supplier_country_group", label: "Country Group", group: "Supplier" },
  { key: "supplier_vat_id", label: "VAT ID", group: "Supplier" },
  { key: "supplier_email", label: "Email", group: "Supplier" },
  { key: "buyer_name", label: "Buyer Name", group: "Buyer" },
  { key: "buyer_address", label: "Address", group: "Buyer" },
  { key: "buyer_country", label: "Country", group: "Buyer" },
  { key: "buyer_country_group", label: "Country Group", group: "Buyer" },
  { key: "buyer_vat_id", label: "VAT ID", group: "Buyer" },
  { key: "buyer_email", label: "Email", group: "Buyer" },
];

function getConfidence(invoice: Invoice, fieldKey: string): string | null {
  const llm = invoice.llm_raw_response;
  if (!llm) return null;
  const entry = llm[fieldKey] as { confidence?: string } | undefined;
  return entry?.confidence || null;
}

const confidenceColor: Record<string, string> = {
  "strong confidence": "text-green-600",
  "medium confidence": "text-yellow-600",
  "low confidence": "text-red-600",
  "definitely wrong": "text-red-800 font-bold",
};

export default function InvoiceDetailPage() {
  const { orgId, invoiceId } = useParams<{ orgId: string; invoiceId: string }>();
  const { user } = useAuth();
  const [invoice, setInvoice] = useState<Invoice | null>(null);
  const [loading, setLoading] = useState(true);
  const [editingField, setEditingField] = useState<string | null>(null);
  const [editValue, setEditValue] = useState("");
  const [savingField, setSavingField] = useState<string | null>(null);
  const [approving, setApproving] = useState(false);
  const [comment, setComment] = useState("");
  const [error, setError] = useState("");
  const [showPdf, setShowPdf] = useState(false);
  const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(new Set());

  const fetchInvoice = async () => {
    setLoading(true);
    try {
      const data = await api.getInvoice(orgId, invoiceId);
      setInvoice(data);
    } catch {
      setError("Failed to load invoice");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchInvoice(); }, [orgId, invoiceId]); // eslint-disable-line react-hooks/exhaustive-deps

  const startFieldEdit = (key: string) => {
    if (!invoice || (invoice.status !== "PENDING_REVIEW" && invoice.status !== "EXTRACTION_FAILED")) return;
    const v = (invoice as unknown as Record<string, unknown>)[key];
    setEditValue(v != null ? String(v) : "");
    setEditingField(key);
  };

  const saveFieldEdit = async (key: string) => {
    if (!invoice) return;
    const oldVal = (invoice as unknown as Record<string, unknown>)[key];
    const oldStr = oldVal != null ? String(oldVal) : "";
    const newStr = editValue;
    if (oldStr === newStr) { setEditingField(null); return; }
    setSavingField(key);
    setError("");
    try {
      const updated = await api.editInvoice(orgId, invoiceId, { [key]: newStr || null });
      setInvoice(updated);
      setEditingField(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSavingField(null);
    }
  };

  const handleApproval = async (decision: "APPROVED" | "EDIT_REQUESTED") => {
    if (decision === "EDIT_REQUESTED" && !comment.trim()) {
      setError("Comment required when requesting edits");
      return;
    }
    setApproving(true);
    setError("");
    try {
      const updated = await api.approveInvoice(orgId, invoiceId, decision, comment || undefined);
      setInvoice(updated);
      setComment("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Action failed");
    } finally {
      setApproving(false);
    }
  };

  const handleBook = async () => {
    setApproving(true);
    setError("");
    try {
      const updated = await api.bookInvoice(orgId, invoiceId);
      setInvoice(updated);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Booking failed");
    } finally {
      setApproving(false);
    }
  };

  if (loading) return <AppShell orgId={orgId}><div className="py-8 text-center text-gray-400">Loading...</div></AppShell>;
  if (!invoice) return <AppShell orgId={orgId}><div className="py-8 text-center text-red-500">{error || "Not found"}</div></AppShell>;

  const canEdit = invoice.status === "PENDING_REVIEW" || invoice.status === "EXTRACTION_FAILED";
  const canApprove = invoice.status === "PENDING_REVIEW" || invoice.status === "APPROVED";
  const canBook = invoice.status === "APPROVED";
  const userExistingReview = user ? invoice.approvals.find((a) => a.user.id === user.id) : null;

  const groups = ["Invoice", "Supplier", "Buyer"];

  return (
    <AppShell orgId={orgId}>
      {/* Header */}
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold text-gray-900">
            Invoice {invoice.invoice_number || invoice.id.slice(0, 8)}
          </h1>
          <div className="mt-1 flex items-center gap-3">
            <StatusBadge status={invoice.status} />
            <span className="text-sm text-gray-500">
              {invoice.approvals_obtained} approval(s)
            </span>
          </div>
        </div>
        <div className="flex gap-2">
          {invoice.pdf_file && (
            <button
              onClick={() => setShowPdf(!showPdf)}
              className="rounded-md border border-gray-300 px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              {showPdf ? "Hide PDF" : "View PDF"}
            </button>
          )}
          {canBook && (
            <button onClick={handleBook} disabled={approving} className="rounded-md bg-purple-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-purple-700 disabled:opacity-50">
              Book to ERP
            </button>
          )}
        </div>
      </div>

      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      <div className={`grid grid-cols-1 gap-6 ${showPdf ? "lg:grid-cols-2" : "lg:grid-cols-3"}`}>
        {/* Left column: extracted fields + review actions */}
        <div className={showPdf ? "" : "lg:col-span-2"}>
          <div className="space-y-6">
            {groups.map((group) => {
              const isCollapsed = collapsedGroups.has(group);
              return (
                <div key={group} className="rounded-lg border border-gray-200 bg-white">
                  <button
                    type="button"
                    onClick={() => {
                      const next = new Set(collapsedGroups);
                      if (isCollapsed) next.delete(group); else next.add(group);
                      setCollapsedGroups(next);
                    }}
                    className="flex w-full items-center justify-between border-b border-gray-200 px-4 py-2.5 text-left"
                  >
                    <h3 className="text-sm font-semibold text-gray-900">{group} Details</h3>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      className={`h-4 w-4 text-gray-400 transition-transform ${isCollapsed ? "" : "rotate-180"}`}
                      viewBox="0 0 20 20"
                      fill="currentColor"
                    >
                      <path fillRule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clipRule="evenodd" />
                    </svg>
                  </button>
                  {!isCollapsed && (
                    <div className="divide-y divide-gray-100">
                      {EDITABLE_FIELDS.filter((f) => f.group === group).map(({ key, label }) => {
                        const value = (invoice as unknown as Record<string, unknown>)[key];
                        const confidence = getConfidence(invoice, key);
                        const isEditing = editingField === key;
                        const isSaving = savingField === key;
                        return (
                          <div key={key} className="flex items-center gap-4 px-4 py-2.5">
                            <div className="w-36 text-xs font-medium text-gray-500">{label}</div>
                            <div className="flex-1">
                              {isEditing ? (
                                <input
                                  type="text"
                                  autoFocus
                                  value={editValue}
                                  onChange={(e) => setEditValue(e.target.value)}
                                  onBlur={() => saveFieldEdit(key)}
                                  onKeyDown={(e) => {
                                    if (e.key === "Enter") saveFieldEdit(key);
                                    if (e.key === "Escape") setEditingField(null);
                                  }}
                                  disabled={isSaving}
                                  className="w-full rounded border border-gray-300 px-2 py-1 text-sm focus:border-blue-500 focus:outline-none disabled:opacity-50"
                                />
                              ) : (
                                <span
                                  onClick={() => startFieldEdit(key)}
                                  className={`text-sm text-gray-900 ${canEdit ? "cursor-pointer rounded px-1 -mx-1 hover:bg-gray-100" : ""}`}
                                >
                                  {value != null ? String(value) : "—"}
                                </span>
                              )}
                            </div>
                            {confidence && !isEditing && (
                              <span className={`text-xs ${confidenceColor[confidence] || "text-gray-400"}`}>
                                {confidence}
                              </span>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              );
            })}

            {/* Approval actions */}
            {canApprove && (
              <div className="rounded-lg border border-gray-200 bg-white p-4">
                <h3 className="mb-3 text-sm font-semibold text-gray-900">Review</h3>
                <textarea
                  placeholder="Comment (required for edit requests)..."
                  value={comment}
                  onChange={(e) => setComment(e.target.value)}
                  rows={2}
                  className="mb-3 w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
                <div className="flex gap-2">
                  <button
                    onClick={() => handleApproval("APPROVED")}
                    disabled={approving || !!userExistingReview}
                    className="rounded-md bg-green-600 px-4 py-2 text-sm font-medium text-white hover:bg-green-700 disabled:opacity-50"
                  >
                    {userExistingReview?.decision === "APPROVED" ? "Approved" : "Approve"}
                  </button>
                  <button
                    onClick={() => handleApproval("EDIT_REQUESTED")}
                    disabled={approving || !!userExistingReview}
                    className="rounded-md bg-orange-600 px-4 py-2 text-sm font-medium text-white hover:bg-orange-700 disabled:opacity-50"
                  >
                    {userExistingReview?.decision === "EDIT_REQUESTED" ? "Edits Requested" : "Request Edits"}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Right column: approvals, activity, extraction error, PDF */}
        <div className="space-y-6">
          {invoice.approvals.length > 0 && (
            <div className="rounded-lg border border-gray-200 bg-white p-4">
              <h3 className="mb-2 text-sm font-semibold text-gray-900">Approvals</h3>
              <div className="space-y-2">
                {invoice.approvals.map((a) => (
                  <div key={a.id} className="text-sm">
                    <span className="font-medium text-gray-900">{a.user.full_name || a.user.email}</span>
                    <span className={a.decision === "APPROVED" ? " text-green-600" : " text-orange-600"}>
                      {" "}{a.decision === "APPROVED" ? "approved" : "requested edits"}
                    </span>
                    {a.comment && <p className="mt-0.5 text-xs text-gray-500">{a.comment}</p>}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="rounded-lg border border-gray-200 bg-white p-4">
            <h3 className="mb-2 text-sm font-semibold text-gray-900">Activity</h3>
            <div className="space-y-3">
              {invoice.activities.map((a) => (
                <div key={a.id} className="border-l-2 border-gray-200 pl-3">
                  <div className="text-sm font-medium text-gray-900">{a.action.replace(/_/g, " ").toLowerCase()}</div>
                  <div className="text-xs text-gray-500">
                    {a.user ? a.user.full_name || a.user.email : "System"} &middot; {new Date(a.created_at).toLocaleString()}
                  </div>
                  {a.comment && <p className="mt-0.5 text-xs text-gray-600">{a.comment}</p>}
                  {a.changes && (
                    <div className="mt-1 space-y-0.5">
                      {Object.entries(a.changes).map(([field, diff]) => (
                        <div key={field} className="text-xs text-gray-500">
                          <span className="font-medium">{field}</span>: <span className="line-through text-red-400">{diff.old || "empty"}</span> &rarr; <span className="text-green-600">{diff.new || "empty"}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {invoice.extraction_error && (
            <div className="rounded-lg border border-red-200 bg-red-50 p-4">
              <h3 className="mb-1 text-sm font-semibold text-red-800">Extraction Error</h3>
              <p className="text-xs text-red-700">{invoice.extraction_error}</p>
            </div>
          )}

          {/* Inline PDF viewer */}
          {showPdf && invoice.pdf_file && (
            <div className="relative rounded-lg border border-gray-200 bg-white lg:sticky lg:top-4 h-[calc(100vh-7rem)]">
              <button
                onClick={() => setShowPdf(false)}
                className="absolute right-2 top-2 z-10 rounded-full bg-white/80 p-1 text-gray-500 shadow hover:bg-gray-100 hover:text-gray-700"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
              <iframe
                src={invoice.pdf_file}
                className="h-full w-full rounded-lg"
                title="Invoice PDF"
              />
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
