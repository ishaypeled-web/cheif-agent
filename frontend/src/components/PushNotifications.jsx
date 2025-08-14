// Push Notifications Management Component - יהל Naval System
import React, { useState, useEffect } from 'react';
import usePushNotifications from '../hooks/usePushNotifications';
import { Card, CardHeader, CardTitle, CardContent } from './ui/card';
import { Button } from './ui/button';
import { AlertCircle, CheckCircle, Bell, BellOff, Settings, Send, History } from 'lucide-react';

const PushNotifications = ({ userId = 'yahel-user' }) => {
  const {
    isSupported,
    permission,
    isSubscribed,
    isLoading,
    error,
    isInitialized,
    preferences,
    categories,
    subscribe,
    unsubscribe,
    sendTestNotification,
    updatePreferences,
    refreshPreferences,
    getNotificationHistory,
    clearError
  } = usePushNotifications(userId);

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [localPreferences, setLocalPreferences] = useState(null);
  const [hasChanges, setHasChanges] = useState(false);
  const [notificationHistory, setNotificationHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(false);

  // Sync local preferences with hook preferences
  useEffect(() => {
    if (preferences && !localPreferences) {
      setLocalPreferences(preferences);
    }
  }, [preferences, localPreferences]);

  // Check for changes
  useEffect(() => {
    if (localPreferences && preferences) {
      const changed = JSON.stringify(localPreferences) !== JSON.stringify(preferences);
      setHasChanges(changed);
    }
  }, [localPreferences, preferences]);

  // Load notification history
  const loadHistory = async () => {
    const history = await getNotificationHistory(20);
    setNotificationHistory(history);
    setShowHistory(true);
  };

  const handleSubscriptionToggle = async () => {
    if (isSubscribed) {
      const success = await unsubscribe();
      if (success) {
        alert('התראות הושבתו בהצלחה');
      }
    } else {
      const success = await subscribe();
      if (success) {
        alert('התראות הופעלו בהצלחה! אתה תקבל התראות על כשלים דחופים ותזכורות תחזוקה.');
      }
    }
  };

  const handleTestNotification = async () => {
    const success = await sendTestNotification();
    if (success) {
      alert('התראת בדיקה נשלחה! בדוק את ההתרעות שלך.');
    }
  };

  const handleCategoryChange = (categoryKey, enabled) => {
    setLocalPreferences(prev => ({
      ...prev,
      categories: {
        ...prev.categories,
        [categoryKey]: enabled
      }
    }));
  };

  const handleQuietHoursToggle = (enabled) => {
    setLocalPreferences(prev => ({
      ...prev,
      quiet_hours_enabled: enabled,
      quiet_hours_start: enabled ? prev.quiet_hours_start || '22:00' : null,
      quiet_hours_end: enabled ? prev.quiet_hours_end || '07:00' : null
    }));
  };

  const handleQuietHoursChange = (field, value) => {
    setLocalPreferences(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleSavePreferences = async () => {
    const success = await updatePreferences(localPreferences);
    if (success) {
      setHasChanges(false);
      alert('העדפות נשמרו בהצלחה!');
    }
  };

  const handleResetPreferences = () => {
    setLocalPreferences(preferences);
    setHasChanges(false);
  };

  if (!isInitialized) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">טוען הגדרות התראות...</p>
        </div>
      </div>
    );
  }

  if (!isSupported) {
    return (
      <Card>
        <CardContent className="text-center py-8">
          <AlertCircle className="h-12 w-12 text-yellow-500 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">התראות לא נתמכות</h3>
          <p className="text-gray-600 mb-4">
            הדפדפן שלך אינו תומך בהתראות דחיפה. אנא עדכן את הדפדפן או השתמש בדפדפן אחר.
          </p>
          <div className="bg-yellow-50 p-4 rounded-lg">
            <p className="text-sm text-yellow-800">
              מומלץ: Chrome, Firefox, Safari (גרסאות מעודכנות)
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6" dir="rtl">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">התראות דחיפה</h2>
          <p className="text-gray-600">
            קבל התראות על כשלים דחופים, תזכורות תחזוקה ועדכונים חשובים מג'סיקה
          </p>
        </div>
        <div className="flex items-center space-x-2 space-x-reverse">
          {isSubscribed ? (
            <span className="flex items-center text-green-600 text-sm">
              <CheckCircle className="h-4 w-4 ml-1" />
              פעיל
            </span>
          ) : (
            <span className="flex items-center text-gray-500 text-sm">
              <BellOff className="h-4 w-4 ml-1" />
              לא פעיל
            </span>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-center">
            <AlertCircle className="h-5 w-5 text-red-500 ml-2" />
            <span className="text-red-800">{error}</span>
            <Button 
              onClick={clearError} 
              variant="ghost" 
              size="sm" 
              className="mr-auto text-red-600 hover:text-red-800"
            >
              ✕
            </Button>
          </div>
        </div>
      )}

      {/* Main Control Panel */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center">
            <Bell className="h-5 w-5 ml-2" />
            בקרת התראות
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="font-medium">סטטוס הרשאות:</h4>
              <p className="text-sm text-gray-600">
                {permission === 'granted' && 'מאושר - אתה תקבל התראות'}
                {permission === 'denied' && 'נדחה - התראות חסומות'}
                {permission === 'default' && 'לא נבחר - יש לאשר הרשאות'}
              </p>
            </div>
            <div className={`px-3 py-1 rounded-full text-sm font-medium ${
              permission === 'granted' ? 'bg-green-100 text-green-800' :
              permission === 'denied' ? 'bg-red-100 text-red-800' :
              'bg-gray-100 text-gray-700'
            }`}>
              {permission === 'granted' && 'מאושר'}
              {permission === 'denied' && 'נדחה'}
              {permission === 'default' && 'ממתין'}
            </div>
          </div>

          <div className="flex space-x-3 space-x-reverse">
            <Button
              onClick={handleSubscriptionToggle}
              disabled={isLoading || permission === 'denied'}
              className={isSubscribed ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'}
            >
              {isLoading ? (
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white ml-2"></div>
              ) : isSubscribed ? (
                <BellOff className="h-4 w-4 ml-2" />
              ) : (
                <Bell className="h-4 w-4 ml-2" />
              )}
              {isSubscribed ? 'השבת התראות' : 'הפעל התראות'}
            </Button>

            {isSubscribed && (
              <Button
                onClick={handleTestNotification}
                disabled={isLoading}
                variant="outline"
              >
                <Send className="h-4 w-4 ml-2" />
                שלח התראת בדיקה
              </Button>
            )}

            <Button
              onClick={loadHistory}
              disabled={!isSubscribed}
              variant="outline"
            >
              <History className="h-4 w-4 ml-2" />
              היסטוריית התראות
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Advanced Settings */}
      {isSubscribed && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <Settings className="h-5 w-5 ml-2" />
                הגדרות מתקדמות
              </div>
              <Button
                onClick={() => setShowAdvanced(!showAdvanced)}
                variant="ghost"
                size="sm"
              >
                {showAdvanced ? '▲' : '▼'}
              </Button>
            </CardTitle>
          </CardHeader>
          
          {showAdvanced && localPreferences && (
            <CardContent className="space-y-6">
              {/* Categories */}
              <div>
                <h4 className="font-medium mb-3">קטגוריות התראות</h4>
                <div className="space-y-3">
                  {Object.entries(categories).map(([key, category]) => (
                    <div key={key} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div>
                        <h5 className="font-medium">{category.label_he}</h5>
                        <p className="text-sm text-gray-600">{category.description_he}</p>
                      </div>
                      <label className="relative inline-flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          className="sr-only peer"
                          checked={localPreferences.categories?.[key] ?? category.default_enabled}
                          onChange={(e) => handleCategoryChange(key, e.target.checked)}
                        />
                        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                      </label>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quiet Hours */}
              <div>
                <h4 className="font-medium mb-3">שעות שקט</h4>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input
                      type="checkbox"
                      checked={localPreferences.quiet_hours_enabled || false}
                      onChange={(e) => handleQuietHoursToggle(e.target.checked)}
                      className="rounded border-gray-300 text-blue-600 focus:ring-blue-500 ml-2"
                    />
                    <span>הפעל שעות שקט (לא יישלחו התראות בשעות אלו)</span>
                  </label>
                  
                  {localPreferences.quiet_hours_enabled && (
                    <div className="flex space-x-4 space-x-reverse mr-6">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          החל מהשעה:
                        </label>
                        <input
                          type="time"
                          value={localPreferences.quiet_hours_start || '22:00'}
                          onChange={(e) => handleQuietHoursChange('quiet_hours_start', e.target.value)}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">
                          עד השעה:
                        </label>
                        <input
                          type="time"
                          value={localPreferences.quiet_hours_end || '07:00'}
                          onChange={(e) => handleQuietHoursChange('quiet_hours_end', e.target.value)}
                          className="block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Save/Reset Buttons */}
              {hasChanges && (
                <div className="flex justify-between items-center pt-4 border-t">
                  <span className="text-sm text-amber-600">יש לך שינויים שלא נשמרו</span>
                  <div className="flex space-x-2 space-x-reverse">
                    <Button onClick={handleResetPreferences} variant="outline">
                      בטל שינויים
                    </Button>
                    <Button onClick={handleSavePreferences} disabled={isLoading}>
                      שמור הגדרות
                    </Button>
                  </div>
                </div>
              )}
            </CardContent>
          )}
        </Card>
      )}

      {/* Notification History Modal */}
      {showHistory && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <div className="flex items-center">
                <History className="h-5 w-5 ml-2" />
                היסטוריית התראות
              </div>
              <Button onClick={() => setShowHistory(false)} variant="ghost" size="sm">
                ✕
              </Button>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {notificationHistory.length > 0 ? (
              <div className="space-y-2 max-h-60 overflow-y-auto">
                {notificationHistory.map((notification, index) => (
                  <div key={index} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <div>
                      <div className="font-medium">{notification.title}</div>
                      <div className="text-sm text-gray-600">{notification.body}</div>
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(notification.delivery_timestamp).toLocaleDateString('he-IL')}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-4 text-gray-500">
                אין היסטוריה של התראות
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default PushNotifications;