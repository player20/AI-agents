import { useEffect, useState } from 'react';
import { WifiOff } from 'lucide-react';

export default function OfflineIndicator() {
  const [isOnline, setIsOnline] = useState(true);

  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  if (isOnline) return null;

  return (
    <div className="mb-6 flex items-center justify-center p-3 bg-destructive/10 border border-destructive/20 rounded-lg text-destructive animate-fade-in" role="alert">
      <WifiOff className="h-5 w-5 mr-2" />
      <span>You are offline. Some content may not be available.</span>
    </div>
  );
}