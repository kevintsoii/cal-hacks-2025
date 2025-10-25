"use client";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";

const threats = [
  {
    name: "Brute Force",
    count: 487,
    trend: "+23%",
    color: "from-red-500 to-orange-500",
  },
  {
    name: "Scraping",
    count: 312,
    trend: "+15%",
    color: "from-orange-500 to-yellow-500",
  },
  {
    name: "Jailbreak",
    count: 89,
    trend: "+8%",
    color: "from-yellow-500 to-red-500",
  },
  {
    name: "Anomaly",
    count: 156,
    trend: "-5%",
    color: "from-blue-500 to-cyan-500",
  },
];

export default function ThreatAnalysis() {
  return (
    <Card className="bg-white border-gray-200">
      <CardHeader>
        <CardTitle className="text-gray-900">Threat Analysis</CardTitle>
        <CardDescription className="text-gray-600">
          Last 24 hours
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {threats.map((threat) => (
            <div key={threat.name} className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium text-gray-700">
                  {threat.name}
                </span>
                <span className="text-sm font-bold text-gray-900">
                  {threat.count}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div
                  className={`h-full bg-gradient-to-r ${threat.color}`}
                  style={{ width: `${(threat.count / 500) * 100}%` }}
                ></div>
              </div>
              <div className="text-xs text-gray-500">
                {threat.trend} from yesterday
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}