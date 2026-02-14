function switchTab(tabName, evt) {
  document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"));

  const target = evt?.target || document.querySelector(`[data-tab='${tabName}']`);
  if (target) target.classList.add("active");
  const tab = document.getElementById(tabName);
  if (tab) {
    tab.classList.add("active");
  } else {
    // fallback: activate first tab-content if not found
    const firstTab = document.querySelector(".tab-content");
    if (firstTab) firstTab.classList.add("active");
  }

  if (tabName === "tab-merges") loadMergeProposals();
  if (tabName === "tab-metadata") loadMetadataProposals();
  if (tabName === "tab-rates") loadRatesForReview();
  if (tabName === "tab-notifications") loadNotifications();
  if (tabName === "tab-shops") loadShops();
  if (tabName === "tab-users") loadUsers();
  if (tabName === "tab-scheduled-jobs") loadScheduledJobs();
}

function loadScheduledJobs() {
  const container = document.getElementById("scheduled-jobs-dynamic");
  if (!container) return;
  container.innerHTML = `<div class='admin-card'><h3 class='mt-18'>Scheduled Jobs</h3><div>Loading...</div></div>`;
  fetch("/admin/scheduled_jobs?json=1")
    .then((r) => r.json())
    .then((data) => renderScheduledJobs(data.jobs))
    .catch((err) => {
      container.innerHTML = `<div class='admin-card'><h3 class='mt-18'>Scheduled Jobs</h3><div class='empty-state'><p>Fehler beim Laden der Jobs: ${err}</p></div></div>`;
    });
}

function renderScheduledJobs(jobs) {
  const container = document.getElementById("scheduled-jobs-dynamic");
  if (!container) return;
  let html = `<div class='admin-card'>`;
  html += `<h2 class='section-title'>Scheduled Jobs</h2>`;
  html += `<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;'>`;
  html += `<a class='btn btn-success' href='/admin/scheduled_jobs/create'>➕ Neuen Job hinzufügen</a>`;
  html += `</div>`;
  if (!jobs || jobs.length === 0) {
    html += `<div class='empty-state'><p>Keine Scheduled Jobs vorhanden.</p></div>`;
  } else {
    html += `<table class='admin-table'><thead><tr><th>ID</th><th>Name</th><th>Typ</th><th>Cron</th><th>Status</th><th>Letzter Lauf</th><th>Ergebnis</th><th>Aktionen</th></tr></thead><tbody>`;
    jobs.forEach((job) => {
      html += `<tr>`;
      html += `<td><strong>${job.id}</strong></td>`;
      html += `<td>${job.job_name || "—"}</td>`;
      html += `<td>${job.job_type || "—"}</td>`;
      html += `<td><code>${job.cron_expression || "—"}</code></td>`;
      html += `<td>${
        job.enabled
          ? "<span class='job-enabled'>✅ Aktiviert</span>"
          : "<span class='job-disabled'>⏸️ Deaktiviert</span>"
      }</td>`;
      html += `<td>${job.last_run_at || "<span class='text-muted'>Noch nicht ausgeführt</span>"}</td>`;
      html += `<td>`;
      if (job.last_run_status === "success") html += `<span class='status-success'>✅ Erfolgreich</span>`;
      else if (job.last_run_status === "failed") html += `<span class='status-failed'>❌ Fehlgeschlagen</span>`;
      else if (job.last_run_status === "queued") html += `<span class='status-queued'>⏳ In Warteschlange</span>`;
      else html += `<span class='text-muted'>—</span>`;
      if (job.last_run_message) html += `<br /><small class='text-muted'>${job.last_run_message}</small>`;
      html += `</td>`;
      html += `<td><div class='btn-group' style='display:flex;gap:6px;flex-wrap:wrap;'>`;
      html += `<a href='/admin/scheduled_jobs/${job.id}/edit' class='btn btn-sm btn-primary' title='Bearbeiten'>✏️</a> `;
      html += `<button class='btn btn-sm btn-success' title='Jetzt ausführen' onclick='runScheduledJob(${job.id})'>▶️</button> `;
      html += `<button class='btn btn-sm btn-danger' title='Entfernen' onclick='deleteScheduledJob(${job.id})'>🗑️</button> `;
      html += `<button class='btn btn-sm btn-secondary' title='Logs anzeigen' onclick='showJobLogs(${job.id})'>📜</button>`;
      html += `</div></td>`;
      html += `</tr>`;
    });
    html += `</tbody></table>`;
  }
  html += `</div>`;
  container.innerHTML = html;
}

function runScheduledJob(jobId) {
  if (!confirm("Diesen Job jetzt ausführen?")) return;
  fetch(`/admin/scheduled_jobs/${jobId}/run`, {
    method: "POST",
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("✅ Job wurde gestartet!");
        loadScheduledJobs();
      } else {
        alert("❌ Fehler: " + (data.error || "Unbekannter Fehler"));
      }
    })
    .catch((err) => alert("❌ Fehler: " + err));
}

function deleteScheduledJob(jobId) {
  if (!confirm("Diesen Job wirklich löschen?")) return;
  fetch(`/admin/scheduled_jobs/${jobId}/delete`, {
    method: "POST",
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("✅ Job wurde gelöscht!");
        loadScheduledJobs();
      } else {
        alert("❌ Fehler: " + (data.error || "Unbekannter Fehler"));
      }
    })
    .catch((err) => alert("❌ Fehler: " + err));
}

function showJobLogs(jobId) {
  fetch(`/admin/scheduled_jobs/${jobId}/logs?json=1`, {
    method: "GET",
    headers: { Accept: "application/json" },
    credentials: "same-origin",
  })
    .then((r) => {
      if (!r.ok) {
        throw new Error(`HTTP ${r.status}: ${r.statusText}`);
      }
      return r.json();
    })
    .then((data) => {
      if (data.logs && data.logs.length > 0) {
        const logs = data.logs.map((log) => `[${log.timestamp}] ${log.message}`).join("\n");
        alert("Job Logs:\n\n" + logs);
      } else {
        alert("Keine Logs vorhanden für diesen Job.");
      }
    })
    .catch((err) => alert("❌ Fehler beim Laden der Logs: " + err.message));
}

// Dynamically load users for Users tab
function loadUsers() {
  fetch("/admin/users?json=1")
    .then((r) => r.json())
    .then((data) => renderUserTable(data.users))
    .catch((err) => {
      const tab = document.getElementById("tab-users");
      if (tab) tab.innerHTML = `<div class='empty-state'><p>Fehler beim Laden der User: ${err}</p></div>`;
    });
}

