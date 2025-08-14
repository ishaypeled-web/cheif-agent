// Service Worker for Push Notifications - יהל Naval System
const CACHE_NAME = 'yahel-push-notifications-v1';
const urlsToCache = [
  '/',
  '/static/js/bundle.js',
  '/static/css/main.css',
  '/icons/notification-icon.png',
  '/icons/badge-icon.png'
];

// Service Worker Installation
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching app shell');
        return cache.addAll(urlsToCache);
      })
  );
  self.skipWaiting();
});

// Service Worker Activation  
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== CACHE_NAME) {
            console.log('[Service Worker] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  self.clients.claim();
});

// Push Event Handler
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push Received:', event);
  
  let notificationData = {};
  
  if (event.data) {
    try {
      notificationData = event.data.json();
    } catch (error) {
      console.error('[Service Worker] Error parsing push data:', error);
      notificationData = {
        title: 'התרעה חדשה',
        body: 'יש לך הודעה חדשה במערכת יהל'
      };
    }
  }
  
  const title = notificationData.title || 'התרעה חדשה';
  const options = {
    body: notificationData.body || 'יש לך הודעה חדשה במערכת יהל',
    icon: notificationData.icon || '/icons/notification-icon.png',
    badge: notificationData.badge || '/icons/badge-icon.png',
    data: notificationData.data || {},
    tag: notificationData.category || 'general',
    requireInteraction: notificationData.category === 'urgent_failures',
    dir: notificationData.rtl ? 'rtl' : 'ltr',
    lang: notificationData.lang || 'he',
    vibrate: notificationData.category === 'urgent_failures' ? [200, 100, 200, 100, 200] : [100, 50, 100],
    actions: [
      {
        action: 'view',
        title: notificationData.rtl ? 'צפייה' : 'View',
        icon: '/icons/view-icon.png'
      },
      {
        action: 'dismiss',
        title: notificationData.rtl ? 'סגירה' : 'Dismiss',
        icon: '/icons/dismiss-icon.png'
      }
    ]
  };
  
  // Add different styling based on category
  if (notificationData.category === 'urgent_failures') {
    options.requireInteraction = true;
    options.silent = false;
  } else if (notificationData.category === 'maintenance_reminders') {
    options.tag = 'maintenance';
    options.renotify = true;
  }
  
  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

// Notification Click Handler
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification Click:', event);
  
  event.notification.close();
  
  if (event.action === 'dismiss') {
    return;
  }
  
  // Determine URL to open based on notification data
  let urlToOpen = '/';
  
  if (event.notification.data.url) {
    urlToOpen = event.notification.data.url;
  } else if (event.notification.data.category) {
    // Map categories to specific app sections
    const categoryUrls = {
      'urgent_failures': '/?tab=failures',
      'maintenance_reminders': '/?tab=maintenance', 
      'jessica_updates': '/?tab=ai-agent',
      'system_status': '/?tab=dashboard'
    };
    urlToOpen = categoryUrls[event.notification.data.category] || '/';
  }
  
  event.waitUntil(
    clients.matchAll({
      type: 'window',
      includeUncontrolled: true
    }).then((clientList) => {
      // Try to focus existing window
      for (const client of clientList) {
        if (client.url.includes(self.location.origin) && 'navigate' in client) {
          client.navigate(urlToOpen);
          return client.focus();
        }
      }
      // Open new window if no existing window found
      if (clients.openWindow) {
        return clients.openWindow(urlToOpen);
      }
    })
  );
});

// Notification Close Handler
self.addEventListener('notificationclose', (event) => {
  console.log('[Service Worker] Notification Closed:', event.notification.tag);
  // Could send analytics data here
});

// Background Message Handler (for data-only messages)
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message Received:', event.data);
  
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});

// Background Sync (future enhancement)
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background Sync:', event.tag);
  
  if (event.tag === 'notification-sync') {
    event.waitUntil(
      // Could sync pending notifications here
      Promise.resolve()
    );
  }
});

// Error Handler
self.addEventListener('error', (event) => {
  console.error('[Service Worker] Error:', event.error);
});

console.log('[Service Worker] יהל Naval System Service Worker loaded successfully');