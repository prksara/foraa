import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Sparkles, ArrowRight } from "lucide-react";

function AskForraa({
  placeholder = "Ask Forraa anything about your health...",
  suggestions = [],
  activeReportId = null,
}) {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");

  const handleSubmit = () => {
    if (!query.trim()) {
      navigate("/assistant", { state: { activeReportId } });
      return;
    }
    navigate("/assistant", { state: { query, activeReportId } });
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
        <Sparkles size={18} className="ask-forraa__sparkle" />
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
              onClick={() => navigate("/assistant")}
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
