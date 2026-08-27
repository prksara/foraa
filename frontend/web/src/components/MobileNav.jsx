import { NavLink } from "react-router-dom";
import { Home, Sparkles, Heart, FileText, Settings } from "lucide-react";

const navItems = [
  { path: "/", icon: Home, label: "Home" },
  { path: "/assistant", icon: Sparkles, label: "Assistant" },
  { path: "/health", icon: Heart, label: "Health" },
  { path: "/reports", icon: FileText, label: "Reports" },
  { path: "/settings", icon: Settings, label: "Settings" },
];

function MobileNav() {
  return (
    <nav className="mobile-nav">
      {navItems.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          end={item.path === "/"}
          className={({ isActive }) =>
            `mobile-nav__item${isActive ? " active" : ""}`
          }
        >
          <item.icon size={20} />
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}

export default MobileNav;
