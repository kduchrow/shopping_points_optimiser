function switchTab(tabName, evt) {
  document.querySelectorAll('.tab-button').forEach((btn) => btn.classList.remove('active'));
  document.querySelectorAll('.tab-content').forEach((content) => content.classList.remove('active'));

  const target = evt?.target || document.querySelector(`[data-tab="${tabName}"]`);
  if (target) target.classList.add('active');
  const tab = document.getElementById(`tab-${tabName}`);
  if (tab) tab.classList.add('active');

  if (tabName === 'merges') loadMergeProposals();
  if (tabName === 'metadata') loadMetadataProposals();
  if (tabName === 'rates') loadRatesForReview();
  if (tabName === 'notifications') loadNotifications();
  if (tabName === 'shops') loadShops();
}

function fetchNotifications() {
  return fetch('/api/notifications').then((r) => r.json());
}

function updateNotificationBadge() {
  fetchNotifications().then((data) => {
    const badge = document.getElementById('unread-badge');
    if (!badge) return;
    const unread = data.notifications.filter((n) => !n.is_read).length;
    if (unread > 0) {
      badge.textContent = unread;
      badge.style.display = 'inline-block';
    } else {
      badge.style.display = 'none';
    }
  });
}

function loadNotifications() {
  fetchNotifications().then((data) => {
    const list = document.getElementById('notifications-list');
    if (!list) return;
    list.innerHTML = '';

    if (!data.notifications.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No notifications</p></div>';
      return;
    }

    data.notifications.forEach((n) => {
      const li = document.createElement('li');
      li.className = `notification-item${n.is_read ? '' : ' unread'}`;
      li.onclick = () => markAsRead(n.id);
      const time = new Date(n.created_at).toLocaleString();
      li.innerHTML = `
        <div class="notification-title">${n.title}</div>
        <div class="notification-message">${n.message}</div>
        <div class="notification-time">${time}</div>
      `;
      list.appendChild(li);
    });

    updateNotificationBadge();
  });
}

function markAsRead(notificationId) {
  fetch(`/api/notifications/${notificationId}/read`, { method: 'POST' }).then(() => loadNotifications());
}

function markAllAsRead() {
  fetch('/api/notifications/read_all', { method: 'POST' }).then(() => loadNotifications());
}

function loadMergeProposals() {
  fetch('/admin/shops/merge_proposals')
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById('merge-proposals-list');
      if (!list) return;
      list.innerHTML = '';

      if (!data.proposals.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✅</div><p>No pending merge proposals</p></div>';
        return;
      }

      data.proposals.forEach((p) => {
        const div = document.createElement('div');
        div.className = 'proposal-item';
        div.innerHTML = `
          <div class="proposal-header">
            <span>Proposed by: <strong>${p.proposed_by}</strong></span>
            <span style="font-size: 12px; color: #999;">${new Date(p.created_at).toLocaleString()}</span>
          </div>
          <div class="proposal-shops">
            <div class="shop-badge">${p.variant_a.source}: ${p.variant_a.name}</div>
            <span class="merge-arrow">→</span>
            <div class="shop-badge">${p.variant_b.source}: ${p.variant_b.name}</div>
          </div>
          <div style="margin: 10px 0; font-size: 13px; color: #666;"><strong>Reason:</strong> ${p.reason || 'No reason provided'}</div>
          <div>
            <button class="btn btn-success" onclick="approveMerge(${p.id})">✓ Approve</button>
            <button class="btn btn-danger" onclick="rejectMerge(${p.id})">✗ Reject</button>
          </div>
        `;
        list.appendChild(div);
      });
    });
}

function approveMerge(proposalId) {
  if (!confirm('Are you sure you want to approve this merge?')) return;

  fetch(`/admin/shops/merge_proposal/${proposalId}/approve`, { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert('Merge approved successfully!');
        loadMergeProposals();
      } else {
        alert('Error: ' + data.error);
      }
    });
}

