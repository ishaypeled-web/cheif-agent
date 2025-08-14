// Push Notification Service for יהל Naval System
class PushNotificationService {
  constructor() {
    this.serviceWorkerRegistration = null;
    this.vapidPublicKey = null;
    this.apiBaseUrl = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
  }

  // Initialize service and get VAPID key
  async initialize() {
    try {
      if ('serviceWorker' in navigator) {
        // Register service worker
        this.serviceWorkerRegistration = await navigator.serviceWorker.register('/sw.js', {
          scope: '/'
        });
        
        console.log('Service Worker registered:', this.serviceWorkerRegistration.scope);
        
        // Wait for service worker to be ready
        await navigator.serviceWorker.ready;
        
        // Get VAPID public key from server
        const response = await fetch(`${this.apiBaseUrl}/api/notifications/vapid-key`);
        const data = await response.json();
        this.vapidPublicKey = data.public_key;
        
        console.log('Push notification service initialized successfully');
        return true;
      } else {
        throw new Error('Service Workers not supported');
      }
    } catch (error) {
      console.error('Failed to initialize push notification service:', error);
      throw error;
    }
  }

  // Check if push notifications are supported
  isSupported() {
    return 'serviceWorker' in navigator && 
           'PushManager' in window && 
           'Notification' in window;
  }

  // Get current permission status
  getPermissionStatus() {
    if (!this.isSupported()) {
      return 'unsupported';
    }
    return Notification.permission;
  }

  // Request notification permission
  async requestPermission() {
    if (!this.isSupported()) {
      throw new Error('Push notifications not supported');
    }

    const permission = await Notification.requestPermission();
    
    if (permission === 'granted') {
      console.log('Notification permission granted');
      return true;
    } else if (permission === 'denied') {
      throw new Error('Notification permission denied');
    } else {
      throw new Error('Notification permission dismissed');
    }
  }

  // Convert VAPID key for subscription
  urlBase64ToUint8Array(base64String) {
    const padding = '='.repeat((4 - base64String.length % 4) % 4);
    const base64 = (base64String + padding)
      .replace(/-/g, '+')
      .replace(/_/g, '/');

    const rawData = window.atob(base64);
    const outputArray = new Uint8Array(rawData.length);

    for (let i = 0; i < rawData.length; ++i) {
      outputArray[i] = rawData.charCodeAt(i);
    }
    return outputArray;
  }

  // Subscribe to push notifications
  async subscribe(userId) {
    try {
      if (!this.serviceWorkerRegistration) {
        await this.initialize();
      }

      // Check permission
      if (Notification.permission !== 'granted') {
        await this.requestPermission();
      }

      // Get push subscription
      const subscription = await this.serviceWorkerRegistration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: this.urlBase64ToUint8Array(this.vapidPublicKey)
      });

      // Send subscription to server
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/subscribe`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: userId,
          subscription: {
            endpoint: subscription.endpoint,
            keys: {
              p256dh: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('p256dh')))),
              auth: btoa(String.fromCharCode.apply(null, new Uint8Array(subscription.getKey('auth'))))
            }
          }
        })
      });

      if (!response.ok) {
        throw new Error(`Subscription failed: ${response.statusText}`);
      }

      const result = await response.json();
      console.log('Successfully subscribed to push notifications:', result);
      
      return subscription;
    } catch (error) {
      console.error('Failed to subscribe to push notifications:', error);
      throw error;
    }
  }

  // Unsubscribe from push notifications
  async unsubscribe(userId) {
    try {
      if (this.serviceWorkerRegistration) {
        const subscription = await this.serviceWorkerRegistration.pushManager.getSubscription();
        
        if (subscription) {
          // Unsubscribe from browser
          await subscription.unsubscribe();
          
          // Notify server
          await fetch(`${this.apiBaseUrl}/api/notifications/unsubscribe?user_id=${userId}&endpoint=${encodeURIComponent(subscription.endpoint)}`, {
            method: 'POST'
          });
          
          console.log('Successfully unsubscribed from push notifications');
          return true;
        }
      }
      return false;
    } catch (error) {
      console.error('Failed to unsubscribe from push notifications:', error);
      throw error;
    }
  }

  // Get current subscription status
  async getSubscription() {
    try {
      if (this.serviceWorkerRegistration) {
        return await this.serviceWorkerRegistration.pushManager.getSubscription();
      }
      return null;
    } catch (error) {
      console.error('Failed to get subscription:', error);
      return null;
    }
  }

  // Send test notification
  async sendTestNotification(userId) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/test?user_id=${userId}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      if (!response.ok) {
        throw new Error(`Test notification failed: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to send test notification:', error);
      throw error;
    }
  }

  // Get user preferences
  async getUserPreferences(userId) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/preferences/${userId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get preferences: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get user preferences:', error);
      throw error;
    }
  }

  // Update user preferences
  async updateUserPreferences(userId, preferences) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/preferences/${userId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(preferences)
      });

      if (!response.ok) {
        throw new Error(`Failed to update preferences: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Failed to update user preferences:', error);
      throw error;
    }
  }

  // Get notification categories
  async getNotificationCategories() {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/categories`);
      
      if (!response.ok) {
        throw new Error(`Failed to get categories: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get notification categories:', error);
      throw error;
    }
  }

  // Get notification history
  async getNotificationHistory(userId, limit = 50) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/history/${userId}?limit=${limit}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get history: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('Failed to get notification history:', error);
      throw error;
    }
  }

  // Send notification from failure alert
  async sendFailureAlert(failureData) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'system', // Broadcast to all users
          title: `🚨 כשל דחוף: ${failureData.system}`,
          body: `תקלה ${failureData.failure_number} - ${failureData.description}`,
          category: 'urgent_failures',
          urgent: true,
          data: {
            url: '/?tab=failures',
            failure_id: failureData.id,
            type: 'failure_alert'
          }
        })
      });

      return await response.json();
    } catch (error) {
      console.error('Failed to send failure alert:', error);
      throw error;
    }
  }

  // Send maintenance reminder
  async sendMaintenanceReminder(maintenanceData) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'system', // Broadcast to all users
          title: `🔧 תזכורת תחזוקה: ${maintenanceData.component}`,
          body: `תחזוקה מתוכננת ${maintenanceData.maintenance_type} - ${maintenanceData.description}`,
          category: 'maintenance_reminders',
          urgent: false,
          data: {
            url: '/?tab=maintenance',
            maintenance_id: maintenanceData.id,
            type: 'maintenance_reminder'
          }
        })
      });

      return await response.json();
    } catch (error) {
      console.error('Failed to send maintenance reminder:', error);
      throw error;
    }
  }

  // Send Jessica AI update
  async sendJessicaUpdate(message) {
    try {
      const response = await fetch(`${this.apiBaseUrl}/api/notifications/send`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: 'system', // Broadcast to all users
          title: '💬 הודעה מג\'סיקה',
          body: message,
          category: 'jessica_updates',
          urgent: false,
          data: {
            url: '/?tab=ai-agent',
            type: 'jessica_update'
          }
        })
      });

      return await response.json();
    } catch (error) {
      console.error('Failed to send Jessica update:', error);
      throw error;
    }
  }
}

export default new PushNotificationService();