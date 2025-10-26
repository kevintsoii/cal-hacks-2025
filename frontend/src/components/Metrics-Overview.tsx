"use client";

import { useState, useEffect } from "react";
import { Shield, Activity, Target, TrendingUp, AlertTriangle } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import ActivityChart from "@/components/Activity-Chart";

interface MetricsData {
  total_requests: number;
  total_mitigations: number;
  active_mitigations: number;
  threat_types: Record<string, number>;
}

const formatNumber = (num: number): string => {
  if (num >= 1000000) {
    return `${(num / 1000000).toFixed(1)}M`;
  }
  if (num >= 1000) {
    return `${(num / 1000).toFixed(1)}K`;
  }
  return num.toLocaleString();
};

export default function MetricsOverview() {
  const [metrics, setMetrics] = useState<MetricsData>({
    total_requests: 0,
    total_mitigations: 0,
    active_mitigations: 0,
    threat_types: {},
  });
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    try {
      const response = await fetch("http://localhost:8000/metrics/overview");
      if (response.ok) {
        const data = await response.json();
        setMetrics(data.metrics);
      }
    } catch (error) {
      console.error("Error fetching metrics:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
    const interval = setInterval(fetchMetrics, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="space-y-8">
      {/* Hero Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Total Requests - Large Featured Card */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-blue-500 via-blue-600 to-cyan-600 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 animate-fade-in-up" style={{ animationDelay: '0ms' }}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
          
          <CardContent className="relative pt-4 pb-4">
            <div className="flex items-start justify-between mb-3">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <Activity className="w-6 h-6 text-white" />
              </div>
              <div className="flex items-center gap-1 text-white/90 text-xs font-medium">
                <TrendingUp className="w-3 h-3" />
                <span>Live</span>
              </div>
            </div>
            
            <div className="space-y-1">
              <p className="text-white/80 text-sm font-medium uppercase tracking-wider">
                Total Requests
              </p>
              <div className="flex items-baseline gap-2">
                <h3 className="text-4xl font-black text-white">
                  {loading ? "—" : formatNumber(metrics.total_requests)}
                </h3>
              </div>
              <p className="text-white/70 text-xs">
                {loading ? "Loading..." : `${metrics.total_requests.toLocaleString()} API calls processed`}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Total Mitigations - Large Featured Card */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-orange-500 via-orange-600 to-red-600 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 animate-fade-in-up" style={{ animationDelay: '100ms' }}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
          
          <CardContent className="relative pt-4 pb-4">
            <div className="flex items-start justify-between mb-3">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <Target className="w-6 h-6 text-white" />
              </div>
              <div className="flex items-center gap-1 text-white/90 text-xs font-medium">
                <AlertTriangle className="w-3 h-3" />
                <span>Total</span>
              </div>
            </div>
            
            <div className="space-y-1">
              <p className="text-white/80 text-sm font-medium uppercase tracking-wider">
                Total Mitigations
              </p>
              <div className="flex items-baseline gap-2">
                <h3 className="text-4xl font-black text-white">
                  {loading ? "—" : formatNumber(metrics.total_mitigations)}
                </h3>
              </div>
              <p className="text-white/70 text-xs">
                {loading ? "Loading..." : `${metrics.total_mitigations.toLocaleString()} threats neutralized`}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Active Mitigations - Large Featured Card */}
        <Card className="relative overflow-hidden bg-gradient-to-br from-red-600 via-pink-600 to-rose-700 border-0 shadow-xl hover:shadow-2xl transition-all duration-300 transform hover:-translate-y-1 animate-fade-in-up" style={{ animationDelay: '200ms' }}>
          <div className="absolute top-0 right-0 w-32 h-32 bg-white/10 rounded-full -mr-16 -mt-16"></div>
          <div className="absolute bottom-0 left-0 w-24 h-24 bg-white/10 rounded-full -ml-12 -mb-12"></div>
          
          <CardContent className="relative pt-4 pb-4">
            <div className="flex items-start justify-between mb-3">
              <div className="p-3 bg-white/20 backdrop-blur-sm rounded-xl">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <div className="flex items-center">
                <span className="relative flex h-3 w-3">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-white opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-white"></span>
                </span>
              </div>
            </div>
            
            <div className="space-y-1">
              <p className="text-white/80 text-sm font-medium uppercase tracking-wider">
                Active Mitigations
              </p>
              <div className="flex items-baseline gap-2">
                <h3 className="text-4xl font-black text-white">
                  {loading ? "—" : metrics.active_mitigations}
                </h3>
              </div>
              <p className="text-white/70 text-xs">
                {loading ? "Loading..." : `${metrics.active_mitigations} currently blocking threats`}
              </p>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Activity Chart */}
      <ActivityChart />
    </div>
  );
}
