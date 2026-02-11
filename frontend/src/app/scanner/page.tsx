'use client';

import { useState, useEffect, useRef, useCallback } from 'react';
import Header from '@/components/layout/Header';
import ScanTerminal from '@/components/scanner/ScanTerminal';
import ToolStatusBar from '@/components/scanner/ToolStatusBar';
import ScanProgressDetail from '@/components/scanner/ScanProgressDetail';
import {
  getProjects, getToolStatus, installTool, startScan,
  getScanJobs, cancelScan, pauseScan, resumeScan, stopScan,
  createScanStream, getScanJob,
} from '@/lib/api';
import type { Project, ToolStatus as ToolStatusType, ScanJob } from '@/lib/types';

const SCAN_TOOLS = [
  { value: 'full_auto', label: 'Full Auto Scan', desc: 'subfinder > httpx > waybackurls > nuclei', icon: '▶' },
  { value: 'subfinder', label: 'Subfinder', desc: 'Subdomain enumeration', icon: 'S' },
  { value: 'httpx', label: 'HTTPX', desc: 'HTTP probing & tech detection', icon: 'H' },
  { value: 'waybackurls', label: 'Waybackurls', desc: 'Historical URL discovery', icon: 'W' },
  { value: 'gau', label: 'GAU', desc: 'Get All URLs', icon: 'G' },
  { value: 'katana', label: 'Katana', desc: 'Active web crawler', icon: 'K' },
  { value: 'nuclei', label: 'Nuclei', desc: 'Vulnerability scanner', icon: 'N' },
];

interface ScanStats {
  subdomains_found: number;
  urls_discovered: number;
  params_classified: number;
  findings_count: number;
  current_tool: string | null;
  elapsed_seconds: number | null;
  tool_timings: Record<string, string>;
}

