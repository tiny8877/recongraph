export interface Project {
  id: string;
  name: string;
  root_domain: string;
  created_at: string;
  subdomain_count: number;
  url_count: number;
  param_count: number;
  finding_count: number;
}

export interface GraphNode {
  id: string;
  label: string;
  type: 'domain' | 'subdomain' | 'url' | 'parameter' | 'attack_type' | 'finding';
  color: string;
  size: number;
  data: Record<string, any>;
  // D3 simulation properties
  x?: number;
  y?: number;
  fx?: number | null;
  fy?: number | null;
  vx?: number;
  vy?: number;
}

export interface GraphEdge {
  source: string | GraphNode;
  target: string | GraphNode;
  label: string;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
  total_nodes: number;
  truncated: boolean;
  risk_summary: Record<string, number>;
}

export interface DashboardStats {
  total_subdomains: number;
  total_urls: number;
  total_params: number;
  total_findings: number;
  params_by_attack: Record<string, number>;
  status_codes: Record<string, number>;
  top_params: { name: string; count: number }[];
  technologies: { name: string; count: number }[];
  nuclei_summary: Record<string, number>;
}

export interface UploadResponse {
  tool_type: string;
  parsed_count: number;
  new_count: number;
  duplicate_count: number;
  message: string;
}

export interface ParamItem {
  name: string;
  count: number;
  attack_types: string[];
  sample_value: string | null;
}

export interface SubdomainItem {
  id: string;
  subdomain: string;
  ip_address: string | null;
  status_code: number | null;
  title: string | null;
  technologies: string[] | null;
  url_count: number;
  source: string;
}

export interface ScanJob {
  id: string;
  project_id: string;
  scan_type: string;
  target: string;
  status: 'pending' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled' | 'stopped';
  current_step: string | null;
  progress: number;
  log: string | null;
  result_summary: Record<string, any> | null;
  error: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
}

export interface ToolStatus {
  name: string;
  installed: boolean;
  path: string | null;
  version: string | null;
}

export interface ScanRequest {
  project_id?: string;
  project_name?: string;
  target_domain: string;
  scan_type: string;
}

// Mindmap types
export interface MindmapUrl {
  full_url: string;
  path: string;
}

export interface MindmapTechnique {
  name: string;
  description: string;
  payloads: string[];
  tools: string[];
  references: string[];
}

export interface MindmapParameter {
  name: string;
  risk_score: number;
  sample_value: string | null;
  urls: MindmapUrl[];
  attack_types: string[];
}

export interface MindmapAttackType {
  attack_type: string;
  description: string;
  severity: number;
  color: string;
  param_count: number;
  parameters: MindmapParameter[];
  techniques: MindmapTechnique[];
}

export interface MindmapSummary {
  total_params: number;
  total_attack_types: number;
  highest_severity: number;
  attack_type_counts: Record<string, number>;
}

export interface MindmapData {
  root_domain: string;
  project_name: string;
  summary: MindmapSummary;
  attack_types: MindmapAttackType[];
}