function renderUserTable(users) {
  const tab = document.getElementById("tab-users");
  if (!tab) return;
  let html = `<div class='admin-card'><h3>👥 User-Verwaltung</h3>`;
  html += `<h4>Alle registrierten User (${users.length})</h4>`;
  if (users.length > 0) {
    html += `<table class='user-table'><thead><tr><th>ID</th><th>Username</th><th>Email</th><th>Rolle</th><th>Status</th><th>Registriert</th><th>Aktionen</th></tr></thead><tbody>`;
    users.forEach((user) => {
      html += `<tr>`;
      html += `<td>${user.id}</td>`;
      html += `<td><strong>${user.username}</strong></td>`;
      html += `<td>${user.email}</td>`;
      html += `<td><span class='role-badge role-${user.role}'>${user.role}</span></td>`;
      html += `<td><span class='status-badge status-${user.status}'>${user.status}</span></td>`;
      html += `<td>${user.created_at ? new Date(user.created_at).toLocaleDateString() : ""}</td>`;
      html += `<td>`;
      html += `<form action='/admin/users/${user.id}/update_role' method='POST' class='action-form user-role-form' data-user-id='${user.id}'>`;
      html += `<select name='role' class='role-select'>`;
      html += `<option value=''>Rolle ändern...</option>`;
      ["viewer", "user", "contributor", "moderator", "admin"].forEach((role) => {
        html += `<option value='${role}'${user.role === role ? " disabled" : ""}>${
          role.charAt(0).toUpperCase() + role.slice(1)
        }</option>`;
      });
      html += `</select></form>`;
      // Wire up AJAX role change after rendering
      setTimeout(() => {
        document.querySelectorAll(".user-role-form .role-select").forEach((select) => {
          select.addEventListener("change", function (e) {
            const form = this.closest("form");
            const userId = form.getAttribute("data-user-id");
            const newRole = this.value;
            if (!newRole) return;
            fetch(`/admin/users/${userId}/update_role`, {
              method: "POST",
              headers: { "Content-Type": "application/x-www-form-urlencoded", Accept: "application/json" },
              body: `role=${encodeURIComponent(newRole)}`,
            })
              .then((r) => (r.ok ? r.json() : r.text()))
              .then(() => loadUsers())
              .catch(() => loadUsers());
          });
        });
      }, 50);
      html += `<form action='/admin/users/${user.id}/toggle_status' method='POST' class='action-form' onsubmit='return confirm("Status von ${user.username} wirklich ändern?");'>`;
      if (user.status === "active") {
        html += `<button type='submit' class='btn btn-sm btn-warning'>🔒 Deaktivieren</button>`;
      } else {
        html += `<button type='submit' class='btn btn-sm btn-success'>✅ Aktivieren</button>`;
      }
      html += `</form>`;
      html += `</td></tr>`;
    });
    html += `</tbody></table>`;
  } else {
    html += `<div class='empty-state'><p>Keine User gefunden.</p></div>`;
  }
  html += `<h4 class='mt-30'>ℹ️ Rollen-Erklärung</h4><ul class='line-height-1-8 pl-20'><li><strong>Viewer:</strong> Kann nur öffentliche Inhalte sehen</li><li><strong>User:</strong> Kann Proposals erstellen</li><li><strong>Contributor:</strong> Kann Proposals erstellen und über Proposals abstimmen</li><li><strong>Moderator:</strong> Kann Raten einsehen</li><li><strong>Admin:</strong> Volle Rechte (User-Verwaltung, Scrapers, Proposals direkt genehmigen)</li></ul></div>`;
  tab.innerHTML = html;
}

// Shop details modal helpers
function _ensureShopDetailsModal() {
  if (document.getElementById("shop-details-modal")) return;
  const modal = document.createElement("div");
  modal.id = "shop-details-modal";
  modal.style.display = "none";
  modal.style.position = "fixed";
  modal.style.left = "0";
  modal.style.top = "0";
  modal.style.width = "100%";
  modal.style.height = "100%";
  modal.style.background = "rgba(0,0,0,0.5)";
  modal.style.zIndex = "9999";
  modal.innerHTML = `
    <div id="shop-details-box" style="background:#fff; max-width:900px; margin:40px auto; padding:20px; border-radius:8px; overflow:auto; max-height:80%; position:relative;">
      <button style="position:absolute; right:12px; top:12px;" onclick="closeShopDetails()">✖</button>
      <h3 id="shop-details-title" style="margin-top:40px;">Shop Details</h3>
      <div id="shop-details-content" style="margin-top:50px;"></div>
    </div>
  `;
  document.body.appendChild(modal);
}

