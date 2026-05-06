"use client";

import { useState, useEffect } from "react";

interface Position {
  symbol: string;
  side: string;
  quantity: number;
  entry_price: number;
  unrealized_pnl: number;
}

interface BotStatus {
  running: boolean;
  balance: number;
  positions: Position[];
  config: {
    whitelist: string[];
    volume_percent: number;
    max_positions: number;
  };
  logs: string[];
}

export default function Home() {
  const [status, setStatus] = useState<BotStatus | null>(null);
  const [whitelist, setWhitelist] = useState("");
  const [volume, setVolume] = useState(3);
  const [maxPos, setMaxPos] = useState(3);
  const [loading, setLoading] = useState(false);

  const fetchStatus = async () => {
    try {
      const res = await fetch("http://localhost:5000/api/status");
      const data = await res.json();
      setStatus(data);
      if (data.config) {
        setWhitelist(data.config.whitelist.join(", "));
        setVolume(data.config.volume_percent);
        setMaxPos(data.config.max_positions);
      }
    } catch (e) {
      console.error("Failed to fetch", e);
    }
  };

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleStart = async () => {
    setLoading(true);
    await fetch("http://localhost:5000/api/start", { method: "POST" });
    await fetchStatus();
    setLoading(false);
  };

  const handleStop = async () => {
    setLoading(true);
    await fetch("http://localhost:5000/api/stop", { method: "POST" });
    await fetchStatus();
    setLoading(false);
  };

  const handleSaveConfig = async () => {
    const coins = whitelist.split(",").map((c) => c.trim().toUpperCase()).filter(Boolean);
    await fetch("http://localhost:5000/api/config", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        whitelist: coins,
        volume_percent: volume,
        max_positions: maxPos,
      }),
    });
    await fetchStatus();
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white p-6">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Trading Bot Dashboard</h1>
          <div className="flex items-center gap-4">
            <span
              className={`px-4 py-2 rounded-full text-sm font-medium ${
                status?.running ? "bg-green-600" : "bg-red-600"
              }`}
            >
              {status?.running ? "Running" : "Stopped"}
            </span>
            <button
              onClick={handleStart}
              disabled={loading || status?.running}
              className="px-6 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-600 rounded-lg font-medium"
            >
              Start
            </button>
            <button
              onClick={handleStop}
              disabled={loading || !status?.running}
              className="px-6 py-2 bg-red-600 hover:bg-red-700 disabled:bg-gray-600 rounded-lg font-medium"
            >
              Stop
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-3 gap-4 mb-8">
          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="text-gray-400 text-sm">Balance</div>
            <div className="text-2xl font-bold">
              ${status?.balance?.toFixed(2) || "0"}
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="text-gray-400 text-sm">Open Positions</div>
            <div className="text-2xl font-bold">
              {status?.positions?.length || 0} / {status?.config?.max_positions || 0}
            </div>
          </div>
          <div className="bg-gray-800 p-6 rounded-xl">
            <div className="text-gray-400 text-sm">Total P&L</div>
            <div
              className={`text-2xl font-bold ${
                (status?.positions || []).reduce(
                  (sum: number, p: Position) => sum + p.unrealized_pnl,
                  0
                ) >= 0
                  ? "text-green-400"
                  : "text-red-400"
              }`}
            >
              $
              {(status?.positions || []).reduce(
                (sum: number, p: Position) => sum + p.unrealized_pnl,
                0
              ).toFixed(2)}
            </div>
          </div>
        </div>

        {/* Config */}
        <div className="bg-gray-800 p-6 rounded-xl mb-8">
          <h2 className="text-xl font-bold mb-4">Configuration</h2>
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-gray-400 text-sm">Whitelist (comma-separated)</label>
              <input
                type="text"
                value={whitelist}
                onChange={(e) => setWhitelist(e.target.value)}
                className="w-full bg-gray-700 px-4 py-2 rounded-lg mt-1"
                placeholder="BTCUSDT, ETHUSDT, SOLUSDT"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm">Volume %</label>
              <input
                type="number"
                value={volume}
                onChange={(e) => setVolume(Number(e.target.value))}
                className="w-full bg-gray-700 px-4 py-2 rounded-lg mt-1"
              />
            </div>
            <div>
              <label className="text-gray-400 text-sm">Max Positions</label>
              <input
                type="number"
                value={maxPos}
                onChange={(e) => setMaxPos(Number(e.target.value))}
                className="w-full bg-gray-700 px-4 py-2 rounded-lg mt-1"
              />
            </div>
          </div>
          <button
            onClick={handleSaveConfig}
            className="mt-4 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg font-medium"
          >
            Save Config
          </button>
        </div>

        {/* Positions */}
        <div className="bg-gray-800 p-6 rounded-xl mb-8">
          <h2 className="text-xl font-bold mb-4">Open Positions</h2>
          {status?.positions && status.positions.length > 0 ? (
            <table className="w-full">
              <thead>
                <tr className="text-gray-400 text-left">
                  <th className="pb-3">Symbol</th>
                  <th className="pb-3">Side</th>
                  <th className="pb-3">Qty</th>
                  <th className="pb-3">Entry</th>
                  <th className="pb-3">P&L</th>
                </tr>
              </thead>
              <tbody>
                {status.positions.map((pos, i) => (
                  <tr key={i} className="border-t border-gray-700">
                    <td className="py-3">{pos.symbol}</td>
                    <td className="py-3">
                      <span
                        className={`px-2 py-1 rounded text-sm ${
                          pos.side === "LONG"
                            ? "bg-green-900 text-green-400"
                            : "bg-red-900 text-red-400"
                        }`}
                      >
                        {pos.side}
                      </span>
                    </td>
                    <td className="py-3">{pos.quantity}</td>
                    <td className="py-3">{pos.entry_price}</td>
                    <td
                      className={`py-3 ${
                        pos.unrealized_pnl >= 0 ? "text-green-400" : "text-red-400"
                      }`}
                    >
                      {pos.unrealized_pnl.toFixed(2)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <div className="text-gray-400">No open positions</div>
          )}
        </div>

        {/* Logs */}
        <div className="bg-gray-800 p-6 rounded-xl">
          <h2 className="text-xl font-bold mb-4">Recent Logs</h2>
          <div className="font-mono text-sm text-gray-300 max-h-48 overflow-y-auto">
            {status?.logs?.map((log, i) => (
              <div key={i} className="py-1 border-b border-gray-700">
                {log}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}