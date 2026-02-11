'use client';

import { useEffect, useRef } from 'react';
import * as d3 from 'd3';

const ATTACK_COLORS: Record<string, string> = {
  LFI: '#ff4444',
  XSS: '#ff8800',
  SQLi: '#ff0066',
  SSRF: '#aa00ff',
  'Open Redirect': '#ffaa00',
  RCE: '#ff0000',
  IDOR: '#00aaff',
};

interface Props {
  data: Record<string, number>;
}

export default function AttackPieChart({ data }: Props) {
  const ref = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!ref.current || Object.keys(data).length === 0) return;

    const svg = d3.select(ref.current);
    svg.selectAll('*').remove();

    const width = 280;
    const height = 280;
    const radius = Math.min(width, height) / 2 - 20;

    const g = svg
      .attr('width', width)
      .attr('height', height)
      .append('g')
      .attr('transform', `translate(${width / 2},${height / 2})`);

    const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
    const pie = d3.pie<[string, number]>().value(d => d[1]).sort(null);
    const arc = d3.arc<d3.PieArcDatum<[string, number]>>().innerRadius(radius * 0.5).outerRadius(radius);

    const arcs = g.selectAll('.arc').data(pie(entries)).enter().append('g').attr('class', 'arc');

    arcs.append('path')
      .attr('d', arc)
      .attr('fill', d => ATTACK_COLORS[d.data[0]] || '#666')
      .attr('stroke', '#0a0e17')
      .attr('stroke-width', 2)
      .style('opacity', 0.85)
      .on('mouseover', function () { d3.select(this).style('opacity', 1).attr('stroke-width', 3); })
      .on('mouseout', function () { d3.select(this).style('opacity', 0.85).attr('stroke-width', 2); });

    // Center total
    const total = entries.reduce((s, [, v]) => s + v, 0);
    g.append('text').attr('text-anchor', 'middle').attr('dy', '-0.2em')
      .attr('fill', '#00ffff').attr('font-size', '24px').attr('font-weight', 'bold')
      .text(total.toString());
    g.append('text').attr('text-anchor', 'middle').attr('dy', '1.2em')
      .attr('fill', '#64748b').attr('font-size', '10px')
      .text('PARAMS');
  }, [data]);

  return (
    <div className="glass-card p-4">
      <h3 className="text-sm text-gray-400 mb-3 uppercase tracking-wider">Attack Distribution</h3>
      <div className="flex items-center gap-4">
        <svg ref={ref} />
        <div className="flex flex-col gap-1.5">
          {Object.entries(data).sort((a, b) => b[1] - a[1]).map(([attack, count]) => (
            <div key={attack} className="flex items-center gap-2 text-xs">
              <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: ATTACK_COLORS[attack] || '#666' }} />
              <span className="text-gray-400 w-24">{attack}</span>
              <span className="text-gray-300 font-semibold">{count}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
