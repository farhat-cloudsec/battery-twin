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
  const [latest, setLatest] = useState<Latest | null>(null);
  const [history, setHistory] = useState<HistoryPoint[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [latestRes, historyRes, alertsRes] = await Promise.all([
          fetch(`${API_BASE}/cells/${CELL_ID}/latest`),
          fetch(`${API_BASE}/cells/${CELL_ID}/history?minutes=5`),
          fetch(`${API_BASE}/alerts?limit=10`),
        ]);
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
  }, []);

  const chartData = history.map((h) => ({
    time: new Date(h.time).toLocaleTimeString(),
    measured: h.voltage,
    expected: h.expected_voltage,
  }));

  return (
    <div className="min-h-screen bg-zinc-50 p-8 font-sans">
      <h1 className="text-2xl font-semibold mb-6">
        Battery Digital Twin — {CELL_ID}
      </h1>

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