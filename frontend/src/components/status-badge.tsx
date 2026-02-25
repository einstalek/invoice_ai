import { clsx } from "clsx";
import type { InvoiceStatus } from "@/lib/types";

const styles: Record<InvoiceStatus, string> = {
  PROCESSING: "bg-yellow-100 text-yellow-800",
  EXTRACTION_FAILED: "bg-red-100 text-red-800",
  PENDING_REVIEW: "bg-blue-100 text-blue-800",
  APPROVED: "bg-green-100 text-green-800",
  BOOKED: "bg-purple-100 text-purple-800",
};

const labels: Record<InvoiceStatus, string> = {
  PROCESSING: "Processing",
  EXTRACTION_FAILED: "Failed",
  PENDING_REVIEW: "Pending Review",
  APPROVED: "Approved",
  BOOKED: "Booked",
};

export default function StatusBadge({ status }: { status: InvoiceStatus }) {
  return (
    <span className={clsx("inline-flex rounded-full px-2 py-0.5 text-xs font-medium", styles[status])}>
      {labels[status]}
    </span>
  );
}
