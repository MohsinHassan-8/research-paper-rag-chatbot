// Point this at your deployed FastAPI backend before going live.
const API_BASE_URL = "https://mohsin73-research-paper-rag-chatbot.hf.space/ask";

// ---------- Theme toggle ----------
const themeToggle = document.getElementById("theme-toggle");
const savedTheme = localStorage.getItem("theme") || "light";
document.documentElement.setAttribute("data-theme", savedTheme);

themeToggle.addEventListener("click", () => {
  const current = document.documentElement.getAttribute("data-theme");
  const next = current === "light" ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", next);
  localStorage.setItem("theme", next);
});

// ---------- Chat ----------
// Model mode is fixed to "cloud" for now -- the Local/Ollama toggle was
// removed from the UI until that backend path is actually wired up.
const modelMode = "cloud";
const thread = document.getElementById("thread");
const composer = document.getElementById("composer");
const queryInput = document.getElementById("query-input");
const sendBtn = document.getElementById("send-btn");

function scrollToBottom() {
  thread.scrollTop = thread.scrollHeight;
}

function addUserMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg msg-user";
  msg.innerHTML = `<div class="msg-bubble"></div>`;
  msg.querySelector(".msg-bubble").textContent = text;
  thread.appendChild(msg);
  scrollToBottom();
}

function addTypingIndicator() {
  const msg = document.createElement("div");
  msg.className = "msg msg-assistant";
  msg.id = "typing-indicator";
  msg.innerHTML = `
    <div class="msg-bubble">
      <span class="typing-dots"><span></span><span></span><span></span></span>
    </div>`;
  thread.appendChild(msg);
  scrollToBottom();
}

function removeTypingIndicator() {
  const el = document.getElementById("typing-indicator");
  if (el) el.remove();
}

function renderSources(sources) {
  const entries = Object.entries(sources || {});
  if (entries.length === 0) return "";

  const items = entries
    .map(([filename, pages]) => {
      const pageStr = Array.isArray(pages) ? pages.join(", ") : pages;
      return `<div class="source-item"><b>${escapeHtml(filename)}</b> — page${pages.length > 1 ? "s" : ""} ${escapeHtml(String(pageStr))}</div>`;
    })
    .join("");

  const id = "src-" + Math.random().toString(36).slice(2, 9);
  return `
    <div class="sources">
      <button class="sources-toggle" data-target="${id}">▸ Sources (${entries.length})</button>
      <div class="sources-list" id="${id}">${items}</div>
    </div>`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

function addAssistantMessage(answer, sources) {
  const msg = document.createElement("div");
  msg.className = "msg msg-assistant";
  msg.innerHTML = `
    <div>
      <div class="msg-bubble"></div>
      ${renderSources(sources)}
    </div>`;
  msg.querySelector(".msg-bubble").textContent = answer;
  thread.appendChild(msg);

  const toggle = msg.querySelector(".sources-toggle");
  if (toggle) {
    toggle.addEventListener("click", () => {
      const list = document.getElementById(toggle.dataset.target);
      const isOpen = list.classList.toggle("open");
      toggle.textContent = toggle.textContent.replace(/^./, isOpen ? "▾" : "▸");
    });
  }
  scrollToBottom();
}

function addErrorMessage(text) {
  const msg = document.createElement("div");
  msg.className = "msg msg-assistant error";
  msg.innerHTML = `<div class="msg-bubble"></div>`;
  msg.querySelector(".msg-bubble").textContent = text;
  thread.appendChild(msg);
  scrollToBottom();
}

async function sendQuery(query) {
  addUserMessage(query);
  queryInput.value = "";
  sendBtn.disabled = true;
  addTypingIndicator();

  try {
    const res = await fetch(`${API_BASE_URL}/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, model_mode: modelMode }),
    });

    const data = await res.json();
    removeTypingIndicator();

    if (!res.ok) {
      addErrorMessage(data.detail || "Something went wrong answering that. Try again.");
      return;
    }

    addAssistantMessage(data.answer, data.sources);
  } catch (err) {
    removeTypingIndicator();
    addErrorMessage(
      "Couldn't reach the backend. Make sure the API is running and API_BASE_URL in app.js points to it."
    );
  } finally {
    sendBtn.disabled = false;
    queryInput.focus();
  }
}

composer.addEventListener("submit", (e) => {
  e.preventDefault();
  const query = queryInput.value.trim();
  if (!query) return;
  sendQuery(query);
});

// ---------- Example chips ----------
document.querySelectorAll(".chip").forEach((chip) => {
  chip.addEventListener("click", () => {
    sendQuery(chip.dataset.q);
    document.querySelector(".chat-panel").scrollIntoView({ behavior: "smooth", block: "start" });
  });
});