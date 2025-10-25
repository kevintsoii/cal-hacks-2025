import { Activity, AlertTriangle, Lock, Home, Settings, FlaskConical } from "lucide-react";

interface NavbarProps {
  readonly activeTab: "overview" | "detections" | "endpoints" | "run-tests";
  readonly setActiveTab: (tab: "overview" | "detections" | "endpoints" | "run-tests") => void;
  readonly onSettingsClick: () => void;
}

export default function Navbar({
  activeTab,
  setActiveTab,
  onSettingsClick,
}: Readonly<NavbarProps>) {
  const navItems = [
    { id: "overview" as const, label: "Overview", icon: Activity },
    { id: "detections" as const, label: "Detections", icon: AlertTriangle },
    { id: "endpoints" as const, label: "Endpoints", icon: Lock },
    { id: "run-tests" as const, label: "Run Tests", icon: FlaskConical },
  ];

  return (
    <nav className="w-64 bg-white border-r border-gray-200 fixed left-0 top-0 h-full z-50">
      <div className="flex flex-col h-full">
        {/* Sidebar Header */}
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center">
              <Home className="w-5 h-5 text-white" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-gray-900 leading-none">Dashboard</h2>
              <p className="text-xs text-gray-500 mt-1">Navigation</p>
            </div>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg font-medium transition-all ${
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

        {/* Sidebar Footer */}
        <div className="p-4 border-t border-gray-200">
          <button 
            onClick={onSettingsClick}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100 font-medium transition-all"
          >
            <Settings className="w-5 h-5" />
            <span>Settings</span>
          </button>
        </div>
      </div>
    </nav>
  );
}
