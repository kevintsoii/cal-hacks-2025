import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import Navbar from '@/components/Navbar'

interface SearchResult {
  username: string
  status: string
  details: string
}

export default function UserSearch() {
  const [yourUsername, setYourUsername] = useState('')
  const [usernamesList, setUsernamesList] = useState('')
  const [results, setResults] = useState<SearchResult[]>([])
  const [errorMessage, setErrorMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault()
    setErrorMessage('')
    setIsLoading(true)
    
    // Split usernames by newline and filter out empty strings
    const usernames = usernamesList
      .split('\n')
      .map(name => name.trim())
      .filter(name => name.length > 0)
    
    if (usernames.length === 0) {
      setErrorMessage('Please enter at least one username to search')
      setResults([])
      setIsLoading(false)
      return
    }

    try {
      const response = await fetch('http://localhost:8000/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          yourUsername: yourUsername || undefined, 
          usernames 
        }),
      })

      const data = await response.json()

      if (data.error) {
        setErrorMessage(data.error)
        setResults([])
      } else if (data.success && data.results) {
        setResults(data.results)
        setErrorMessage('')
      }
    } catch (error) {
      setErrorMessage('Failed to connect to the server. Please try again.')
      setResults([])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <Navbar />
      
      {/* Background decorations */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="absolute top-20 left-10 w-72 h-72 bg-indigo-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <div className="flex gap-6 px-6 pt-30 pb-6 px-40" style={{ height: 'calc(100vh - 4rem)' }}>
        {/* Left Side - Search Form */}
        <div className="w-1/3 flex flex-col">
          <div className="flex-1 p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 overflow-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                User Search
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                Search for users by entering their usernames below
              </p>
            </div>
            <form className="space-y-4" onSubmit={handleSearch}>
              <div className="space-y-4">
                <div>
                  <label htmlFor="yourUsername" className="block text-sm font-medium text-gray-700 mb-1">
                    Your Username <span className="text-gray-400 font-normal">(optional)</span>
                  </label>
                  <Input
                    id="yourUsername"
                    name="yourUsername"
                    type="text"
                    value={yourUsername}
                    onChange={(e) => setYourUsername(e.target.value)}
                    placeholder="Enter your username"
                    className="w-full"
                  />
                </div>
                <div>
                  <label htmlFor="usernamesList" className="block text-sm font-medium text-gray-700 mb-1">
                    Usernames to Search
                  </label>
                  <Textarea
                    id="usernamesList"
                    name="usernamesList"
                    value={usernamesList}
                    onChange={(e) => setUsernamesList(e.target.value)}
                    placeholder="Enter usernames (one per line)&#10;Example:&#10;john_doe&#10;jane_smith&#10;bob_jones"
                    className="w-full min-h-[300px] font-mono text-sm"
                    rows={12}
                  />
                </div>
              </div>

              <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700" disabled={isLoading}>
                {isLoading ? 'Searching...' : 'Search Users'}
              </Button>
            </form>
          </div>
        </div>

        {/* Right Side - Results Table */}
        <div className="flex-1 flex flex-col">
          <div className="flex-1 p-6 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100 overflow-auto">
            <div className="mb-6">
              <h2 className="text-2xl font-bold text-gray-900">
                Results
              </h2>
              <p className="mt-2 text-sm text-gray-600">
                User search results will appear here
              </p>
            </div>
            
            {errorMessage && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4 mb-4">
                <p className="text-sm text-red-800">{errorMessage}</p>
              </div>
            )}

            <div className="border rounded-lg">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Details</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {results.length === 0 ? (
                    <TableRow>
                      <TableCell colSpan={3} className="text-center text-gray-500 py-8">
                        No results yet. Submit a search to see results.
                      </TableCell>
                    </TableRow>
                  ) : (
                    results.map((result, index) => (
                      <TableRow key={index}>
                        <TableCell className="font-medium">{result.username}</TableCell>
                        <TableCell>
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            result.status === 'Active' ? 'bg-green-100 text-green-800' :
                            result.status === 'Inactive' ? 'bg-gray-100 text-gray-800' :
                            result.status === 'Pending' ? 'bg-yellow-100 text-yellow-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {result.status}
                          </span>
                        </TableCell>
                        <TableCell className="text-gray-600">{result.details}</TableCell>
                      </TableRow>
                    ))
                  )}
                </TableBody>
              </Table>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}