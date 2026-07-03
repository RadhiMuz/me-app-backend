import { useState, useEffect } from "react";

const API = "http://172.16.4.113:8000/api/auth";

const APPS = [
  {
    id: "checksheet",
    title: "PM Checksheet",
    subtitle: "Preventive Maintenance",
    description: "Conduct inspections, log OK/NG results and track history across production lines.",
    url: "http://172.16.4.113:5173",
    icon: "📋",
    color: "#1d4ed8",
    light: "#eff6ff",
    features: ["Line inspections", "OK/NG tracking", "Measurement records"],
  },
  {
    id: "spareparts",
    title: "Spare Parts",
    subtitle: "Inventory Management",
    description: "Track stock levels, receive low stock alerts and record parts taken from inventory.",
    url: "http://172.16.4.113:5174",
    icon: "🔧",
    color: "#059669",
    light: "#ecfdf5",
    features: ["Stock tracking", "Low stock alerts", "Stock out records"],
  },
];

// ── Auth API ──────────────────────────────────────────────────────────────────
async function apiLogin(username, password) {
  const form = new URLSearchParams();
  form.append("username", username);
  form.append("password", password);
  const res = await fetch(`${API}/login`, { method: "POST", body: form });
  if (!res.ok) {
    const err = await res.json();
    throw new Error(err.detail || "Login failed");
  }
  return res.json();
}

async function apiGetUsers(token) {
  const res = await fetch(`${API}/users`, { headers: { Authorization: `Bearer ${token}` } });
  if (!res.ok) throw new Error("Failed to load users");
  return res.json();
}

async function apiCreateUser(token, data) {
  const res = await fetch(`${API}/users`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Failed"); }
  return res.json();
}

async function apiToggleUser(token, id) {
  const res = await fetch(`${API}/users/${id}/toggle`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!res.ok) throw new Error("Failed");
  return res.json();
}

async function apiDeleteUser(token, id) {
  await fetch(`${API}/users/${id}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${token}` },
  });
}

async function apiChangePassword(token, current_password, new_password) {
  const res = await fetch(`${API}/change-password`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ current_password, new_password }),
  });
  if (!res.ok) { const e = await res.json(); throw new Error(e.detail || "Failed"); }
  return res.json();
}

// ── Styles ────────────────────────────────────────────────────────────────────
const input = {
  width: "100%", padding: "11px 14px", border: "1.5px solid #e5e7eb",
  borderRadius: 10, fontSize: 14, color: "#111", background: "#fff",
  fontFamily: "'DM Sans', sans-serif", boxSizing: "border-box", outline: "none",
};

// ── Login Page ────────────────────────────────────────────────────────────────
function LoginPage({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e) => {
    e.preventDefault();
    if (!username || !password) return;
    setLoading(true); setError("");
    try {
      const data = await apiLogin(username, password);
      localStorage.setItem("token", data.access_token);
      localStorage.setItem("username", data.username);
      localStorage.setItem("full_name", data.full_name);
      onLogin(data);
    } catch (e) {
      setError(e.message);
    } finally { setLoading(false); }
  };

  return (
    <div style={{
      minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center",
      background: "linear-gradient(135deg, #1e3a8a 0%, #1d4ed8 50%, #0369a1 100%)",
      fontFamily: "'DM Sans', sans-serif", padding: 16,
    }}>
      <div style={{ width: "100%", maxWidth: 380 }}>
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 48, marginBottom: 12 }}>🏭</div>
          <h1 style={{ margin: 0, fontSize: 26, fontWeight: 800, color: "#fff", letterSpacing: "-0.03em" }}>Factory Apps</h1>
          <p style={{ margin: "6px 0 0", fontSize: 14, color: "rgba(255,255,255,0.7)" }}>Sign in to continue</p>
        </div>

        {/* Card */}
        <div style={{ background: "#fff", borderRadius: 16, padding: 28, boxShadow: "0 24px 48px rgba(0,0,0,0.2)" }}>
          {error && (
            <div style={{ background: "#fee2e2", color: "#7f1d1d", borderRadius: 8, padding: "10px 14px", fontSize: 13, fontWeight: 600, marginBottom: 16 }}>
              ⚠ {error}
            </div>
          )}
          <form onSubmit={handleLogin}>
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#6b7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Username</label>
              <input style={input} placeholder="Enter username" value={username} onChange={e => setUsername(e.target.value)} autoComplete="username" />
            </div>
            <div style={{ marginBottom: 20 }}>
              <label style={{ display: "block", fontSize: 12, fontWeight: 700, color: "#6b7280", marginBottom: 6, textTransform: "uppercase", letterSpacing: "0.04em" }}>Password</label>
              <input style={input} type="password" placeholder="Enter password" value={password} onChange={e => setPassword(e.target.value)} autoComplete="current-password" />
            </div>
            <button type="submit" disabled={loading || !username || !password} style={{
              width: "100%", padding: "12px 0", borderRadius: 10, border: "none",
              background: loading ? "#93c5fd" : "#1d4ed8", color: "#fff",
              fontWeight: 800, fontSize: 15, cursor: loading ? "not-allowed" : "pointer",
              fontFamily: "'DM Sans', sans-serif", letterSpacing: "-0.01em",
            }}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>
        </div>

        <p style={{ textAlign: "center", marginTop: 16, fontSize: 12, color: "rgba(255,255,255,0.5)" }}>
          Contact your administrator for access
        </p>
      </div>
    </div>
  );
}

