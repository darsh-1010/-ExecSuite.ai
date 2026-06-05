// AgenticOrg Frontend Application Logic

document.addEventListener("DOMContentLoaded", () => {
    // UI Elements
    const systemStatusPill = document.getElementById("system-status-pill");
    const systemStatusText = document.getElementById("system-status-text");
    const activeLlmText = document.getElementById("active-llm-text");
    
    const runTaskBtn = document.getElementById("run-task-btn");
    const taskInput = document.getElementById("task-input");
    const workflowSelect = document.getElementById("workflow-select");
    const departmentSelect = document.getElementById("department-select");
    const agentRosterList = document.getElementById("agent-roster-list");
    
    const chatMessagesContainer = document.getElementById("chat-messages-container");
    const consoleLogsList = document.getElementById("console-logs-list");
    const workspaceFileList = document.getElementById("workspace-file-list");
    
    const tabFilesBtn = document.getElementById("tab-files-btn");
    const tabConsoleBtn = document.getElementById("tab-console-btn");
    const tabFilesContent = document.getElementById("tab-files-content");
    const tabConsoleContent = document.getElementById("tab-console-content");
    
    const fileViewerBody = document.getElementById("file-viewer-body");
    const openFilenameText = document.getElementById("open-filename-text");
    const copyFileBtn = document.getElementById("copy-file-btn");
    
    const openSettingsBtn = document.getElementById("open-settings-btn");
    const closeSettingsBtn = document.getElementById("close-settings-btn");
    const cancelSettingsBtn = document.getElementById("cancel-settings-btn");
    const settingsModal = document.getElementById("settings-modal");
    const configForm = document.getElementById("config-form");
    
    const providerSelect = document.getElementById("provider-select");
    const modelInput = document.getElementById("model-input");
    
    // API Key inputs
    const keyInputs = {
        gemini: document.getElementById("key-gemini"),
        groq: document.getElementById("key-groq"),
        openrouter: document.getElementById("key-openrouter"),
        cohere: document.getElementById("key-cohere"),
        openai: document.getElementById("key-openai")
    };
    
    // API Key status dots
    const keyStatusIndicators = {
        gemini: document.getElementById("status-key-gemini"),
        groq: document.getElementById("status-key-groq"),
        openrouter: document.getElementById("status-key-openrouter"),
        cohere: document.getElementById("status-key-cohere"),
        openai: document.getElementById("status-key-openai")
    };

    // State Variables
    let isRunning = false;
    let selectedFile = null;
    let eventSource = null;

    // Initialize Lucide Icons
    lucide.createIcons();

    // Fetch initial state on load
    fetchState();
    
    // Connect to SSE Stream
    connectEventStream();

    // --- Event Listeners ---

    // Tabs
    tabFilesBtn.addEventListener("click", () => {
        tabFilesBtn.classList.add("active");
        tabConsoleBtn.classList.remove("active");
        tabFilesContent.classList.remove("hidden");
        tabConsoleContent.classList.add("hidden");
    });

    tabConsoleBtn.addEventListener("click", () => {
        tabConsoleBtn.classList.add("active");
        tabFilesBtn.classList.remove("active");
        tabConsoleContent.classList.remove("hidden");
        tabFilesContent.classList.add("hidden");
    });

    // Task Execution
    runTaskBtn.addEventListener("click", runTask);
    taskInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault();
            runTask();
        }
    });

    // Department Selector Change
    departmentSelect.addEventListener("change", async () => {
        try {
            const response = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    default_department: departmentSelect.value
                })
            });
            if (!response.ok) throw new Error("Failed to update department config");
            fetchState();
        } catch (err) {
            console.error("Error setting department:", err);
        }
    });

    // Settings Modal
    openSettingsBtn.addEventListener("click", () => {
        settingsModal.classList.remove("hidden");
    });

    const closeModal = () => {
        settingsModal.classList.add("hidden");
        configForm.reset();
        fetchState(); // reload key config states without saving
    };
    closeSettingsBtn.addEventListener("click", closeModal);
    cancelSettingsBtn.addEventListener("click", closeModal);

    configForm.addEventListener("submit", saveConfiguration);

    // Copy file contents
    copyFileBtn.addEventListener("click", () => {
        if (!selectedFile) return;
        const codeElement = fileViewerBody.querySelector("code");
        const textToCopy = codeElement ? codeElement.textContent : fileViewerBody.textContent;
        navigator.clipboard.writeText(textToCopy).then(() => {
            const originalHTML = copyFileBtn.innerHTML;
            copyFileBtn.innerHTML = `<i data-lucide="check" style="color: var(--success)"></i>`;
            lucide.createIcons();
            setTimeout(() => {
                copyFileBtn.innerHTML = originalHTML;
                lucide.createIcons();
            }, 2000);
        });
    });

    // --- SSE Event Stream ---

    function connectEventStream() {
        if (eventSource) {
            eventSource.close();
        }
        
        eventSource = new EventSource("/api/stream");
        
        eventSource.onmessage = (event) => {
            try {
                const payload = JSON.parse(event.data);
                handleStreamEvent(payload);
            } catch (err) {
                console.error("Error parsing SSE data:", err);
            }
        };

        eventSource.onerror = (err) => {
            console.error("SSE Connection error. Reconnecting...");
            eventSource.close();
            setTimeout(connectEventStream, 3000);
        };
    }

    function handleStreamEvent(payload) {
        const { event, data } = payload;
        
        if (event === "connected") {
            console.log("SSE connected and listening.");
            return;
        }

        if (event === "message") {
            appendChatMessage(data);
            return;
        }

        if (event === "event") {
            appendConsoleLog(data);
            handleSystemEvent(data);
            return;
        }

        if (event === "file") {
            fetchFiles(); // Refresh file explorer
            return;
        }
        
        if (event === "blackboard") {
            console.log("Blackboard updated:", data);
        }
    }

    // --- State Fetching & Sync ---

    async function fetchState() {
        try {
            const response = await fetch("/api/state");
            const data = await response.json();
            
            // Set LLM Display
            let providerName = data.current_provider;
            if (providerName) {
                providerName = providerName.charAt(0).toUpperCase() + providerName.slice(1);
                activeLlmText.textContent = `${providerName} (${data.current_model})`;
                providerSelect.value = data.current_provider;
                modelInput.value = data.current_model;
            } else {
                activeLlmText.textContent = "No LLM Configured";
            }

            // Update Status Pill
            updateStatusPill(data.is_running);

            // Configure API key indicators
            for (const [provider, isConfigured] of Object.entries(data.keys_configured)) {
                if (keyStatusIndicators[provider]) {
                    if (isConfigured) {
                        keyStatusIndicators[provider].classList.add("configured");
                    } else {
                        keyStatusIndicators[provider].classList.remove("configured");
                    }
                }
            }

            // Load historical messages if we are idle (fresh reload)
            if (data.messages && data.messages.length > 0 && chatMessagesContainer.querySelector(".welcome-message")) {
                chatMessagesContainer.innerHTML = "";
                data.messages.forEach(appendChatMessage);
            }

            // Load historical logs
            if (data.logs && data.logs.length > 0 && consoleLogsList.innerHTML.trim() === "") {
                data.logs.forEach(appendConsoleLog);
            }

            // Load files
            renderFileList(data.files);
            
            // Render available departments
            if (departmentSelect && data.available_departments) {
                if (departmentSelect.children.length === 0) {
                    departmentSelect.innerHTML = "";
                    for (const [key, name] of Object.entries(data.available_departments)) {
                        const opt = document.createElement("option");
                        opt.value = key;
                        opt.textContent = name;
                        departmentSelect.appendChild(opt);
                    }
                }
                departmentSelect.value = data.active_department;
            }

            // Render active agents roster
            if (agentRosterList && data.active_agents) {
                renderAgentRoster(data.active_agents);
            }
            
        } catch (err) {
            console.error("Failed to fetch app state:", err);
        }
    }

    async function fetchFiles() {
        try {
            const response = await fetch("/api/state");
            const data = await response.json();
            renderFileList(data.files);
        } catch (err) {
            console.error("Failed to fetch files list:", err);
        }
    }

    function renderFileList(files) {
        if (!files || files.length === 0) {
            workspaceFileList.innerHTML = `<li class="empty-list-msg">No files generated yet.</li>`;
            return;
        }

        workspaceFileList.innerHTML = "";
        files.forEach(file => {
            const li = document.createElement("li");
            li.className = "file-item";
            if (selectedFile === file.name) {
                li.classList.add("active-file");
            }
            
            // Detect file icon based on extension
            let icon = "file-text";
            const ext = file.name.split('.').pop().toLowerCase();
            if (["html", "htm"].includes(ext)) icon = "code-2";
            else if (["css"].includes(ext)) icon = "brush";
            else if (["js", "ts"].includes(ext)) icon = "binary";
            else if (["json"].includes(ext)) icon = "database";
            else if (["md"].includes(ext)) icon = "file-spreadsheet";
            
            li.innerHTML = `<i data-lucide="${icon}"></i> <span>${file.name}</span>`;
            li.addEventListener("click", () => selectFile(file.name));
            workspaceFileList.appendChild(li);
        });
        
        lucide.createIcons();
    }

    async function selectFile(filename) {
        selectedFile = filename;
        
        // Highlight active item
        const items = workspaceFileList.querySelectorAll(".file-item");
        items.forEach(item => {
            const spanText = item.querySelector("span").textContent;
            if (spanText === filename) {
                item.classList.add("active-file");
            } else {
                item.classList.remove("active-file");
            }
        });

        openFilenameText.innerHTML = `<i data-lucide="file-text"></i> ${filename}`;
        fileViewerBody.textContent = "Loading file content...";
        copyFileBtn.style.display = "none";
        lucide.createIcons();

        try {
            const response = await fetch(`/api/files/read?path=${encodeURIComponent(filename)}`);
            if (!response.ok) {
                throw new Error("Could not read file");
            }
            const data = await response.json();
            
            // Render file content with clean text formatting
            fileViewerBody.innerHTML = "";
            const code = document.createElement("code");
            code.textContent = data.content;
            
            // Basic syntax highlighting class based on extension
            const ext = filename.split('.').pop().toLowerCase();
            code.className = `language-${ext}`;
            
            fileViewerBody.appendChild(code);
            copyFileBtn.style.display = "flex";
        } catch (err) {
            fileViewerBody.textContent = `Error loading file: ${err.message}`;
        }
    }

    function getRoleThemeClass(roleStr) {
        const r = roleStr.toLowerCase();
        if (r.includes("ceo") || r.includes("director") || r.includes("manager") || r.includes("lead product marketer") || r.includes("product marketer")) {
            return "ceo";
        }
        if (r.includes("cfo") || r.includes("researcher") || r.includes("architect") || r.includes("copywriter")) {
            return "cfo";
        }
        if (r.includes("cmo") || r.includes("social") || r.includes("outreach") || r.includes("qa")) {
            return "cmo";
        }
        return "dev";
    }

    function renderAgentRoster(activeAgents) {
        if (!agentRosterList) return;
        agentRosterList.innerHTML = "";
        
        activeAgents.forEach(agent => {
            const item = document.createElement("div");
            item.className = "agent-item";
            item.id = `agent-${agent.role_id}`;
            
            const initial = agent.name.charAt(0);
            const themeClass = getRoleThemeClass(agent.role_id);
            
            item.innerHTML = `
                <div class="agent-avatar ${themeClass}">${initial}</div>
                <div class="agent-info">
                    <div class="agent-name">${agent.name}</div>
                    <div class="agent-role">${agent.role}</div>
                </div>
                <div class="agent-status idle">Idle</div>
            `;
            agentRosterList.appendChild(item);
        });
    }

    // --- UI Helper Functions ---

    function updateStatusPill(running) {
        isRunning = running;
        if (running) {
            systemStatusPill.className = "status-pill running";
            systemStatusText.textContent = "Running";
            runTaskBtn.disabled = true;
            runTaskBtn.innerHTML = `<i data-lucide="loader" class="btn-icon animate-spin"></i> Executing...`;
        } else {
            systemStatusPill.className = "status-pill idler";
            systemStatusText.textContent = "Idle";
            runTaskBtn.disabled = false;
            runTaskBtn.innerHTML = `<i data-lucide="play" class="btn-icon"></i> Run Task`;
            
            // Ensure all agents go back to idle status in DOM
            const statuses = document.querySelectorAll(".agent-status");
            statuses.forEach(s => {
                s.className = "agent-status idle";
                s.textContent = "Idle";
            });
            
            const activeItems = document.querySelectorAll(".agent-item");
            activeItems.forEach(item => item.classList.remove("active-agent"));
        }
        lucide.createIcons();
    }

    function appendChatMessage(msg) {
        // Remove welcome message if still there
        const welcome = chatMessagesContainer.querySelector(".welcome-message");
        if (welcome) {
            chatMessagesContainer.innerHTML = "";
        }

        // Check if message bubble already exists (avoid duplicates on reconnect)
        if (document.getElementById(`msg-${msg.index}`)) {
            return;
        }

        const bubble = document.createElement("div");
        const senderRoleClass = msg.role.replace(/\s+/g, "-");
        bubble.className = `message-bubble ${senderRoleClass}`;
        bubble.id = `msg-${msg.index}`;

        // Dynamically color border-left based on theme
        const theme = getRoleThemeClass(msg.role);
        let borderColor = "#8b5cf6"; // default purple
        if (theme === "ceo") borderColor = "#7c3aed";
        else if (theme === "cfo") borderColor = "#059669";
        else if (theme === "cmo") borderColor = "#d97706";
        else if (theme === "dev") borderColor = "#2563eb";
        bubble.style.borderLeft = `3px solid ${borderColor}`;

        const initial = msg.sender.charAt(0);
        const avatarClass = getRoleThemeClass(msg.role);

        // Format message body (bold headers, code snippets)
        let formattedContent = formatMarkdown(msg.content);

        bubble.innerHTML = `
            <div class="bubble-avatar ${avatarClass}">${initial}</div>
            <div class="message-content">
                <div class="message-sender">
                    ${msg.sender} <span class="sender-role">${msg.role}</span>
                </div>
                <div class="message-text">${formattedContent}</div>
            </div>
        `;

        chatMessagesContainer.appendChild(bubble);
        chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
    }

    function appendConsoleLog(log) {
        // Check if log entry already exists
        if (document.getElementById(`log-${log.time}`)) {
            return;
        }

        const entry = document.createElement("div");
        entry.className = `console-entry ${log.type}`;
        entry.id = `log-${log.time}`;
        
        // Formatted timestamp index (like [STEP 01])
        const stepNum = String(log.time + 1).padStart(2, '0');
        
        entry.innerHTML = `
            <span class="log-time">[STEP ${stepNum}]</span>
            <span class="log-msg">${log.message}</span>
        `;
        
        consoleLogsList.appendChild(entry);
        consoleLogsList.scrollTop = consoleLogsList.scrollHeight;
    }

    function handleSystemEvent(log) {
        // Remove active class from all agent items
        const agentItems = document.querySelectorAll(".agent-item");
        agentItems.forEach(item => item.classList.remove("active-agent"));
        
        const statuses = document.querySelectorAll(".agent-status");
        statuses.forEach(s => {
            s.className = "agent-status idle";
            s.textContent = "Idle";
        });

        if (log.type === "agent_turn" || log.type === "phase_start") {
            const roleId = log.details?.role;
            if (roleId) {
                const element = document.getElementById(`agent-${roleId}`);
                if (element) {
                    element.classList.add("active-agent");
                    const statusText = element.querySelector(".agent-status");
                    if (statusText) {
                        const isSpeaking = log.type === "agent_turn";
                        statusText.className = isSpeaking ? "agent-status speaking" : "agent-status thinking";
                        statusText.textContent = isSpeaking ? "Speaking..." : "Thinking...";
                    }
                }
            }
        }
        
        if (log.type === "task_start") {
            updateStatusPill(true);
        }
        
        if (log.type === "task_end" || log.type === "task_error") {
            updateStatusPill(false);
            fetchFiles(); // final sync
        }
    }

    // --- Task Execution ---

    async function runTask() {
        const taskText = taskInput.value.trim();
        if (!taskText) return;
        if (isRunning) return;

        updateStatusPill(true);
        chatMessagesContainer.innerHTML = `<div class="welcome-message"><i data-lucide="loader" class="welcome-icon animate-spin"></i><h3>Initiating Agentic Team</h3><p>Starting up communication channels and loading personas...</p></div>`;
        consoleLogsList.innerHTML = "";
        workspaceFileList.innerHTML = `<li class="empty-list-msg">Waiting for code outputs...</li>`;
        selectedFile = null;
        fileViewerBody.textContent = "Select a generated file from the left panel to inspect its contents. As agents work, code and documents will appear here.";
        openFilenameText.innerHTML = `<i data-lucide="file-text"></i> Select a file to view`;
        copyFileBtn.style.display = "none";
        lucide.createIcons();

        try {
            const response = await fetch("/api/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    task: taskText,
                    workflow: workflowSelect.value,
                    department: departmentSelect.value,
                    provider: providerSelect.value,
                    model: modelInput.value || null
                })
            });

            if (!response.ok) {
                throw new Error("Failed to start task");
            }
            
            taskInput.value = ""; // clear input
        } catch (err) {
            console.error("Error executing task:", err);
            updateStatusPill(false);
            chatMessagesContainer.innerHTML = `
                <div class="welcome-message" style="color: var(--danger)">
                    <i data-lucide="alert-triangle" class="welcome-icon"></i>
                    <h3>Launch Failed</h3>
                    <p>${err.message}. Make sure the backend server is running and API keys are set.</p>
                </div>
            `;
            lucide.createIcons();
        }
    }

    // --- Settings Configuration ---

    async function saveConfiguration(e) {
        e.preventDefault();
        
        const payload = {
            default_provider: providerSelect.value,
            default_model: modelInput.value.trim() || null,
            gemini_key: keyInputs.gemini.value.trim() || null,
            groq_key: keyInputs.groq.value.trim() || null,
            openrouter_key: keyInputs.openrouter.value.trim() || null,
            cohere_key: keyInputs.cohere.value.trim() || null,
            openai_key: keyInputs.openai.value.trim() || null
        };

        try {
            const response = await fetch("/api/config", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!response.ok) throw new Error("Failed to save config");
            
            const data = await response.json();
            console.log("Configuration saved successfully.");
            
            settingsModal.classList.add("hidden");
            configForm.reset();
            fetchState(); // refresh display
            
        } catch (err) {
            alert(`Error saving configuration: ${err.message}`);
        }
    }

    // --- Basic Markdown Helper ---
    function formatMarkdown(text) {
        if (!text) return "";
        let escaped = text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;");

        // Code blocks: ```lang ... ```
        escaped = escaped.replace(/```([a-zA-Z0-9]*)\n([\s\S]*?)\n```/g, (match, lang, code) => {
            return `<pre><code class="language-${lang}">${code}</code></pre>`;
        });

        // Inline code: `code`
        escaped = escaped.replace(/`([^`]+)`/g, "<code>$1</code>");

        // Bold headers or lists
        escaped = escaped.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");

        // Headers: ### Header
        escaped = escaped.replace(/^### (.*$)/gim, "<h4>$1</h4>");
        escaped = escaped.replace(/^## (.*$)/gim, "<h3>$1</h3>");
        escaped = escaped.replace(/^# (.*$)/gim, "<h2>$1</h2>");

        return escaped;
    }
});
