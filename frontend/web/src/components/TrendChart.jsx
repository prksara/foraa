import React, { useEffect, useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { fetchTrends } from '../api/client';
import { TrendingUp, TrendingDown, Minus } from 'lucide-react';

export default function TrendChart({ metric, category = "measurement", title, days = 30 }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function loadData() {
      try {
        setLoading(true);
        const res = await fetchTrends(metric, category, days);
        if (mounted) {
          // Format dates for display
          if (res.data_points) {
            res.data_points = res.data_points.map(pt => {
              const d = new Date(pt.date);
              return {
                ...pt,
                displayDate: `${d.getMonth()+1}/${d.getDate()}`
              }
            });
          }
          setData(res);
          setError(null);
        }
      } catch (err) {
        if (mounted) setError("Failed to load trend data.");
      } finally {
        if (mounted) setLoading(false);
      }
    }
    loadData();
    return () => { mounted = false; };
  }, [metric, category, days]);

  if (loading) return <div className="trend-loading" style={{ height: "300px", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-surface)", borderRadius: "var(--radius-lg)" }}>Loading trends...</div>;
  if (error) return <div className="trend-error" style={{ height: "300px", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-surface)", color: "var(--color-error)", borderRadius: "var(--radius-lg)" }}>{error}</div>;
  if (!data || data.data_points.length === 0) {
    return (
      <div className="trend-empty" style={{ height: "300px", display: "flex", alignItems: "center", justifyContent: "center", background: "var(--color-surface)", color: "var(--color-text-muted)", borderRadius: "var(--radius-lg)", border: "1px dashed var(--color-border)" }}>
        Not enough data to show trends for {title}
      </div>
    );
  }

  return (
    <div className="trend-container" style={{ background: "var(--color-surface)", padding: "20px", borderRadius: "var(--radius-lg)", border: "1px solid var(--color-border)" }}>
      <div className="trend-header" style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: "20px" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "16px", fontWeight: "var(--weight-semibold)", color: "var(--color-text)" }}>{title}</h3>
          <div style={{ fontSize: "13px", color: "var(--color-text-secondary)", marginTop: "4px" }}>Last {days} days</div>
        </div>
        <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
          <div>
            <div style={{ fontSize: "12px", color: "var(--color-text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>Current Avg</div>
            <div style={{ fontSize: "20px", fontWeight: "var(--weight-bold)", color: "var(--color-text)" }}>
              {data.current_avg} <span style={{ fontSize: "14px", color: "var(--color-text-muted)", fontWeight: "normal" }}>{data.unit}</span>
            </div>
          </div>
          {data.percent_change !== null && (
            <div style={{ 
              display: "flex", alignItems: "center", gap: "4px", padding: "4px 8px", borderRadius: "var(--radius-full)",
              background: data.direction === "up" ? "rgba(239, 68, 68, 0.1)" : data.direction === "down" ? "rgba(34, 197, 94, 0.1)" : "var(--color-surface-hover)",
              color: data.direction === "up" ? "var(--color-error)" : data.direction === "down" ? "var(--color-success)" : "var(--color-text-secondary)"
            }}>
              {data.direction === "up" ? <TrendingUp size={14} /> : data.direction === "down" ? <TrendingDown size={14} /> : <Minus size={14} />}
              <span style={{ fontSize: "13px", fontWeight: "var(--weight-medium)" }}>{Math.abs(data.percent_change)}%</span>
            </div>
          )}
        </div>
      </div>

      <div style={{ height: "250px", width: "100%" }}>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data.data_points} margin={{ top: 5, right: 10, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
            <XAxis dataKey="displayDate" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "var(--color-text-muted)" }} dy={10} />
            <YAxis axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: "var(--color-text-muted)" }} domain={['dataMin - 5', 'dataMax + 5']} />
            <Tooltip 
              contentStyle={{ background: "var(--color-surface)", border: "1px solid var(--color-border)", borderRadius: "var(--radius-md)", boxShadow: "0 4px 6px rgba(0,0,0,0.05)" }}
              itemStyle={{ color: "var(--color-text)", fontWeight: "var(--weight-medium)" }}
              labelStyle={{ color: "var(--color-text-secondary)", marginBottom: "4px" }}
            />
            {data.data_points[0]?.secondary_value !== undefined && data.data_points[0]?.secondary_value !== null ? (
               <>
                 <Line type="monotone" dataKey="value" name="Systolic" stroke="var(--color-accent)" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
                 <Line type="monotone" dataKey="secondary_value" name="Diastolic" stroke="var(--color-brand)" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
               </>
            ) : (
               <Line type="monotone" dataKey="value" name={title} stroke="var(--color-accent)" strokeWidth={3} dot={{ r: 4, strokeWidth: 2 }} activeDot={{ r: 6 }} />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
