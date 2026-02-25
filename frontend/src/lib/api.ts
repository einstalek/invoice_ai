const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

type Method = "GET" | "POST" | "PATCH" | "PUT" | "DELETE";

class ApiError extends Error {
  status: number;
  data: unknown;
  constructor(status: number, data: unknown) {
    super(typeof data === "object" && data && "detail" in data ? String((data as { detail: string }).detail) : `Request failed with status ${status}`);
    this.status = status;
    this.data = data;
  }
}

function getTokens() {
  if (typeof window === "undefined") return { access: null, refresh: null };
  return {
    access: localStorage.getItem("access_token"),
    refresh: localStorage.getItem("refresh_token"),
  };
}

function setTokens(access: string, refresh: string) {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

function clearTokens() {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

async function refreshAccessToken(): Promise<string | null> {
  const { refresh } = getTokens();
  if (!refresh) return null;
  try {
    const res = await fetch(`${API_BASE}/api/auth/token/refresh/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh }),
    });
    if (!res.ok) {
      clearTokens();
      return null;
    }
    const data = await res.json();
    setTokens(data.access, data.refresh);
    return data.access;
  } catch {
    clearTokens();
    return null;
  }
}

async function request<T>(method: Method, path: string, body?: unknown, isFormData = false): Promise<T> {
  let { access } = getTokens();

  const doFetch = (token: string | null) => {
    const headers: Record<string, string> = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;
    if (!isFormData) headers["Content-Type"] = "application/json";

    return fetch(`${API_BASE}${path}`, {
      method,
      headers,
      body: isFormData ? (body as FormData) : body ? JSON.stringify(body) : undefined,
    });
  };

  let res = await doFetch(access);

  // If 401, try refreshing the token once
  if (res.status === 401 && access) {
    const newToken = await refreshAccessToken();
    if (newToken) {
      res = await doFetch(newToken);
    }
  }

  if (!res.ok) {
    const data = await res.json().catch(() => null);
    throw new ApiError(res.status, data);
  }

  if (res.status === 204) return undefined as T;
  return res.json();
}

// ---- Auth ----
export async function login(email: string, password: string) {
  const data = await request<{ access: string; refresh: string; user: import("./types").User }>(
    "POST", "/api/auth/login/", { email, password }
  );
  setTokens(data.access, data.refresh);
  return data.user;
}

export async function register(email: string, password: string, fullName: string) {
  const data = await request<{ access: string; refresh: string; user: import("./types").User }>(
    "POST", "/api/auth/registration/", { email, password1: password, password2: password, full_name: fullName }
  );
  setTokens(data.access, data.refresh);
  return data.user;
}

export async function googleLogin(code: string) {
  const data = await request<{ access: string; refresh: string; user: import("./types").User }>(
    "POST", "/api/auth/google/", { code }
  );
  setTokens(data.access, data.refresh);
  return data.user;
}

export function logout() {
  clearTokens();
}

export function isLoggedIn() {
  return !!getTokens().access;
}

export async function getMe() {
  return request<import("./types").User>("GET", "/api/auth/me/");
}

export async function getMyMemberships() {
  return request<import("./types").UserMembership[]>("GET", "/api/auth/me/memberships/");
}

export async function getMyPendingInvites() {
  return request<import("./types").PendingInvite[]>("GET", "/api/auth/me/pending-invites/");
}

// ---- Organizations ----
export async function getOrgs() {
  return request<import("./types").PaginatedResponse<import("./types").Organization>>("GET", "/api/orgs/");
}

export async function getOrg(orgId: string) {
  return request<import("./types").Organization>("GET", `/api/orgs/${orgId}/`);
}

export async function createOrg(data: { name: string; vat_number?: string; address?: string; country?: string }) {
  return request<import("./types").Organization>("POST", "/api/orgs/", data);
}

export async function updateOrg(orgId: string, data: Partial<import("./types").Organization>) {
  return request<import("./types").Organization>("PATCH", `/api/orgs/${orgId}/`, data);
}

// ---- Members ----
export async function getMembers(orgId: string) {
  return request<import("./types").PaginatedResponse<import("./types").Membership>>("GET", `/api/orgs/${orgId}/members/`);
}

export async function inviteMember(orgId: string, email: string, role: string) {
  return request<import("./types").Membership>("POST", `/api/orgs/${orgId}/members/invite/`, { email, role });
}

export async function acceptInvite(orgId: string) {
  return request<import("./types").Membership>("POST", `/api/orgs/${orgId}/members/accept/`);
}

export async function deactivateMember(orgId: string, memberId: string) {
  return request<import("./types").Membership>("POST", `/api/orgs/${orgId}/members/${memberId}/deactivate/`);
}

// ---- Suppliers ----
export async function getSuppliers(orgId: string) {
  return request<import("./types").PaginatedResponse<import("./types").Supplier>>("GET", `/api/orgs/${orgId}/suppliers/`);
}

export async function createSupplier(orgId: string, data: Partial<import("./types").Supplier>) {
  return request<import("./types").Supplier>("POST", `/api/orgs/${orgId}/suppliers/`, data);
}

export async function updateSupplier(orgId: string, supplierId: string, data: Partial<import("./types").Supplier>) {
  return request<import("./types").Supplier>("PATCH", `/api/orgs/${orgId}/suppliers/${supplierId}/`, data);
}

// ---- Google Sheets OAuth ----
export async function connectGoogleSheets(orgId: string, code: string) {
  return request<{ connected: boolean }>("POST", `/api/orgs/${orgId}/google-sheets/connect/`, { code });
}

export async function disconnectGoogleSheets(orgId: string) {
  return request<{ connected: boolean }>("POST", `/api/orgs/${orgId}/google-sheets/disconnect/`);
}

// ---- Invoices ----
export async function getInvoices(orgId: string, params?: Record<string, string>) {
  const qs = params ? "?" + new URLSearchParams(params).toString() : "";
  return request<import("./types").PaginatedResponse<import("./types").InvoiceListItem>>("GET", `/api/orgs/${orgId}/invoices/${qs}`);
}

export async function getInvoice(orgId: string, invoiceId: string) {
  return request<import("./types").Invoice>("GET", `/api/orgs/${orgId}/invoices/${invoiceId}/`);
}

export async function uploadInvoice(orgId: string, file: File) {
  const formData = new FormData();
  formData.append("pdf_file", file);
  return request<import("./types").Invoice>("POST", `/api/orgs/${orgId}/invoices/upload/`, formData, true);
}

export async function editInvoice(orgId: string, invoiceId: string, data: Record<string, unknown>) {
  return request<import("./types").Invoice>("PATCH", `/api/orgs/${orgId}/invoices/${invoiceId}/edit/`, data);
}

export async function approveInvoice(orgId: string, invoiceId: string, decision: string, comment?: string) {
  return request<import("./types").Invoice>("POST", `/api/orgs/${orgId}/invoices/${invoiceId}/approve/`, { decision, comment });
}

export async function bookInvoice(orgId: string, invoiceId: string) {
  return request<import("./types").Invoice>("POST", `/api/orgs/${orgId}/invoices/${invoiceId}/book/`);
}

// ---- Notifications ----
export async function getNotifications(isRead?: boolean) {
  const qs = isRead !== undefined ? `?is_read=${isRead}` : "";
  return request<import("./types").PaginatedResponse<import("./types").Notification>>("GET", `/api/notifications/${qs}`);
}

export async function markNotificationRead(id: string) {
  return request<import("./types").Notification>("POST", `/api/notifications/${id}/read/`);
}

export async function markAllNotificationsRead() {
  return request<{ marked_read: number }>("POST", "/api/notifications/read-all/");
}

export { ApiError, setTokens, clearTokens };
