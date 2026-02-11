'use client';

import { useState, useEffect, useCallback } from 'react';
import Header from '@/components/layout/Header';
import { getProjects, uploadReconFile, uploadAutoDetect, createProject } from '@/lib/api';
import type { Project, UploadResponse } from '@/lib/types';

const TOOL_TYPES = [
  { value: 'auto', label: 'Auto Detect', desc: 'Combined file - system detects everything automatically' },
  { value: 'subfinder', label: 'Subfinder / Amass', desc: 'Subdomain list (.txt)' },
  { value: 'waybackurls', label: 'Waybackurls / GAU / Katana', desc: 'URL list (.txt)' },
  { value: 'httpx', label: 'HTTPX', desc: 'JSON output (.json / .jsonl)' },
  { value: 'nuclei', label: 'Nuclei', desc: 'JSON output (.json / .jsonl)' },
];

interface AutoResult extends UploadResponse {
  breakdown?: Record<string, number>;
}

export default function UploadPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState('');
  const [toolType, setToolType] = useState('auto');
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [results, setResults] = useState<AutoResult[]>([]);
  const [showNewProject, setShowNewProject] = useState(false);
  const [newName, setNewName] = useState('');
  const [newDomain, setNewDomain] = useState('');

  useEffect(() => {
    getProjects().then((data) => {
      setProjects(data);
      if (data.length > 0) setSelectedProject(data[0].id);
    });
  }, []);

  const handleFiles = useCallback(async (files: FileList) => {
    if (!selectedProject) return;
    setUploading(true);
    const newResults: AutoResult[] = [];

    for (const file of Array.from(files)) {
      try {
        let result;
        if (toolType === 'auto') {
          result = await uploadAutoDetect(selectedProject, file);
        } else {
          result = await uploadReconFile(selectedProject, file, toolType);
        }
        newResults.push(result);
      } catch (err: any) {
        newResults.push({
          tool_type: toolType, parsed_count: 0, new_count: 0, duplicate_count: 0,
          message: `Error: ${err.response?.data?.detail || err.message}`,
        });
      }
    }

    setResults((prev) => [...newResults, ...prev]);
    setUploading(false);
  }, [selectedProject, toolType]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragActive(false);
    if (e.dataTransfer.files.length) handleFiles(e.dataTransfer.files);
  }, [handleFiles]);

  const handleCreateProject = async () => {
    if (!newName || !newDomain) return;
    const project = await createProject(newName, newDomain);
    setProjects((prev) => [project, ...prev]);
    setSelectedProject(project.id);
    setShowNewProject(false);
    setNewName('');
    setNewDomain('');
  };

  return (
    <div className="flex flex-col h-screen">
      <Header title="Upload Recon Data" subtitle="Import data from your recon tools" />

      <div className="flex-1 overflow-auto p-6 space-y-6">
        {/* Project Selection */}
        <div className="glass-card p-4">
          <div className="flex items-center gap-4">
            <select
              value={selectedProject}
              onChange={(e) => setSelectedProject(e.target.value)}
              className="bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent-cyan/50 flex-1"
            >
              {projects.length === 0 && <option value="">No projects</option>}
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name} ({p.root_domain})</option>
              ))}
            </select>
            <button
              onClick={() => setShowNewProject(!showNewProject)}
              className="px-4 py-2 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/20 rounded-lg text-sm hover:bg-accent-cyan/20 transition-colors"
            >
              + New Project
            </button>
          </div>

          {showNewProject && (
            <div className="mt-4 flex gap-3">
              <input
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                placeholder="Project name"
                className="bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 flex-1 focus:outline-none focus:border-accent-cyan/50"
              />
              <input
                value={newDomain}
                onChange={(e) => setNewDomain(e.target.value)}
                placeholder="Root domain (e.g. target.com)"
                className="bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 flex-1 focus:outline-none focus:border-accent-cyan/50"
              />
              <button
                onClick={handleCreateProject}
                className="px-4 py-2 bg-accent-green/10 text-accent-green border border-accent-green/20 rounded-lg text-sm hover:bg-accent-green/20"
              >
                Create
              </button>
            </div>
          )}
        </div>

        {/* Tool Type Selection */}
        <div className="grid grid-cols-5 gap-3">
          {TOOL_TYPES.map((tool) => (
            <button
              key={tool.value}
              onClick={() => setToolType(tool.value)}
              className={`glass-card p-3 text-left transition-all ${
                toolType === tool.value
                  ? tool.value === 'auto'
                    ? 'border-accent-green/50 bg-accent-green/5'
                    : 'border-accent-cyan/50 bg-accent-cyan/5'
                  : 'hover:border-gray-700'
              }`}
            >
              <div className={`text-sm font-semibold ${
                toolType === tool.value
                  ? tool.value === 'auto' ? 'text-accent-green' : 'text-accent-cyan'
                  : 'text-gray-300'
              }`}>
                {tool.label}
              </div>
              <div className="text-xs text-gray-500 mt-1">{tool.desc}</div>
            </button>
          ))}
        </div>

        {/* Auto detect info banner */}
        {toolType === 'auto' && (
          <div className="glass-card p-3 border-accent-green/20 bg-accent-green/5">
            <p className="text-xs text-accent-green">
              Auto Detect mode: Drop a combined file containing subdomains, URLs, httpx JSON, nuclei JSON all mixed together - the system automatically detects each line type.
            </p>
          </div>
        )}

        {/* Drop Zone */}
        <div
          onDragOver={(e) => { e.preventDefault(); setDragActive(true); }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          className={`glass-card border-2 border-dashed rounded-xl p-12 text-center transition-all cursor-pointer ${
            dragActive
              ? 'border-accent-cyan bg-accent-cyan/5'
              : 'border-border-dark hover:border-gray-600'
          }`}
          onClick={() => {
            const input = document.createElement('input');
            input.type = 'file';
            input.multiple = true;
            input.accept = '.txt,.json,.jsonl';
            input.onchange = (e) => {
              const files = (e.target as HTMLInputElement).files;
              if (files) handleFiles(files);
            };
            input.click();
          }}
        >
          {uploading ? (
            <div className="text-accent-cyan animate-pulse">
              <div className="text-4xl mb-2">&#x27F3;</div>
              <div className="text-lg">Processing files...</div>
            </div>
          ) : (
            <>
              <div className="text-4xl mb-3 text-gray-600">&#x2B06;</div>
              <div className="text-lg text-gray-400">Drop files here or click to browse</div>
              <div className="text-xs text-gray-600 mt-2">
                {toolType === 'auto'
                  ? 'Drop any recon file - subdomains, URLs, httpx JSON, nuclei JSON - all supported!'
                  : 'Supports .txt, .json, .jsonl files'}
              </div>
            </>
          )}
        </div>

        {/* Results */}
        {results.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Upload Results</h3>
            <div className="space-y-2">
              {results.map((r, i) => (
                <div key={i} className="p-3 bg-bg-primary rounded-lg">
                  <div className="flex items-center gap-4">
                    <span className={`text-xs px-2 py-1 rounded ${
                      r.tool_type === 'auto'
                        ? 'bg-accent-green/10 text-accent-green'
                        : 'bg-accent-blue/10 text-accent-blue'
                    }`}>{r.tool_type}</span>
                    <span className="text-sm text-gray-300 flex-1">{r.message}</span>
                    <div className="flex gap-3 text-xs">
                      <span className="text-accent-green">+{r.new_count} new</span>
                      <span className="text-gray-500">{r.duplicate_count} dup</span>
                      <span className="text-gray-400">{r.parsed_count} total</span>
                    </div>
                  </div>
                  {/* Breakdown for auto-detect */}
                  {r.breakdown && (
                    <div className="mt-2 flex gap-3 flex-wrap">
                      {Object.entries(r.breakdown).map(([key, val]) => (
                        val > 0 && (
                          <span key={key} className="text-[10px] px-2 py-0.5 bg-bg-card border border-border-dark rounded text-gray-400">
                            {key.replace(/_/g, ' ')}: <span className="text-accent-cyan font-bold">{val}</span>
                          </span>
                        )
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
