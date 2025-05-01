async function fetchLogs(params = {}) {
  const query = new URLSearchParams(params).toString();
  const res = await fetch(`/logs?${query}`);
  const logs = await res.json();

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
  fetchLogs({ session_id: sessionId });
}

function resetFilters() {
  document.getElementById("session-id").value = "";
  fetchLogs();
}

function searchByTime() {
  const from = document.getElementById("start-time").value;
  const to = document.getElementById("end-time").value;
  fetchLogs({ start_time: from, end_time: to });
}

function resetTime() {
  document.getElementById("start-time").value = "";
  document.getElementById("end-time").value = "";
  fetchLogs();
}

function selectAll() {
  const checked = document.getElementById("select-all").checked;
  document.querySelectorAll("#log-table input[type='checkbox']").forEach(cb => cb.checked = checked);
}

async function deleteSelected() {
  const ids = [...document.querySelectorAll("#log-table input[type='checkbox']:checked")]
      .map(cb => cb.value);

  if (!ids.length) return alert("No records selected.");

  if (!confirm("Delete selected logs?")) return;

  const res = await fetch("/delete", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids })
  });

  const result = await res.json();
  alert(result.message || result.error);
  fetchLogs();
}

async function updateRetention() {
  const checkbox = document.getElementById("retention-toggle");
  const days = document.getElementById("retention-days").value;
  if (checkbox.checked) {
      const res = await fetch("/retention", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ days: parseInt(days) || 30 })
      });
      const result = await res.json();
      alert(result.message || result.error);
      fetchLogs();
  }
}

async function loadRetention() {
  const res = await fetch("/retention");
  const { days } = await res.json();
  document.getElementById("retention-toggle").checked = true;
  document.getElementById("retention-days").value = days;
}

window.onload = () => {
  fetchLogs();
  loadRetention();
};
