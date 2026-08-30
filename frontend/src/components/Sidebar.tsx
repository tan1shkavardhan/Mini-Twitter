import {
  Bell,
  Bookmark,
  Compass,
  House,
  LogOut,
  MessageCircle,
  Search,
  User,
} from "lucide-react";

import { useAuth } from "../context/AuthContext";

function Sidebar() {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <aside className="sidebar">
      <div>
        <div className="logo">
          <div className="logo-icon">
            <MessageCircle size={23} />
          </div>

          <span>Ripple</span>
        </div>

        <nav className="nav-menu">
          <button className="nav-item active">
            <House size={21} />
            <span>Home</span>
          </button>

          <button className="nav-item">
            <Search size={21} />
            <span>Explore</span>
          </button>

          <button className="nav-item">
            <Compass size={21} />
            <span>Discover</span>
          </button>

          <button className="nav-item">
            <Bell size={21} />
            <span>Notifications</span>
          </button>

          <button className="nav-item">
            <Bookmark size={21} />
            <span>Bookmarks</span>
          </button>

          <button className="nav-item">
            <User size={21} />
            <span>Profile</span>
          </button>
        </nav>
      </div>

      <div className="sidebar-bottom">
        <div className="current-user">
          <div className="avatar">
            {user?.username?.charAt(0).toUpperCase()}
          </div>

          <div className="current-user-info">
            <strong>{user?.username}</strong>
            <span>@{user?.username}</span>
          </div>
        </div>

        <button
          className="logout-button"
          onClick={handleLogout}
        >
          <LogOut size={19} />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}

export default Sidebar;