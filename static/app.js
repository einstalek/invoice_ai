(() => {
    const { googleApiKey, googleClientId, isAuthenticated: isAuthenticatedFlag } = window.APP_CONFIG || {};
    const isAuthenticated = Boolean(isAuthenticatedFlag);

    const dropZone = document.getElementById('drop-zone');
    const fileInput = document.getElementById('file-input');
    const orgMenuBtn = document.getElementById('org-menu-btn');
    const orgMenuLabel = document.getElementById('org-menu-label');
    const brandOrg = document.getElementById('brand-org');
    const brandOrgName = document.getElementById('brand-org-name');
    const orgDropdown = document.getElementById('org-dropdown');
    const orgCreateToggle = document.getElementById('org-create-toggle');
    const orgCreateModal = document.getElementById('org-create-modal');
    const orgCreateClose = document.getElementById('org-create-close');
    const orgCreateInput = document.getElementById('org-create-input');
    const orgCreateEmailChips = document.getElementById('org-create-email-chips');
    const orgCreateEmailInput = document.getElementById('org-create-email-input');
    const orgCreateEmailStatus = document.getElementById('org-create-email-status');
    const orgCreateSubmit = document.getElementById('org-create-submit');
    const orgCreateStatus = document.getElementById('org-create-status');
    const orgSelectToggle = document.getElementById('org-select-toggle');
    const orgInfoToggle = document.getElementById('org-info-toggle');
    const orgEditToggle = document.getElementById('org-edit-toggle');
    const orgSelectModal = document.getElementById('org-select-modal');
    const orgSelectClose = document.getElementById('org-select-close');
    const orgSelectList = document.getElementById('org-select-list');
    const orgSelectSubmit = document.getElementById('org-select-submit');
    const orgSelectStatus = document.getElementById('org-select-status');
    const orgInfoModal = document.getElementById('org-info-modal');
    const orgInfoClose = document.getElementById('org-info-close');
    const orgInfoContent = document.getElementById('org-info-content');
    const orgInfoSelect = document.getElementById('org-info-select');
    const orgInfoCreate = document.getElementById('org-info-create');
    const orgInfoEdit = document.getElementById('org-info-edit');
    const orgEditModal = document.getElementById('org-edit-modal');
    const orgEditClose = document.getElementById('org-edit-close');
    const orgEditMembers = document.getElementById('org-edit-members');
    const orgEditMembersStatus = document.getElementById('org-edit-members-status');
    const orgEditEmailChips = document.getElementById('org-edit-email-chips');
    const orgEditEmailInput = document.getElementById('org-edit-email-input');
    const orgEditEmailStatus = document.getElementById('org-edit-email-status');
    const orgEditInviteSubmit = document.getElementById('org-edit-invite-submit');
    const orgEditInviteStatus = document.getElementById('org-edit-invite-status');
    const googleDisconnectBtn = document.getElementById('google-disconnect-btn');
    const exportBtn = document.getElementById('export-btn');
    const cancelExtractionBtn = document.getElementById('cancel-extraction-btn');
    const submitBtn = document.getElementById('submit-btn');
    const deleteSubmissionBtn = document.getElementById('delete-submission-btn');
    const approvalActions = document.getElementById('approval-actions');
    const approveBtn = document.getElementById('approve-btn');
    const requestEditBtn = document.getElementById('request-edit-btn');
    const rejectBtn = document.getElementById('reject-btn');
    const exportMenuBtn = document.getElementById('export-menu-btn');
    const exportMenu = document.getElementById('export-menu');
    const exportGoogleBtn = document.getElementById('export-google-btn');
    const exportErpBtn = document.getElementById('export-erp-btn');
    const exportStatus = document.getElementById('export-status');
    const exportLockedHint = document.getElementById('export-locked-hint');
    const reviewProgress = document.getElementById('review-progress');
    const selectSheetBtn = document.getElementById('select-sheet-btn');
    const createSheetBtn = document.getElementById('create-sheet-btn');
    const sheetStatus = document.getElementById('sheet-status');
    const savingDestination = document.getElementById('saving-destination');
    const savingDestinationValue = document.getElementById('saving-destination-value');
    const savingDestinationClear = document.getElementById('saving-destination-clear');
    const closeInvoiceBtn = document.getElementById('close-invoice-btn');
    const submissionMeta = document.getElementById('submission-meta');
    const reviewComment = document.getElementById('review-comment');
    const reviewCommentTitle = document.getElementById('review-comment-title');
    const reviewCommentBody = document.getElementById('review-comment-body');
    const requestEditModal = document.getElementById('request-edit-modal');
    const ocrEmptyModal = document.getElementById('ocr-empty-modal');
    const ocrEmptyClose = document.getElementById('ocr-empty-close');
    const ocrEmptyOk = document.getElementById('ocr-empty-ok');
    const requestEditClose = document.getElementById('request-edit-close');
    const requestEditCancel = document.getElementById('request-edit-cancel');
    const requestEditSend = document.getElementById('request-edit-send');
    const requestEditInput = document.getElementById('request-edit-input');
    const requestEditStatus = document.getElementById('request-edit-status');
    const reviewerPanel = document.getElementById('reviewer-panel');
    const reviewerList = document.getElementById('reviewer-list');
    const reviewerSelect = document.getElementById('reviewer-select');
    const reviewerSelectStatus = document.getElementById('reviewer-select-status');
    const reviewerAdd = document.getElementById('reviewer-add');
    const reviewerAddSelect = document.getElementById('reviewer-add-select');
    const reviewerAddBtn = document.getElementById('reviewer-add-btn');
    const reviewerAddStatus = document.getElementById('reviewer-add-status');
    const zoomOutBtn = document.getElementById('zoom-out-btn');
    const zoomInBtn = document.getElementById('zoom-in-btn');
    const zoomLabel = document.getElementById('zoom-label');
    const pageCounter = document.getElementById('page-counter');
    const canvasContainer = document.getElementById('canvas-container');
    const jsonContent = document.getElementById('json-content');
    const pdfWrapper = document.getElementById('pdf-wrapper');
    const sidebar = document.getElementById('sidebar');
    const sidebarResizer = document.getElementById('sidebar-resizer');
    const sidebarCollapseBtn = document.getElementById('sidebar-collapse-btn');
    const sidebarCollapseIcon = document.getElementById('sidebar-collapse-icon');
    const layoutMain = document.querySelector('main');

    let currentPdfDoc = null;
    let currentPdfFile = null;
    let pageScale = 1.2;
    let currentData = null;
    let currentSubmissionId = null;
    let currentSubmissionStatus = null;
    let currentSubmissionMeta = null;
    let isExtracting = false;
    let extractionController = null;
    let googleConnected = false;
    let orgRoleInitialized = false;
    let currentSheetId = null;
    let currentSheetLabel = null;
    let exportDestination = 'google';
    let pendingExportAfterSheetSelect = false;
    let pickerApiLoaded = false;
    let isRenderingPdf = false;
    let scrollRaf = null;
    let orgInviteEmails = [];
    let orgEditInviteEmails = [];
    let activeOrgRole = null;
    let currentUserId = null;
    let currentCanReview = false;
    let currentCanExport = false;
    let currentReviewers = [];
    let currentReviewerStatus = null;
    let orgAdmins = [];
    let singleAdminOrg = false;
    let selectedReviewerIds = new Set();
    let extractionRequestId = null;
    const initialSubmissionId = new URLSearchParams(window.location.search).get('submission_id');
    let initialSubmissionHandled = false;
    if (initialSubmissionId && isAuthenticated) {
        renderSubmissionLoading();
    }

    const ZOOM_MIN = 0.7;
    const ZOOM_MAX = 2.0;
    const ZOOM_STEP = 0.1;
    const SIDEBAR_MIN = 320;
    const LEFT_PANEL_MIN = 320;

    function showToast(message, tone = 'info') {
        if (!message) return;
        let container = document.getElementById('toast-container');
        if (!container) {
            container = document.createElement('div');
            container.id = 'toast-container';
            container.className = 'toast-container';
            document.body.appendChild(container);
        }
        const toast = document.createElement('div');
        toast.className = `toast toast-${tone}`;
        toast.setAttribute('data-toast', 'true');
        toast.innerHTML = `
            <div class="toast-body">
                <div class="toast-title">${tone.toUpperCase()}</div>
                <div class="toast-message"></div>
            </div>
            <button class="toast-close" type="button" data-toast-close aria-label="Dismiss">✕</button>
        `;
        const messageEl = toast.querySelector('.toast-message');
        if (messageEl) {
            messageEl.textContent = message;
        }
        const closeBtn = toast.querySelector('[data-toast-close]');
        const dismiss = () => {
            toast.classList.add('toast-hide');
            setTimeout(() => toast.remove(), 250);
        };
        if (closeBtn) {
            closeBtn.addEventListener('click', dismiss);
        }
        container.appendChild(toast);
        setTimeout(dismiss, 4800);
    }

    function clampSidebarWidth(width) {
        if (!layoutMain) {
            return Math.max(width, SIDEBAR_MIN);
        }
        const mainWidth = layoutMain.getBoundingClientRect().width;
        const maxWidth = Math.max(SIDEBAR_MIN, mainWidth - LEFT_PANEL_MIN);
        return Math.min(Math.max(width, SIDEBAR_MIN), maxWidth);
    }

    function setupSidebarResize() {
        if (!sidebar || !sidebarResizer) {
            return;
        }
        let startX = 0;
        let startWidth = 0;
        let isResizing = false;
        let activePointerId = null;

        const startResize = (clientX) => {
            isResizing = true;
            startX = clientX;
            startWidth = sidebar.getBoundingClientRect().width;
            document.body.classList.add('resizing');
        };

        const updateResize = (clientX) => {
            if (!isResizing) {
                return;
            }
            const deltaX = clientX - startX;
            const nextWidth = clampSidebarWidth(startWidth - deltaX);
            sidebar.style.width = `${nextWidth}px`;
        };

        const stopResize = () => {
            if (!isResizing) {
                return;
            }
            isResizing = false;
            activePointerId = null;
            document.body.classList.remove('resizing');
        };

        if (window.PointerEvent) {
            const handlePointerMove = (event) => {
                if (!isResizing || activePointerId === null || event.pointerId !== activePointerId) {
                    return;
                }
                updateResize(event.clientX);
            };

            const handlePointerUp = (event) => {
                if (activePointerId === null || event.pointerId !== activePointerId) {
                    return;
                }
                try {
                    sidebarResizer.releasePointerCapture(event.pointerId);
                } catch (err) {
                    // Ignore if pointer capture was already released.
                }
                stopResize();
            };

            sidebarResizer.addEventListener('pointerdown', (event) => {
                if (event.button !== undefined && event.button !== 0) {
                    return;
                }
                activePointerId = event.pointerId;
                startResize(event.clientX);
                sidebarResizer.setPointerCapture(event.pointerId);
                event.preventDefault();
            });

            window.addEventListener('pointermove', handlePointerMove);
            window.addEventListener('pointerup', handlePointerUp);
            window.addEventListener('pointercancel', handlePointerUp);
        } else {
            const handleMouseMove = (event) => updateResize(event.clientX);
            const handleMouseUp = () => stopResize();

            sidebarResizer.addEventListener('mousedown', (event) => {
                if (event.button !== 0) {
                    return;
                }
                startResize(event.clientX);
                event.preventDefault();
            });

            window.addEventListener('mousemove', handleMouseMove);
            window.addEventListener('mouseup', handleMouseUp);

            sidebarResizer.addEventListener('touchstart', (event) => {
                if (!event.touches.length) {
                    return;
                }
                startResize(event.touches[0].clientX);
                event.preventDefault();
            }, { passive: false });

            window.addEventListener('touchmove', (event) => {
                if (!event.touches.length) {
                    return;
                }
                updateResize(event.touches[0].clientX);
            }, { passive: true });

            window.addEventListener('touchend', stopResize);
            window.addEventListener('touchcancel', stopResize);
        }

        window.addEventListener('resize', () => {
            const currentWidth = sidebar.getBoundingClientRect().width;
            const clampedWidth = clampSidebarWidth(currentWidth);
            if (Math.abs(clampedWidth - currentWidth) > 0.5) {
                sidebar.style.width = `${clampedWidth}px`;
            }
        });
    }

    function updateZoomLabel() {
        zoomLabel.textContent = `${Math.round(pageScale * 100)}%`;
    }

    function updatePageCounter() {
        if (!currentPdfDoc) {
            pageCounter.textContent = 'Page 0 / 0';
            return;
        }
        const pages = document.querySelectorAll('.pdf-page');
        if (!pages.length) {
            pageCounter.textContent = `Page 1 / ${currentPdfDoc.numPages}`;
            return;
        }
        const scrollTop = pdfWrapper.scrollTop;
        let closestPage = 1;
        let minDistance = Infinity;
        pages.forEach((page) => {
            const pageTop = page.offsetTop;
            const distance = Math.abs(pageTop - scrollTop);
            if (distance < minDistance) {
                minDistance = distance;
                closestPage = Number(page.dataset.page || 1);
            }
        });
        pageCounter.textContent = `Page ${closestPage} / ${currentPdfDoc.numPages}`;
    }

    function closeOrgDropdown() {
        if (orgDropdown) orgDropdown.classList.add('hidden');
    }

    function closeOrgModals() {
        orgCreateModal.classList.add('hidden');
        orgSelectModal.classList.add('hidden');
        orgInfoModal.classList.add('hidden');
        orgEditModal.classList.add('hidden');
    }


    function openOcrEmptyModal() {
        if (!ocrEmptyModal) return;
        ocrEmptyModal.classList.remove('hidden');
    }

    function closeOcrEmptyModal() {
        if (!ocrEmptyModal) return;
        ocrEmptyModal.classList.add('hidden');
    }

    function renderEmailChips() {
        orgCreateEmailChips.querySelectorAll('.email-chip').forEach((chip) => chip.remove());
        orgInviteEmails.forEach((email) => {
            const chip = document.createElement('span');
            chip.className = 'email-chip inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600';
            chip.textContent = email;
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'text-slate-400 hover:text-slate-600';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', () => {
                orgInviteEmails = orgInviteEmails.filter((value) => value !== email);
                renderEmailChips();
            });
            chip.appendChild(removeBtn);
            orgCreateEmailChips.insertBefore(chip, orgCreateEmailInput);
        });
    }

    function renderEditEmailChips() {
        orgEditEmailChips.querySelectorAll('.email-chip').forEach((chip) => chip.remove());
        orgEditInviteEmails.forEach((email) => {
            const chip = document.createElement('span');
            chip.className = 'email-chip inline-flex items-center gap-1 rounded-full bg-slate-100 px-2 py-0.5 text-xs text-slate-600';
            chip.textContent = email;
            const removeBtn = document.createElement('button');
            removeBtn.type = 'button';
            removeBtn.className = 'text-slate-400 hover:text-slate-600';
            removeBtn.textContent = '×';
            removeBtn.addEventListener('click', () => {
                orgEditInviteEmails = orgEditInviteEmails.filter((value) => value !== email);
                renderEditEmailChips();
            });
            chip.appendChild(removeBtn);
            orgEditEmailChips.insertBefore(chip, orgEditEmailInput);
        });
    }

    function tryAddEmail(value) {
        const trimmed = (value || '').trim().replace(/,$/, '');
        if (!trimmed) return true;
        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(trimmed)) {
            setStatus(orgCreateEmailStatus, `Invalid email: ${trimmed}`, 'error');
            return false;
        }
        if (!orgInviteEmails.includes(trimmed)) {
            orgInviteEmails.push(trimmed);
            renderEmailChips();
        }
        setStatus(orgCreateEmailStatus, '');
        return true;
    }

    function tryAddEditEmail(value) {
        const trimmed = (value || '').trim().replace(/,$/, '');
        if (!trimmed) return true;
        const emailRegex = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
        if (!emailRegex.test(trimmed)) {
            setStatus(orgEditEmailStatus, `Invalid email: ${trimmed}`, 'error');
            return false;
        }
        if (!orgEditInviteEmails.includes(trimmed)) {
            orgEditInviteEmails.push(trimmed);
            renderEditEmailChips();
        }
        setStatus(orgEditEmailStatus, '');
        return true;
    }

    function consumeEmailInput() {
        const value = orgCreateEmailInput.value || '';
        if (!value) return true;
        const parts = value.split(/[\n,]+/);
        const last = parts.pop();
        let ok = true;
        parts.forEach((part) => {
            if (!tryAddEmail(part)) ok = false;
        });
        orgCreateEmailInput.value = last ? last.trimStart() : '';
        return ok;
    }

    function consumeEditEmailInput() {
        const value = orgEditEmailInput.value || '';
        if (!value) return true;
        const parts = value.split(/[\n,]+/);
        const last = parts.pop();
        let ok = true;
        parts.forEach((part) => {
            if (!tryAddEditEmail(part)) ok = false;
        });
        orgEditEmailInput.value = last ? last.trimStart() : '';
        return ok;
    }

    function finalizeEmailInput() {
        const value = orgCreateEmailInput.value || '';
        if (!value.trim()) return true;
        const ok = tryAddEmail(value);
        if (ok) orgCreateEmailInput.value = '';
        return ok;
    }

    function finalizeEditEmailInput() {
        const value = orgEditEmailInput.value || '';
        if (!value.trim()) return true;
        const ok = tryAddEditEmail(value);
        if (ok) orgEditEmailInput.value = '';
        return ok;
    }
    function setOrgLabel(activeOrg) {
        orgMenuLabel.textContent = 'org';
        orgMenuBtn.title = activeOrg && activeOrg.name ? activeOrg.name : 'No org selected';
        if (brandOrg && brandOrgName) {
            const name = activeOrg && activeOrg.name ? activeOrg.name : '';
            brandOrgName.textContent = name;
            brandOrg.classList.toggle('hidden', !name);
        }
        loadOrgAdmins();
    }

    function closeExportMenu() {
        if (exportMenu) {
            exportMenu.classList.add('hidden');
        }
    }

    const SIDEBAR_COLLAPSE_KEY = 'invoice_ai_sidebar_collapsed';

    function setSidebarCollapsed(collapsed, { persist = true } = {}) {
        if (!sidebar) return;
        sidebar.classList.toggle('sidebar-collapsed', collapsed);
        if (sidebarCollapseBtn) {
            const label = collapsed ? 'Expand details' : 'Collapse details';
            sidebarCollapseBtn.setAttribute('aria-label', label);
            sidebarCollapseBtn.setAttribute('title', label);
        }
        if (persist) {
            try {
                localStorage.setItem(SIDEBAR_COLLAPSE_KEY, collapsed ? '1' : '0');
            } catch (error) {
                // Ignore storage errors
            }
        }
    }

    function initSidebarCollapse() {
        if (!sidebar || !sidebarCollapseBtn) return;
        let collapsed = false;
        try {
            collapsed = localStorage.getItem(SIDEBAR_COLLAPSE_KEY) === '1';
        } catch (error) {
            collapsed = false;
        }
        setSidebarCollapsed(collapsed, { persist: false });
        sidebarCollapseBtn.addEventListener('click', () => {
            const next = !sidebar.classList.contains('sidebar-collapsed');
            setSidebarCollapsed(next);
        });
    }

    function startGoogleConnect(statusEl) {
        if (statusEl) {
            statusEl.textContent = 'Connecting Google...';
        }
        const nextUrl = window.location.pathname + window.location.search;
        window.location.href = `/auth/google/?next=${encodeURIComponent(nextUrl)}`;
    }

    function updateInvoiceActions() {
        if (!orgRoleInitialized) {
            if (selectSheetBtn) selectSheetBtn.classList.add('hidden');
            if (createSheetBtn) createSheetBtn.classList.add('hidden');
            return;
        }
        const hasData = Boolean(currentData || currentSubmissionId || currentPdfFile || currentPdfDoc);
        if (closeInvoiceBtn) {
            closeInvoiceBtn.classList.toggle('hidden', !hasData);
        }
        if (cancelExtractionBtn) {
            const showCancel = !currentSubmissionId && (isExtracting || Boolean(currentData));
            cancelExtractionBtn.classList.toggle('hidden', !showCancel);
        }
        if (approvalActions) {
            const showActions = Boolean(currentSubmissionId) && (currentCanReview || currentCanExport);
            approvalActions.classList.toggle('hidden', !showActions);
            const showReviewButtons = Boolean(currentSubmissionId) && currentCanReview;
            if (approveBtn) approveBtn.classList.toggle('hidden', !showReviewButtons);
            if (requestEditBtn) requestEditBtn.classList.toggle('hidden', !showReviewButtons);
            if (rejectBtn) rejectBtn.classList.toggle('hidden', !showReviewButtons);
            if (exportMenuBtn) {
                exportMenuBtn.classList.toggle('hidden', !currentCanExport);
                exportMenuBtn.disabled = !currentCanExport;
            }
            if (!currentCanExport) {
                closeExportMenu();
            }
            if (exportLockedHint) {
                const showHint = Boolean(currentSubmissionId) && !currentCanExport
                    && currentSubmissionStatus === 'pending';
                exportLockedHint.classList.toggle('hidden', !showHint);
            }
        }
        if (currentSubmissionId) {
            exportBtn.classList.add('hidden');
            if (activeOrgRole === 'admin') {
                if (selectSheetBtn) selectSheetBtn.classList.add('hidden');
                if (createSheetBtn) createSheetBtn.classList.add('hidden');
                submitBtn.classList.add('hidden');
                if (deleteSubmissionBtn) {
                    deleteSubmissionBtn.classList.add('hidden');
                }
            } else {
                if (selectSheetBtn) selectSheetBtn.classList.add('hidden');
                if (createSheetBtn) createSheetBtn.classList.add('hidden');
                const canResubmit = currentSubmissionStatus === 'changes_requested';
                const canCancel = currentSubmissionStatus === 'pending';
                submitBtn.classList.toggle('hidden', !canResubmit);
                submitBtn.textContent = canResubmit ? 'Resubmit' : 'Submit';
                submitBtn.classList.remove(
                    'text-emerald-700',
                    'border-emerald-200',
                    'bg-emerald-50',
                    'hover:bg-emerald-100',
                    'text-white',
                    'bg-slate-900',
                    'hover:bg-slate-800'
                );
                if (deleteSubmissionBtn) {
                    deleteSubmissionBtn.classList.toggle('hidden', !(canResubmit || canCancel));
                    deleteSubmissionBtn.classList.remove('action-btn-multiline');
                    deleteSubmissionBtn.textContent = 'Cancel';
                }
            }
            return;
        }
        submitBtn.textContent = 'Submit';
        submitBtn.classList.remove(
            'text-emerald-700',
            'border-emerald-200',
            'bg-emerald-50',
            'hover:bg-emerald-100',
            'text-white',
            'bg-slate-900',
            'hover:bg-slate-800'
        );
        if (deleteSubmissionBtn) {
            deleteSubmissionBtn.classList.add('hidden');
        }
        const hasActiveOrg = Boolean(activeOrgRole);
        if (!hasActiveOrg) {
            if (selectSheetBtn) selectSheetBtn.classList.add('hidden');
            exportBtn.classList.toggle('hidden', !hasData);
            if (createSheetBtn) createSheetBtn.classList.add('hidden');
            submitBtn.classList.add('hidden');
            return;
        }
        if (selectSheetBtn) selectSheetBtn.classList.add('hidden');
        exportBtn.classList.add('hidden');
        if (createSheetBtn) createSheetBtn.classList.add('hidden');
        submitBtn.classList.toggle('hidden', !currentData || isExtracting);
    }

    function renderSubmissionLoading() {
        exportStatus.textContent = 'Loading submission...';
        if (jsonContent) {
            jsonContent.innerHTML = `
                <div class="p-8 text-center text-slate-500">
                    <div class="progress-track h-2 rounded-full overflow-hidden">
                        <div class="progress-bar h-full rounded-full"></div>
                    </div>
                </div>
            `;
        }
        if (savingDestination) {
            savingDestination.classList.add('hidden');
        }
    }

    function updateSavingDestination() {
        if (!savingDestinationValue || !savingDestination) return;
        let value = '';
        let href = '';
        if (exportDestination === 'google' && currentSheetLabel) {
            value = `Google: ${currentSheetLabel}`;
            if (currentSheetId) {
                href = `https://docs.google.com/spreadsheets/d/${currentSheetId}`;
            }
        } else if (exportDestination === 'erp') {
            value = 'ERP: —';
        }
        savingDestinationValue.innerHTML = '';
        if (value) {
            if (href) {
                const link = document.createElement('a');
                link.href = href;
                link.target = '_blank';
                link.rel = 'noopener';
                link.className = 'meta-link';
                link.textContent = value;
                savingDestinationValue.appendChild(link);
            } else {
                savingDestinationValue.textContent = value;
            }
        }
        const hasContext = Boolean(currentSubmissionId || currentData);
        savingDestination.classList.toggle('hidden', !hasContext || !value);
    }

    function setReviewState(submissionId, status, canReviewOverride, canExportOverride) {
        currentSubmissionId = submissionId || null;
        currentSubmissionStatus = status || null;
        if (typeof canReviewOverride === 'boolean') {
            currentCanReview = canReviewOverride;
        } else {
            currentCanReview = activeOrgRole === 'admin'
                && Boolean(currentSubmissionId)
                && currentSubmissionStatus === 'pending';
        }
        if (typeof canExportOverride === 'boolean') {
            currentCanExport = canExportOverride;
        } else {
            currentCanExport = activeOrgRole === 'admin'
                && Boolean(currentSubmissionId)
                && currentSubmissionStatus === 'approved';
        }
        updateInvoiceActions();
        updateReviewerPanel();
        if (reviewProgress && (!currentSubmissionId || !Array.isArray(currentReviewers) || !currentReviewers.length)) {
            reviewProgress.classList.add('hidden');
            reviewProgress.textContent = '';
        }
    }

    function clearInvoiceView(message) {
        currentPdfDoc = null;
        currentPdfFile = null;
        currentData = null;
        currentSubmissionId = null;
        currentSubmissionStatus = null;
        currentCanReview = false;
        currentCanExport = false;
        currentReviewers = [];
        currentReviewerStatus = null;
        if (approvalActions) {
            approvalActions.classList.add('hidden');
        }
        if (closeInvoiceBtn) {
            closeInvoiceBtn.classList.add('hidden');
        }
        if (deleteSubmissionBtn) {
            deleteSubmissionBtn.classList.add('hidden');
        }
        if (submissionMeta) {
            submissionMeta.classList.add('hidden');
            submissionMeta.textContent = '';
        }
        if (reviewComment) {
            reviewComment.classList.add('hidden');
        }
        if (reviewerSelectStatus) {
            reviewerSelectStatus.textContent = '';
        }
        if (reviewProgress) {
            reviewProgress.classList.add('hidden');
            reviewProgress.textContent = '';
        }
        if (exportLockedHint) {
            exportLockedHint.classList.add('hidden');
        }
        canvasContainer.innerHTML = '';
        canvasContainer.classList.add('hidden');
        dropZone.classList.remove('hidden');
        jsonContent.innerHTML =
            message ||
            '<div class="h-full flex flex-col items-center justify-center text-slate-400 text-sm p-8 text-center">Waiting for document...</div>';
        exportStatus.textContent = '';
        updatePageCounter();
        updateInvoiceActions();
        updateReviewerPanel();
    }

    function setStatus(el, message, tone) {
        el.textContent = message || '';
        el.classList.remove('text-rose-500', 'text-emerald-600');
        if (tone === 'error') {
            el.classList.add('text-rose-500');
        } else if (tone === 'success') {
            el.classList.add('text-emerald-600');
        }
    }

    function formatStatusLabel(status) {
        if (!status) return '';
        if (status === 'changes_requested') return 'Changes requested';
        if (status === 'approved') return 'Approved';
        if (status === 'rejected') return 'Rejected';
        if (status === 'pending') return 'Pending';
        return status;
    }

    function formatShortDate(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString();
    }

    function setSubmissionMeta(meta) {
        if (!submissionMeta) return;
        if (!meta) {
            currentSubmissionMeta = null;
            submissionMeta.classList.add('hidden');
            submissionMeta.textContent = '';
            return;
        }
        currentSubmissionMeta = { ...meta };
        const createdAt = formatShortDate(meta.created_at);
        const exportedAt = formatShortDate(meta.exported_at);
        const submittedBy = meta.submitted_by ? meta.submitted_by : '';
        const exportedBy = meta.exported_by ? meta.exported_by : '';
        const statusLabel = formatStatusLabel(meta.status);
        let html = '';
        if (submittedBy || createdAt) {
            html += `
                <div class="meta-item">
                    <div class="meta-content">
                        <div class="meta-label">Submitted by</div>
                        <div class="meta-value">${submittedBy || 'Unknown'}</div>
                        ${createdAt ? `<div class="meta-subvalue">${createdAt}</div>` : ''}
                    </div>
                </div>
            `;
        }
        if (meta.status === 'approved' || exportedAt || exportedBy) {
            html += `
                <div class="meta-item">
                    <div class="meta-content">
                        <div class="meta-label">Exported</div>
                        <div class="meta-value">${exportedAt || 'Not yet'}</div>
                        ${exportedBy ? `<div class="meta-subvalue">by ${exportedBy}</div>` : ''}
                    </div>
                </div>
            `;
        }
        if (statusLabel) {
            html += `
                <div class="meta-item">
                    <div class="meta-content">
                        <div class="meta-label">Status</div>
                        <div class="meta-value meta-status-value">${statusLabel}</div>
                    </div>
                </div>
            `;
        }
        if (!html) {
            submissionMeta.classList.add('hidden');
            submissionMeta.textContent = '';
            return;
        }
        submissionMeta.innerHTML = html;
        submissionMeta.classList.remove('hidden');
    }

    function applySubmissionStatus(status) {
        if (!currentSubmissionId) return;
        const canExport = status === 'approved' && currentReviewerStatus === 'approved';
        setReviewState(currentSubmissionId, status, false, canExport);
        if (currentSubmissionMeta) {
            setSubmissionMeta({ ...currentSubmissionMeta, status });
        } else {
            setSubmissionMeta({ status });
        }
    }

    function setReviewComment(comments) {
        if (!reviewComment || !reviewCommentBody || !reviewCommentTitle) return;
        if (!Array.isArray(comments) || comments.length === 0) {
            reviewComment.classList.add('hidden');
            reviewCommentBody.textContent = '';
            return;
        }
        const adminComment = comments.filter((comment) => comment.author_is_admin).slice(-1)[0];
        const latest = comments[comments.length - 1];
        const selected = activeOrgRole === 'admin' ? latest : (adminComment || latest);
        if (!selected || !selected.message) {
            reviewComment.classList.add('hidden');
            reviewCommentBody.textContent = '';
            return;
        }
        reviewCommentTitle.textContent = selected.author_is_admin ? 'Admin note' : 'Commentary';
        reviewCommentBody.textContent = selected.message;
        reviewComment.classList.remove('hidden');
    }

    function reviewerStatusBadge(status) {
        const normalized = (status || '').toLowerCase();
        let label = status || '';
        let className = 'badge-neutral';
        if (normalized === 'pending') {
            label = 'Pending';
            className = 'badge-info';
        } else if (normalized === 'approved') {
            label = 'Approved';
            className = 'badge-success';
        } else if (normalized === 'changes_requested') {
            label = 'Changes requested';
            className = 'badge-warning';
        } else if (normalized === 'declined') {
            label = 'Declined';
            className = 'badge-danger';
        }
        return { label, className };
    }

    function renderReviewerAssignments(reviewers) {
        if (!reviewerList) return;
        reviewerList.innerHTML = '';
        if (!Array.isArray(reviewers) || reviewers.length === 0) {
            reviewerList.innerHTML =
                '<div class="text-xs text-slate-500">No reviewers assigned yet.</div>';
            if (reviewProgress) {
                reviewProgress.classList.add('hidden');
                reviewProgress.textContent = '';
            }
            return;
        }
        if (reviewProgress) {
            const total = reviewers.length;
            const approvedCount = reviewers.filter((reviewer) => {
                return (reviewer.status || '').toLowerCase() === 'approved';
            }).length;
            reviewProgress.textContent = `${approvedCount}/${total} approved`;
            reviewProgress.classList.remove('hidden');
        }
        reviewers.forEach((reviewer) => {
            const row = document.createElement('div');
            row.className = 'reviewer-item';
            const name = document.createElement('div');
            name.className = 'reviewer-name';
            name.textContent = reviewer.email || 'Unknown';
            const badge = document.createElement('span');
            const { label, className } = reviewerStatusBadge(reviewer.status);
            badge.className = `badge ${className}`;
            badge.textContent = label || 'Pending';
            row.appendChild(name);
            row.appendChild(badge);
            reviewerList.appendChild(row);
        });
    }

    function renderSelectedReviewers() {
        if (!reviewerList) return;
        reviewerList.innerHTML = '';
        const selected = Array.from(selectedReviewerIds);
        if (!selected.length) {
            reviewerList.innerHTML =
                '<div class="text-xs text-slate-500">No reviewers selected yet.</div>';
            return;
        }
        selected.forEach((reviewerId) => {
            const admin = orgAdmins.find((item) => item.id === reviewerId);
            const row = document.createElement('div');
            row.className = 'reviewer-item';
            const name = document.createElement('div');
            name.className = 'reviewer-name';
            name.textContent = admin && admin.email ? admin.email : 'Unknown';
            const remove = document.createElement('button');
            remove.type = 'button';
            remove.className = 'reviewer-remove';
            remove.textContent = '✕';
            remove.addEventListener('click', () => {
                selectedReviewerIds.delete(reviewerId);
                renderReviewerSelection(orgAdmins);
                renderSelectedReviewers();
            });
            row.appendChild(name);
            row.appendChild(remove);
            reviewerList.appendChild(row);
        });
    }

    function renderReviewerSelection(admins) {
        if (!reviewerSelect) return;
        reviewerSelect.innerHTML = '';
        if (!Array.isArray(admins) || admins.length === 0) {
            reviewerSelect.innerHTML =
                '<div class="text-xs text-slate-500">No admins available.</div>';
            return;
        }
        const row = document.createElement('div');
        row.className = 'reviewer-add-row';
        const select = document.createElement('select');
        select.className = 'input-base input-sm';
        const candidates = admins.filter((admin) => {
            if (currentUserId && Number(admin.id) === Number(currentUserId)) {
                return false;
            }
            return !selectedReviewerIds.has(admin.id);
        });
        if (!candidates.length) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No eligible reviewers';
            select.appendChild(option);
            select.disabled = true;
        } else {
            candidates.forEach((admin) => {
                const option = document.createElement('option');
                option.value = String(admin.id);
                option.textContent = admin.email || 'Unknown';
                select.appendChild(option);
            });
        }
        const addBtn = document.createElement('button');
        addBtn.type = 'button';
        addBtn.className = 'btn btn-outline btn-xs';
        addBtn.textContent = 'Add reviewer';
        addBtn.disabled = !candidates.length;
        addBtn.addEventListener('click', () => {
            const value = select.value;
            if (!value) return;
            selectedReviewerIds.add(Number(value));
            if (reviewerSelectStatus) reviewerSelectStatus.textContent = '';
            renderReviewerSelection(admins);
            renderSelectedReviewers();
        });
        row.appendChild(select);
        row.appendChild(addBtn);
        reviewerSelect.appendChild(row);
    }

    function renderReviewerAddOptions() {
        if (!reviewerAddSelect) return;
        reviewerAddSelect.innerHTML = '';
        const assignedIds = new Set(
            Array.isArray(currentReviewers)
                ? currentReviewers.map((reviewer) => Number(reviewer.id))
                : []
        );
        const candidates = Array.isArray(orgAdmins)
            ? orgAdmins.filter((admin) => {
                if (!admin) return false;
                if (currentUserId && Number(admin.id) === Number(currentUserId)) {
                    return false;
                }
                return !assignedIds.has(admin.id);
            })
            : [];
        if (!candidates.length) {
            const option = document.createElement('option');
            option.value = '';
            option.textContent = 'No eligible reviewers';
            reviewerAddSelect.appendChild(option);
            reviewerAddSelect.disabled = true;
            if (reviewerAddBtn) reviewerAddBtn.disabled = true;
            return;
        }
        reviewerAddSelect.disabled = false;
        if (reviewerAddBtn) reviewerAddBtn.disabled = false;
        candidates.forEach((admin) => {
            const option = document.createElement('option');
            option.value = String(admin.id);
            option.textContent = admin.email || 'Unknown';
            reviewerAddSelect.appendChild(option);
        });
    }

    function updateReviewerPanel() {
        if (!reviewerPanel) return;
        const hasActiveOrg = Boolean(activeOrgRole);
        reviewerPanel.classList.toggle('hidden', !hasActiveOrg);
        if (!hasActiveOrg) return;

        if (singleAdminOrg && !currentSubmissionId) {
            reviewerPanel.classList.add('hidden');
            return;
        }

        if (currentSubmissionId) {
            if (reviewerSelect) reviewerSelect.classList.add('hidden');
            if (reviewerSelectStatus) reviewerSelectStatus.textContent = '';
            if (reviewerAddStatus) reviewerAddStatus.textContent = '';
            renderReviewerAssignments(currentReviewers);
            if (reviewerAdd) {
                const canAddReviewer =
                    activeOrgRole === 'admin'
                    && (currentSubmissionStatus === 'pending' || currentSubmissionStatus === 'approved');
                reviewerAdd.classList.toggle('hidden', !canAddReviewer);
                if (canAddReviewer) {
                    renderReviewerAddOptions();
                }
            }
            if (singleAdminOrg && (!currentReviewers || currentReviewers.length === 0)) {
                reviewerPanel.classList.add('hidden');
            }
            return;
        }

        const showPanel = Boolean(currentData);
        reviewerPanel.classList.toggle('hidden', !showPanel);
        if (!showPanel) return;
        if (reviewerAdd) reviewerAdd.classList.add('hidden');
        if (reviewerSelect) reviewerSelect.classList.remove('hidden');
        if (reviewerSelectStatus) reviewerSelectStatus.textContent = '';
        renderReviewerSelection(orgAdmins);
        renderSelectedReviewers();
    }

    async function loadOrgAdmins() {
        if (!isAuthenticated) return;
        try {
            const response = await fetch('/orgs/info');
            if (!response.ok) return;
            const data = await response.json();
            if (!data || !data.id) return;
            orgAdmins = Array.isArray(data.admins)
                ? data.admins
                      .filter((admin) => admin && admin.id)
                      .map((admin) => ({
                          id: Number(admin.id),
                          email: admin.email || '',
                      }))
                : [];
            singleAdminOrg = orgAdmins.length === 1
                && currentUserId
                && Number(orgAdmins[0].id) === Number(currentUserId);
            selectedReviewerIds = new Set(
                Array.from(selectedReviewerIds).filter((id) =>
                    orgAdmins.some((admin) => admin.id === id)
                )
            );
            renderReviewerSelection(orgAdmins);
            updateReviewerPanel();
        } catch (error) {
            // Ignore admin load errors
        }
    }

    async function fetchOrganizations() {
        const response = await fetch('/orgs');
        if (!response.ok) {
            throw new Error('Failed to load orgs');
        }
        return response.json();
    }

    async function loadOrganizations() {
        try {
            const data = await fetchOrganizations();
            const orgs = Array.isArray(data.organizations) ? data.organizations : [];
            orgSelectList.innerHTML = '';
            if (!orgs.length) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No orgs yet';
                orgSelectList.appendChild(option);
            } else {
                orgs.forEach((org) => {
                    const option = document.createElement('option');
                    option.value = org.id;
                    option.textContent = org.name;
                    if (org.is_active) {
                        option.selected = true;
                    }
                    orgSelectList.appendChild(option);
                });
            }
            if (data.active_org) {
                setOrgLabel(data.active_org);
            }
        } catch (error) {
            setStatus(orgSelectStatus, 'Unable to load organizations.', 'error');
        }
    }

    async function loadOrgInfo() {
        try {
            const response = await fetch('/orgs/info');
            if (!response.ok) {
                orgInfoContent.innerHTML =
                    '<div class="text-xs text-slate-500">Unable to load org info.</div>';
                if (orgInfoEdit) {
                    orgInfoEdit.classList.add('hidden');
                }
                return;
            }
            const data = await response.json();
            if (!data || !data.id) {
                orgInfoContent.innerHTML =
                    '<div class="text-xs text-slate-500">No active organization.</div>';
                if (orgInfoEdit) {
                    orgInfoEdit.classList.add('hidden');
                }
                return;
            }
            const admins = Array.isArray(data.admins) ? data.admins : [];
            const roleLabel = data.role_label || (data.role ? data.role.replace('_', ' ') : '');
            const adminList = admins.length
                ? admins
                      .map((admin) => {
                          const label = admin.email || 'Unknown';
                          return `<li class="text-sm text-slate-600">${label}</li>`;
                      })
                      .join('')
                : '<li class="text-sm text-slate-500">No admins listed.</li>';

            orgInfoContent.innerHTML = `
                <div>
                    <div class="text-xs text-slate-400 uppercase tracking-wider">Name</div>
                    <div class="text-sm font-semibold text-slate-700">${data.name}</div>
                </div>
                <div>
                    <div class="text-xs text-slate-400 uppercase tracking-wider">Your role</div>
                    <div class="text-sm text-slate-600">${roleLabel || 'Member'}</div>
                </div>
                <div>
                    <div class="text-xs text-slate-400 uppercase tracking-wider">Admins</div>
                    <ul class="mt-1 space-y-1">${adminList}</ul>
                </div>
                <div>
                    <div class="text-xs text-slate-400 uppercase tracking-wider">Members</div>
                    <div class="text-sm text-slate-600">${data.member_count}</div>
                </div>
            `;
            if (orgInfoEdit) {
                orgInfoEdit.classList.toggle('hidden', data.role !== 'admin');
            }
        } catch (error) {
            orgInfoContent.innerHTML =
                '<div class="text-xs text-slate-500">Unable to load org info.</div>';
            if (orgInfoEdit) {
                orgInfoEdit.classList.add('hidden');
            }
        }
    }

    async function loadOrgMembers() {
        try {
            const response = await fetch('/orgs/members');
            if (!response.ok) {
                orgEditMembers.innerHTML = '';
                orgEditMembersStatus.textContent = 'Unable to load members.';
                return;
            }
            const data = await response.json();
            const members = Array.isArray(data.members) ? data.members : [];
            orgEditMembers.innerHTML = '';
            if (!members.length) {
                orgEditMembers.innerHTML =
                    '<div class="text-xs text-slate-500">No members yet.</div>';
            } else {
                members.filter((member) => !member.is_self).forEach((member) => {
                    const row = document.createElement('div');
                    row.className = 'flex items-center justify-between gap-2 rounded-md border border-slate-200 bg-white px-2 py-1.5';

                    const info = document.createElement('div');
                    info.className = 'text-sm text-slate-700';
                    info.textContent = member.email || 'Unknown';

                    const role = document.createElement('span');
                    role.className = 'text-[10px] uppercase tracking-wider text-slate-400';
                    role.textContent = member.role || '';

                    const right = document.createElement('div');
                    right.className = 'flex items-center gap-3';
                    right.appendChild(role);

                    if (member.role !== 'admin') {
                        const promoteBtn = document.createElement('button');
                        promoteBtn.type = 'button';
                        promoteBtn.className = 'text-xs text-slate-700 hover:text-slate-900';
                        promoteBtn.textContent = 'Make admin';
                        promoteBtn.addEventListener('click', () =>
                            promoteOrgMember(member.membership_id)
                        );
                        right.appendChild(promoteBtn);
                    }

                    const removeBtn = document.createElement('button');
                    removeBtn.type = 'button';
                    removeBtn.className =
                        'text-xs text-rose-600 hover:text-rose-700';
                    removeBtn.textContent = 'Remove';
                    removeBtn.addEventListener('click', () =>
                        removeOrgMember(member.membership_id)
                    );

                    right.appendChild(removeBtn);
                    row.appendChild(info);
                    row.appendChild(right);
                    orgEditMembers.appendChild(row);
                });
            }
            if (data.member_count !== undefined) {
                orgEditMembersStatus.textContent = `Total: ${data.member_count}`;
            } else {
                orgEditMembersStatus.textContent = '';
            }
        } catch (error) {
            orgEditMembers.innerHTML = '';
            orgEditMembersStatus.textContent = 'Unable to load members.';
        }
    }

    async function removeOrgMember(membershipId) {
        if (!membershipId) return;
        try {
            const response = await fetch('/orgs/members/remove', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ membership_id: membershipId }),
            });
            const data = await response.json();
            if (!response.ok) {
                orgEditMembersStatus.textContent = data.error || 'Failed to remove member.';
                return;
            }
            loadOrgMembers();
        } catch (error) {
            orgEditMembersStatus.textContent = 'Failed to remove member.';
        }
    }

    async function promoteOrgMember(membershipId) {
        if (!membershipId) return;
        try {
            const response = await fetch('/orgs/members/promote', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ membership_id: membershipId }),
            });
            const data = await response.json();
            if (!response.ok) {
                orgEditMembersStatus.textContent = data.error || 'Failed to promote member.';
                return;
            }
            loadOrgMembers();
        } catch (error) {
            orgEditMembersStatus.textContent = 'Failed to promote member.';
        }
    }

    async function submitOrgInvites() {
        consumeEditEmailInput();
        const ok = finalizeEditEmailInput();
        if (!ok) return;
        setStatus(orgEditEmailStatus, '');
        if (!orgEditInviteEmails.length) {
            setStatus(orgEditInviteStatus, 'Add at least one email.', 'error');
            return;
        }
        setStatus(orgEditInviteStatus, 'Sending invites...');
        try {
            const response = await fetch('/orgs/invites/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invite_emails: orgEditInviteEmails }),
            });
            const data = await response.json();
            if (!response.ok) {
                setStatus(orgEditInviteStatus, data.error || 'Failed to send invites.', 'error');
                return;
            }
            orgEditInviteEmails = [];
            renderEditEmailChips();
            orgEditEmailInput.value = '';
            const created = data.created || 0;
            const skipped = data.skipped || 0;
            setStatus(
                orgEditInviteStatus,
                `Invites sent: ${created}. Skipped: ${skipped}.`,
                'success'
            );
            if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshNotifications) {
                window.InvoiceAIHeader.refreshNotifications(true);
            }
        } catch (error) {
            setStatus(orgEditInviteStatus, 'Failed to send invites.', 'error');
        }
    }

    async function openSubmissionFromNotification(submissionId) {
        if (!submissionId) return;
        isExtracting = false;
        renderSubmissionLoading();
        setReviewState(submissionId, 'loading', false);
        updateInvoiceActions();
        try {
            const response = await fetch(`/invoices/submissions/${submissionId}`);
            const data = await response.json();
            if (!response.ok) {
                exportStatus.textContent = data.error || 'Failed to load submission.';
                if (jsonContent) {
                    jsonContent.innerHTML = '<div class="text-red-500 p-4">Failed to load submission.</div>';
                }
                return;
            }
            currentPdfFile = null;
            exportStatus.textContent = '';
            const canReview = typeof data.can_review === 'boolean'
                ? data.can_review
                : (activeOrgRole === 'admin'
                    && data.status === 'pending');
            const canExport = typeof data.can_export === 'boolean'
                ? data.can_export
                : (activeOrgRole === 'admin'
                    && data.status === 'approved');
            currentReviewers = Array.isArray(data.reviewers) ? data.reviewers : [];
            currentReviewerStatus = data.reviewer_status || null;
            setReviewState(submissionId, data.status, canReview, canExport);
            canvasContainer.innerHTML = '';
            canvasContainer.classList.add('hidden');
            dropZone.classList.remove('hidden');
            setSubmissionMeta({
                submitted_by: data.submitted_by,
                created_at: data.created_at,
                status: data.status,
                exported_at: data.exported_at,
                exported_by: data.exported_by,
            });
            setReviewComment(data.comments);
            updateReviewerPanel();
            if (data.invoice_data) {
                displayJSON(data.invoice_data);
            } else {
                displayJSON({});
            }
            if (data.invoice_file_url) {
                await renderPDFFromUrl(data.invoice_file_url);
            } else {
                exportStatus.textContent = 'Invoice PDF is missing.';
            }
        } catch (error) {
            exportStatus.textContent = 'Failed to load submission.';
            if (jsonContent) {
                jsonContent.innerHTML = '<div class="text-red-500 p-4">Failed to load submission.</div>';
            }
        }
    }

    window.InvoiceAI = window.InvoiceAI || {};
    window.InvoiceAI.openSubmissionFromNotification = openSubmissionFromNotification;

    async function handleSubmissionAction(submissionId, approve) {
        if (!submissionId) return;
        if (approveBtn) approveBtn.disabled = true;
        if (rejectBtn) rejectBtn.disabled = true;
        try {
            exportStatus.textContent = approve ? 'Recording approval...' : 'Declining...';
            const endpoint = approve
                ? '/invoices/submissions/approve'
                : '/invoices/submissions/reject';
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ submission_id: submissionId }),
            });
            const result = await response.json();
            if (!response.ok) {
                exportStatus.textContent = result.error || 'Update failed.';
                return;
            }
            if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshNotifications) {
                await window.InvoiceAIHeader.refreshNotifications(true);
            }
            if (result && typeof result === 'object') {
                currentReviewers = Array.isArray(result.reviewers) ? result.reviewers : currentReviewers;
                currentReviewerStatus = result.reviewer_status || currentReviewerStatus;
                const canReview = typeof result.can_review === 'boolean'
                    ? result.can_review
                    : (result.status === 'pending'
                        && (currentReviewerStatus === 'pending'
                            || (activeOrgRole === 'admin' && !currentReviewerStatus)));
                const canExport = typeof result.can_export === 'boolean'
                    ? result.can_export
                    : (result.status === 'approved' && currentReviewerStatus === 'approved');
                setReviewState(submissionId, result.status || currentSubmissionStatus, canReview, canExport);
                if (currentSubmissionMeta) {
                    setSubmissionMeta({ ...currentSubmissionMeta, status: result.status || currentSubmissionStatus });
                }
            }
            exportStatus.textContent = approve ? 'Approval recorded.' : 'Declined.';
        } catch (error) {
            exportStatus.textContent = approve ? 'Approval failed.' : 'Rejection failed.';
        } finally {
            if (approveBtn) approveBtn.disabled = false;
            if (rejectBtn) rejectBtn.disabled = false;
        }
    }

    async function exportCurrentInvoice() {
        const hasSubmission = Boolean(currentSubmissionId);
        if (!currentData) {
            exportStatus.textContent = 'No data to export.';
            return;
        }
        if (!hasSubmission) {
            exportStatus.textContent = 'Submit for approval before exporting.';
            return;
        }
        if (!currentCanExport || currentSubmissionStatus !== 'approved') {
            exportStatus.textContent = 'Export is available after all reviewers approve.';
            return;
        }
        if (!googleConnected) {
            startGoogleConnect(exportStatus);
            return;
        }
        if (!currentSheetId) {
            if (!googleApiKey) {
                sheetStatus.textContent = 'Google API key is not configured.';
                return;
            }
            if (!pickerApiLoaded) {
                sheetStatus.textContent = 'Loading Google Sheet picker...';
                return;
            }
            pendingExportAfterSheetSelect = true;
            openSheetPicker();
            return;
        }
        exportStatus.textContent = 'Exporting invoice...';
        try {
            const payload = hasSubmission
                ? { ...currentData, submission_id: currentSubmissionId }
                : { ...currentData };
            const exportResponse = await fetch('/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const exportResult = await exportResponse.json();
            if (!exportResponse.ok) {
                exportStatus.textContent = exportResult.error || 'Export failed.';
                return;
            }
            exportStatus.textContent = 'Exported to Google Sheets.';
            if (hasSubmission && currentSubmissionMeta) {
                setSubmissionMeta({
                    ...currentSubmissionMeta,
                    exported_at: exportResult.exported_at || new Date().toISOString(),
                    exported_by: exportResult.exported_by || '',
                });
            }
            updateGoogleStatus();
            showToast('Exported to Google Sheets.', 'success');
            setTimeout(() => {
                clearInvoiceView('<div class="h-full flex flex-col items-center justify-center text-slate-400 text-sm p-8 text-center">Export completed.</div>');
            }, 400);
        } catch (error) {
            exportStatus.textContent = 'Export failed.';
        }
    }

    async function submitRequestEdit() {
        if (!currentSubmissionId) return;
        const message = (requestEditInput.value || '').trim();
        if (!message) {
            requestEditStatus.textContent = 'Please add a comment before sending.';
            return;
        }
        requestEditSend.disabled = true;
        requestEditStatus.textContent = 'Sending...';
        try {
            const response = await fetch('/invoices/submissions/request-edit', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    submission_id: currentSubmissionId,
                    message,
                }),
            });
            const result = await response.json();
            if (!response.ok) {
                requestEditStatus.textContent = result.error || 'Failed to request edit.';
                return;
            }
            closeRequestEditModal();
            exportStatus.textContent = 'Edit requested.';
            if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshNotifications) {
                await window.InvoiceAIHeader.refreshNotifications(true);
            }
            clearInvoiceView();
        } catch (error) {
            requestEditStatus.textContent = 'Failed to request edit.';
        } finally {
            requestEditSend.disabled = false;
        }
    }

    async function deleteSubmission() {
        if (!currentSubmissionId) return;
        const isCancel = currentSubmissionStatus === 'pending';
        const promptText = isCancel
            ? 'Cancel this submission? This cannot be undone.'
            : 'Delete this submission? This cannot be undone.';
        const ok = window.confirm(promptText);
        if (!ok) return;
        if (deleteSubmissionBtn) deleteSubmissionBtn.disabled = true;
        exportStatus.textContent = isCancel ? 'Cancelling submission...' : 'Deleting submission...';
        try {
            const response = await fetch('/invoices/submissions/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ submission_id: currentSubmissionId }),
            });
            const result = await response.json();
            if (!response.ok) {
                exportStatus.textContent = result.error || 'Delete failed.';
                return;
            }
            const doneMessage = isCancel ? 'Submission cancelled.' : 'Submission deleted.';
            exportStatus.textContent = doneMessage;
            setReviewState(null);
            if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshNotifications) {
                await window.InvoiceAIHeader.refreshNotifications(true);
            }
            clearInvoiceView(`<div class="h-full flex flex-col items-center justify-center text-slate-400 text-sm p-8 text-center">${doneMessage}</div>`);
        } catch (error) {
            exportStatus.textContent = 'Delete failed.';
        } finally {
            if (deleteSubmissionBtn) deleteSubmissionBtn.disabled = false;
        }
    }

    function loadPickerApi() {
        if (!googleApiKey || !window.gapi) return;
        window.gapi.load('picker', { callback: () => { pickerApiLoaded = true; } });
    }

    dropZone.addEventListener('click', () => fileInput.click());
    fileInput.addEventListener('change', (e) => handleFiles(e.target.files));
    dropZone.addEventListener('dragover', (e) => { e.preventDefault(); dropZone.classList.add('border-blue-400'); });
    dropZone.addEventListener('dragleave', (e) => { e.preventDefault(); dropZone.classList.remove('border-blue-400'); });
    dropZone.addEventListener('drop', (e) => { e.preventDefault(); handleFiles(e.dataTransfer.files); });

    function handleFiles(files) {
        if (files.length > 0 && files[0].type === 'application/pdf') {
            currentPdfFile = files[0];
            currentData = null;
            isExtracting = true;
            if (extractionController) {
                extractionController.abort();
                extractionController = null;
            }
            if (!(currentSubmissionId && currentSubmissionStatus === 'changes_requested' && activeOrgRole !== 'admin')) {
                setReviewState(null);
            }
            updateInvoiceActions();
            uploadFile(files[0]);
            renderPDF(files[0]);
        } else {
            showToast('Please upload a valid PDF file.', 'warning');
        }
    }

    async function renderCurrentPdf() {
        if (!currentPdfDoc || isRenderingPdf) return;
        isRenderingPdf = true;
        zoomInBtn.disabled = true;
        zoomOutBtn.disabled = true;

        canvasContainer.innerHTML = '';
        canvasContainer.classList.remove('hidden');
        dropZone.classList.add('hidden');

        pdfWrapper.scrollTop = 0;

        for (let pageNum = 1; pageNum <= currentPdfDoc.numPages; pageNum++) {
            if (!currentPdfDoc) {
                isRenderingPdf = false;
                zoomInBtn.disabled = false;
                zoomOutBtn.disabled = false;
                return;
            }
            const page = await currentPdfDoc.getPage(pageNum);
            const viewport = page.getViewport({ scale: pageScale });

            const pageWrapper = document.createElement('div');
            pageWrapper.className = 'pdf-page relative shadow-lg bg-white';
            pageWrapper.dataset.page = pageNum;
            pageWrapper.style.width = viewport.width + 'px';
            pageWrapper.style.height = viewport.height + 'px';

            const canvas = document.createElement('canvas');
            canvas.height = viewport.height;
            canvas.width = viewport.width;
            const ctx = canvas.getContext('2d');

            const highlightLayer = document.createElement('div');
            highlightLayer.className = 'highlight-layer absolute inset-0';
            highlightLayer.dataset.page = pageNum;

            pageWrapper.appendChild(canvas);
            pageWrapper.appendChild(highlightLayer);
            canvasContainer.appendChild(pageWrapper);

            await page.render({ canvasContext: ctx, viewport: viewport }).promise;
        }

        isRenderingPdf = false;
        zoomInBtn.disabled = false;
        zoomOutBtn.disabled = false;
        updateZoomLabel();
        updatePageCounter();
    }

    async function renderPDFBuffer(buffer) {
        const typedarray = new Uint8Array(buffer);
        currentPdfDoc = await pdfjsLib.getDocument(typedarray).promise;
        await renderCurrentPdf();
    }

    async function renderPDF(file) {
        const buffer = await file.arrayBuffer();
        await renderPDFBuffer(buffer);
    }

    async function renderPDFFromUrl(url) {
        const response = await fetch(url);
        if (!response.ok) {
            throw new Error('Failed to load PDF');
        }
        const buffer = await response.arrayBuffer();
        await renderPDFBuffer(buffer);
    }

    async function uploadFile(file) {
        if (extractionController) {
            extractionController.abort();
        }
        extractionController = new AbortController();
        extractionRequestId = (window.crypto && window.crypto.randomUUID)
            ? window.crypto.randomUUID()
            : `${Date.now()}-${Math.random().toString(16).slice(2)}`;
        const formData = new FormData();
        formData.append('file', file);
        formData.append('request_id', extractionRequestId);
        jsonContent.innerHTML = `
            <div class="p-8 text-center text-slate-500">
                <div class="text-sm font-medium mb-4">Extracting invoice data</div>
                <div class="progress-track h-2 rounded-full overflow-hidden">
                    <div class="progress-bar h-full rounded-full"></div>
                </div>
            </div>
        `;

        try {
            const response = await fetch('/process', {
                method: 'POST',
                body: formData,
                signal: extractionController.signal,
            });
            const result = await response.json();
            if (!response.ok) {
                if (result && result.code === 'OCR_EMPTY') {
                    openOcrEmptyModal();
                    jsonContent.innerHTML = '<div class="p-6 text-center text-amber-600">No text detected in this PDF.</div>';
                } else if (result && result.code === 'RATE_LIMITED') {
                    showToast('We are throttling requests right now. Please try again in a moment.', 'error');
                    jsonContent.innerHTML = '<div class="p-6 text-center text-slate-500">Please try again in a moment.</div>';
                } else {
                    jsonContent.innerHTML = '<div class="text-red-500 p-4">Error processing file.</div>';
                }
                return;
            }
            if (result && result.error) {
                jsonContent.innerHTML = `<div class="text-red-500 p-4">${result.error}</div>`;
                return;
            }
            displayJSON(result);
        } catch (error) {
            if (error && error.name === 'AbortError') {
                jsonContent.innerHTML = '<div class="p-6 text-center text-slate-500">Extraction cancelled.</div>';
                return;
            }
            jsonContent.innerHTML = '<div class="text-red-500 p-4">Error processing file.</div>';
        } finally {
            if (extractionController) {
                extractionController = null;
            }
            extractionRequestId = null;
            isExtracting = false;
            updateInvoiceActions();
        }
    }

    function normalizeDateToInput(value) {
        if (!value || typeof value !== 'string') return '';
        const trimmed = value.trim();
        const dmy = trimmed.match(/^(\d{1,2})\.(\d{1,2})\.(\d{4})$/);
        if (dmy) {
            const [_, d, m, y] = dmy;
            const dd = d.padStart(2, '0');
            const mm = m.padStart(2, '0');
            return `${y}-${mm}-${dd}`;
        }
        const ymd = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (ymd) return trimmed;
        return '';
    }

    function normalizeDateFromInput(value) {
        if (!value || typeof value !== 'string') return '';
        const trimmed = value.trim();
        const ymd = trimmed.match(/^(\d{4})-(\d{2})-(\d{2})$/);
        if (!ymd) return trimmed;
        const [_, y, m, d] = ymd;
        return `${d}.${m}.${y}`;
    }

    function displayJSON(data) {
        currentData = {};
        isExtracting = false;
        exportStatus.textContent = '';
        jsonContent.innerHTML = '';
        updateReviewerPanel();
        const sectionConfig = [
            {
                id: 'invoice',
                title: 'Invoice',
                match: (key) =>
                    key.startsWith('invoice_') ||
                    key === 'description_keyword'
            },
            {
                id: 'supplier',
                title: 'Supplier',
                match: (key) => key.startsWith('supplier_')
            },
            {
                id: 'buyer',
                title: 'Buyer',
                match: (key) => key.startsWith('buyer_')
            },
            {
                id: 'vat',
                title: 'VAT',
                match: (key) =>
                    key === 'vat_rates' ||
                    key === 'supply_type' ||
                    key === 'service_category' ||
                    key === 'scenario'
            }
        ];

        const sections = {};
        sectionConfig.forEach((section) => {
            const wrapper = document.createElement('div');
            wrapper.className = '';

            const header = document.createElement('button');
            header.type = 'button';
            header.className = 'section-header w-full flex items-center justify-between rounded-lg px-3 py-2 text-left text-sm font-semibold text-slate-700';
            header.innerHTML = `
                <span>${section.title}</span>
                <span class="transition-transform text-slate-400" data-chevron>⌄</span>
            `;

            const body = document.createElement('div');
            body.className = 'section-body rounded-b-lg bg-white/70 p-2 space-y-1';

            header.addEventListener('click', () => {
                const isHidden = body.classList.toggle('hidden');
                const chevron = header.querySelector('[data-chevron]');
                if (chevron) {
                    chevron.style.transform = isHidden ? 'rotate(-90deg)' : 'rotate(0deg)';
                }
            });

            wrapper.appendChild(header);
            wrapper.appendChild(body);
            jsonContent.appendChild(wrapper);

            sections[section.id] = { wrapper, body };
        });

        const getSectionId = (key) => {
            const match = sectionConfig.find((section) => section.match(key));
            return match ? match.id : 'invoice';
        };

        Object.entries(data).forEach(([key, item]) => {
            const row = document.createElement('div');

            const value = typeof item === 'object' && item !== null ? item.value : item;
            const bbox = typeof item === 'object' && item !== null ? item.bbox : null;
            const confidence = typeof item === 'object' && item !== null ? item.confidence : null;

            currentData[key] = {
                value: value ?? '',
                bbox: bbox ?? null,
                confidence: confidence ?? null
            };

            let confidenceClass = '';
            let confidenceBadgeClass = '';
            let confidenceLabel = '';
            if (typeof confidence === 'string') {
                const conf = confidence.toLowerCase();
                if (conf === 'definitely wrong') {
                    confidenceClass = 'confidence-wrong';
                    confidenceBadgeClass = 'bg-rose-100 text-rose-700 border-rose-200';
                    confidenceLabel = 'Definitely wrong';
                } else if (conf === 'low confidence') {
                    confidenceClass = 'confidence-low';
                    confidenceBadgeClass = 'bg-amber-100 text-amber-700 border-amber-200';
                    confidenceLabel = 'Low confidence';
                }
            }

            row.className = `json-row p-3 rounded-lg mb-1 transition-colors border border-transparent ${confidenceClass}`;

            const labelRow = document.createElement('div');
            labelRow.className = 'flex items-center justify-between gap-2 mb-1';

            const label = document.createElement('div');
            label.className = 'text-xs font-bold uppercase text-slate-400 tracking-wider';
            label.textContent = key.replace(/_/g, ' ');

            labelRow.appendChild(label);

            if (confidenceLabel) {
                const badge = document.createElement('div');
                badge.className = `text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full border ${confidenceBadgeClass}`;
                badge.textContent = confidenceLabel;
                labelRow.appendChild(badge);
            }

            const input = document.createElement('input');
            const isDateField = key === 'invoice_date';
            input.type = isDateField ? 'date' : 'text';
            input.value = isDateField ? normalizeDateToInput(value) : (value ?? '');
            input.placeholder = 'Empty';
            input.className = 'w-full text-sm font-medium text-slate-800 bg-white border border-slate-200 rounded-md px-2 py-1 focus:outline-none focus:ring-2 focus:ring-blue-200';

            input.addEventListener('input', (e) => {
                currentData[key].value = isDateField
                    ? normalizeDateFromInput(e.target.value)
                    : e.target.value;
            });

            row.appendChild(labelRow);
            row.appendChild(input);

            if (bbox) {
                row.addEventListener('click', () => {
                    document.querySelectorAll('.json-row').forEach(r => r.classList.remove('active'));
                    row.classList.add('active');
                    drawHighlight(bbox);
                });
            }
            const sectionId = getSectionId(key);
            const target = sections[sectionId] ? sections[sectionId].body : jsonContent;
            target.appendChild(row);
        });
        updateInvoiceActions();
    }

    function drawHighlight(bbox) {
        document.querySelectorAll('.highlight-layer').forEach(el => el.innerHTML = '');

        if (!bbox) return;

        const pageNum = bbox.page || 1;
        const targetLayer = document.querySelector(`.highlight-layer[data-page="${pageNum}"]`);

        if (targetLayer) {
            const div = document.createElement('div');
            div.className = 'highlight-box';
            div.style.left = 100 * bbox[0] + '%';
            div.style.top = 100 * bbox[1] + '%';
            div.style.width = 100 * bbox[2] + '%';
            div.style.height = 100 * bbox[3] + '%';

            targetLayer.appendChild(div);

            targetLayer.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }
    }

    async function updateGoogleStatus() {
        try {
            const response = await fetch('/auth/status/');
            if (!response.ok) {
                googleConnected = false;
                closeOrgDropdown();
                activeOrgRole = null;
                singleAdminOrg = false;
                orgRoleInitialized = true;
                updateInvoiceActions();
                if (sheetStatus) {
                    sheetStatus.textContent = '';
                }
                clearInvoiceView();
                return;
            }
            const data = await response.json();
            const isAuthenticated = Boolean(data.authenticated);
            googleConnected = Boolean(data.google_connected ?? data.connected);
            if (isAuthenticated) {
                currentUserId = data.user_id || null;
                activeOrgRole = data.active_org ? data.active_org.role : null;
                currentSheetId = data.spreadsheet_id || null;
                currentSheetLabel = data.spreadsheet_title || data.spreadsheet_id || null;
                orgRoleInitialized = true;
                if (window.InvoiceAIHeader && window.InvoiceAIHeader.applyAuthStatus) {
                    window.InvoiceAIHeader.applyAuthStatus(data);
                }
                if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshOrgMenu) {
                    window.InvoiceAIHeader.refreshOrgMenu();
                }

                updateInvoiceActions();
                loadOrgAdmins();
                if (initialSubmissionId && !initialSubmissionHandled) {
                    initialSubmissionHandled = true;
                    openSubmissionFromNotification(initialSubmissionId);
                }
                if (data.spreadsheet_id) {
                    currentSheetLabel = data.spreadsheet_title || data.spreadsheet_id;
                }
                updateSavingDestination();
            } else {
                googleConnected = false;
                if (window.InvoiceAIHeader && window.InvoiceAIHeader.applyAuthStatus) {
                    window.InvoiceAIHeader.applyAuthStatus(data);
                }
                closeOrgDropdown();
                activeOrgRole = null;
                singleAdminOrg = false;
                currentSheetId = null;
                currentSheetLabel = null;
                orgRoleInitialized = true;
                updateInvoiceActions();
                updateReviewerPanel();
                sheetStatus.textContent = 'Connect Google to select a sheet.';
                clearInvoiceView();
                updateSavingDestination();
            }
        } catch (error) {
            orgRoleInitialized = true;
            updateInvoiceActions();
        }
    }

    if (googleDisconnectBtn) {
        googleDisconnectBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/auth/google/disconnect/', { method: 'POST' });
                if (!response.ok) return;
                googleConnected = false;
                closeOrgDropdown();
                closeOrgModals();
                setOrgLabel(null);
                activeOrgRole = null;
                updateInvoiceActions();
                updateGoogleStatus();
            } catch (error) {
                // Ignore disconnect errors in UI
            }
        });
    }

    function openOrgCreateModal() {
        closeOrgDropdown();
        orgCreateModal.classList.remove('hidden');
        setStatus(orgCreateStatus, '');
        setStatus(orgCreateEmailStatus, '');
        orgCreateEmailInput.focus();
    }

    function openOrgSelectModal() {
        closeOrgDropdown();
        orgSelectModal.classList.remove('hidden');
        setStatus(orgSelectStatus, '');
        loadOrganizations();
    }

    function openOrgInfoModal() {
        closeOrgDropdown();
        orgInfoModal.classList.remove('hidden');
        orgInfoContent.innerHTML = '<div class="text-xs text-slate-400">Loading...</div>';
        if (orgInfoEdit) {
            orgInfoEdit.classList.toggle('hidden', activeOrgRole !== 'admin');
        }
        loadOrgInfo();
    }

    function openOrgEditModal() {
        closeOrgDropdown();
        orgEditModal.classList.remove('hidden');
        orgEditMembersStatus.textContent = '';
        setStatus(orgEditEmailStatus, '');
        setStatus(orgEditInviteStatus, '');
        orgEditInviteEmails = [];
        renderEditEmailChips();
        orgEditEmailInput.value = '';
        loadOrgMembers();
        orgEditEmailInput.focus();
    }

    if (orgCreateToggle) {
        orgCreateToggle.addEventListener('click', () => {
            openOrgCreateModal();
        });
    }

    if (orgSelectToggle) {
        orgSelectToggle.addEventListener('click', () => {
            openOrgSelectModal();
        });
    }

    if (orgInfoToggle) {
        orgInfoToggle.addEventListener('click', () => {
            openOrgInfoModal();
        });
    }

    if (orgInfoSelect) {
        orgInfoSelect.addEventListener('click', () => {
            if (orgInfoModal) {
                orgInfoModal.classList.add('hidden');
            }
            openOrgSelectModal();
        });
    }

    if (orgInfoCreate) {
        orgInfoCreate.addEventListener('click', () => {
            if (orgInfoModal) {
                orgInfoModal.classList.add('hidden');
            }
            openOrgCreateModal();
        });
    }

    if (orgInfoEdit) {
        orgInfoEdit.addEventListener('click', () => {
            if (orgInfoModal) {
                orgInfoModal.classList.add('hidden');
            }
            openOrgEditModal();
        });
    }

    if (orgEditToggle) {
        orgEditToggle.addEventListener('click', () => {
            openOrgEditModal();
        });
    }

    if (window.InvoiceAIHeader) {
        window.InvoiceAIHeader.openOrgInfoModal = openOrgInfoModal;
    } else {
        window.InvoiceAIHeader = { openOrgInfoModal };
    }

    document.addEventListener('org-info-open', (event) => {
        openOrgInfoModal();
        if (event && typeof event.preventDefault === 'function') {
            event.preventDefault();
        }
    });

    orgCreateClose.addEventListener('click', () => {
        orgCreateModal.classList.add('hidden');
    });

    orgSelectClose.addEventListener('click', () => {
        orgSelectModal.classList.add('hidden');
    });

    orgInfoClose.addEventListener('click', () => {
        orgInfoModal.classList.add('hidden');
    });

    orgEditClose.addEventListener('click', () => {
        orgEditModal.classList.add('hidden');
    });

    orgCreateEmailInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',' || e.key === 'Tab') {
            if (e.key === 'Tab' && !orgCreateEmailInput.value.trim()) {
                return;
            }
            e.preventDefault();
            finalizeEmailInput();
        }
    });

    orgCreateEmailInput.addEventListener('input', () => {
        consumeEmailInput();
    });

    orgCreateEmailInput.addEventListener('blur', () => {
        finalizeEmailInput();
    });

    orgEditEmailInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ',' || e.key === 'Tab') {
            if (e.key === 'Tab' && !orgEditEmailInput.value.trim()) {
                return;
            }
            e.preventDefault();
            finalizeEditEmailInput();
        }
    });

    orgEditEmailInput.addEventListener('input', () => {
        consumeEditEmailInput();
    });

    orgEditEmailInput.addEventListener('blur', () => {
        finalizeEditEmailInput();
    });

    orgCreateModal.addEventListener('click', (e) => {
        if (e.target === orgCreateModal) {
            orgCreateModal.classList.add('hidden');
        }
    });

    orgSelectModal.addEventListener('click', (e) => {
        if (e.target === orgSelectModal) {
            orgSelectModal.classList.add('hidden');
        }
    });

    orgInfoModal.addEventListener('click', (e) => {
        if (e.target === orgInfoModal) {
            orgInfoModal.classList.add('hidden');
        }
    });

    orgEditModal.addEventListener('click', (e) => {
        if (e.target === orgEditModal) {
            orgEditModal.classList.add('hidden');
        }
    });

    function openRequestEditModal() {
        if (!requestEditModal) return;
        requestEditInput.value = '';
        requestEditStatus.textContent = '';
        requestEditModal.classList.remove('hidden');
        requestEditInput.focus();
    }

    function closeRequestEditModal() {
        if (!requestEditModal) return;
        requestEditModal.classList.add('hidden');
        requestEditStatus.textContent = '';
    }

    if (requestEditClose) {
        requestEditClose.addEventListener('click', () => {
            closeRequestEditModal();
        });
    }

    if (requestEditCancel) {
        requestEditCancel.addEventListener('click', () => {
            closeRequestEditModal();
        });
    }

    if (requestEditModal) {
        requestEditModal.addEventListener('click', (e) => {
            if (e.target === requestEditModal) {
                closeRequestEditModal();
            }
        });
    }

    orgCreateSubmit.addEventListener('click', async () => {
        const name = (orgCreateInput.value || '').trim();
        if (!name) {
            setStatus(orgCreateStatus, 'Organization name is required.', 'error');
            return;
        }
        consumeEmailInput();
        const ok = finalizeEmailInput();
        if (!ok) {
            return;
        }
        setStatus(orgCreateEmailStatus, '');
        setStatus(orgCreateStatus, 'Creating...');
        try {
            const response = await fetch('/orgs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name, invite_emails: orgInviteEmails }),
            });
            const data = await response.json();
            if (!response.ok) {
                setStatus(orgCreateStatus, data.error || 'Failed to create org.', 'error');
                return;
            }
            orgCreateInput.value = '';
            orgCreateEmailInput.value = '';
            orgInviteEmails = [];
            renderEmailChips();
            setOrgLabel({ name: data.name });
            setStatus(orgCreateStatus, 'Organization created.', 'success');
            loadOrganizations();
            updateGoogleStatus();
        } catch (error) {
            setStatus(orgCreateStatus, 'Failed to create org.', 'error');
        }
    });

    orgSelectSubmit.addEventListener('click', async () => {
        const orgId = orgSelectList.value;
        if (!orgId) {
            setStatus(orgSelectStatus, 'Select an organization first.', 'error');
            return;
        }
        setStatus(orgSelectStatus, 'Setting active org...');
        try {
            const response = await fetch('/orgs/activate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ org_id: orgId }),
            });
            const data = await response.json();
            if (!response.ok) {
                setStatus(orgSelectStatus, data.error || 'Failed to activate org.', 'error');
                return;
            }
            setOrgLabel({ name: data.name });
            setStatus(orgSelectStatus, 'Active org updated.', 'success');
            loadOrganizations();
            updateGoogleStatus();
        } catch (error) {
            setStatus(orgSelectStatus, 'Failed to activate org.', 'error');
        }
    });

    orgEditInviteSubmit.addEventListener('click', () => {
        submitOrgInvites();
    });

    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeOrgDropdown();
            closeOrgModals();
            closeExportMenu();
            closeOcrEmptyModal();
        }
    });

    exportBtn.addEventListener('click', async () => {
        if (!currentData) {
            exportStatus.textContent = 'No data to export yet.';
            return;
        }
        if (!googleConnected) {
            startGoogleConnect(exportStatus);
            return;
        }

        exportStatus.textContent = 'Exporting...';
        exportBtn.disabled = true;
        try {
            const response = await fetch('/export', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(currentData),
            });
            const result = await response.json();
            if (!response.ok) {
                exportStatus.textContent = result.error || 'Export failed.';
            } else {
                exportStatus.textContent = 'Exported to Google Sheets.';
                    updateGoogleStatus();
                }
        } catch (error) {
            exportStatus.textContent = 'Export failed.';
        } finally {
            exportBtn.disabled = false;
        }
    });

    submitBtn.addEventListener('click', async () => {
        if (!currentData) {
            exportStatus.textContent = 'No data to submit yet.';
            return;
        }
        if (!activeOrgRole) {
            exportStatus.textContent = 'Select an organization before submitting.';
            return;
        }
        const isResubmit = Boolean(currentSubmissionId) && currentSubmissionStatus === 'changes_requested';
        if (!currentPdfFile && !isResubmit) {
            exportStatus.textContent = 'Upload the invoice PDF before submitting.';
            return;
        }
        if (!isResubmit) {
            if (reviewerSelectStatus) reviewerSelectStatus.textContent = '';
            if (selectedReviewerIds.size === 0 && !singleAdminOrg) {
                exportStatus.textContent = 'Select at least one reviewer.';
                if (reviewerSelectStatus) {
                    reviewerSelectStatus.textContent = 'Select at least one reviewer.';
                }
                return;
            }
        }
        exportStatus.textContent = isResubmit ? 'Resubmitting for approval...' : 'Submitting for approval...';
        submitBtn.disabled = true;
        try {
            const formData = new FormData();
            formData.append('invoice_data', JSON.stringify(currentData));
            if (currentPdfFile) {
                formData.append('invoice_file', currentPdfFile);
            }
            if (isResubmit) {
                formData.append('submission_id', currentSubmissionId);
            } else {
                formData.append('reviewer_ids', JSON.stringify(Array.from(selectedReviewerIds)));
            }
            const response = await fetch(isResubmit ? '/invoices/submissions/resubmit' : '/invoices/submissions', {
                method: 'POST',
                body: formData,
            });
            const result = await response.json();
            if (!response.ok) {
                exportStatus.textContent = result.error || 'Submission failed.';
            } else {
                exportStatus.textContent = isResubmit ? 'Resubmitted for approval.' : 'Submitted for approval.';
                if (window.InvoiceAIHeader && window.InvoiceAIHeader.refreshNotifications) {
                    window.InvoiceAIHeader.refreshNotifications();
                }
                if (isResubmit) {
                    setReviewState(null);
                    setSubmissionMeta(null);
                    setReviewComment([]);
                    clearInvoiceView();
                    exportStatus.textContent = 'Resubmitted for approval.';
                } else {
                    selectedReviewerIds.clear();
                    renderReviewerSelection(orgAdmins);
                    clearInvoiceView();
                    exportStatus.textContent = 'Submitted for approval.';
                }
            }
        } catch (error) {
            exportStatus.textContent = 'Submission failed.';
        } finally {
            submitBtn.disabled = false;
        }
    });

    if (approveBtn) {
        approveBtn.addEventListener('click', () => {
            handleSubmissionAction(currentSubmissionId, true);
        });
    }

    if (requestEditBtn) {
        requestEditBtn.addEventListener('click', () => {
            openRequestEditModal();
        });
    }

    if (cancelExtractionBtn) {
        cancelExtractionBtn.addEventListener('click', () => {
            const requestId = extractionRequestId;
            if (requestId) {
                fetch('/process/cancel', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ request_id: requestId }),
                    keepalive: true,
                }).catch(() => {});
            }
            if (extractionController) {
                extractionController.abort();
                extractionController = null;
            }
            isExtracting = false;
            currentPdfFile = null;
            clearInvoiceView();
        });
    }

    if (rejectBtn) {
        rejectBtn.addEventListener('click', () => {
            handleSubmissionAction(currentSubmissionId, false);
        });
    }

    if (exportMenuBtn) {
        exportMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            if (exportMenu) {
                exportMenu.classList.toggle('hidden');
            }
        });
    }

    if (exportMenu) {
        exportMenu.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    document.addEventListener('click', () => {
        closeExportMenu();
    });

    if (exportGoogleBtn) {
        exportGoogleBtn.addEventListener('click', () => {
            closeExportMenu();
            exportDestination = 'google';
            updateSavingDestination();
            if (!googleConnected) {
                startGoogleConnect(exportStatus);
                return;
            }
            if (!currentSheetId) {
                if (!googleApiKey) {
                    sheetStatus.textContent = 'Google API key is not configured.';
                    return;
                }
                if (!pickerApiLoaded) {
                    sheetStatus.textContent = 'Loading Google Sheet picker...';
                    return;
                }
                pendingExportAfterSheetSelect = true;
                openSheetPicker();
                return;
            }
            exportCurrentInvoice();
        });
    }

    if (exportErpBtn) {
        exportErpBtn.addEventListener('click', () => {
            closeExportMenu();
            exportDestination = 'erp';
            updateSavingDestination();
            exportStatus.textContent = 'ERP export is coming soon.';
        });
    }

    if (savingDestinationClear) {
        savingDestinationClear.addEventListener('click', () => {
            exportDestination = '';
            currentSheetId = null;
            currentSheetLabel = null;
            updateSavingDestination();
        });
    }

    if (requestEditSend) {
        requestEditSend.addEventListener('click', () => {
            submitRequestEdit();
        });
    }

    if (reviewerAddBtn) {
        reviewerAddBtn.addEventListener('click', async () => {
            if (!currentSubmissionId || !reviewerAddSelect) return;
            const reviewerId = reviewerAddSelect.value;
            if (!reviewerId) {
                if (reviewerAddStatus) reviewerAddStatus.textContent = 'Select an admin to add.';
                return;
            }
            if (reviewerAddStatus) reviewerAddStatus.textContent = 'Adding reviewer...';
            reviewerAddBtn.disabled = true;
            try {
                const response = await fetch('/invoices/submissions/reviewers/add', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        submission_id: currentSubmissionId,
                        reviewer_id: reviewerId,
                    }),
                });
                const result = await response.json();
                if (!response.ok) {
                    if (reviewerAddStatus) {
                        reviewerAddStatus.textContent = result.error || 'Failed to add reviewer.';
                    }
                    return;
                }
                if (reviewerAddStatus) reviewerAddStatus.textContent = 'Reviewer added.';
                await openSubmissionFromNotification(currentSubmissionId);
            } catch (error) {
                if (reviewerAddStatus) reviewerAddStatus.textContent = 'Failed to add reviewer.';
            } finally {
                reviewerAddBtn.disabled = false;
            }
        });
    }

    if (ocrEmptyClose) {
        ocrEmptyClose.addEventListener('click', () => closeOcrEmptyModal());
    }
    if (ocrEmptyOk) {
        ocrEmptyOk.addEventListener('click', () => closeOcrEmptyModal());
    }
    if (ocrEmptyModal) {
        ocrEmptyModal.addEventListener('click', (e) => {
            if (e.target === ocrEmptyModal) {
                closeOcrEmptyModal();
            }
        });
    }

    if (deleteSubmissionBtn) {
        deleteSubmissionBtn.addEventListener('click', () => {
            deleteSubmission();
        });
    }

    if (closeInvoiceBtn) {
        closeInvoiceBtn.addEventListener('click', () => {
            clearInvoiceView();
        });
    }

    async function fetchAccessToken() {
        const response = await fetch('/auth/google/token/');
        let data = {};
        try {
            data = await response.json();
        } catch (error) {
            data = {};
        }
        if (!response.ok) {
            return { token: null, error: data.error || null };
        }
        return { token: data.access_token || null, error: data.error || null };
    }

    async function setSelectedSheet(spreadsheetId, label, rows) {
        const response = await fetch('/auth/google/sheet', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spreadsheet_id: spreadsheetId }),
        });
        const data = await response.json();
        if (!response.ok) {
            sheetStatus.textContent = 'Failed to set sheet.';
            return;
        }
        const displayLabel = data.spreadsheet_title || label || spreadsheetId;
        const displayRows = Number.isInteger(data.spreadsheet_rows) ? data.spreadsheet_rows : rows;
        currentSheetId = data.spreadsheet_id || spreadsheetId;
        currentSheetLabel = displayLabel;
        if (Number.isInteger(displayRows)) {
            sheetStatus.textContent = `Current sheet: ${displayLabel} (${displayRows} entries)`;
        } else {
            sheetStatus.textContent = `Current sheet: ${displayLabel}`;
        }
        updateSavingDestination();
        if (pendingExportAfterSheetSelect) {
            pendingExportAfterSheetSelect = false;
            exportCurrentInvoice();
        }
    }

    function pickerCallback(data) {
        if (data.action !== google.picker.Action.PICKED) return;
        const doc = data.docs && data.docs[0];
        if (!doc || !doc.id) return;
        setSelectedSheet(doc.id, doc.name, null);
    }

    async function openSheetPicker() {
        const { token, error } = await fetchAccessToken();
        if (!token) {
            sheetStatus.textContent = error || 'Connect Google to select a sheet.';
            return;
        }
        const view = new google.picker.DocsView(google.picker.ViewId.SPREADSHEETS);
        const picker = new google.picker.PickerBuilder()
            .addView(view)
            .setOAuthToken(token)
            .setDeveloperKey(googleApiKey)
            .setOrigin(window.location.origin)
            .setCallback(pickerCallback)
            .build();
        picker.setVisible(true);
    }

    // Sheet selection now happens via the Export dropdown.

    zoomOutBtn.addEventListener('click', async () => {
        if (!currentPdfDoc || isRenderingPdf) return;
        pageScale = Math.max(ZOOM_MIN, Math.round((pageScale - ZOOM_STEP) * 10) / 10);
        await renderCurrentPdf();
    });

    zoomInBtn.addEventListener('click', async () => {
        if (!currentPdfDoc || isRenderingPdf) return;
        pageScale = Math.min(ZOOM_MAX, Math.round((pageScale + ZOOM_STEP) * 10) / 10);
        await renderCurrentPdf();
    });

    pdfWrapper.addEventListener('scroll', () => {
        if (scrollRaf) return;
        scrollRaf = requestAnimationFrame(() => {
            updatePageCounter();
            scrollRaf = null;
        });
    });

    updateZoomLabel();
    setupSidebarResize();
    initSidebarCollapse();
    loadPickerApi();
    updateGoogleStatus();

    const initialOrgAction = new URLSearchParams(window.location.search).get('org_action');
    if (initialOrgAction) {
        if (initialOrgAction === 'create') {
            openOrgCreateModal();
        } else if (initialOrgAction === 'select') {
            openOrgSelectModal();
        } else if (initialOrgAction === 'info') {
            openOrgInfoModal();
        } else if (initialOrgAction === 'edit') {
            openOrgEditModal();
        }
    }
})();
