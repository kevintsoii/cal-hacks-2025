import { Activity, Search, LayoutGrid, Shield, Settings, Rocket, MessageSquare } from "lucide-react";
import { useNavigate } from "react-router-dom";

interface NavbarProps {
  readonly activeTab: "overview" | "detections" | "endpoints" | "run-tests" | "chat";
  readonly setActiveTab: (tab: "overview" | "detections" | "endpoints" | "run-tests" | "chat") => void;
  readonly onSettingsClick: () => void;
}

export default function Navbar({
  activeTab,
  setActiveTab,
  onSettingsClick,
}: Readonly<NavbarProps>) {
  const navigate = useNavigate();
  
  const mainNavItems = [
    { id: "overview" as const, label: "Overview", icon: Activity },
    { id: "detections" as const, label: "Detections", icon: Search },
    { id: "endpoints" as const, label: "Endpoints", icon: LayoutGrid },
    { id: "chat" as const, label: "AI Chat", icon: MessageSquare },
  ];

  const testNavItems = [
    { id: "run-tests" as const, label: "Run Tests", icon: Rocket },
  ];

  return (
    <nav className="w-64 bg-white border-r border-gray-200 fixed left-0 top-0 h-full z-50">
      <div className="flex flex-col h-full">
        {/* Sidebar Header */}
        <div className="px-6 py-[18px] border-b border-gray-200 h-[89px] flex items-center">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center gap-3 hover:opacity-80 transition-opacity cursor-pointer"
          >
            <div className="w-11 h-11 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Shield className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900 leading-none" style={{ fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif' }}>Dyno</h2>
            </div>
          </button>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 p-4">
          {/* MAIN Section */}
          <div className="mb-6 mt-4">
            <h3 className="px-4 mb-2 text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Main
            </h3>
            <div className="space-y-1">
              {mainNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-4 px-4 py-3 rounded-lg transition-all ${
                      activeTab === item.id
                        ? "bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/20"
                        : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>

          {/* TESTS Section */}
          <div>
            <h3 className="px-4 mb-2 text-xs font-semibold text-gray-700 uppercase tracking-wider">
              Tests
            </h3>
            <div className="space-y-1">
              {testNavItems.map((item) => {
                const Icon = item.icon;
                return (
                  <button
                    key={item.id}
                    onClick={() => setActiveTab(item.id)}
                    className={`w-full flex items-center gap-4 px-4 py-3 rounded-lg transition-all ${
                      activeTab === item.id
                        ? "bg-gradient-to-r from-blue-600 to-cyan-600 text-white shadow-lg shadow-blue-500/20"
                        : "text-gray-600 hover:bg-gray-100"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span>{item.label}</span>
                  </button>
                );
              })}
            </div>
          </div>
        </div>

        {/* Sidebar Footer */}
        <div className="p-3 border-t border-gray-200">
          <button 
            onClick={onSettingsClick}
            className="w-full flex items-center gap-4 px-3 py-2 rounded-lg text-gray-600 hover:bg-gray-100 transition-all"
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
