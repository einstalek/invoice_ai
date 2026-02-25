"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import { useGoogleLogin } from "@react-oauth/google";
import AppShell from "@/components/app-shell";
import * as api from "@/lib/api";
import type { Organization } from "@/lib/types";

const SHEETS_SCOPES =
  "https://www.googleapis.com/auth/spreadsheets https://www.googleapis.com/auth/drive.file";

const googleClientConfigured = !!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;

/** Extracted so useGoogleLogin only runs inside the GoogleOAuthProvider tree. */
function GoogleSheetsConnectButton({
  orgId,
  connecting,
  onConnecting,
  onSuccess,
  onError,
}: {
  orgId: string;
  connecting: boolean;
  onConnecting: () => void;
  onSuccess: () => void;
  onError: (msg: string) => void;
}) {
  const login = useGoogleLogin({
    flow: "auth-code",
    scope: SHEETS_SCOPES,
    onSuccess: async (response) => {
      onConnecting();
      try {
        await api.connectGoogleSheets(orgId, response.code);
        onSuccess();
      } catch (err) {
        onError(err instanceof Error ? err.message : "Failed to connect Google account");
      }
    },
    onError: () => {
      onError("Google authorization was cancelled or failed");
    },
  });

  return (
    <button
      type="button"
      onClick={() => login()}
      disabled={connecting}
      className="flex items-center gap-2 rounded-md border border-gray-300 bg-white px-3 py-1.5 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50"
    >
      <svg className="h-4 w-4" viewBox="0 0 24 24">
        <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92a5.06 5.06 0 0 1-2.2 3.32v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.1z" fill="#4285F4" />
        <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853" />
        <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05" />
        <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335" />
      </svg>
      {connecting ? "Connecting..." : "Connect Google Account"}
    </button>
  );
}

