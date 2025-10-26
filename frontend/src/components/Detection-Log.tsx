"use client";

import { useState, useMemo } from "react";
import { Search, Filter, ChevronDown, Check } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useRequests, useConnectionStatus } from "@/hooks/useWebSocket";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

interface RequestLogProps {
  readonly expanded?: boolean;
  readonly onViewAll?: () => void;
}

const methodColors: Record<string, string> = {
  GET: "bg-blue-100 text-blue-700 border-blue-200",
  POST: "bg-green-100 text-green-700 border-green-200",
  PUT: "bg-yellow-100 text-yellow-700 border-yellow-200",
  DELETE: "bg-red-100 text-red-700 border-red-200",
  PATCH: "bg-purple-100 text-purple-700 border-purple-200",
};

const statusColors = (status: number) => {
  if (status === 200 || status === 201) return "bg-green-100 text-green-700";
  if (status === 401) return "bg-orange-100 text-orange-700";
  if (status === 403 || status === 404) return "bg-yellow-100 text-yellow-700";
  if (status >= 500) return "bg-red-100 text-red-700";
  if (status >= 400) return "bg-orange-100 text-orange-700";
  return "bg-gray-100 text-gray-700";
};

export default function DetectionLog({ expanded = false }: Readonly<RequestLogProps>) {
  const rawRequests = useRequests();
  const { isConnected } = useConnectionStatus();
  const [searchQuery, setSearchQuery] = useState("");
  const [filterTab, setFilterTab] = useState<"all" | "401" | "errors">("all");
  const [selectedEndpoint, setSelectedEndpoint] = useState<string>("all");
  const [selectedStatus, setSelectedStatus] = useState<string>("all");

  // Transform and filter requests
  const { allRequests, requests401, errorRequests, displayRequests, uniqueEndpoints, uniqueStatuses, hasMoreThan100 } = useMemo(() => {
    // Only keep the most recent 100 entries
    const recentRawRequests = rawRequests.slice(-100);
    
    const all = recentRawRequests.map((req, index) => ({
      id: `${req.timestamp}-${index}`,
      timestamp: new Date(req.timestamp).toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      }),
      method: req.method,
      endpoint: req.path,
      status: req.response_status,
      ipAddress: req.client_ip,
      responseTime: `${Math.round(req.processing_time_ms)}ms`,
      userId: req.user || req.username || "–", // Fix: use 'user' field from data
    }));

    const errors401 = all.filter(r => r.status === 401);
    const errors = all.filter(r => r.status >= 400);

    // Get unique endpoints and statuses for dropdowns
    const endpoints = Array.from(new Set(all.map(r => r.endpoint))).sort();
    const statuses = Array.from(new Set(all.map(r => r.status))).sort((a, b) => a - b);

    // Apply filters
    let filtered = all;
    
    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(
        r =>
          r.endpoint.toLowerCase().includes(query) ||
          r.ipAddress.toLowerCase().includes(query) ||
          r.status.toString().includes(query)
      );
    }

    // Endpoint filter
    if (selectedEndpoint !== "all") {
      filtered = filtered.filter(r => r.endpoint === selectedEndpoint);
    }

    // Status filter
    if (selectedStatus !== "all") {
      filtered = filtered.filter(r => r.status === parseInt(selectedStatus));
    }

    // Tab filter (applies after other filters)
    if (filterTab === "401") {
      filtered = filtered.filter(r => r.status === 401);
    } else if (filterTab === "errors") {
      filtered = filtered.filter(r => r.status >= 400);
    }

    return {
      allRequests: all,
      requests401: errors401,
      errorRequests: errors,
      displayRequests: expanded ? filtered : filtered,
      uniqueEndpoints: endpoints,
      uniqueStatuses: statuses,
      hasMoreThan100: rawRequests.length > 100,
    };
  }, [rawRequests, searchQuery, filterTab, selectedEndpoint, selectedStatus, expanded]);

  return (
    <Card className={`bg-white border-gray-200 ${expanded ? 'h-full flex flex-col' : ''}`}>
      <CardHeader>
        <div className="flex items-start justify-between mb-4">
          <div>
            <CardTitle className="text-xl font-bold text-gray-900 flex items-center gap-2">
              Request Logs
              {isConnected && (
                <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs font-medium rounded-full">
                  <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></span>
                  Live
                </span>
              )}
            </CardTitle>
            <CardDescription className="text-gray-500 mt-1">
              Monitor all API requests with detailed information
            </CardDescription>
          </div>
        </div>

        {/* Search and Filters */}
        <div className="flex gap-3 mt-4">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <Input
              placeholder="Search by endpoint, IP, or status code..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-gray-50 border-gray-200"
            />
          </div>
          
          {/* Endpoint Filter Dropdown */}
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-700 min-w-[160px] justify-between">
                <div className="flex items-center gap-2">
                  <Filter className="w-4 h-4" />
                  {selectedEndpoint === "all" ? "All Endpoints" : selectedEndpoint}
                </div>
                <ChevronDown className="w-4 h-4" />
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="bg-white rounded-lg shadow-lg border border-gray-200 p-1 min-w-[200px] max-h-[300px] overflow-y-auto z-50"
                sideOffset={5}
              >
                <DropdownMenu.Item
                  className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                  onSelect={() => setSelectedEndpoint("all")}
                >
                  All Endpoints
                  {selectedEndpoint === "all" && <Check className="w-4 h-4" />}
                </DropdownMenu.Item>
                {uniqueEndpoints.map((endpoint) => (
                  <DropdownMenu.Item
                    key={endpoint}
                    className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between font-mono"
                    onSelect={() => setSelectedEndpoint(endpoint)}
                  >
                    {endpoint}
                    {selectedEndpoint === endpoint && <Check className="w-4 h-4" />}
                  </DropdownMenu.Item>
                ))}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>

          {/* Status Filter Dropdown */}
          <DropdownMenu.Root>
            <DropdownMenu.Trigger asChild>
              <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-700 min-w-[140px] justify-between">
                {selectedStatus === "all" ? "All Status" : selectedStatus}
                <ChevronDown className="w-4 h-4" />
              </button>
            </DropdownMenu.Trigger>
            <DropdownMenu.Portal>
              <DropdownMenu.Content
                className="bg-white rounded-lg shadow-lg border border-gray-200 p-1 min-w-[150px] max-h-[300px] overflow-y-auto z-50"
                sideOffset={5}
              >
                <DropdownMenu.Item
                  className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                  onSelect={() => setSelectedStatus("all")}
                >
                  All Status
                  {selectedStatus === "all" && <Check className="w-4 h-4" />}
                </DropdownMenu.Item>
                {uniqueStatuses.map((status) => (
                  <DropdownMenu.Item
                    key={status}
                    className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                    onSelect={() => setSelectedStatus(status.toString())}
                  >
                    {status}
                    {selectedStatus === status.toString() && <Check className="w-4 h-4" />}
                  </DropdownMenu.Item>
                ))}
              </DropdownMenu.Content>
            </DropdownMenu.Portal>
          </DropdownMenu.Root>
        </div>

        {/* Filter Tabs */}
        <div className="flex gap-2 mt-4">
          <button
            onClick={() => setFilterTab("all")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === "all"
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All Logs ({hasMoreThan100 ? '100+' : allRequests.length})
          </button>
          <button
            onClick={() => setFilterTab("401")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === "401"
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            401 Unauthorized ({requests401.length > 100 ? '100+' : requests401.length})
          </button>
          <button
            onClick={() => setFilterTab("errors")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filterTab === "errors"
                ? "bg-gray-900 text-white"
                : "bg-gray-100 text-gray-700 hover:bg-gray-200"
            }`}
          >
            All Errors ({errorRequests.length > 100 ? '100+' : errorRequests.length})
          </button>
        </div>
      </CardHeader>

      <CardContent className={expanded ? 'flex-1 flex flex-col overflow-hidden' : ''}>
        {!isConnected && (
          <div className="p-4 mb-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <p className="text-sm text-yellow-800">🔌 Connecting to live feed...</p>
          </div>
        )}

        {/* Fixed or flexible height container based on expanded mode */}
        <div className={expanded ? 'flex-1 flex flex-col overflow-hidden' : 'h-[600px] flex flex-col'}>
          {displayRequests.length === 0 && isConnected && (
            <div className="flex-1 flex items-center justify-center text-gray-500">
              <p>No requests found matching your filters</p>
            </div>
          )}

          {/* Table with internal scrolling */}
          {displayRequests.length > 0 && (
            <div className="overflow-y-auto overflow-x-auto flex-1">
              <table className="w-full">
                <thead className="sticky top-0 bg-white z-10 shadow-sm">
                  <tr className="border-b border-gray-200">
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      Timestamp
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      Method
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      Endpoint
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      Status
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      IP Address
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      Response Time
                    </th>
                    <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                      User ID
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {displayRequests.map((request, index) => (
                    <tr
                      key={request.id}
                      className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                        index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                      }`}
                    >
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {request.timestamp}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-3 py-1 rounded-md text-xs font-medium border ${
                            methodColors[request.method] || methodColors.GET
                          }`}
                        >
                          {request.method}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm font-mono text-gray-900">
                        {request.endpoint}
                      </td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-3 py-1 rounded-md text-xs font-semibold ${statusColors(
                            request.status
                          )}`}
                        >
                          {request.status}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {request.ipAddress}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-900">
                        {request.responseTime}
                      </td>
                      <td className="py-3 px-4 text-sm text-gray-500">
                        {request.userId}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
