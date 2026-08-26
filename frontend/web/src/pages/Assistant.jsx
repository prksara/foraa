import { useState, useEffect, useRef } from "react";
import { useLocation } from "react-router-dom";
import { Send, Sparkles, User, StopCircle, RefreshCw, Copy, Plus, MessageSquare, Trash2, CheckCircle2 } from "lucide-react";
import { streamChatMessage, fetchConversations, createConversation, deleteConversation, fetchConversation } from "../api/client";
import ReactMarkdown from "react-markdown";

function Assistant() {
    const [message, setMessage] = useState("");
    const [activeConversationId, setActiveConversationId] = useState(null);
    const [conversations, setConversations] = useState([]);
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
                window.history.replaceState({}, document.title)
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

    const handleDeleteConversation = async (e, id) => {
        e.stopPropagation();
        try {
            await deleteConversation(id);
            setConversations(conversations.filter(c => c.id !== id));
            if (activeConversationId === id) {
                setActiveConversationId(null);
                setMessages([]);
            }
        } catch (err) {
            console.error("Failed to delete conversation", err);
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
        const updatedMessages = [
            ...messages,
            { role: "user", content: text }
        ];
        
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
                    if (data.content) {
                        assistantContent += data.content;
                        // Update the last message in state
                        setMessages((prev) => {
                            const newMsgs = [...prev];
                            newMsgs[newMsgs.length - 1] = { role: "assistant", content: assistantContent };
                            return newMsgs;
                        });
                    }
                    if (data.error) {
                        throw new Error(data.error);
                    }
                },
                abortControllerRef.current.signal
            );
            
            // Refresh conversation list after generation to get the potentially updated title
            loadConversations();
            
        } catch (err) {
            if (err.name === "AbortError") {
                // Expected when user clicks Stop
                console.log("Stream aborted");
            } else {
                const errorMessage = err.message === "Failed to fetch"
                    ? "Cannot reach the Forraa backend."
                    : `Error: ${err.message}`;
                
                setError("Forraa couldn't complete that response. Please try again.");
                
                // If it failed immediately and we have no content
                if (!assistantContent) {
                    setMessages((prev) => {
                        const newMsgs = [...prev];
                        newMsgs[newMsgs.length - 1] = { role: "assistant", content: errorMessage, isError: true };
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
        const lastUserMessage = [...messages].reverse().find(m => m.role === "user");
        if (lastUserMessage) {
            // Remove the failed assistant message if it exists
            setMessages(messages.filter(m => !m.isError));
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
                    {conversations.map(conv => (
                        <div 
                            key={conv.id} 
                            className={`conversation-item ${activeConversationId === conv.id ? 'active' : ''}`}
                            onClick={() => handleSelectConversation(conv.id)}
                        >
                            <MessageSquare size={16} className="conv-icon" />
                            <span className="conv-title">{conv.title}</span>
                            <button 
                                className="delete-conv-btn" 
                                onClick={(e) => handleDeleteConversation(e, conv.id)}
                                title="Delete chat"
                            >
                                <Trash2 size={14} />
                            </button>
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
                                <div className="chat-logo">
                                    <Sparkles size={25} />
                                </div>
                                <h2>How can I help you today?</h2>
                                <p>Tell me what you're experiencing, what you're trying to improve, or ask a health question.</p>
                            </div>
                        )}

                        {messages.map((item, index) => (
                            <div key={index} className={`message-row ${item.role}`}>
                                <div className="message-avatar">
                                    {item.role === "user" ? <User size={16} /> : <Sparkles size={16} />}
                                </div>

                                <div className="message-content-wrapper">
                                    <div className={`message-bubble ${item.isError ? 'error-bubble' : ''}`}>
                                        {item.role === "assistant" && !item.isError ? (
                                            <ReactMarkdown>{item.content}</ReactMarkdown>
                                        ) : (
                                            item.content
                                        )}
                                        {/* Show cursor if loading and this is the last message */}
                                        {loading && index === messages.length - 1 && item.role === "assistant" && (
                                            <span className="typing-cursor">|</span>
                                        )}
                                    </div>
                                    
                                    {item.role === "assistant" && item.content && !item.isError && !loading && (
                                        <div className="message-actions">
                                            <button 
                                                className="action-btn copy-btn"
                                                onClick={() => handleCopy(item.content, index)}
                                            >
                                                {copiedIndex === index ? (
                                                    <><CheckCircle2 size={14} /> <span>Copied</span></>
                                                ) : (
                                                    <><Copy size={14} /> <span>Copy</span></>
                                                )}
                                            </button>
                                            
                                            {index === messages.length - 1 && (
                                                <button className="action-btn retry-btn" onClick={handleRetry}>
                                                    <RefreshCw size={14} /> <span>Retry</span>
                                                </button>
                                            )}
                                        </div>
                                    )}
                                    
                                    {item.isError && (
                                        <div className="message-actions">
                                            <button className="action-btn retry-btn" onClick={handleRetry}>
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
                                <button className="stop-btn" onClick={handleStop} title="Stop generating">
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
                            For informational purposes only. Forraa does not replace professional medical care.
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export default Assistant;