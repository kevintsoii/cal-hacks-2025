/**
 * Activity Data Hook - Global State Management
 * Fetches and provides activity data (hourly trends) to all components
 */

import { useState, useEffect, createContext, useContext, ReactNode } from 'react';

// Types for activity data
export interface HourlyData {
  hour: number;
  requests: number;
  failed: number;
  avg_response_time: number;
}

export interface DayData {
  date: string;
  day_of_week: string;
  day_of_month: number;
  hourly_data: HourlyData[];
  total_requests: number;
}

export interface ActivityData {
  days: DayData[];
  start_date: string;
  end_date: string;
  timestamp: string;
}

interface ActivityDataContextType {
  activityData: ActivityData | null;
  weeklyData: any | null;
  monthlyData: any | null;
  loading: boolean;
  error: string | null;
  refetch: (interval?: 'hour' | 'day' | 'week') => Promise<void>;
}

const ActivityDataContext = createContext<ActivityDataContextType | undefined>(undefined);

interface ActivityDataProviderProps {
  children: ReactNode;
}

export function ActivityDataProvider({ children }: ActivityDataProviderProps) {
  const [activityData, setActivityData] = useState<ActivityData | null>(null); // Hourly/Daily
  const [weeklyData, setWeeklyData] = useState<any | null>(null); // Weekly for Weeks view
  const [monthlyData, setMonthlyData] = useState<any | null>(null); // Weekly for Months view
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchActivityData = async (interval: 'hour' | 'day' | 'week' = 'hour') => {
    try {
      setError(null);
      
      let url = '';
      if (interval === 'hour') {
        // Last 14 days for Days view (hourly data)
        url = 'http://localhost:8000/elastic/activity?days=14&interval=hour';
      } else if (interval === 'day') {
        // Last 28 days for Weeks view (daily data)
        url = 'http://localhost:8000/elastic/activity?days=28&interval=day';
      } else {
        // Last 90 days for Months view (weekly data)
        url = 'http://localhost:8000/elastic/activity?days=90&interval=week';
      }
      
      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (interval === 'hour') {
        setActivityData(data);
        console.log('✅ Hourly activity data loaded:', data.days?.length || 0, 'days');
      } else if (interval === 'day') {
        setWeeklyData(data);
        console.log('✅ Daily activity data loaded:', data.data?.length || 0, 'days');
      } else {
        setMonthlyData(data);
        console.log('✅ Weekly activity data loaded:', data.data?.length || 0, 'weeks');
      }
      
      setLoading(false);
    } catch (err) {
      console.error('❌ Error fetching activity data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch activity data');
      setLoading(false);
    }
  };

  useEffect(() => {
    // Fetch all data on mount
    const loadAllData = async () => {
      await fetchActivityData('hour');
      await fetchActivityData('day');
      await fetchActivityData('week');
    };
    
    loadAllData();

    // Refresh every 2 minutes (less frequent than WebSocket, for trend data)
    const interval = setInterval(() => loadAllData(), 120000);
    
    return () => clearInterval(interval);
  }, []);

  const value: ActivityDataContextType = {
    activityData,
    weeklyData,
    monthlyData,
    loading,
    error,
    refetch: fetchActivityData,
  };

  return (
    <ActivityDataContext.Provider value={value}>
      {children}
    </ActivityDataContext.Provider>
  );
}

// Custom hook to use activity data
export function useActivityData() {
  const context = useContext(ActivityDataContext);
  if (context === undefined) {
    throw new Error('useActivityData must be used within an ActivityDataProvider');
  }
  return context;
}

// Helper hook to get today's data
export function useTodayActivity() {
  const { activityData, loading, error } = useActivityData();
  
  const todayData = activityData?.days && activityData.days.length > 0 
    ? activityData.days[activityData.days.length - 1] 
    : null;

  return { todayData, loading, error };
}

