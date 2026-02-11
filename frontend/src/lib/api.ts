import axios from 'axios';
import type { Project, GraphData, MindmapData, DashboardStats, UploadResponse, ScanJob, ToolStatus, ScanRequest } from './types';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api',
});

// Projects
export const createProject = (name: string, root_domain: string) =>
  api.post<Project>('/projects/', { name, root_domain }).then(r => r.data);

export const getProjects = () =>
  api.get<Project[]>('/projects/').then(r => r.data);

export const getProject = (id: string) =>
  api.get<Project>(`/projects/${id}`).then(r => r.data);

export const deleteProject = (id: string) =>
  api.delete(`/projects/${id}`).then(r => r.data);

// Upload
export const uploadReconFile = (projectId: string, file: File, toolType: string) => {
  const form = new FormData();
  form.append('file', file);
  form.append('tool_type', toolType);
  return api.post<UploadResponse>(`/projects/${projectId}/upload`, form).then(r => r.data);
};

export const uploadAutoDetect = (projectId: string, file: File) => {
  const form = new FormData();
  form.append('file', file);
  return api.post(`/projects/${projectId}/upload-auto`, form).then(r => r.data);
};

// Graph
export const getGraphData = (projectId: string, params?: { depth?: number; attack_type?: string; limit?: number; min_risk?: number }) =>
  api.get<GraphData>(`/projects/${projectId}/graph`, { params }).then(r => r.data);

// Mindmap
export const getMindmapData = (projectId: string, params?: { attack_type?: string }) =>
  api.get<MindmapData>(`/projects/${projectId}/mindmap`, { params }).then(r => r.data);

// Stats
export const getStats = (projectId: string) =>
  api.get<DashboardStats>(`/projects/${projectId}/stats`).then(r => r.data);

// Search
export const searchProject = (projectId: string, q: string, type?: string) =>
  api.get(`/projects/${projectId}/search`, { params: { q, type } }).then(r => r.data);

export const getParams = (projectId: string, params?: { attack_type?: string; page?: number; limit?: number }) =>
  api.get(`/projects/${projectId}/params`, { params }).then(r => r.data);

export const getSubdomains = (projectId: string, params?: { status_code?: number; page?: number; limit?: number }) =>
  api.get(`/projects/${projectId}/subdomains`, { params }).then(r => r.data);

export const getUrls = (projectId: string, params?: { attack_type?: string; subdomain?: string; page?: number }) =>
  api.get(`/projects/${projectId}/urls`, { params }).then(r => r.data);

// Attack URLs
export const getAttackUrls = (projectId: string, attackType?: string) =>
  api.get(`/projects/${projectId}/attack-urls`, { params: { attack_type: attackType } }).then(r => r.data);

// Export
export const exportData = (projectId: string, params?: { attack_type?: string; format?: string }) =>
  api.get(`/projects/${projectId}/export`, { params, responseType: 'blob' }).then(r => r.data);

// Health
export const checkHealth = () =>
  api.get('/health', { baseURL: 'http://localhost:8000' }).then(r => r.data).catch(() => null);

// Scanner - Tools
export const getToolStatus = () =>
  api.get<ToolStatus[]>('/scanner/tools').then(r => r.data);

export const installTool = (name: string) =>
  api.post(`/scanner/tools/${name}/install`).then(r => r.data);

// Scanner - Scans
export const startScan = (request: ScanRequest) =>
  api.post<ScanJob>('/scanner/start', request).then(r => r.data);

export const getScanJobs = (projectId?: string) =>
  api.get<ScanJob[]>('/scanner/jobs', { params: { project_id: projectId } }).then(r => r.data);

export const getScanJob = (scanId: string) =>
  api.get<ScanJob>(`/scanner/jobs/${scanId}`).then(r => r.data);

export const cancelScan = (scanId: string) =>
  api.post(`/scanner/jobs/${scanId}/cancel`).then(r => r.data);

export const pauseScan = (scanId: string) =>
  api.post(`/scanner/jobs/${scanId}/pause`).then(r => r.data);

export const resumeScan = (scanId: string) =>
  api.post(`/scanner/jobs/${scanId}/resume`).then(r => r.data);

export const stopScan = (scanId: string) =>
  api.post(`/scanner/jobs/${scanId}/stop`).then(r => r.data);

export const getScanDetails = (scanId: string) =>
  api.get(`/scanner/jobs/${scanId}/details`).then(r => r.data);

// Scanner - SSE stream
export const createScanStream = (scanId: string): EventSource => {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api';
  return new EventSource(`${baseUrl}/scanner/jobs/${scanId}/stream`);
};

// Delete operations
export const deleteSubdomain = (projectId: string, subdomainId: string) =>
  api.delete(`/projects/${projectId}/subdomains/${subdomainId}`).then(r => r.data);

export const deleteUrl = (projectId: string, urlId: string) =>
  api.delete(`/projects/${projectId}/urls/${urlId}`).then(r => r.data);

export const deleteParameter = (projectId: string, paramId: string) =>
  api.delete(`/projects/${projectId}/parameters/${paramId}`).then(r => r.data);

export const deleteFinding = (projectId: string, findingId: string) =>
  api.delete(`/projects/${projectId}/findings/${findingId}`).then(r => r.data);

export const clearProjectData = (projectId: string) =>
  api.delete(`/projects/${projectId}/clear`).then(r => r.data);

export const deleteUrlsByAttack = (projectId: string, attackType: string) =>
  api.delete(`/projects/${projectId}/urls-by-attack`, { params: { attack_type: attackType } }).then(r => r.data);

export default api;
