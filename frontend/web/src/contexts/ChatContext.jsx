import { createContext, useContext, useState, useEffect } from "react";
import { fetchConversations, deleteConversation, updateConversation } from "../api/client";
import { useAuth } from "./AuthContext";

const ChatContext = createContext(undefined);

export function ChatProvider({ children }) {
  const { user } = useAuth();
  const [pendingAssistantMessage, setPendingAssistantMessage] = useState(null);
  const [conversations, setConversations] = useState([]);

  const loadConversations = async () => {
    if (!user) {
      setConversations([]);
      return;
    }
    try {
      const data = await fetchConversations();
      setConversations(data || []);
    } catch (err) {
      console.error("Failed to load conversations", err);
    }
  };

  useEffect(() => {
    loadConversations();
  }, [user]);

  const handleDeleteConversation = async (id) => {
    try {
      await deleteConversation(id);
      setConversations((prev) => prev.filter((c) => c.id !== id));
      return true;
    } catch (err) {
      console.error("Failed to delete conversation", err);
      return false;
    }
  };

  const handleRenameConversation = async (id, title) => {
    try {
      await updateConversation(id, { title });
      setConversations((prev) =>
        prev.map((c) => (c.id === id ? { ...c, title } : c))
      );
      return true;
    } catch (err) {
      console.error("Failed to rename conversation", err);
      return false;
    }
  };

  const value = {
    pendingAssistantMessage,
    setPendingAssistantMessage,
    clearPendingAssistantMessage: () => setPendingAssistantMessage(null),
    conversations,
    loadConversations,
    handleDeleteConversation,
    handleRenameConversation,
  };

  return <ChatContext.Provider value={value}>{children}</ChatContext.Provider>;
}

export function useChat() {
  const context = useContext(ChatContext);
  if (context === undefined) {
    throw new Error("useChat must be used within a ChatProvider");
  }
  return context;
}
