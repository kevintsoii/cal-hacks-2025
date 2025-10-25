"use client";

import { AlertTriangle, Clock, Shield, Activity, XCircle, CheckCircle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useRequests, useConnectionStatus } from "@/hooks/useWebSocket";
import { useMemo } from "react";

interface LiveRequest {
  id: string;
  timestamp: string;
  method: string;
  path: string;
  status: number;
  ip: string;
  username?: string;
  responseTime: number;
  success: boolean;
}

const methodColors: Record<string, string> = {
  GET: "bg-blue-500/10 text-blue-600",
  POST: "bg-green-500/10 text-green-600",
  PUT: "bg-yellow-500/10 text-yellow-600",
  DELETE: "bg-red-500/10 text-red-600",
  PATCH: "bg-purple-500/10 text-purple-600",
};

const statusColors = (status: number) => {
  if (status >= 200 && status < 300) return "bg-green-500/10 text-green-600 border-green-500/30";
  if (status >= 400 && status < 500) return "bg-yellow-500/10 text-yellow-600 border-yellow-500/30";
  if (status >= 500) return "bg-red-500/10 text-red-600 border-red-500/30";
  return "bg-gray-500/10 text-gray-600 border-gray-500/30";
};

// Format timestamp to relative time
const formatTimestamp = (timestamp: string): string => {
  try {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffSec = Math.floor(diffMs / 1000);
    
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHour = Math.floor(diffMin / 60);
    if (diffHour < 24) return `${diffHour}h ago`;
    return date.toLocaleDateString();
  } catch {
    return timestamp;
  }
};

interface DetectionLogProps {
  readonly expanded?: boolean;
  readonly onViewAll?: () => void;
}

export default function DetectionLog({
  expanded = false,
  onViewAll,
}: Readonly<DetectionLogProps>) {
  // Get live requests from WebSocket
  const rawRequests = useRequests();
  const { isConnected } = useConnectionStatus();

  // Transform raw requests into display format
  const liveRequests = useMemo<LiveRequest[]>(() => {
    return rawRequests.map((req, index) => ({
      id: `${req.timestamp}-${index}`,
      timestamp: req.timestamp,
      method: req.method,
      path: req.path,
      status: req.response_status,
      ip: req.client_ip,
      username: req.username,
      responseTime: req.processing_time_ms,
      success: req.response_success,
    }));
  }, [rawRequests]);

  // Filter to show most relevant requests (failed ones first)
  const displayRequests = useMemo(() => {
    const sorted = [...liveRequests].sort((a, b) => {
      // Failed requests first
      if (!a.success && b.success) return -1;
      if (a.success && !b.success) return 1;
      return 0;
    });
    return sorted.slice(0, expanded ? 50 : 10);
  }, [liveRequests, expanded]);

  return (
    <Card className="bg-white border-gray-200">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="text-gray-900 flex items-center gap-2">
              Live Request Log
              {isConnected && (
                <span className="flex items-center gap-1 text-sm font-normal text-green-600">
                  <Activity className="w-3 h-3 animate-pulse" />
                  Live
                </span>
              )}
            </CardTitle>
            <CardDescription className="text-gray-600">
              Real-time API requests and responses
            </CardDescription>
          </div>
          <Badge variant="outline" className="text-gray-600">
            {liveRequests.length} total
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        {!isConnected && (
          <div className="p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">
              🔌 Connecting to live feed...
            </p>
          </div>
        )}
        
        {liveRequests.length === 0 && isConnected && (
          <div className="p-8 text-center text-gray-500">
            <Activity className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Waiting for requests...</p>
          </div>
        )}

        <div className="space-y-2">
          {displayRequests.map((request) => (
            <div
              key={request.id}
              className={`p-3 border rounded-lg hover:border-gray-300 transition-all ${
                !request.success 
                  ? 'bg-red-50 border-red-200' 
                  : 'bg-gray-50 border-gray-200'
              }`}
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className={`p-2 rounded-lg mt-0.5 ${
                    !request.success ? 'bg-red-100' : 'bg-gray-100'
                  }`}>
                    {request.success ? (
                      <CheckCircle className="w-4 h-4 text-green-600" />
                    ) : (
                      <XCircle className="w-4 h-4 text-red-600" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1 flex-wrap">
                      <Badge
                        className={`text-xs font-medium ${
                          methodColors[request.method] || methodColors.GET
                        }`}
                      >
                        {request.method}
                      </Badge>
                      <span className="font-mono text-sm text-gray-900 truncate">
                        {request.path}
                      </span>
                      <Badge
                        variant="outline"
                        className={`text-xs ${statusColors(request.status)}`}
                      >
                        {request.status}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
                      <span className="flex items-center gap-1">
                        <Shield className="w-3 h-3" />
                        {request.ip}
                      </span>
                      {request.username && (
                        <span className="font-medium">
                          User: {request.username}
                        </span>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {request.responseTime.toFixed(2)}ms
                      </span>
                      <span>{formatTimestamp(request.timestamp)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
        
        {!expanded && liveRequests.length > 10 && (
          <Button
            variant="outline"
            className="w-full mt-4 border-gray-200 text-gray-600 hover:bg-gray-50 bg-white"
            onClick={onViewAll}
          >
            View All {liveRequests.length} Requests
          </Button>
        )}
      </CardContent>
    </Card>
  );
}