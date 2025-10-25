"use client";

import { CheckCircle, AlertTriangle } from "lucide-react";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

interface Endpoint {
  name: string;
  path: string;
  status: "protected" | "warning" | "critical";
  requestsToday: number;
  threatsBlocked: number;
  avgResponseTime: number;
  lastThreat: string;
}

const endpoints: Endpoint[] = [
  {
    name: "Authentication",
    path: "/api/auth/login",
    status: "protected",
    requestsToday: 45230,
    threatsBlocked: 247,
    avgResponseTime: 42,
    lastThreat: "2 min ago",
  },
  {
    name: "User Search",
    path: "/api/users/search",
    status: "protected",
    requestsToday: 128450,
    threatsBlocked: 1200,
    avgResponseTime: 38,
    lastThreat: "8 min ago",
  },
  {
    name: "Admin Export",
    path: "/api/admin/export",
    status: "warning",
    requestsToday: 3420,
    threatsBlocked: 45,
    avgResponseTime: 156,
    lastThreat: "15 min ago",
  },
  {
    name: "LLM Chat",
    path: "/api/llm/chat",
    status: "protected",
    requestsToday: 89230,
    threatsBlocked: 89,
    avgResponseTime: 245,
    lastThreat: "32 min ago",
  },
  {
    name: "User Registration",
    path: "/api/auth/register",
    status: "protected",
    requestsToday: 12340,
    threatsBlocked: 45,
    avgResponseTime: 51,
    lastThreat: "1 hour ago",
  },
  {
    name: "Payment Processing",
    path: "/api/payments/process",
    status: "critical",
    requestsToday: 5670,
    threatsBlocked: 12,
    avgResponseTime: 89,
    lastThreat: "45 min ago",
  },
];

const statusConfig = {
  protected: {
    icon: CheckCircle,
    color: "text-green-600",
    bg: "bg-green-500/10",
    label: "Protected",
  },
  warning: {
    icon: AlertTriangle,
    color: "text-yellow-600",
    bg: "bg-yellow-500/10",
    label: "Warning",
  },
  critical: {
    icon: AlertTriangle,
    color: "text-red-600",
    bg: "bg-red-500/10",
    label: "Critical",
  },
};

export default function EndpointStatus() {
  return (
    <div className="space-y-4">
      <Card className="bg-white border-gray-200">
        <CardHeader>
          <CardTitle className="text-gray-900">Protected Endpoints</CardTitle>
          <CardDescription className="text-gray-600">
            Real-time protection status across all API endpoints
          </CardDescription>
        </CardHeader>
      </Card>

      <div className="grid gap-4">
        {endpoints.map((endpoint) => {
          const config = statusConfig[endpoint.status];
          const StatusIcon = config.icon;
          return (
            <Card
              key={endpoint.path}
              className="bg-white border-gray-200 hover:border-gray-300 transition-all"
            >
              <CardContent className="pt-6">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex items-start gap-4 flex-1">
                    <div className={`p-3 ${config.bg} rounded-lg`}>
                      <StatusIcon className={`w-5 h-5 ${config.color}`} />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900">
                          {endpoint.name}
                        </h3>
                        <Badge
                          className={`text-xs font-medium ${config.bg} ${config.color}`}
                        >
                          {config.label}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 font-mono mb-3">
                        {endpoint.path}
                      </p>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <p className="text-xs text-gray-500 mb-1">
                            Requests Today
                          </p>
                          <p className="text-lg font-bold text-gray-900">
                            {(endpoint.requestsToday / 1000).toFixed(1)}K
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">
                            Threats Blocked
                          </p>
                          <p className="text-lg font-bold text-red-600">
                            {endpoint.threatsBlocked}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">
                            Avg Response
                          </p>
                          <p className="text-lg font-bold text-gray-900">
                            {endpoint.avgResponseTime}ms
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-gray-500 mb-1">
                            Last Threat
                          </p>
                          <p className="text-lg font-bold text-yellow-600">
                            {endpoint.lastThreat}
                          </p>
                        </div>
                      </div>
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    className="border-gray-200 text-gray-600 hover:bg-gray-50 whitespace-nowrap bg-white"
                  >
                    View Details
                  </Button>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}