import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import './App.css'
import Home from './pages/Home'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import UserSearch from './pages/UserSearch'
import { WebSocketProvider } from './hooks/useWebSocket'
import { ActivityDataProvider } from './hooks/useActivityData'
import ScrollToTop from './components/ScrollToTop'

function App() {
  return (
    <Router>
      <ScrollToTop />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={
          <WebSocketProvider>
            <ActivityDataProvider>
              <Dashboard />
            </ActivityDataProvider>
          </WebSocketProvider>
        } />
        <Route path="/login" element={<Login />} />
        <Route path="/search" element={<UserSearch />} />
      </Routes>
    </Router>
  )
}

export default App