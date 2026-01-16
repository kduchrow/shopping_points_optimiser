// Add missing runScheduledJob function for scheduled jobs Play button
function runScheduledJob(jobId) {
  if (!confirm("Diesen Job jetzt ausführen?")) return;
  fetch(`/admin/scheduled_jobs/${jobId}/run`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        location.reload();
      } else {
        alert("Fehler beim Starten des Jobs: " + (data.message || "Unbekannter Fehler"));
      }
    })
    .catch(() => alert("Fehler beim Starten des Jobs."));
}

// Add missing runScheduledJob function for scheduled jobs Play button
function runScheduledJob(jobId) {
  if (!confirm("Diesen Job jetzt ausführen?")) return;
  fetch(`/admin/scheduled_jobs/${jobId}/run`, {
    method: "POST",
    headers: { Accept: "application/json" },
  })
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        location.reload();
      } else {
        alert("Fehler beim Starten des Jobs: " + (data.message || "Unbekannter Fehler"));
      }
    })
    .catch(() => alert("Fehler beim Starten des Jobs."));
}

// Show logs for a scheduled job in a modal dialog
function showJobLogs(jobId) {
  // Create modal if not exists
  let modal = document.getElementById("job-logs-modal");
  if (!modal) {
    modal = document.createElement("div");
    modal.id = "job-logs-modal";
    modal.style.position = "fixed";
    modal.style.left = 0;
    modal.style.top = 0;
    modal.style.width = "100%";
    modal.style.height = "100%";
    modal.style.background = "rgba(0,0,0,0.5)";
    modal.style.zIndex = 10000;
    modal.innerHTML = `
      <div id="job-logs-box" style="background:#fff; max-width:800px; margin:40px auto; padding:24px; border-radius:8px; overflow:auto; max-height:80%; position:relative;">
        <button style="position:absolute; right:12px; top:12px;" onclick="closeJobLogsModal()">✖</button>
        <h3 id="job-logs-title">Job Logs</h3>
        <div id="job-logs-content" style="margin-top:24px; font-family:monospace; font-size:14px; white-space:pre-wrap; max-height:60vh; overflow-y:auto;"></div>
      </div>
    `;
    document.body.appendChild(modal);
  }
  document.getElementById("job-logs-title").textContent = `Logs für Job #${jobId}`;
  document.getElementById("job-logs-content").innerHTML = "Lade Logs...";
  modal.style.display = "block";
  fetch(`/admin/scheduled_jobs/${jobId}/logs?json=1`)
    .then((r) => (r.ok ? r.json() : Promise.reject("Fehler beim Laden der Logs.")))
    .then((data) => {
      if (data.logs && data.logs.length > 0) {
        document.getElementById("job-logs-content").innerHTML = data.logs
          .map((l) => `<div><span style='color:#888;'>[${l.timestamp || ""}]</span> ${l.message || ""}</div>`)
          .join("");
      } else {
        document.getElementById("job-logs-content").innerHTML = "<em>Keine Logs vorhanden.</em>";
      }
    })
    .catch(() => {
      document.getElementById("job-logs-content").innerHTML =
        '<span style="color:red">Fehler beim Laden der Logs.</span>';
    });
}

function closeJobLogsModal() {
  const modal = document.getElementById("job-logs-modal");
  if (modal) modal.style.display = "none";
}