function openShopDetails(mainId) {
  _ensureShopDetailsModal();
  const modal = document.getElementById("shop-details-modal");
  const content = document.getElementById("shop-details-content");
  const title = document.getElementById("shop-details-title");
  if (!modal || !content) return;
  modal.style.display = "block";
  content.innerHTML = "<div>Loading...</div>";
  fetch(`/admin/shops/${mainId}/details`)
    .then((r) => r.json())
    .then((data) => {
      const main = data.main || data || {};
      title.textContent = main.canonical_name || `Shop ${mainId}`;
      if (!data.shops || data.shops.length === 0) {
        content.innerHTML = "<div>No linked shops or rates found.</div>";
        return;
      }
      let html = "";
      // ShopMain metadata with action buttons
      html += `<div style='margin-bottom:18px;'>`;
      html += `<strong>ShopMain Metadaten:</strong><ul style='margin:6px 0 0 18px;'>`;
      html += `<li><strong>Name:</strong> ${main.canonical_name || "—"}</li>`;
      html += `<li><strong>Status:</strong> <span style="padding: 3px 8px; border-radius: 4px; font-size: 12px; ${
        main.status === "deleted"
          ? "background: #ffcccc; color: #8b0000;"
          : main.status === "merged"
            ? "background: #fff3cd; color: #856404;"
            : "background: #d4edda; color: #155724;"
      }">${(main.status || "active").toUpperCase()}</span></li>`;
      html += `<li><strong>Website:</strong> ${
        main.website ? `<a href='${main.website}' target='_blank'>${main.website}</a>` : "—"
      }</li>`;
      if (main.logo_url)
        html += `<li><strong>Logo:</strong> <img src='${main.logo_url}' alt='Logo' style='max-height:32px;vertical-align:middle;'></li>`;
      html += `</ul>`;
      html += `<div style='margin-top:12px; display:flex; gap:8px;'>`;
      if (main.status === "deleted") {
        html += `<button class='btn btn-success' onclick="restoreShop('${mainId}')">✔️ Shop wiederherstellen</button>`;
      } else {
        html += `<button class='btn btn-danger' onclick="deleteShop('${mainId}')">🗑️ Shop löschen</button>`;
      }
      html += `</div></div>`;
      // Variants section (detailed, with all metadata and delete button)
      html += `<div style='margin-bottom:18px;'><strong>Varianten:</strong>`;
      if (main.variants && main.variants.length > 0) {
        html += `<table class='admin-table' style='margin-top:6px;'><thead><tr><th>Source</th><th>Name</th><th>Source ID</th><th>Confidence</th><th>Aktionen</th></tr></thead><tbody>`;
        main.variants.forEach((v) => {
          html += `<tr>`;
          html += `<td>${v.source}</td>`;
          html += `<td>${v.name}</td>`;
          html += `<td>${v.source_id || "—"}</td>`;
          html += `<td>${typeof v.confidence !== "undefined" ? Math.round(v.confidence) + "%" : "—"}</td>`;
          html += `<td><button class='btn btn-sm btn-danger' onclick="deleteVariant(${v.id})">🗑️</button></td>`;
          html += `</tr>`;
        });
        html += `</tbody></table>`;
      } else {
        html += `<p style='color:#888; margin:6px 0;'>Keine Varianten vorhanden.</p>`;
      }
      html += `<button class='btn btn-primary' onclick="showAddVariantForm('${mainId}')">➕ Variante hinzufügen</button></div>`;
      // Linked shops and rates
      data.shops.forEach((s) => {
        html += `<div style='margin-bottom:18px;'><h4 style='margin:6px 0 4px 0;'>${s.name}</h4>`;
        if (s.rates && s.rates.length > 0) {
          html += `<table class='admin-table' style='margin-bottom:8px;'><thead><tr><th>Programm</th><th>Typ</th><th>Kategorie</th><th>Subkategorie</th><th>Raten</th><th>Gültig von</th><th>Gültig bis</th></tr></thead><tbody>`;
          s.rates.forEach((rt) => {
            let rateParts = [];
            if (rt.points_per_eur) rateParts.push(`${rt.points_per_eur} P/EUR`);
            if (rt.points_absolute) rateParts.push(`${rt.points_absolute} P absolut`);
            if (rt.cashback_pct) rateParts.push(`${rt.cashback_pct}% CB`);
            if (rt.cashback_absolute) rateParts.push(`${rt.cashback_absolute}€ CB absolut`);
            const rateTypeLabel = rt.rate_type === "contract" ? "📝 Vertrag" : "🛒 Shop";
            html += `<tr>`;
            html += `<td>${rt.program}</td>`;
            html += `<td>${rateTypeLabel}</td>`;
            html += `<td>${rt.category || "—"}</td>`;
            html += `<td>${rt.sub_category || "—"}</td>`;
            html += `<td>${rateParts.join(", ") || "—"}</td>`;
            html += `<td>${rt.valid_from ? rt.valid_from.split("T")[0] : "—"}</td>`;
            html += `<td>${rt.valid_to ? rt.valid_to.split("T")[0] : "—"}</td>`;
            html += `</tr>`;
          });
          html += `</tbody></table>`;
        } else {
          html += `<div style='color:#888'>Keine Raten vorhanden.</div>`;
        }
        html += `</div>`;
      });
      content.innerHTML = html;
    })
    .catch((err) => {
      content.innerHTML = `<div style=\"color:red\">Error: ${err}</div>`;
    });
}

function closeShopDetails() {
  const modal = document.getElementById("shop-details-modal");
  if (modal) modal.style.display = "none";
}

function deleteShop(shopMainId) {
  if (!confirm("Diesen Shop wirklich löschen?")) return;
  fetch(`/admin/shops/${shopMainId}/delete`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Shop gelöscht");
        closeShopDetails();
        loadShops();
      } else {
        alert("Fehler: " + (data.error || "Unbekannt"));
      }
    })
    .catch((e) => alert("Fehler: " + e));
}

function restoreShop(shopMainId) {
  if (!confirm("Diesen Shop wirklich wiederherstellen?")) return;
  fetch(`/admin/shops/${shopMainId}/restore`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Shop wiederhergestellt");
        closeShopDetails();
        loadShops();
      } else {
        alert("Fehler: " + (data.error || "Unbekannt"));
      }
    })
    .catch((e) => alert("Fehler: " + e));
}

function deleteVariant(variantId) {
  if (!confirm("Diese Variante wirklich löschen?")) return;
  fetch(`/admin/variants/${variantId}/delete`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Variante gelöscht");
        // Reload shop details to reflect changes
        const modal = document.getElementById("shop-details-modal");
        const shopId = modal?.dataset?.shopMainId;
        if (shopId) {
          openShopDetails(shopId);
        } else {
          closeShopDetails();
          loadShops();
        }
      } else {
        alert("Fehler: " + (data.error || "Unbekannt"));
      }
    })
    .catch((e) => alert("Fehler: " + e));
}

function showAddVariantForm(shopMainId) {
  const form = `
    <div style="background:#f8f9fa; padding:16px; border-radius:8px; margin-top:12px;" id="add-variant-form">
      <h4 style="margin:0 0 12px 0;">Neue Variante hinzufügen</h4>
      <div style="display:grid; gap:12px;">
        <div>
          <label style="display:block; margin-bottom:4px; font-weight:600;">Source (z.B. Google, Amazon, manual):</label>
          <input type="text" id="variant-source" class="shop-search-input" placeholder="manual" value="manual" style="width:100%;" />
        </div>
        <div>
          <label style="display:block; margin-bottom:4px; font-weight:600;">Name (z.B. "1 und 1"):</label>
          <input type="text" id="variant-name" class="shop-search-input" placeholder="Shop-Varianten-Name" style="width:100%;" required />
        </div>
        <div>
          <label style="display:block; margin-bottom:4px; font-weight:600;">Source ID (optional):</label>
          <input type="text" id="variant-source-id" class="shop-search-input" placeholder="z.B. google_12345" style="width:100%;" />
        </div>
        <div>
          <label style="display:block; margin-bottom:4px; font-weight:600;">Confidence (0-100):</label>
          <input type="number" id="variant-confidence" class="shop-search-input" value="100" min="0" max="100" style="width:100%;" />
        </div>
        <div style="display:flex; gap:8px;">
          <button class="btn btn-success" onclick="addVariant('${shopMainId}')">✅ Speichern</button>
          <button class="btn btn-secondary" onclick="hideAddVariantForm()">❌ Abbrechen</button>
        </div>
      </div>
    </div>
  `;

  // Find the variants section and insert form
  const modal = document.getElementById("shop-details-content");
  if (!modal) return;

  // Remove existing form if present
  const existingForm = document.getElementById("add-variant-form");
  if (existingForm) existingForm.remove();

  // Insert form at the end of content
  modal.insertAdjacentHTML("beforeend", form);

  // Focus name input
  document.getElementById("variant-name")?.focus();
}

function hideAddVariantForm() {
  const form = document.getElementById("add-variant-form");
  if (form) form.remove();
}

