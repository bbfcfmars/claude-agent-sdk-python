#!/usr/bin/env python3
"""
Minimal Web UI for Claude Agent SDK.

This example provides a simple browser-based interface to interact with Claude,
featuring:
- A clean prompt input field
- Submit button (or press Enter)
- Info button showing available commands and shortcodes
- Real-time streaming response display

Usage:
    python examples/minimal_web_ui.py

Then open http://localhost:8765 in your browser.

Environment Variables:
    PORT: Server port (default: 8765)
"""

import asyncio
import json
import os
import sys
import threading
import webbrowser
from http.server import HTTPServer, SimpleHTTPRequestHandler

# Add src to path for development
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from claude_agent_sdk import (
    AssistantMessage,
    ClaudeSDKClient,
    ResultMessage,
    TextBlock,
    ToolResultBlock,
    ToolUseBlock,
    UserMessage,
)

# Global client and event loop
client: ClaudeSDKClient | None = None
loop: asyncio.AbstractEventLoop | None = None

# Shortcodes and commands reference
SHORTCODES = {
    "General": {
        "/help": "Show available commands",
        "/clear": "Clear conversation history",
        "/compact": "Compact conversation to save context",
        "/quit": "Exit the session",
    },
    "File Operations": {
        "read <file>": "Ask Claude to read a file",
        "write <file>": "Ask Claude to create/edit a file",
        "search <pattern>": "Search for files or code",
    },
    "Code Tasks": {
        "explain": "Explain a code snippet or concept",
        "fix": "Fix a bug or issue",
        "refactor": "Improve code structure",
        "test": "Generate tests for code",
        "review": "Review code for issues",
    },
    "Tips": {
        "Be specific": "The more details you provide, the better the response",
        "Use context": "Reference files or previous conversation for better results",
        "Multi-step": "Break complex tasks into smaller steps",
    },
}