export default function SettingsPage() {
  const { orgId } = useParams<{ orgId: string }>();
  const [org, setOrg] = useState<Organization | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const [name, setName] = useState("");
  const [vatNumber, setVatNumber] = useState("");
  const [address, setAddress] = useState("");
  const [country, setCountry] = useState("");
  const [requiredApprovals, setRequiredApprovals] = useState(1);
  const [erpType, setErpType] = useState("NONE");
  const [spreadsheetId, setSpreadsheetId] = useState("");
  const [worksheetName, setWorksheetName] = useState("");

  // Google Sheets connection state
  const [sheetsConnected, setSheetsConnected] = useState(false);
  const [connecting, setConnecting] = useState(false);
  const [disconnecting, setDisconnecting] = useState(false);

  const loadOrg = useCallback(async () => {
    try {
      const data = await api.getOrg(orgId);
      setOrg(data);
      setName(data.name);
      setVatNumber(data.vat_number || "");
      setAddress(data.address || "");
      setCountry(data.country || "");
      setRequiredApprovals(data.required_approvals);
      setErpType(data.erp_type);
      if (data.erp_config) {
        const config = data.erp_config as Record<string, unknown>;
        setSpreadsheetId((config.spreadsheet_id as string) || "");
        setWorksheetName((config.worksheet_name as string) || "");
        setSheetsConnected(!!config.google_sheets_connected);
      } else {
        setSheetsConnected(false);
      }
    } catch {
      setError("Failed to load organization");
    }
  }, [orgId]);

  useEffect(() => {
    (async () => {
      setLoading(true);
      await loadOrg();
      setLoading(false);
    })();
  }, [loadOrg]);

  const handleDisconnect = async () => {
    setDisconnecting(true);
    setError("");
    setSuccess("");
    try {
      await api.disconnectGoogleSheets(orgId);
      await loadOrg();
      setSuccess("Google account disconnected");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to disconnect");
    } finally {
      setDisconnecting(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError("");
    setSuccess("");
    try {
      const payload: Record<string, unknown> = {
        name,
        vat_number: vatNumber || null,
        address: address || null,
        country: country || null,
        required_approvals: requiredApprovals,
        erp_type: erpType,
      };
      if (erpType === "GOOGLE_SHEETS") {
        // Only send spreadsheet config fields — the backend serializer
        // preserves existing google_credentials automatically.
        payload.erp_config = {
          spreadsheet_id: spreadsheetId || null,
          worksheet_name: worksheetName || "Sheet1",
        };
      } else {
        payload.erp_config = null;
      }
      const updated = await api.updateOrg(orgId, payload as Partial<Organization>);
      setOrg(updated);
      setSuccess("Settings saved");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <AppShell orgId={orgId}><div className="py-8 text-center text-gray-400">Loading...</div></AppShell>;
  if (!org) return <AppShell orgId={orgId}><div className="py-8 text-center text-red-500">{error || "Not found"}</div></AppShell>;

  return (
    <AppShell orgId={orgId}>
      <h1 className="mb-6 text-xl font-bold text-gray-900">Organization Settings</h1>

      <form onSubmit={handleSave} className="max-w-lg space-y-6">
        {/* General */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900">General</h3>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Organization Name *</label>
            <input type="text" value={name} onChange={(e) => setName(e.target.value)} required className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">VAT Number</label>
            <input type="text" value={vatNumber} onChange={(e) => setVatNumber(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Address</label>
            <input type="text" value={address} onChange={(e) => setAddress(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Country</label>
            <input type="text" value={country} onChange={(e) => setCountry(e.target.value)} className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none" />
          </div>
        </div>

        {/* Approvals */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900">Approval Workflow</h3>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">Required Approvals</label>
            <input
              type="number"
              min={1}
              max={10}
              value={requiredApprovals}
              onChange={(e) => setRequiredApprovals(parseInt(e.target.value) || 1)}
              className="w-24 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
            />
            <p className="mt-1 text-xs text-gray-500">
              Number of approvals required before an invoice can be booked.
            </p>
          </div>
        </div>

        {/* ERP Integration */}
        <div className="rounded-lg border border-gray-200 bg-white p-4 space-y-4">
          <h3 className="text-sm font-semibold text-gray-900">ERP Integration</h3>
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">ERP Type</label>
            <select
              value={erpType}
              onChange={(e) => setErpType(e.target.value)}
              className="w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm"
            >
              <option value="NONE">None</option>
              <option value="GOOGLE_SHEETS">Google Sheets</option>
              <option value="QUICKBOOKS">QuickBooks (coming soon)</option>
            </select>
          </div>
          {erpType === "GOOGLE_SHEETS" && (
            <div className="space-y-4">
              {/* Google Account Connection */}
              {!sheetsConnected ? (
                <div className="rounded-md border border-amber-200 bg-amber-50 p-3">
                  <p className="mb-2 text-sm text-amber-800">
                    Connect your Google account to allow invoice export to Google Sheets.
                  </p>
                  {googleClientConfigured ? (
                    <GoogleSheetsConnectButton
                      orgId={orgId}
                      connecting={connecting}
                      onConnecting={() => { setConnecting(true); setError(""); }}
                      onSuccess={async () => { await loadOrg(); setConnecting(false); setSuccess("Google account connected successfully"); }}
                      onError={(msg) => { setError(msg); setConnecting(false); }}
                    />
                  ) : (
                    <p className="text-sm text-gray-500">Google OAuth is not configured. Set NEXT_PUBLIC_GOOGLE_CLIENT_ID to enable.</p>
                  )}
                </div>
              ) : (
                <div className="rounded-md border border-green-200 bg-green-50 p-3">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <div className="h-2 w-2 rounded-full bg-green-500" />
                      <span className="text-sm font-medium text-green-800">Google Account Connected</span>
                    </div>
                    <button
                      type="button"
                      onClick={handleDisconnect}
                      disabled={disconnecting}
                      className="text-sm text-red-600 hover:text-red-700 disabled:opacity-50"
                    >
                      {disconnecting ? "Disconnecting..." : "Disconnect"}
                    </button>
                  </div>
                </div>
              )}

              {/* Spreadsheet config (shown regardless of connection status) */}
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Spreadsheet ID</label>
                <input
                  type="text"
                  value={spreadsheetId}
                  onChange={(e) => setSpreadsheetId(e.target.value)}
                  placeholder="e.g. 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
              <div>
                <label className="mb-1 block text-sm font-medium text-gray-700">Worksheet Name</label>
                <input
                  type="text"
                  value={worksheetName}
                  onChange={(e) => setWorksheetName(e.target.value)}
                  placeholder="Sheet1"
                  className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none"
                />
              </div>
            </div>
          )}
        </div>

        {error && <div className="rounded-md bg-red-50 p-3 text-sm text-red-700">{error}</div>}
        {success && <div className="rounded-md bg-green-50 p-3 text-sm text-green-700">{success}</div>}

        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-blue-600 px-4 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:opacity-50"
        >
          {saving ? "Saving..." : "Save Settings"}
        </button>
      </form>
    </AppShell>
  );
}