function addVariant(shopMainId) {
  const source = document.getElementById("variant-source")?.value?.trim() || "manual";
  const name = document.getElementById("variant-name")?.value?.trim();
  const sourceId = document.getElementById("variant-source-id")?.value?.trim() || null;
  const confidence = parseFloat(document.getElementById("variant-confidence")?.value) || 100.0;

  if (!name) {
    alert("Bitte gib einen Namen für die Variante ein.");
    return;
  }

  fetch(`/admin/shops/${shopMainId}/variants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      source: source,
      source_name: name,
      source_id: sourceId,
      confidence_score: confidence,
    }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Variante erfolgreich hinzugefügt!");
        hideAddVariantForm();
        openShopDetails(shopMainId); // Reload details
      } else {
        alert("Fehler: " + (data.error || "Unbekannt"));
      }
    })
    .catch((e) => alert("Fehler: " + e));
}

function fetchNotifications() {
  return fetch("/api/notifications").then((r) => r.json());
}

function updateNotificationBadge() {
  fetchNotifications().then((data) => {
    const badge = document.getElementById("unread-badge");
    if (!badge) return;
    const unread = data.notifications.filter((n) => !n.is_read).length;
    if (unread > 0) {
      badge.textContent = unread;
      badge.style.display = "inline-block";
    } else {
      badge.style.display = "none";
    }
  });
}

function loadNotifications() {
  fetchNotifications().then((data) => {
    const list = document.getElementById("notifications-list");
    if (!list) return;
    list.innerHTML = "";

    if (!data.notifications.length) {
      list.innerHTML = '<div class="empty-state"><div class="empty-state-icon">📭</div><p>No notifications</p></div>';
      return;
    }

    data.notifications.forEach((n) => {
      const li = document.createElement("li");
      li.className = `notification-item${n.is_read ? "" : " unread"}`;
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
  fetch(`/api/notifications/${notificationId}/read`, { method: "POST" }).then(() => loadNotifications());
}

function markAllAsRead() {
  fetch("/api/notifications/read_all", { method: "POST" }).then(() => loadNotifications());
}

function loadMergeProposals() {
  fetch("/admin/shops/merge_proposals")
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById("merge-proposals-list");
      if (!list) return;
      list.innerHTML = "";

      if (!data.proposals.length) {
        list.innerHTML =
          '<div class="empty-state"><div class="empty-state-icon">✅</div><p>No pending merge proposals</p></div>';
        return;
      }

      data.proposals.forEach((p) => {
        const div = document.createElement("div");
        div.className = "proposal-item";
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
          <div style="margin: 10px 0; font-size: 13px; color: #666;"><strong>Reason:</strong> ${
            p.reason || "No reason provided"
          }</div>
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
  if (!confirm("Are you sure you want to approve this merge?")) return;

  fetch(`/admin/shops/merge_proposal/${proposalId}/approve`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Merge approved successfully!");
        loadMergeProposals();
      } else {
        alert("Error: " + data.error);
      }
    });
}

function rejectMerge(proposalId) {
  const reason = prompt("Reason for rejection:");
  if (!reason) return;

  fetch(`/admin/shops/merge_proposal/${proposalId}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Merge rejected");
        loadMergeProposals();
      } else {
        alert("Error: " + data.error);
      }
    });
}

