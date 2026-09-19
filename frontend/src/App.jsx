import { useEffect, useRef, useState } from "react";
import "./App.css";

const API_URL = "http://127.0.0.1:8000";

function App() {
  const [youtubeUrl, setYoutubeUrl] = useState("");
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);

  const [sourceLoaded, setSourceLoaded] = useState(false);
  const [sourceName, setSourceName] = useState("");
  const [sourceType, setSourceType] = useState("");

  const [loadingYoutube, setLoadingYoutube] = useState(false);
  const [loadingPdf, setLoadingPdf] = useState(false);
  const [loadingChat, setLoadingChat] = useState(false);

  const [copiedIndex, setCopiedIndex] = useState(null);

  // Sidebar
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);
  const fileInputRef = useRef(null);

  // ==========================================
  // AUTO SCROLL
  // ==========================================

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({
      behavior: "smooth",
    });
  }, [messages, loadingChat]);

  // ==========================================
  // SIDEBAR
  // ==========================================

  const toggleSidebar = () => {
    setSidebarCollapsed((previous) => !previous);
  };

  // ==========================================
  // TEXTAREA RESIZE
  // ==========================================

  const resizeTextarea = () => {
    const textarea = textareaRef.current;

    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height =
      Math.min(textarea.scrollHeight, 180) + "px";
  };

  // ==========================================
  // NEW CHAT
  // ==========================================

  const newChat = () => {
    setMessages([]);
    setQuestion("");
    setSourceLoaded(false);
    setSourceName("");
    setSourceType("");
    setYoutubeUrl("");
  };

  // ==========================================
  // YOUTUBE ID
  // ==========================================

  const extractYoutubeId = (value) => {
    try {
      const url = new URL(value.trim());

      if (url.hostname.includes("youtube.com")) {
        return url.searchParams.get("v");
      }

      if (url.hostname.includes("youtu.be")) {
        return url.pathname.substring(1);
      }

      return null;
    } catch {
      return null;
    }
  };

  // ==========================================
  // LOAD YOUTUBE
  // ==========================================

  const loadYoutube = async () => {
    const urlValue = youtubeUrl.trim();

    if (!urlValue) {
      alert("Please paste a YouTube URL.");
      return;
    }

    const videoId = extractYoutubeId(urlValue);

    if (!videoId) {
      alert("Please enter a valid YouTube URL.");
      return;
    }

    try {
      setLoadingYoutube(true);

      const response = await fetch(`${API_URL}/youtube`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          video_id: videoId,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        alert(
          data.error || "Unable to load YouTube video."
        );
        return;
      }

      setSourceLoaded(true);
      setSourceType("youtube");
      setSourceName("YouTube video");

      setMessages([
        {
          role: "assistant",
          content:
            "Your YouTube video is ready. Ask me anything about its content.",
        },
      ]);
    } catch (error) {
      console.error("YouTube error:", error);

      alert(
        "Cannot connect to AskIt backend. Make sure FastAPI is running."
      );
    } finally {
      setLoadingYoutube(false);
    }
  };

  // ==========================================
  // PDF / TXT
  // ==========================================

  const openFilePicker = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (event) => {
    const file = event.target.files?.[0];

    if (!file) return;

    const allowedTypes = [
      "application/pdf",
      "text/plain",
    ];

    const isPdf = file.type === "application/pdf";
    const isTxt =
      file.type === "text/plain" ||
      file.name.toLowerCase().endsWith(".txt");

    if (!allowedTypes.includes(file.type) && !isTxt) {
      alert("Only PDF and TXT files are supported.");
      event.target.value = "";
      return;
    }

    try {
      setLoadingPdf(true);

      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_URL}/document`,
        {
          method: "POST",
          body: formData,
        }
      );

      const data = await response.json();

      if (!response.ok || !data.success) {
        alert(
          data.error ||
            "Unable to process this document."
        );
        return;
      }

      setSourceLoaded(true);
      setSourceType(isPdf ? "pdf" : "txt");
      setSourceName(file.name);

      setMessages([
        {
          role: "assistant",
          content:
            `${file.name} is ready. You can now ask questions about this document.`,
        },
      ]);
    } catch (error) {
      console.error("Document error:", error);

      alert(
        "Cannot connect to AskIt backend. Make sure FastAPI is running."
      );
    } finally {
      setLoadingPdf(false);
      event.target.value = "";
    }
  };

  // ==========================================
  // SEND MESSAGE
  // ==========================================

  const askQuestion = async () => {
    const userQuestion = question.trim();

    if (!userQuestion || loadingChat) return;

    if (!sourceLoaded) {
      alert("Please load a YouTube video or document first.");
      return;
    }

    setMessages((previous) => [
      ...previous,
      {
        role: "user",
        content: userQuestion,
      },
    ]);

    setQuestion("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    try {
      setLoadingChat(true);

      const response = await fetch(`${API_URL}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          question: userQuestion,
        }),
      });

      const data = await response.json();

      if (!response.ok || !data.success) {
        setMessages((previous) => [
          ...previous,
          {
            role: "assistant",
            content:
              data.error ||
              "I couldn't process that request.",
            error: true,
          },
        ]);

        return;
      }

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content: data.answer,
        },
      ]);
    } catch (error) {
      console.error("Chat error:", error);

      setMessages((previous) => [
        ...previous,
        {
          role: "assistant",
          content:
            "I couldn't connect to the server. Please try again.",
          error: true,
        },
      ]);
    } finally {
      setLoadingChat(false);
    }
  };

  // ==========================================
  // KEYBOARD
  // ==========================================

  const handleKeyDown = (event) => {
    if (
      event.key === "Enter" &&
      !event.shiftKey
    ) {
      event.preventDefault();
      askQuestion();
    }
  };

  // ==========================================
  // COPY
  // ==========================================

  const copyMessage = async (content, index) => {
    try {
      await navigator.clipboard.writeText(content);

      setCopiedIndex(index);

      setTimeout(() => {
        setCopiedIndex(null);
      }, 1500);
    } catch (error) {
      console.error(error);
    }
  };

  // ==========================================
  // SUGGESTION
  // ==========================================

  const useSuggestion = (text) => {
    setQuestion(text);

    requestAnimationFrame(() => {
      textareaRef.current?.focus();
      resizeTextarea();
    });
  };

  // ==========================================
  // RENDER
  // ==========================================

  return (
    <div
      className={`app-shell ${
        sidebarCollapsed ? "sidebar-collapsed" : ""
      }`}
    >
      {/* ======================================
          SIDEBAR
      ======================================= */}

      <aside className="sidebar">
        <div className="sidebar-header">
          <div className="logo-mark">A</div>

          {!sidebarCollapsed && (
            <div className="logo-text">
              <strong>AskIt</strong>
              <span>Knowledge assistant</span>
            </div>
          )}
        </div>

        <button
          className="sidebar-toggle"
          onClick={toggleSidebar}
          title={
            sidebarCollapsed
              ? "Expand sidebar"
              : "Collapse sidebar"
          }
        >
          {sidebarCollapsed ? "→" : "←"}
        </button>

        <button
          className="new-chat-button"
          onClick={newChat}
          title="New conversation"
        >
          <span className="new-chat-icon">+</span>

          {!sidebarCollapsed && (
            <>
              <span>New conversation</span>

              <span className="shortcut">
                Ctrl K
              </span>
            </>
          )}
        </button>

        <div className="sidebar-content">
          {!sidebarCollapsed && (
            <div className="sidebar-title">
              WORKSPACE
            </div>
          )}

          <div
            className="sidebar-nav-item active"
            title="Chat"
          >
            <span>⌂</span>

            {!sidebarCollapsed && (
              <span>Chat</span>
            )}
          </div>

          <div
            className="sidebar-nav-item"
            title="Documents"
            onClick={openFilePicker}
          >
            <span>▣</span>

            {!sidebarCollapsed && (
              <span>Documents</span>
            )}
          </div>

          {!sidebarCollapsed && (
            <>
              <div className="sidebar-title recent-title">
                RECENT
              </div>

              <div className="recent-chat active">
                <span className="recent-dot live"></span>

                <span>
                  {sourceLoaded
                    ? sourceName
                    : "Current conversation"}
                </span>

                <span className="recent-chat-time">
                  Now
                </span>
              </div>
            </>
          )}
        </div>

        <div className="sidebar-footer">
          {!sidebarCollapsed && (
            <div className="plan-card">
              <div className="plan-icon">✦</div>

              <div>
                <strong>AskIt</strong>
                <span>
                  AI knowledge workspace
                </span>
              </div>
            </div>
          )}
        </div>
      </aside>

      {/* ======================================
          MAIN
      ======================================= */}

      <main className="main">
        {/* TOPBAR */}

        <header className="topbar">
          <div className="topbar-left">
            <button
              className="desktop-menu"
              onClick={toggleSidebar}
              title="Toggle sidebar"
            >
              ☰
            </button>

            <div>
              <div className="topbar-title">
                AskIt
              </div>

              <div className="topbar-subtitle">
                {sourceLoaded
                  ? sourceName
                  : "AI knowledge assistant"}
              </div>
            </div>
          </div>

          <div className="topbar-right">
            {sourceLoaded && (
              <div className="connection-status">
                <span></span>
                Ready
              </div>
            )}
          </div>
        </header>

        {/* ==================================
            CHAT AREA
        =================================== */}

        <section className="chat-area">
          {messages.length === 0 ? (
            <div className="empty-state">
              <div className="empty-logo">A</div>

              <h1>
                What would you like to know?
              </h1>

              <p>
                Connect a YouTube video or upload
                a document to start chatting.
              </p>

              {/* SOURCE CARD */}

              <div className="source-card">
                <div className="source-card-header">
                  <div>
                    <h3>
                      Add a knowledge source
                    </h3>

                    <p>
                      Choose where AskIt should
                      get its information from.
                    </p>
                  </div>
                </div>

                {/* SOURCE OPTIONS */}

                <div className="source-options">
                  <button
                    className="source-option youtube-option"
                    onClick={() =>
                      document
                        .getElementById(
                          "youtube-input"
                        )
                        ?.focus()
                    }
                  >
                    <div className="source-option-icon youtube-icon">
                      ▶
                    </div>

                    <div className="source-option-content">
                      <strong>YouTube</strong>

                      <span>
                        Analyze a video's transcript
                      </span>
                    </div>
                  </button>

                  <button
                    className="source-option"
                    onClick={openFilePicker}
                  >
                    <div className="source-option-icon document-icon">
                      ▣
                    </div>

                    <div className="source-option-content">
                      <strong>
                        PDF / TXT
                      </strong>

                      <span>
                        Upload your documents
                      </span>
                    </div>
                  </button>
                </div>

                {/* YOUTUBE INPUT */}

                <div className="source-input">
                  <span className="url-icon">
                    ↗
                  </span>

                  <input
                    id="youtube-input"
                    type="text"
                    placeholder="Paste a YouTube URL"
                    value={youtubeUrl}
                    onChange={(event) =>
                      setYoutubeUrl(
                        event.target.value
                      )
                    }
                    onKeyDown={(event) => {
                      if (
                        event.key === "Enter"
                      ) {
                        loadYoutube();
                      }
                    }}
                  />

                  <button
                    onClick={loadYoutube}
                    disabled={
                      loadingYoutube ||
                      !youtubeUrl.trim()
                    }
                  >
                    {loadingYoutube
                      ? "Loading..."
                      : "Connect"}
                  </button>
                </div>

                {/* PDF FILE INPUT */}

                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".pdf,.txt,application/pdf,text/plain"
                  onChange={handleFileChange}
                  hidden
                />

                <button
                  className="upload-button"
                  onClick={openFilePicker}
                  disabled={loadingPdf}
                >
                  <span>↑</span>

                  {loadingPdf
                    ? "Processing document..."
                    : "Upload PDF / TXT"}
                </button>
              </div>

              {/* SUGGESTIONS */}

              <div className="suggestions">
                <button
                  onClick={() =>
                    useSuggestion(
                      "Summarize this content"
                    )
                  }
                >
                  <span>✦</span>
                  Summarize
                </button>

                <button
                  onClick={() =>
                    useSuggestion(
                      "What are the main points?"
                    )
                  }
                >
                  <span>≡</span>
                  Main points
                </button>

                <button
                  onClick={() =>
                    useSuggestion(
                      "Explain this in simple language"
                    )
                  }
                >
                  <span>◌</span>
                  Explain simply
                </button>
              </div>
            </div>
          ) : (
            <div className="conversation">
              {messages.map(
                (message, index) => (
                  <div
                    key={index}
                    className={`message ${message.role}`}
                  >
                    <div className="message-inner">
                      <div
                        className={`message-avatar ${message.role}`}
                      >
                        {message.role ===
                        "user"
                          ? "U"
                          : "A"}
                      </div>

                      <div className="message-main">
                        <div className="message-meta">
                          {message.role ===
                          "user"
                            ? "You"
                            : "AskIt"}
                        </div>

                        <div
                          className={`message-content ${
                            message.error
                              ? "message-error"
                              : ""
                          }`}
                        >
                          {message.content}
                        </div>

                        {message.role ===
                          "assistant" &&
                          !message.error && (
                            <div className="message-actions">
                              <button
                                onClick={() =>
                                  copyMessage(
                                    message.content,
                                    index
                                  )
                                }
                              >
                                {copiedIndex ===
                                index
                                  ? "Copied"
                                  : "Copy"}
                              </button>
                            </div>
                          )}
                      </div>
                    </div>
                  </div>
                )
              )}

              {loadingChat && (
                <div className="message assistant">
                  <div className="message-inner">
                    <div className="message-avatar assistant">
                      A
                    </div>

                    <div className="message-main">
                      <div className="message-meta">
                        AskIt
                      </div>

                      <div className="typing-indicator">
                        <span></span>
                        <span></span>
                        <span></span>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>
          )}
        </section>

        {/* COMPOSER */}

        <div className="composer-wrapper">
          <div
            className={`composer ${
              !sourceLoaded
                ? "composer-disabled"
                : ""
            }`}
          >
            <textarea
              ref={textareaRef}
              rows="1"
              value={question}
              disabled={
                !sourceLoaded ||
                loadingChat
              }
              placeholder={
                sourceLoaded
                  ? "Message AskIt..."
                  : "Connect a source to start chatting"
              }
              onChange={(event) => {
                setQuestion(
                  event.target.value
                );
                resizeTextarea();
              }}
              onKeyDown={handleKeyDown}
            />

            <button
              className="send-button"
              onClick={askQuestion}
              disabled={
                !sourceLoaded ||
                loadingChat ||
                !question.trim()
              }
            >
              ↑
            </button>
          </div>

          <div className="composer-footer">
            <span>
              AskIt answers using your connected
              source.
            </span>

            <span>
              Enter to send · Shift + Enter
              for new line
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;