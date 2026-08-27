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
} from "lucide-react";
import MobileNav from "./MobileNav";
import { useAuth } from "../contexts/AuthContext";

const mainNav = [
  { name: "Home", path: "/", icon: Home },
  { name: "Health Assistant", path: "/assistant", icon: MessageSquare },
  { name: "My Health", path: "/health", icon: Heart },
  { name: "Reports", path: "/reports", icon: FileText },
  { name: "Nutrition", path: "/nutrition", icon: Apple },
  { name: "Wellness", path: "/wellness", icon: Sun },
];

function Layout() {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [isCollapsed, setIsCollapsed] = useState(() => {
    return localStorage.getItem("sidebarCollapsed") === "true";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

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
            <img src="/foraa%20logo.png" alt="Foraa" className="sidebar-logo" />
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
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === "/"}
              className={({ isActive }) =>
                `sidebar-nav-item${isActive ? " active" : ""}`
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
        className={`main-content ${location.pathname === "/assistant" ? "main-content--no-padding" : ""}`}
      >
        <Outlet />
      </main>

      <MobileNav />
    </div>
  );
}

export default Layout;