function loadMetadataProposals() {
  fetch("/admin/shops/metadata_proposals")
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById("metadata-proposals-list");
      if (!list) return;
      list.innerHTML = "";

      if (!data.proposals || !data.proposals.length) {
        list.innerHTML =
          '<div class="empty-state"><div class="empty-state-icon">✅</div><p>Keine offenen Metadaten-Anträge</p></div>';
        return;
      }

      data.proposals.forEach((p) => {
        const div = document.createElement("div");
        div.className = "proposal-item";
        const created = new Date(p.created_at).toLocaleString();
        div.innerHTML = `
          <div class="proposal-header">
            <span>ShopMain: <strong>${p.shop_main_id}</strong></span>
            <span style="font-size: 12px; color: #999;">${created}</span>
          </div>
          <div style="margin: 8px 0; font-size: 13px; color: #333;">
            ${p.proposed_name ? `<div><strong>Name:</strong> ${p.proposed_name}</div>` : ""}
            ${p.proposed_website ? `<div><strong>Website:</strong> ${p.proposed_website}</div>` : ""}
            ${p.proposed_logo_url ? `<div><strong>Logo:</strong> ${p.proposed_logo_url}</div>` : ""}
            ${p.reason ? `<div style="margin-top:6px;"><strong>Begründung:</strong> ${p.reason}</div>` : ""}
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
  if (!confirm("Metadaten-Antrag freigeben?")) return;
  fetch(`/admin/shops/metadata_proposals/${id}/approve`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Freigegeben");
        loadMetadataProposals();
      } else {
        alert("Fehler: " + data.error);
      }
    });
}

function rejectMetadata(id) {
  const reason = prompt("Grund für Ablehnung:");
  if (reason === null) return;
  fetch(`/admin/shops/metadata_proposals/${id}/reject`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Abgelehnt");
        loadMetadataProposals();
      } else {
        alert("Fehler: " + data.error);
      }
    });
}

function deleteMetadata(id) {
  if (!confirm("Diesen Antrag wirklich löschen?")) return;
  fetch(`/admin/shops/metadata_proposals/${id}/delete`, { method: "POST" })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Gelöscht");
        loadMetadataProposals();
      } else {
        alert("Fehler: " + data.error);
      }
    });
}

function loadRatesForReview() {
  const list = document.getElementById("rates-list");
  if (!list) return;
  list.innerHTML =
    '<div class="empty-state"><div class="empty-state-icon">⭐</div><p>Rate review coming soon...</p></div>';
}

function wireScraperForms() {
  const milesForm = document.getElementById("miles-and-more-form");
  const paybackForm = document.getElementById("payback-form");
  const topcashbackForm = document.getElementById("topcashback-form");
  const shoopForm = document.getElementById("shoop-form");
  if (shoopForm) {
    shoopForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_shoop", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting Shoop scraper: " + err));
    });
  }

  if (milesForm) {
    milesForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_miles_and_more", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting Miles & More scraper: " + err));
    });
  }

  if (paybackForm) {
    paybackForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_payback", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting Payback scraper: " + err));
    });
  }

  if (topcashbackForm) {
    topcashbackForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_topcashback", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting TopCashback scraper: " + err));
    });
  }

  const letyForm = document.getElementById("letyshops-form");
  if (letyForm) {
    letyForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_letyshops", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting LetyShops scraper: " + err));
    });
  }

  const andChargeForm = document.getElementById("and-charge-form");
  if (andChargeForm) {
    andChargeForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_and_charge", {
        method: "POST",
        headers: { Accept: "application/json" },
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting &Charge scraper: " + err));
    });
  }

  const importForm = document.getElementById("consolidated-import-form");
  const importPreview = document.getElementById("consolidated-preview");
  const importProgram = document.getElementById("consolidated-program");
  const importCount = document.getElementById("consolidated-shop-count");
  const importConfirm = document.getElementById("consolidated-confirm");

  if (importForm) {
    importForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const fileInput = document.getElementById("consolidated-file");
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert("Bitte eine JSON-Datei auswählen.");
        return;
      }

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      fetch("/admin/import_consolidated/preview", {
        method: "POST",
        body: formData,
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) {
            alert("Fehler: " + data.error);
            return;
          }
          importPreview.style.display = "block";
          importProgram.textContent = data.program || "—";
          importCount.textContent = data.shop_count ?? 0;
          importConfirm.disabled = false;
          importConfirm.dataset.token = data.token;
        })
        .catch((err) => alert("Fehler beim Laden der Vorschau: " + err));
    });
  }

  if (importConfirm) {
    importConfirm.addEventListener("click", () => {
      const token = importConfirm.dataset.token;
      if (!token) {
        alert("Kein Token vorhanden. Bitte Vorschau erneut laden.");
        return;
      }
      fetch("/admin/import_consolidated/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ token }),
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) {
            alert("Fehler: " + data.error);
            return;
          }
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Fehler beim Starten des Imports: " + err));
    });
  }

  const couponForm = document.getElementById("coupon-import-form");
  const couponPreview = document.getElementById("coupon-preview");
  const couponProgram = document.getElementById("coupon-program");
  const couponCount = document.getElementById("coupon-count");
  const couponMissing = document.getElementById("coupon-missing");
  const couponMissingPrograms = document.getElementById("coupon-missing-programs");
  const couponMissingShops = document.getElementById("coupon-missing-shops");
  const couponConfirm = document.getElementById("coupon-confirm");
  const couponTableWrapper = document.getElementById("coupon-table-wrapper");
  const couponFeedback = document.getElementById("coupon-import-feedback");

  const couponState = {
    token: null,
    rows: [],
  };

  function setCouponConfirmEnabled() {
    if (!couponConfirm) return;
    const table = document.getElementById("coupon-table");
    if (!table) {
      couponConfirm.disabled = true;
      return;
    }
    const anyChecked = table.querySelectorAll(".coupon-include:checked").length > 0;
    couponConfirm.disabled = !anyChecked;
  }

  function showCouponFeedback(message, type) {
    if (!couponFeedback) return;
    couponFeedback.style.display = "block";
    const color = type === "success" ? "#2e7d32" : type === "error" ? "#b00020" : "#555";
    couponFeedback.innerHTML = `<p style="margin:0;color:${color};">${message}</p>`;
  }

  function buildSuggestionOptions(row) {
    const suggestions = row.suggestions || [];
    const matchedId = row.matched_shop_id;
    const matchedName = row.matched_shop_name;
    const ids = new Set(suggestions.map((s) => String(s.id)));
    let options = `<option value="">— Shop wählen —</option>`;
    if (matchedId && matchedName && !ids.has(String(matchedId))) {
      options += `<option value="${matchedId}" selected>${matchedName}</option>`;
    }
    suggestions.forEach((s) => {
      const selected = matchedId && String(s.id) === String(matchedId) ? "selected" : "";
      options += `<option value="${s.id}" ${selected}>${s.name}</option>`;
    });
    return options;
  }

  function updateMatchStatus(rowEl) {
    const statusEl = rowEl.querySelector(".coupon-match-status");
    const select = rowEl.querySelector(".coupon-shop-select");
    if (!statusEl || !select) return;
    statusEl.textContent = select.value ? "✅" : "❌";
  }

  function renderCouponTable(rows) {
    if (!couponTableWrapper) return;
    if (!rows || rows.length === 0) {
      couponTableWrapper.innerHTML = "<div class='empty-state'><p>Keine Coupons gefunden.</p></div>";
      return;
    }

    let html = `<table class='admin-table' id='coupon-table'>`;
    html += `<thead><tr>`;
    html += `<th>Import</th>`;
    html += `<th>Shopname (editierbar)</th>`;
    html += `<th>Shop-Match</th>`;
    html += `<th>Status</th>`;
    html += `<th>Coupon</th>`;
    html += `</tr></thead><tbody>`;

    rows.forEach((row) => {
      const title = row.title || "Coupon";
      const discount = row.discount_text || "";
      html += `<tr data-index='${row.index}'>`;
      const isMatched = !!row.matched_shop_id;
      html += `<td><input type='checkbox' class='coupon-include' ${isMatched ? "checked" : ""} /></td>`;
      html += `<td><input type='text' class='coupon-merchant-input' value='${row.merchant || ""}' /></td>`;
      html += `<td><select class='coupon-shop-select'>${buildSuggestionOptions(row)}</select></td>`;
      html += `<td><span class='coupon-match-status'>${row.matched_shop_id ? "✅" : "❌"}</span></td>`;
      html += `<td><strong>${title}</strong><br /><small>${discount}</small></td>`;
      html += `</tr>`;
    });

    html += `</tbody></table>`;
    couponTableWrapper.innerHTML = html;

    couponTableWrapper.querySelectorAll(".coupon-include").forEach((input) => {
      input.addEventListener("change", setCouponConfirmEnabled);
    });

    couponTableWrapper.querySelectorAll(".coupon-shop-select").forEach((select) => {
      select.addEventListener("change", (e) => {
        const rowEl = e.target.closest("tr");
        if (rowEl) updateMatchStatus(rowEl);
      });
    });

    couponTableWrapper.querySelectorAll(".coupon-merchant-input").forEach((input) => {
      let timeout = null;
      input.addEventListener("input", (e) => {
        const rowEl = e.target.closest("tr");
        const select = rowEl ? rowEl.querySelector(".coupon-shop-select") : null;
        if (!rowEl || !select) return;
        if (timeout) clearTimeout(timeout);
        timeout = setTimeout(() => {
          const q = e.target.value.trim();
          if (!q) {
            select.innerHTML = `<option value="">— Shop wählen —</option>`;
            updateMatchStatus(rowEl);
            return;
          }
          fetch(`/shop_names?q=${encodeURIComponent(q)}&limit=50`)
            .then((r) => r.json())
            .then((suggestions) => {
              const tempRow = {
                suggestions: suggestions || [],
                matched_shop_id: null,
                matched_shop_name: null,
              };
              select.innerHTML = buildSuggestionOptions(tempRow);
              updateMatchStatus(rowEl);
            })
            .catch(() => {
              select.innerHTML = `<option value="">— Shop wählen —</option>`;
              updateMatchStatus(rowEl);
            });
        }, 300);
      });
    });

    setCouponConfirmEnabled();
  }

  if (couponForm) {
    couponForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const fileInput = document.getElementById("coupon-file");
      if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        alert("Bitte eine JSON-Datei auswählen.");
        return;
      }

      const formData = new FormData();
      formData.append("file", fileInput.files[0]);

      fetch("/admin/import_coupons/preview", {
        method: "POST",
        body: formData,
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) {
            alert("Fehler: " + data.error);
            return;
          }
          couponPreview.style.display = "block";
          couponProgram.textContent = data.program || "—";
          couponCount.textContent = data.coupon_count ?? 0;

          const missingPrograms = data.missing_programs || [];
          const missingShops = data.missing_shops || [];
          if (missingPrograms.length || missingShops.length) {
            couponMissing.style.display = "block";
            couponMissingPrograms.textContent = missingPrograms.join(", ") || "—";
            couponMissingShops.textContent = missingShops.join(", ") || "—";
          } else {
            couponMissing.style.display = "none";
          }

          couponState.token = data.token;
          couponState.rows = data.rows || [];
          couponConfirm.dataset.token = data.token;
          renderCouponTable(couponState.rows);
          showCouponFeedback("Vorschau geladen. Bitte Auswahl prüfen und Import starten.", "info");
        })
        .catch((err) => alert("Fehler beim Laden der Vorschau: " + err));
    });
  }

  if (couponConfirm) {
    couponConfirm.addEventListener("click", () => {
      const token = couponConfirm.dataset.token;
      if (!token) {
        alert("Kein Token vorhanden. Bitte Vorschau erneut laden.");
        return;
      }
      const table = document.getElementById("coupon-table");
      if (!table) {
        alert("Keine Tabelle gefunden. Bitte Vorschau erneut laden.");
        return;
      }

      const selections = [];
      const missing = [];
      table.querySelectorAll("tbody tr").forEach((row) => {
        const include = row.querySelector(".coupon-include");
        if (!include || !include.checked) return;
        const index = row.getAttribute("data-index");
        const merchant = row.querySelector(".coupon-merchant-input")?.value || "";
        const shopId = row.querySelector(".coupon-shop-select")?.value || "";
        if (!shopId) {
          missing.push(merchant || `Index ${index}`);
          return;
        }
        selections.push({ index: Number(index), shop_id: Number(shopId), merchant });
      });

      if (missing.length) {
        alert(`Bitte Shop auswählen für: ${missing.join(", ")}`);
        return;
      }
      if (!selections.length) {
        alert("Bitte mindestens einen Coupon auswählen.");
        return;
      }
      couponConfirm.disabled = true;
      showCouponFeedback("Import wird gestartet…", "info");
      fetch("/admin/import_coupons/confirm", {
        method: "POST",
        headers: { "Content-Type": "application/json", Accept: "application/json" },
        body: JSON.stringify({ token, selections }),
        credentials: "same-origin",
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.error) {
            const extra = [];
            if (data.missing_programs && data.missing_programs.length) {
              extra.push(`Fehlende Programme: ${data.missing_programs.join(", ")}`);
            }
            if (data.missing_shops && data.missing_shops.length) {
              extra.push(`Fehlende Shops: ${data.missing_shops.join(", ")}`);
            }
            showCouponFeedback(
              "Fehler: " + data.error + (extra.length ? "<br />" + extra.join("<br />") : ""),
              "error",
            );
            setCouponConfirmEnabled();
            return;
          }
          if (data.job_id) startJobMonitoring(data.job_id);
          showCouponFeedback("Import gestartet. Job läuft im Hintergrund.", "success");
        })
        .catch((err) => {
          showCouponFeedback("Fehler beim Starten des Imports: " + err, "error");
          setCouponConfirmEnabled();
        });
    });
  }
}

let jobId = null;
let pollInterval = null;

function startJobMonitoring(id) {
  jobId = id;
  const progress = document.getElementById("job-progress");
  if (progress) progress.classList.add("active");
  pollInterval = setInterval(updateJobStatus, 500);
  updateJobStatus();
}

function updateJobStatus() {
  if (!jobId) return;

  fetch(`/admin/job_status/${jobId}`)
    .then((r) => r.json())
    .then((data) => {
      const statusEl = document.getElementById("job-status");
      const progressFill = document.getElementById("progress-fill");
      if (statusEl) {
        statusEl.textContent = data.status.toUpperCase();
        statusEl.className = `job-status ${data.status}`;
        // Make status clickable to view worker logs (if available)
        statusEl.style.cursor = "pointer";
        statusEl.onclick = () => {
          fetch(`/admin/job_status/${jobId}?include_logs=1`)
            .then((r) => r.json())
            .then((d) => {
              const logs = d.logs || d.messages || [];
              if (logs.length === 0) {
                alert("No logs available for this job.");
                return;
              }
              const txt = logs.map((m) => (m.timestamp ? `[${m.timestamp}] ${m.message}` : m.message)).join("\n");
              alert(`Worker logs:\n\n${txt}`);
            })
            .catch((err) => alert("Error fetching logs: " + err));
        };
      }
      if (progressFill) {
        progressFill.style.width = `${data.progress_percent}%`;
        progressFill.textContent = `${data.progress_percent}%`;
      }

      const messagesDiv = document.getElementById("job-messages");
      if (messagesDiv) {
        messagesDiv.innerHTML = "";
        (data.messages || []).slice(-50).forEach((msg) => {
          const msgEl = document.createElement("div");
          msgEl.textContent = `[${msg.timestamp.substr(11, 8)}] ${msg.message}`;
          messagesDiv.appendChild(msgEl);
        });
        messagesDiv.scrollTop = messagesDiv.scrollHeight;
      }

      if (data.status === "completed" || data.status === "failed") {
        clearInterval(pollInterval);
        if (data.status === "completed") {
          setTimeout(() => window.location.reload(), 2000);
        }
      }
    });
}

function renderShopList(data) {
  const container = document.getElementById("shop-list");
  const paging = document.getElementById("shop-paging");
  if (!container) return;
  if (!data.shops || data.shops.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🛒</div><p>Keine Shops gefunden.</p></div>';
    if (paging) paging.innerHTML = "";
    return;
  }

  let html = `<table class='admin-table'><thead><tr><th>Name</th><th>Status</th><th>Website</th><th>Varianten</th><th>Raten</th><th>Aktionen</th></tr></thead><tbody>`;
  data.shops.forEach((shop) => {
    const variants = shop.variants
      .map((v) => `${v.source}: ${v.name} (conf ${Math.round(v.confidence)}%)`)
      .join("<br>");
    let rates = "—";
    if (shop.rates && shop.rates.length > 0) {
      const r = shop.rates[0];
      let cat = r.category ? `<span style='color:#888'>[${r.category}]</span> ` : "";
      let subcat = r.sub_category ? ` (${r.sub_category})` : "";
      const rateTypeIcon = r.rate_type === "contract" ? "📝" : "🛒";
      let rateParts = [];
      if (r.points_per_eur) rateParts.push(`${r.points_per_eur} P/EUR`);
      if (r.points_absolute) rateParts.push(`${r.points_absolute} P absolut`);
      if (r.cashback_pct) rateParts.push(`${r.cashback_pct}% CB`);
      if (r.cashback_absolute) rateParts.push(`${r.cashback_absolute}€ CB absolut`);
      rates = `${rateTypeIcon} ${cat}${r.program}: ${rateParts.join(", ")}${subcat}`;
      if (shop.rates.length > 1) {
        rates += ` <span style='color:#888'>(+${shop.rates.length - 1} weitere, siehe Details)</span>`;
      }
    }
    html += `<tr>`;
    html += `<td><strong>${shop.name}</strong></td>`;
    html += `<td><span style="padding: 4px 8px; border-radius: 4px; font-size: 12px; ${
      shop.status === "deleted"
        ? "background: #ffcccc; color: #8b0000; font-weight: bold;"
        : shop.status === "merged"
          ? "background: #fff3cd; color: #856404;"
          : "background: #d4edda; color: #155724;"
    }">${shop.status.toUpperCase()}</span></td>`;
    html += `<td>${shop.website ? `<a href='${shop.website}' target='_blank'>${shop.website}</a>` : "—"}</td>`;
    html += `<td>${variants || "—"}</td>`;
    html += `<td>${rates}</td>`;
    html += `<td>
      <button class='btn btn-inline' onclick="openShopDetails('${shop.id}')">🔎 Details</button>
    </td>`;
    html += `</tr>`;
  });
  html += `</tbody></table>`;
  container.innerHTML = html;

  // Paging controls
  if (paging && data.total && data.per_page) {
    const totalPages = Math.ceil(data.total / data.per_page);
    let html = "";
    if (totalPages > 1) {
      const page = data.page || 1;
      html += `<button class='btn btn-inline' ${page <= 1 ? "disabled" : ""} onclick='changeShopPage(${
        page - 1
      })'>⏮️ Vorherige</button>`;
      html += ` Seite ${page} / ${totalPages} `;
      html += `<button class='btn btn-inline' ${page >= totalPages ? "disabled" : ""} onclick='changeShopPage(${
        page + 1
      })'>Nächste ⏭️</button>`;
    }
    paging.innerHTML = html;
  }
}