# HTML template for the UI
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Claude Agent SDK - Minimal UI</title>
    <style>
        :root {
            --bg-primary: #1a1a2e;
            --bg-secondary: #16213e;
            --bg-tertiary: #0f3460;
            --text-primary: #eaeaea;
            --text-secondary: #a0a0a0;
            --accent: #e94560;
            --accent-hover: #ff6b6b;
            --success: #4ecca3;
            --border-radius: 12px;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
        }

        header {
            background: var(--bg-secondary);
            padding: 16px 24px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--bg-tertiary);
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent);
        }

        .logo span {
            color: var(--text-primary);
            font-weight: 400;
        }

        .info-btn {
            background: var(--bg-tertiary);
            border: none;
            color: var(--text-primary);
            width: 40px;
            height: 40px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            font-weight: bold;
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .info-btn:hover {
            background: var(--accent);
            transform: scale(1.1);
        }

        main {
            flex: 1;
            display: flex;
            flex-direction: column;
            max-width: 900px;
            width: 100%;
            margin: 0 auto;
            padding: 24px;
        }

        #response-area {
            flex: 1;
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 20px;
            margin-bottom: 20px;
            overflow-y: auto;
            min-height: 300px;
            max-height: 60vh;
            white-space: pre-wrap;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
        }

        .message {
            margin-bottom: 16px;
            padding: 12px 16px;
            border-radius: 8px;
        }

        .user-message {
            background: var(--bg-tertiary);
            border-left: 3px solid var(--accent);
        }

        .assistant-message {
            background: rgba(78, 204, 163, 0.1);
            border-left: 3px solid var(--success);
        }

        .system-message {
            background: rgba(233, 69, 96, 0.1);
            color: var(--text-secondary);
            font-size: 0.85rem;
        }

        .message-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 6px;
            opacity: 0.7;
        }

        #input-area {
            display: flex;
            gap: 12px;
        }

        #prompt-input {
            flex: 1;
            background: var(--bg-secondary);
            border: 2px solid var(--bg-tertiary);
            color: var(--text-primary);
            padding: 16px 20px;
            border-radius: var(--border-radius);
            font-size: 1rem;
            transition: border-color 0.2s;
        }

        #prompt-input:focus {
            outline: none;
            border-color: var(--accent);
        }

        #prompt-input::placeholder {
            color: var(--text-secondary);
        }

        #submit-btn {
            background: var(--accent);
            color: white;
            border: none;
            padding: 16px 32px;
            border-radius: var(--border-radius);
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }

        #submit-btn:hover:not(:disabled) {
            background: var(--accent-hover);
            transform: translateY(-2px);
        }

        #submit-btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }

        /* Modal styles */
        .modal-overlay {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            justify-content: center;
            align-items: center;
        }

        .modal-overlay.active {
            display: flex;
        }

        .modal {
            background: var(--bg-secondary);
            border-radius: var(--border-radius);
            padding: 24px;
            max-width: 600px;
            max-height: 80vh;
            overflow-y: auto;
            margin: 20px;
        }

        .modal h2 {
            color: var(--accent);
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-close {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.5rem;
            cursor: pointer;
        }

        .modal-close:hover {
            color: var(--text-primary);
        }

        .shortcode-section {
            margin-bottom: 20px;
        }

        .shortcode-section h3 {
            color: var(--success);
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
            padding-bottom: 8px;
            border-bottom: 1px solid var(--bg-tertiary);
        }

        .shortcode-item {
            display: flex;
            justify-content: space-between;
            padding: 8px 12px;
            margin-bottom: 4px;
            background: var(--bg-primary);
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }

        .shortcode-item:hover {
            background: var(--bg-tertiary);
        }

        .shortcode-key {
            font-family: monospace;
            color: var(--accent);
            font-weight: 600;
        }

        .shortcode-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
        }

        .status-bar {
            padding: 8px 24px;
            background: var(--bg-secondary);
            border-top: 1px solid var(--bg-tertiary);
            font-size: 0.85rem;
            color: var(--text-secondary);
            display: flex;
            justify-content: space-between;
        }

        .status-indicator {
            display: flex;
            align-items: center;
            gap: 8px;
        }

        .status-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: var(--success);
        }

        .status-dot.loading {
            background: var(--accent);
            animation: pulse 1s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        /* Typing indicator */
        .typing-indicator {
            display: none;
            padding: 12px;
            background: rgba(78, 204, 163, 0.1);
            border-radius: 8px;
            margin-bottom: 16px;
        }

        .typing-indicator.active {
            display: flex;
            gap: 4px;
        }

        .typing-dot {
            width: 8px;
            height: 8px;
            background: var(--success);
            border-radius: 50%;
            animation: typing 1.4s infinite;
        }

        .typing-dot:nth-child(2) { animation-delay: 0.2s; }
        .typing-dot:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-4px); }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">Claude <span>Agent SDK</span></div>
        <button class="info-btn" onclick="toggleModal()" title="Show commands & shortcuts">ℹ</button>
    </header>

    <main>
        <div id="response-area">
            <div class="message system-message">
                <div class="message-label">Welcome</div>
                Welcome to Claude Agent SDK! Type your prompt below and press Enter or click Send.
                <br><br>
                💡 Click the <strong>ℹ</strong> button for helpful commands and shortcuts.
            </div>
        </div>

        <div id="input-area">
            <input
                type="text"
                id="prompt-input"
                placeholder="Ask Claude anything... (e.g., 'explain how async/await works')"
                autocomplete="off"
            >
            <button id="submit-btn" onclick="sendPrompt()">Send</button>
        </div>
    </main>

    <div class="status-bar">
        <div class="status-indicator">
            <div class="status-dot" id="status-dot"></div>
            <span id="status-text">Ready</span>
        </div>
        <div>Press <kbd>Enter</kbd> to send • <kbd>Shift+Enter</kbd> for new line</div>
    </div>

    <!-- Info Modal -->
    <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <h2>
                Commands & Shortcuts
                <button class="modal-close" onclick="toggleModal()">×</button>
            </h2>
            <div id="shortcodes-content"></div>
        </div>
    </div>

    <script>
        const responseArea = document.getElementById('response-area');
        const promptInput = document.getElementById('prompt-input');
        const submitBtn = document.getElementById('submit-btn');
        const statusDot = document.getElementById('status-dot');
        const statusText = document.getElementById('status-text');
        const modalOverlay = document.getElementById('modal-overlay');
        const shortcodesContent = document.getElementById('shortcodes-content');

        // Initialize shortcodes
        const shortcodes = SHORTCODES_DATA;

        function initShortcodes() {
            let html = '';
            for (const [section, items] of Object.entries(shortcodes)) {
                html += `<div class="shortcode-section">
                    <h3>${section}</h3>`;
                for (const [key, desc] of Object.entries(items)) {
                    html += `<div class="shortcode-item" onclick="useShortcode('${key}')">
                        <span class="shortcode-key">${key}</span>
                        <span class="shortcode-desc">${desc}</span>
                    </div>`;
                }
                html += '</div>';
            }
            shortcodesContent.innerHTML = html;
        }

        function useShortcode(shortcode) {
            if (!shortcode.startsWith('/') && !shortcode.includes(' ')) {
                promptInput.value = shortcode + ' ';
            } else if (shortcode.includes('<')) {
                promptInput.value = shortcode.split('<')[0];
            } else {
                promptInput.value = shortcode;
            }
            toggleModal();
            promptInput.focus();
        }

        function toggleModal() {
            modalOverlay.classList.toggle('active');
        }

        function closeModal(event) {
            if (event.target === modalOverlay) {
                toggleModal();
            }
        }

        function setLoading(loading) {
            submitBtn.disabled = loading;
            promptInput.disabled = loading;
            statusDot.classList.toggle('loading', loading);
            statusText.textContent = loading ? 'Claude is thinking...' : 'Ready';
        }

        function addMessage(content, type = 'assistant') {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${type}-message`;

            const labelMap = {
                'user': 'You',
                'assistant': 'Claude',
                'system': 'System'
            };

            messageDiv.innerHTML = `
                <div class="message-label">${labelMap[type] || type}</div>
                ${escapeHtml(content)}
            `;

            responseArea.appendChild(messageDiv);
            responseArea.scrollTop = responseArea.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function sendPrompt() {
            const prompt = promptInput.value.trim();
            if (!prompt) return;

            // Add user message
            addMessage(prompt, 'user');
            promptInput.value = '';
            setLoading(true);

            try {
                const response = await fetch('/query', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                    body: 'prompt=' + encodeURIComponent(prompt)
                });

                const data = await response.json();

                if (data.error) {
                    addMessage('Error: ' + data.error, 'system');
                } else if (data.response) {
                    addMessage(data.response, 'assistant');
                }
            } catch (error) {
                addMessage('Connection error: ' + error.message, 'system');
            } finally {
                setLoading(false);
            }
        }

        // Handle Enter key
        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPrompt();
            }
        });

        // Initialize
        initShortcodes();
        promptInput.focus();
    </script>
</body>
</html>
""".replace("SHORTCODES_DATA", json.dumps(SHORTCODES))


class RequestHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for the minimal web UI."""

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default logging."""
        pass

    def do_GET(self) -> None:
        """Handle GET requests."""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        else:
            self.send_error(404)

    def do_POST(self) -> None:
        """Handle POST requests for queries."""
        if self.path == "/query":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length).decode()
            params = parse_qs(post_data)
            prompt = params.get("prompt", [""])[0]

            if not prompt:
                self._send_json({"error": "No prompt provided"})
                return

            # Run query in the async loop
            if loop:
                future = asyncio.run_coroutine_threadsafe(
                    self._query_claude(prompt), loop
                )
                try:
                    result = future.result(timeout=120)  # 120 seconds (2 minutes)
                    self._send_json(result)
                except TimeoutError:
                    self._send_json({"error": "Request timed out"})
                except Exception as e:
                    self._send_json({"error": str(e)})
            else:
                self._send_json({"error": "Server not initialized"})
        else:
            self.send_error(404)

    def _send_json(self, data: dict[str, Any]) -> None:
        """Send JSON response."""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    async def _query_claude(self, prompt: str) -> dict[str, Any]:
        """Query Claude and return the response."""
        global client

        try:
            if client is None:
                client = ClaudeSDKClient()
                await client.connect()

            await client.query(prompt)

            response_text = []
            async for msg in client.receive_response():
                if isinstance(msg, AssistantMessage):
                    for block in msg.content:
                        if isinstance(block, TextBlock):
                            response_text.append(block.text)
                        elif isinstance(block, ToolUseBlock):
                            response_text.append(f"[Using tool: {block.name}]")
                elif isinstance(msg, UserMessage):
                    content_blocks = (
                        msg.content if isinstance(msg.content, list) else []
                    )
                    for block in content_blocks:
                        if isinstance(block, ToolResultBlock) and block.content:
                            result_preview = str(block.content)[:200]
                            if len(str(block.content)) > 200:
                                result_preview += "..."
                            response_text.append(f"[Tool result: {result_preview}]")
                elif isinstance(msg, ResultMessage):
                    break

            return {
                "response": "\n".join(response_text)
                if response_text
                else "No response received."
            }

        except Exception as e:
            return {"error": str(e)}


def run_server(port: int) -> None:
    """Run the HTTP server."""
    server = HTTPServer(("localhost", port), RequestHandler)
    print(f"Server running on http://localhost:{port}")
    server.serve_forever()


async def async_main() -> None:
    """Async main function to manage the event loop."""
    global loop
    loop = asyncio.get_event_loop()

    # Wait forever (server runs in separate thread)
    while True:
        await asyncio.sleep(3600)


def main() -> None:
    """Main entry point."""
    port = int(os.environ.get("PORT", "8765"))

    print("=" * 60)
    print("Claude Agent SDK - Minimal Web UI")
    print("=" * 60)
    print()
    print("Starting server...")
    print()

    # Start server in separate thread
    server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    server_thread.start()

    print(f"✓ Server started on http://localhost:{port}")
    print()
    print("Tips:")
    print("  • Type your prompt in the input field and press Enter")
    print("  • Click the ℹ button for helpful commands and shortcuts")
    print("  • Press Ctrl+C to stop the server")
    print()

    # Open browser
    webbrowser.open(f"http://localhost:{port}")

    # Run async loop in main thread
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nShutting down...")
        if client:
            asyncio.run(client.disconnect())


if __name__ == "__main__":
    main()
