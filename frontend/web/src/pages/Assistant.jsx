import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import {
  Send,
  Sparkles,
  User,
  StopCircle,
  RefreshCw,
  Copy,
  Plus,
  MessageSquare,
  Trash2,
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  FileText,
  Edit2,
} from "lucide-react";
import {
  streamChatMessage,
  fetchConversations,
  createConversation,
  deleteConversation,
  fetchConversation,
  updateConversation,
} from "../api/client";
import ReactMarkdown from "react-markdown";
import ConfirmModal from "../components/ConfirmModal";

function Assistant() {
  const [message, setMessage] = useState("");
  const [activeConversationId, setActiveConversationId] = useState(null);
  const [conversations, setConversations] = useState([]);
  const [messages, setMessages] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);
  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [convToDelete, setConvToDelete] = useState(null);

  const location = useLocation();
  const activeReportIdRef = useRef(location.state?.activeReportId || null);

  const abortControllerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  // Auto-scroll handling
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  // Fetch conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  const loadConversations = async () => {
    try {
      const data = await fetchConversations();
      setConversations(data);
      if (data.length > 0 && !activeConversationId) {
        // Optionally auto-select most recent
      }
      // Auto send initial query from navigation state if present
      if (location.state?.query && !activeConversationId) {
        // Wait a tick for states to settle
        setTimeout(() => handleSend(location.state.query), 100);
        // Clear state so it doesn't fire again on refresh
        window.history.replaceState({}, document.title);
      }
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  const handleNewChat = async () => {
    try {
      const conv = await createConversation();
      setConversations([conv, ...conversations]);
      setActiveConversationId(conv.id);
      setMessages([]);
      setMessage("");
      setError(null);
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    } catch (err) {
      console.error("Failed to create conversation", err);
    }
  };

  const handleSelectConversation = async (id) => {
    if (loading && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    try {
      setActiveConversationId(id);
      const conv = await fetchConversation(id);
      setMessages(conv.messages || []);
      setError(null);
      setMessage("");
    } catch (err) {
      console.error("Failed to load conversation details", err);
    }
  };

  const handleDeleteConversation = async () => {
    if (!convToDelete) return;
    try {
      await deleteConversation(convToDelete);
      setConversations(conversations.filter((c) => c.id !== convToDelete));
      if (activeConversationId === convToDelete) {
        setActiveConversationId(null);
        setMessages([]);
      }
    } catch (err) {
      console.error("Failed to delete conversation", err);
    } finally {
      setConvToDelete(null);
    }
  };

  const handleRenameSubmit = async (id) => {
    if (!editTitle.trim()) {
      setEditingConvId(null);
      return;
    }
    try {
      await updateConversation(id, { title: editTitle });
      setConversations(
        conversations.map((c) =>
          c.id === id ? { ...c, title: editTitle } : c,
        ),
      );
    } catch (err) {
      console.error("Failed to rename conversation", err);
    } finally {
      setEditingConvId(null);
    }
  };

  const handleSend = async (customMessage = null) => {
    const text = customMessage || message.trim();
    if (!text || loading) return;

    let convId = activeConversationId;
    if (!convId) {
      // Need to wait for backend to return conversation ID during stream
    }

    // Add user message to UI immediately
    const updatedMessages = [...messages, { role: "user", content: text }];

    setMessages(updatedMessages);
    if (!customMessage) setMessage(""); // Only clear input if not a retry

    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setLoading(true);
    setError(null);

    // Add empty assistant message placeholder
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    let assistantContent = "";

    abortControllerRef.current = new AbortController();

    try {
      await streamChatMessage(
        text,
        convId,
        activeReportIdRef.current,
        (data) => {
          if (data.conversation_id) {
            convId = data.conversation_id;
            setActiveConversationId(convId);
            // We should probably refresh the sidebar title at some point
          }
          if (data.evidence_metadata) {
            // Store the metadata on the current assistant message
            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = {
                ...newMsgs[newMsgs.length - 1],
                evidenceMetadata: data.evidence_metadata,
              };
              return newMsgs;
            });
          }
          if (data.content) {
            assistantContent += data.content;
            // Update the last message in state
            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = {
                ...newMsgs[newMsgs.length - 1],
                role: "assistant",
                content: assistantContent,
              };
              return newMsgs;
            });
          }
          if (data.error) {
            throw new Error(data.error);
          }
        },
        abortControllerRef.current.signal,
      );

      // Refresh conversation list after generation to get the potentially updated title
      loadConversations();
    } catch (err) {
      if (err.name === "AbortError") {
        // Expected when user clicks Stop
        console.log("Stream aborted");
      } else {
        const errorMessage =
          err.message === "Failed to fetch"
            ? "Cannot reach the Forraa backend."
            : `Error: ${err.message}`;

        setError("Forraa couldn't complete that response. Please try again.");

        // If it failed immediately and we have no content
        if (!assistantContent) {
          setMessages((prev) => {
            const newMsgs = [...prev];
            newMsgs[newMsgs.length - 1] = {
              role: "assistant",
              content: errorMessage,
              isError: true,
            };
            return newMsgs;
          });
        }
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  };

  const handleStop = () => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
  };

  const handleRetry = () => {
    // Find the last user message
    const lastUserMessage = [...messages]
      .reverse()
      .find((m) => m.role === "user");
    if (lastUserMessage) {
      // Remove the failed assistant message if it exists
      setMessages(messages.filter((m) => !m.isError));
      handleSend(lastUserMessage.content);
    }
  };

  const handleCopy = (content, index) => {
    navigator.clipboard.writeText(content);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 2000);
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleInput = (e) => {
    setMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  return (
    <div className="assistant-page has-sidebar">
      {/* Conversation Sidebar */}
      <div className="conversation-sidebar">
        <button className="new-chat-btn" onClick={handleNewChat}>
          <Plus size={18} />
          New Chat
        </button>

        <div className="conversation-list">
          <span className="list-label">Recent</span>
          {conversations.map((conv) => (
            <div
              key={conv.id}
              className={`conversation-item ${activeConversationId === conv.id ? "active" : ""}`}
              onClick={() => {
                if (editingConvId !== conv.id)
                  handleSelectConversation(conv.id);
              }}
            >
              <MessageSquare size={16} className="conv-icon" />
              {editingConvId === conv.id ? (
                <input
                  autoFocus
                  className="conv-title-input"
                  value={editTitle}
                  onChange={(e) => setEditTitle(e.target.value)}
                  onBlur={() => handleRenameSubmit(conv.id)}
                  onKeyDown={(e) => {
                    if (e.key === "Enter") handleRenameSubmit(conv.id);
                    if (e.key === "Escape") setEditingConvId(null);
                  }}
                  onClick={(e) => e.stopPropagation()}
                  style={{
                    flex: 1,
                    minWidth: 0,
                    background: "transparent",
                    border: "1px solid var(--color-border)",
                    color: "var(--color-text)",
                    padding: "2px 4px",
                    borderRadius: "4px",
                  }}
                />
              ) : (
                <span className="conv-title">{conv.title}</span>
              )}

              {!editingConvId && (
                <div
                  className="conv-actions"
                  style={{ display: "flex", gap: "4px" }}
                >
                  <button
                    className="edit-conv-btn"
                    style={{
                      background: "none",
                      border: "none",
                      color: "inherit",
                      cursor: "pointer",
                      padding: "2px",
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setEditingConvId(conv.id);
                      setEditTitle(conv.title);
                    }}
                    title="Rename chat"
                  >
                    <Edit2 size={14} />
                  </button>
                  <button
                    className="delete-conv-btn"
                    style={{
                      background: "none",
                      border: "none",
                      color: "inherit",
                      cursor: "pointer",
                      padding: "2px",
                    }}
                    onClick={(e) => {
                      e.stopPropagation();
                      setConvToDelete(conv.id);
                    }}
                    title="Delete chat"
                  >
                    <Trash2 size={14} />
                  </button>
                </div>
              )}
            </div>
          ))}
          {conversations.length === 0 && (
            <div className="empty-conversations">No recent chats</div>
          )}
        </div>
      </div>

      {/* Main Chat Area */}
      <div className="assistant-main">
        <div className="assistant-header">
          <div>
            <span className="section-label">FORRAA HEALTH INTELLIGENCE</span>
            <h1>Health Assistant</h1>
          </div>
          <div className="assistant-status">
            <span className={loading ? "loading-dot" : ""} />
            {loading ? "Generating..." : "Forraa online"}
          </div>
        </div>

        <div className="chat-container">
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="chat-empty">
                <div
                  className="chat-logo"
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    background: "transparent",
                  }}
                >
                  <img
                    src="/foraa%20logo.png"
                    alt="Foraa"
                    style={{
                      width: "100px",
                      height: "100px",
                      objectFit: "contain",
                      margin: "0 auto",
                    }}
                  />
                </div>
                <h2>How can I help you today?</h2>
                <p>
                  Tell me what you're experiencing, what you're trying to
                  improve, or ask a health question.
                </p>
              </div>
            )}

            {messages.map((item, index) => (
              <div key={index} className={`message-row ${item.role}`}>
                <div
                  className="message-avatar"
                  style={
                    item.role !== "user" ? { background: "transparent" } : {}
                  }
                >
                  {item.role === "user" ? (
                    <User size={16} />
                  ) : (
                    <img
                      src="/foraa%20logo.png"
                      alt="Foraa"
                      style={{
                        width: "100%",
                        height: "100%",
                        objectFit: "contain",
                      }}
                    />
                  )}
                </div>

                <div className="message-content-wrapper">
                  <div
                    className={`message-bubble ${item.isError ? "error-bubble" : ""}`}
                  >
                    {item.role === "assistant" && !item.isError ? (
                      <>
                        {item.content ? (
                          <ReactMarkdown>{item.content}</ReactMarkdown>
                        ) : loading && index === messages.length - 1 ? (
                          <div className="typing-dots">
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                            <div className="typing-dot"></div>
                          </div>
                        ) : null}

                        {/* Sources Panel */}
                        {item.evidenceMetadata &&
                          item.evidenceMetadata.length > 0 && (
                            <div className="sources-panel">
                              <div className="sources-header">
                                <FileText size={14} />
                                <span>Sources</span>
                              </div>
                              <div className="sources-list">
                                {item.evidenceMetadata.map((src, i) => (
                                  <div key={i} className="source-item">
                                    <div className="source-citation">
                                      [{src.citation}]
                                    </div>
                                    <div className="source-info">
                                      <div className="source-name">
                                        {src.source_name}
                                      </div>
                                      {src.url ? (
                                        <a
                                          href={src.url}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          className="source-title link"
                                        >
                                          {src.title}
                                        </a>
                                      ) : (
                                        <div className="source-title">
                                          {src.title}
                                        </div>
                                      )}
                                      {src.publication_date && (
                                        <div className="source-date">
                                          {src.publication_date}
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                      </>
                    ) : (
                      item.content
                    )}
                    {/* Show cursor if loading and this is the last message AND there's text */}
                    {loading &&
                      index === messages.length - 1 &&
                      item.role === "assistant" &&
                      item.content && <span className="typing-cursor">|</span>}
                  </div>

                  {item.role === "assistant" &&
                    item.content &&
                    !item.isError &&
                    !loading && (
                      <div className="message-actions">
                        <button
                          className="action-btn copy-btn"
                          onClick={() => handleCopy(item.content, index)}
                        >
                          {copiedIndex === index ? (
                            <>
                              <CheckCircle2 size={14} /> <span>Copied</span>
                            </>
                          ) : (
                            <>
                              <Copy size={14} /> <span>Copy</span>
                            </>
                          )}
                        </button>

                        {index === messages.length - 1 && (
                          <button
                            className="action-btn retry-btn"
                            onClick={handleRetry}
                          >
                            <RefreshCw size={14} /> <span>Retry</span>
                          </button>
                        )}
                      </div>
                    )}

                  {item.isError && (
                    <div className="message-actions">
                      <button
                        className="action-btn retry-btn"
                        onClick={handleRetry}
                      >
                        <RefreshCw size={14} /> <span>Retry</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}

            <div ref={messagesEndRef} />
          </div>

          <div className="chat-input-wrapper">
            {error && <div className="chat-error-banner">{error}</div>}

            <div className="input-row">
              <textarea
                ref={textareaRef}
                value={message}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Ask Forraa anything about your health..."
                rows={1}
                disabled={loading && abortControllerRef.current !== null}
              />

              {loading ? (
                <button
                  className="stop-btn"
                  onClick={handleStop}
                  title="Stop generating"
                >
                  <StopCircle size={20} />
                </button>
              ) : (
                <button
                  className="send-btn"
                  onClick={() => handleSend()}
                  disabled={!message.trim()}
                >
                  <Send size={17} />
                </button>
              )}
            </div>

            <div className="chat-disclaimer">
              For informational purposes only. Forraa does not replace
              professional medical care.
            </div>
          </div>
        </div>
      </div>

      <ConfirmModal
        isOpen={!!convToDelete}
        onClose={() => setConvToDelete(null)}
        onConfirm={handleDeleteConversation}
        title="Delete Chat"
        message="Are you sure you want to delete this conversation? This action cannot be undone."
        confirmText="Delete"
        isDestructive={true}
      />
    </div>
  );
}

export default Assistant;
