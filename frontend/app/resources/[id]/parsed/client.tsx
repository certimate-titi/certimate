'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Loader2 } from 'lucide-react';

export default function ParsedClient() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/knowledge');
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <Loader2 className="h-6 w-6 animate-spin text-emerald-500 mx-auto mb-2" />
        <p className="text-sm text-slate-500">學習鷹架已整合至知識地圖，正在前往...</p>
      </div>
    </div>
  );
}