let shopPage = 1;
let shopPerPage = 50;
function changeShopPage(page) {
  if (page < 1) page = 1;
  shopPage = page;
  loadShops();
}
function loadShops() {
  const searchInput = document.getElementById("shop-search");
  const programSelect = document.getElementById("bonus-program-filter");
  const showDeletedCheckbox = document.getElementById("show-deleted-shops");
  const q = searchInput?.value || "";
  const program = programSelect?.value || "";
  const showDeleted = showDeletedCheckbox?.checked ? "1" : "0";
  const url = `/admin/shops_overview?q=${encodeURIComponent(q)}${
    program ? `&program=${encodeURIComponent(program)}` : ""
  }&page=${shopPage}&per_page=${shopPerPage}&include_deleted=${showDeleted}`;
  fetch(url)
    .then((r) => r.json())
    .then((data) => renderShopList(data));
}

function wireShopSearch() {
  const input = document.getElementById("shop-search");
  if (input) {
    input.addEventListener("input", () => {
      clearTimeout(window._shopSearchTimer);
      window._shopSearchTimer = setTimeout(() => {
        shopPage = 1;
        loadShops();
      }, 250);
    });
  }
  const programSelect = document.getElementById("bonus-program-filter");
  if (programSelect) {
    programSelect.addEventListener("change", () => {
      shopPage = 1;
      loadShops();
    });
  }
  const showDeletedCheckbox = document.getElementById("show-deleted-shops");
  if (showDeletedCheckbox) {
    showDeletedCheckbox.addEventListener("change", () => {
      shopPage = 1;
      loadShops();
    });
  }
}

