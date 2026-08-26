import { useState } from "react";
import { Send, Sparkles, User } from "lucide-react";
import { sendChatMessage } from "../api/client";

function Assistant() {
    const [message, setMessage] = useState("");
    const [messages, setMessages] = useState([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const handleSend = async () => {
        const text = message.trim();

        if (!text || loading) return;

        setMessages((previous) => [
            ...previous,
            {
                role: "user",
                content: text,
            },
        ]);

        setMessage("");
        setLoading(true);
        setError(null);

        try {
            const data = await sendChatMessage(text);

            setMessages((previous) => [
                ...previous,
                {
                    role: "assistant",
                    content: data.reply,
                },
            ]);
        } catch (err) {
            const errorMessage =
                err.message === "Failed to fetch"
                    ? "Cannot reach the Forraa backend. Make sure it is running on port 8000."
                    : `Error: ${err.message}`;

            setError(errorMessage);

            setMessages((previous) => [
                ...previous,
                {
                    role: "assistant",
                    content: errorMessage,
                },
            ]);
        } finally {
            setLoading(false);
        }
    };

    const handleKeyDown = (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            handleSend();
        }
    };

    return (
        <div className="assistant-page">

            <div className="assistant-header">
                <div>
                    <span className="section-label">
                        FORRAA HEALTH INTELLIGENCE
                    </span>

                    <h1>Health Assistant</h1>

                    <p>
                        Ask questions about your health, habits,
                        reports and wellbeing.
                    </p>
                </div>

                <div className="assistant-status">
                    <span />
                    Forraa online
                </div>
            </div>

            <div className="chat-container">

                <div className="chat-messages">

                    {messages.length === 0 && (
                        <div className="chat-empty">

                            <div className="chat-logo">
                                <Sparkles size={25} />
                            </div>

                            <h2>
                                How can I help you today?
                            </h2>

                            <p>
                                Tell me what you're experiencing,
                                what you're trying to improve,
                                or ask a health question.
                            </p>

                        </div>
                    )}

                    {messages.map((item, index) => (
                        <div
                            key={index}
                            className={`message-row ${item.role}`}
                        >
                            <div className="message-avatar">
                                {item.role === "user" ? (
                                    <User size={16} />
                                ) : (
                                    <Sparkles size={16} />
                                )}
                            </div>

                            <div className="message-bubble">
                                {item.content}
                            </div>
                        </div>
                    ))}

                    {loading && (
                        <div className="message-row assistant">
                            <div className="message-avatar">
                                <Sparkles size={16} />
                            </div>

                            <div className="message-bubble">
                                Forraa is thinking...
                            </div>
                        </div>
                    )}

                </div>

                <div className="chat-input-wrapper">

                    <textarea
                        value={message}
                        onChange={(event) => setMessage(event.target.value)}
                        onKeyDown={handleKeyDown}
                        placeholder="Ask Forraa anything about your health..."
                        rows={1}
                        disabled={loading}
                    />

                    <button
                        onClick={handleSend}
                        disabled={!message.trim() || loading}
                    >
                        <Send size={17} />
                    </button>

                </div>

                <div className="chat-disclaimer">
                    For informational purposes only. Forraa does not
                    replace professional medical care.
                </div>

            </div>

        </div>
    );
}

export default Assistant;