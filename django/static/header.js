(() => {
    const loginMenu = document.getElementById('login-menu');
    const loginMenuBtn = document.getElementById('login-menu-btn');
    const loginDropdown = document.getElementById('login-dropdown');
    const googleConnectBtn = document.getElementById('google-connect-btn');
    const emailLoginBtn = document.getElementById('email-login-btn');
    const orgMenu = document.getElementById('org-menu');
    const orgMenuBtn = document.getElementById('org-menu-btn');
    const orgMenuLabel = document.getElementById('org-menu-label');
    const brandOrg = document.getElementById('brand-org');
    const brandOrgName = document.getElementById('brand-org-name');
    const orgDropdown = document.getElementById('org-dropdown');
    const orgCreateToggle = document.getElementById('org-create-toggle');
    const orgSelectToggle = document.getElementById('org-select-toggle');
    const orgInfoToggle = document.getElementById('org-info-toggle');
    const orgEditToggle = document.getElementById('org-edit-toggle');
    const accountMenu = document.getElementById('account-menu');
    const accountButton = document.getElementById('account-button');
    const accountInitials = document.getElementById('account-initials');
    const accountDropdown = document.getElementById('account-dropdown');
    const accountEmail = document.getElementById('account-email');
    const googleConnectAccountBtn = document.getElementById('google-connect-account-btn');
    const notificationsInvitesHeader = document.getElementById('notifications-invites-header');
    const notificationsInvites = document.getElementById('notifications-invites');
    const notificationsCount = document.getElementById('notifications-count');
    const notificationsApprovalsHeader = document.getElementById('notifications-approvals-header');
    const notificationsApprovals = document.getElementById('notifications-approvals');
    const notificationsEmpty = document.getElementById('notifications-empty');
    const googlePermissionNote = document.getElementById('google-permission-note');
    const googleDisconnectBtn = document.getElementById('google-disconnect-btn');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIconLight = document.getElementById('theme-icon-light');
    const themeIconDark = document.getElementById('theme-icon-dark');

    if (!loginMenu || !accountMenu) return;

    function updateGoogleConnectLinks() {
        const nextUrl = window.location.pathname + window.location.search;
        const connectUrl = `/auth/google/?next=${encodeURIComponent(nextUrl)}`;
        if (googleConnectBtn) googleConnectBtn.setAttribute('href', connectUrl);
        if (googleConnectAccountBtn) googleConnectAccountBtn.setAttribute('href', connectUrl);
    }

    let pendingInviteCount = 0;
    let pendingInvoiceCount = 0;
    let invoiceMode = null;
    let isAuthenticated = false;
    const STORAGE_KEY = 'invoice_ai_notifications_total';
    const ORG_STORAGE_KEY = 'invoice_ai_org_menu';
    const THEME_STORAGE_KEY = 'invoice_ai_theme_pref';
    let themePreference = 'system';
    const systemMedia =
        typeof window !== 'undefined' && window.matchMedia
            ? window.matchMedia('(prefers-color-scheme: dark)')
            : null;

    function getInitials(givenName, familyName, name, email) {
        if (givenName && familyName) {
            return (givenName[0] + familyName[0]).toUpperCase();
        }
        if (name && typeof name === 'string') {
            const parts = name.trim().split(/\s+/).filter(Boolean);
            if (parts.length >= 2) {
                return (parts[0][0] + parts[1][0]).toUpperCase();
            }
            if (parts.length === 1) {
                return parts[0].slice(0, 2).toUpperCase();
            }
        }
        if (email && typeof email === 'string') {
            const handle = email.split('@')[0] || '';
            const parts = handle.split(/[._-]+/).filter(Boolean);
            if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase();
            if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
        }
        return '';
    }

    function normalizeTheme(value) {
        if (value === 'light' || value === 'dark' || value === 'system') return value;
        return 'system';
    }

    function resolveTheme(preference) {
        if (preference !== 'system') return preference;
        return systemMedia && systemMedia.matches ? 'dark' : 'light';
    }

    function updateThemeToggle(preference, resolved) {
        if (!themeToggle) return;
        const label = `Theme: ${resolved[0].toUpperCase()}${resolved.slice(1)}`;
        themeToggle.setAttribute('aria-label', label);
        themeToggle.setAttribute('title', label);
        if (themeIconLight) themeIconLight.classList.toggle('hidden', resolved !== 'light');
        if (themeIconDark) themeIconDark.classList.toggle('hidden', resolved !== 'dark');
    }

    function applyThemePreference(preference, { persistLocal = true } = {}) {
        themePreference = normalizeTheme(preference);
        const resolved = resolveTheme(themePreference);
        const root = document.documentElement;
        if (root) {
            root.dataset.theme = resolved;
            root.dataset.themePref = themePreference;
        }
        if (document.body) {
            document.body.dataset.theme = resolved;
            document.body.dataset.themePref = themePreference;
        }
        updateThemeToggle(themePreference, resolved);
        if (persistLocal) {
            try {
                localStorage.setItem(THEME_STORAGE_KEY, themePreference);
            } catch (error) {
                // Ignore storage errors
            }
        }
    }

    function loadStoredTheme() {
        try {
            return normalizeTheme(localStorage.getItem(THEME_STORAGE_KEY));
        } catch (error) {
            return 'system';
        }
    }

    async function saveThemePreference(preference) {
        if (!isAuthenticated) return;
        try {
            await fetch('/auth/theme/', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ theme: preference }),
            });
        } catch (error) {
            // Ignore theme save errors
        }
    }

    function setBrandOrgName(name) {
        if (!brandOrg || !brandOrgName) return;
        const value = name || '';
        brandOrgName.textContent = value;
        brandOrg.classList.toggle('hidden', !value);
    }

    function closeDropdown(dropdown) {
        if (dropdown) dropdown.classList.add('hidden');
    }

    function toggleDropdown(dropdown) {
        if (dropdown) dropdown.classList.toggle('hidden');
    }

    function closeAllDropdowns() {
        closeDropdown(loginDropdown);
        closeDropdown(orgDropdown);
        closeDropdown(accountDropdown);
    }

    if (loginMenuBtn) {
        loginMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(loginDropdown);
            closeDropdown(orgDropdown);
            closeDropdown(accountDropdown);
        });
    }

    if (orgMenuBtn) {
        orgMenuBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            closeDropdown(loginDropdown);
            closeDropdown(accountDropdown);
            closeDropdown(orgDropdown);
            if (window.InvoiceAIHeader && window.InvoiceAIHeader.openOrgInfoModal) {
                window.InvoiceAIHeader.openOrgInfoModal();
                return;
            }
            const evt = new CustomEvent('org-info-open', { cancelable: true });
            document.dispatchEvent(evt);
            if (evt.defaultPrevented) return;
            if (orgInfoToggle) {
                orgInfoToggle.click();
                return;
            }
            openOrgInfoFallback();
        });
    }

    function routeOrgAction(action, modalId) {
        if (document.getElementById(modalId)) return;
        window.location.href = `/app/?org_action=${encodeURIComponent(action)}`;
    }

    function getOrCreateOrgInfoModal() {
        let modal = document.getElementById('org-info-modal');
        if (modal) return modal;
        modal = document.createElement('div');
        modal.id = 'org-info-modal';
        modal.className = 'hidden fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 backdrop-blur-sm';
        modal.innerHTML = `
            <div class="w-full max-w-md rounded-2xl bg-white shadow-2xl border border-slate-200 p-4">
                <div class="flex items-center justify-between mb-3">
                    <h3 class="text-sm font-semibold text-slate-700">Organization info</h3>
                    <button id="org-info-close" class="text-slate-400 hover:text-slate-600">✕</button>
                </div>
                <div id="org-info-content" class="space-y-3 text-sm text-slate-600">
                    <div class="text-xs text-slate-400">Loading...</div>
                </div>
                <div class="mt-4 space-y-2">
                    <button id="org-info-select" class="btn btn-outline w-full">Select another organization</button>
                    <button id="org-info-create" class="btn btn-outline w-full">Create new organization</button>
                    <button id="org-info-edit" class="btn btn-outline w-full">Edit organization</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        const closeBtn = modal.querySelector('#org-info-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
        }
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                modal.classList.add('hidden');
            }
        });
        const selectBtn = modal.querySelector('#org-info-select');
        if (selectBtn) {
            selectBtn.addEventListener('click', () => routeOrgAction('select', 'org-select-modal'));
        }
        const createBtn = modal.querySelector('#org-info-create');
        if (createBtn) {
            createBtn.addEventListener('click', () => routeOrgAction('create', 'org-create-modal'));
        }
        const editBtn = modal.querySelector('#org-info-edit');
        if (editBtn) {
            editBtn.addEventListener('click', () => routeOrgAction('edit', 'org-edit-modal'));
        }
        return modal;
    }

    async function openOrgInfoFallback() {
        const modal = getOrCreateOrgInfoModal();
        const content = modal.querySelector('#org-info-content');
        modal.classList.remove('hidden');
        if (content) {
            content.innerHTML = '<div class="text-xs text-slate-400">Loading...</div>';
        }
        try {
            const response = await fetch('/orgs/info');
            if (!response.ok) {
                if (content) {
                    content.innerHTML = '<div class="text-xs text-slate-500">Unable to load org info.</div>';
                }
                return;
            }
            const data = await response.json();
            if (!data || !data.id) {
                if (content) {
                    content.innerHTML = '<div class="text-xs text-slate-500">No active organization.</div>';
                }
                const editBtn = modal.querySelector('#org-info-edit');
                if (editBtn) editBtn.classList.add('hidden');
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
            if (content) {
                content.innerHTML = `
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
            }
            const editBtn = modal.querySelector('#org-info-edit');
            if (editBtn) {
                editBtn.classList.toggle('hidden', data.role !== 'admin');
            }
        } catch (error) {
            if (content) {
                content.innerHTML = '<div class="text-xs text-slate-500">Unable to load org info.</div>';
            }
        }
    }

    if (orgCreateToggle) {
        orgCreateToggle.addEventListener('click', () => {
            routeOrgAction('create', 'org-create-modal');
        });
    }

    if (orgSelectToggle) {
        orgSelectToggle.addEventListener('click', () => {
            routeOrgAction('select', 'org-select-modal');
        });
    }

    if (orgInfoToggle) {
        orgInfoToggle.addEventListener('click', () => {
            routeOrgAction('info', 'org-info-modal');
        });
    }

    if (orgEditToggle) {
        orgEditToggle.addEventListener('click', () => {
            routeOrgAction('edit', 'org-edit-modal');
        });
    }

    if (accountButton) {
        accountButton.addEventListener('click', (e) => {
            e.stopPropagation();
            toggleDropdown(accountDropdown);
            closeDropdown(loginDropdown);
            closeDropdown(orgDropdown);
            if (accountDropdown && !accountDropdown.classList.contains('hidden')) {
                loadNotifications(true);
            }
        });
    }

    if (loginDropdown) {
        loginDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    if (orgDropdown) {
        orgDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    if (accountDropdown) {
        accountDropdown.addEventListener('click', (e) => {
            e.stopPropagation();
        });
    }

    if (googleDisconnectBtn) {
        googleDisconnectBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/auth/google/disconnect/', { method: 'POST' });
                if (!response.ok) return;
                if (accountDropdown) accountDropdown.classList.add('hidden');
                updateHeaderStatus();
            } catch (error) {
                // Ignore disconnect errors in UI
            }
        });
    }

    if (notificationsInvites || notificationsApprovals) {
        const container = notificationsInvites?.parentElement || notificationsApprovals?.parentElement;
        if (container) {
            container.addEventListener('click', (e) => {
                e.stopPropagation();
            });
        }
    }

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const resolved = resolveTheme(themePreference);
            const next = resolved === 'dark' ? 'light' : 'dark';
            applyThemePreference(next);
            saveThemePreference(next);
        });
    }

    if (systemMedia && systemMedia.addEventListener) {
        systemMedia.addEventListener('change', () => {
            if (themePreference === 'system') {
                applyThemePreference('system', { persistLocal: false });
            }
        });
    }

    document.addEventListener('click', () => {
        closeAllDropdowns();
    });

    function formatShortDate(value) {
        if (!value) return '';
        const date = new Date(value);
        if (Number.isNaN(date.getTime())) return value;
        return date.toLocaleString();
    }

    function setBadgeCount(total) {
        if (!notificationsCount) return;
        if (!Number.isFinite(total) || total <= 0) {
            notificationsCount.classList.add('hidden');
            notificationsCount.textContent = '0';
            return;
        }
        notificationsCount.classList.remove('hidden');
        notificationsCount.textContent = total > 9 ? '9+' : String(total);
    }

    function updateNotificationsBadge() {
        const total = pendingInviteCount + pendingInvoiceCount;
        setBadgeCount(total);
    }

    function updateNotificationsEmpty() {
        if (!notificationsEmpty) return;
        const total = pendingInviteCount + pendingInvoiceCount;
        notificationsEmpty.classList.toggle('hidden', total > 0);
    }

    function seedBadgeFromStorage() {
        try {
            const stored = Number(localStorage.getItem(STORAGE_KEY));
            if (Number.isFinite(stored) && stored > 0) {
                setBadgeCount(stored);
            }
        } catch (error) {
            // Ignore storage errors
        }
    }

    async function handleInviteAction(inviteId, accept) {
        const endpoint = accept ? '/orgs/invites/accept' : '/orgs/invites/decline';
        try {
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ invite_id: inviteId }),
            });
            if (!response.ok) return;
            await loadNotifications(true);
            await loadOrgMenu();
        } catch (error) {
            // Ignore invite errors
        }
    }

    function renderInvites(invites) {
        if (!notificationsInvites) return;
        notificationsInvites.innerHTML = '';
        if (!invites.length) {
            notificationsInvites.classList.add('hidden');
            if (notificationsInvitesHeader) notificationsInvitesHeader.classList.add('hidden');
            updateNotificationsEmpty();
            return;
        }
        notificationsInvites.classList.remove('hidden');
        if (notificationsInvitesHeader) notificationsInvitesHeader.classList.remove('hidden');
        invites.forEach((invite) => {
            const row = document.createElement('div');
            row.className = 'rounded-lg border border-slate-200 bg-slate-50/60 p-2 space-y-2';

            const title = document.createElement('div');
            title.className = 'text-sm font-semibold text-slate-700';
            title.textContent = invite.org_name || 'Organization';

            const meta = document.createElement('div');
            meta.className = 'text-xs text-slate-500';
            meta.textContent = invite.invited_by ? `Invited by ${invite.invited_by}` : 'Invitation received';

            const actions = document.createElement('div');
            actions.className = 'flex gap-2';

            const acceptBtn = document.createElement('button');
            acceptBtn.type = 'button';
            acceptBtn.className =
                'flex-1 px-2 py-1 text-xs font-medium rounded-md border border-slate-200 bg-white hover:bg-slate-100';
            acceptBtn.textContent = 'Accept';
            acceptBtn.addEventListener('click', () => handleInviteAction(invite.id, true));

            const declineBtn = document.createElement('button');
            declineBtn.type = 'button';
            declineBtn.className =
                'flex-1 px-2 py-1 text-xs font-medium rounded-md border border-slate-200 bg-white hover:bg-slate-100';
            declineBtn.textContent = 'Decline';
            declineBtn.addEventListener('click', () => handleInviteAction(invite.id, false));

            actions.appendChild(acceptBtn);
            actions.appendChild(declineBtn);
            row.appendChild(title);
            row.appendChild(meta);
            row.appendChild(actions);
            notificationsInvites.appendChild(row);
        });
    }

    function handleInvoiceClick(id) {
        closeDropdown(accountDropdown);
        if (window.InvoiceAI && typeof window.InvoiceAI.openSubmissionFromNotification === 'function') {
            window.InvoiceAI.openSubmissionFromNotification(id);
            return;
        }
        window.location.href = `/app/?submission_id=${id}`;
    }

    function renderInvoices(items) {
        if (!notificationsApprovals) return;
        notificationsApprovals.innerHTML = '';
        if (!items.length) {
            notificationsApprovals.classList.add('hidden');
            if (notificationsApprovalsHeader) notificationsApprovalsHeader.classList.add('hidden');
            updateNotificationsEmpty();
            return;
        }
        notificationsApprovals.classList.remove('hidden');
        if (notificationsApprovalsHeader) notificationsApprovalsHeader.classList.remove('hidden');

        items.forEach((item) => {
            const row = document.createElement('button');
            row.type = 'button';
            row.className =
                'w-full text-left rounded-lg border border-slate-200 bg-white p-2 space-y-1 hover:bg-slate-50 transition-colors';
            row.addEventListener('click', () => handleInvoiceClick(item.id));

            const title = document.createElement('div');
            title.className = 'text-sm font-semibold text-slate-700';
            title.textContent = invoiceMode === 'requests' ? 'Edit requested' : 'Invoice submission';

            const meta = document.createElement('div');
            meta.className = 'text-xs text-slate-500';
            if (invoiceMode === 'requests') {
                const updatedAt = formatShortDate(item.last_comment_at || item.updated_at);
                meta.textContent = updatedAt ? `Updated ${updatedAt}` : 'Update requested';
            } else {
                const submittedBy = item.submitted_by ? `Submitted by ${item.submitted_by}` : 'Submitted';
                const createdAt = formatShortDate(item.created_at);
                meta.textContent = createdAt ? `${submittedBy} • ${createdAt}` : submittedBy;
            }

            row.appendChild(title);
            row.appendChild(meta);
            if (invoiceMode === 'requests' && item.last_comment) {
                const note = document.createElement('div');
                note.className = 'text-xs text-slate-500';
                note.textContent = item.last_comment;
                row.appendChild(note);
            }
            notificationsApprovals.appendChild(row);
        });
    }

    function applyOrgSnapshot(snapshot) {
        if (!snapshot || !orgMenu) return;
        const orgCount = Number(snapshot.orgCount) || 0;
        const hasActive = Boolean(snapshot.hasActive);
        const role = snapshot.role || null;
        const name = 'org';
        setBrandOrgName(snapshot.name);
        if (orgSelectToggle) orgSelectToggle.classList.toggle('hidden', orgCount === 0);
        if (orgInfoToggle) orgInfoToggle.classList.toggle('hidden', !hasActive);
        if (orgEditToggle) orgEditToggle.classList.toggle('hidden', role !== 'admin');
        if (orgMenuLabel) orgMenuLabel.textContent = name;
    }

    function buildOrgSnapshot(data) {
        const orgs = Array.isArray(data.organizations) ? data.organizations : [];
        const activeMembership = orgs.find((org) => org.is_active);
        const activeOrg = data.active_org || activeMembership;
        return {
            orgCount: orgs.length,
            hasActive: Boolean(activeOrg),
            role: activeOrg ? activeOrg.role : null,
            name: activeOrg && activeOrg.name ? activeOrg.name : '',
        };
    }

    function seedOrgFromStorage() {
        try {
            const raw = localStorage.getItem(ORG_STORAGE_KEY);
            if (!raw) return;
            const snapshot = JSON.parse(raw);
            applyOrgSnapshot(snapshot);
        } catch (error) {
            // Ignore storage errors
        }
    }

    function storeOrgSnapshot(snapshot) {
        try {
            localStorage.setItem(ORG_STORAGE_KEY, JSON.stringify(snapshot));
        } catch (error) {
            // Ignore storage errors
        }
    }

    async function loadOrgMenu() {
        try {
            const response = await fetch('/orgs');
            if (!response.ok) return;
            const data = await response.json();
            const snapshot = buildOrgSnapshot(data);
            applyOrgSnapshot(snapshot);
            storeOrgSnapshot(snapshot);
        } catch (error) {
            // Ignore org menu errors
        }
    }

    async function loadNotifications(renderList = false) {
        try {
            const response = await fetch('/notifications');
            if (!response.ok) return;
            const data = await response.json();
            const invites = Array.isArray(data.invites) ? data.invites : [];
            const invoices = Array.isArray(data.invoices) ? data.invoices : [];
            pendingInviteCount = invites.length;
            pendingInvoiceCount = invoices.length;
            invoiceMode = data.invoice_mode || null;
            updateNotificationsBadge();
            updateNotificationsEmpty();
            try {
                localStorage.setItem(STORAGE_KEY, String(pendingInviteCount + pendingInvoiceCount));
            } catch (error) {
                // Ignore storage errors
            }
            if (renderList) {
                renderInvites(invites);
                renderInvoices(invoices);
            }
        } catch (error) {
            // Keep existing badge on transient errors
        }
    }

    function applyAuthStatus(data) {
        isAuthenticated = Boolean(data && data.authenticated);
        const isGoogleConnected = Boolean(data && (data.google_connected ?? data.connected));
        if (isAuthenticated) {
            accountMenu.classList.remove('hidden');
            orgMenu.classList.remove('hidden');
            if (themeToggle) themeToggle.classList.remove('hidden');

            loginMenu.classList.add('hidden');
            if (googleConnectBtn) googleConnectBtn.classList.remove('hidden');
            if (emailLoginBtn) emailLoginBtn.classList.remove('hidden');
            if (googleConnectAccountBtn) {
                googleConnectAccountBtn.classList.toggle('hidden', isGoogleConnected);
            }
            if (googlePermissionNote) googlePermissionNote.classList.add('hidden');

            if (orgMenuLabel) orgMenuLabel.textContent = 'org';
            setBrandOrgName(data && data.active_org && data.active_org.name ? data.active_org.name : '');

            const email = data.google_email || '';
            if (accountEmail) accountEmail.textContent = email;

            const initials = getInitials(
                data.google_given_name,
                data.google_family_name,
                data.google_name,
                data.google_email
            );
            if (accountInitials) {
                accountInitials.textContent = initials;
            } else if (accountButton) {
                accountButton.textContent = initials;
            }

            const serverTheme = data && data.theme_preference ? data.theme_preference : 'system';
            applyThemePreference(serverTheme);
        } else {
            accountMenu.classList.add('hidden');
            orgMenu.classList.add('hidden');
            if (themeToggle) themeToggle.classList.add('hidden');
            loginMenu.classList.remove('hidden');
            if (loginMenuBtn) loginMenuBtn.textContent = 'Log in';
            if (googleConnectBtn) googleConnectBtn.classList.remove('hidden');
            if (emailLoginBtn) emailLoginBtn.classList.remove('hidden');
            if (googlePermissionNote) googlePermissionNote.classList.add('hidden');
            if (googleConnectAccountBtn) googleConnectAccountBtn.classList.add('hidden');
            if (notificationsCount) notificationsCount.classList.add('hidden');
            if (notificationsApprovalsHeader) notificationsApprovalsHeader.classList.add('hidden');
            if (notificationsApprovals) notificationsApprovals.classList.add('hidden');
            if (notificationsInvitesHeader) notificationsInvitesHeader.classList.add('hidden');
            if (notificationsInvites) notificationsInvites.classList.add('hidden');
            pendingInviteCount = 0;
            pendingInvoiceCount = 0;
            try {
                localStorage.removeItem(STORAGE_KEY);
                localStorage.removeItem(ORG_STORAGE_KEY);
                localStorage.removeItem(THEME_STORAGE_KEY);
            } catch (error) {
                // Ignore storage errors
            }
            if (orgSelectToggle) orgSelectToggle.classList.add('hidden');
            if (orgInfoToggle) orgInfoToggle.classList.add('hidden');
            if (orgEditToggle) orgEditToggle.classList.add('hidden');
            setBrandOrgName('');
            updateNotificationsEmpty();
            applyThemePreference('system', { persistLocal: false });
        }
    }

    async function updateHeaderStatus() {
        try {
            const response = await fetch('/auth/status/');
            if (!response.ok) return;
            const data = await response.json();
            applyAuthStatus(data);
            if (data && data.authenticated) {
                loadNotifications();
                loadOrgMenu();
            }
        } catch (error) {
            // Ignore status errors
        }
    }

    window.InvoiceAIHeader = {
        refresh: updateHeaderStatus,
        refreshNotifications: (renderList = false) => loadNotifications(renderList),
        refreshOrgMenu: () => loadOrgMenu(),
        applyAuthStatus,
    };

    seedBadgeFromStorage();
    seedOrgFromStorage();
    applyThemePreference(loadStoredTheme(), { persistLocal: false });
    updateGoogleConnectLinks();
    updateHeaderStatus();
})();
