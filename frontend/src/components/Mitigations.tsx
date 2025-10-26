"use client";

import { useState, useEffect } from "react";
import { Search, AlertCircle, Clock, Shield, Ban, XCircle, User, Globe, Filter, ChevronDown, Check, X } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import * as DropdownMenu from "@radix-ui/react-dropdown-menu";

interface ActiveMitigation {
  entity_type: string;
  entity: string;
  mitigation: string;
  ttl: number | null;
}

interface PastMitigation {
  id: string;
  text: string;
  metadata: {
    user: string;
    ip: string;
    severity: number;
    timestamp: string;
    mitigation?: string;
    source_agent?: string;
    [key: string]: string | number | boolean | undefined;
  };
}

type IconComponent = typeof Check | typeof Clock | typeof Shield | typeof Ban | typeof XCircle;

const mitigationConfig: Record<string, { label: string; color: string; bgColor: string; icon: IconComponent }> = {
  none: { label: "No Action", color: "text-gray-600", bgColor: "bg-gray-100", icon: Check },
  delay: { label: "Slow Down", color: "text-yellow-600", bgColor: "bg-yellow-100", icon: Clock },
  captcha: { label: "CAPTCHA", color: "text-orange-600", bgColor: "bg-orange-100", icon: Shield },
  temp_block: { label: "Temp Block", color: "text-red-600", bgColor: "bg-red-100", icon: Ban },
  ban: { label: "Permanent Ban", color: "text-red-800", bgColor: "bg-red-200", icon: XCircle },
};

const severityConfig = [
  { level: 1, label: "Low", color: "bg-blue-100 text-blue-700" },
  { level: 2, label: "Medium", color: "bg-yellow-100 text-yellow-700" },
  { level: 3, label: "High", color: "bg-orange-100 text-orange-700" },
  { level: 4, label: "Critical", color: "bg-red-100 text-red-700" },
];

