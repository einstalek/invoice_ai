export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  date_joined: string;
}

export interface Organization {
  id: string;
  name: string;
  vat_number: string | null;
  address: string | null;
  country: string | null;
  erp_type: "NONE" | "GOOGLE_SHEETS" | "QUICKBOOKS";
  erp_config: Record<string, unknown> | null;
  required_approvals: number;
  created_at: string;
}

export interface Membership {
  id: string;
  user: User | null;
  organization: string;
  role: "OWNER" | "ACCOUNTANT";
  status: "PENDING" | "ACTIVE" | "DEACTIVATED";
  invited_email: string;
  invited_by: string | null;
  created_at: string;
}

export interface UserMembership {
  id: string;
  organization: { id: string; name: string };
  role: "OWNER" | "ACCOUNTANT";
}

export interface PendingInvite {
  id: string;
  organization: { id: string; name: string };
  role: "OWNER" | "ACCOUNTANT";
  created_at: string;
}

export interface Supplier {
  id: string;
  organization: string;
  name: string;
  vat_id: string | null;
  address: string | null;
  country: string | null;
  country_group: "EE" | "EU_OTHER" | "NON_EU" | null;
  email: string | null;
  created_at: string;
  updated_at: string;
}

export type InvoiceStatus =
  | "PROCESSING"
  | "EXTRACTION_FAILED"
  | "PENDING_REVIEW"
  | "APPROVED"
  | "BOOKED";

export interface InvoiceListItem {
  id: string;
  status: InvoiceStatus;
  invoice_number: string | null;
  invoice_date: string | null;
  total_amount: string | null;
  currency: string | null;
  supplier_name: string | null;
  uploaded_by: User;
  created_at: string;
  updated_at: string;
}

export interface InvoiceActivity {
  id: string;
  user: User | null;
  action: string;
  comment: string | null;
  changes: Record<string, { old: string | null; new: string | null }> | null;
  created_at: string;
}

export interface InvoiceApproval {
  id: string;
  user: User;
  round: number;
  decision: "APPROVED" | "EDIT_REQUESTED";
  comment: string | null;
  created_at: string;
}

export interface Invoice {
  id: string;
  organization: string;
  uploaded_by: User;
  pdf_file: string;
  status: InvoiceStatus;
  supplier: string | null;
  supplier_detail: Supplier | null;
  current_approval_round: number;
  approvals_obtained: number;
  booked_at: string | null;
  booked_by: User | null;
  created_at: string;
  updated_at: string;
  // Extracted fields
  invoice_number: string | null;
  invoice_date: string | null;
  invoice_due_date: string | null;
  total_amount: string | null;
  currency: string | null;
  description_keyword: string | null;
  vat_rates: string | null;
  supply_type: "GOODS" | "SERVICES" | null;
  service_category: string | null;
  supplier_name: string | null;
  supplier_address: string | null;
  supplier_country: string | null;
  supplier_country_group: "EE" | "EU_OTHER" | "NON_EU" | null;
  supplier_vat_id: string | null;
  supplier_email: string | null;
  buyer_name: string | null;
  buyer_address: string | null;
  buyer_country: string | null;
  buyer_country_group: "EE" | "EU_OTHER" | "NON_EU" | null;
  buyer_vat_id: string | null;
  buyer_email: string | null;
  // LLM
  llm_raw_response: Record<string, unknown> | null;
  extracted_text: string | null;
  extraction_error: string | null;
  // Nested
  activities: InvoiceActivity[];
  approvals: InvoiceApproval[];
}

export interface Notification {
  id: string;
  organization: string | null;
  invoice: string | null;
  type: string;
  title: string;
  is_read: boolean;
  created_at: string;
}

export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
