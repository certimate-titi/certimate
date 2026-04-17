'use client';

import React, { useState, useEffect } from 'react';
import { Loader2, CheckCircle, XCircle } from 'lucide-react';
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { superAdminService } from '@/lib/api/services';
import { BUILD_INFO } from '@/lib/build-info';

function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

interface VersionInfo {
  backend_version: string;
  backend_commit: string;
  api_prefix: string;
  python_version: string;
  alembic_head: string;
  deployed_at: string;
  environment: string;
}

export default function VersionPage() {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  const fetchVersion = () => {
    setLoading(true);
    setError(false);
    superAdminService.getVersionInfo().then(res => {
      setVersionInfo(res);
    }).catch(() => setError(true)).finally(() => setLoading(false));
  };

  useEffect(() => { fetchVersion(); }, []);

  return (
    <div className="p-8 space-y-8">
      <h3 className="text-lg font-bold text-slate-900">版本資訊</h3>

      <section>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Frontend</h4>
        <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {[
            { label: 'Version', value: BUILD_INFO.version },
            { label: 'Commit', value: BUILD_INFO.commit, mono: true },
            { label: 'Build Time', value: BUILD_INFO.buildTime, small: true },
          ].map(item => (
            <div key={item.label} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{item.label}</p>
              <p className={cn("font-bold text-slate-900", item.mono && "font-mono", item.small ? "text-sm" : "text-lg")}>{item.value}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Backend</h4>
        {loading ? (
          <div className="flex items-center gap-3 p-6 rounded-2xl bg-slate-50 border border-slate-100">
            <Loader2 className="h-5 w-5 text-slate-400 animate-spin" />
            <span className="text-sm text-slate-500">Loading backend info...</span>
          </div>
        ) : error ? (
          <div className="flex items-center gap-3 p-6 rounded-2xl bg-rose-50 border border-rose-100">
            <XCircle className="h-5 w-5 text-rose-500" />
            <span className="text-sm text-rose-700">Unable to connect to backend API</span>
            <button onClick={fetchVersion} className="ml-auto text-xs font-bold text-rose-600 hover:text-rose-800 transition-colors">Retry</button>
          </div>
        ) : versionInfo ? (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {[
              { label: 'Version', value: versionInfo.backend_version },
              { label: 'Commit', value: versionInfo.backend_commit, mono: true },
              { label: 'Python', value: versionInfo.python_version },
              { label: 'Alembic Head', value: versionInfo.alembic_head, mono: true },
              { label: 'Environment', value: versionInfo.environment, badge: true },
              { label: 'Deployed At', value: versionInfo.deployed_at, small: true },
            ].map(item => (
              <div key={item.label} className="p-5 rounded-2xl bg-slate-50 border border-slate-100">
                <p className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1">{item.label}</p>
                {item.badge ? (
                  <span className={cn("inline-block text-xs font-bold px-2.5 py-1 rounded-lg uppercase tracking-wider mt-1", item.value === 'production' ? "bg-emerald-100 text-emerald-700" : "bg-amber-100 text-amber-700")}>
                    {item.value}
                  </span>
                ) : (
                  <p className={cn("font-bold text-slate-900", item.mono && "font-mono", item.small ? "text-sm" : "text-lg")}>{item.value}</p>
                )}
              </div>
            ))}
          </div>
        ) : null}
      </section>

      <section>
        <h4 className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-4">Connection Status</h4>
        <div className="grid sm:grid-cols-2 gap-4">
          <div className="p-5 rounded-2xl bg-slate-50 border border-slate-100 flex items-center gap-3">
            {versionInfo ? <CheckCircle className="h-5 w-5 text-emerald-500 shrink-0" /> : <XCircle className="h-5 w-5 text-rose-500 shrink-0" />}
            <div>
              <p className="text-xs font-bold text-slate-400 uppercase tracking-wider">Database</p>
              <p className="text-sm font-bold text-slate-900">{versionInfo ? 'Connected' : 'Unreachable'}</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