export default function ScannerPage() {
  const [tools, setTools] = useState<ToolStatusType[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState('__new__');
  const [targetDomain, setTargetDomain] = useState('');
  const [scanType, setScanType] = useState('full_auto');
  const [activeScan, setActiveScan] = useState<ScanJob | null>(null);
  const [logLines, setLogLines] = useState<string[]>([]);
  const [scanHistory, setScanHistory] = useState<ScanJob[]>([]);
  const [installing, setInstalling] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [scanStats, setScanStats] = useState<ScanStats | null>(null);
  const [showDetails, setShowDetails] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  const isRunning = activeScan?.status === 'running' || activeScan?.status === 'pending';
  const isPaused = activeScan?.status === 'paused';
  const isActive = isRunning || isPaused;

  // Load tools + projects + history on mount
  useEffect(() => {
    getToolStatus().then(setTools).catch(() => {});
    getProjects().then(setProjects).catch(() => {});
    getScanJobs().then(setScanHistory).catch(() => {});
  }, []);

  // SSE connection for active scan
  const connectSSE = useCallback((scanId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const es = createScanStream(scanId);
    eventSourceRef.current = es;

    es.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'log') {
          setLogLines(prev => [...prev, data.line]);
        } else if (data.type === 'stats') {
          setScanStats(data.data);
        } else if (data.type === 'status') {
          setActiveScan(prev => prev ? { ...prev, status: data.status } : null);
        } else if (data.type === 'done') {
          es.close();
          eventSourceRef.current = null;
          getScanJob(scanId).then((job) => {
            setActiveScan(job);
            getScanJobs().then(setScanHistory).catch(() => {});
            getProjects().then(setProjects).catch(() => {});
          });
        }
      } catch {}
    };

    es.onerror = () => {
      es.close();
      eventSourceRef.current = null;
    };
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleInstall = async (name: string) => {
    setInstalling(name);
    try {
      await installTool(name);
      const updated = await getToolStatus();
      setTools(updated);
    } catch (err: any) {
      alert(`Install failed: ${err.response?.data?.detail || err.message}`);
    }
    setInstalling(null);
  };

  const handleStartScan = async () => {
    if (!targetDomain.trim()) return;
    setStarting(true);
    setLogLines([]);
    setScanStats(null);
    setShowDetails(false);

    try {
      const job = await startScan({
        project_id: selectedProject === '__new__' ? undefined : selectedProject,
        project_name: selectedProject === '__new__' ? targetDomain : undefined,
        target_domain: targetDomain.trim(),
        scan_type: scanType,
      });
      setActiveScan(job);
      connectSSE(job.id);
    } catch (err: any) {
      alert(`Scan failed to start: ${err.response?.data?.detail || err.message}`);
    }
    setStarting(false);
  };

  const handlePause = async () => {
    if (!activeScan) return;
    try {
      await pauseScan(activeScan.id);
      setActiveScan(prev => prev ? { ...prev, status: 'paused' } : null);
    } catch {}
  };

  const handleResume = async () => {
    if (!activeScan) return;
    try {
      await resumeScan(activeScan.id);
      setActiveScan(prev => prev ? { ...prev, status: 'running' } : null);
    } catch {}
  };

  const handleStop = async () => {
    if (!activeScan) return;
    try {
      await stopScan(activeScan.id);
      setActiveScan(prev => prev ? { ...prev, status: 'stopped' } : null);
    } catch {}
  };

  const handleCancel = async () => {
    if (!activeScan) return;
    try {
      await cancelScan(activeScan.id);
      setActiveScan(prev => prev ? { ...prev, status: 'cancelled' } : null);
    } catch {}
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'bg-accent-cyan/10 text-accent-cyan';
      case 'paused': return 'bg-accent-yellow/10 text-accent-yellow';
      case 'completed': return 'bg-accent-green/10 text-accent-green';
      case 'failed': return 'bg-accent-red/10 text-accent-red';
      case 'stopped': return 'bg-accent-orange/10 text-accent-orange';
      case 'cancelled': return 'bg-gray-500/10 text-gray-400';
      default: return 'bg-gray-500/10 text-gray-400';
    }
  };

  const getStatusTextColor = (status: string) => {
    switch (status) {
      case 'running': return 'text-accent-cyan';
      case 'paused': return 'text-accent-yellow';
      case 'completed': return 'text-accent-green';
      case 'failed': return 'text-accent-red';
      case 'stopped': return 'text-accent-orange';
      default: return 'text-gray-500';
    }
  };

  const getProgressBarClass = () => {
    if (!activeScan) return 'bg-accent-cyan';
    switch (activeScan.status) {
      case 'completed': return 'bg-accent-green progress-glow';
      case 'failed': return 'bg-accent-red';
      case 'paused': return 'bg-accent-yellow';
      case 'stopped': return 'bg-accent-orange';
      default: return 'bg-gradient-to-r from-accent-cyan to-accent-blue progress-glow';
    }
  };

  return (
    <div className="flex flex-col h-screen">
      <Header title="Scanner" subtitle="Run recon tools directly from the UI" />

      <div className="flex-1 overflow-auto p-6 space-y-4">
        {/* Tool Status Bar */}
        <ToolStatusBar tools={tools} installing={installing} onInstall={handleInstall} />

        {/* Scan Configuration */}
        <div className="glass-card-elevated p-4 relative overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-accent-green via-accent-cyan to-accent-blue" />
          <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Scan Configuration</h3>

          <div className="flex gap-4 items-end mb-4">
            {/* Project Selector */}
            <div className="flex-1">
              <label className="text-[10px] text-gray-500 uppercase block mb-1">Project</label>
              <select
                value={selectedProject}
                onChange={(e) => setSelectedProject(e.target.value)}
                className="w-full bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent-cyan/50"
                disabled={isActive}
              >
                <option value="__new__">+ Create New Project</option>
                {projects.map((p) => (
                  <option key={p.id} value={p.id}>{p.name} ({p.root_domain})</option>
                ))}
              </select>
            </div>

            {/* Target Domain */}
            <div className="flex-1">
              <label className="text-[10px] text-gray-500 uppercase block mb-1">Target Domain</label>
              <input
                value={targetDomain}
                onChange={(e) => setTargetDomain(e.target.value)}
                placeholder="example.com"
                className="w-full bg-bg-primary border border-border-dark rounded-lg px-3 py-2 text-sm text-gray-300 focus:outline-none focus:border-accent-cyan/50"
                disabled={isActive}
              />
            </div>

            {/* Control Buttons */}
            <div className="flex gap-2">
              {isActive ? (
                <>
                  {isRunning ? (
                    <button
                      onClick={handlePause}
                      className="px-4 py-2 bg-accent-yellow/10 text-accent-yellow border border-accent-yellow/30 rounded-lg text-sm font-semibold hover:bg-accent-yellow/20 transition-colors"
                    >
                      Pause
                    </button>
                  ) : isPaused ? (
                    <button
                      onClick={handleResume}
                      className="px-4 py-2 bg-accent-cyan/10 text-accent-cyan border border-accent-cyan/30 rounded-lg text-sm font-semibold hover:bg-accent-cyan/20 transition-colors"
                    >
                      Resume
                    </button>
                  ) : null}
                  <button
                    onClick={handleStop}
                    className="px-4 py-2 bg-accent-orange/10 text-accent-orange border border-accent-orange/30 rounded-lg text-sm font-semibold hover:bg-accent-orange/20 transition-colors"
                  >
                    Stop
                  </button>
                  <button
                    onClick={handleCancel}
                    className="px-4 py-2 bg-accent-red/10 text-accent-red border border-accent-red/30 rounded-lg text-sm font-semibold hover:bg-accent-red/20 transition-colors"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <button
                  onClick={handleStartScan}
                  disabled={!targetDomain.trim() || starting}
                  className="px-6 py-2 bg-accent-green/10 text-accent-green border border-accent-green/30 rounded-lg text-sm font-semibold hover:bg-accent-green/20 transition-colors disabled:opacity-30"
                >
                  {starting ? 'Starting...' : 'Start Scan'}
                </button>
              )}
            </div>
          </div>

          {/* Scan Type Selector */}
          <div className="grid grid-cols-7 gap-2">
            {SCAN_TOOLS.map((tool) => (
              <button
                key={tool.value}
                onClick={() => !isActive && setScanType(tool.value)}
                disabled={isActive}
                className={`p-3 rounded-lg text-center transition-all border relative overflow-hidden ${
                  scanType === tool.value
                    ? tool.value === 'full_auto'
                      ? 'border-accent-green/50 bg-accent-green/10 shadow-lg shadow-accent-green/10'
                      : 'border-accent-cyan/50 bg-accent-cyan/10 shadow-lg shadow-accent-cyan/10'
                    : 'border-border-dark hover:border-gray-600 hover:bg-bg-hover disabled:opacity-50'
                }`}
              >
                <div className={`text-lg font-bold ${
                  scanType === tool.value
                    ? tool.value === 'full_auto' ? 'text-accent-green' : 'text-accent-cyan'
                    : 'text-gray-500'
                }`}>{tool.icon}</div>
                <div className={`text-[10px] font-semibold mt-1 ${
                  scanType === tool.value
                    ? tool.value === 'full_auto' ? 'text-accent-green' : 'text-accent-cyan'
                    : 'text-gray-400'
                }`}>{tool.label}</div>
                <div className="text-[8px] text-gray-600 mt-0.5">{tool.desc}</div>
              </button>
            ))}
          </div>
        </div>

        {/* Active Scan Progress */}
        {activeScan && (
          <div
            className="glass-card p-4 cursor-pointer hover:border-accent-cyan/30 transition-colors"
            onClick={() => setShowDetails(!showDetails)}
          >
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-3">
                <span className={`text-xs font-bold px-2 py-0.5 rounded ${getStatusColor(activeScan.status)}`}>
                  {activeScan.status.toUpperCase()}
                </span>
                <span className="text-xs text-gray-400">{activeScan.scan_type} &bull; {activeScan.target}</span>
                {activeScan.current_step && (
                  <span className="text-xs text-accent-cyan animate-pulse">{activeScan.current_step}</span>
                )}
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-500">{activeScan.progress}%</span>
                <span className="text-[10px] text-gray-600">Click for details</span>
              </div>
            </div>
            {/* Progress bar */}
            <div className="w-full h-2 bg-bg-primary rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${getProgressBarClass()}`}
                style={{ width: `${activeScan.progress}%`, color: activeScan.status === 'completed' ? '#00ff88' : '#00ffff' }}
              />
            </div>
          </div>
        )}

        {/* Scan Progress Detail */}
        {showDetails && activeScan && (
          <ScanProgressDetail
            stats={scanStats}
            progress={activeScan.progress}
            scanType={activeScan.scan_type}
            target={activeScan.target}
          />
        )}

        {/* Log Terminal */}
        <ScanTerminal lines={logLines} isRunning={isRunning || false} />

        {/* Scan History */}
        {scanHistory.length > 0 && (
          <div className="glass-card p-4">
            <h3 className="text-xs text-gray-500 uppercase tracking-wider mb-3">Scan History</h3>
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border-dark text-xs text-gray-500 uppercase">
                  <th className="px-3 py-2 text-left">Target</th>
                  <th className="px-3 py-2 text-left">Type</th>
                  <th className="px-3 py-2 text-left">Status</th>
                  <th className="px-3 py-2 text-left">Progress</th>
                  <th className="px-3 py-2 text-left">Started</th>
                </tr>
              </thead>
              <tbody>
                {scanHistory.map((job) => (
                  <tr key={job.id} className="border-b border-border-dark/50 hover:bg-bg-hover transition-colors">
                    <td className="px-3 py-2 text-accent-cyan">{job.target}</td>
                    <td className="px-3 py-2 text-gray-400">{job.scan_type}</td>
                    <td className="px-3 py-2">
                      <span className={`text-xs font-bold ${getStatusTextColor(job.status)}`}>{job.status}</span>
                    </td>
                    <td className="px-3 py-2 text-gray-400">{job.progress}%</td>
                    <td className="px-3 py-2 text-gray-500 text-xs">
                      {job.started_at ? new Date(job.started_at).toLocaleString() : '-'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
