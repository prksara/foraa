import { NavLink, useNavigate } from "react-router-dom";
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
  LogOut,
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

function Layout({ children }) {
  const { user, signOut } = useAuth();
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await signOut();
    navigate('/login');
  };

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
            {user?.user_metadata?.avatar_url ? (
               <img src={user.user_metadata.avatar_url} alt="Avatar" style={{width: '100%', height: '100%', borderRadius: '50%'}}/>
            ) : (
               <User size={16} />
            )}
          </div>
          <div className="sidebar-profile-info">
            <strong>{user?.user_metadata?.full_name || user?.email || 'Your Profile'}</strong>
            <span>Health workspace</span>
          </div>
          <button onClick={handleSignOut} className="sidebar-logout" style={{ background: 'none', border: 'none', color: 'var(--color-text-secondary)', cursor: 'pointer', padding: '4px' }} title="Sign Out">
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      <main className="main-content">{children}</main>

      <MobileNav />
    </div>
  );
}

export default Layout;