import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import "./App.css";

import { AuthProvider } from "./contexts/AuthContext";
import { ToastProvider } from "./contexts/ToastContext";
import { ChatProvider } from "./contexts/ChatContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";
import ErrorBoundary from "./components/ErrorBoundary";
import { useTheme } from "./hooks/useTheme";

import Login from "./pages/Login";
import Signup from "./pages/Signup";
import Home from "./pages/Home";
import Assistant from "./pages/Assistant";
import MyHealth from "./pages/MyHealth";
import Reports from "./pages/Reports";
import Nutrition from "./pages/Nutrition";
import Wellness from "./pages/Wellness";
import Settings from "./pages/Settings";

import { useEffect } from "react";

/** Applies the user's saved theme preference to <body>. */
function ThemeApplier() {
  // useTheme(); // Disabled to enforce clean white minimalistic theme
  useEffect(() => {
    document.title = "Forraa Healthcare Intelligence";
  }, []);
  return null;
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
            <ChatProvider>
              <ThemeApplier />
              <ErrorBoundary>
              <Routes>
                {/* Public Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/signup" element={<Signup />} />

                {/* Protected Routes inside Layout */}
                <Route element={<ProtectedRoute />}>
                  <Route element={<Layout />}>
                    <Route path="/" element={<Home />} />
                    <Route path="/assistant/:id?" element={<Assistant />} />
                    <Route path="/health" element={<MyHealth />} />
                    <Route path="/reports" element={<Reports />} />
                    <Route path="/nutrition" element={<Nutrition />} />
                    <Route path="/wellness" element={<Wellness />} />
                    <Route path="/settings" element={<Settings />} />
                  </Route>
                </Route>

                {/* Catch all */}
                <Route path="*" element={<Navigate to="/" replace />} />
              </Routes>
              </ErrorBoundary>
            </ChatProvider>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;

