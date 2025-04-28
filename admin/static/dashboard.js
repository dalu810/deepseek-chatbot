async function fetchLogs(params = "") {
  const response = await fetch(`/logs?${params}`);
  const logs = await response.json();

  const table = document.getElementById("log-table");
  table.innerHTML = "";
  logs.forEach(log => {
    const row = document.createElement("tr");
    row.innerHTML = `
      <td><input type="checkbox" value="${log.id}"></td>
      <td>${log.timestamp}</td>
      <td>${log.session_id}</td>
      <td>${log.user_message}</td>
      <td>${log.ai_response}</td>
    `;
    table.appendChild(row);
  });
}

function searchBySession() {
  const sessionId = document.getElementById("session-id").value.trim();
  if (!sessionId) return fetchLogs();
  fetchLogs(`session_id=${encodeURIComponent(sessionId)}`);
}

function searchByTime() {
  const startTime = document.getElementById("start-time").value;
  const endTime = document.getElementById("end-time").value;

  if (!startTime && !endTime) {
    fetchLogs();
    return;
  }

  const params = new URLSearchParams();
  if (startTime) params.append("start_time", startTime);
  if (endTime) params.append("end_time", endTime);

  fetchLogs(params.toString());
}

function resetFilters() {
  document.getElementById("session-id").value = "";
  fetchLogs();
}

function resetTime() {
  document.getElementById("start-time").value = "";
  document.getElementById("end-time").value = "";
  fetchLogs();
}

function selectAll() {
  const checkboxes = document.querySelectorAll("#log-table input[type='checkbox']");
  const allChecked = document.getElementById("select-all").checked;
  checkboxes.forEach(cb => cb.checked = allChecked);
}

async function deleteSelected() {
  const selected = [...document.querySelectorAll("#log-table input[type='checkbox']:checked")]
    .map(cb => parseInt(cb.value));

  if (selected.length === 0) {
    alert("No logs selected.");
    return;
  }

  if (!confirm(`Delete ${selected.length} selected log(s)?`)) return;

  const res = await fetch("/delete", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids: selected }),
  });

  const result = await res.json();
  if (result.deleted) {
    alert(`Deleted ${result.deleted.length} log(s)!`);
  } else {
    alert("Deletion failed.");
  }
  fetchLogs();
}

window.onload = fetchLogs;
