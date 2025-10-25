import { Link } from 'react-router-dom'

export default function Navbar() {
  return (
    <nav className="bg-white border-b border-gray-200 fixed top-0 left-0 right-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          <div className="flex-shrink-0">
            <Link to="/login" className="text-2xl font-bold text-indigo-600 hover:text-indigo-700 transition-colors">
              MyStartup
            </Link>
          </div>
          <div className="flex items-center gap-8">
            <Link 
              to="/login" 
              className="text-gray-700 hover:text-indigo-600 font-medium transition-colors"
            >
              Login
            </Link>
            <Link 
              to="/search" 
              className="text-gray-700 hover:text-indigo-600 font-medium transition-colors"
            >
              Search
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}