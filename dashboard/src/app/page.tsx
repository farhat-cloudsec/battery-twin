"use client";

import { useEffect, useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts";

const API_BASE = "http://127.0.0.1:8000";
const CELL_ID = "cell1";

type Latest = {
  time: string;
  voltage: number;
  current: number;
  temperature: number;
  soc: number | null;
  expected_voltage: number | null;
  residual: number | null;
  soh: number | null;
};

type HistoryPoint = {
  time: string;
  voltage: number;
  expected_voltage: number | null;
  soh: number | null;
};

type Alert = {
  id: number;
  time: string;
  cell_id: string;
  severity: string;
  message: string;
};

export default function Home() {
  // The token lives only in memory (React state), so it is gone after a page refresh.
  const [token, setToken] = useState<string | null>(null);
  const [username, setUsername] = useState("admin");
  const [password, setPassword] = useState("");
  const [loginError, setLoginError] = useState("");

  const [latest, setLatest] = useState<Latest | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoginError("");
    try {
      const res = await fetch(`${API_BASE}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username, password }),
      });
      if (!res.ok) {
        setLoginError("Incorrect username or password");
        return;
      }
      const data = await res.json();
      setToken(data.access_token);
      setPassword("");
    } catch {
      setLoginError("Could not reach the API. Is it running?");
    }
  };

  const handleLogout = () => {
    setToken(null);
    setLatest(null);
    setHistory([]);
    setAlerts([]);
  };

  useEffect(() => {
    if (!token) return;

    const fetchData = async () => {
      const headers = { Authorization: `Bearer ${token}` };
      try {
        const [latestRes, historyRes, alertsRes] = await Promise.all([
          fetch(`${API_BASE}/cells/${CELL_ID}/latest`, { headers }),
          fetch(`${API_BASE}/cells/${CELL_ID}/history?minutes=5`, { headers }),
          fetch(`${API_BASE}/alerts?limit=10`, { headers }),
        ]);
        if ([latestRes, historyRes, alertsRes].some((r) => r.status === 401)) {
          handleLogout(); // token expired or invalid
          return;
        }
        if (latestRes.ok) setLatest(await latestRes.json());
        if (historyRes.ok) setHistory(await historyRes.json());
        if (alertsRes.ok) setAlerts(await alertsRes.json());
      } catch (err) {
        console.error("Failed to fetch data:", err);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, [token]);

  if (!token) {
    return (
      <div className="min-h-screen bg-zinc-50 flex items-center justify-center font-sans">
        <form
          onSubmit={handleLogin}
          className="bg-white rounded-lg border border-zinc-200 p-8 w-80 space-y-4"
        >
          <h1 className="text-xl font-semibold">Battery Digital Twin</h1>
          <p className="text-sm text-zinc-500">Sign in to view the dashboard.</p>
          <input
            className="w-full border border-zinc-300 rounded px-3 py-2 text-sm"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
          />
          <input
            className="w-full border border-zinc-300 rounded px-3 py-2 text-sm"
            placeholder="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
          {loginError && <p className="text-sm text-red-600">{loginError}</p>}
          <button
            type="submit"
            className="w-full bg-black text-white rounded py-2 text-sm font-medium"
          >
            Sign in
          </button>
        </form>
      </div>
    );
  }

  const chartData = history.map((h) => ({
    time: new Date(h.time).toLocaleTimeString(),
    measured: h.voltage,
    expected: h.expected_voltage,
  }));

  return (
    <div className="min-h-screen bg-zinc-50 p-8 font-sans">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">
          Battery Digital Twin — {CELL_ID}
        </h1>
        <button
          onClick={handleLogout}
          className="text-sm border border-zinc-300 rounded px-3 py-1 bg-white"
        >
          Sign out
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-5 gap-4 mb-8">
        <Kpi label="Voltage" value={latest?.voltage} unit="V" />
        <Kpi label="Current" value={latest?.current} unit="A" />
        <Kpi label="Temperature" value={latest?.temperature} unit="°C" />
        <Kpi label="SoC" value={latest?.soc} unit="%" />
        <Kpi label="SoH" value={latest?.soh} unit="%" />
      </div>

      <div className="bg-white rounded-lg border border-zinc-200 p-4 mb-8">
        <h2 className="text-sm font-medium mb-3">
          Voltage: measured vs twin expected
        </h2>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis dataKey="time" tick={{ fontSize: 11 }} />
            <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Legend />
            <Line
              type="monotone"
              dataKey="measured"
              stroke="#eb6834"
              dot={false}
              name="Measured"
            />
            <Line
              type="monotone"
              dataKey="expected"
              stroke="#2a78d6"
              dot={false}
              name="Twin expected"
            />
          </LineChart>
        </ResponsiveContainer>
      </div>

      <div className="bg-white rounded-lg border border-zinc-200 p-4">
        <h2 className="text-sm font-medium mb-3">Alerts</h2>
        {alerts.length === 0 ? (
          <p className="text-sm text-zinc-500">No alerts.</p>
        ) : (
          <ul className="divide-y divide-zinc-100">
            {alerts.map((a) => (
              <li key={a.id} className="py-2 flex items-center gap-3 text-sm">
                <span className="text-zinc-500 w-20">
                  {new Date(a.time).toLocaleTimeString()}
                </span>
                <span className="px-2 py-0.5 rounded bg-red-100 text-red-700 text-xs font-medium">
                  {a.severity}
                </span>
                <span>{a.message}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

function Kpi({
  label,
  value,
  unit,
}: {
  label: string;
  value: number | null | undefined;
  unit: string;
}) {
  return (
    <div className="bg-white rounded-lg border border-zinc-200 p-4">
      <div className="text-xs text-zinc-500">{label}</div>
      <div className="text-xl font-semibold">
        {value != null ? `${value.toFixed(2)} ${unit}` : "—"}
      </div>
    </div>
  );
}