// ── App Card ─────────────────────────────────────────────────────────────────
function AppCard({ app }) {
  return (
    <a href={app.url} style={{ textDecoration: "none" }}>
      <div style={{
        background: "#fff", borderRadius: 14, padding: 22,
        border: "1.5px solid #f0f0f0", cursor: "pointer",
        borderTop: `3px solid ${app.color}`,
        boxShadow: "0 2px 8px rgba(0,0,0,0.05)",
        transition: "all 0.15s",
      }}
        onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.boxShadow = "0 10px 24px rgba(0,0,0,0.1)"; }}
        onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.boxShadow = "0 2px 8px rgba(0,0,0,0.05)"; }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: app.light, display: "flex", alignItems: "center", justifyContent: "center", fontSize: 22, flexShrink: 0 }}>
            {app.icon}
          </div>
          <div>
            <div style={{ fontWeight: 800, fontSize: 16, color: "#111", letterSpacing: "-0.02em" }}>{app.title}</div>
            <div style={{ fontSize: 12, color: app.color, fontWeight: 600 }}>{app.subtitle}</div>
          </div>
        </div>
        <p style={{ margin: "0 0 14px", fontSize: 13, color: "#6b7280", lineHeight: 1.6 }}>{app.description}</p>
        <div style={{ display: "flex", flexDirection: "column", gap: 4, marginBottom: 16 }}>
          {app.features.map(f => (
            <div key={f} style={{ display: "flex", alignItems: "center", gap: 7, fontSize: 12, color: "#374151" }}>
              <span style={{ width: 5, height: 5, borderRadius: "50%", background: app.color, flexShrink: 0 }} />{f}
            </div>
          ))}
        </div>
        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "8px 12px", background: app.light, borderRadius: 8 }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: app.color }}>Open {app.title}</span>
          <span style={{ color: app.color, fontWeight: 700 }}>→</span>
        </div>
      </div>
    </a>
  );
}

