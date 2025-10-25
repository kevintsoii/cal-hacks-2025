"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

// Sample data for the chart (last 24 hours)
const chartData = {
  labels: ["00:00", "04:00", "08:00", "12:00", "16:00", "20:00", "23:59"],
  datasets: [
    {
      label: "Requests",
      data: [1200, 1900, 3000, 5000, 4200, 3800, 2400],
      color: "rgb(59, 130, 246)", // blue
    },
    {
      label: "Threats",
      data: [20, 45, 80, 120, 90, 75, 50],
      color: "rgb(239, 68, 68)", // red
    },
  ],
};

interface LineChartProps {
  readonly data: typeof chartData;
}

interface TooltipData {
  x: number;
  y: number;
  value: number;
  label: string;
  time: string;
  color: string;
}

function LineChart({ data }: Readonly<LineChartProps>) {
  const [tooltip, setTooltip] = useState<TooltipData | null>(null);
  const width = 1000;
  const height = 300;
  const padding = { top: 20, right: 20, bottom: 40, left: 50 };
  const chartWidth = width - padding.left - padding.right;
  const chartHeight = height - padding.top - padding.bottom;

  // Find max value for scaling
  const allValues = data.datasets.flatMap((d) => d.data);
  const maxValue = Math.max(...allValues);
  const minValue = 0;

  // Create points for each dataset
  const createPath = (dataPoints: number[]) => {
    return dataPoints
      .map((value, index) => {
        const x = padding.left + (index / (dataPoints.length - 1)) * chartWidth;
        const y =
          padding.top +
          chartHeight -
          ((value - minValue) / (maxValue - minValue)) * chartHeight;
        return `${index === 0 ? "M" : "L"} ${x},${y}`;
      })
      .join(" ");
  };

  return (
    <div className="w-full relative">
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-auto">
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((percent) => {
          const y = padding.top + chartHeight * (1 - percent);
          return (
            <g key={percent}>
              <line
                x1={padding.left}
                y1={y}
                x2={width - padding.right}
                y2={y}
                stroke="#e5e7eb"
                strokeWidth="1"
              />
              <text
                x={padding.left - 10}
                y={y + 5}
                textAnchor="end"
                fontSize="12"
                fill="#6b7280"
              >
                {Math.round(maxValue * percent)}
              </text>
            </g>
          );
        })}

        {/* X-axis labels */}
        {data.labels.map((label, index) => {
          const x =
            padding.left + (index / (data.labels.length - 1)) * chartWidth;
          return (
            <text
              key={label}
              x={x}
              y={height - padding.bottom + 25}
              textAnchor="middle"
              fontSize="12"
              fill="#6b7280"
            >
              {label}
            </text>
          );
        })}

        {/* Lines */}
        {data.datasets.map((dataset) => {
          const path = createPath(dataset.data);
          const areaPath = `${path} L ${padding.left + chartWidth},${
            padding.top + chartHeight
          } L ${padding.left},${padding.top + chartHeight} Z`;

          return (
            <g key={dataset.label}>
              {/* Area fill */}
              <path d={areaPath} fill={dataset.color} opacity="0.1" />
              {/* Line */}
              <path
                d={path}
                stroke={dataset.color}
                strokeWidth="3"
                fill="none"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              {/* Points */}
              {dataset.data.map((value, index) => {
                const x =
                  padding.left +
                  (index / (dataset.data.length - 1)) * chartWidth;
                const y =
                  padding.top +
                  chartHeight -
                  ((value - minValue) / (maxValue - minValue)) * chartHeight;
                return (
                  <g key={`${dataset.label}-${data.labels[index]}`}>
                    {/* Invisible larger circle for easier hover */}
                    <circle
                      cx={x}
                      cy={y}
                      r="12"
                      fill="transparent"
                      style={{ cursor: "pointer" }}
                      onMouseEnter={() =>
                        setTooltip({
                          x,
                          y,
                          value,
                          label: dataset.label,
                          time: data.labels[index],
                          color: dataset.color,
                        })
                      }
                      onMouseLeave={() => setTooltip(null)}
                    />
                    {/* Visible circle */}
                    <circle
                      cx={x}
                      cy={y}
                      r="4"
                      fill="white"
                      stroke={dataset.color}
                      strokeWidth="2"
                      style={{ pointerEvents: "none" }}
                    />
                  </g>
                );
              })}
            </g>
          );
        })}

        {/* Tooltip */}
        {tooltip && (
          <g>
            {/* Tooltip background */}
            <rect
              x={tooltip.x - 50}
              y={tooltip.y - 60}
              width="100"
              height="50"
              rx="6"
              fill="rgba(0, 0, 0, 0.9)"
              stroke={tooltip.color}
              strokeWidth="2"
            />
            {/* Tooltip text - label */}
            <text
              x={tooltip.x}
              y={tooltip.y - 40}
              textAnchor="middle"
              fontSize="12"
              fill="white"
              fontWeight="bold"
            >
              {tooltip.label}
            </text>
            {/* Tooltip text - value */}
            <text
              x={tooltip.x}
              y={tooltip.y - 25}
              textAnchor="middle"
              fontSize="14"
              fill={tooltip.color}
              fontWeight="bold"
            >
              {tooltip.value.toLocaleString()}
            </text>
            {/* Tooltip text - time */}
            <text
              x={tooltip.x}
              y={tooltip.y - 12}
              textAnchor="middle"
              fontSize="10"
              fill="#9ca3af"
            >
              {tooltip.time}
            </text>
          </g>
        )}
      </svg>
    </div>
  );
}

export default function ActivityChart() {
  return (
    <Card className="bg-white border-gray-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-lg font-bold text-gray-900">
              Activity Trends
            </CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              Request volume and threat detection over the last 24 hours
            </p>
          </div>
          <div className="flex gap-4">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Requests</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-red-500 rounded-full"></div>
              <span className="text-sm text-gray-600">Threats</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <LineChart data={chartData} />
      </CardContent>
    </Card>
  );
}