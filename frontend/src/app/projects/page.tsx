'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Header from '@/components/layout/Header';
import { getProjects, createProject, deleteProject } from '@/lib/api';
import type { Project } from '@/lib/types';

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [domain, setDomain] = useState('');
  const [loading, setLoading] = useState(true);

  const loadProjects = () => {
    setLoading(true);
    getProjects().then(setProjects).finally(() => setLoading(false));
  };

  useEffect(loadProjects, []);

  const handleCreate = async () => {
    if (!name || !domain) return;
    await createProject(name, domain);
    setName('');
    setDomain('');
    setShowCreate(false);
    loadProjects();
  };

  const handleDelete = async (id: string) => {
    if (!confirm('Delete this project and all its data?')) return;
    await deleteProject(id);
    loadProjects();
  };

  return (
    <div className="flex flex-col h-screen">
      <Header title="Projects" subtitle="Manage your recon targets" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="px-4 py-2 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 rounded-lg text-sm hover:bg-accent-cyan/20 transition-colors"
        >
          + New Project
        </button>

        {showCreate && (
          <div className="glass-card p-4 flex gap-3">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Project name"
              className="bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 flex-1 focus:outline-none focus:border-accent-cyan/50"
            />
            <input
              value={domain}
              onChange={(e) => setDomain(e.target.value)}
              placeholder="Root domain"
              className="bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 flex-1 focus:outline-none focus:border-accent-cyan/50"
            />
            <button onClick={handleCreate} className="px-4 py-2 bg-accent-green/10 text-accent-green border border-accent-green/20 rounded-lg text-sm">
              Create
            </button>
          </div>
        )}

        {loading ? (
          <div className="text-center py-12 text-accent-cyan animate-pulse">Loading...</div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12 text-gray-600">No projects yet. Create one to get started.</div>
        ) : (
          <div className="grid grid-cols-3 gap-4">
            {projects.map((p) => (
              <div key={p.id} className="glass-card p-4 hover:border-accent-cyan/30 transition-colors">
                <div className="flex justify-between items-start mb-3">
                  <div>
                    <h3 className="text-accent-cyan font-semibold">{p.name}</h3>
                    <p className="text-xs text-gray-500">{p.root_domain}</p>
                  </div>
                  <button
                    onClick={() => handleDelete(p.id)}
                    className="text-gray-600 hover:text-red-400 text-xs"
                  >
                    delete
                  </button>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Subdomains</span>
                    <span className="text-accent-blue">{p.subdomain_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">URLs</span>
                    <span className="text-accent-green">{p.url_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Params</span>
                    <span className="text-accent-yellow">{p.param_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Findings</span>
                    <span className="text-accent-red">{p.finding_count}</span>
                  </div>
                </div>
                <div className="mt-3 flex gap-2">
                  <Link href={`/graph?project=${p.id}`}
                    className="flex-1 text-center py-1.5 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 rounded text-xs hover:bg-accent-cyan/20">
                    View Graph
                  </Link>
                  <Link href={`/upload?project=${p.id}`}
                    className="flex-1 text-center py-1.5 bg-accent-green/10 text-accent-green border border-accent-green/20 rounded text-xs hover:bg-accent-green/20">
                    Upload Data
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
