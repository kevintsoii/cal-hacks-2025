"use client";

import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { useActivityData } from "@/hooks/useActivityData";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

type TimeFrame = 'Days' | 'Weeks' | 'Months';

export default function ActivityChart() {
  const { activityData, weeklyData, monthlyData, loading } = useActivityData();
  const [selectedButtonIndex, setSelectedButtonIndex] = useState<number | null>(null); // Track which button is clicked
  const [timeFrame, setTimeFrame] = useState<TimeFrame>('Days');

  // Get the appropriate data based on time frame
  const getCurrentData = () => {
    if (timeFrame === 'Days') {
      // Determine which button is selected
      const buttonIndex = selectedButtonIndex !== null ? selectedButtonIndex : recentDays.length - 1;
      const selectedButton = recentDays[buttonIndex];
      
      if (!selectedButton) {
        // Fallback: return empty 24 hours
        return Array.from({ length: 24 }, (_, i) => ({
          time: `${i.toString().padStart(2, '0')}:00`,
          Requests: 0,
          Threats: 0,
        }));
      }

      // If this day has data, use it
      if (selectedButton.dataIndex !== null && activityData?.days?.[selectedButton.dataIndex]) {
        const selectedDay = activityData.days[selectedButton.dataIndex];
        const hourMap = new Map(selectedDay.hourly_data.map(h => [h.hour, h]));
        
        return Array.from({ length: 24 }, (_, hour) => {
          const data = hourMap.get(hour);
          return {
            time: `${hour.toString().padStart(2, '0')}:00`,
            Requests: data?.requests || 0,
            Threats: data?.failed || 0,
          };
        });
      }

      // Day has no data - return empty 24 hours
      return Array.from({ length: 24 }, (_, i) => ({
        time: `${i.toString().padStart(2, '0')}:00`,
        Requests: 0,
        Threats: 0,
      }));
    } else if (timeFrame === 'Weeks') {
      // Daily view - last 28 days
      if (!weeklyData?.data) return [];
      
      return weeklyData.data.map((d: any) => ({
        time: `${d.day_of_week} ${d.day_of_month}`,
        Requests: d.requests,
        Threats: d.failed,
      }));
    } else {
      // Weekly view - last 90 days grouped by week, show month names
      if (!monthlyData?.data) return [];
      
      return monthlyData.data.map((d: any) => {
        const weekDate = new Date(d.week_start);
        const monthName = weekDate.toLocaleDateString('en-US', { month: 'long' });
        
        return {
          time: monthName,
          Requests: d.requests,
          Threats: d.failed,
        };
      });
    }
  };

  // Generate days for selector - enough to fill the width
  const generateDayButtons = () => {
    const days = [];
    const today = new Date();
    
    // Show last 21 days (3 weeks) to fill the width
    const daysToShow = 21;
    
    // Go back from today
    for (let i = daysToShow - 1; i >= 0; i--) {
      const date = new Date(today);
      date.setDate(date.getDate() - i);
      
      const dateStr = date.toISOString().split('T')[0];
      
      // Check if this date has data
      const dayIndex = activityData?.days?.findIndex(d => d.date === dateStr);
      
      days.push({
        date: dateStr,
        day_of_week: date.toLocaleDateString('en-US', { weekday: 'short' }),
        day_of_month: date.getDate(),
        hasData: dayIndex !== -1,
        dataIndex: dayIndex !== -1 ? dayIndex : null,
        actualDate: date,
      });
    }
    
    return days;
  };

  const recentDays = generateDayButtons();
  const chartData = getCurrentData();

  return (
    <Card className="bg-white border-gray-200">
      <CardHeader>
        <div className="flex items-center justify-between mb-6">
          <div>
            <CardTitle className="text-lg font-bold text-gray-900">
              Activity Trends
            </CardTitle>
            <p className="text-sm text-gray-500 mt-1">
              {timeFrame === 'Days' && 'Request volume and threat detection over the last 24 hours'}
              {timeFrame === 'Weeks' && 'Daily request volume over the last 4 weeks'}
              {timeFrame === 'Months' && 'Weekly request volume over the last 3 months'}
            </p>
          </div>
          
          {/* Time Frame Selector */}
          <div className="flex gap-6 text-sm">
            {(['Days', 'Weeks', 'Months'] as TimeFrame[]).map((frame) => (
              <button
                key={frame}
                onClick={() => setTimeFrame(frame)}
                className={`${
                  timeFrame === frame
                    ? 'text-gray-900 font-semibold'
                    : 'text-gray-500 hover:text-gray-700'
                } transition-colors`}
              >
                {frame}
              </button>
            ))}
          </div>
        </div>

        {/* Day Selector - Only show for Days view */}
        {!loading && timeFrame === 'Days' && recentDays.length > 0 && (
          <div className="flex gap-2 overflow-x-auto pb-2 justify-end">
            {recentDays.map((day, buttonIdx) => {
              // Default to last button (today) if nothing selected
              const effectiveSelection = selectedButtonIndex !== null ? selectedButtonIndex : recentDays.length - 1;
              const isSelected = buttonIdx === effectiveSelection;
              
              return (
                <button
                  key={day.date}
                  onClick={() => setSelectedButtonIndex(buttonIdx)}
                  className={`
                    flex-shrink-0 rounded-xl px-4 py-3 min-w-[70px] text-center transition-all
                    ${isSelected 
                      ? 'bg-gradient-to-br from-blue-500 to-cyan-500 text-white shadow-lg shadow-blue-500/30' 
                      : day.hasData
                        ? 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                        : 'bg-gray-50 text-gray-400 hover:bg-gray-100'
                    }
                  `}
                >
                  <div className="text-xl font-semibold">
                    {day.day_of_month.toString().padStart(2, '0')}
                  </div>
                  <div className="text-xs mt-1">{day.day_of_week}</div>
                </button>
              );
            })}
          </div>
        )}
      </CardHeader>
      
      <CardContent className="pt-2">
        {loading ? (
          <div className="h-[320px] flex items-center justify-center">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-400">Loading activity data...</p>
            </div>
          </div>
        ) : (
          <div className="w-full h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart
                data={chartData}
                margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
              >
                <defs>
                  {/* Blue gradient for Requests */}
                  <linearGradient id="colorRequests" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0.1}/>
                  </linearGradient>
                  {/* Red gradient for Threats */}
                  <linearGradient id="colorThreats" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.8}/>
                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0.1}/>
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                <XAxis 
                  dataKey="time" 
                  stroke="#9ca3af"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  tickLine={false}
                  angle={timeFrame === 'Weeks' ? -45 : 0}
                  textAnchor={timeFrame === 'Weeks' ? 'end' : 'middle'}
                  height={timeFrame === 'Weeks' ? 80 : 60}
                />
                <YAxis 
                  stroke="#9ca3af"
                  tick={{ fill: '#6b7280', fontSize: 12 }}
                  tickLine={false}
                  tickFormatter={(value) => {
                    if (value >= 1000) return `${(value / 1000).toFixed(0)}k`;
                    return value.toString();
                  }}
                />
                <Tooltip
                  contentStyle={{
                    backgroundColor: 'rgba(255, 255, 255, 0.95)',
                    border: '1px solid #e5e7eb',
                    borderRadius: '8px',
                    boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)',
                  }}
                  labelStyle={{ color: '#374151', fontWeight: 600 }}
                />
                
                {/* Threats area (red, behind) */}
                <Area
                  type="monotone"
                  dataKey="Threats"
                  stroke="#ef4444"
                  strokeWidth={2}
                  fill="url(#colorThreats)"
                  fillOpacity={0.3}
                  dot={{ fill: '#ef4444', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                />
                
                {/* Requests area (blue, in front) */}
                <Area
                  type="monotone"
                  dataKey="Requests"
                  stroke="#3b82f6"
                  strokeWidth={3}
                  fill="url(#colorRequests)"
                  fillOpacity={0.6}
                  dot={{ fill: '#3b82f6', strokeWidth: 2, r: 4 }}
                  activeDot={{ r: 6 }}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
