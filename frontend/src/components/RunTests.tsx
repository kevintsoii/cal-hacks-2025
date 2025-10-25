import { Button } from '@/components/ui/button'
import { PlayIcon, CrossCircledIcon } from '@radix-ui/react-icons'
import { useEffect, useRef } from 'react'
import type { MutableRefObject } from 'react'

export type RunTestsTestType = 'Authentication' | 'Search'

interface Test {
  id: string
  name: string
  description: string
}

const authTests: Test[] = [
  {
    id: 'admin-100',
    name: 'Brute Force Attack',
    description: 'Login to "admin" 100x (Different IPs)'
  },
  {
    id: 'admin-1000',
    name: 'Large Brute Force Attack',
    description: 'Login to "admin" 1,000x (Different IPs)'
  },
  {
    id: 'credential-stuffing',
    name: 'Credential Stuffing Attack',
    description: 'Login to 100 different accounts (Same IP)'
  }
]

const searchTests: Test[] = [
  {
    id: 'admin-search',
    name: 'Admin Search Abuse',
    description: 'Search on "admin" 200x'
  },
  {
    id: 'scraping-pattern',
    name: 'Scraping Pattern',
    description: 'Search user IDs 1 -> 1000'
  },
  {
    id: 'sql-injection',
    name: 'SQL Injection',
    description: 'Attempt 50 SQL injection queries'
  }
]

export interface RunTestsLogEntry {
  timestamp: string
  message: string
  type: 'info' | 'warning' | 'error' | 'success'
}

interface RunTestsProps {
  activeTab: RunTestsTestType
  setActiveTab: (tab: RunTestsTestType) => void
  runningTests: Set<string>
  setRunningTests: (tests: Set<string> | ((prev: Set<string>) => Set<string>)) => void
  progress: number
  setProgress: (progress: number | ((prev: number) => number)) => void
  logs: RunTestsLogEntry[]
  setLogs: (logs: RunTestsLogEntry[] | ((prev: RunTestsLogEntry[]) => RunTestsLogEntry[])) => void
  completedCount: number
  setCompletedCount: (count: number | ((prev: number) => number)) => void
  currentRequest: number
  setCurrentRequest: (request: number | ((prev: number) => number)) => void
  totalRequests: number
  setTotalRequests: (total: number | ((prev: number) => number)) => void
  wsRef: MutableRefObject<WebSocket | null>
}

