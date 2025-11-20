import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:3000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export interface TopologySummary {
  total_resources: number;
  total_regions: number;
  resources_by_type: Record<string, number>;
  resources_by_region: Record<string, number>;
}

export interface Anomaly {
  type: string;
  severity: string;
  title: string;
  description: string;
  affected_resources: string[];
  remediation?: string;
  confidence_score: number;
}

export interface AnomalyReport {
  total_anomalies: number;
  by_severity: Record<string, number>;
  by_type: Record<string, number>;
  anomalies: Anomaly[];
}

export async function fetchTopologySummary(): Promise<TopologySummary> {
  const response = await api.get('/topology/summary');
  return response.data;
}

export async function fetchTopology(region: string, vpcId: string) {
  const response = await api.get(`/topology/${region}/${vpcId}`);
  return response.data.topology;
}

export async function fetchAnomalies(): Promise<AnomalyReport> {
  const response = await api.get('/analyses/latest');
  return response.data.anomaly_report;
}

export async function triggerDiscovery(regions: string[]) {
  const response = await api.post('/discovery/trigger', { regions });
  return response.data;
}

export async function triggerAnalysis(region: string, vpcId: string) {
  const response = await api.post('/analysis/trigger', { region, vpc_id: vpcId });
  return response.data;
}

export default api;
