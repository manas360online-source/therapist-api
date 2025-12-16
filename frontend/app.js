const apiBase = "/api/v1";

async function fetchJSON(url, options = {}) {
    const res = await fetch(url, {
        headers: {
            ...(options.headers || {})
        },
        ...options
    });
    if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `Request failed with status ${res.status}`);
    }
    return res.json();
}

function switchTab(tabId) {
    document.querySelectorAll(".tab-button").forEach(btn => {
        btn.classList.toggle("active", btn.dataset.tab === tabId);
    });
    document.querySelectorAll(".tab").forEach(tab => {
        tab.classList.toggle("active", tab.id === tabId);
    });
}

function setupTabs() {
    document.querySelectorAll(".tab-button").forEach(btn => {
        btn.addEventListener("click", () => switchTab(btn.dataset.tab));
    });
}

function renderProfile(profile) {
    const view = document.getElementById("profile-view");
    view.innerHTML = `
        <h3>${profile.full_name}</h3>
        <small>${profile.email}</small>
        <p class="muted">${profile.specialization || "No specialization set"}</p>
        <p>${profile.bio || "<em>No bio yet.</em>"}</p>
    `;

    const form = document.getElementById("profile-form");
    form.full_name.value = profile.full_name || "";
    form.email.value = profile.email || "";
    form.specialization.value = profile.specialization || "";
    form.bio.value = profile.bio || "";
}

async function loadProfile() {
    try {
        const data = await fetchJSON(`${apiBase}/therapists/me/profile`);
        renderProfile(data);
    } catch (err) {
        document.getElementById("profile-view").innerHTML =
            `<p class="status err">Could not load profile: ${err.message}</p>`;
    }
}

function setupProfileForm() {
    const form = document.getElementById("profile-form");
    const statusEl = document.getElementById("profile-status");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        statusEl.textContent = "Saving...";
        statusEl.className = "status";
        const body = {
            full_name: form.full_name.value,
            email: form.email.value,
            specialization: form.specialization.value,
            bio: form.bio.value
        };
        try {
            const saved = await fetchJSON(`${apiBase}/therapists/profile`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(body)
            });
            renderProfile(saved);
            statusEl.textContent = "Profile saved!";
            statusEl.classList.add("ok");
        } catch (err) {
            statusEl.textContent = `Error: ${err.message}`;
            statusEl.classList.add("err");
        }
    });
}

function renderLeads(leads) {
    const container = document.getElementById("leads-list");
    if (!leads.length) {
        container.innerHTML = `<p class="muted">No leads yet.</p>`;
        return;
    }
    container.innerHTML = "";
    leads.forEach(lead => {
        const card = document.createElement("div");
        card.className = "card";
        const purchasedBadge = lead.purchased
            ? `<span class="badge green">Purchased</span>`
            : `<span class="badge amber">Available</span>`;
        card.innerHTML = `
            <h3>${lead.patient_name}</h3>
            <small>${lead.issue || "No issue description"}</small>
            <p class="muted">Price: ₹${lead.price.toFixed(2)}</p>
            ${purchasedBadge}
        `;
        if (!lead.purchased) {
            const btn = document.createElement("button");
            btn.textContent = "Purchase Lead";
            btn.addEventListener("click", async () => {
                btn.disabled = true;
                btn.textContent = "Purchasing...";
                try {
                    await fetchJSON(`${apiBase}/therapists/me/leads/${lead.id}/purchase`, {
                        method: "POST"
                    });
                    await loadLeads();
                    await loadEarnings();
                } catch (err) {
                    alert("Error purchasing lead: " + err.message);
                    btn.disabled = false;
                    btn.textContent = "Purchase Lead";
                }
            });
            card.appendChild(btn);
        }
        container.appendChild(card);
    });
}

async function loadLeads() {
    try {
        const data = await fetchJSON(`${apiBase}/therapists/me/leads`);
        renderLeads(data);
    } catch (err) {
        document.getElementById("leads-list").innerHTML =
            `<p class="status err">Could not load leads: ${err.message}</p>`;
        console.error("Error loading leads:", err);
    }
}