function initAdminPage() {
  // Load shops immediately if Shop tab is active on page load
  const shopsTab = document.getElementById("tab-shops");
  if (shopsTab && shopsTab.classList.contains("active")) {
    loadShops();
  }
  updateNotificationBadge();
  setInterval(updateNotificationBadge, 30000);
  wireScraperForms();
  wireShopSearch();
  fetch("/admin/bonus_programs")
    .then((r) => r.json())
    .then((data) => {
      const select = document.getElementById("bonus-program-filter");
      const delBtn = document.getElementById("delete-program-shops");
      if (!select || !data.programs) return;
      data.programs.forEach((p) => {
        const opt = document.createElement("option");
        opt.value = p.name;
        opt.textContent = p.name;
        select.appendChild(opt);
      });
      // Enable/disable delete button based on selection
      if (delBtn && select) {
        select.addEventListener("change", () => {
          delBtn.disabled = !select.value;
          delBtn.title = select.value
            ? `Alle Shops für ${select.value} löschen`
            : "Wähle ein Bonusprogramm zum Löschen";
        });
        delBtn.disabled = !select.value;
        delBtn.title = select.value ? `Alle Shops für ${select.value} löschen` : "Wähle ein Bonusprogramm zum Löschen";
        delBtn.addEventListener("click", () => {
          if (!select.value) return;
          if (
            !confirm(
              `⚠️ Sicher? Dies löscht ALLE Shops für das Bonusprogramm '${select.value}'!\n\nDiese Aktion kann nicht rückgängig gemacht werden.`,
            )
          )
            return;
          fetch(`/admin/clear_shops_for_program`, {
            method: "POST",
            headers: { "Content-Type": "application/json", Accept: "application/json" },
            body: JSON.stringify({ program: select.value }),
          })
            .then((r) => r.json())
            .then((data) => {
              if (data.success) {
                alert(`✅ ${data.deleted} Shops für '${select.value}' gelöscht!`);
                loadShops();
              } else {
                alert("❌ Fehler: " + (data.error || "Unbekannter Fehler"));
              }
            })
            .catch((err) => {
              alert("❌ Fehler beim Löschen: " + err);
            });
        });
      }
    });

  // Ensure only the first tab-content is active on load
  document.querySelectorAll(".tab-content").forEach((el, idx) => {
    if (idx === 0) {
      el.classList.add("active");
    } else {
      el.classList.remove("active");
    }
  });
}

function clearAllShops() {
  if (
    !confirm(
      "⚠️ Sicher? Dies löscht ALLE Shops aus der Datenbank!\n\nDiese Aktion kann nicht rückgängig gemacht werden.",
    )
  ) {
    return;
  }

  if (!confirm("Wirklich? Alle Shops werden gelöscht.")) {
    return;
  }

  fetch("/admin/clear_shops", {
    method: "POST",
    headers: {
      Accept: "application/json",
    },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert(`✅ ${data.deleted} Shops gelöscht!`);
        location.reload();
      } else {
        alert("❌ Fehler: " + (data.error || "Unbekannter Fehler"));
      }
    })
    .catch((err) => {
      alert("❌ Fehler beim Löschen: " + err);
    });
}

function setupTabDelegation() {
  const tabNav = document.querySelector(".tab-nav");
  if (tabNav) {
    tabNav.addEventListener("click", function (e) {
      const btn = e.target.closest(".tab-button");
      if (btn && btn.dataset.tab) {
        e.preventDefault();
        switchTab(btn.dataset.tab, e);
      }
    });
  }
}

