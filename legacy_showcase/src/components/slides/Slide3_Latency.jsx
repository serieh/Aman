import React from 'react';
import { Clock, Cpu, Monitor, HardDrive, Database } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell, CartesianGrid, LabelList } from 'recharts';

const chartData = [
  { name: 'VRAM (GB)', value: 9.89, fill: '#10b981' },
  { name: 'RAM (GB)', value: 11.07, fill: '#ec4899' },
  { name: 'CPU (%)', value: 21.4, fill: '#8b5cf6' }
];

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white dark:bg-slate-800 p-3 rounded-xl shadow-xl border border-slate-100 dark:border-slate-700">
        <p className="font-bold text-slate-800 dark:text-white">{`${payload[0].payload.name}: ${payload[0].value}`}</p>
      </div>
    );
  }
  return null;
};

const renderCustomBarLabel = ({ x, y, width, height, value, index }) => {
  const units = [' GB', ' GB', '%'];
  return (
    <text x={x + width + 10} y={y + height / 2 + 4} fill="#64748b" fontSize={13} fontWeight={600}>
      {value.toFixed(2)}{units[index]}
    </text>
  );
};

export default function Slide3_Latency() {
  return (
    <div className="flex flex-col h-full items-center justify-center p-8 animate-in fade-in slide-in-from-bottom-8 duration-700 relative overflow-hidden">
      
      {/* Background Decorative Shapes */}
      <div className="absolute top-10 left-10 w-64 h-64 bg-emerald-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse"></div>
      <div className="absolute bottom-10 right-10 w-72 h-72 bg-blue-300 rounded-full mix-blend-multiply filter blur-3xl opacity-30 animate-pulse" style={{ animationDelay: '1s' }}></div>

      <div className="max-w-5xl w-full bg-white/90 dark:bg-slate-800/90 backdrop-blur-xl rounded-3xl p-10 shadow-2xl border border-slate-200/50 dark:border-slate-700/50 z-10">
        <h2 className="text-4xl font-extrabold text-transparent bg-clip-text bg-gradient-to-r from-aman-primary to-aman-tertiary mb-10 text-center drop-shadow-sm">
          3. Latency & Efficiency
        </h2>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-10">
          <div className="space-y-6">
            <div className="flex items-center gap-6 bg-slate-50/80 dark:bg-slate-900/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 transform transition-transform hover:scale-105">
              <div className="w-14 h-14 rounded-full bg-orange-100 dark:bg-orange-900/30 flex items-center justify-center text-orange-500 flex-shrink-0 shadow-inner">
                <Clock size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-1">Response Latency</h3>
                <p className="text-slate-600 dark:text-slate-300">TTFT under <span className="font-bold text-orange-600">7s</span> with complex background processing.</p>
              </div>
            </div>

            <div className="flex items-center gap-6 bg-slate-50/80 dark:bg-slate-900/50 p-5 rounded-2xl border border-slate-100 dark:border-slate-700 transform transition-transform hover:scale-105">
              <div className="w-14 h-14 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-500 flex-shrink-0 shadow-inner">
                <HardDrive size={28} />
              </div>
              <div>
                <h3 className="text-lg font-bold text-slate-800 dark:text-white mb-1">Hardware Required</h3>
                <p className="text-slate-600 dark:text-slate-300">Consumer-grade deployment requires min. <span className="font-bold text-blue-600">12 GB VRAM</span>.</p>
              </div>
            </div>
          </div>

          <div className="flex flex-col justify-center h-64">
            <h3 className="text-xl font-bold text-slate-800 dark:text-white mb-4 border-b border-slate-200 dark:border-slate-700 pb-2">Resource Utilization Peak</h3>
            
            <div className="flex-1 w-full h-full pr-12">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} layout="vertical" margin={{ top: 5, right: 30, left: 10, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#cbd5e1" opacity={0.5} />
                  <XAxis type="number" hide />
                  <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fill: '#64748b', fontWeight: 600, fontSize: 13 }} width={85} />
                  <Tooltip content={<CustomTooltip />} cursor={{fill: 'transparent'}} />
                  <Bar dataKey="value" radius={[0, 6, 6, 0]} animationDuration={1500} animationEasing="ease-out" barSize={24} label={renderCustomBarLabel}>
                    {chartData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