function renderSessions(sessions) {
    const container = document.getElementById("sessions-list");
    if (!sessions.length) {
        container.innerHTML = `<p class="muted">No sessions scheduled yet.</p>`;
        return;
    }
    container.innerHTML = "";
    sessions.forEach(session => {
        const card = document.createElement("div");
        card.className = "card";
        const dt = new Date(session.scheduled_for);
        let badgeClass = "gray";
        if (session.status === "completed") badgeClass = "green";
        else if (session.status === "scheduled") badgeClass = "amber";
        else if (session.status === "cancelled") badgeClass = "gray";
        
        card.innerHTML = `
            <h3>${session.patient_name}</h3>
            <small>${dt.toLocaleString()}</small>
            <p class="muted">Fee: ₹${session.fee.toFixed(2)}</p>
            <span class="badge ${badgeClass}">${session.status}</span>
        `;

        if (session.status !== "completed" && session.status !== "cancelled") {
            const completeBtn = document.createElement("button");
            completeBtn.textContent = "Mark Completed";
            completeBtn.style.marginRight = "6px";
            completeBtn.addEventListener("click", async () => {
                try {
                    await fetchJSON(`${apiBase}/therapists/me/sessions/${session.id}`, {
                        method: "PATCH",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ status: "completed" })
                    });
                    await loadSessions();
                    await loadEarnings();
                } catch (err) {
                    alert("Error updating session: " + err.message);
                }
            });
            card.appendChild(completeBtn);
        }

        const notesBtn = document.createElement("button");
        notesBtn.textContent = "Add Notes (Encrypted)";
        notesBtn.addEventListener("click", async () => {
            const notes = prompt("Enter session notes (will be stored encrypted):");
            if (!notes) return;
            try {
                await fetchJSON(`${apiBase}/therapists/me/sessions/${session.id}/notes`, {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ notes })
                });
                alert("Notes saved securely!");
            } catch (err) {
                alert("Error saving notes: " + err.message);
            }
        });
        card.appendChild(notesBtn);

        container.appendChild(card);
    });
}

async function loadSessions() {
    try {
        const data = await fetchJSON(`${apiBase}/therapists/me/sessions`);
        renderSessions(data);
    } catch (err) {
        document.getElementById("sessions-list").innerHTML =
            `<p class="status err">Could not load sessions: ${err.message}</p>`;
        console.error("Error loading sessions:", err);
    }
}

function setupDocumentForm() {
    const form = document.getElementById("document-form");
    const statusEl = document.getElementById("document-status");
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = form.querySelector("input[type=file]");
        if (!fileInput.files.length) {
            statusEl.textContent = "Please choose a file.";
            statusEl.className = "status err";
            return;
        }
        const formData = new FormData();
        formData.append("file", fileInput.files[0]);

        statusEl.textContent = "Uploading...";
        statusEl.className = "status";
        try {
            const res = await fetchJSON(`${apiBase}/therapists/me/documents`, {
                method: "POST",
                body: formData
            });
            statusEl.textContent = res.message;
            statusEl.classList.add("ok");
            fileInput.value = "";
        } catch (err) {
            statusEl.textContent = `Error: ${err.message}`;
            statusEl.classList.add("err");
        }
    });
}

function renderEarnings(data) {
    const card = document.getElementById("earnings-card");
    card.innerHTML = `
        <h3>Financial Summary</h3>
        <p class="muted">Overview of your practice finances and earnings performance.</p>
        <div class="earnings-grid">
            <div class="earnings-item">
                <h4>Total Earned</h4>
                <p class="earning-value">₹${data.total_earnings.toFixed(2)}</p>
            </div>
            <div class="earnings-item">
                <h4>From Sessions</h4>
                <p class="earning-value">₹${data.from_sessions.toFixed(2)}</p>
            </div>
            <div class="earnings-item">
                <h4>Spent on Leads</h4>
                <p class="earning-value">₹${data.spent_on_leads.toFixed(2)}</p>
            </div>
            <div class="earnings-item" style="background: linear-gradient(135deg, #dcfce7, #fef3c7);">
                <h4>Net Earnings</h4>
                <p class="earning-value">₹${data.net_earnings.toFixed(2)}</p>
            </div>
        </div>
        <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #e5e7eb;">
            <p class="muted"><strong>Session Count:</strong> ${data.from_sessions > 0 ? Math.round(data.from_sessions / 100) : 0} sessions | <strong>Leads Purchased:</strong> ${data.spent_on_leads > 0 ? Math.round(data.spent_on_leads / 20) : 0} leads</p>
        </div>
    `;
}

async function loadEarnings() {
    try {
        const data = await fetchJSON(`${apiBase}/therapists/me/earnings`);
        renderEarnings(data);
    } catch (err) {
        document.getElementById("earnings-card").innerHTML =
            `<p class="status err">Could not load earnings: ${err.message}</p>`;
        console.error("Error loading earnings:", err);
    }
}

async function init() {
    setupTabs();
    setupProfileForm();
    setupDocumentForm();
    await Promise.all([
        loadProfile(),
        loadLeads(),
        loadSessions(),
        loadEarnings()
    ]);
}

document.addEventListener("DOMContentLoaded", init);
