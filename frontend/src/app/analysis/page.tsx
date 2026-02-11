'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/layout/Header';
import {
  getProjects, getParams, getSubdomains, getAttackUrls, exportData,
  clearProjectData, deleteSubdomain, deleteUrlsByAttack,
} from '@/lib/api';
import type { Project, ParamItem, SubdomainItem } from '@/lib/types';

const ATTACK_TYPES = ['All', 'LFI', 'XSS', 'SQLi', 'SSRF', 'Open Redirect', 'RCE', 'IDOR'];
const ATTACK_COLORS: Record<string, string> = {
  LFI: '#ff4444', XSS: '#ff8800', SQLi: '#ff0066', SSRF: '#aa00ff',
  'Open Redirect': '#ffaa00', RCE: '#ff0000', IDOR: '#00aaff',
};

interface AttackUrlEntry {
  url: string;
  param: string;
  value: string | null;
}

interface AttackUrlGroup {
  count: number;
  urls: AttackUrlEntry[];
}

export default function AnalysisPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [activeTab, setActiveTab] = useState<'attack_urls' | 'params' | 'subdomains'>('attack_urls');
  const [attackFilter, setAttackFilter] = useState('All');
  const [params, setParams] = useState<ParamItem[]>([]);
  const [subdomains, setSubdomains] = useState<SubdomainItem[]>([]);
  const [attackUrls, setAttackUrls] = useState<Record<string, AttackUrlGroup>>({});
  const [loading, setLoading] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    getProjects().then((data) => {
      setProjects(data);
      if (data.length > 0) setSelectedProject(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);

    if (activeTab === 'attack_urls') {
      const filter = attackFilter === 'All' ? undefined : attackFilter;
      getAttackUrls(selectedProject, filter)
        .then(setAttackUrls)
        .finally(() => setLoading(false));
    } else if (activeTab === 'params') {
      const filter = attackFilter === 'All' ? undefined : attackFilter;
      getParams(selectedProject, { attack_type: filter, limit: 200 })
        .then((data) => setParams(data.items))
        .finally(() => setLoading(false));
    } else {
      getSubdomains(selectedProject, { limit: 200 })
        .then((data) => setSubdomains(data.items))
        .finally(() => setLoading(false));
    }
  }, [selectedProject, activeTab, attackFilter, refreshKey]);

  const reload = () => setRefreshKey(k => k + 1);

  const handleExport = async (format: string) => {
    if (!selectedProject) return;
    const filter = attackFilter === 'All' ? undefined : attackFilter;
    const blob = await exportData(selectedProject, { attack_type: filter, format });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `export.${format}`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  const handleClearAll = async () => {
    if (!selectedProject) return;
    if (!confirm('Are you sure you want to delete ALL data for this project? This cannot be undone.')) return;
    await clearProjectData(selectedProject);
    reload();
  };

  const handleDeleteAttackUrls = async (attackType: string) => {
    if (!selectedProject) return;
    if (!confirm(`Delete all URLs vulnerable to ${attackType}?`)) return;
    await deleteUrlsByAttack(selectedProject, attackType);
    reload();
  };

  const handleDeleteSubdomain = async (subdomainId: string) => {
    if (!selectedProject) return;
    if (!confirm('Delete this subdomain and all its URLs/parameters?')) return;
    await deleteSubdomain(selectedProject, subdomainId);
    reload();
  };

  return (
    <div className="flex flex-col h-screen">
      <Header title="Analysis" subtitle="Deep dive into your recon data" />

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* Controls */}
        <div className="flex items-center gap-4">
          <select
            value={selectedProject}
            onChange={(e) => setSelectedProject(e.target.value)}
            className="bg-bg-card border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent-cyan/50"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.name}</option>
            ))}
          </select>

          {/* Tabs */}
          <div className="flex bg-bg-card rounded-lg border border-border-dark overflow-hidden">
            {([
              { key: 'attack_urls' as const, label: 'Attack URLs' },
              { key: 'params' as const, label: 'Parameters' },
              { key: 'subdomains' as const, label: 'Subdomains' },
            ]).map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 text-xs transition-colors ${
                  activeTab === tab.key
                    ? tab.key === 'attack_urls'
                      ? 'bg-accent-red/10 text-accent-red'
                      : 'bg-accent-cyan/10 text-accent-cyan'
                    : 'text-gray-500 hover:text-gray-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          <div className="flex-1" />

          {/* Clear All */}
          <button
            onClick={handleClearAll}
            className="px-3 py-1.5 bg-accent-red/5 border border-accent-red/20 rounded text-xs text-accent-red hover:bg-accent-red/10"
          >
            Clear All Data
          </button>

          {/* Export */}
          <div className="flex gap-2">
            {['txt', 'json', 'csv'].map((fmt) => (
              <button
                key={fmt}
                onClick={() => handleExport(fmt)}
                className="px-3 py-1.5 bg-bg-card border border-border-dark rounded text-xs text-gray-400 hover:text-accent-green hover:border-accent-green/30"
              >
                .{fmt}
              </button>
            ))}
          </div>
        </div>

        {/* Attack Type Filter */}
        {(activeTab === 'params' || activeTab === 'attack_urls') && (
          <div className="flex gap-2">
            {ATTACK_TYPES.map((at) => (
              <button
                key={at}
                onClick={() => setAttackFilter(at)}
                className={`px-3 py-1.5 rounded-lg text-xs transition-colors border ${
                  attackFilter === at
                    ? 'border-accent-cyan/50 bg-accent-cyan/10 text-accent-cyan'
                    : 'border-border-dark text-gray-500 hover:text-gray-300'
                }`}
              >
                {at}
              </button>
            ))}
          </div>
        )}

        {/* Data Display */}
        <div className="glass-card overflow-hidden">
          {loading ? (
            <div className="p-8 text-center text-accent-cyan animate-pulse">Loading...</div>
          ) : activeTab === 'attack_urls' ? (
            /* === ATTACK URLs TAB === */
            <div className="divide-y divide-border-dark">
              {Object.keys(attackUrls).length === 0 ? (
                <div className="p-8 text-center text-gray-600">No vulnerable URLs found. Upload waybackurls/gau/katana data first.</div>
              ) : (
                Object.entries(attackUrls).map(([attack, group]) => (
                  <div key={attack} className="p-4">
                    {/* Attack header */}
                    <div className="flex items-center gap-3 mb-3">
                      <span
                        className="px-3 py-1 rounded-lg text-sm font-bold"
                        style={{ color: ATTACK_COLORS[attack], backgroundColor: (ATTACK_COLORS[attack] || '#888') + '15' }}
                      >
                        {attack}
                      </span>
                      <span className="text-xs text-gray-500">{group.count} vulnerable URLs</span>
                      <button
                        onClick={() => handleDeleteAttackUrls(attack)}
                        className="text-[10px] px-2 py-0.5 text-accent-red border border-accent-red/20 rounded hover:bg-accent-red/10 ml-auto"
                      >
                        Delete All {attack}
                      </button>
                    </div>
                    {/* URL list */}
                    <div className="space-y-1 max-h-80 overflow-auto">
                      {group.urls.map((entry, i) => (
                        <div key={i} className="flex items-center gap-3 px-3 py-2 bg-bg-primary rounded hover:bg-bg-hover transition-colors group">
                          <span className="text-xs text-gray-300 flex-1 font-mono truncate" title={entry.url}>
                            {entry.url}
                          </span>
                          <span
                            className="text-[10px] px-2 py-0.5 rounded font-bold shrink-0"
                            style={{ color: ATTACK_COLORS[attack], backgroundColor: (ATTACK_COLORS[attack] || '#888') + '15' }}
                          >
                            ?{entry.param}=
                          </span>
                          <button
                            onClick={() => navigator.clipboard.writeText(entry.url)}
                            className="text-[10px] text-gray-600 hover:text-accent-cyan opacity-0 group-hover:opacity-100 transition-opacity shrink-0"
                          >
                            copy
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          ) : activeTab === 'params' ? (
            /* === PARAMS TAB === */
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dark text-xs text-gray-500 uppercase">
                  <th className="px-4 py-3 text-left">Parameter</th>
                  <th className="px-4 py-3 text-left">Count</th>
                  <th className="px-4 py-3 text-left">Attack Types</th>
                  <th className="px-4 py-3 text-left">Sample Value</th>
                </tr>
              </thead>
              <tbody>
                {params.map((p, i) => (
                  <tr key={i} className="border-b border-border-dark/50 hover:bg-bg-hover transition-colors">
                    <td className="px-4 py-3 text-accent-yellow font-semibold">{p.name}</td>
                    <td className="px-4 py-3 text-gray-400">{p.count}</td>
                    <td className="px-4 py-3">
                      <div className="flex gap-1 flex-wrap">
                        {p.attack_types.map((at) => (
                          <span key={at} className="px-1.5 py-0.5 rounded text-[10px] font-bold"
                            style={{ color: ATTACK_COLORS[at], backgroundColor: (ATTACK_COLORS[at] || '#888') + '15' }}>
                            {at}
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-gray-500 truncate max-w-xs">{p.sample_value || '-'}</td>
                  </tr>
                ))}
                {params.length === 0 && (
                  <tr><td colSpan={4} className="px-4 py-8 text-center text-gray-600">No parameters found</td></tr>
                )}
              </tbody>
            </table>
          ) : (
            /* === SUBDOMAINS TAB === */
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dark text-xs text-gray-500 uppercase">
                  <th className="px-4 py-3 text-left">Subdomain</th>
                  <th className="px-4 py-3 text-left">IP</th>
                  <th className="px-4 py-3 text-left">Status</th>
                  <th className="px-4 py-3 text-left">Title</th>
                  <th className="px-4 py-3 text-left">URLs</th>
                  <th className="px-4 py-3 text-left">Source</th>
                  <th className="px-4 py-3 text-left w-16"></th>
                </tr>
              </thead>
              <tbody>
                {subdomains.map((s) => (
                  <tr key={s.id} className="border-b border-border-dark/50 hover:bg-bg-hover transition-colors group">
                    <td className="px-4 py-3 text-accent-blue">{s.subdomain}</td>
                    <td className="px-4 py-3 text-gray-500 font-mono text-xs">{s.ip_address || '-'}</td>
                    <td className="px-4 py-3">
                      {s.status_code && (
                        <span className={`text-xs font-bold ${
                          s.status_code < 300 ? 'text-accent-green' :
                          s.status_code < 400 ? 'text-accent-orange' : 'text-accent-red'
                        }`}>{s.status_code}</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-gray-400 truncate max-w-xs">{s.title || '-'}</td>
                    <td className="px-4 py-3 text-gray-400">{s.url_count}</td>
                    <td className="px-4 py-3 text-gray-500 text-xs">{s.source}</td>
                    <td className="px-4 py-3">
                      <button
                        onClick={() => handleDeleteSubdomain(s.id)}
                        className="text-[10px] text-gray-600 hover:text-accent-red opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        delete
                      </button>
                    </td>
                  </tr>
                ))}
                {subdomains.length === 0 && (
                  <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-600">No subdomains found</td></tr>
                )}
              </tbody>
            </table>
          )}
        </div>
      </div>
    </div>
  );
}
