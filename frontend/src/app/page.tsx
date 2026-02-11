'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/layout/Header';
import StatsCards from '@/components/dashboard/StatsCards';
import AttackPieChart from '@/components/dashboard/AttackPieChart';
import TopParams from '@/components/dashboard/TopParams';
import StatusCodes from '@/components/dashboard/StatusCodes';
import { getProjects, getStats } from '@/lib/api';
import type { Project, DashboardStats } from '@/lib/types';

const emptyStats: DashboardStats = {
  total_subdomains: 0, total_urls: 0, total_params: 0, total_findings: 0,
  params_by_attack: {}, status_codes: {}, top_params: [], technologies: [], nuclei_summary: {},
};

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string>('');
  const [stats, setStats] = useState<DashboardStats>(emptyStats);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getProjects().then((data) => {
      setProjects(data);
      if (data.length > 0) setSelectedProject(data[0].id);
      setLoading(false);
    }).catch(() => setLoading(false));
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);
    getStats(selectedProject).then(setStats).finally(() => setLoading(false));
  }, [selectedProject]);

  return (
    <div className="flex flex-col h-screen">
      <Header title="ReconGraph" subtitle="Bug Bounty Recon Visualizer" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Project Selector */}
        <div className="flex items-center gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="bg-bg-card border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent-cyan/50"
          >
            {projects.length === 0 && <option value="">No projects - Create one first</option>}
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name} ({p.root_domain})</option>
            ))}
          </select>
          {loading && <span className="text-xs text-accent-cyan animate-pulse">Loading...</span>}
        </div>

        {/* Stats Cards */}
        <StatsCards stats={stats} />

        {/* Charts Grid */}
        <div className="grid grid-cols-2 gap-6">
          <AttackPieChart data={stats.params_by_attack} />
          <TopParams data={stats.top_params} />
        </div>

        <div className="grid grid-cols-2 gap-6">
          <StatusCodes data={stats.status_codes} />

          {/* Technologies */}
          <div className="glass-card p-4">
            <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Technologies</h3>
            <div className="flex flex-wrap gap-2">
              {stats.technologies.map((tech) => (
                <span key={tech.name} className="px-2 py-1 bg-accent-purple/10 text-accent-purple border border-accent-purple/20 rounded text-xs">
                  {tech.name} ({tech.count})
                </span>
              ))}
              {stats.technologies.length === 0 && (
                <p className="text-xs text-gray-600">No technology data yet</p>
              )}
            </div>
          </div>
        </div>

        {/* Nuclei Summary */}
        {Object.keys(stats.nuclei_summary).length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Nuclei Findings</h3>
            <div className="flex gap-4">
              {['critical', 'high', 'medium', 'low', 'info'].map((sev) => {
                const count = stats.nuclei_summary[sev] || 0;
                const colors: Record<string, string> = {
                  critical: 'text-red-500 bg-red-500/10', high: 'text-orange-500 bg-orange-500/10',
                  medium: 'text-yellow-500 bg-yellow-500/10', low: 'text-blue-400 bg-blue-400/10',
                  info: 'text-gray-400 bg-gray-400/10',
                };
                return (
                  <div key={sev} className={`px-4 py-2 rounded-lg ${colors[sev]}`}>
                    <div className="text-2xl font-bold">{count}</div>
                    <div className="text-xs uppercase">{sev}</div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
