'use client';

interface Props {
  data: { name: string; count: number }[];
}

export default function TopParams({ data }: Props) {
  const max = data.length > 0 ? data[0].count : 1;

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Top Parameters</h3>
      <div className="flex flex-col gap-2">
        {data.map((param, i) => (
          <div key={param.name} className="flex items-center gap-3">
            <span className="text-xs text-gray-500 w-4 text-right">{i + 1}</span>
            <span className="text-xs text-accent-yellow w-20 truncate font-semibold">{param.name}</span>
            <div className="flex-1 h-4 bg-bg-primary rounded-full overflow-hidden">
              <div
                className="h-full rounded-full bg-gradient-to-r from-accent-cyan/60 to-accent-cyan"
                style={{ width: `${(param.count / max) * 100}%` }}
              />
            </div>
            <span className="text-xs text-gray-400 w-10 text-right">{param.count}</span>
          </div>
        ))}
        {data.length === 0 && (
          <p className="text-xs text-gray-600 text-center py-4">No parameters found yet</p>
        )}
      </div>
    </div>
  );
}
