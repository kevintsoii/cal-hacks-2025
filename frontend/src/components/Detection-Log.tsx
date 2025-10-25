"use client";

import { AlertTriangle, Clock, Shield } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Detection {
  id: string;
  timestamp: string;
  type: "brute-force" | "scraping" | "jailbreak" | "anomaly";
  endpoint: string;
  ip: string;
  severity: "high" | "medium" | "low";
  action: "blocked" | "captcha" | "delayed" | "flagged";
  details: string;
}

const detections: Detection[] = [
  {
    id: "1",
    timestamp: "2 min ago",
    type: "brute-force",
    endpoint: "/api/auth/login",
    ip: "192.168.1.105",
    severity: "high",
    action: "blocked",
    details: "247 login attempts in 5 minutes",
  },
  {
    id: "2",
    timestamp: "8 min ago",
    type: "scraping",
    endpoint: "/api/users/search",
    ip: "203.45.67.89",
    severity: "high",
    action: "blocked",
    details: "1,200+ sequential requests detected",
  },
  {
    id: "3",
    timestamp: "15 min ago",
    type: "anomaly",
    endpoint: "/api/admin/export",
    ip: "10.0.0.42",
    severity: "medium",
    action: "captcha",
    details: "Unusual access pattern from admin account",
  },
  {
    id: "4",
    timestamp: "32 min ago",
    type: "jailbreak",
    endpoint: "/api/llm/chat",
    ip: "198.51.100.23",
    severity: "high",
    action: "blocked",
    details: "Prompt injection attempt detected",
  },
  {
    id: "5",
    timestamp: "1 hour ago",
    type: "brute-force",
    endpoint: "/api/auth/register",
    ip: "172.16.0.88",
    severity: "low",
    action: "delayed",
    details: "45 registration attempts from same IP",
  },
];

const typeIcons = {
  "brute-force": AlertTriangle,
  scraping: Shield,
  jailbreak: AlertTriangle,
  anomaly: Clock,
};

const severityColors = {
  high: "bg-red-500/10 text-red-600 border-red-500/30",
  medium: "bg-yellow-500/10 text-yellow-600 border-yellow-500/30",
  low: "bg-blue-500/10 text-blue-600 border-blue-500/30",
};

const actionColors = {
  blocked: "bg-red-500/10 text-red-600",
  captcha: "bg-yellow-500/10 text-yellow-600",
  delayed: "bg-blue-500/10 text-blue-600",
  flagged: "bg-purple-500/10 text-purple-600",
};

interface DetectionLogProps {
  readonly expanded?: boolean;
  readonly onViewAll?: () => void;
}

export default function DetectionLog({
  expanded = false,
  onViewAll,
}: Readonly<DetectionLogProps>) {
  return (
    <Card className="bg-white border-gray-200">
      <CardHeader>
        <CardTitle className="text-gray-900">Detection Log</CardTitle>
        <CardDescription className="text-gray-600">
          Real-time API threat detections and mitigations
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {detections.slice(0, expanded ? undefined : 3).map((detection) => {
            const TypeIcon = typeIcons[detection.type];
            return (
              <div
                key={detection.id}
                className="p-4 bg-gray-50 border border-gray-200 rounded-lg hover:border-gray-300 transition-all"
              >
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-3 flex-1">
                    <div className="p-2 bg-gray-100 rounded-lg mt-0.5">
                      <TypeIcon className="w-4 h-4 text-gray-600" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="font-semibold text-gray-900 capitalize">
                          {detection.type.replace("-", " ")}
                        </span>
                        <Badge
                          variant="outline"
                          className={`text-xs ${
                            severityColors[detection.severity]
                          }`}
                        >
                          {detection.severity}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">
                        {detection.details}
                      </p>
                      <div className="flex items-center gap-4 text-xs text-gray-500">
                        <span>Endpoint: {detection.endpoint}</span>
                        <span>IP: {detection.ip}</span>
                        <span>{detection.timestamp}</span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      className={`text-xs font-medium ${
                        actionColors[detection.action]
                      }`}
                    >
                      {detection.action}
                    </Badge>
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-gray-600 hover:text-gray-900"
                    >
                      Review
                    </Button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
        {!expanded && (
          <Button
            variant="outline"
            className="w-full mt-4 border-gray-200 text-gray-600 hover:bg-gray-50 bg-white"
            onClick={onViewAll}
          >
            View All Detections
          </Button>
        )}
      </CardContent>
    </Card>
  );
}