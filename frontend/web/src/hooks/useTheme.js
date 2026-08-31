import { useEffect } from "react";
import { useAuth } from "../contexts/AuthContext";
import { fetchPreferences } from "../api/client";

/**
 * Applies the user's saved theme preference to <body>.
 * Runs once after the user authenticates.
 * Respects the system preference when theme === 'system'.
 */
export function useTheme() {
  const { user } = useAuth();

  useEffect(() => {
    if (!user) {
      // When logged out, remove any explicit theme
      document.body.classList.remove("dark-theme");
      return;
    }

    let cancelled = false;

    fetchPreferences()
      .then((prefs) => {
        if (cancelled) return;
        applyTheme(prefs?.theme ?? "system");
      })
      .catch(() => {
        // Fallback to system preference on error
        if (!cancelled) applyTheme("system");
      });

    return () => {
      cancelled = true;
    };
  }, [user]);
}

function applyTheme(theme) {
  if (theme === "dark") {
    document.body.classList.add("dark-theme");
  } else if (theme === "light") {
    document.body.classList.remove("dark-theme");
  } else {
    // 'system' — follow OS preference
    const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
    if (prefersDark) {
      document.body.classList.add("dark-theme");
    } else {
      document.body.classList.remove("dark-theme");
    }
  }
}