export default function RunTests({
  activeTab,
  setActiveTab,
  runningTests,
  setRunningTests,
  progress,
  setProgress,
  logs,
  setLogs,
  completedCount,
  setCompletedCount,
  currentRequest,
  setCurrentRequest,
  totalRequests,
  setTotalRequests,
  wsRef
}: RunTestsProps) {
  const logsEndRef = useRef<HTMLDivElement>(null)

  const tests = activeTab === 'Authentication' ? authTests : searchTests

  // Auto-scroll to bottom when new logs are added
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [logs])

  const handleAbortTest = (testId: string) => {
    if (wsRef.current) {
      setLogs(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        message: 'Test aborted by user',
        type: 'error'
      }])
      
      // Send explicit abort message to backend before closing
      try {
        wsRef.current.send(JSON.stringify({ type: 'abort' }))
      } catch (e) {
        console.error('Failed to send abort message:', e)
      }
      
      // Close the WebSocket connection
      wsRef.current.close()
      wsRef.current = null
      
      // Immediately remove from running tests
      setRunningTests(prev => {
        const newSet = new Set(prev)
        newSet.delete(testId)
        return newSet
      })
    }
  }

  const handleRunTest = async (testId: string, testName: string) => {
    setRunningTests(prev => new Set(prev).add(testId))
    setProgress(0) // Reset progress for new test
    setLogs([]) // Clear previous logs
    setCurrentRequest(0) // Reset current request
    setTotalRequests(0) // Reset total requests
    
    // Add log entry
    const timestamp = new Date().toLocaleTimeString()
    setLogs(prev => [...prev, {
      timestamp,
      message: `Starting test: ${testName}`,
      type: 'info'
    }])

    try {
      // Connect to WebSocket which will automatically start the test
      const ws = new WebSocket(`ws://localhost:8000/ws/test/${testId}`)
      wsRef.current = ws
      
      ws.onopen = () => {
        // setLogs(prev => [...prev, {
        //   timestamp: new Date().toLocaleTimeString(),
        //   message: 'Connected to test WebSocket',
        //   type: 'info'
        // }])
      }

      ws.onmessage = (event) => {
        const message = JSON.parse(event.data)
        
        switch (message.type) {
          case 'connected':
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: message.message,
              type: 'info'
            }])
            break
            
          case 'started':
            setTotalRequests(message.total)
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: `${message.message} (Total: ${message.total} requests)`,
              type: 'info'
            }])
            break
            
          case 'progress':
            // Update progress bar
            const progressPercent = Math.round((message.request_num / message.total) * 100)
            setProgress(progressPercent)
            setCurrentRequest(message.request_num)
            setTotalRequests(message.total)
            
            // Add detailed log for each request
            const statusMessage = `Request ${message.request_num}/${message.total}: Status ${message.status_code} from IP ${message.ip}`
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: statusMessage,
              type: message.status_code === 200 ? 'success' : (message.status_code === 401 ? 'warning' : 'error')
            }])
            break
            
          case 'summary':
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: `Test Summary: ${message.total} total requests, ${message.successful} successful, ${message.failed} failed`,
              type: 'success'
            }])
            break
            
          case 'completed':
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: 'Test execution completed',
              type: 'success'
            }])
            setCompletedCount(prev => prev + 1)
            ws.close()
            break
            
          case 'error':
            setLogs(prev => [...prev, {
              timestamp: new Date().toLocaleTimeString(),
              message: `Error: ${message.message}`,
              type: 'error'
            }])
            ws.close()
            break
        }
      }

      ws.onerror = () => {
        setLogs(prev => [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          message: 'WebSocket error occurred',
          type: 'error'
        }])
      }

      ws.onclose = () => {
        setLogs(prev => [...prev, {
          timestamp: new Date().toLocaleTimeString(),
          message: 'WebSocket connection closed',
          type: 'info'
        }])
        
        // Remove from running tests
        setRunningTests(prev => {
          const newSet = new Set(prev)
          newSet.delete(testId)
          return newSet
        })
        
        // Clear WebSocket reference
        wsRef.current = null
      }

    } catch (error) {
      setLogs(prev => [...prev, {
        timestamp: new Date().toLocaleTimeString(),
        message: `Failed to start test: ${error instanceof Error ? error.message : 'Unknown error'}`,
        type: 'error'
      }])
      
      setRunningTests(prev => {
        const newSet = new Set(prev)
        newSet.delete(testId)
        return newSet
      })
    }
  }

  const getLogColor = (type: RunTestsLogEntry['type']) => {
    switch (type) {
      case 'info':
        return 'text-blue-700 bg-blue-50 border-blue-200'
      case 'warning':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200'
      case 'error':
        return 'text-red-700 bg-red-50 border-red-200'
      case 'success':
        return 'text-green-700 bg-green-50 border-green-200'
    }
  }

  return (
    <div className="space-y-6">
      {/* Tab Selection */}
      <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg w-fit">
        <button
          onClick={() => setActiveTab('Authentication')}
          className={`px-6 py-2.5 rounded-md text-sm font-semibold transition-all ${
            activeTab === 'Authentication'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Authentication
        </button>
        <button
          onClick={() => setActiveTab('Search')}
          className={`px-6 py-2.5 rounded-md text-sm font-semibold transition-all ${
            activeTab === 'Search'
              ? 'bg-white text-blue-600 shadow-sm'
              : 'text-gray-600 hover:text-gray-900'
          }`}
        >
          Search
        </button>
      </div>

      {/* Divider */}
      <div className="border-t border-gray-200" />

      {/* Test Cards */}
      <div className="grid grid-cols-4 gap-4">
        {tests.map((test) => (
          <div
            key={test.id}
            className="bg-white rounded-lg border border-gray-200 p-5 hover:shadow-lg transition-shadow"
          >
            <h3 className="font-semibold text-gray-900 mb-2">{test.name}</h3>
            <p className="text-sm text-gray-600 mb-4 line-clamp-2">{test.description}</p>
            {runningTests.has(test.id) ? (
              <Button
                onClick={() => handleAbortTest(test.id)}
                variant="destructive"
                className="w-full bg-red-600 hover:bg-red-700"
              >
                <CrossCircledIcon className="mr-2 h-4 w-4" />
                Abort Test
              </Button>
            ) : (
              <Button
                onClick={() => handleRunTest(test.id, test.name)}
                disabled={runningTests.size > 0}
                className="w-full bg-gradient-to-r from-blue-600 to-cyan-600 hover:from-blue-500 hover:to-cyan-500"
              >
                <PlayIcon className="mr-2 h-4 w-4" />
                Run Test
              </Button>
            )}
          </div>
        ))}
      </div>

      {/* Split View: Progress & Logs */}
      <div className="grid grid-cols-2 gap-6">
        {/* Left: Progress Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 h-[500px] flex flex-col">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Test Progress</h3>
          
          {/* Progress Bar */}
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                {totalRequests > 0 ? `Request ${currentRequest} of ${totalRequests}` : 'Overall Completion'}
              </span>
              <span className="text-sm font-semibold text-blue-600">{progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
              <div
                className="bg-gradient-to-r from-blue-600 to-cyan-600 h-3 rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          {/* Statistics */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gradient-to-br from-blue-50 to-cyan-50 rounded-lg p-4 border border-blue-100">
              <div className="text-2xl font-bold text-blue-600">{completedCount}</div>
              <div className="text-sm text-gray-600 mt-1">Tests Completed</div>
            </div>
            <div className="bg-gradient-to-br from-purple-50 to-pink-50 rounded-lg p-4 border border-purple-100">
              <div className="text-2xl font-bold text-purple-600">{runningTests.size}</div>
              <div className="text-sm text-gray-600 mt-1">Tests Running</div>
            </div>
          </div>

          {/* Chart Placeholder */}
          <div className="mt-6 pt-6 border-t border-gray-200 flex-1 flex flex-col min-h-0">
            <h4 className="text-sm font-semibold text-gray-700 mb-3 flex-shrink-0">Activity Timeline</h4>
            <div className="flex-1 bg-gradient-to-br from-gray-50 to-gray-100 rounded-lg flex items-center justify-center border border-gray-200 min-h-0">
              <span className="text-sm text-gray-500">Chart visualization coming soon</span>
            </div>
          </div>
        </div>

        {/* Right: Logs Section */}
        <div className="bg-white rounded-lg border border-gray-200 p-6 h-[500px] flex flex-col">
          <div className="flex items-center justify-between mb-4 flex-shrink-0">
            <h3 className="text-lg font-semibold text-gray-900">Test Logs</h3>
            {logs.length > 0 && (
              <button
                onClick={() => setLogs([])}
                className="text-xs text-gray-500 hover:text-gray-700 font-medium"
              >
                Clear Logs
              </button>
            )}
          </div>
          
          <div className="space-y-2 flex-1 overflow-y-auto min-h-0">
            {logs.length === 0 ? (
              <div className="text-center py-12 text-gray-500 text-sm">
                No logs yet. Run a test to see activity.
              </div>
            ) : (
              <>
                {logs.map((log, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded-lg border text-sm ${getLogColor(log.type)}`}
                  >
                    <div className="flex items-start justify-between">
                      <span className="font-mono text-xs opacity-75">{log.timestamp}</span>
                    </div>
                    <div className="mt-1 font-medium">{log.message}</div>
                  </div>
                ))}
                <div ref={logsEndRef} />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