function rejectMerge(proposalId) {
  const reason = prompt('Reason for rejection:');
  if (!reason) return;

  fetch(`/admin/shops/merge_proposal/${proposalId}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert('Merge rejected');
        loadMergeProposals();
      } else {
        alert('Error: ' + data.error);
      }
    });
}

function loadMetadataProposals() {
  fetch('/admin/shops/metadata_proposals')
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById('metadata-proposals-list');
      if (!list) return;
      list.innerHTML = '';

      if (!data.proposals || !data.proposals.length) {
        list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">✅</div><p>Keine offenen Metadaten-Anträge</p></div>';
        return;
      }

      data.proposals.forEach((p) => {
        const div = document.createElement('div');
        div.className = 'proposal-item';
        const created = new Date(p.created_at).toLocaleString();
        div.innerHTML = `
          <div class="proposal-header">
            <span>ShopMain: <strong>${p.shop_main_id}</strong></span>
            <span style="font-size: 12px; color: #999;">${created}</span>
          </div>
          <div style="margin: 8px 0; font-size: 13px; color: #333;">
            ${p.proposed_name ? `<div><strong>Name:</strong> ${p.proposed_name}</div>` : ''}
            ${p.proposed_website ? `<div><strong>Website:</strong> ${p.proposed_website}</div>` : ''}
            ${p.proposed_logo_url ? `<div><strong>Logo:</strong> ${p.proposed_logo_url}</div>` : ''}
            ${p.reason ? `<div style="margin-top:6px;"><strong>Begründung:</strong> ${p.reason}</div>` : ''}
          </div>
          <div>
            <button class="btn btn-success" onclick="approveMetadata(${p.id})">✓ Freigeben</button>
            <button class="btn btn-danger" onclick="rejectMetadata(${p.id})">✗ Ablehnen</button>
            <button class="btn btn-warning" onclick="deleteMetadata(${p.id})">🗑 Löschen</button>
          </div>
        `;
        list.appendChild(div);
      });
    });
}

function approveMetadata(id) {
  if (!confirm('Metadaten-Antrag freigeben?')) return;
  fetch(`/admin/shops/metadata_proposals/${id}/approve`, { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert('Freigegeben');
        loadMetadataProposals();
      } else {
        alert('Fehler: ' + data.error);
      }
    });
}

function rejectMetadata(id) {
  const reason = prompt('Grund für Ablehnung:');
  if (reason === null) return;
  fetch(`/admin/shops/metadata_proposals/${id}/reject`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert('Abgelehnt');
        loadMetadataProposals();
      } else {
        alert('Fehler: ' + data.error);
      }
    });
}

function deleteMetadata(id) {
  if (!confirm('Diesen Antrag wirklich löschen?')) return;
  fetch(`/admin/shops/metadata_proposals/${id}/delete`, { method: 'POST' })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert('Gelöscht');
        loadMetadataProposals();
      } else {
        alert('Fehler: ' + data.error);
      }
    });
}

function loadRatesForReview() {
  const list = document.getElementById('rates-list');
  if (!list) return;
  list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">⭐</div><p>Rate review coming soon...</p></div>';
}

function wireScraperForms() {
  const milesForm = document.getElementById('miles-and-more-form');
  const paybackForm = document.getElementById('payback-form');

  if (milesForm) {
    milesForm.addEventListener('submit', (e) => {
      e.preventDefault();
      fetch('/admin/run_miles_and_more', { method: 'POST', headers: { Accept: 'application/json' } })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert('Error starting Miles & More scraper: ' + err));
    });
  }

  if (paybackForm) {
    paybackForm.addEventListener('submit', (e) => {
      e.preventDefault();
      fetch('/admin/run_payback', { method: 'POST', headers: { Accept: 'application/json' } })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert('Error starting Payback scraper: ' + err));
    });
  }
}

let jobId = null;
let pollInterval = null;

function startJobMonitoring(id) {
  jobId = id;
  const progress = document.getElementById('job-progress');
  if (progress) progress.classList.add('active');
  pollInterval = setInterval(updateJobStatus, 500);
  updateJobStatus();
}

function updateJobStatus() {
  if (!jobId) return;

  fetch(`/admin/job_status/${jobId}`)
    .then((r) => r.json())
    .then((data) => {
      const statusEl = document.getElementById('job-status');
      const progressFill = document.getElementById('progress-fill');
      if (statusEl) {
        statusEl.textContent = data.status.toUpperCase();
        statusEl.className = `job-status ${data.status}`;
      }
      if (progressFill) {
        progressFill.style.width = `${data.progress_percent}%`;
        progressFill.textContent = `${data.progress_percent}%`;
      }

      const messagesDiv = document.getElementById('job-messages');
      if (messagesDiv) {
        messagesDiv.innerHTML = '';
        (data.messages || []).slice(-50).forEach((msg) => {
          const msgEl = document.createElement('div');
          msgEl.textContent = `[${msg.timestamp.substr(11, 8)}] ${msg.message}`;
          messagesDiv.appendChild(msgEl);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      }

      if (data.status === 'completed' || data.status === 'failed') {
        clearInterval(pollInterval);
        if (data.status === 'completed') {
          setTimeout(() => window.location.reload(), 2000);
        }
      }
    });
}

function renderShopList(data) {
  const container = document.getElementById('shop-list');
  if (!container) return;
  if (!data.shops || data.shops.length === 0) {
    container.innerHTML = '<div class="empty-state"><div class="empty-state-icon">🛒</div><p>Keine Shops gefunden.</p></div>';
    return;
  }

  const rows = data.shops
    .map((shop) => {
      const variants = shop.variants.map((v) => `${v.source}: ${v.name} (conf ${Math.round(v.confidence)}%)`).join('<br>');
      const rates = shop.rates
        .map((r) => `${r.program}: ${r.points_per_eur} P/EUR${r.cashback_pct ? `, ${r.cashback_pct}% CB` : ''}`)
        .join('<br>');
      return `
        <div style="border-bottom:1px solid #eee; padding:10px 0;">
          <div style="font-weight:600;">${shop.name}</div>
          <div style="color:#666;">${shop.status}${shop.website ? ' • ' + shop.website : ''}</div>
          <div style="margin-top:6px;"><strong>Varianten:</strong><br>${variants || '—'}</div>
          <div style="margin-top:6px;"><strong>Raten:</strong><br>${rates || '—'}</div>
        </div>
      `;
    })
    .join('');
  container.innerHTML = rows;
}

function loadShops() {
  const searchInput = document.getElementById('shop-search');
  const q = searchInput?.value || '';
  fetch(`/admin/shops_overview?q=${encodeURIComponent(q)}`)
    .then((r) => r.json())
    .then((data) => renderShopList(data));
}

function wireShopSearch() {
  const input = document.getElementById('shop-search');
  if (!input) return;
  input.addEventListener('input', () => {
    clearTimeout(window._shopSearchTimer);
    window._shopSearchTimer = setTimeout(loadShops, 250);
  });
}

function initAdminPage() {
  updateNotificationBadge();
  setInterval(updateNotificationBadge, 30000);
  wireScraperForms();
  wireShopSearch();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initAdminPage);
} else {
  initAdminPage();
}
