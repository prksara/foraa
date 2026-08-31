import { Component } from "react";

/**
 * Global error boundary that catches render-phase errors from child components.
 * Prevents the entire app from going blank on an unexpected crash.
 */
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, info) {
    console.error("[Foraa ErrorBoundary] Caught render error:", error, info);
  }

  handleReset = () => {
    this.setState({ hasError: false, error: null });
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            minHeight: "50vh",
            gap: "16px",
            padding: "40px",
            textAlign: "center",
          }}
        >
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="var(--color-error, #c0392b)" strokeWidth="2">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
          <h2 style={{ fontSize: "20px", fontWeight: 600 }}>Something went wrong</h2>
          <p style={{ color: "var(--color-text-secondary, #6b7280)", maxWidth: "400px", lineHeight: 1.6 }}>
            An unexpected error occurred in this section. Your health data is safe.
          </p>
          <button
            onClick={this.handleReset}
            style={{
              padding: "10px 20px",
              borderRadius: "8px",
              background: "var(--color-accent, #168A70)",
              color: "#fff",
              border: "none",
              cursor: "pointer",
              fontWeight: 500,
              fontSize: "14px",
            }}
          >
            Try Again
          </button>
          {this.props.onNavigateHome && (
            <button
              onClick={this.props.onNavigateHome}
              style={{
                padding: "10px 20px",
                borderRadius: "8px",
                background: "transparent",
                color: "var(--color-text-secondary, #6b7280)",
                border: "1px solid var(--color-border, #e5e7eb)",
                cursor: "pointer",
                fontWeight: 500,
                fontSize: "14px",
              }}
            >
              Return to Home
            </button>
          )}
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
