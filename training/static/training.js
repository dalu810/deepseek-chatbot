async function loadMaterials() {
    const res = await fetch("/materials");
    const data = await res.json();
  
    const table = document.getElementById("material-table");
    table.innerHTML = "";
    data.forEach(item => {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><input type="checkbox" value="${item.id}"></td>
        <td>${item.id}</td>
        <td>${item.question}</td>
        <td>${item.answer}</td>
        <td>${item.updated_at}</td>
      `;
      table.appendChild(row);
    });
  }
  
  async function uploadCSV() {
    const fileInput = document.getElementById("csv-file");
    const file = fileInput.files[0];
    if (!file) return alert("Please select a CSV file");
  
    const formData = new FormData();
    formData.append("file", file);
  
    const res = await fetch("/upload", {
      method: "POST",
      body: formData,
    });
  
    const result = await res.json();
    document.getElementById("upload-result").innerText =
      `Inserted: ${result.inserted}, Updated: ${result.updated}`;
    fileInput.value = "";
    loadMaterials();
  }
  
  function toggleSelectAll(source) {
    const checkboxes = document.querySelectorAll("#material-table input[type='checkbox']");
    checkboxes.forEach(cb => cb.checked = source.checked);
  }
  
  async function deleteSelected() {
    const selected = [...document.querySelectorAll("#material-table input[type='checkbox']:checked")]
      .map(cb => parseInt(cb.value));
  
    if (selected.length === 0) {
      alert("No records selected for deletion.");
      return;
    }
  
    if (!confirm(`Are you sure you want to delete ${selected.length} record(s)?`)) return;
  
    const res = await fetch("/delete-materials", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ids: selected })
    });
  
    const result = await res.json();
    alert("Deleted records: " + result.deleted.join(", "));
    loadMaterials();
  }
  
  window.onload = loadMaterials;
  