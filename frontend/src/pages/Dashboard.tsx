"use client";

import { useState, useEffect, useRef } from "react";
import { X, AlertCircle, Clock, CheckCircle, Ban, XCircle, Pause, Shield } from "lucide-react";
import DetectionLog from "@/components/Detection-Log";
import MetricsOverview from "@/components/Metrics-Overview";
import EndpointStatus from "@/components/Endpoint-Status";
import ThreatAnalysis from "@/components/Threat-analysis";
import Navbar from "@/components/Navbar";
import RunTests from "@/components/RunTests";
import Chat from "./Chat";
import type { RunTestsTestType, RunTestsLogEntry } from "@/components/RunTests";

type MitigationLevel = {
  id: string;
  name: string;
  icon: typeof Shield;
  color: string;
  bgColor: string;
  borderColor: string;
};

const allMitigationLevels: MitigationLevel[] = [
  { id: 'nothing', name: 'Do Nothing', icon: CheckCircle, color: 'text-gray-600', bgColor: 'bg-gray-100', borderColor: 'border-gray-300' },
  { id: 'slowdown', name: 'Slow Down', icon: Clock, color: 'text-yellow-600', bgColor: 'bg-yellow-50', borderColor: 'border-yellow-300' },
  { id: 'captcha', name: 'CAPTCHA', icon: Shield, color: 'text-orange-600', bgColor: 'bg-orange-50', borderColor: 'border-orange-300' },
  { id: 'tempban', name: 'Temporary Ban', icon: Ban, color: 'text-red-600', bgColor: 'bg-red-50', borderColor: 'border-red-300' },
  { id: 'permaban', name: 'Perma Ban', icon: XCircle, color: 'text-red-800', bgColor: 'bg-red-100', borderColor: 'border-red-500' },
  { id: 'alert', name: 'Alert Only', icon: AlertCircle, color: 'text-blue-600', bgColor: 'bg-blue-50', borderColor: 'border-blue-300' },
  { id: 'pause', name: 'Pause Request', icon: Pause, color: 'text-purple-600', bgColor: 'bg-purple-50', borderColor: 'border-purple-300' },
];

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<
    "overview" | "detections" | "endpoints" | "run-tests" | "chat"
  >("overview");
  const [showSettings, setShowSettings] = useState(false);

  const getTabTitle = () => {
    switch (activeTab) {
      case "overview":
        return "Overview";
      case "detections":
        return "Detections";
      case "endpoints":
        return "Endpoints";
      case "run-tests":
        return "Run Tests";
      default:
        return "Overview";
    }
  };
  
  const [timelineLevels, setTimelineLevels] = useState<MitigationLevel[]>([
    allMitigationLevels[0], // Do Nothing
    allMitigationLevels[1], // Slow Down
    allMitigationLevels[2], // CAPTCHA
    allMitigationLevels[3], // Temporary Ban
    allMitigationLevels[4], // Perma Ban
  ]);

  // WebSocket ref for test execution (persists across tab changes)
  const testWebSocketRef = useRef<WebSocket | null>(null);

  const availableLevels = allMitigationLevels.filter(
    level => !timelineLevels.find(tl => tl.id === level.id)
  );

  // Drag and Drop state
  const [draggedLevel, setDraggedLevel] = useState<MitigationLevel | null>(null);
  const [draggedFromTimeline, setDraggedFromTimeline] = useState(false);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  const handleDragStart = (level: MitigationLevel, fromTimeline: boolean, index?: number) => {
    setDraggedLevel(level);
    setDraggedFromTimeline(fromTimeline);
    if (index !== undefined) {
      setDraggedIndex(index);
    }
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDropOnTimeline = (targetIndex: number) => {
    if (!draggedLevel) return;

    if (draggedFromTimeline && draggedIndex !== null) {
      // Reordering within timeline
      const newLevels = [...timelineLevels];
      newLevels.splice(draggedIndex, 1);
      newLevels.splice(targetIndex, 0, draggedLevel);
      setTimelineLevels(newLevels);
    } else {
      // Adding from available to timeline
      const newLevels = [...timelineLevels];
      newLevels.splice(targetIndex, 0, draggedLevel);
      setTimelineLevels(newLevels);
    }

    setDraggedLevel(null);
    setDraggedFromTimeline(false);
    setDraggedIndex(null);
  };

  const handleDropOnAvailable = () => {
    if (!draggedLevel || !draggedFromTimeline) return;

    // Remove from timeline
    const newLevels = timelineLevels.filter(level => level.id !== draggedLevel.id);
    setTimelineLevels(newLevels);

    setDraggedLevel(null);
    setDraggedFromTimeline(false);
    setDraggedIndex(null);
  };

  const handleRemoveFromTimeline = (index: number) => {
    const newLevels = [...timelineLevels];
    newLevels.splice(index, 1);
    setTimelineLevels(newLevels);
  };

  // RunTests state
  const [testActiveTab, setTestActiveTab] = useState<RunTestsTestType>('Authentication');
  const [runningTests, setRunningTests] = useState<Set<string>>(new Set());
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<RunTestsLogEntry[]>([]);
  const [completedCount, setCompletedCount] = useState(0);
  const [currentRequest, setCurrentRequest] = useState(0);
  const [totalRequests, setTotalRequests] = useState(0);

  // Handle Escape key to close modal
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && showSettings) {
        setShowSettings(false);
      }
    };

    document.addEventListener('keydown', handleEscape);
    return () => document.removeEventListener('keydown', handleEscape);
  }, [showSettings]);

  // Prevent body scroll when modal is open
  useEffect(() => {
    if (showSettings) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = 'unset';
    }
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [showSettings]);

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar Navigation */}
      <Navbar 
        activeTab={activeTab} 
        setActiveTab={setActiveTab}
        onSettingsClick={() => setShowSettings(true)}
      />

      {/* Main Content Area */}
      <div className="flex-1 ml-64">
        {/* Top Header */}
        <header className="border-b border-gray-200 bg-white fixed top-0 right-0 left-64 z-40">
          <div className="px-6 py-5">
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-2xl font-bold text-gray-900 leading-none" style={{ fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>{getTabTitle()}</h1>
                <p className="text-xs text-gray-600 mt-2">
                  Real-time API Protection
                </p>
              </div>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 px-3 py-1.5 bg-green-500/10 border border-green-500/30 rounded-lg">
                  <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-green-600 font-medium">
                    System Active
                  </span>
                </div>
                <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold cursor-pointer hover:shadow-lg hover:shadow-blue-500/50 transition-all">
                  U
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <main className="px-6 py-8 mt-[89px]">
          {/* Overview Tab */}
          {activeTab === "overview" && (
            <div className="space-y-8">
              {/* Key Metrics */}
              <MetricsOverview />

              {/* Threat Analysis & Recent Detections */}
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="lg:col-span-2">
                  <DetectionLog onViewAll={() => setActiveTab("detections")} />
                </div>
                <div>
                  <ThreatAnalysis />
                </div>
              </div>
            </div>
          )}

          {/* Detections Tab */}
          {activeTab === "detections" && (
            <div className="space-y-6">
              <DetectionLog expanded />
            </div>
          )}

          {/* Endpoints Tab */}
          {activeTab === "endpoints" && (
            <div className="space-y-6">
              <EndpointStatus />
            </div>
          )}

          {/* Run Tests Tab */}
          {activeTab === "run-tests" && (
            <div className="space-y-6">
              <RunTests
                activeTab={testActiveTab}
                setActiveTab={setTestActiveTab}
                runningTests={runningTests}
                setRunningTests={setRunningTests}
                progress={progress}
                setProgress={setProgress}
                logs={logs}
                setLogs={setLogs}
                completedCount={completedCount}
                setCompletedCount={setCompletedCount}
                currentRequest={currentRequest}
                setCurrentRequest={setCurrentRequest}
                totalRequests={totalRequests}
                setTotalRequests={setTotalRequests}
                wsRef={testWebSocketRef}
              />
            </div>
          )}

          {/* Chat Tab */}
          {activeTab === "chat" && (
            <div className="fixed inset-0 ml-64 mt-[73px]">
              <Chat />
            </div>
          )}
        </main>
      </div>

      {/* Settings Modal */}
      {showSettings && (
        <div 
          className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4 modal-overlay"
          onClick={() => setShowSettings(false)}
        >
          <div 
            className="bg-white rounded-2xl shadow-2xl w-[95vw] max-w-[1600px] max-h-[85vh] overflow-hidden modal-content"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b border-gray-200">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">Mitigation Timeline</h2>
                <p className="text-sm text-gray-600 mt-1">Customize your threat escalation path</p>
              </div>
              <button
                onClick={() => setShowSettings(false)}
                className="w-10 h-10 flex items-center justify-center rounded-lg hover:bg-gray-100 transition-colors"
              >
                <X className="w-5 h-5 text-gray-600" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="p-8 overflow-y-auto max-h-[calc(85vh-100px)]">
              <div className="space-y-8">
                {/* Timeline Section */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Active Mitigation Levels (Drag to Reorder)</h3>
                  <div className="flex items-center gap-2">
                    {timelineLevels.map((level, index) => {
                      const Icon = level.icon;
                      return (
                        <div key={level.id} className="flex items-center gap-2 flex-1">
                          {/* Drop zone before each item */}
                          <div
                            onDragOver={handleDragOver}
                            onDrop={(e) => {
                              e.preventDefault();
                              e.stopPropagation();
                              handleDropOnTimeline(index);
                            }}
                            className={`w-4 h-[140px] rounded-lg transition-all ${
                              draggedLevel && draggedLevel.id !== level.id
                                ? 'bg-blue-200 border-2 border-dashed border-blue-400'
                                : 'bg-transparent'
                            }`}
                          />
                          
                          <div 
                            draggable
                            onDragStart={() => handleDragStart(level, true, index)}
                            className={`${level.bgColor} ${level.borderColor} border-2 rounded-xl p-4 flex flex-col items-center justify-center min-h-[140px] flex-1 hover:shadow-lg transition-all cursor-move relative group ${
                              draggedLevel?.id === level.id ? 'opacity-50' : ''
                            }`}
                          >
                            <button
                              onClick={() => handleRemoveFromTimeline(index)}
                              className="absolute top-2 right-2 w-6 h-6 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center hover:bg-red-600"
                              title="Remove from timeline"
                            >
                              <X className="w-4 h-4" />
                            </button>
                            <Icon className={`w-8 h-8 ${level.color} mb-2`} />
                            <span className={`text-sm font-semibold ${level.color} text-center`}>{level.name}</span>
                            <span className="text-xs text-gray-500 mt-1">Level {index + 1}</span>
                          </div>

                          {index < timelineLevels.length - 1 && (
                            <div className="flex flex-col items-center mx-2">
                              <div className="w-8 h-0.5 bg-gradient-to-r from-gray-300 to-gray-400"></div>
                              <span className="text-xs text-gray-400 mt-1">→</span>
                            </div>
                          )}
                        </div>
                      );
                    })}
                    
                    {/* Drop zone at the end */}
                    <div
                      onDragOver={handleDragOver}
                      onDrop={(e) => {
                        e.preventDefault();
                        e.stopPropagation();
                        handleDropOnTimeline(timelineLevels.length);
                      }}
                      className={`w-4 h-[140px] rounded-lg transition-all ${
                        draggedLevel
                          ? 'bg-blue-200 border-2 border-dashed border-blue-400'
                          : 'bg-transparent'
                      }`}
                    />
                  </div>
                </div>

                {/* Available Levels */}
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-4">Available Levels (Drag to Timeline)</h3>
                  <div 
                    className="flex gap-4 min-h-[140px] p-4 bg-gray-50 rounded-xl border-2 border-dashed border-gray-300"
                    onDragOver={handleDragOver}
                    onDrop={(e) => {
                      e.preventDefault();
                      handleDropOnAvailable();
                    }}
                  >
                    {availableLevels.map(level => {
                      const Icon = level.icon;
                      return (
                        <div 
                          key={level.id}
                          draggable
                          onDragStart={() => handleDragStart(level, false)}
                          className={`${level.bgColor} ${level.borderColor} border-2 rounded-xl p-4 flex flex-col items-center justify-center min-h-[120px] w-48 hover:shadow-lg transition-all cursor-grab active:cursor-grabbing ${
                            draggedLevel?.id === level.id ? 'opacity-50' : ''
                          }`}
                        >
                          <Icon className={`w-7 h-7 ${level.color} mb-2`} />
                          <span className={`text-sm font-semibold ${level.color} text-center`}>{level.name}</span>
                        </div>
                      );
                    })}
                    {availableLevels.length === 0 && (
                      <div className="flex-1 flex items-center justify-center">
                        <p className="text-gray-500 text-sm italic">All levels are currently in use. Drag items here to remove them from the timeline.</p>
                      </div>
                    )}
                  </div>
                </div>

                {/* Instructions */}
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <div className="space-y-2">
                    <p className="text-sm text-blue-800 font-semibold">How to use:</p>
                    <ul className="text-sm text-blue-800 list-disc list-inside space-y-1">
                      <li>Drag levels from "Available Levels" to add them to the timeline</li>
                      <li>Drag and drop timeline items onto each other to reorder them</li>
                      <li>Drag timeline items back to "Available Levels" to remove them</li>
                      <li>Click the X button on timeline items to quickly remove them</li>
                    </ul>
                    <p className="text-sm text-blue-700 mt-2">
                      The system will escalate through these levels as threat severity increases.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
