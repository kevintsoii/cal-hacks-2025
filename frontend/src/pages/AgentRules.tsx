import { useState, useEffect } from "react";
import { Plus, Trash2, Edit2, Save, X, Bot, Shield, Search, Key, Brain } from "lucide-react";
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
};

export default function AgentRules() {
  const [rules, setRules] = useState<AgentRulesData>({
    auth: [],
    search: [],
    general: [],
  });
  const [selectedAgent, setSelectedAgent] = useState<"auth" | "search" | "general">("auth");
  const [newRuleText, setNewRuleText] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  // Load rules from backend
  useEffect(() => {
    loadRules();
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

    const newRule: AgentRule = {
      id: `${selectedAgent}-${Date.now()}`,
      text: newRuleText.trim(),
    };

    setRules({
      ...rules,
      [selectedAgent]: [...rules[selectedAgent], newRule],
    });
    setNewRuleText("");
    saveRules(selectedAgent);
  };

  const deleteRule = (ruleId: string) => {
    setRules({
      ...rules,
      [selectedAgent]: rules[selectedAgent].filter(r => r.id !== ruleId),
    });
    saveRules(selectedAgent);
  };

  const startEdit = (ruleId: string) => {
    setRules({
      ...rules,
      [selectedAgent]: rules[selectedAgent].map(r =>
        r.id === ruleId ? { ...r, isEditing: true } : r
      ),
    });
  };

  const cancelEdit = (ruleId: string) => {
    setRules({
      ...rules,
      [selectedAgent]: rules[selectedAgent].map(r =>
        r.id === ruleId ? { ...r, isEditing: false } : r
      ),
    });
  };

  const saveEdit = (ruleId: string, newText: string) => {
    if (!newText.trim()) return;

    setRules({
      ...rules,
      [selectedAgent]: rules[selectedAgent].map(r =>
        r.id === ruleId ? { ...r, text: newText.trim(), isEditing: false } : r
      ),
    });
    saveRules(selectedAgent);
  };

  const updateRuleText = (ruleId: string, text: string) => {
    setRules({
      ...rules,
      [selectedAgent]: rules[selectedAgent].map(r =>
        r.id === ruleId ? { ...r, text } : r
      ),
    });
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
                          <p className="text-xs text-gray-500">{rules[agent].length} rules</p>
                        </div>
                      </div>
                      <p className="text-xs text-gray-600 text-left">{info.description}</p>
                    </button>
                  );
                })}
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
                      {rules[selectedAgent].length} active rule{rules[selectedAgent].length !== 1 ? "s" : ""}
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
                {rules[selectedAgent].length === 0 ? (
                  <div className="text-center py-12 text-gray-500">
                    <Bot className="w-12 h-12 mx-auto mb-3 text-gray-400" />
                    <p className="text-lg font-medium mb-1">No custom rules yet</p>
                    <p className="text-sm">Add your first rule above to customize this agent's behavior</p>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {rules[selectedAgent].map((rule, index) => (
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
                    <h3 className="font-semibold text-blue-900 mb-1">How Custom Rules Work</h3>
                    <p className="text-sm text-blue-800 leading-relaxed">
                      Rules you add here are dynamically appended to the agent's system prompt. They're loaded
                      on each request, so changes take effect immediately without restarting the backend.
                      Rules should be specific, actionable instructions that help the agent make better security decisions.
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

