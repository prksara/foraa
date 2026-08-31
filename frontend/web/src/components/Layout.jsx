import { useState, useEffect } from "react";
import { NavLink, useNavigate, Outlet, useLocation } from "react-router-dom";
import {
  Home,
  MessageSquare,
  Heart,
  FileText,
  Apple,
  Sun,
  Settings,
  User,
  LogOut,
  Menu,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  Edit2,
  Search,
  Archive,
} from "lucide-react";
import MobileNav from "./MobileNav";
import QuickAddLog from "./QuickAddLog";
import { useAuth } from "../contexts/AuthContext";
import { useChat } from "../contexts/ChatContext";

const mainNav = [
  { name: "Home", path: "/", icon: Home },
  { name: "Health Assistant", path: "/assistant", icon: MessageSquare },
  { name: "My Health", path: "/health", icon: Heart },
  { name: "Reports", path: "/reports", icon: FileText },
  { name: "Nutrition", path: "/nutrition", icon: Apple },
  { name: "Wellness", path: "/wellness", icon: Sun },
];

/**
 * Groups conversations into Today, Yesterday, This Week, and Older buckets.
 */
function groupConversationsByDate(conversations) {
  const now = new Date();
  const startOfToday = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const startOfYesterday = new Date(startOfToday);
  startOfYesterday.setDate(startOfYesterday.getDate() - 1);
  const startOfWeek = new Date(startOfToday);
  startOfWeek.setDate(startOfWeek.getDate() - 6);

  const groups = {
    Today: [],
    Yesterday: [],
    "This Week": [],
    Older: [],
  };

  conversations.forEach((conv) => {
    const date = new Date(conv.updated_at);
    if (date >= startOfToday) {
      groups.Today.push(conv);
    } else if (date >= startOfYesterday) {
      groups.Yesterday.push(conv);
    } else if (date >= startOfWeek) {
      groups["This Week"].push(conv);
    } else {
      groups.Older.push(conv);
    }
  });

  return groups;
}