// ── User Management Modal ─────────────────────────────────────────────────────
function UserModal({ token, onClose }) {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [newUser, setNewUser] = useState({ username: "", full_name: "", password: "" });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [tab, setTab] = useState("users"); // users | add | password
  const [pwForm, setPwForm] = useState({ current: "", next: "", confirm: "" });
  const [pwError, setPwError] = useState("");
  const [pwSuccess, setPwSuccess] = useState(false);

  useEffect(() => {
    apiGetUsers(token).then(setUsers).finally(() => setLoading(false));
  }, []);

  const handleAdd = async () => {
    if (!newUser.username || !newUser.password) return;
    setSaving(true); setError("");
    try {
      const u = await apiCreateUser(token, newUser);
      setUsers(us => [...us, u]);
      setNewUser({ username: "", full_name: "", password: "" });
      setTab("users");
    } catch (e) { setError(e.message); }
    finally { setSaving(false); }
  };

  const handleToggle = async (id) => {
    const u = await apiToggleUser(token, id);
    setUsers(us => us.map(x => x.id === id ? u : x));
  };

  const handleDelete = async (id) => {
    if (!confirm("Delete this user?")) return;
    await apiDeleteUser(token, id);
    setUsers(us => us.filter(x => x.id !== id));
  };

  const handleChangePassword = async () => {
    if (pwForm.next !== pwForm.confirm) { setPwError("Passwords don't match"); return; }
    if (pwForm.next.length < 6) { setPwError("Password must be at least 6 characters"); return; }
    setSaving(true); setPwError("");
    try {
      await apiChangePassword(token, pwForm.current, pwForm.next);
      setPwSuccess(true);
      setPwForm({ current: "", next: "", confirm: "" });
    } catch (e) { setPwError(e.message); }
    finally { setSaving(false); }
  };

  return (
    <div style={{ position: "fixed", inset: 0, zIndex: 100, background: "rgba(0,0,0,0.45)", display: "flex", alignItems: "center", justifyContent: "center", padding: 16 }}
      onClick={e => e.target === e.currentTarget && onClose()}>
      <div style={{ background: "#fff", borderRadius: 16, width: "100%", maxWidth: 480, maxHeight: "85vh", display: "flex", flexDirection: "column", boxShadow: "0 24px 48px rgba(0,0,0,0.2)" }}>
        <div style={{ padding: "14px 18px", borderBottom: "1px solid #f0f0f0", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <span style={{ fontWeight: 800, fontSize: 15, color: "#111" }}>Account Settings</span>
          <button onClick={onClose} style={{ border: "none", background: "#f5f5f5", borderRadius: 8, width: 30, height: 30, cursor: "pointer", fontSize: 18, color: "#555", display: "flex", alignItems: "center", justifyContent: "center" }}>×</button>
        </div>

        {/* Tabs */}
        <div style={{ display: "flex", borderBottom: "1px solid #f0f0f0" }}>
          {[["users", "Users"], ["add", "Add User"], ["password", "Change Password"]].map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)} style={{
              flex: 1, padding: "10px 0", border: "none", background: "transparent",
              fontWeight: 700, fontSize: 12, cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
              color: tab === id ? "#1d4ed8" : "#9ca3af",
              borderBottom: tab === id ? "2px solid #1d4ed8" : "2px solid transparent",
            }}>{label}</button>
          ))}
        </div>

        <div style={{ flex: 1, overflowY: "auto", padding: 18 }}>
          {tab === "users" && (
            loading ? <div style={{ textAlign: "center", color: "#9ca3af", padding: 24 }}>Loading...</div> :
            <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
              {users.map(u => (
                <div key={u.id} style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 14px", border: "1.5px solid #f0f0f0", borderRadius: 10, background: u.is_active ? "#fff" : "#f9fafb" }}>
                  <div style={{ width: 34, height: 34, borderRadius: "50%", background: u.is_active ? "#eff6ff" : "#f3f4f6", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 14, fontWeight: 800, color: u.is_active ? "#1d4ed8" : "#9ca3af", flexShrink: 0 }}>
                    {u.username[0].toUpperCase()}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: 700, fontSize: 13, color: u.is_active ? "#111" : "#9ca3af" }}>{u.full_name || u.username}</div>
                    <div style={{ fontSize: 11, color: "#9ca3af" }}>@{u.username} · {u.is_active ? "Active" : "Disabled"}</div>
                  </div>
                  <button onClick={() => handleToggle(u.id)} style={{ padding: "4px 10px", fontSize: 11, fontWeight: 600, border: "1.5px solid #e5e7eb", borderRadius: 6, background: "#fff", color: "#374151", cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                    {u.is_active ? "Disable" : "Enable"}
                  </button>
                  <button onClick={() => handleDelete(u.id)} style={{ padding: "4px 10px", fontSize: 11, fontWeight: 600, border: "1.5px solid #fecaca", borderRadius: 6, background: "#fff", color: "#ef4444", cursor: "pointer", fontFamily: "'DM Sans', sans-serif" }}>
                    Delete
                  </button>
                </div>
              ))}
            </div>
          )}

          {tab === "add" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {error && <div style={{ background: "#fee2e2", color: "#7f1d1d", borderRadius: 8, padding: "9px 13px", fontSize: 13 }}>⚠ {error}</div>}
              {[
                { label: "Username *", key: "username", type: "text", placeholder: "e.g. john" },
                { label: "Full Name", key: "full_name", type: "text", placeholder: "e.g. John Smith" },
                { label: "Password *", key: "password", type: "password", placeholder: "Min 6 characters" },
              ].map(f => (
                <div key={f.key}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#6b7280", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.04em" }}>{f.label}</label>
                  <input type={f.type} style={input} placeholder={f.placeholder} value={newUser[f.key]} onChange={e => setNewUser(u => ({ ...u, [f.key]: e.target.value }))} />
                </div>
              ))}
              <button onClick={handleAdd} disabled={saving || !newUser.username || !newUser.password} style={{
                padding: "10px 0", borderRadius: 10, border: "none",
                background: !newUser.username || !newUser.password ? "#c7d2fe" : "#1d4ed8",
                color: "#fff", fontWeight: 700, fontSize: 14, cursor: "pointer",
                fontFamily: "'DM Sans', sans-serif", marginTop: 4,
              }}>{saving ? "Creating..." : "Create User"}</button>
            </div>
          )}

          {tab === "password" && (
            <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
              {pwError && <div style={{ background: "#fee2e2", color: "#7f1d1d", borderRadius: 8, padding: "9px 13px", fontSize: 13 }}>⚠ {pwError}</div>}
              {pwSuccess && <div style={{ background: "#d1fae5", color: "#065f46", borderRadius: 8, padding: "9px 13px", fontSize: 13, fontWeight: 600 }}>✓ Password changed successfully</div>}
              {[
                { label: "Current Password", key: "current", val: pwForm.current },
                { label: "New Password", key: "next", val: pwForm.next },
                { label: "Confirm New Password", key: "confirm", val: pwForm.confirm },
              ].map(f => (
                <div key={f.key}>
                  <label style={{ display: "block", fontSize: 11, fontWeight: 700, color: "#6b7280", marginBottom: 5, textTransform: "uppercase", letterSpacing: "0.04em" }}>{f.label}</label>
                  <input type="password" style={input} value={f.val} onChange={e => setPwForm(p => ({ ...p, [f.key]: e.target.value }))} />
                </div>
              ))}
              <button onClick={handleChangePassword} disabled={saving} style={{
                padding: "10px 0", borderRadius: 10, border: "none",
                background: "#1d4ed8", color: "#fff", fontWeight: 700, fontSize: 14,
                cursor: "pointer", fontFamily: "'DM Sans', sans-serif", marginTop: 4,
              }}>{saving ? "Saving..." : "Change Password"}</button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ── Home Page ─────────────────────────────────────────────────────────────────
function HomePage({ user, onLogout }) {
  const [showSettings, setShowSettings] = useState(false);
  const token = localStorage.getItem("token");

  return (
    <div style={{ minHeight: "100vh", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Top bar */}
      <div style={{ background: "#fff", borderBottom: "1.5px solid #f0f0f0", padding: "12px 24px", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <span style={{ fontSize: 22 }}>🏭</span>
          <div>
            <div style={{ fontWeight: 800, fontSize: 15, color: "#111", letterSpacing: "-0.02em" }}>Factory Apps</div>
            <div style={{ fontSize: 11, color: "#9ca3af" }}>Production Management System</div>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ textAlign: "right", display: "none" }}>
            <div style={{ fontSize: 13, fontWeight: 700, color: "#111" }}>{user.full_name || user.username}</div>
            <div style={{ fontSize: 11, color: "#9ca3af" }}>@{user.username}</div>
          </div>
          <button onClick={() => setShowSettings(true)} style={{
            display: "flex", alignItems: "center", gap: 6, padding: "7px 14px",
            borderRadius: 9, border: "1.5px solid #e5e7eb", background: "#fff",
            color: "#374151", fontWeight: 600, fontSize: 13, cursor: "pointer",
            fontFamily: "'DM Sans', sans-serif",
          }}>
            <span style={{ width: 26, height: 26, borderRadius: "50%", background: "#eff6ff", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 12, fontWeight: 800, color: "#1d4ed8" }}>
              {(user.full_name || user.username)[0].toUpperCase()}
            </span>
            {user.full_name || user.username}
          </button>
          <button onClick={onLogout} style={{
            padding: "7px 14px", borderRadius: 9, border: "1.5px solid #fecaca",
            background: "#fff", color: "#ef4444", fontWeight: 600, fontSize: 13,
            cursor: "pointer", fontFamily: "'DM Sans', sans-serif",
          }}>Sign Out</button>
        </div>
      </div>

      {/* Content */}
      <div style={{ maxWidth: 760, margin: "0 auto", padding: "36px 24px" }}>
        <div style={{ marginBottom: 28 }}>
          <h2 style={{ margin: 0, fontSize: 24, fontWeight: 800, color: "#111", letterSpacing: "-0.03em" }}>
            Welcome back, {user.full_name?.split(" ")[0] || user.username} 👋
          </h2>
          <p style={{ margin: "6px 0 0", fontSize: 14, color: "#6b7280" }}>Select an application to get started</p>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(300px, 1fr))", gap: 16 }}>
          {APPS.map(app => <AppCard key={app.id} app={app} />)}
        </div>

        <div style={{ marginTop: 36, padding: "16px 20px", background: "#fff", borderRadius: 12, border: "1.5px solid #f0f0f0", display: "flex", alignItems: "center", justifyContent: "space-between", flexWrap: "wrap", gap: 8 }}>
          <div style={{ fontSize: 13, color: "#6b7280" }}>
            <span style={{ fontWeight: 600, color: "#111" }}>Server:</span> 172.16.4.113 &nbsp;·&nbsp;
            <span style={{ fontWeight: 600, color: "#111" }}>Backend:</span> :8000
          </div>
          <div style={{ display: "flex", gap: 8 }}>
            {[["PM Checksheet", 5173, "#1d4ed8"], ["Spare Parts", 5174, "#059669"]].map(([name, port, color]) => (
              <div key={port} style={{ fontSize: 11, fontWeight: 600, color, background: color + "15", padding: "3px 10px", borderRadius: 6 }}>
                {name} :{port}
              </div>
            ))}
          </div>
        </div>
      </div>

      {showSettings && <UserModal token={token} onClose={() => setShowSettings(false)} />}
    </div>
  );
}

// ── Root ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    const token = localStorage.getItem("token");
    const username = localStorage.getItem("username");
    const full_name = localStorage.getItem("full_name");
    if (token && username) {
      // Verify token is still valid
      fetch(`${API}/me`, { headers: { Authorization: `Bearer ${token}` } })
        .then(r => r.ok ? setUser({ username, full_name }) : handleLogout())
        .catch(() => handleLogout())
        .finally(() => setChecking(false));
    } else {
      setChecking(false);
    }
  }, []);

  const handleLogin = (data) => setUser({ username: data.username, full_name: data.full_name });

  const handleLogout = () => {
    localStorage.removeItem("token");
    localStorage.removeItem("username");
    localStorage.removeItem("full_name");
    setUser(null);
  };

  if (checking) return (
    <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center", background: "#f8fafc", fontFamily: "'DM Sans', sans-serif" }}>
      <div style={{ color: "#9ca3af", fontSize: 14 }}>Loading...</div>
    </div>
  );

  return user ? <HomePage user={user} onLogout={handleLogout} /> : <LoginPage onLogin={handleLogin} />;
}