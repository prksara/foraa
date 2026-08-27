import { useEffect, useState } from "react";
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from "lucide-react";

const icons = {
  success: <CheckCircle size={18} className="toast-icon success" />,
  error: <AlertCircle size={18} className="toast-icon error" />,
  info: <Info size={18} className="toast-icon info" />,
  warning: <AlertTriangle size={18} className="toast-icon warning" />,
};

function Toast({ toast, onClose }) {
  const [isClosing, setIsClosing] = useState(false);

  useEffect(() => {
    // Add a slight delay before rendering to trigger the entrance animation
    const enterTimer = setTimeout(() => {
      // Logic for enter handled by CSS class presence
    }, 10);
    return () => clearTimeout(enterTimer);
  }, []);

  const handleClose = () => {
    setIsClosing(true);
    setTimeout(() => {
      onClose();
    }, 300); // Matches CSS exit animation duration
  };

  return (
    <div
      className={`toast toast--${toast.type} ${isClosing ? "toast--exit" : "toast--enter"}`}
    >
      <div className="toast-content">
        {icons[toast.type]}
        <span className="toast-message">{toast.message}</span>
      </div>
      <button
        onClick={handleClose}
        className="toast-close"
        aria-label="Close notification"
      >
        <X size={16} />
      </button>
    </div>
  );
}

export default Toast;
