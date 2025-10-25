import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { MagnifyingGlassIcon, DashboardIcon, RocketIcon, GearIcon, CubeIcon } from '@radix-ui/react-icons'

type Section = 'detections' | 'dashboards' | 'run-tests' | 'settings'

export default function Dashboard() {
  const [activeSection, setActiveSection] = useState<Section>('detections')
  const navigate = useNavigate()

  const sidebarItems = [
    { id: 'detections' as Section, label: 'Detections', icon: MagnifyingGlassIcon },
    { id: 'dashboards' as Section, label: 'Dashboards', icon: DashboardIcon },
    { id: 'run-tests' as Section, label: 'Run Tests', icon: RocketIcon },
    { id: 'settings' as Section, label: 'Settings', icon: GearIcon },
  ]

  const renderContent = () => {
    switch (activeSection) {
      case 'detections':
        return <SectionPlaceholder title="Detections" />
      case 'dashboards':
        return <SectionPlaceholder title="Dashboards" />
      case 'run-tests':
        return <SectionPlaceholder title="Run Tests" />
      case 'settings':
        return <SectionPlaceholder title="Settings" />
      default:
        return <SectionPlaceholder title="Detections" />
    }
  }

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 flex flex-col">
        {/* Logo Section */}
        <div 
          className="p-6 border-b border-gray-200 cursor-pointer hover:bg-gray-50 transition-colors"
          onClick={() => navigate('/')}
        >
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/20">
              <span className="text-white text-xl font-bold">A</span>
            </div>
            <span className="text-xl font-bold text-gray-900">AIgateway</span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="flex-1 p-4 space-y-6">
          {/* Main Category */}
          <div className="space-y-2">
            <div className="px-3 mb-3">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">Main</span>
            </div>
            {sidebarItems.slice(0, 3).map((item) => {
              const IconComponent = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full text-left px-5 py-4 rounded-lg transition-all duration-200 flex items-center space-x-3 ${
                    activeSection === item.id
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-medium shadow-lg shadow-blue-500/30'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <IconComponent className="w-5 h-5" />
                  <span className="text-sm">{item.label}</span>
                </button>
              )
            })}
          </div>

          {/* System Category */}
          <div className="space-y-2">
            <div className="px-3 mb-3">
              <span className="text-xs font-semibold text-gray-600 uppercase tracking-wider">System</span>
            </div>
            {sidebarItems.slice(3).map((item) => {
              const IconComponent = item.icon
              return (
                <button
                  key={item.id}
                  onClick={() => setActiveSection(item.id)}
                  className={`w-full text-left px-5 py-4 rounded-lg transition-all duration-200 flex items-center space-x-3 ${
                    activeSection === item.id
                      ? 'bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-medium shadow-lg shadow-blue-500/30'
                      : 'text-gray-600 hover:bg-gray-100 hover:text-gray-900'
                  }`}
                >
                  <IconComponent className="w-5 h-5" />
                  <span className="text-sm">{item.label}</span>
                </button>
              )
            })}
          </div>
        </nav>

        {/* Footer Section */}
        <div className="p-4 border-t border-gray-200">
          <div className="px-4 py-2 text-xs text-gray-500">
            © 2025 AIgateway
          </div>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-gray-50">
        {/* Top Bar */}
        <header className="bg-white border-b border-gray-200 px-8 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900">
                {sidebarItems.find(item => item.id === activeSection)?.label}
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Manage and monitor your AI gateway
              </p>
            </div>
            <div className="flex items-center space-x-3">
              <button className="px-5 py-2.5 text-sm font-semibold text-white bg-gradient-to-r from-blue-600 to-cyan-600 rounded-lg hover:from-blue-500 hover:to-cyan-500 transition-all shadow-lg shadow-blue-500/30 hover:shadow-blue-500/50">
                Help
              </button>
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-full flex items-center justify-center text-white font-bold cursor-pointer hover:shadow-lg hover:shadow-blue-500/50 transition-all">
                U
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <div className="p-8">
          {renderContent()}
        </div>
      </main>
    </div>
  )
}

function SectionPlaceholder({ title }: { title: string }) {
  return (
    <div className="bg-white rounded-xl shadow-xl border border-gray-200 p-12">
      <div className="max-w-2xl mx-auto text-center">
        <div className="w-24 h-24 bg-gradient-to-br from-blue-500/20 to-cyan-500/20 rounded-full mx-auto mb-6 flex items-center justify-center border border-blue-500/30">
          <CubeIcon className="w-12 h-12 text-blue-500" />
        </div>
        <h2 className="text-3xl font-bold text-gray-900 mb-3">{title}</h2>
        <p className="text-gray-600 text-lg">
          This section is coming soon. Stay tuned for exciting features!
        </p>
        <div className="mt-8 flex justify-center space-x-4">
          <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce shadow-lg shadow-blue-500/50"></div>
          <div className="w-2 h-2 bg-cyan-500 rounded-full animate-bounce shadow-lg shadow-cyan-500/50" style={{ animationDelay: '0.1s' }}></div>
          <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce shadow-lg shadow-blue-400/50" style={{ animationDelay: '0.2s' }}></div>
        </div>
      </div>
    </div>
  )
}