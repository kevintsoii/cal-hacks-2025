import { useState, useEffect } from "react";
import { Plus, Trash2, Edit2, Save, X, Bot, Shield, Search, Key, Brain, Settings } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

interface AgentRule {
  id: string;
  text: string;
  isEditing?: boolean;
}

interface AgentRulesData {
  auth: AgentRule[];
  search: AgentRule[];
  general: AgentRule[];
  calibration?: AgentRule[];
}

interface CalibrationRule {
  id: string;
  original_text: string;
  refined_text: string;
  category: string;
  severity: string;
  timestamp: string;
}

const agentInfo = {
  orchestrator: {
    name: "Orchestrator Agent",
    icon: Brain,
    color: "bg-purple-500",
    description: "Routes requests to specialized agents",
    editable: false,
  },
  auth: {
    name: "Auth Agent",
    icon: Key,
    color: "bg-blue-500",
    description: "Handles authentication & login security",
    editable: true,
  },
  search: {
    name: "Search Agent",
    icon: Search,
    color: "bg-green-500",
    description: "Monitors search & data scraping",
    editable: true,
  },
  general: {
    name: "General Agent",
    icon: Shield,
    color: "bg-orange-500",
    description: "Analyzes general API threats",
    editable: true,
  },
  calibration: {
    name: "Calibration Agent",
    icon: Settings,
    color: "bg-cyan-500",
    description: "AI-refined rules with ChromaDB",
    editable: true,
  },
};

