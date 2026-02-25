"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import AppShell from "@/components/app-shell";
import * as api from "@/lib/api";
import type { Supplier } from "@/lib/types";

const EMPTY_SUPPLIER = { name: "", vat_id: "", address: "", country: "", country_group: "", email: "" };

export default function SuppliersPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [form, setForm] = useState(EMPTY_SUPPLIER);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const data = await api.getSuppliers(orgId);
      setSuppliers(data.results);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchSuppliers(); }, [orgId]); // eslint-disable-line react-hooks/exhaustive-deps

  const openCreate = () => {
    setForm(EMPTY_SUPPLIER);
    setEditingId(null);
    setShowForm(true);
    setError("");
  };

  const openEdit = (s: Supplier) => {
    setForm({
      name: s.name,
      vat_id: s.vat_id || "",
      address: s.address || "",
      country: s.country || "",
      country_group: s.country_group || "",
      email: s.email || "",
    });
    setEditingId(s.id);
    setShowForm(true);
    setError("");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.name.trim()) return;
    setSaving(true);
    setError("");
    try {
      const payload: Record<string, unknown> = { name: form.name };
      if (form.vat_id) payload.vat_id = form.vat_id;
      if (form.address) payload.address = form.address;
      if (form.country) payload.country = form.country;
      if (form.country_group) payload.country_group = form.country_group;
      if (form.email) payload.email = form.email;

      if (editingId) {
        await api.updateSupplier(orgId, editingId, payload);
      } else {
        await api.createSupplier(orgId, payload);
      }
      setShowForm(false);
      fetchSuppliers();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  const setField = (key: string, value: string) => setForm({ ...form, [key]: value });

  return (
    <AppShell orgId={orgId}>
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-xl font-bold text-gray-900">Suppliers</h1>
        <button
          onClick={openCreate}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700"
        >
          Add Supplier
        </button>
      </div>

      {error && <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}

      {/* Inline form */}
      {showForm && (
        <form onSubmit={handleSubmit} className="mb-6 space-y-3 rounded-lg border border-gray-200 bg-white p-4">
          <h3 className="text-sm font-semibold text-gray-900">{editingId ? "Edit Supplier" : "New Supplier"}</h3>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Name *</label>
              <input type="text" value={form.name} onChange={(e) => setField("name", e.target.value)} required className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">VAT ID</label>
              <input type="text" value={form.vat_id} onChange={(e) => setField("vat_id", e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Address</label>
              <input type="text" value={form.address} onChange={(e) => setField("address", e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Country</label>
              <input type="text" value={form.country} onChange={(e) => setField("country", e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Country Group</label>
              <select value={form.country_group} onChange={(e) => setField("country_group", e.target.value)} className="w-full rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm">
                <option value="">—</option>
                <option value="EE">EE (Estonia)</option>
                <option value="EU_OTHER">EU (Other)</option>
                <option value="NON_EU">Non-EU</option>
              </select>
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-600">Email</label>
              <input type="email" value={form.email} onChange={(e) => setField("email", e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-1.5 text-sm focus:border-blue-500 focus:outline-none" />
            </div>
          </div>
          <div className="flex gap-2">
            <button type="submit" disabled={saving} className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50">
              {saving ? "Saving..." : editingId ? "Update" : "Create"}
            </button>
            <button type="button" onClick={() => setShowForm(false)} className="rounded-md border border-gray-300 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50">
              Cancel
            </button>
          </div>
        </form>
      )}

      {/* Suppliers table */}
      <div className="overflow-hidden rounded-lg border border-gray-200 bg-white">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Name</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">VAT ID</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Country</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Group</th>
              <th className="px-4 py-3 text-left text-xs font-medium uppercase text-gray-500">Email</th>
              <th className="px-4 py-3 text-right text-xs font-medium uppercase text-gray-500">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {loading ? (
              <tr><td colSpan={6} className="py-8 text-center text-sm text-gray-400">Loading...</td></tr>
            ) : suppliers.length === 0 ? (
              <tr><td colSpan={6} className="py-8 text-center text-sm text-gray-400">No suppliers yet</td></tr>
            ) : (
              suppliers.map((s) => (
                <tr key={s.id}>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{s.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.vat_id || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.country || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.country_group || "—"}</td>
                  <td className="px-4 py-3 text-sm text-gray-600">{s.email || "—"}</td>
                  <td className="px-4 py-3 text-right">
                    <button onClick={() => openEdit(s)} className="text-sm text-blue-600 hover:text-blue-500">
                      Edit
                    </button>
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
