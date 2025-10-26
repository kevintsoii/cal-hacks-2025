import { useNavigate } from 'react-router-dom'
import { RocketIcon, LightningBoltIcon, CubeIcon, CheckCircledIcon } from '@radix-ui/react-icons'
import { Button } from '@/components/ui/button'
import { useState, useEffect } from 'react'

export default function Home() {
  const navigate = useNavigate()
  
  // Typing animation state
  const [typedText, setTypedText] = useState('')
  const fullCode = `from middleware.middleware import Dyno

app = FastAPI()
app.add_middleware(Dyno)`
  
  useEffect(() => {
    let currentIndex = 0
    const typingInterval = setInterval(() => {
      if (currentIndex <= fullCode.length) {
        setTypedText(fullCode.slice(0, currentIndex))
        currentIndex++
      } else {
        clearInterval(typingInterval)
      }
    }, 50) // Adjust speed here (lower = faster)
    
    return () => clearInterval(typingInterval)
  }, [])

  // Scroll animation observer
  useEffect(() => {
    const observerOptions = {
      threshold: 0.1,
      rootMargin: '0px 0px -100px 0px'
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add('fade-in-visible')
        } else {
          entry.target.classList.remove('fade-in-visible')
        }
      })
    }, observerOptions)

    const elements = document.querySelectorAll('.fade-in-scroll')
    elements.forEach((el) => observer.observe(el))

    return () => {
      elements.forEach((el) => observer.unobserve(el))
    }
  }, [])
  
  // Function to apply syntax highlighting
  const highlightCode = (code: string) => {
    const keywords = ['from', 'import']
    const classNames = ['Dyno', 'FastAPI']
    
    const tokens = []
    let currentToken = ''
    let inWord = false
    
    for (let i = 0; i < code.length; i++) {
      const char = code[i]
      
      if (/[a-zA-Z_]/.test(char) || (inWord && /[a-zA-Z0-9_.]/.test(char))) {
        currentToken += char
        inWord = true
      } else {
        if (currentToken) {
          // Determine color for the completed token
          let color = 'text-white'
          if (keywords.includes(currentToken)) {
            color = 'text-purple-400'
          } else if (classNames.includes(currentToken)) {
            color = 'text-yellow-300'
          }
          tokens.push({ text: currentToken, color })
          currentToken = ''
          inWord = false
        }
        
        // Handle special characters
        if (char === '=') {
          tokens.push({ text: char, color: 'text-pink-400' })
        } else if (char === '(' || char === ')') {
          tokens.push({ text: char, color: 'text-white' })
        } else {
          tokens.push({ text: char, color: 'text-white' })
        }
      }
    }
    
    // Handle remaining token
    if (currentToken) {
      let color = 'text-white'
      if (keywords.includes(currentToken)) {
        color = 'text-purple-400'
      } else if (classNames.includes(currentToken)) {
        color = 'text-yellow-300'
      }
      tokens.push({ text: currentToken, color })
    }
    
    return tokens
  }

  const features = [
    {
      icon: CheckCircledIcon,
      title: 'AI-Powered Security',
      description: 'Advanced threat detection using LLMs and specialized AI agents to protect your APIs'
    },
    {
      icon: LightningBoltIcon,
      title: 'Real-Time Mitigation',
      description: 'Automatic responses to threats with intelligent rate limiting, CAPTCHA, and blocking'
    },
    {
      icon: RocketIcon,
      title: 'Smart Analysis',
      description: 'Orchestrator agents route requests to specialized analyzers for authentication, search, and more'
    },
    {
      icon: CubeIcon,
      title: 'Adaptive Learning',
      description: 'RAG-powered calibration learns from past incidents to improve future threat detection'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-950 relative">

      {/* Complex Animated Background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        {/* Gradient meshes */}
        <div className="absolute inset-0 bg-gradient-to-br from-blue-950 via-gray-950 to-purple-950"></div>
        
        {/* Animated orbs */}
        <div className="absolute top-0 right-0 w-[800px] h-[800px] bg-blue-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '8s' }}></div>
        <div className="absolute bottom-0 left-0 w-[600px] h-[600px] bg-cyan-500/20 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '10s', animationDelay: '2s' }}></div>
        <div className="absolute top-1/2 left-1/2 w-[700px] h-[700px] bg-purple-500/10 rounded-full blur-3xl animate-pulse" style={{ animationDuration: '12s', animationDelay: '4s' }}></div>
        
        {/* Grid pattern */}
        <div className="absolute inset-0 bg-[linear-gradient(rgba(59,130,246,0.03)_1px,transparent_1px),linear-gradient(90deg,rgba(59,130,246,0.03)_1px,transparent_1px)] bg-[size:72px_72px]"></div>
        
      </div>

      {/* Navigation - Dark Glass Effect */}
      <nav className="bg-gray-900/95 backdrop-blur-xl border-b border-gray-700/50 shadow-lg fixed top-0 left-0 right-0 z-50 w-full">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/50">
                <span className="text-white text-xl font-bold">D</span>
              </div>
              <span className="text-2xl font-bold bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent tracking-tight">
                Dyno
              </span>
            </div>
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => navigate('/dashboard')}
                variant="outline"
                className="border-gray-600 text-black hover:border-blue-400 hover:text-blue-400 bg-white transition-all duration-300 hover:scale-105 hover:shadow-lg hover:shadow-blue-500/50"
              >
                Dashboard
              </Button>
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section - Side by Side */}
      <section className="max-w-7xl mx-auto px-4 lg:px-2 pt-24 pb-16 relative">
        <div className="grid lg:grid-cols-2 gap-36 items-center">
          {/* Left: Text Content */}
          <div className="space-y-8 fade-in-scroll">
            <div className="inline-flex items-center space-x-2 bg-blue-500/10 backdrop-blur-md text-blue-400 px-4 py-2 rounded-full border border-blue-500/30 transform -rotate-3 origin-left">
              <CheckCircledIcon className="w-4 h-4" />
              <span className="text-sm font-semibold tracking-wide uppercase ">AI-Powered API Security</span>
            </div>
            
            <h1 className="text-6xl font-bold text-white mb-6 leading-tight tracking-tight">
              Protect Your APIs with
              <br />
              <span className="bg-gradient-to-r from-blue-400 to-cyan-400 bg-clip-text text-transparent">
                Intelligent AI Agents
              </span>
            </h1>
            
            <p className="text-xl text-gray-400 leading-relaxed">
              Detect and mitigate malicious API behavior in real-time using advanced AI agents,
              LLMs, and adaptive learning. Stop brute force attacks, scraping, and abuse before they impact your service.
            </p>
            
            <div className="flex items-center space-x-4">
              <Button
                onClick={() => navigate('/dashboard')}
                size="lg"
                className="bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500 shadow-xl shadow-blue-500/50 hover:shadow-blue-500/70 text-lg px-8 py-6 transition-all duration-300 hover:scale-110"
              >
                <RocketIcon className="mr-2 h-5 w-5" />
                Try Dashboard
              </Button>
              <Button
                onClick={() => navigate('/search')}
                size="lg"
                variant="outline"
                className="text-lg px-8 py-6 border-2 border-gray-600 text-gray-300 hover:border-blue-400 hover:text-blue-400 bg-transparent transition-all duration-300 hover:scale-105"
              >
                View Demo
              </Button>
            </div>

            {/* Quick Stats - LED Style */}
            <div className="flex items-center space-x-6 pt-8 fade-in-scroll">
              <div className="relative group">
                <div className="absolute inset-0 bg-blue-500/20 rounded-lg blur-md group-hover:bg-blue-500/30 transition-all duration-300"></div>
                <div className="relative bg-gray-900/50 backdrop-blur-sm border-2 border-blue-500/50 rounded-lg px-6 py-3 shadow-lg shadow-blue-500/50 group-hover:border-blue-400 group-hover:shadow-blue-400/60 transition-all duration-300">
                  <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400 drop-shadow-[0_0_10px_rgba(59,130,246,0.5)]">5ms</div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Detection Time</div>
                </div>
              </div>
              <div className="relative group">
                <div className="absolute inset-0 bg-cyan-500/20 rounded-lg blur-md group-hover:bg-cyan-500/30 transition-all duration-300"></div>
                <div className="relative bg-gray-900/50 backdrop-blur-sm border-2 border-cyan-500/50 rounded-lg px-6 py-3 shadow-lg shadow-cyan-500/50 group-hover:border-cyan-400 group-hover:shadow-cyan-400/60 transition-all duration-300">
                  <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-400 drop-shadow-[0_0_10px_rgba(34,211,238,0.5)]">99.9%</div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Accuracy</div>
                </div>
              </div>
              <div className="relative group">
                <div className="absolute inset-0 bg-purple-500/20 rounded-lg blur-md group-hover:bg-purple-500/30 transition-all duration-300"></div>
                <div className="relative bg-gray-900/50 backdrop-blur-sm border-2 border-purple-500/50 rounded-lg px-6 py-3 shadow-lg shadow-purple-500/50 group-hover:border-purple-400 group-hover:shadow-purple-400/60 transition-all duration-300">
                  <div className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-400 to-pink-400 drop-shadow-[0_0_10px_rgba(168,85,247,0.5)]">24/7</div>
                  <div className="text-xs text-gray-400 uppercase tracking-wider">Protection</div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Terminal Window */}
          <div className="relative fade-in-scroll">
            <div className="absolute -inset-4 bg-gradient-to-r from-blue-500/20 to-cyan-500/20 rounded-3xl blur-2xl"></div>
            <div className="relative bg-gray-900/90 backdrop-blur-xl rounded-xl shadow-2xl overflow-hidden border border-gray-700/50 hover:border-blue-500/50 transition-all duration-500">
              {/* Terminal Header */}
              <div className="bg-gray-800/90 px-4 py-3 flex items-center justify-between border-b border-gray-700 relative">
                <div className="flex space-x-2 w-16">
                  <div className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-400 transition-colors cursor-pointer"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-400 transition-colors cursor-pointer"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-400 transition-colors cursor-pointer"></div>
                </div>
                <div className="absolute left-1/2 transform -translate-x-1/2">
                  <span className="text-sm text-gray-400 font-mono">main.py</span>
                </div>
                <div className="w-16"></div>
              </div>
              
              {/* Terminal Content */}
              <div className="p-6 font-mono text-sm h-[120px] overflow-hidden">
                <div className="whitespace-pre-wrap">
                  {highlightCode(typedText).map((token, index) => (
                    <span key={index} className={token.color}>
                      {token.text}
                    </span>
                  ))}
                  <span className="animate-pulse text-white">▊</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features - Asymmetric Grid */}
      <section className="max-w-7xl mx-auto px-6 py-16 relative">
        <div className="grid lg:grid-cols-3 gap-6">
          {/* Large Feature Card - Spans 2 rows */}
          <div className="lg:row-span-2 bg-gradient-to-br from-blue-600/90 to-cyan-600/90 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-blue-500/30 hover:scale-105 transition-all duration-500 group fade-in-scroll">
            <div className="h-full flex flex-col justify-between">
              <div>
                <div className="w-16 h-16 bg-white/20 rounded-2xl flex items-center justify-center mb-6 group-hover:scale-110 group-hover:rotate-6 transition-all duration-500">
                  <CheckCircledIcon className="w-8 h-8 text-white" />
                </div>
                <h3 className="text-3xl font-bold text-white mb-4">
                  {features[0].title}
                </h3>
                <p className="text-lg text-blue-100 leading-relaxed mb-6">
                  {features[0].description}
                </p>
              </div>
              <div className="space-y-3">
                <div className="flex items-center space-x-3 text-white/90">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  <span className="text-sm">Multi-Agent System</span>
                </div>
                <div className="flex items-center space-x-3 text-white/90">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  <span className="text-sm">LLM-Powered Analysis</span>
                </div>
                <div className="flex items-center space-x-3 text-white/90">
                  <div className="w-2 h-2 bg-white rounded-full"></div>
                  <span className="text-sm">Pattern Recognition</span>
                </div>
              </div>
            </div>
          </div>

          {/* Small Feature Cards */}
          {features.slice(1).map((feature, index) => {
            const IconComponent = feature.icon
            return (
              <div
                key={index}
                className="bg-gray-800/50 backdrop-blur-xl rounded-2xl p-6 shadow-xl border border-gray-700/50 hover:border-blue-500/50 cursor-pointer hover:scale-105 transition-all duration-500 group fade-in-scroll"
                style={{ animationDelay: `${index * 0.2}s` }}
              >
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center mb-4 shadow-lg shadow-blue-500/30 group-hover:shadow-blue-500/50 transition-all duration-300 group-hover:scale-110 group-hover:rotate-6">
                  <IconComponent className="w-6 h-6 text-white" />
                </div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {feature.title}
                </h3>
                <p className="text-sm text-gray-400 leading-relaxed">
                  {feature.description}
                </p>
              </div>
            )
          })}
        </div>
      </section>

      {/* Architecture Overview - Side by Side */}
      <section className="max-w-7xl mx-auto px-6 py-16 relative">
        <div className="grid lg:grid-cols-2 gap-16 items-center">
          {/* Left: Diagram/Visual */}
          <div className="relative fade-in-scroll">
            <div className="absolute inset-0 bg-gradient-to-br from-purple-500/10 to-pink-500/10 rounded-3xl blur-3xl"></div>
            <div className="relative space-y-6">
              <div className="text-left mb-8">
                <h2 className="text-4xl font-bold text-white mb-4 tracking-tight">
                  How It Works
                </h2>
                <p className="text-lg text-gray-400">
                  Multi-agent AI system for comprehensive API protection
                </p>
              </div>
              
              {/* Flow Diagram */}
              <div className="space-y-4">
                {/* Step 1 */}
                <div className="flex items-start space-x-4 group">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-purple-500 to-pink-500 rounded-xl flex items-center justify-center shadow-lg shadow-purple-500/30 group-hover:scale-110 transition-all duration-300">
                    <span className="text-white text-xl font-bold">1</span>
                  </div>
                  <div className="flex-1 bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50 group-hover:border-purple-500/50 transition-all duration-300">
                    <h4 className="text-lg font-semibold text-white mb-1">Orchestrator</h4>
                    <p className="text-sm text-gray-400">Routes requests to specialized agents by type</p>
                  </div>
                </div>
                
                {/* Connector */}
                <div className="ml-6 w-0.5 h-8 bg-gradient-to-b from-purple-500/50 to-blue-500/50"></div>
                
                {/* Step 2 */}
                <div className="flex items-start space-x-4 group">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-xl flex items-center justify-center shadow-lg shadow-blue-500/30 group-hover:scale-110 transition-all duration-300">
                    <span className="text-white text-xl font-bold">2</span>
                  </div>
                  <div className="flex-1 bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50 group-hover:border-blue-500/50 transition-all duration-300">
                    <h4 className="text-lg font-semibold text-white mb-1">Specialists</h4>
                    <p className="text-sm text-gray-400">LLM-powered analysis with Elasticsearch access</p>
                  </div>
                </div>
                
                {/* Connector */}
                <div className="ml-6 w-0.5 h-8 bg-gradient-to-b from-blue-500/50 to-green-500/50"></div>
                
                {/* Step 3 */}
                <div className="flex items-start space-x-4 group">
                  <div className="flex-shrink-0 w-12 h-12 bg-gradient-to-br from-green-500 to-emerald-500 rounded-xl flex items-center justify-center shadow-lg shadow-green-500/30 group-hover:scale-110 transition-all duration-300">
                    <span className="text-white text-xl font-bold">3</span>
                  </div>
                  <div className="flex-1 bg-gray-800/50 backdrop-blur-xl rounded-xl p-4 border border-gray-700/50 group-hover:border-green-500/50 transition-all duration-300">
                    <h4 className="text-lg font-semibold text-white mb-1">Calibration</h4>
                    <p className="text-sm text-gray-400">RAG-based learning from past mitigations</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right: Benefits List */}
          <div className="space-y-6 fade-in-scroll">
            <div className="bg-gray-800/30 backdrop-blur-xl rounded-2xl p-8 border border-gray-700/50 hover:border-blue-500/50 transition-all duration-500">
              <h3 className="text-2xl font-bold text-white mb-6">Why Choose Dyno?</h3>
              <div className="space-y-4">
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-500/20 rounded-lg flex items-center justify-center mt-1">
                    <CheckCircledIcon className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Zero False Positives</h4>
                    <p className="text-sm text-gray-400">AI learns your traffic patterns to avoid blocking legitimate users</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-500/20 rounded-lg flex items-center justify-center mt-1">
                    <CheckCircledIcon className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Adaptive Mitigation</h4>
                    <p className="text-sm text-gray-400">Escalating responses from delays to CAPTCHAs to blocks</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-500/20 rounded-lg flex items-center justify-center mt-1">
                    <CheckCircledIcon className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Real-Time Analysis</h4>
                    <p className="text-sm text-gray-400">Sub-millisecond detection with batched AI processing</p>
                  </div>
                </div>
                <div className="flex items-start space-x-3">
                  <div className="w-6 h-6 bg-blue-500/20 rounded-lg flex items-center justify-center mt-1">
                    <CheckCircledIcon className="w-4 h-4 text-blue-400" />
                  </div>
                  <div>
                    <h4 className="text-white font-semibold mb-1">Continuous Learning</h4>
                    <p className="text-sm text-gray-400">RAG memory improves detection accuracy over time</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="max-w-7xl mx-auto px-6 py-16 pb-8 relative">
        <div className="relative fade-in-scroll">
          {/* Glowing background */}
          <div className="absolute inset-0 bg-gradient-to-r from-blue-600/30 to-cyan-600/30 rounded-3xl blur-3xl"></div>
          
          {/* Glass card */}
          <div className="relative bg-white/5 backdrop-blur-2xl rounded-3xl p-16 text-center shadow-2xl border border-white/10 hover:border-white/20 transition-all duration-500 overflow-hidden group">
            {/* Subtle gradient overlay */}
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/10 via-transparent to-cyan-500/10 rounded-3xl"></div>
            
            <div className="relative z-10">
              <h2 className="text-5xl font-bold text-white mb-6 tracking-tight drop-shadow-lg">
                Ready to Secure Your APIs?
              </h2>
              <p className="text-xl text-gray-200 mb-10 max-w-2xl mx-auto">
                Join developers protecting their applications with intelligent AI-powered security
              </p>
              <div className="flex items-center justify-center space-x-4">
                <Button
                  onClick={() => navigate('/dashboard')}
                  size="lg"
                  className="bg-white text-black hover:bg-gray-50 shadow-2xl shadow-blue-500/30 hover:shadow-blue-500/50 text-lg px-10 py-7 transition-all duration-300 hover:scale-110 font-semibold"
                >
                  <RocketIcon className="mr-2 h-5 w-5" />
                  Get Started Now
                </Button>
                <Button
                  onClick={() => navigate('/login')}
                  size="lg"
                  variant="outline"
                  className="text-black border-2 border-white/50 hover:border-white shadow-2xl shadow-blue-500/30 hover:shadow-blue-500/50 backdrop-blur-sm text-lg px-10 py-7 transition-all duration-300 hover:scale-105"
                >
                  Sign In
                </Button>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Footer - Dark Glass Effect */}
      <footer className="border-t border-gray-800 bg-gray-900/95 backdrop-blur-xl relative mt-16 z-40">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-8 h-8 bg-gradient-to-br from-blue-500 to-cyan-500 rounded-lg flex items-center justify-center shadow-lg shadow-blue-500/30">
                <span className="text-white font-bold">D</span>
              </div>
              <span className="text-lg font-bold text-white tracking-tight">Dyno</span>
            </div>
            <div className="text-sm text-gray-400">
              © 2025 Dyno. Powered by AI & LLMs.
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