export default function AgentRules() {
  const [rules, setRules] = useState<AgentRulesData>({
    auth: [],
    search: [],
    general: [],
    calibration: [],
  });
  const [selectedAgent, setSelectedAgent] = useState<"auth" | "search" | "general" | "calibration">("auth");
  const [newRuleText, setNewRuleText] = useState("");
  const [isSaving, setIsSaving] = useState(false);
  
  // Calibration Agent state
  const [calibrationRules, setCalibrationRules] = useState<CalibrationRule[]>([]);
  const [calibrationInput, setCalibrationInput] = useState("");
  const [isRefining, setIsRefining] = useState(false);
  const [calibrationError, setCalibrationError] = useState<string | null>(null);

  // Load rules from backend
  useEffect(() => {
    loadRules();
    loadCalibrationRules();
  }, []);

  const loadRules = async () => {
    try {
      // Load rules for each agent
      const agents: Array<"auth" | "search" | "general"> = ["auth", "search", "general"];
      const loadedRules: Partial<AgentRulesData> = {};

      for (const agent of agents) {
        const response = await fetch(`http://localhost:8000/api/agent-rules/${agent}`);
        if (response.ok) {
          const data = await response.json();
          loadedRules[agent] = data.rules.map((text: string, index: number) => ({
            id: `${agent}-${index}-${Date.now()}`,
            text,
          }));
        }
      }

      setRules(loadedRules as AgentRulesData);
    } catch (error) {
      console.error("Failed to load rules:", error);
    }
  };

  const saveRules = async (agent: "auth" | "search" | "general") => {
    setIsSaving(true);
    try {
      const ruleTexts = rules[agent].map(r => r.text);
      const response = await fetch(`http://localhost:8000/api/agent-rules/${agent}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ rules: ruleTexts }),
      });

      if (!response.ok) {
        throw new Error("Failed to save rules");
      }
    } catch (error) {
      console.error("Failed to save rules:", error);
      alert("Failed to save rules. Please try again.");
    } finally {
      setIsSaving(false);
    }
  };

  const addRule = () => {
    if (!newRuleText.trim()) return;
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow

    const newRule: AgentRule = {
      id: `${selectedAgent}-${Date.now()}`,
      text: newRuleText.trim(),
    };

    setRules({
      ...rules,
      [selectedAgent]: [...(rules[selectedAgent] || []), newRule],
    });
    setNewRuleText("");
    saveRules(selectedAgent as "auth" | "search" | "general");
  };

  const deleteRule = (ruleId: string) => {
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow
    
    setRules({
      ...rules,
      [selectedAgent]: (rules[selectedAgent] || []).filter((r: AgentRule) => r.id !== ruleId),
    });
    saveRules(selectedAgent as "auth" | "search" | "general");
  };

  const startEdit = (ruleId: string) => {
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow
    
    setRules({
      ...rules,
      [selectedAgent]: (rules[selectedAgent] || []).map((r: AgentRule) =>
        r.id === ruleId ? { ...r, isEditing: true } : r
      ),
    });
  };

  const cancelEdit = (ruleId: string) => {
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow
    
    setRules({
      ...rules,
      [selectedAgent]: (rules[selectedAgent] || []).map((r: AgentRule) =>
        r.id === ruleId ? { ...r, isEditing: false } : r
      ),
    });
  };

  const saveEdit = (ruleId: string, newText: string) => {
    if (!newText.trim()) return;
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow

    setRules({
      ...rules,
      [selectedAgent]: (rules[selectedAgent] || []).map((r: AgentRule) =>
        r.id === ruleId ? { ...r, text: newText.trim(), isEditing: false } : r
      ),
    });
    saveRules(selectedAgent as "auth" | "search" | "general");
  };

  const updateRuleText = (ruleId: string, text: string) => {
    if (selectedAgent === "calibration") return; // Calibration rules use a different flow
    
    setRules({
      ...rules,
      [selectedAgent]: (rules[selectedAgent] || []).map((r: AgentRule) =>
        r.id === ruleId ? { ...r, text } : r
      ),
    });
  };
  
  // Calibration Agent functions
  const loadCalibrationRules = async () => {
    try {
      console.log("Loading calibration rules...");
      const response = await fetch("http://localhost:8000/api/calibration-rules");
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to load rules:", response.status, errorText);
        throw new Error(`HTTP ${response.status}: ${errorText}`);
      }
      
      const data = await response.json();
      console.log("Loaded calibration rules:", data);
      setCalibrationRules(data.rules || []);
    } catch (error) {
      console.error("Failed to load calibration rules:", error);
      setCalibrationError(error instanceof Error ? error.message : "Failed to load rules");
    }
  };

  const handleAddCalibrationRule = async () => {
    if (!calibrationInput.trim()) {
      setCalibrationError("Please enter a security rule");
      return;
    }
    
    setIsRefining(true);
    setCalibrationError(null);
    
    try {
      console.log("Adding calibration rule:", calibrationInput);
      const response = await fetch("http://localhost:8000/api/calibration-rules", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_input: calibrationInput }),
      });
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Failed to add rule:", response.status, errorText);
        let errorMessage = "Failed to create rule";
        try {
          const errorData = JSON.parse(errorText);
          errorMessage = errorData.detail || errorMessage;
        } catch {
          errorMessage = errorText || errorMessage;
        }
        throw new Error(errorMessage);
      }
      
      const newRule = await response.json();
      console.log("Rule created successfully:", newRule);
      
      // Clear input on success
      setCalibrationInput("");
      setCalibrationError(null);
      
      // Reload all rules to ensure fresh data from DB
      await loadCalibrationRules();
    } catch (error) {
      console.error("Error adding calibration rule:", error);
      setCalibrationError(error instanceof Error ? error.message : "Failed to add rule");
    } finally {
      setIsRefining(false);
    }
  };
  
  const handleDeleteCalibrationRule = async (ruleId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/calibration-rules/${ruleId}`, {
        method: "DELETE",
      });
      
      if (!response.ok) {
        throw new Error("Failed to delete rule");
      }
      
      // Reload all rules to ensure fresh data from DB
      await loadCalibrationRules();
    } catch (error) {
      console.error("Error deleting calibration rule:", error);
      setCalibrationError("Failed to delete rule");
    }
  };

  const getSeverityColor = (severity: string) => {
    switch (severity.toLowerCase()) {
      case "critical": return "bg-red-100 text-red-800 border-red-300";
      case "high": return "bg-orange-100 text-orange-800 border-orange-300";
      case "medium": return "bg-yellow-100 text-yellow-800 border-yellow-300";
      case "low": return "bg-blue-100 text-blue-800 border-blue-300";
      default: return "bg-gray-100 text-gray-800 border-gray-300";
    }
  };

  const getCategoryColor = (category: string) => {
    const colors: Record<string, string> = {
      auth: "bg-purple-100 text-purple-800",
      search: "bg-blue-100 text-blue-800",
      rate_limit: "bg-orange-100 text-orange-800",
      data_access: "bg-green-100 text-green-800",
      sql_injection: "bg-red-100 text-red-800",
    };
    return colors[category.toLowerCase()] || "bg-gray-100 text-gray-800";
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Agent Rules Management</h1>
          <p className="text-gray-600">Configure custom security rules for each AI agent</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Agent Flow Sidebar */}
          <div className="lg:col-span-1">
            <Card className="sticky top-8">
              <CardHeader>
                <CardTitle className="text-lg">Agent Pipeline</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Orchestrator */}
                <div className="p-3 bg-purple-50 border-2 border-purple-200 rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <div className={`w-8 h-8 ${agentInfo.orchestrator.color} rounded-lg flex items-center justify-center`}>
                      <Brain className="w-5 h-5 text-white" />
                    </div>
                    <div className="flex-1">
                      <p className="font-semibold text-sm text-gray-900">{agentInfo.orchestrator.name}</p>
                    </div>
                  </div>
                  <p className="text-xs text-gray-600">{agentInfo.orchestrator.description}</p>
                </div>

                <div className="flex justify-center">
                  <div className="w-0.5 h-8 bg-gray-300"></div>
                </div>

                {/* Specialist Agents */}
                {(["auth", "search", "general"] as const).map((agent) => {
                  const info = agentInfo[agent];
                  const Icon = info.icon;
                  const isSelected = selectedAgent === agent;
                  const ruleCount = rules[agent]?.length || 0;

                  return (
                    <button
                      key={agent}
                      onClick={() => setSelectedAgent(agent)}
                      className={`w-full p-3 rounded-lg border-2 transition-all ${
                        isSelected
                          ? "border-blue-500 bg-blue-50 shadow-md"
                          : "border-gray-200 bg-white hover:border-gray-300 hover:shadow"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-8 h-8 ${info.color} rounded-lg flex items-center justify-center`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 text-left">
                          <p className="font-semibold text-sm text-gray-900">{info.name}</p>
                          <p className="text-xs text-gray-500">{ruleCount} rules</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 text-left">{info.description}</p>
                    </button>
                  );
                })}

                <div className="flex justify-center">
                  <div className="w-0.5 h-8 bg-gray-300"></div>
                </div>

                {/* Calibration Agent */}
                {(() => {
                  const agent = "calibration";
                  const info = agentInfo[agent];
                  const Icon = info.icon;
                  const isSelected = selectedAgent === agent;
                  const ruleCount = calibrationRules.length;

                  return (
                    <button
                      onClick={() => setSelectedAgent(agent)}
                      className={`w-full p-3 rounded-lg border-2 transition-all ${
                        isSelected
                          ? "border-blue-500 bg-blue-50 shadow-md"
                          : "border-gray-200 bg-white hover:border-gray-300 hover:shadow"
                      }`}
                    >
                      <div className="flex items-center gap-2 mb-2">
                        <div className={`w-8 h-8 ${info.color} rounded-lg flex items-center justify-center`}>
                          <Icon className="w-5 h-5 text-white" />
                        </div>
                        <div className="flex-1 text-left">
                          <p className="font-semibold text-sm text-gray-900">{info.name}</p>
                          <p className="text-xs text-gray-500">{ruleCount} rules</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 text-left">{info.description}</p>
                    </button>
                  );
                })()}
              </CardContent>
            </Card>
          </div>

          {/* Rules Editor */}
          <div className="lg:col-span-3 space-y-6">
            {/* Selected Agent Header */}
            <Card>
              <CardHeader>
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 ${agentInfo[selectedAgent].color} rounded-xl flex items-center justify-center`}>
                    {(() => {
                      const Icon = agentInfo[selectedAgent].icon;
                      return <Icon className="w-6 h-6 text-white" />;
                    })()}
                  </div>
                  <div>
                    <CardTitle>{agentInfo[selectedAgent].name}</CardTitle>
                    <CardDescription>{agentInfo[selectedAgent].description}</CardDescription>
                  </div>
                </div>
              </CardHeader>
            </Card>

            {/* Specialist Agents UI */}
            {selectedAgent !== "calibration" && (
              <>
                {/* Add New Rule */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Add New Rule</CardTitle>
                    <CardDescription>
                      Define a custom security rule that will be appended to this agent's prompt
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex gap-3">
                      <Textarea
                        value={newRuleText}
                        onChange={(e) => setNewRuleText(e.target.value)}
                        placeholder="E.g., Flag any login attempts from known VPN IP ranges"
                        className="flex-1 min-h-[80px]"
                        onKeyDown={(e) => {
                          if (e.key === "Enter" && e.ctrlKey) {
                            addRule();
                          }
                        }}
                      />
                      <Button
                        onClick={addRule}
                        disabled={!newRuleText.trim()}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Plus className="w-4 h-4 mr-2" />
                        Add Rule
                      </Button>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">Press Ctrl + Enter to quickly add a rule</p>
                  </CardContent>
                </Card>

                {/* Current Rules */}
                <Card>
                  <CardHeader>
                    <div className="flex items-center justify-between">
                      <div>
                        <CardTitle className="text-lg">Current Rules</CardTitle>
                        <CardDescription>
                          {(rules[selectedAgent] || []).length} active rule{(rules[selectedAgent] || []).length !== 1 ? "s" : ""}
                        </CardDescription>
                      </div>
                      {isSaving && (
                        <span className="text-sm text-blue-600 flex items-center gap-2">
                          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                          Saving...
                        </span>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent>
                    {(rules[selectedAgent] || []).length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                        <p className="text-lg font-medium mb-1">No custom rules yet</p>
                        <p className="text-sm">Add your first rule above to customize this agent's behavior</p>
                      </div>
                    ) : (
                      <div className="space-y-3">
                        {(rules[selectedAgent] || []).map((rule: AgentRule, index: number) => (
                          <div
                            key={rule.id}
                            className="p-4 bg-gray-50 border border-gray-200 rounded-lg hover:border-gray-300 transition-all"
                          >
                            {rule.isEditing ? (
                              // Edit Mode
                              <div className="space-y-3">
                                <Textarea
                                  value={rule.text}
                                  onChange={(e) => updateRuleText(rule.id, e.target.value)}
                                  className="w-full"
                                  autoFocus
                                />
                                <div className="flex gap-2">
                                  <Button
                                    size="sm"
                                    onClick={() => saveEdit(rule.id, rule.text)}
                                    className="bg-green-600 hover:bg-green-700"
                                  >
                                    <Save className="w-4 h-4 mr-1" />
                                    Save
                                  </Button>
                                  <Button
                                    size="sm"
                                    variant="outline"
                                    onClick={() => cancelEdit(rule.id)}
                                  >
                                    <X className="w-4 h-4 mr-1" />
                                    Cancel
                                  </Button>
                                </div>
                              </div>
                            ) : (
                              // View Mode
                              <div className="flex items-start gap-3">
                                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-700 rounded-full flex items-center justify-center text-xs font-bold mt-0.5">
                                  {index + 1}
                                </div>
                                <p className="flex-1 text-gray-900 leading-relaxed">{rule.text}</p>
                                <div className="flex gap-1">
                                  <button
                                    onClick={() => startEdit(rule.id)}
                                    className="p-2 text-gray-500 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                                    title="Edit rule"
                                  >
                                    <Edit2 className="w-4 h-4" />
                                  </button>
                                  <button
                                    onClick={() => deleteRule(rule.id)}
                                    className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                                    title="Delete rule"
                                  >
                                    <Trash2 className="w-4 h-4" />
                                  </button>
                                </div>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {/* Calibration Agent UI */}
            {selectedAgent === "calibration" && (
              <>
                {/* Add AI-Refined Rule */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">Add AI-Refined Security Rule</CardTitle>
                    <CardDescription>
                      Enter a rule in plain English. Groq AI will refine it and save to ChromaDB with semantic embeddings.
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <Textarea
                        value={calibrationInput}
                        onChange={(e) => setCalibrationInput(e.target.value)}
                        placeholder="E.g., Block users who try too many passwords"
                        className="min-h-[100px]"
                        disabled={isRefining}
                      />
                      {calibrationError && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
                          {calibrationError}
                        </div>
                      )}
                      <Button
                        onClick={handleAddCalibrationRule}
                        disabled={!calibrationInput.trim() || isRefining}
                        className="w-full bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500"
                      >
                        {isRefining ? (
                          <>
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                            Refining with AI...
                          </>
                        ) : (
                          <>
                            <Plus className="w-4 h-4 mr-2" />
                            Add & Refine Rule
                          </>
                        )}
                      </Button>
                    </div>
                  </CardContent>
                </Card>

                {/* AI-Refined Rules */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">AI-Refined Rules in ChromaDB</CardTitle>
                    <CardDescription>
                      {calibrationRules.length} rule{calibrationRules.length !== 1 ? "s" : ""} stored with semantic embeddings
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    {calibrationRules.length === 0 ? (
                      <div className="text-center py-12 text-gray-500">
                        <Settings className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                        <p className="text-lg font-medium mb-1">No AI-refined rules yet</p>
                        <p className="text-sm">Add your first rule above to let Groq AI refine and store it in ChromaDB</p>
                      </div>
                    ) : (
                      <div className="space-y-4">
                        {calibrationRules.map((rule) => (
                          <div
                            key={rule.id}
                            className="p-4 bg-gradient-to-br from-cyan-50 to-blue-50 border border-cyan-200 rounded-lg"
                          >
                            <div className="flex items-start justify-between gap-3 mb-3">
                              <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                  <span className={`px-2 py-1 rounded text-xs font-semibold ${getCategoryColor(rule.category)}`}>
                                    {rule.category}
                                  </span>
                                  <span className={`px-2 py-1 rounded text-xs font-semibold border ${getSeverityColor(rule.severity)}`}>
                                    {rule.severity}
                                  </span>
                                </div>
                                <p className="text-sm text-gray-600 mb-2">
                                  <span className="font-medium">Original:</span> {rule.original_text}
                                </p>
                                <p className="text-sm text-gray-900 font-medium">
                                  <span className="font-semibold">AI-Refined:</span> {rule.refined_text}
                                </p>
                              </div>
                              <button
                                onClick={() => handleDeleteCalibrationRule(rule.id)}
                                className="p-2 text-gray-500 hover:text-red-600 hover:bg-red-50 rounded transition-colors flex-shrink-0"
                                title="Delete rule"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                            <p className="text-xs text-gray-500">
                              Added {new Date(rule.timestamp).toLocaleString()}
                            </p>
                          </div>
                        ))}
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}

            {/* Info Card */}
            <Card className="bg-blue-50 border-blue-200">
              <CardContent className="pt-6">
                <div className="flex gap-3">
                  <div className="flex-shrink-0">
                    <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center">
                      <Bot className="w-6 h-6 text-white" />
                    </div>
                  </div>
                  <div>
                    <h3 className="font-semibold text-blue-900 mb-1">
                      {selectedAgent === "calibration" ? "AI-Refined ChromaDB Rules" : "How Custom Rules Work"}
                    </h3>
                    <p className="text-sm text-blue-800 leading-relaxed">
                      {selectedAgent === "calibration" 
                        ? "These rules are refined by Groq AI and stored in ChromaDB with semantic embeddings. The Calibration Agent queries them when making mitigation decisions, combining AI intelligence with historical data for smarter security responses."
                        : "Rules you add here are dynamically appended to the agent's system prompt. They're loaded on each request, so changes take effect immediately without restarting the backend. Rules should be specific, actionable instructions that help the agent make better security decisions."
                      }
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

