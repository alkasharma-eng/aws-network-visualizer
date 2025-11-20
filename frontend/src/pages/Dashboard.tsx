import { useQuery } from '@tanstack/react-query';
import { BarChart, Network, Shield, AlertTriangle } from 'lucide-react';
import { fetchTopologySummary, fetchAnomalies } from '../api/client';

const Dashboard = () => {
  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ['topology-summary'],
    queryFn: fetchTopologySummary,
  });

  const { data: anomalies, isLoading: anomaliesLoading } = useQuery({
    queryKey: ['anomalies'],
    queryFn: fetchAnomalies,
  });

  if (summaryLoading || anomaliesLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <h1 className="text-3xl font-bold">AWS Network Visualizer</h1>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Resources</p>
              <p className="text-3xl font-bold">{summary?.total_resources || 0}</p>
            </div>
            <Network className="w-12 h-12 text-blue-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">VPCs</p>
              <p className="text-3xl font-bold">
                {summary?.resources_by_type?.vpc || 0}
              </p>
            </div>
            <BarChart className="w-12 h-12 text-green-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Security Groups</p>
              <p className="text-3xl font-bold">
                {summary?.resources_by_type?.security_group || 0}
              </p>
            </div>
            <Shield className="w-12 h-12 text-purple-500" />
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Anomalies</p>
              <p className="text-3xl font-bold text-red-600">
                {anomalies?.total_anomalies || 0}
              </p>
            </div>
            <AlertTriangle className="w-12 h-12 text-red-500" />
          </div>
        </div>
      </div>

      {/* Recent Anomalies */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Recent Anomalies</h2>
        {anomalies && anomalies.anomalies.length > 0 ? (
          <div className="space-y-4">
            {anomalies.anomalies.slice(0, 5).map((anomaly, index) => (
              <div
                key={index}
                className="border-l-4 border-red-500 pl-4 py-2"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-semibold">{anomaly.title}</p>
                    <p className="text-sm text-gray-600">
                      {anomaly.description}
                    </p>
                  </div>
                  <span
                    className={`px-3 py-1 rounded text-sm font-semibold ${
                      anomaly.severity === 'critical'
                        ? 'bg-red-100 text-red-800'
                        : anomaly.severity === 'high'
                        ? 'bg-orange-100 text-orange-800'
                        : 'bg-yellow-100 text-yellow-800'
                    }`}
                  >
                    {anomaly.severity.toUpperCase()}
                  </span>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-600">No anomalies detected</p>
        )}
      </div>
    </div>
  );
};

export default Dashboard;
