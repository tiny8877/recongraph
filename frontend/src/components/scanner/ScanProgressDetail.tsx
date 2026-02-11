'use client';

interface ScanStats {
  subdomains_found: number;
  urls_discovered: number;
  params_classified: number;
  findings_count: number;
  current_tool: string | null;
  elapsed_seconds: number | null;
  tool_timings: Record<string, string>;
}

interface Props {
  stats: ScanStats | null;
  progress: number;
  scanType: string;
  target: string;
}

const PIPELINE_STEPS = ['subfinder', 'httpx', 'waybackurls', 'nuclei'];

function formatElapsed(seconds: number | null): string {
  if (!seconds) return '0s';
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  return m > 0 ? `${m}m ${s}s` : `${s}s`;
}

export default function ScanProgressDetail({ stats, progress, scanType, target }: Props) {
  const timings = stats?.tool_timings || {};
  const currentTool = stats?.current_tool;

  return (
    <div className="glass-card-elevated p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-xs text-gray-500 uppercase tracking-wider">Scan Progress Details</h3>
        <span className="text-xs text-gray-400">
          Elapsed: <span className="text-accent-cyan font-bold">{formatElapsed(stats?.elapsed_seconds ?? null)}</span>
        </span>
      </div>

      {/* Pipeline Visualization */}
      {scanType === 'full_auto' && (
        <div className="flex items-center gap-1">
          {PIPELINE_STEPS.map((step, i) => {
            const isDone = timings[step] === 'completed';
            const isActive = currentTool === step && !isDone;
            const isPending = !isDone && !isActive;

            return (
              <div key={step} className="flex items-center gap-1 flex-1">
                <div className={`flex-1 rounded-lg px-3 py-2 text-center text-xs font-semibold border transition-all ${
                  isDone ? 'bg-accent-green/10 border-accent-green/30 text-accent-green' :
                  isActive ? 'bg-accent-cyan/10 border-accent-cyan/30 text-accent-cyan status-pulse-running' :
                  'bg-bg-primary border-border-dark text-gray-600'
                }`}>
                  <div className="text-[10px] uppercase">{step}</div>
                  <div className="text-[8px] mt-0.5">
                    {isDone ? 'Done' : isActive ? 'Running...' : 'Pending'}
                  </div>
                </div>
                {i < PIPELINE_STEPS.length - 1 && (
                  <span className={`text-xs ${isDone ? 'text-accent-green' : 'text-gray-600'}`}>→</span>
                )}
              </div>
            );
          })}
        </div>
      )}

      {/* Stats Grid */}
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: 'Subdomains', value: stats?.subdomains_found ?? 0, color: 'text-accent-blue' },
          { label: 'URLs', value: stats?.urls_discovered ?? 0, color: 'text-accent-green' },
          { label: 'Parameters', value: stats?.params_classified ?? 0, color: 'text-accent-yellow' },
          { label: 'Findings', value: stats?.findings_count ?? 0, color: 'text-accent-red' },
        ].map((stat) => (
          <div key={stat.label} className="bg-bg-primary rounded-lg p-3 text-center border border-border-dark">
            <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
            <div className="text-[10px] text-gray-500 uppercase mt-1">{stat.label}</div>
          </div>
        ))}
      </div>

      {/* Progress Summary */}
      <div className="flex items-center gap-3 text-xs text-gray-400">
        <span>Target: <span className="text-accent-cyan">{target}</span></span>
        <span>|</span>
        <span>Progress: <span className="text-accent-green font-bold">{progress}%</span></span>
        {stats?.current_tool && (
          <>
            <span>|</span>
            <span>Current: <span className="text-accent-cyan">{stats.current_tool}</span></span>
          </>
        )}
      </div>
    </div>
  );
}
