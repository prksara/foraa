import { useState, useEffect, useRef } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import {
  Send,
  User,
  StopCircle,
  RefreshCw,
  Copy,
  MessageSquare,
  CheckCircle2,
  FileText,
} from "lucide-react";
import {
  streamChatMessage,
  fetchConversation,
} from "../api/client";
import ReactMarkdown from "react-markdown";
import { useChat } from "../contexts/ChatContext";

function Assistant() {
  const { id } = useParams();
  const navigate = useNavigate();
  const { pendingAssistantMessage, clearPendingAssistantMessage, loadConversations } = useChat();

  const [message, setMessage] = useState("");
  const [messages, setMessages] = useState([]);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [copiedIndex, setCopiedIndex] = useState(null);

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

  // Handle URL ID changes
  useEffect(() => {
    if (id) {
      handleSelectConversation(id);
    } else {
      // New Chat state
      setMessages([]);
      setMessage("");
      setError(null);
      if (textareaRef.current) textareaRef.current.focus();
    }
  }, [id]);

  // Handle pending message from Home
  useEffect(() => {
    if (pendingAssistantMessage) {
      const msg = pendingAssistantMessage;
      clearPendingAssistantMessage();
      // Wait a tick to ensure component is fully mounted/state is clean
      setTimeout(() => handleSend(msg), 50);
    }
  }, [pendingAssistantMessage, id]);

  const handleSelectConversation = async (convId) => {
    if (loading && abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    try {
      const conv = await fetchConversation(convId);
      setMessages(conv.messages || []);
      setError(null);
      setMessage("");
    } catch (err) {
      console.error("Failed to load conversation details", err);
      setError("Unable to load conversation.");
    }
  };

  const handleSend = async (customMessage = null) => {
    const text = customMessage || message.trim();
    if (!text || loading) return;

    let currentConvId = id;

    // Add user message to UI immediately
    const updatedMessages = [...messages, { role: "user", content: text }];

    setMessages(updatedMessages);
    if (!customMessage) setMessage("");

    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
    }

    setLoading(true);
    setError(null);

    // Add empty assistant message placeholder
    setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
    let assistantContent = "";
    let receivedNewConvId = null;

    abortControllerRef.current = new AbortController();

    try {
      await streamChatMessage(
        text,
        currentConvId, // passes undefined/null if New Chat
        activeReportIdRef.current,
        (data) => {
          if (data.conversation_id && !currentConvId) {
            receivedNewConvId = data.conversation_id;
            currentConvId = data.conversation_id;
            // Silently update URL without triggering a remount/re-fetch
            navigate(`/assistant/${data.conversation_id}`, { replace: true });
          }
          if (data.reasoning_status !== undefined) {
            setMessages((prev) => {
              const newMsgs = [...prev];
              newMsgs[newMsgs.length - 1] = {
                ...newMsgs[newMsgs.length - 1],
                reasoningStatus: data.reasoning_status,
              };
              return newMsgs;
            });
          }
          if (data.evidence_metadata) {
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

      // Refresh list to show new conversation / auto-generated title
      loadConversations();
    } catch (err) {
      if (err.name === "AbortError") {
        console.log("Stream aborted");
        loadConversations(); // Update list anyway in case conv was created
      } else {
        const errorMessage =
          err.message === "Failed to fetch"
            ? "Cannot reach the Forraa backend."
            : `Error: ${err.message}`;

        setError("Forraa couldn't complete that response. Please try again.");

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
      if (textareaRef.current) textareaRef.current.focus();
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
      // Safely slice the messages array up to the point BEFORE the last failed/stopped assistant response
      // But actually, just removing the last assistant error message is fine if it was an error.
      // If we retry, we can strip the last assistant message and resend the user message.
      const msgsWithoutLastAssistant = [...messages];
      if (msgsWithoutLastAssistant[msgsWithoutLastAssistant.length - 1].role === "assistant") {
        msgsWithoutLastAssistant.pop();
      }
      if (msgsWithoutLastAssistant[msgsWithoutLastAssistant.length - 1].role === "user") {
          msgsWithoutLastAssistant.pop(); // Also remove the user message so we don't duplicate it in the UI when handleSend adds it again
      }
      setMessages(msgsWithoutLastAssistant);
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
      if (!loading && abortControllerRef.current === null) {
        handleSend();
      }
    }
  };

  const handleInput = (e) => {
    setMessage(e.target.value);
    if (textareaRef.current) {
      textareaRef.current.style.height = "24px";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 150)}px`;
    }
  };

  return (
    <div className="assistant-page">
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
                <div style={{ display: "flex", gap: "8px", flexWrap: "wrap", justifyContent: "center", marginTop: "24px", maxWidth: "600px", margin: "24px auto 0" }}>
                  {[
                    "Understand a lab report",
                    "Improve my nutrition",
                    "Explain my symptoms",
                    "Review my health history"
                  ].map((suggestion, i) => (
                    <button 
                      key={i} 
                      onClick={() => handleSend(suggestion)}
                      style={{
                        padding: "8px 16px",
                        background: "var(--color-surface)",
                        border: "1px solid var(--color-border)",
                        borderRadius: "var(--radius-full)",
                        color: "var(--color-text)",
                        cursor: "pointer",
                        fontSize: "14px",
                        transition: "all var(--ease-fast)"
                      }}
                      onMouseOver={(e) => {
                        e.currentTarget.style.borderColor = "var(--color-accent)";
                      }}
                      onMouseOut={(e) => {
                        e.currentTarget.style.borderColor = "var(--color-border)";
                      }}
                    >
                      "{suggestion}"
                    </button>
                  ))}
                </div>
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
                        {item.reasoningStatus && !item.content ? (
                          <div className="reasoning-status" style={{ display: "flex", alignItems: "center", gap: "8px", color: "var(--color-text-muted)", fontSize: "14px", fontStyle: "italic" }}>
                            <div className="typing-dots" style={{ margin: 0, padding: 0 }}>
                              <div className="typing-dot" style={{ background: "var(--color-text-muted)", width: "4px", height: "4px" }}></div>
                              <div className="typing-dot" style={{ background: "var(--color-text-muted)", width: "4px", height: "4px" }}></div>
                              <div className="typing-dot" style={{ background: "var(--color-text-muted)", width: "4px", height: "4px" }}></div>
                            </div>
                            {item.reasoningStatus}
                          </div>
                        ) : item.content ? (
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
    </div>
  );
}

export default Assistant;
