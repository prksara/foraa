import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";
import { useChat } from "../contexts/ChatContext";

function AskForraa({
  placeholder = "Ask Forraa anything about your health...",
  suggestions = [],
  activeReportId = null,
}) {
  const navigate = useNavigate();
  const { setPendingAssistantMessage } = useChat();
  const [query, setQuery] = useState("");

  const handleSubmit = () => {
    if (!query.trim()) {
      navigate("/assistant");
      return;
    }
    setPendingAssistantMessage(query);
    navigate("/assistant");
    setQuery("");
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="ask-forraa">
      <div className="ask-forraa__input-row">
        <div
          className="ask-forraa__sparkle"
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: "32px",
            height: "32px",
            padding: "0",
          }}
        >
          <img
            src="/foraa%20logo.png"
            alt="Foraa"
            style={{ width: "100%", height: "100%", objectFit: "contain" }}
          />
        </div>
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          className="ask-forraa__input"
        />
        <button
          className="ask-forraa__btn"
          onClick={handleSubmit}
          aria-label="Ask Forraa"
        >
          <ArrowRight size={16} />
        </button>
      </div>
      {suggestions.length > 0 && (
        <div className="ask-forraa__suggestions">
          {suggestions.map((s, i) => (
            <button
              key={i}
              className="ask-forraa__suggestion"
              onClick={() => {
                setPendingAssistantMessage(s);
                navigate("/assistant");
              }}
            >
              {s}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}

export default AskForraa;
