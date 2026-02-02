'use client';

import { useEffect, useState, createContext, useContext, ReactNode } from 'react';
import { 
  registerServiceWorker, 
  requestNotificationPermission,
  subscribeToPush,
  onConnectionChange,
  setupInstallPrompt,
  promptInstall,
  canInstall,
  isRunningAsPWA,
  isOnline as checkOnline
} from '@/lib/pwa';

interface PWAContextType {
  isOnline: boolean;
  canInstallPWA: boolean;
  isPWA: boolean;
  notificationPermission: NotificationPermission;
  installPWA: () => Promise<boolean>;
  enableNotifications: () => Promise<boolean>;
  updateAvailable: boolean;
  reloadForUpdate: () => void;
}

const PWAContext = createContext<PWAContextType>({
  isOnline: true,
  canInstallPWA: false,
  isPWA: false,
  notificationPermission: 'default',
  installPWA: async () => false,
  enableNotifications: async () => false,
  updateAvailable: false,
  reloadForUpdate: () => {}
});

export function usePWA() {
  return useContext(PWAContext);
}

interface PWAProviderProps {
  children: ReactNode;
}

export default function PWAProvider({ children }: PWAProviderProps) {
  const [isOnline, setIsOnline] = useState(true);
  const [canInstallPWA, setCanInstallPWA] = useState(false);
  const [isPWA, setIsPWA] = useState(false);
  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [swRegistration, setSwRegistration] = useState<ServiceWorkerRegistration | null>(null);

  useEffect(() => {
    // Initial states
    setIsOnline(checkOnline());
    setIsPWA(isRunningAsPWA());
    
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }

    // Service Worker kayıt
    registerServiceWorker().then((registration) => {
      if (registration) {
        setSwRegistration(registration);
      }
    });

    // Install prompt setup
    setupInstallPrompt();

    // Event listeners
    const unsubscribeConnection = onConnectionChange(setIsOnline);

    const handleInstallAvailable = () => setCanInstallPWA(true);
    const handleUpdateAvailable = () => setUpdateAvailable(true);

    window.addEventListener('pwa-install-available', handleInstallAvailable);
    window.addEventListener('sw-update-available', handleUpdateAvailable);

    return () => {
      unsubscribeConnection();
      window.removeEventListener('pwa-install-available', handleInstallAvailable);
      window.removeEventListener('sw-update-available', handleUpdateAvailable);
    };
  }, []);

  const installPWA = async (): Promise<boolean> => {
    const result = await promptInstall();
    if (result) {
      setCanInstallPWA(false);
    }
    return result;
  };

  const enableNotifications = async (): Promise<boolean> => {
    const permission = await requestNotificationPermission();
    setNotificationPermission(permission);
    
    if (permission === 'granted' && swRegistration) {
      await subscribeToPush(swRegistration);
      return true;
    }
    
    return false;
  };

  const reloadForUpdate = () => {
    if (swRegistration?.waiting) {
      swRegistration.waiting.postMessage({ type: 'SKIP_WAITING' });
    }
    window.location.reload();
  };

  return (
    <PWAContext.Provider value={{
      isOnline,
      canInstallPWA,
      isPWA,
      notificationPermission,
      installPWA,
      enableNotifications,
      updateAvailable,
      reloadForUpdate
    }}>
      {children}
    </PWAContext.Provider>
  );
}
