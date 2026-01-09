function switchTab(tabName, evt) {
  document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"));
  document.querySelectorAll(".tab-content").forEach((content) => content.classList.remove("active"));

  const target = evt?.target || document.querySelector(`[data-tab="${tabName}"]`);
  if (target) target.classList.add("active");
  const tab = document.getElementById(`tab-${tabName}`);
  if (tab) tab.classList.add("active");

  if (tabName === "merges") loadMergeProposals();
  if (tabName === "metadata") loadMetadataProposals();
  if (tabName === "rates") loadRatesForReview();
  if (tabName === "notifications") loadNotifications();
  if (tabName === "shops") loadShops();
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
      <h3 id="shop-details-title">Shop Details</h3>
      <div id="shop-details-content"></div>
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
      title.textContent = data.canonical_name || `Shop ${mainId}`;
      if (!data.shops || data.shops.length === 0) {
        content.innerHTML = "<div>No linked shops or rates found.</div>";
        return;
      }
      const html = data.shops
        .map((s) => {
          const rates = s.rates
            .map((rt) => {
              const cat = rt.category ? `<strong>[${rt.category}]</strong> ` : "";
              const valid = rt.valid_from ? `${rt.valid_from}${rt.valid_to ? " → " + rt.valid_to : ""}` : "";
              return `<div style="padding:6px 0; border-bottom:1px solid #f0f0f0;">${cat}${rt.program}: ${
                rt.points_per_eur
              } P/EUR${
                rt.cashback_pct ? `, ${rt.cashback_pct}% CB` : ""
              }<div style="font-size:12px;color:#666">${valid}</div></div>`;
            })
            .join("");
          return `<div style="margin-bottom:12px;"><h4 style="margin:6px 0;">${s.name}</h4>${
            rates || "<div>No rates</div>"
          }</div>`;
        })
        .join("");
      content.innerHTML = html;
    })
    .catch((err) => {
      content.innerHTML = `<div style="color:red">Error: ${err}</div>`;
    });
}

function closeShopDetails() {
  const modal = document.getElementById("shop-details-modal");
  if (modal) modal.style.display = "none";
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

  if (milesForm) {
    milesForm.addEventListener("submit", (e) => {
      e.preventDefault();
      fetch("/admin/run_miles_and_more", {
        method: "POST",
        headers: { Accept: "application/json" },
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
      })
        .then((r) => r.json())
        .then((data) => {
          if (data.job_id) startJobMonitoring(data.job_id);
        })
        .catch((err) => alert("Error starting TopCashback scraper: " + err));
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
  if (!container) return;
  if (!data.shops || data.shops.length === 0) {
    container.innerHTML =
      '<div class="empty-state"><div class="empty-state-icon">🛒</div><p>Keine Shops gefunden.</p></div>';
    return;
  }

  const rows = data.shops
    .map((shop) => {
      const variants = shop.variants
        .map((v) => `${v.source}: ${v.name} (conf ${Math.round(v.confidence)}%)`)
        .join("<br>");
      const rates = shop.rates
        .map((r) => {
          let cat = r.category ? `<span style='color:#888'>[${r.category}]</span> ` : "";
          let subcat = r.sub_category ? ` (${r.sub_category})` : "";
          return `${cat}${r.program}: ${r.points_per_eur} P/EUR${
            r.cashback_pct ? `, ${r.cashback_pct}% CB` : ""
          }${subcat}`;
        })
        .join("<br>");
      return `
        <div style="border-bottom:1px solid #eee; padding:10px 0;">
          <div style="font-weight:600;">${shop.name}</div>
          <div style="color:#666;">${shop.status}${shop.website ? " • " + shop.website : ""}</div>
          <div style="margin-top:6px;"><button class="btn btn-inline" onclick="openShopDetails('${
            shop.id
          }')">🔎 Details</button></div>
          <div style="margin-top:6px;"><strong>Varianten:</strong><br>${variants || "—"}</div>
          <div style="margin-top:6px;"><strong>Raten:</strong><br>${rates || "—"}</div>
        </div>
      `;
    })
    .join("");
  container.innerHTML = rows;
}

function loadShops() {
  const searchInput = document.getElementById("shop-search");
  const programSelect = document.getElementById("bonus-program-filter");
  const q = searchInput?.value || "";
  const program = programSelect?.value || "";
  const url = `/admin/shops_overview?q=${encodeURIComponent(q)}${
    program ? `&program=${encodeURIComponent(program)}` : ""
  }`;
  fetch(url)
    .then((r) => r.json())
    .then((data) => renderShopList(data));
}

function wireShopSearch() {
  const input = document.getElementById("shop-search");
  if (input) {
    input.addEventListener("input", () => {
      clearTimeout(window._shopSearchTimer);
      window._shopSearchTimer = setTimeout(loadShops, 250);
    });
  }
  const programSelect = document.getElementById("bonus-program-filter");
  if (programSelect) {
    programSelect.addEventListener("change", loadShops);
  }
}

function initAdminPage() {
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

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initAdminPage);
} else {
  initAdminPage();
}
