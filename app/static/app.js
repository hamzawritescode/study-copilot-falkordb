const messages = document.querySelector("#messages");
const context = document.querySelector("#context");
const count = document.querySelector("#context-count");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const actionCard = document.querySelector("#action-card");
const submitButton = form.querySelector("button[type='submit']");
const graphStatus = document.querySelector("#graph-status");

function escapeHtml(value) {
  return String(value).replace(
    /[&<>"']/g,
    (character) =>
      ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;",
      })[character],
  );
}

function addMessage(text, who = "user") {
  const item = document.createElement("div");
  item.className = `message ${who}`;
  item.innerHTML =
    who === "assistant"
      ? `<span class="avatar">SC</span><div><p>${escapeHtml(text)}</p></div>`
      : `<div><p>${escapeHtml(text)}</p></div>`;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
}

function setGraphStatus(online, label) {
  graphStatus.lastChild.textContent = ` ${label}`;
  graphStatus.style.color = online ? "#52704d" : "#a25a39";
  graphStatus.querySelector("i").style.background = online
    ? "#70ba4b"
    : "#dd7c2f";
}

async function checkHealth() {
  try {
    const response = await fetch("/health");
    const data = await response.json();
    setGraphStatus(
      response.ok && data.ok,
      response.ok && data.ok ? "graph online" : "graph unavailable",
    );
  } catch {
    setGraphStatus(false, "graph unavailable");
  }
}

function setLoading(loading) {
  submitButton.disabled = loading;
  input.disabled = loading;
  submitButton.textContent = loading ? "Thinking..." : "Send";
}

function renderContext(rows) {
  count.textContent = `${rows.length} graph records`;
  context.innerHTML =
    rows
      .slice(0, 8)
      .map((row) => {
        const candidate = row.candidate || row.t || row.g || row.resource || {};
        const name =
          candidate.name ||
          candidate.title ||
          candidate.id ||
          "Connected record";
        const type = candidate.name
          ? "Topic"
          : candidate.title
            ? "Resource"
            : "Graph node";
        return `<div class="context-item"><strong>${escapeHtml(name)}</strong><span>${escapeHtml(type)} · retrieved from FalkorDB</span></div>`;
      })
      .join("") ||
    '<div class="context-empty">No matching records found.</div>';
}
function renderAction(response) {
  actionCard.classList.toggle("hidden", !response.pending_action_id);
  if (!response.pending_action_id) {
    delete actionCard.dataset.actionId;
    return;
  }

  function renderEvidence(response) {
    const evidence = response.evidence;
    const blocked = response.blocked_candidates || [];
    const panel = document.querySelector("#evidence");
    if (!panel) return;
    if (!evidence && !blocked.length) {
      panel.innerHTML = "";
      panel.classList.add("hidden");
      return;
    }
    const pathMarkup = (paths) =>
      (paths || [])
        .map((path) => {
          const nodes = (path.nodes || []).map((node) => node.name || node.title || node.id || "node");
          const relationships = path.relationships || [];
          const parts = [];
          nodes.forEach((node, index) => {
            parts.push(`<span>${escapeHtml(node)}</span>`);
            if (relationships[index]) parts.push(`<b>→ ${escapeHtml(relationships[index])} →</b>`);
          });
          return `<div class="evidence-path">${parts.join(" ")}</div>`;
        })
        .join("");
    const blockedMarkup = blocked
      .map(
        (item) =>
          `<li><strong>${escapeHtml(item.topic.name || item.topic.id)}</strong><span>${escapeHtml(item.reason)}</span>${pathMarkup(item.prerequisite_path)}</li>`,
      )
      .join("");
    panel.classList.remove("hidden");
    panel.innerHTML = `
      ${evidence ? `<h3>Why this topic?</h3>
        <p>${escapeHtml(evidence.reason)}</p>
        <dl>
          <dt>Available time</dt><dd>${escapeHtml(evidence.available_time ?? "unknown")} minutes</dd>
          <dt>Progress</dt><dd>${(evidence.user_progress || []).map((item) => `${escapeHtml(item.topic?.name || item.topic?.id || "topic")}: ${escapeHtml(item.mastery ?? "n/a")}`).join(", ") || "No progress record"}</dd>
        </dl>
        ${pathMarkup(evidence.prerequisite_path)}
        <p class="connected">${(evidence.connected_resources || []).map((item) => `Resource: ${escapeHtml(item.title)}`).join(" · ")} ${(evidence.connected_quizzes || []).map((item) => `Quiz: ${escapeHtml(item.title)}`).join(" · ")}</p>` : ""}
      ${blockedMarkup ? `<h3>Blocked candidates</h3><ul>${blockedMarkup}</ul>` : ""}
    `;
  }
  actionCard.dataset.actionId = response.pending_action_id;
  actionCard.innerHTML = `<strong>Confirmation required</strong><p>${escapeHtml(response.decision.reason)}</p><button id="approve">Approve action</button> <button id="reject">Reject</button>`;
  document.querySelector("#approve").onclick = () => confirmAction(true);
  document.querySelector("#reject").onclick = () => confirmAction(false);
}
async function confirmAction(approved) {
  const id = actionCard.dataset.actionId;
  try {
    const response = await fetch(`/api/actions/${id}/confirm`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ approved }),
    });
    const result = await response.json();
    if (!response.ok)
      throw new Error(result.detail || "The action could not be completed.");
    actionCard.innerHTML = `<strong>Action ${escapeHtml(result.status)}</strong><p>${escapeHtml(result.result.message || "The action has been logged.")}</p>`;
  } catch (error) {
    actionCard.innerHTML = `<strong>Action unavailable</strong><p>${escapeHtml(error.message)}</p>`;
  }
}
async function submit(text) {
  if (!text || submitButton.disabled) return;
  addMessage(text, "user");
  input.value = "";
  setLoading(true);
  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: text, user_id: "u_001" }),
    });
    const data = await response.json();
    if (!response.ok) {
      addMessage(
        data.detail ||
          "The study graph is unavailable. Start FalkorDB and try again.",
        "assistant",
      );
      setGraphStatus(false, "graph unavailable");
      return;
    }
    addMessage(data.answer, "assistant");
    renderContext(data.context || []);
    renderAction(data);
    renderEvidence(data);
  } catch {
    addMessage(
      "I could not reach the Study Copilot API. Check that the backend is running and try again.",
      "assistant",
    );
  } finally {
    setLoading(false);
  }
}
form.onsubmit = (event) => {
  event.preventDefault();
  submit(input.value.trim());
};
document
  .querySelectorAll("[data-prompt]")
  .forEach((button) => (button.onclick = () => submit(button.dataset.prompt)));

checkHealth();
