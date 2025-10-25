"use client";

import { TrendingUp, AlertTriangle, Shield, Zap } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import ActivityChart from "@/components/Activity-Chart";

const metrics = [
  {
    title: "Requests Protected",
    value: "2.4M",
    percentage: 94,
    icon: Shield,
    color: "text-blue-500",
    strokeColor: "stroke-blue-500",
    bgColor: "bg-blue-500",
  },
  {
    title: "Threats Blocked",
    value: "1,247",
    percentage: 87,
    icon: AlertTriangle,
    color: "text-red-500",
    strokeColor: "stroke-red-500",
    bgColor: "bg-red-500",
  },
  {
    title: "Success Rate",
    value: "99.5%",
    percentage: 99.5,
    icon: TrendingUp,
    color: "text-green-500",
    strokeColor: "stroke-green-500",
    bgColor: "bg-green-500",
  },
  {
    title: "Avg Response",
    value: "45ms",
    percentage: 91,
    icon: Zap,
    color: "text-purple-500",
    strokeColor: "stroke-purple-500",
    bgColor: "bg-purple-500",
  },
];

interface CircularProgressProps {
  readonly percentage: number;
  readonly strokeColor: string;
  readonly size?: number;
}

function CircularProgress({
  percentage,
  strokeColor,
  size = 120,
}: Readonly<CircularProgressProps>) {
  const radius = 50;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <svg width={size} height={size} className="transform -rotate-90">
      {/* Background circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="currentColor"
        strokeWidth="8"
        fill="none"
        className="text-gray-200"
      />
      {/* Progress circle */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={radius}
        stroke="currentColor"
        strokeWidth="8"
        fill="none"
        strokeLinecap="round"
        className={strokeColor}
        style={{
          strokeDasharray: circumference,
          strokeDashoffset: strokeDashoffset,
          transition: "stroke-dashoffset 0.5s ease-in-out",
        }}
      />
    </svg>
  );
}

export default function MetricsOverview() {
  return (
    <div className="space-y-6">
      {/* Circular Progress Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {metrics.map((metric) => {
          const Icon = metric.icon;
          return (
            <Card
              key={metric.title}
              className="bg-white border-gray-200 hover:border-gray-300 transition-all hover:shadow-lg"
            >
              <CardHeader className="pb-2">
                <div className="flex items-center justify-between">
                  <CardTitle className="text-sm font-medium text-gray-600">
                    {metric.title}
                  </CardTitle>
                  <div className={`p-2 ${metric.bgColor} rounded-lg`}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                </div>
              </CardHeader>
              <CardContent className="flex flex-col items-center pt-4">
                {/* Circular Progress */}
                <div className="relative">
                  <CircularProgress
                    percentage={metric.percentage}
                    strokeColor={metric.strokeColor}
                    size={120}
                  />
                  {/* Center text */}
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="text-center">
                      <div className={`text-2xl font-bold ${metric.color}`}>
                        {metric.percentage}%
                      </div>
                      <div className="text-xs text-gray-500">efficiency</div>
                    </div>
                  </div>
                </div>
                {/* Value */}
                <div className="mt-4 text-center">
                  <span className="text-3xl font-bold text-gray-900">
                    {metric.value}
                  </span>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Trend Chart */}
      <ActivityChart />
    </div>
  );
}