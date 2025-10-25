import { useState, useRef, useEffect } from "react";
import { Send, Bot, Loader2, TrendingUp, BarChart3, PieChart as PieChartIcon } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { PieChart, Pie, Cell, ResponsiveContainer, LineChart, Line, XAxis, YAxis, Tooltip, BarChart, Bar, CartesianGrid } from "recharts";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: string;
  chartData?: {
    type: "line" | "bar" | "pie";
    title: string;
    data: {
      labels: string[];
      values: number[];
    };
  };
}

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollContainerRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new content arrives (keeps newest content visible)
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth", block: "end" });
    }
  }, [messages, isLoading]);

  const handleSend = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: input,
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setIsLoading(true);

    try {
      // Call the chatbot agent
      const response = await fetch("http://localhost:8007/query", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ query: input }),
      });

      const data = await response.json();
      
      console.log("Raw API response:", data);
      
      // Parse the response - handle both string and object
      let parsedMessage = data.message || "I couldn't process that request.";
      let chartData = data.chart_data;
      
      // If the message is a JSON string, parse it
      if (typeof parsedMessage === 'string' && parsedMessage.trim().startsWith('{')) {
        try {
          const parsed = JSON.parse(parsedMessage);
          parsedMessage = parsed.message || parsedMessage;
          chartData = parsed.chart_suggestion || chartData;
        } catch (e) {
          console.log("Message is not JSON, using as-is");
        }
      }

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: parsedMessage,
        timestamp: data.timestamp || new Date().toISOString(),
        chartData: chartData,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: "Sorry, I encountered an error connecting to the chatbot service. Please make sure the backend is running.",
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const renderChart = (chartData: Message["chartData"]) => {
    // Handle null or undefined - don't show anything
    if (!chartData || chartData === null) {
      return null;
    }

    // Validate chart data structure exists
    if (!chartData.data?.labels || !chartData.data?.values) {
      return (
        <div className="mt-4 p-4 bg-amber-50/80 backdrop-blur-sm border-2 border-amber-300/60 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3">
            <div className="text-3xl">⚠️</div>
            <div>
              <p className="text-sm font-semibold text-amber-900">Chart data is incomplete</p>
              <p className="text-xs text-amber-700 mt-1">Unable to render visualization due to missing data fields.</p>
            </div>
          </div>
        </div>
      );
    }

    // Check if data arrays are empty
    if (chartData.data.labels.length === 0 || chartData.data.values.length === 0) {
      return (
        <div className="mt-4 p-4 bg-blue-50/80 backdrop-blur-sm border-2 border-blue-300/60 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3">
            <div className="text-3xl">📊</div>
            <div>
              <p className="text-sm font-semibold text-blue-900">No data available</p>
              <p className="text-xs text-blue-700 mt-1">Try a different query or adjust your time range.</p>
            </div>
          </div>
        </div>
      );
    }

    // Validate chart type is supported
    const supportedTypes = ["bar", "line", "pie"];
    if (!supportedTypes.includes(chartData.type)) {
      return (
        <div className="mt-4 p-4 bg-purple-50/80 backdrop-blur-sm border-2 border-purple-300/60 rounded-2xl shadow-sm">
          <div className="flex items-center gap-3">
            <div className="text-3xl">🎨</div>
            <div>
              <p className="text-sm font-semibold text-purple-900">Unsupported chart type</p>
              <p className="text-xs text-purple-700 mt-1">
                Type "{chartData.type}" is not supported. Available: bar, line, pie.
              </p>
            </div>
          </div>
        </div>
      );
    }

    const getChartIcon = () => {
      switch (chartData.type) {
        case "line":
          return <TrendingUp className="w-5 h-5" />;
        case "bar":
          return <BarChart3 className="w-5 h-5" />;
        case "pie":
          return <PieChartIcon className="w-5 h-5" />;
        default:
          return <BarChart3 className="w-5 h-5" />;
      }
    };
    
    // Colors for charts
    const COLORS = ['#3b82f6', '#06b6d4', '#8b5cf6', '#ec4899', '#f59e0b', '#10b981', '#ef4444'];
    
    // Prepare data for recharts
    const chartDataFormatted = chartData.data.labels.map((label, idx) => ({
      name: label,
      value: chartData.data.values[idx],
    }));

    // Render Pie Chart using Recharts
    if (chartData.type === "pie") {
      return (
        <Card className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-2 mb-3">
            {getChartIcon()}
            <h4 className="font-semibold text-gray-800">{chartData.title}</h4>
            <span className="text-xs text-gray-500 ml-auto">Pie Chart</span>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={chartDataFormatted}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(props: any) => `${props.name}: ${(props.percent * 100).toFixed(0)}%`}
                outerRadius={90}
                fill="#8884d8"
                dataKey="value"
              >
                {chartDataFormatted.map((_entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </Card>
      );
    }

    // Render Line Chart using Recharts
    if (chartData.type === "line") {
      return (
        <Card className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
          <div className="flex items-center gap-2 mb-3">
            {getChartIcon()}
            <h4 className="font-semibold text-gray-800">{chartData.title}</h4>
            <span className="text-xs text-gray-500 ml-auto">Line Chart</span>
          </div>
          <ResponsiveContainer width="100%" height={280}>
            <LineChart data={chartDataFormatted} margin={{ top: 5, right: 30, left: 0, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis dataKey="name" stroke="#6b7280" style={{ fontSize: '12px' }} />
              <YAxis stroke="#6b7280" style={{ fontSize: '12px' }} />
              <Tooltip 
                contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="#3b82f6" 
                strokeWidth={3}
                dot={{ fill: '#3b82f6', r: 5 }}
                activeDot={{ r: 7 }}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      );
    }

    // Render Bar Chart using Recharts (horizontal)
    return (
      <Card className="mt-3 p-4 bg-gradient-to-br from-blue-50 to-cyan-50 border-blue-200">
        <div className="flex items-center gap-2 mb-3">
          {getChartIcon()}
          <h4 className="font-semibold text-gray-800">{chartData.title}</h4>
          <span className="text-xs text-gray-500 ml-auto">Bar Chart</span>
        </div>
        <ResponsiveContainer width="100%" height={Math.max(250, chartDataFormatted.length * 50)}>
          <BarChart 
            data={chartDataFormatted} 
            layout="vertical"
            margin={{ top: 5, right: 30, left: 100, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
            <XAxis type="number" stroke="#6b7280" style={{ fontSize: '12px' }} />
            <YAxis 
              type="category" 
              dataKey="name" 
              stroke="#6b7280" 
              style={{ fontSize: '12px' }} 
              width={90}
            />
            <Tooltip 
              contentStyle={{ backgroundColor: '#fff', border: '1px solid #e5e7eb', borderRadius: '8px' }}
            />
            <Bar dataKey="value" radius={[0, 8, 8, 0]}>
              {chartDataFormatted.map((_entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Card>
    );
  };

  return (
    <div className="flex h-screen bg-gradient-to-br from-slate-50 via-blue-50 to-cyan-50">
      {/* Main Query Interface */}
      <div className="flex-1 flex flex-col max-w-7xl mx-auto w-full">
        {/* Query Input Bar - Top (No Panel Background) */}
        <div className="px-6 pt-6 pb-4">
          <div className="max-w-4xl mx-auto">
            <div className="flex gap-3 items-center">
              <div className="flex-1 relative">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Query your security data..."
                  className="w-full h-14 text-base px-6 pr-4 rounded-2xl border-2 border-white/80 bg-white/90 backdrop-blur-md focus:bg-white focus:border-blue-500 focus:ring-2 focus:ring-blue-300 transition-all shadow-xl"
                  disabled={isLoading}
                />
              </div>
              <Button
                onClick={handleSend}
                disabled={isLoading || !input.trim()}
                className="h-14 w-14 rounded-2xl bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-700 hover:to-cyan-700 text-white shadow-xl hover:shadow-2xl hover:scale-105 transition-all flex items-center justify-center"
              >
                {isLoading ? (
                  <Loader2 className="w-6 h-6 animate-spin" />
                ) : (
                  <Send className="w-6 h-6" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Results Container - Smooth Scroll */}
        <div ref={scrollContainerRef} className="flex-1 overflow-y-auto px-6 scroll-smooth">
          {/* Empty State - Vertically Centered (with offset) */}
          {messages.length === 0 && !isLoading && (
            <div className="flex items-center justify-center min-h-full py-12" style={{ marginTop: '-10vh' }}>
              <div className="flex flex-col items-center justify-center text-center px-4">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-3xl flex items-center justify-center mb-8 shadow-2xl animate-in fade-in zoom-in duration-700">
                  <Bot className="w-12 h-12 text-white" />
                </div>
                <h2 className="text-4xl font-bold text-gray-900 mb-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                  Security Analytics Query
                </h2>
                <p className="text-gray-600 text-lg max-w-2xl mb-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
                  Query your API security data and generate visualizations instantly
                </p>
                
                {/* Quick suggestions - Only show when empty */}
                <div className="flex flex-wrap gap-3 justify-center max-w-3xl animate-in fade-in slide-in-from-bottom-4 duration-1000">
                  <button
                    onClick={() => setInput("Show me a pie chart of HTTP methods")}
                    className="text-sm font-medium px-5 py-3 bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/70 hover:border-blue-400 rounded-xl text-gray-700 hover:text-blue-700 transition-all shadow-md hover:shadow-lg"
                  >
                    💥 HTTP Methods Chart
                  </button>
                  <button
                    onClick={() => setInput("Show failed login attempts in the last hour")}
                    className="text-sm font-medium px-5 py-3 bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/70 hover:border-blue-400 rounded-xl text-gray-700 hover:text-blue-700 transition-all shadow-md hover:shadow-lg"
                  >
                    🎯 Failed Logins
                  </button>
                  <button
                    onClick={() => setInput("What are the top 5 most active IPs?")}
                    className="text-sm font-medium px-5 py-3 bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/70 hover:border-blue-400 rounded-xl text-gray-700 hover:text-blue-700 transition-all shadow-md hover:shadow-lg"
                  >
                    📊 Top IPs
                  </button>
                  <button
                    onClick={() => setInput("Show me API usage over time")}
                    className="text-sm font-medium px-5 py-3 bg-white/60 backdrop-blur-md hover:bg-white/90 border border-white/70 hover:border-blue-400 rounded-xl text-gray-700 hover:text-blue-700 transition-all shadow-md hover:shadow-lg"
                  >
                    🚀 Usage Trends
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Chat History Container - Grows downward, newest at bottom */}
          {(messages.length > 0 || isLoading) && (
            <div className="max-w-6xl mx-auto space-y-6 py-6 min-h-full flex flex-col justify-end">
            
              {/* Full Chat History - Ordered from oldest to newest */}
              {messages.map((message) => (
                <div 
                  key={message.id} 
                  className="animate-in fade-in slide-in-from-bottom-6 duration-500"
                  style={{ animationFillMode: 'backwards' }}
                >
                  {message.role === "user" ? (
                    // User Query
                    <div className="mb-4">
                      <div className="flex items-center gap-2 text-sm text-blue-600 mb-2">
                        <span className="font-medium">Query:</span>
                      </div>
                      <p className="text-gray-900 font-semibold text-lg">
                        {message.content}
                      </p>
                    </div>
                  ) : (
                    // Assistant Response
                    <div className="mb-8">
                      <div className="bg-white/95 backdrop-blur-sm rounded-3xl p-8 shadow-xl border border-white/20 hover:shadow-2xl transition-all duration-300">
                        <div className="prose prose-lg max-w-none">
                          <p className="text-gray-800 leading-relaxed whitespace-pre-wrap text-base">
                            {message.content}
                          </p>
                        </div>
                        
                        {/* Only render chart if chartData exists and is not null */}
                        {message.chartData && message.chartData !== null && renderChart(message.chartData)}
                      </div>
                    </div>
                  )}
                </div>
              ))}

              {/* Loading State with Thinking Animation */}
              {isLoading && (
                <div className="animate-in fade-in slide-in-from-bottom-6 duration-300">
                  <div className="bg-gradient-to-br from-white/80 to-blue-50/60 backdrop-blur-sm rounded-3xl p-8 shadow-2xl border border-blue-200/50">
                    <div className="flex items-center justify-center gap-3 mb-4">
                      <div className="relative">
                        <div className="w-14 h-14 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center animate-pulse shadow-lg">
                          <Bot className="w-7 h-7 text-white" />
                        </div>
                        <div className="absolute inset-0 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full animate-ping opacity-20"></div>
                      </div>
                    </div>
                    <div className="text-center space-y-3">
                      <p className="text-xl font-bold text-gray-800">Analyzing your query...</p>
                      <div className="flex items-center justify-center gap-2">
                        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce shadow-lg" style={{ animationDelay: '0ms' }}></div>
                        <div className="w-2.5 h-2.5 bg-cyan-500 rounded-full animate-bounce shadow-lg" style={{ animationDelay: '150ms' }}></div>
                        <div className="w-2.5 h-2.5 bg-blue-500 rounded-full animate-bounce shadow-lg" style={{ animationDelay: '300ms' }}></div>
                      </div>
                      <p className="text-sm text-gray-600">Querying Elasticsearch and generating insights</p>
                    </div>
                  </div>
                </div>
              )}
              
              {/* Scroll anchor - keeps newest content at bottom */}
              <div ref={messagesEndRef} className="pb-24" />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

