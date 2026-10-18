const messages = document.querySelector("#messages");
const context = document.querySelector("#context");
const count = document.querySelector("#context-count");
const form = document.querySelector("#chat-form");
const input = document.querySelector("#message-input");
const actionCard = document.querySelector("#action-card");

function addMessage(text, who = "user") {
  const item = document.createElement("div");
  item.className = `message ${who}`;
  item.innerHTML =
    who === "assistant"
      ? `<span class="avatar">SC</span><div><p>${text}</p></div>`
      : `<div><p>${text}</p></div>`;
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
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
        return `<div class="context-item"><strong>${name}</strong><span>${type} · retrieved from FalkorDB</span></div>`;
      })
      .join("") ||
    '<div class="context-empty">No matching records found.</div>';
}
function renderAction(response) {
  actionCard.classList.toggle("hidden", !response.pending_action_id);
  if (!response.pending_action_id) return;
  actionCard.innerHTML = `<strong>Confirmation required</strong><p>${response.decision.reason}</p><button id="approve">Approve action</button> <button id="reject">Reject</button>`;
  document.querySelector("#approve").onclick = () => confirmAction(true);
  document.querySelector("#reject").onclick = () => confirmAction(false);
}
async function confirmAction(approved) {
  const id = actionCard.dataset.actionId;
  const response = await fetch(`/api/actions/${id}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approved }),
  });
  const result = await response.json();
  actionCard.innerHTML = `<strong>Action ${result.status}</strong><p>${result.result.message || "The action has been logged."}</p>`;
}
async function submit(text) {
  addMessage(text, "user");
  input.value = "";
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message: text, user_id: "u_001" }),
  });
  const data = await response.json();
  if (!response.ok) {
    addMessage(
      data.detail ||
        "The study graph is unavailable. Start FalkorDB on localhost:6379 and try again.",
      "assistant",
    );
    return;
  }
  addMessage(data.answer, "assistant");
  renderContext(data.context || []);
  renderAction(data);
  if (data.pending_action_id)
    actionCard.dataset.actionId = data.pending_action_id;
}
form.onsubmit = (event) => {
  event.preventDefault();
  submit(input.value.trim());
};
document
  .querySelectorAll("[data-prompt]")
  .forEach((button) => (button.onclick = () => submit(button.dataset.prompt)));
