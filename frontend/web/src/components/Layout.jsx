import { NavLink } from "react-router-dom";
import {
  Sparkles,
  Home,
  MessageSquare,
  Heart,
  FileText,
  Apple,
  Sun,
  Settings,
  User,
} from "lucide-react";
import MobileNav from "./MobileNav";

const mainNav = [
  { name: "Home", path: "/", icon: Home },
  { name: "Health Assistant", path: "/assistant", icon: MessageSquare },
  { name: "My Health", path: "/health", icon: Heart },
  { name: "Reports", path: "/reports", icon: FileText },
  { name: "Nutrition", path: "/nutrition", icon: Apple },
  { name: "Wellness", path: "/wellness", icon: Sun },
];

function Layout({ children }) {
  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          <div className="sidebar-brand-mark">
            <Sparkles size={18} />
          </div>
          <div>
            <div className="sidebar-brand-name">forraa</div>
            <div className="sidebar-brand-sub">healthcare intelligence</div>
          </div>
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
            >
              <span className="sidebar-nav-icon">
                <item.icon size={18} />
              </span>
              {item.name}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-divider" />

        <NavLink
          to="/settings"
          className={({ isActive }) =>
            `sidebar-nav-item${isActive ? " active" : ""}`
          }
        >
          <span className="sidebar-nav-icon">
            <Settings size={18} />
          </span>
          Settings
        </NavLink>

        <div className="sidebar-profile">
          <div className="sidebar-profile-avatar">
            <User size={16} />
          </div>
          <div className="sidebar-profile-info">
            <strong>Your Profile</strong>
            <span>Health workspace</span>
          </div>
        </div>
      </aside>

      <main className="main-content">{children}</main>

      <MobileNav />
    </div>
  );
}

export default Layout;