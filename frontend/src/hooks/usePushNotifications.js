// React Hook for Push Notifications - יהל Naval System
import { useState, useEffect, useCallback } from 'react';
import pushNotificationService from '../services/pushNotificationService';

const usePushNotifications = (userId) => {
  const [isSupported, setIsSupported] = useState(false);
  const [permission, setPermission] = useState('default');
  const [subscription, setSubscription] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [isInitialized, setIsInitialized] = useState(false);
  const [preferences, setPreferences] = useState(null);
  const [categories, setCategories] = useState({});

  // Initialize the service
  useEffect(() => {
    const initializeService = async () => {
      try {
        setIsLoading(true);
        setError(null);
        
        const supported = pushNotificationService.isSupported();
        setIsSupported(supported);
        
        if (supported) {
          await pushNotificationService.initialize();
          setPermission(pushNotificationService.getPermissionStatus());
          
          const currentSubscription = await pushNotificationService.getSubscription();
          setSubscription(currentSubscription);

          // Load categories
          const categoriesData = await pushNotificationService.getNotificationCategories();
          setCategories(categoriesData.categories || {});

          // Load user preferences if userId is provided
          if (userId) {
            try {
              const userPrefs = await pushNotificationService.getUserPreferences(userId);
              setPreferences(userPrefs);
            } catch (err) {
              console.log('No existing preferences found, will create defaults');
            }
          }
        }
        
        setIsInitialized(true);
      } catch (err) {
        setError(err.message);
        console.error('Failed to initialize push notifications:', err);
        setIsInitialized(true); // Still mark as initialized even with error
      } finally {
        setIsLoading(false);
      } 
    };

    initializeService();
  }, [userId]);

  // Subscribe to notifications
  const subscribe = useCallback(async () => {
    if (!userId) {
      setError('User ID is required for subscription');
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const newSubscription = await pushNotificationService.subscribe(userId);
      setSubscription(newSubscription);
      setPermission('granted');
      
      // Create default preferences if they don't exist
      if (!preferences) {
        const defaultPrefs = {
          user_id: userId,
          categories: {
            urgent_failures: true,
            maintenance_reminders: true,
            jessica_updates: true,
            system_status: false
          },
          quiet_hours_enabled: false,
          language_code: 'he',
          rtl_support: true
        };
        
        await pushNotificationService.updateUserPreferences(userId, defaultPrefs);
        setPreferences(defaultPrefs);
      }
      
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Subscription failed:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [userId, preferences]);

  // Unsubscribe from notifications
  const unsubscribe = useCallback(async () => {
    if (!userId) {
      setError('User ID is required for unsubscription');
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      await pushNotificationService.unsubscribe(userId);
      setSubscription(null);
      
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Unsubscribe failed:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Send test notification
  const sendTestNotification = useCallback(async () => {
    if (!userId || !subscription) {
      setError('User must be subscribed to send test notifications');
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const result = await pushNotificationService.sendTestNotification(userId);
      console.log('Test notification result:', result);
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Test notification failed:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [userId, subscription]);

  // Update preferences
  const updatePreferences = useCallback(async (newPreferences) => {
    if (!userId) {
      setError('User ID is required to update preferences');
      return false;
    }

    try {
      setIsLoading(true);
      setError(null);
      
      const result = await pushNotificationService.updateUserPreferences(userId, {
        ...newPreferences,
        user_id: userId
      });
      
      setPreferences(result.preferences);
      return true;
    } catch (err) {
      setError(err.message);
      console.error('Failed to update preferences:', err);
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [userId]);

  // Refresh preferences
  const refreshPreferences = useCallback(async () => {
    if (!userId) return;

    try {
      const userPrefs = await pushNotificationService.getUserPreferences(userId);
      setPreferences(userPrefs);
    } catch (err) {
      console.error('Failed to refresh preferences:', err);
    }
  }, [userId]);

  // Get notification history
  const getNotificationHistory = useCallback(async (limit = 50) => {
    if (!userId) {
      setError('User ID is required to get notification history');
      return [];
    }

    try {
      const result = await pushNotificationService.getNotificationHistory(userId, limit);
      return result.history || [];
    } catch (err) {
      setError(err.message);
      console.error('Failed to get notification history:', err);
      return [];
    }
  }, [userId]);

  // Clear error
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // Send system notifications (for admin use)
  const sendFailureAlert = useCallback(async (failureData) => {
    try {
      return await pushNotificationService.sendFailureAlert(failureData);
    } catch (err) {
      console.error('Failed to send failure alert:', err);
      return false;
    }
  }, []);

  const sendMaintenanceReminder = useCallback(async (maintenanceData) => {
    try {
      return await pushNotificationService.sendMaintenanceReminder(maintenanceData);
    } catch (err) {
      console.error('Failed to send maintenance reminder:', err);
      return false;
    }
  }, []);

  const sendJessicaUpdate = useCallback(async (message) => {
    try {
      return await pushNotificationService.sendJessicaUpdate(message);
    } catch (err) {
      console.error('Failed to send Jessica update:', err);
      return false;
    }
  }, []);

  return {
    // Status
    isSupported,
    permission,
    subscription,
    isSubscribed: !!subscription,
    isLoading,
    error,
    isInitialized,
    
    // User data
    preferences,
    categories,
    
    // Actions
    subscribe,
    unsubscribe,
    sendTestNotification,
    updatePreferences,
    refreshPreferences,
    getNotificationHistory,
    clearError,
    
    // System notifications
    sendFailureAlert,
    sendMaintenanceReminder,
    sendJessicaUpdate
  };
};

export default usePushNotifications;