// Shop Variant Management
let currentShopMainId = null;
let selectedVariantIds = new Set();

function loadShopVariantSearch() {
  const searchInput = document.getElementById("shop-variant-search");
  if (!searchInput) return;

  searchInput.addEventListener("input", (e) => {
    const query = e.target.value.toLowerCase().trim();
    searchShopMains(query);
  });
}

function searchShopMains(query) {
  // Use admin shops overview to get ShopMain data
  fetch(`/admin/shops_overview?q=${encodeURIComponent(query)}&per_page=20`)
    .then((r) => r.json())
    .then((data) => {
      const list = document.getElementById("shop-variant-list");
      if (!list) return;

      list.innerHTML = "";

      if (!data.shops || !data.shops.length) {
        list.innerHTML = '<div style="padding: 12px; color: #999;">Keine Shops gefunden</div>';
        return;
      }

      data.shops.forEach((shop) => {
        const div = document.createElement("div");
        div.className = "shop-variant-item";
        div.style.cssText =
          "padding: 10px; border-bottom: 1px solid #eee; cursor: pointer; transition: background 0.2s;";
        div.innerHTML = `<strong>${shop.name}</strong> <span style="color: #999; font-size: 12px;">(${shop.variants.length} Varianten)</span>`;
        div.addEventListener("mouseenter", () => (div.style.background = "#f5f5f5"));
        div.addEventListener("mouseleave", () => (div.style.background = ""));
        div.addEventListener("click", () => loadShopVariants(shop.id));
        list.appendChild(div);
      });
    });
}

function loadShopVariants(shopId) {
  fetch(`/admin/shops/${shopId}/details`)
    .then((r) => r.json())
    .then((data) => {
      if (data.error) {
        alert("Error: " + data.error);
        return;
      }

      currentShopMainId = data.main.id;
      selectedVariantIds.clear();

      document.getElementById("selected-shop-name").textContent = `Shop: ${data.main.canonical_name}`;
      const idEl = document.getElementById("selected-shop-id");
      if (idEl) {
        idEl.textContent = `ID: ${data.main.id}`;
      }
      document.getElementById("shop-variant-details").style.display = "block";

      const container = document.getElementById("variant-selection-container");
      container.innerHTML = "";

      if (!data.main.variants || data.main.variants.length === 0) {
        container.innerHTML = '<p style="color: #999;">Keine Varianten vorhanden</p>';
        return;
      }

      container.innerHTML = "<h5>Varianten:</h5>";
      data.main.variants.forEach((variant) => {
        const div = document.createElement("div");
        div.style.cssText = "padding: 8px; margin: 4px 0; border: 1px solid #ddd; border-radius: 4px;";
        div.innerHTML = `
          <label style="display: flex; align-items: center; cursor: pointer;">
            <input
              type="checkbox"
              data-variant-id="${variant.id}"
              style="margin-right: 8px; width: 18px; height: 18px;"
            />
            <div>
              <strong>${variant.source_name}</strong>
              <span style="color: #666; font-size: 12px;">(${variant.source})</span>
            </div>
          </label>
        `;
        const checkbox = div.querySelector("input[type=checkbox]");
        checkbox.addEventListener("change", (e) => {
          if (e.target.checked) {
            selectedVariantIds.add(parseInt(e.target.dataset.variantId));
          } else {
            selectedVariantIds.delete(parseInt(e.target.dataset.variantId));
          }
        });
        container.appendChild(div);
      });
    })
    .catch((err) => {
      alert("Error loading shop details: " + err.message);
    });
}

function splitShopVariants() {
  if (!currentShopMainId) {
    alert("Bitte wähle zuerst einen Shop aus");
    return;
  }

  if (selectedVariantIds.size === 0) {
    alert("Bitte wähle mindestens eine Variante aus");
    return;
  }

  const newShopName = document.getElementById("new-shop-name").value.trim();
  if (!newShopName) {
    alert("Bitte gib einen Namen für den neuen Shop ein");
    return;
  }

  if (!confirm(`${selectedVariantIds.size} Variante(n) in neuen Shop "${newShopName}" verschieben?`)) {
    return;
  }

  fetch(`/admin/shops/${currentShopMainId}/split`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      variant_ids: Array.from(selectedVariantIds),
      new_shop_name: newShopName,
    }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert(`Shop erfolgreich gesplittet! Neuer Shop ID: ${data.new_shop_main_id}`);
        document.getElementById("shop-variant-details").style.display = "none";
        document.getElementById("new-shop-name").value = "";
        selectedVariantIds.clear();
      } else {
        alert("Error: " + data.error);
      }
    })
    .catch((err) => {
      alert("Error: " + err.message);
    });
}

function moveVariantsToExistingShop() {
  if (!currentShopMainId) {
    alert("Kein Shop ausgewählt");
    return;
  }

  if (selectedVariantIds.size === 0) {
    alert("Bitte wähle mindestens eine Variante aus");
    return;
  }

  const targetShopMainId = document.getElementById("target-shop-main-id").value.trim();
  if (!targetShopMainId) {
    alert("Bitte Ziel-ShopMain ID angeben");
    return;
  }

  const confirmMsg = `${selectedVariantIds.size} Variante(n) in bestehenden Shop ${targetShopMainId} verschieben?`;
  if (!confirm(confirmMsg)) {
    return;
  }

  fetch(`/admin/shops/${currentShopMainId}/move_variants`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      variant_ids: Array.from(selectedVariantIds),
      target_shop_main_id: targetShopMainId,
    }),
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Varianten erfolgreich verschoben!");
        document.getElementById("shop-variant-details").style.display = "none";
        document.getElementById("target-shop-main-id").value = "";
        selectedVariantIds.clear();
      } else {
        alert("Error: " + data.error);
      }
    })
    .catch((err) => {
      alert("Error: " + err.message);
    });
}

function deleteShop() {
  if (!currentShopMainId) {
    alert("Kein Shop ausgewählt");
    return;
  }

  const shopName = document.getElementById("selected-shop-name").textContent;
  if (
    !confirm(
      `Shop "${shopName}" wirklich löschen?\n\nDer Shop wird auf Status 'deleted' gesetzt und ist nicht mehr sichtbar.`,
    )
  ) {
    return;
  }

  fetch(`/admin/shops/${currentShopMainId}/delete`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        alert("Shop erfolgreich gelöscht!");
        document.getElementById("shop-variant-details").style.display = "none";
        document.getElementById("shop-variant-search").value = "";
        currentShopMainId = null;
      } else {
        alert("Error: " + data.error);
      }
    })
    .catch((err) => {
      alert("Error: " + err.message);
    });
}

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => {
    initAdminPage();
    setupTabDelegation();
    loadShopVariantSearch();
  });
} else {
  initAdminPage();
  setupTabDelegation();
  loadShopVariantSearch();
}
