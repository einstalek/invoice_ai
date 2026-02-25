(() => {
    const tableBody = document.getElementById('invoices-table');
    const statusEl = document.getElementById('invoices-status');
    const titleEl = document.getElementById('invoices-title');
    const subtitleEl = document.getElementById('invoices-subtitle');
    const deleteModal = document.getElementById('invoice-delete-modal');
    const deleteClose = document.getElementById('invoice-delete-close');
    const deleteCancel = document.getElementById('invoice-delete-cancel');
    const deleteConfirm = document.getElementById('invoice-delete-confirm');

    let pendingDeleteId = null;
    let pendingDeleteBtn = null;

    function openDeleteModal(submissionId, triggerBtn) {
        if (!deleteModal) return;
        pendingDeleteId = submissionId;
        pendingDeleteBtn = triggerBtn || null;
        deleteConfirm.disabled = false;
        deleteModal.classList.remove('hidden');
    }

    function closeDeleteModal() {
        if (!deleteModal) return;
        deleteModal.classList.add('hidden');
        pendingDeleteId = null;
        pendingDeleteBtn = null;
        deleteConfirm.disabled = false;
    }

    async function confirmDelete() {
        if (!pendingDeleteId) return;
        deleteConfirm.disabled = true;
        if (pendingDeleteBtn) pendingDeleteBtn.disabled = true;
        try {
            const response = await fetch('/invoices/submissions/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ submission_id: pendingDeleteId }),
            });
            const result = await response.json();
            if (!response.ok) {
                statusEl.textContent = result.error || 'Delete failed.';
                deleteConfirm.disabled = false;
                if (pendingDeleteBtn) pendingDeleteBtn.disabled = false;
                return;
            }
            statusEl.textContent = '';
            closeDeleteModal();
            await loadSubmissions();
        } catch (error) {
            statusEl.textContent = 'Delete failed.';
            deleteConfirm.disabled = false;
            if (pendingDeleteBtn) pendingDeleteBtn.disabled = false;
        }
    }

    function formatDate(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString();
    }

    function statusBadge(status) {
        const normalized = (status || '').toLowerCase();
        let label = status || '';
        let className = 'badge-neutral';
        if (normalized === 'pending') {
            label = 'Pending';
            className = 'badge-info';
        } else if (normalized === 'changes_requested') {
            label = 'Changes requested';
            className = 'badge-warning';
        } else if (normalized === 'approved') {
            label = 'Approved';
            className = 'badge-success';
        } else if (normalized === 'rejected') {
            label = 'Rejected';
            className = 'badge-danger';
        }
        return { label, className };
    }

    function formatInvoiceLabel(invoiceNumber, submissionId) {
        const raw = invoiceNumber == null ? '' : String(invoiceNumber).trim();
        if (!raw) {
            return `Submission #${submissionId}`;
        }
        const lower = raw.toLowerCase();
        if (lower.startsWith('submission') || lower.startsWith('submmission') || lower.startsWith('submision')) {
            return `Submission #${submissionId}`;
        }
        if (lower.startsWith('invoice')) {
            return raw;
        }
        if (raw.includes('#')) {
            return raw;
        }
        return `Invoice #${raw}`;
    }

    function renderRows(submissions, isAdmin) {
        tableBody.innerHTML = '';
        if (!submissions.length) {
            const row = document.createElement('tr');
            const cell = document.createElement('td');
            cell.colSpan = 6;
            cell.className = 'px-4 py-6 text-center text-slate-500';
            cell.textContent = 'No submissions found.';
            row.appendChild(cell);
            tableBody.appendChild(row);
            return;
        }
        submissions.forEach((submission) => {
            const row = document.createElement('tr');
            row.className = 'table-row';

            const invoiceCell = document.createElement('td');
            invoiceCell.className = 'px-4 py-3 font-medium text-slate-700';
            const link = document.createElement('a');
            link.href = `/app/?submission_id=${submission.id}`;
            link.className = 'text-blue-600 hover:text-blue-700 hover:underline';
            link.textContent = formatInvoiceLabel(submission.invoice_number, submission.id);
            invoiceCell.appendChild(link);

            const senderCell = document.createElement('td');
            senderCell.className = 'px-4 py-3 text-slate-600';
            senderCell.textContent = submission.submitted_by || 'Unknown';

            const commentCell = document.createElement('td');
            commentCell.className = 'px-4 py-3 text-slate-500';
            commentCell.textContent = submission.comment || '—';

            const dateCell = document.createElement('td');
            dateCell.className = 'px-4 py-3 text-slate-500';
            dateCell.textContent = formatDate(submission.created_at);

            const statusCell = document.createElement('td');
            statusCell.className = 'px-4 py-3';
            const badge = document.createElement('span');
            const { label, className } = statusBadge(submission.status);
            badge.className = `badge ${className}`;
            badge.textContent = label || 'Unknown';
            statusCell.appendChild(badge);

            const actionsCell = document.createElement('td');
            actionsCell.className = 'px-4 py-3 text-right';
            if (isAdmin) {
                const deleteBtn = document.createElement('button');
                deleteBtn.type = 'button';
                deleteBtn.className = 'btn btn-danger btn-xs';
                deleteBtn.textContent = 'Delete';
                deleteBtn.addEventListener('click', async (e) => {
                    e.preventDefault();
                    e.stopPropagation();
                    openDeleteModal(submission.id, deleteBtn);
                });
                actionsCell.appendChild(deleteBtn);
            } else {
                actionsCell.textContent = '—';
                actionsCell.classList.add('text-slate-400');
            }

            row.appendChild(invoiceCell);
            row.appendChild(senderCell);
            row.appendChild(commentCell);
            row.appendChild(dateCell);
            row.appendChild(statusCell);
            row.appendChild(actionsCell);
            tableBody.appendChild(row);
        });
    }

    async function loadSubmissions() {
        statusEl.textContent = 'Loading submissions...';
        try {
            const response = await fetch('/invoices/submissions/table?status=all');
            const data = await response.json();
            if (!response.ok) {
                const errorMessage = data.error || 'Unable to load submissions.';
                const suppressError =
                    errorMessage === 'Authentication required.'
                    || errorMessage === 'No active organization.';
                statusEl.textContent = suppressError ? '' : errorMessage;
                renderRows([], false);
                return;
            }
            const isAdmin = data.role === 'admin';
            if (titleEl) {
                titleEl.textContent = isAdmin ? 'All submissions' : 'Your submissions';
            }
            if (subtitleEl) {
                subtitleEl.textContent = isAdmin
                    ? ''
                    : 'Track your submissions and their review status.';
            }
            const submissions = Array.isArray(data.submissions) ? data.submissions : [];
            statusEl.textContent = '';
            renderRows(submissions, isAdmin);
        } catch (error) {
            statusEl.textContent = 'Unable to load submissions.';
            renderRows([], false);
        }
    }

    if (deleteClose) {
        deleteClose.addEventListener('click', () => closeDeleteModal());
    }
    if (deleteCancel) {
        deleteCancel.addEventListener('click', () => closeDeleteModal());
    }
    if (deleteConfirm) {
        deleteConfirm.addEventListener('click', () => confirmDelete());
    }
    if (deleteModal) {
        deleteModal.addEventListener('click', (e) => {
            if (e.target === deleteModal) {
                closeDeleteModal();
            }
        });
    }
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && deleteModal && !deleteModal.classList.contains('hidden')) {
            closeDeleteModal();
        }
    });

    loadSubmissions();
})();
