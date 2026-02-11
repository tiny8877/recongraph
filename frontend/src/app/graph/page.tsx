'use client';

import { useState, useEffect, useMemo, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import AttackTypeBranch from '@/components/mindmap/AttackTypeBranch';
import { getProjects, getMindmapData } from '@/lib/api';
import type { Project, MindmapData } from '@/lib/types';

const ATTACK_TYPE_PILLS = ['All', 'RCE', 'SQLi', 'SSRF', 'LFI', 'IDOR', 'XSS', 'Open Redirect'];

function AttackMapContent() {
  const searchParams = useSearchParams();
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState(searchParams.get('project') || '');
  const [attackFilter, setAttackFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [mindmap, setMindmap] = useState<MindmapData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getProjects().then((data) => {
      setProjects(data);
      if (!selectedProject && data.length > 0) setSelectedProject(data[0].id);
    });
  }, []);

  useEffect(() => {
    if (!selectedProject) return;
    setLoading(true);
    getMindmapData(selectedProject, {
      attack_type: attackFilter || undefined,
    })
      .then(setMindmap)
      .finally(() => setLoading(false));
  }, [selectedProject, attackFilter]);

  const filteredBranches = useMemo(() => {
    if (!mindmap) return [];
    return mindmap.attack_types;
  }, [mindmap]);

  return (
    <div className="h-screen flex flex-col overflow-hidden">
      {/* Top bar */}
      <div className="h-12 bg-bg-secondary/80 backdrop-blur-sm border-b border-border-dark flex items-center px-4 gap-4 z-30 shrink-0">
        <span className="text-accent-cyan font-bold text-sm">ATTACK MAP</span>
        <select
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-bg-card border border-border-dark rounded px-2 py-1 text-xs text-gray-300 focus:outline-none"
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>{p.name}</option>
          ))}
        </select>
        {loading && <span className="text-accent-cyan text-xs animate-pulse">Loading...</span>}
        <div className="flex-1" />
        {mindmap && (
          <div className="flex items-center gap-3 text-xs text-gray-500">
            <span>{mindmap.summary.total_params} params</span>
            <span>{mindmap.summary.total_attack_types} attack types</span>
            {mindmap.summary.highest_severity > 0 && (
              <span className={`font-bold ${
                mindmap.summary.highest_severity >= 8 ? 'text-red-400' :
                mindmap.summary.highest_severity >= 5 ? 'text-orange-400' :
                'text-yellow-400'
              }`}>
                Max Severity: {mindmap.summary.highest_severity}/10
              </span>
            )}
          </div>
        )}
      </div>

      {/* Filter bar */}
      <div className="bg-bg-secondary/40 border-b border-border-dark px-4 py-2 flex items-center gap-2 flex-wrap shrink-0">
        {ATTACK_TYPE_PILLS.map((at) => (
          <button
            key={at}
            onClick={() => setAttackFilter(at === 'All' ? '' : at)}
            className={`px-2.5 py-1 rounded text-[10px] font-bold transition-colors ${
              (at === 'All' && !attackFilter) || attackFilter === at
                ? 'bg-accent-cyan/20 text-accent-cyan border border-accent-cyan/40'
                : 'bg-bg-primary text-gray-500 border border-border-dark hover:text-gray-300'
            }`}
          >
            {at}
          </button>
        ))}
        <div className="flex-1" />
        <input
          type="text"
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="Search parameters..."
          className="bg-bg-primary border border-border-dark rounded px-3 py-1 text-xs text-gray-300 w-56 focus:outline-none focus:border-accent-cyan/40 placeholder-gray-600"
        />
      </div>

      {/* Scrollable content */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {/* Domain hub card */}
        {mindmap && (
          <div className="glass-card p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-accent-cyan via-accent-blue to-accent-purple flex items-center justify-center text-bg-primary font-bold text-lg">
                {mindmap.root_domain.charAt(0).toUpperCase()}
              </div>
              <div className="flex-1">
                <h2 className="text-sm font-bold text-accent-cyan">{mindmap.root_domain}</h2>
                <p className="text-[10px] text-gray-500">{mindmap.project_name}</p>
              </div>
              <div className="flex items-center gap-4 text-center">
                <div>
                  <p className="text-lg font-bold text-gray-200">{mindmap.summary.total_params}</p>
                  <p className="text-[10px] text-gray-500">Params</p>
                </div>
                <div>
                  <p className="text-lg font-bold text-gray-200">{mindmap.summary.total_attack_types}</p>
                  <p className="text-[10px] text-gray-500">Types</p>
                </div>
                <div>
                  <p className={`text-lg font-bold ${
                    mindmap.summary.highest_severity >= 8 ? 'text-red-400' :
                    mindmap.summary.highest_severity >= 5 ? 'text-orange-400' :
                    mindmap.summary.highest_severity > 0 ? 'text-yellow-400' :
                    'text-gray-400'
                  }`}>
                    {mindmap.summary.highest_severity || '-'}
                  </p>
                  <p className="text-[10px] text-gray-500">Max Sev</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Attack type grid */}
        {filteredBranches.length > 0 && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-3">
            {filteredBranches.map((branch) => (
              <AttackTypeBranch
                key={branch.attack_type}
                branch={branch}
                searchQuery={searchQuery}
              />
            ))}
          </div>
        )}

        {/* Empty state */}
        {!loading && mindmap && filteredBranches.length === 0 && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-6xl text-gray-700 mb-4">&#x2694;</div>
              <p className="text-gray-500">No attack data found</p>
              <p className="text-xs text-gray-600 mt-1">Upload recon data to see the attack map</p>
            </div>
          </div>
        )}

        {/* Initial empty state */}
        {!loading && !mindmap && projects.length === 0 && (
          <div className="flex items-center justify-center py-20">
            <div className="text-center">
              <div className="text-6xl text-gray-700 mb-4">&#x2694;</div>
              <p className="text-gray-500">No projects found</p>
              <p className="text-xs text-gray-600 mt-1">Create a project and upload recon data</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default function AttackMapPage() {
  return (
    <Suspense fallback={<div className="h-screen flex items-center justify-center text-accent-cyan animate-pulse">Loading...</div>}>
      <AttackMapContent />
    </Suspense>
  );
}