function Layout() {
  const { user, signOut } = useAuth();
  const {
    conversations,
    handleDeleteConversation,
    handleRenameConversation,
    handleArchiveConversation,
  } = useChat();
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem("sidebarCollapsed") === "true";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const [editingConvId, setEditingConvId] = useState(null);
  const [editTitle, setEditTitle] = useState("");
  const [searchQuery, setSearchQuery] = useState("");

  useEffect(() => {
    localStorage.setItem("sidebarCollapsed", isCollapsed);
  }, [isCollapsed]);

  // Close mobile menu on route change
  useEffect(() => {
    setMobileMenuOpen(false);
  }, [location.pathname]);

  const handleSignOut = async () => {
    await signOut();
    navigate("/login");
  };

  const toggleSidebar = () => setIsCollapsed(!isCollapsed);

  const handleRenameSubmit = async (convId) => {
    if (!editTitle.trim()) {
      setEditingConvId(null);
      return;
    }
    await handleRenameConversation(convId, editTitle);
    setEditingConvId(null);
  };

  const onDeleteClick = async (e, convId) => {
    e.preventDefault();
    e.stopPropagation();
    if (window.confirm("Are you sure you want to delete this conversation?")) {
      const success = await handleDeleteConversation(convId);
      if (success && location.pathname === `/assistant/${convId}`) {
        navigate("/assistant", { replace: true });
      }
    }
  };

  const onArchiveClick = async (e, convId) => {
    e.preventDefault();
    e.stopPropagation();
    const result = await handleArchiveConversation(convId);
    if (result && location.pathname === `/assistant/${convId}`) {
      navigate("/assistant", { replace: true });
    }
  };

  const isAssistantActive = location.pathname.startsWith("/assistant");

  const sortedConversations = [...conversations].sort(
    (a, b) => new Date(b.updated_at) - new Date(a.updated_at)
  );
  const filteredConversations = sortedConversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const grouped = groupConversationsByDate(filteredConversations);
  const groupOrder = ["Today", "Yesterday", "This Week", "Older"];

  const renderConvItem = (conv) => (
    <NavLink
      key={conv.id}
      to={`/assistant/${conv.id}`}
      className={({ isActive }) =>
        `sidebar-subnav-item${isActive ? " active" : ""}`
      }
    >
      <MessageSquare size={14} className="subnav-icon" />
      {editingConvId === conv.id ? (
        <input
          autoFocus
          className="subnav-title-input"
          value={editTitle}
          onChange={(e) => setEditTitle(e.target.value)}
          onBlur={() => handleRenameSubmit(conv.id)}
          onKeyDown={(e) => {
            if (e.key === "Enter") handleRenameSubmit(conv.id);
            if (e.key === "Escape") setEditingConvId(null);
          }}
          onClick={(e) => e.preventDefault() || e.stopPropagation()}
        />
      ) : (
        <span className="subnav-title">{conv.title}</span>
      )}

      {!editingConvId && (
        <div className="subnav-actions">
          <button
            className="subnav-action-btn"
            onClick={(e) => {
              e.preventDefault();
              e.stopPropagation();
              setEditingConvId(conv.id);
              setEditTitle(conv.title);
            }}
            title="Rename chat"
          >
            <Edit2 size={12} />
          </button>
          <button
            className="subnav-action-btn"
            onClick={(e) => onArchiveClick(e, conv.id)}
            title="Archive chat"
          >
            <Archive size={12} />
          </button>
          <button
            className="subnav-action-btn delete-btn"
            onClick={(e) => onDeleteClick(e, conv.id)}
            title="Delete chat"
          >
            <Trash2 size={12} />
          </button>
        </div>
      )}
    </NavLink>
  );

  return (
    <div className={`app-shell ${isCollapsed ? "sidebar-collapsed" : ""}`}>
      {/* Mobile Top Bar */}
      <div className="mobile-top-bar" style={{ display: "none" }}>
        <button
          className="mobile-menu-btn"
          onClick={() => setMobileMenuOpen(true)}
        >
          <Menu size={24} />
        </button>
        <img src="/foraa%20logo.png" alt="Foraa" style={{ height: "24px" }} />
        <div style={{ width: 24 }}></div>
      </div>

      {/* Mobile Overlay */}
      {mobileMenuOpen && (
        <div
          className="sidebar-overlay"
          onClick={() => setMobileMenuOpen(false)}
          style={{
            position: "fixed",
            inset: 0,
            backgroundColor: "rgba(0,0,0,0.5)",
            zIndex: 99,
          }}
        />
      )}

      <aside className={`sidebar ${mobileMenuOpen ? "mobile-open" : ""}`}>
        <div className="sidebar-brand">
          {!isCollapsed ? (
            <img src="/foraa%20logo.png" alt="Foraa" className="sidebar-logo" style={{ height: "56px", objectFit: "contain" }} />
          ) : (
            <img
              src="/foraa%20logo.png"
              alt="Foraa"
              className="sidebar-logo-small"
              style={{ width: "32px", height: "32px", objectFit: "contain" }}
            />
          )}

          <button className="sidebar-toggle" onClick={toggleSidebar}>
            {isCollapsed ? (
              <ChevronRight size={16} />
            ) : (
              <ChevronLeft size={16} />
            )}
          </button>
        </div>

        <nav className="sidebar-nav">
          {mainNav.map((item) => (
            <div key={item.path} style={{ display: "flex", flexDirection: "column" }}>
              <NavLink
                to={item.path}
                end={item.path === "/"}
                className={({ isActive }) =>
                  `sidebar-nav-item${isActive || (item.path === "/assistant" && isAssistantActive) ? " active" : ""}`
                }
                title={isCollapsed ? item.name : undefined}
              >
                <span className="sidebar-nav-icon">
                  <item.icon size={20} />
                </span>
                {!isCollapsed && (
                  <span className="sidebar-nav-label">{item.name}</span>
                )}
              </NavLink>

              {/* Submenu for Assistant */}
              {item.path === "/assistant" && isAssistantActive && !isCollapsed && (
                <div className="sidebar-subnav">
                  <button
                    className="sidebar-new-chat-btn"
                    onClick={() => navigate("/assistant")}
                  >
                    <Plus size={16} />
                    <span>New Chat</span>
                  </button>

                  <div className="sidebar-subnav-list">
                    <div className="sidebar-search">
                      <Search size={14} className="sidebar-search-icon" />
                      <input
                        type="text"
                        placeholder="Search chats..."
                        className="sidebar-search-input"
                        value={searchQuery}
                        onChange={(e) => setSearchQuery(e.target.value)}
                      />
                    </div>

                    {/* Grouped conversations */}
                    {groupOrder.map((group) => {
                      const groupConvs = grouped[group];
                      if (!groupConvs || groupConvs.length === 0) return null;
                      return (
                        <div key={group}>
                          <span className="sidebar-subnav-label">{group.toUpperCase()}</span>
                          {groupConvs.map(renderConvItem)}
                        </div>
                      );
                    })}

                    {filteredConversations.length === 0 && (
                      <div className="sidebar-subnav-empty">No recent chats</div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `sidebar-nav-item${isActive ? " active" : ""}`
          }
          title={isCollapsed ? "Settings" : undefined}
        >
          <span className="sidebar-nav-icon">
            <Settings size={20} />
          </span>
          {!isCollapsed && <span className="sidebar-nav-label">Settings</span>}
        </NavLink>

        <div className="sidebar-profile">
          <div className="sidebar-profile-avatar">
            {user?.user_metadata?.avatar_url ? (
              <img
                src={user.user_metadata.avatar_url}
                alt="Avatar"
                style={{ width: "100%", height: "100%", borderRadius: "50%" }}
              />
            ) : (
              <User size={16} />
            )}
          </div>
          {!isCollapsed && (
            <>
              <div className="sidebar-profile-info">
                <strong>
                  {user?.user_metadata?.full_name ||
                    user?.email ||
                    "Your Profile"}
                </strong>
                <span>Health workspace</span>
              </div>
              <button
                onClick={handleSignOut}
                className="sidebar-logout"
                title="Sign Out"
              >
                <LogOut size={16} />
              </button>
            </>
          )}
        </div>
      </aside>

      <main
        className={`main-content ${location.pathname.startsWith("/assistant") ? "main-content--no-padding" : ""}`}
      >
        <Outlet />
      </main>

      {!location.pathname.startsWith("/assistant") && <QuickAddLog />}

      <MobileNav />
    </div>
  );
}

export default Layout;
