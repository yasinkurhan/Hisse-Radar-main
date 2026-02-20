'use client';

import { useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';

export default function StocksRedirectPage() {
  const params = useParams();
  const router = useRouter();
  const symbol = params.symbol as string;

  useEffect(() => {
    router.replace(`/stock/${symbol}`);
  }, [symbol, router]);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
    </div>
  );
}