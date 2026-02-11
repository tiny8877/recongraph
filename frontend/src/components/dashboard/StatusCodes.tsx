'use client';

const STATUS_COLORS: Record<string, string> = {
  '2': '#00ff88',
  '3': '#ffaa00',
  '4': '#ff4444',
  '5': '#ff0066',
};

interface Props {
  data: Record<string, number>;
}

export default function StatusCodes({ data }: Props) {
  const total = Object.values(data).reduce((s, v) => s + v, 0) || 1;
  const sorted = Object.entries(data).sort((a, b) => b[1] - a[1]);

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Status Codes</h3>
      <div className="flex flex-col gap-2">
        {sorted.map(([code, count]) => (
          <div key={code} className="flex items-center gap-3">
            <span
              className="text-xs font-bold w-10 text-center py-0.5 rounded"
              style={{ color: STATUS_COLORS[code[0]] || '#888', backgroundColor: (STATUS_COLORS[code[0]] || '#888') + '15' }}
            >
              {code}
            </span>
            <div className="flex-1 h-3 bg-bg-primary rounded-full overflow-hidden">
              <div
                className="h-full rounded-full"
                style={{ width: `${(count / total) * 100}%`, backgroundColor: STATUS_COLORS[code[0]] || '#888' }}
              />
            </div>
            <span className="text-xs text-gray-400 w-10 text-right">{count}</span>
          </div>
        ))}
        {sorted.length === 0 && (
          <p className="text-xs text-gray-600 text-center py-4">No httpx data uploaded yet</p>
        )}
      </div>
    </div>
  );
}
