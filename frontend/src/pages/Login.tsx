import { useState, useRef } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import StartupNavbar from '@/components/StartupNavbar'
import ReCAPTCHA from 'react-google-recaptcha'

const RECAPTCHA_SITE_KEY = '6Ldp_vMrAAAAAAftWfJS8c5SuYqzyZP6TpytO6tq'

export default function Login() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [showCaptcha, setShowCaptcha] = useState(false)
  const [captchaToken, setCaptchaToken] = useState<string | null>(null)
  const recaptchaRef = useRef<ReCAPTCHA>(null)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const requestBody: any = { username, password }
      if (captchaToken) {
        requestBody.captcha_token = captchaToken
      }

      const response = await fetch('http://localhost:8000/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      })

      const data = await response.json()

      if (data.error) {
        setErrorMessage(data.error)
        setSuccessMessage('')
        
        // Check if error requires captcha
        if (data.error.toLowerCase().includes('captcha required') || 
            data.error.toLowerCase().includes('captcha verification failed')) {
          setShowCaptcha(true)
        }
      } else if (data.success) {
        setSuccessMessage(data.message || 'Login successful!')
        // Optional: Clear the form
        setPassword('')
        setErrorMessage('')
        setShowCaptcha(false)
      }
    } catch (error) {
      setErrorMessage('Failed to connect to the server. Please try again.')
      setSuccessMessage('')
    } finally {
      // Always reset captcha on every request
      setCaptchaToken(null)
      if (recaptchaRef.current) {
        recaptchaRef.current.reset()
      }
      setIsLoading(false)
    }
  }

  const onCaptchaChange = (token: string | null) => {
    setCaptchaToken(token)
  }

  return (
    <div className="min-h-screen relative overflow-hidden">
      <StartupNavbar />
      
      {/* Background decorations */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-indigo-50 via-white to-purple-50">
        <div className="absolute top-20 left-10 w-72 h-72 bg-indigo-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob"></div>
        <div className="absolute top-40 right-10 w-72 h-72 bg-purple-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-2000"></div>
        <div className="absolute -bottom-8 left-1/2 w-72 h-72 bg-pink-200 rounded-full mix-blend-multiply filter blur-xl opacity-70 animate-blob animation-delay-4000"></div>
      </div>

      <div className="min-h-screen flex items-center justify-center pt-16 px-4">
        <div className="max-w-md w-full space-y-8 p-8 bg-white/80 backdrop-blur-sm rounded-2xl shadow-xl border border-gray-100">
          <div>
            <h2 className="text-center text-3xl font-bold text-gray-900">
              Welcome back
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Sign in to your account to continue
            </p>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleLogin}>
            <div className="space-y-4">
              <div>
                <label htmlFor="username" className="block text-sm font-medium text-gray-700 mb-1">
                  Username
                </label>
                <Input
                  id="username"
                  name="username"
                  type="text"
                  required
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="w-full"
                />
              </div>
              <div>
                <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                  Password
                </label>
                <Input
                  id="password"
                  name="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="w-full"
                />
              </div>
            </div>

            {errorMessage && (
              <div className="rounded-lg bg-red-50 border border-red-200 p-4">
                <p className="text-sm text-red-800">{errorMessage}</p>
              </div>
            )}
            
            {successMessage && (
              <div className="rounded-lg bg-green-50 border border-green-200 p-4">
                <p className="text-sm text-green-800">{successMessage}</p>
              </div>
            )}

            {showCaptcha && (
              <div className="flex justify-center">
                <ReCAPTCHA
                  ref={recaptchaRef}
                  sitekey={RECAPTCHA_SITE_KEY}
                  onChange={onCaptchaChange}
                />
              </div>
            )}

            <Button type="submit" className="w-full bg-indigo-600 hover:bg-indigo-700" disabled={isLoading || (showCaptcha && !captchaToken)}>
              {isLoading ? 'Signing in...' : 'Sign in'}
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}