// Countdown component for real-time TTL display
const CountdownTimer = ({ initialTTL }: { initialTTL: number | null }) => {
  const [timeLeft, setTimeLeft] = useState(initialTTL || 0);

  useEffect(() => {
    if (!initialTTL || initialTTL < 0) return;

    setTimeLeft(initialTTL);

    const interval = setInterval(() => {
      setTimeLeft((prev) => {
        if (prev <= 1) {
          clearInterval(interval);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);

    return () => clearInterval(interval);
  }, [initialTTL]);

  if (!initialTTL || initialTTL < 0) {
    return <span>Permanent</span>;
  }

  if (timeLeft <= 0) {
    return <span className="text-gray-400">Expired</span>;
  }

  const hours = Math.floor(timeLeft / 3600);
  const minutes = Math.floor((timeLeft % 3600) / 60);
  const secs = timeLeft % 60;

  let display = "";
  if (hours > 0) {
    display = `${hours}h ${minutes}m ${secs}s`;
  } else if (minutes > 0) {
    display = `${minutes}m ${secs}s`;
  } else {
    display = `${secs}s`;
  }

  return <span>{display}</span>;
};

export default function Mitigations() {
  const [activeMitigations, setActiveMitigations] = useState<ActiveMitigation[]>([]);
  const [pastMitigations, setPastMitigations] = useState<PastMitigation[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedMitigation, setSelectedMitigation] = useState<PastMitigation | null>(null);
  const [activeTab, setActiveTab] = useState<"active" | "history">("active");
  const [loading, setLoading] = useState(true);
  const [filterType, setFilterType] = useState<string>("all");
  const [filterMitigation, setFilterMitigation] = useState<string>("all");

  // Fetch active mitigations from Redis
  const fetchActiveMitigations = async () => {
    try {
      const response = await fetch("http://localhost:8000/mitigations/active");
      if (response.ok) {
        const data = await response.json();
        setActiveMitigations(data.mitigations || []);
      }
    } catch (error) {
      console.error("Error fetching active mitigations:", error);
    }
  };

  // Fetch past mitigations from ChromaDB
  const fetchPastMitigations = async () => {
    try {
      const response = await fetch("http://localhost:8000/mitigations/history?limit=100");
      if (response.ok) {
        const data = await response.json();
        setPastMitigations(data.mitigations || []);
      }
    } catch (error) {
      console.error("Error fetching past mitigations:", error);
    } finally {
      setLoading(false);
    }
  };

  // Search mitigations semantically
  const searchMitigations = async (query: string) => {
    if (!query.trim()) {
      fetchPastMitigations();
      return;
    }

    try {
      const response = await fetch(
        `http://localhost:8000/mitigations/search?query=${encodeURIComponent(query)}&k=50`
      );
      if (response.ok) {
        const data = await response.json();
        setPastMitigations(data.items || []);
      }
    } catch (error) {
      console.error("Error searching mitigations:", error);
    }
  };

  useEffect(() => {
    fetchActiveMitigations();
    fetchPastMitigations();

    // Refresh active mitigations every 5 seconds
    const interval = setInterval(fetchActiveMitigations, 5000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    const delaySearch = setTimeout(() => {
      if (searchQuery) {
        searchMitigations(searchQuery);
      } else {
        fetchPastMitigations();
      }
    }, 500);

    return () => clearTimeout(delaySearch);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchQuery]);

  // Filter past mitigations
  const filteredPastMitigations = pastMitigations.filter((m) => {
    if (filterType !== "all") {
      const entityType = m.metadata.user && m.metadata.user !== "None" ? "user" : "ip";
      if (entityType !== filterType) return false;
    }
    if (filterMitigation !== "all" && m.metadata.mitigation !== filterMitigation) {
      return false;
    }
    return true;
  });

  const uniqueTypes = Array.from(new Set(pastMitigations.map(m => 
    m.metadata.user && m.metadata.user !== "None" ? "user" : "ip"
  )));

  const uniqueMitigations = Array.from(new Set(
    pastMitigations.map(m => m.metadata.mitigation).filter(Boolean)
  ));

  const formatTimestamp = (timestamp: string) => {
    try {
      return new Date(timestamp).toLocaleString('en-US', {
        month: 'short',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        hour12: true,
      });
    } catch {
      return timestamp;
    }
  };

  return (
    <div className="h-full flex flex-col">
      {/* Main Content */}
      <Card className="h-full flex flex-col overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between mb-4">
            <div>
              <CardTitle className="text-xl font-bold text-gray-900">
                Mitigation Management
              </CardTitle>
              <CardDescription className="text-gray-500 mt-1">
                View and manage security mitigations across your API
              </CardDescription>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setActiveTab("active")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "active"
                  ? "bg-gray-900 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              Active Mitigations ({activeMitigations.length})
            </button>
            <button
              onClick={() => setActiveTab("history")}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === "history"
                  ? "bg-gray-900 text-white"
                  : "bg-gray-100 text-gray-700 hover:bg-gray-200"
              }`}
            >
              History ({pastMitigations.length})
            </button>
          </div>

          {/* Search and Filters - Only show for history tab */}
          {activeTab === "history" && (
            <div className="flex gap-3 mt-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
                <Input
                  placeholder="Search mitigations semantically..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10 bg-gray-50 border-gray-200"
                />
              </div>

              {/* Type Filter */}
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                  <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-700 min-w-[140px] justify-between">
                    <div className="flex items-center gap-2">
                      <Filter className="w-4 h-4" />
                      {filterType === "all" ? "All Types" : filterType.toUpperCase()}
                    </div>
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    className="bg-white rounded-lg shadow-lg border border-gray-200 p-1 min-w-[140px] z-50"
                    sideOffset={5}
                  >
                    <DropdownMenu.Item
                      className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                      onSelect={() => setFilterType("all")}
                    >
                      All Types
                      {filterType === "all" && <Check className="w-4 h-4" />}
                    </DropdownMenu.Item>
                    {uniqueTypes.map((type) => (
                      <DropdownMenu.Item
                        key={type}
                        className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                        onSelect={() => setFilterType(type)}
                      >
                        {type.toUpperCase()}
                        {filterType === type && <Check className="w-4 h-4" />}
                      </DropdownMenu.Item>
                    ))}
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>

              {/* Mitigation Filter */}
              <DropdownMenu.Root>
                <DropdownMenu.Trigger asChild>
                  <button className="px-4 py-2 border border-gray-200 rounded-lg hover:bg-gray-50 flex items-center gap-2 text-gray-700 min-w-[160px] justify-between">
                    {filterMitigation === "all" ? "All Mitigations" : mitigationConfig[filterMitigation]?.label || filterMitigation}
                    <ChevronDown className="w-4 h-4" />
                  </button>
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    className="bg-white rounded-lg shadow-lg border border-gray-200 p-1 min-w-[160px] z-50"
                    sideOffset={5}
                  >
                    <DropdownMenu.Item
                      className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                      onSelect={() => setFilterMitigation("all")}
                    >
                      All Mitigations
                      {filterMitigation === "all" && <Check className="w-4 h-4" />}
                    </DropdownMenu.Item>
                    {uniqueMitigations.map((mitigation) => (
                      mitigation ? (
                        <DropdownMenu.Item
                          key={mitigation}
                          className="px-3 py-2 text-sm text-gray-900 hover:bg-gray-100 rounded cursor-pointer outline-none flex items-center justify-between"
                          onSelect={() => setFilterMitigation(mitigation)}
                        >
                          {mitigationConfig[mitigation]?.label || mitigation}
                          {filterMitigation === mitigation && <Check className="w-4 h-4" />}
                        </DropdownMenu.Item>
                      ) : null
                    ))}
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            </div>
          )}
        </CardHeader>

        <CardContent className="flex-1 flex flex-col overflow-hidden">
          {loading ? (
            <div className="flex-1 flex items-center justify-center">
              <p className="text-gray-500">Loading mitigations...</p>
            </div>
          ) : activeTab === "active" ? (
            // Active Mitigations Table
            <div className="flex-1 overflow-y-auto">
              {activeMitigations.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <Shield className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No active mitigations</p>
                    <p className="text-gray-400 text-sm mt-2">
                      All systems are running normally
                    </p>
                  </div>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-white z-10 shadow-sm">
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Type
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Target
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Mitigation
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Time Remaining
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {activeMitigations.map((mitigation, index) => {
                      const config = mitigationConfig[mitigation.mitigation] || mitigationConfig.none;
                      const Icon = config.icon;

                      return (
                        <tr
                          key={`${mitigation.entity_type}-${mitigation.entity}`}
                          className={`border-b border-gray-100 hover:bg-gray-50 transition-colors ${
                            index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                          }`}
                        >
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              {mitigation.entity_type === "ip" ? (
                                <Globe className="w-4 h-4 text-blue-600" />
                              ) : (
                                <User className="w-4 h-4 text-purple-600" />
                              )}
                              <span className="text-sm font-medium text-gray-900 uppercase">
                                {mitigation.entity_type}
                              </span>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm font-mono text-gray-900">
                            {mitigation.entity}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <Icon className={`w-4 h-4 ${config.color}`} />
                              <Badge className={`${config.bgColor} ${config.color} border-0`}>
                                {config.label}
                              </Badge>
                            </div>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-900">
                            <div className="flex items-center gap-2">
                              <Clock className="w-4 h-4 text-gray-400" />
                              <CountdownTimer initialTTL={mitigation.ttl} />
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          ) : (
            // Past Mitigations History
            <div className="flex-1 overflow-y-auto">
              {filteredPastMitigations.length === 0 ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <AlertCircle className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <p className="text-gray-500 text-lg">No historical mitigations found</p>
                    <p className="text-gray-400 text-sm mt-2">
                      {searchQuery ? "Try a different search query" : "Mitigations will appear here once applied"}
                    </p>
                  </div>
                </div>
              ) : (
                <table className="w-full">
                  <thead className="sticky top-0 bg-white z-10 shadow-sm">
                    <tr className="border-b border-gray-200">
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Timestamp
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Target
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Mitigation
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Severity
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Agent
                      </th>
                      <th className="text-left py-3 px-4 text-sm font-semibold text-gray-700 bg-gray-50">
                        Actions
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {filteredPastMitigations.map((mitigation, index) => {
                      const entityType = mitigation.metadata.user && mitigation.metadata.user !== "None" ? "user" : "ip";
                      const entity = entityType === "user" ? mitigation.metadata.user : mitigation.metadata.ip;
                      const mitigationType = mitigation.metadata.mitigation || "unknown";
                      const config = mitigationConfig[mitigationType] || mitigationConfig.none;
                      const Icon = config.icon;
                      const severity = severityConfig.find(s => s.level === mitigation.metadata.severity) || severityConfig[0];

                      return (
                        <tr
                          key={mitigation.id}
                          className={`border-b border-gray-100 hover:bg-gray-50 transition-colors cursor-pointer ${
                            index % 2 === 0 ? "bg-white" : "bg-gray-50/50"
                          }`}
                          onClick={() => setSelectedMitigation(mitigation)}
                        >
                          <td className="py-3 px-4 text-sm text-gray-900">
                            {formatTimestamp(mitigation.metadata.timestamp)}
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              {entityType === "ip" ? (
                                <Globe className="w-4 h-4 text-blue-600" />
                              ) : (
                                <User className="w-4 h-4 text-purple-600" />
                              )}
                              <span className="text-sm font-mono text-gray-900">{entity}</span>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <div className="flex items-center gap-2">
                              <Icon className={`w-4 h-4 ${config.color}`} />
                              <Badge className={`${config.bgColor} ${config.color} border-0`}>
                                {config.label}
                              </Badge>
                            </div>
                          </td>
                          <td className="py-3 px-4">
                            <Badge className={`${severity.color} border-0`}>
                              {severity.label}
                            </Badge>
                          </td>
                          <td className="py-3 px-4 text-sm text-gray-600">
                            {mitigation.metadata.source_agent || "—"}
                          </td>
                          <td className="py-3 px-4">
                            <button
                              onClick={(e) => {
                                e.stopPropagation();
                                setSelectedMitigation(mitigation);
                              }}
                              className="text-sm text-blue-600 hover:text-blue-800 font-medium"
                            >
                              View Details
                            </button>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Detail Modal */}
      {selectedMitigation && (
        <div
          className="fixed inset-0 left-64 bg-black/50 backdrop-blur-sm z-[100] flex items-center justify-center p-8 pt-24 overflow-y-auto"
          onClick={() => setSelectedMitigation(null)}
        >
          <div
            className="bg-white rounded-2xl shadow-2xl w-full max-w-3xl max-h-[75vh] my-auto overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Mitigation Details</h2>
                <p className="text-sm text-gray-600 mt-1">
                  {formatTimestamp(selectedMitigation.metadata.timestamp)}
                </p>
              </div>
              <button
                onClick={() => setSelectedMitigation(null)}
                className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[calc(75vh-120px)]">
              <div className="space-y-6">
                {/* Target Information */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                    <div className="flex items-center gap-2 mb-2">
                      <Globe className="w-4 h-4 text-blue-600" />
                      <p className="text-sm font-semibold text-blue-900">IP Address</p>
                    </div>
                    <p className="text-lg font-mono text-blue-700">{selectedMitigation.metadata.ip}</p>
                  </div>

                  <div className="p-4 bg-purple-50 rounded-lg border border-purple-200">
                    <div className="flex items-center gap-2 mb-2">
                      <User className="w-4 h-4 text-purple-600" />
                      <p className="text-sm font-semibold text-purple-900">User</p>
                    </div>
                    <p className="text-lg font-mono text-purple-700">
                      {selectedMitigation.metadata.user || "—"}
                    </p>
                  </div>
                </div>

                {/* Mitigation & Severity */}
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm font-semibold text-gray-700 mb-2">Mitigation Applied</p>
                    {(() => {
                      const mitigationType = selectedMitigation.metadata.mitigation || "unknown";
                      const config = mitigationConfig[mitigationType] || mitigationConfig.none;
                      const Icon = config.icon;
                      return (
                        <div className="flex items-center gap-2">
                          <Icon className={`w-5 h-5 ${config.color}`} />
                          <Badge className={`${config.bgColor} ${config.color} border-0 text-base px-3 py-1`}>
                            {config.label}
                          </Badge>
                        </div>
                      );
                    })()}
                  </div>

                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm font-semibold text-gray-700 mb-2">Severity Level</p>
                    {(() => {
                      const severity = severityConfig.find(s => s.level === selectedMitigation.metadata.severity) || severityConfig[0];
                      return (
                        <Badge className={`${severity.color} border-0 text-base px-3 py-1`}>
                          {severity.label}
                        </Badge>
                      );
                    })()}
                  </div>
                </div>

                {/* Source Agent */}
                {selectedMitigation.metadata.source_agent && (
                  <div className="p-4 bg-indigo-50 rounded-lg border border-indigo-200">
                    <p className="text-sm font-semibold text-indigo-900 mb-1">Detected By</p>
                    <p className="text-lg text-indigo-700">{selectedMitigation.metadata.source_agent}</p>
                  </div>
                )}

                {/* AI Reasoning */}
                <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                  <div className="flex items-center gap-2 mb-3">
                    <AlertCircle className="w-5 h-5 text-green-700" />
                    <p className="text-sm font-semibold text-green-900">AI Decision Reasoning</p>
                  </div>
                  <p className="text-sm text-green-800 leading-relaxed whitespace-pre-wrap">
                    {selectedMitigation.text}
                  </p>
                </div>

                {/* Additional Metadata */}
                {Object.keys(selectedMitigation.metadata).length > 0 && (
                  <div className="p-4 bg-gray-50 rounded-lg border border-gray-200">
                    <p className="text-sm font-semibold text-gray-900 mb-3">Additional Information</p>
                    <div className="space-y-2 text-sm">
                      {Object.entries(selectedMitigation.metadata)
                        .filter(([key]) => !["user", "ip", "severity", "timestamp", "mitigation", "source_agent"].includes(key))
                        .map(([key, value]) => (
                          <div key={key} className="flex justify-between py-1 border-b border-gray-200 last:border-0">
                            <span className="text-gray-600 font-medium">{key}:</span>
                            <span className="text-gray-900">{String(value)}</span>
                          </div>
                        ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

