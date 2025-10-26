/**
 * WebSocket Hook - Universal State Management
 * Connects to backend WebSocket and provides live Elasticsearch data
 * to all components across the application
 */

import { useState, useEffect, useRef, createContext, useContext, ReactNode } from 'react';

// Types for WebSocket messages
interface RequestData {
  method: string;
  path: string;
  response_status: number;
  response_success: boolean;
  client_ip: string;
  username?: string;
  user?: string;
  timestamp: string;
  processing_time_ms: number;
  user_agent?: string;
  body_json?: any;
  full_url?: string;
}

interface StatsData {
  total_requests: number;
  unique_ips: number;
  unique_users: number;
  failed_requests: number;
  avg_response_time_ms: number;
  status_codes: Array<{ code: number; count: number }>;
  top_endpoints: Array<{ endpoint: string; count: number }>;
  top_ips: Array<{ ip: string; count: number }>;
  top_failed_usernames: Array<{ username: string; failed_attempts: number }>;
  http_methods: Array<{ method: string; count: number }>;
  timestamp: string;
}

interface AlertData {
  type: 'brute_force' | 'credential_stuffing' | 'high_request_rate' | 'suspicious_activity';
  message: string;
  ip_address?: string;
  username?: string;
  failed_attempts?: number;
  unique_usernames_tried?: number;
  unique_ips?: number;
  ip_addresses?: string[];
  request_count?: number;
  severity: 'critical' | 'high' | 'medium';
  timestamp: string;
  recommendation: string;
}

interface WebSocketContextType {
  // Live data
  requests: RequestData[];
  stats: StatsData | null;
  alerts: AlertData[];
  
  // Connection status
  isConnected: boolean;
  connectionId: number | null;
  
  // Helper methods
  clearRequests: () => void;
  clearAlerts: () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export function WebSocketProvider({ children }: WebSocketProviderProps) {
  const [requests, setRequests] = useState<RequestData[]>([]);
  const [stats, setStats] = useState<StatsData | null>(null);
  const [alerts, setAlerts] = useState<AlertData[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionId, setConnectionId] = useState<number | null>(null);
  
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<NodeJS.Timeout>();

  const connect = () => {
    try {
      // Connect to WebSocket
      ws.current = new WebSocket('ws://localhost:8000/ws/elasticsearch');

      ws.current.onopen = () => {
        console.log('✅ WebSocket connected');
        setIsConnected(true);
      };

      ws.current.onmessage = (event) => {
        const message = JSON.parse(event.data);

        switch (message.type) {
          case 'connection':
            // Initial connection message
            setConnectionId(message.connection_id);
            console.log('🔗 Connected to Elasticsearch live feed');
            break;

          case 'initial_data':
            // Initial batch of last 100 logs on connection
            console.log(`📥 Received ${message.count} initial logs`);
            setRequests(message.data || []);
            break;

          case 'new_request':
            // Real-time request from middleware - add to top
            setRequests((prev) => [message.data, ...prev].slice(0, 200));
            break;

          case 'stats':
            // Stats update (every 30s)
            setStats(message.stats);
            break;

          case 'alert':
            // Security alert - keep last 50 alerts
            setAlerts((prev) => [message.alert, ...prev].slice(0, 50));
            
            // Show browser notification for critical alerts
            if (message.severity === 'critical' && 'Notification' in window) {
              if (Notification.permission === 'granted') {
                new Notification('🚨 Security Alert', {
                  body: message.alert.message,
                  icon: '/alert-icon.png',
                });
              }
            }
            break;

          default:
            console.log('Unknown message type:', message.type);
        }
      };

      ws.current.onclose = () => {
        console.log('❌ WebSocket disconnected');
        setIsConnected(false);
        
        // Attempt to reconnect after 3 seconds
        reconnectTimeout.current = setTimeout(() => {
          console.log('🔄 Attempting to reconnect...');
          connect();
        }, 3000);
      };

      ws.current.onerror = (error) => {
        console.error('WebSocket error:', error);
      };
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
    }
  };

  useEffect(() => {
    // Request notification permission
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission();
    }

    // Connect on mount
    connect();

    // Cleanup on unmount
    return () => {
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
      }
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const clearRequests = () => setRequests([]);
  const clearAlerts = () => setAlerts([]);

  const value: WebSocketContextType = {
    requests,
    stats,
    alerts,
    isConnected,
    connectionId,
    clearRequests,
    clearAlerts,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

// Custom hook to use WebSocket data
export function useWebSocket() {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
}

// Helper hooks for specific data
export function useRequests() {
  const { requests } = useWebSocket();
  return requests;
}

export function useStats() {
  const { stats } = useWebSocket();
  return stats;
}

export function useAlerts() {
  const { alerts } = useWebSocket();
  return alerts;
}

export function useConnectionStatus() {
  const { isConnected, connectionId } = useWebSocket();
  return { isConnected, connectionId };
}