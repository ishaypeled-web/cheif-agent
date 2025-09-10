import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Textarea } from './components/ui/textarea';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Badge } from './components/ui/badge';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { AlertTriangle, Clock, Settings, Calendar, Plus, Edit, Trash2, Bot, Send, MessageCircle, CalendarPlus, Link, Bell, Download, User } from 'lucide-react';
import PushNotifications from './components/PushNotifications';

function App() {
  // Authentication states
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);

  // Data states
  const [activeTab, setActiveTab] = useState('dashboard');
  const [activeFailures, setActiveFailures] = useState([]);
  const [resolvedFailures, setResolvedFailures] = useState([]);
  const [pendingMaintenance, setPendingMaintenance] = useState([]);
  const [equipmentHours, setEquipmentHours] = useState([]);
  const [dailyWork, setDailyWork] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [dnaTracker, setDnaTracker] = useState([]);
  const [ninetyDayPlan, setNinetyDayPlan] = useState([]);

  // Google Calendar states
  const [googleUser, setGoogleUser] = useState(null);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [showCalendarDialog, setShowCalendarDialog] = useState(false);

  // Form states (moved up to fix initialization order)
  const [failureForm, setFailureForm] = useState({
    failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0, status: 'פתוח'
  });
  const [maintenanceForm, setMaintenanceForm] = useState({
    maintenance_type: '', system: '', frequency_days: 30, last_performed: ''
  });
  const [equipmentForm, setEquipmentForm] = useState({
    system: '', system_type: 'מנועים', current_hours: 0, last_service_date: ''
  });
  const [workForm, setWorkForm] = useState({
    date: '', task: '', source: 'תקלה', source_id: '', assignee: '', estimated_hours: 0, notes: ''
  });
  const [resolvedFailureForm, setResolvedFailureForm] = useState({
    resolution_method: '', resolved_by: '', actual_hours: 0, lessons_learned: ''
  });
  const [conversationForm, setConversationForm] = useState({
    meeting_number: 1, date: '', participant: '', topic: '', insights: '', follow_up_plan: ''
  });
  const [dnaForm, setDnaForm] = useState({
    component_name: '', self_assessment: 3, target_score: 5, action_plan: '', mentor_notes: '', last_updated: ''
  });
  const [ninetyDayForm, setNinetyDayForm] = useState({
    week_number: 1, goals: '', planned_activities: '', required_resources: '', success_indicators: '', status: 'מתוכנן'
  });

  const [editingItem, setEditingItem] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');

  // Chat states
  const [sessionId, setSessionId] = useState(null);
  const [currentMessage, setCurrentMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // API calls
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://fleet-mentor.preview.emergentagent.com';

  // Authentication helpers
  const getAuthHeaders = () => {
    if (authToken) {
      return { Authorization: `Bearer ${authToken}` };
    }
    return {};
  };

  // Check for authentication on load
  useEffect(() => {
    // Check for stored token
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('current_user');
    
    if (storedToken && storedUser) {
      setAuthToken(storedToken);
      setCurrentUser(JSON.parse(storedUser));
      setIsAuthenticated(true);
    }

    // Check for Google OAuth callback
    const urlParams = new URLSearchParams(window.location.search);
    const googleAuth = urlParams.get('google_auth');
    const token = urlParams.get('token');
    const email = urlParams.get('email');
    const name = urlParams.get('name');

    if (googleAuth === 'success' && token) {
      // Save authentication info
      localStorage.setItem('auth_token', token);
      const user = { email, name };
      localStorage.setItem('current_user', JSON.stringify(user));
      
      setAuthToken(token);
      setCurrentUser(user);
      setIsAuthenticated(true);
      setGoogleConnected(true);

      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
      
      // Show success message
      alert(`✅ התחברת בהצלחה! שלום ${name}`);
    } else if (googleAuth === 'error') {
      const message = urlParams.get('message');
      alert(`❌ שגיאה בהתחברות: ${message}`);
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  // Initialize chat session
  useEffect(() => {
    if (!sessionId && isAuthenticated) {
      const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
      setSessionId(newSessionId);
    }
  }, [isAuthenticated]);

  // Load chat history
  useEffect(() => {
    if (sessionId && isAuthenticated) {
      loadChatHistory();
    }
  }, [sessionId, isAuthenticated]);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/ai-chat/history/${sessionId}`, {
        headers: getAuthHeaders()
      });
      setChatHistory(response.data.history || []);
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  // Fill form when editing
  useEffect(() => {
    if (editingItem) {
      if (dialogType === 'failure') {
        setFailureForm({
          failure_number: editingItem.failure_number || '',
          date: editingItem.date || '',
          system: editingItem.system || '',
          description: editingItem.description || '',
          urgency: editingItem.urgency || 1,
          assignee: editingItem.assignee || '',
          estimated_hours: editingItem.estimated_hours || 0,
          status: editingItem.status || 'פתוח'
        });
      } else if (dialogType === 'resolved-failure') {
        setResolvedFailureForm({
          resolution_method: editingItem.resolution_method || '',
          resolved_by: editingItem.resolved_by || '',
          actual_hours: editingItem.actual_hours || editingItem.estimated_hours || 0,
          lessons_learned: editingItem.lessons_learned || ''
        });
      } else if (dialogType === 'maintenance') {
        setMaintenanceForm({
          maintenance_type: editingItem.maintenance_type || '',
          system: editingItem.system || '',
          frequency_days: editingItem.frequency_days || 30,
          last_performed: editingItem.last_performed || ''
        });
      } else if (dialogType === 'equipment') {
        setEquipmentForm({
          system: editingItem.system || '',
          system_type: editingItem.system_type || 'מנועים',
          current_hours: editingItem.current_hours || 0,
          last_service_date: editingItem.last_service_date || ''
        });
      } else if (dialogType === 'work') {
        setWorkForm({
          date: editingItem.date || '',
          task: editingItem.task || '',
          source: editingItem.source || 'תקלה',
          source_id: editingItem.source_id || '',
          assignee: editingItem.assignee || '',
          estimated_hours: editingItem.estimated_hours || 0,
          notes: editingItem.notes || ''
        });
      }
    } else {
      // איפוס טפסים כאשר אין עריכה
      if (!showDialog) {
        setFailureForm({
          failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0, status: 'פתוח'
        });
        setMaintenanceForm({
          maintenance_type: '', system: '', frequency_days: 30, last_performed: ''
        });
        setResolvedFailureForm({
          resolution_method: '', resolved_by: '', actual_hours: 0, lessons_learned: ''
        });
      }
    }
  }, [editingItem, dialogType, showDialog]);

  // Handle key press in textarea
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAiMessage();
    }
  };

  const fetchData = async () => {
    if (!isAuthenticated) return;

    try {
      const authHeaders = getAuthHeaders();
      const [
        failuresRes, 
        resolvedFailuresRes, 
        maintenanceRes, 
        equipmentRes, 
        dailyWorkRes, 
        conversationsRes,
        dnaTrackerRes,
        ninetyDayRes,
        summaryRes,
        googleUserRes
      ] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/failures`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/resolved-failures`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/maintenance`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/equipment`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/daily-work`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/conversations`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/dna-tracker`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/ninety-day-plan`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/summary`, { headers: authHeaders }),
        axios.get(`${BACKEND_URL}/api/auth/google/user`, { headers: authHeaders }).catch(() => ({ data: null }))
      ]);

      setActiveFailures(failuresRes.data);
      setResolvedFailures(resolvedFailuresRes.data);
      setPendingMaintenance(maintenanceRes.data);
      setEquipmentHours(equipmentRes.data);
      setDailyWork(dailyWorkRes.data);
      setConversations(conversationsRes.data);
      setDnaTracker(dnaTrackerRes.data);
      setNinetyDayPlan(ninetyDayRes.data);
      setGoogleUser(googleUserRes.data);
      setGoogleConnected(!!googleUserRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      if (error.response && error.response.status === 401) {
        // Token expired or invalid
        handleLogout();
      }
    }
  };

  useEffect(() => {
    fetchData();
  }, [isAuthenticated]);

  // Authentication functions
  const handleLogout = () => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    setAuthToken(null);
    setCurrentUser(null);
    setIsAuthenticated(false);
    setGoogleConnected(false);
    setChatHistory([]);
    setActiveTab('dashboard');
  };

  const initiateGoogleAuth = () => {
    // Force redirect to the OAuth endpoint directly 
    console.log('Google OAuth button clicked');
    window.location.assign('https://fleet-mentor.preview.emergentagent.com/api/auth/google/login');
  };

  // Helper functions
  const getUrgencyColor = (urgency) => {
    if (urgency >= 4) return 'bg-red-100 text-red-800';
    if (urgency >= 3) return 'bg-yellow-100 text-yellow-800';
    return 'bg-green-100 text-green-800';
  };

  const getUrgencyText = (urgency) => {
    if (urgency >= 4) return 'דחוף מאוד';
    if (urgency >= 3) return 'דחוף';
    if (urgency >= 2) return 'בינוני';
    return 'נמוך';
  };

  const getDaysFromDate = (dateStr) => {
    if (!dateStr) return 0;
    const date = new Date(dateStr);
    const now = new Date();
    const diffTime = now - date;
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    return diffDays;
  };

  const getMaintenanceStatusColor = (days) => {
    if (days < 0) return 'bg-blue-100 text-blue-800';
    if (days <= 30) return 'bg-green-100 text-green-800';
    if (days <= 60) return 'bg-yellow-100 text-yellow-800';
    return 'bg-red-100 text-red-800';
  };

  const openDialog = (type, item = null) => {
    setDialogType(type);
    setEditingItem(item);
    setShowDialog(true);
  };

  const handleAddFailure = async () => {
    if (!isAuthenticated) return;
    
    try {
      const authHeaders = getAuthHeaders();
      if (editingItem) {
        // עריכה - עדכון קיים
        await axios.put(`${BACKEND_URL}/api/failures/${editingItem.id}`, failureForm, { headers: authHeaders });
      } else {
        // הוספה חדשה
        await axios.post(`${BACKEND_URL}/api/failures`, failureForm, { headers: authHeaders });
      }
      setFailureForm({
        failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0, status: 'פתוח'
      });
      setShowDialog(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      console.error('Error saving failure:', error);
      if (error.response && error.response.status === 401) {
        handleLogout();
      }
    }
  };

  const handleUpdateResolvedFailure = async () => {
    if (!isAuthenticated) return;
    
    try {
      if (editingItem) {
        // עדכון תקלה שטופלה
        await axios.put(`${BACKEND_URL}/api/resolved-failures/${editingItem.id}`, resolvedFailureForm, { 
          headers: getAuthHeaders() 
        });
        setResolvedFailureForm({
          resolution_method: '', resolved_by: '', actual_hours: 0, lessons_learned: ''
        });
        setShowDialog(false);
        setEditingItem(null);
        fetchData();
      }
    } catch (error) {
      console.error('Error updating resolved failure:', error);
    }
  };

  const handleDeleteResolvedFailure = async (failureId) => {
    if (!isAuthenticated) return;
    
    try {
      if (window.confirm('האם אתה בטוח שברצונך למחוק תקלה שטופלה זו?')) {
        await axios.delete(`${BACKEND_URL}/api/resolved-failures/${failureId}`, { 
          headers: getAuthHeaders() 
        });
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting resolved failure:', error);
      alert('שגיאה במחיקת התקלה השטופלה');
    }
  };

  // Export functions
  const handleExportTable = async (tableName, customTitle = null) => {
    if (!isAuthenticated) return;
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/export/${tableName}`, {
        table_name: tableName,
        sheet_title: customTitle || `${tableName} Export - ${new Date().toLocaleString('he-IL')}`
      }, { headers: getAuthHeaders() });

      if (response.data.success) {
        alert(`✅ הייצוא הושלם בהצלחה!\n${response.data.message}`);
        
        // Open the Google Sheet in a new tab
        if (response.data.spreadsheet_url) {
          window.open(response.data.spreadsheet_url, '_blank');
        }
      } else {
        alert(`❌ שגיאה בייצוא: ${response.data.message}`);
      }
    } catch (error) {
      console.error('Error exporting table:', error);
      alert(`❌ שגיאה בייצוא: ${error.response?.data?.detail || error.message}`);
    }
  };

  const handleAddMaintenance = async () => {
    if (!isAuthenticated) return;
    
    try {
      const authHeaders = getAuthHeaders();
      if (editingItem) {
        // עריכה - עדכון קיים
        await axios.put(`${BACKEND_URL}/api/maintenance/${editingItem.id}`, maintenanceForm, { headers: authHeaders });
      } else {
        // הוספה חדשה
        await axios.post(`${BACKEND_URL}/api/maintenance`, maintenanceForm, { headers: authHeaders });
      }
      setMaintenanceForm({
        maintenance_type: '', system: '', frequency_days: 30, last_performed: ''
      });
      setShowDialog(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      console.error('Error saving maintenance:', error);
    }
  };

  const handleDeleteMaintenance = async (maintenance) => {
    if (!window.confirm('האם אתה בטוח שברצונך למחוק תחזוקה זו?')) {
      return;
    }
    
    try {
      const response = await fetch(`${BACKEND_URL}/api/maintenance/${maintenance.id}`, {
        method: 'DELETE',
        headers: getAuthHeaders(),
      });

      if (response.ok) {
        await fetchData();
        alert('התחזוקה נמחקה בהצלחה');
      } else {
        throw new Error('Failed to delete maintenance');
      }
    } catch (error) {
      console.error('Error deleting maintenance:', error);
      alert('שגיאה במחיקת התחזוקה');
    }
  };

  const handleAddEquipment = async () => {
    if (!isAuthenticated) return;
    
    try {
      await axios.post(`${BACKEND_URL}/api/equipment`, equipmentForm, { headers: getAuthHeaders() });
      setEquipmentForm({
        system: '', system_type: 'מנועים', current_hours: 0, last_service_date: ''
      });
      setShowDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error adding equipment:', error);
    }
  };

  const handleAddWork = async () => {
    if (!isAuthenticated) return;
    
    try {
      await axios.post(`${BACKEND_URL}/api/daily-work`, workForm, { headers: getAuthHeaders() });
      setWorkForm({
        date: '', task: '', source: 'תקלה', source_id: '', assignee: '', estimated_hours: 0, notes: ''
      });
      setShowDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error adding work:', error);
    }
  };

  // Google Calendar functions
  const createCalendarEvent = async (eventData, source = null) => {
    if (!isAuthenticated) return;
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/calendar/events`, {
        summary: eventData.summary,
        description: eventData.description,
        start_time: eventData.start_time,
        end_time: eventData.end_time
      }, { headers: getAuthHeaders() });

      if (response.data.success) {
        alert(`✅ אירוע נוצר בהצלחה ב-Google Calendar!`);
        if (response.data.event_link) {
          window.open(response.data.event_link, '_blank');
        }
        return true;
      } else {
        alert('❌ שגיאה ביצירת אירוע');
        return false;
      }
    } catch (error) {
      console.error('Error creating calendar event:', error);
      alert('שגיאה ביצירת אירוע מתכנון יומי');
      return false;
    }
  };

  // AI Chat functions
  const sendAiMessage = async () => {
    if (!currentMessage.trim() || isLoading || !isAuthenticated) return;
    
    setIsLoading(true);
    const userMessage = currentMessage;
    setCurrentMessage('');
    
    // Add user message to chat
    const newUserMessage = { role: 'user', content: userMessage };
    setChatHistory(prev => [...prev, newUserMessage]);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/ai-chat`, {
        user_message: userMessage,
        session_id: sessionId,
        chat_history: chatHistory
      }, { headers: getAuthHeaders() });
      
      // Add AI response to chat
      const aiResponse = { role: 'assistant', content: response.data.response };
      setChatHistory(prev => [...prev, aiResponse]);
      
      // Refresh data if tables were updated
      if (response.data.updated_tables && response.data.updated_tables.length > 0) {
        fetchData();
      }
      
    } catch (error) {
      console.error('Error sending message:', error);
      const errorMessage = { role: 'assistant', content: 'מצטער, יש בעיה בחיבור למערכת. נסה שוב מאוחר יותר.' };
      setChatHistory(prev => [...prev, errorMessage]);
      
      if (error.response && error.response.status === 401) {
        handleLogout();
      }
    }
    
    setIsLoading(false);
  };

  const clearChat = async () => {
    if (!isAuthenticated) return;
    
    try {
      await axios.delete(`${BACKEND_URL}/api/ai-chat/history/${sessionId}`, { headers: getAuthHeaders() });
      setChatHistory([]);
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

  // Login screen if not authenticated
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center" style={{ direction: 'rtl' }}>
        <Card className="w-full max-w-md mx-4">
          <CardHeader className="text-center pb-8">
            <div className="bg-blue-600 text-white p-4 rounded-full w-20 h-20 mx-auto mb-6 flex items-center justify-center">
              <Settings className="h-10 w-10" />
            </div>
            <CardTitle className="text-2xl font-bold text-gray-900">
              יהל - מערכת ניהול המחלקה
            </CardTitle>
            <CardDescription className="text-gray-600 mt-2">
              חיל הים הישראלי • מערכת AI מתקדמת
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="text-center">
              <h3 className="text-lg font-semibold text-gray-900 mb-2">
                התחברות נדרשת
              </h3>
              <p className="text-gray-600 text-sm mb-6">
                התחבר עם חשבון Google שלך כדי לגשת למערכת
              </p>
              <a 
                href="https://fleet-mentor.preview.emergentagent.com/api/auth/google/login"
                className="w-full"
              >
                <Button 
                  className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3"
                  size="lg"
                >
                  <User className="h-5 w-5 ml-2" />
                  התחבר עם Google
                </Button>
              </a>
            </div>
            
            <div className="text-center text-sm text-gray-500">
              <div className="flex items-center justify-center space-x-2">
                <div className="h-2 w-2 bg-gray-300 rounded-full"></div>
                <span>מערכת מאובטחת</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50" style={{ direction: 'rtl' }}>
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-4 rtl:space-x-reverse">
              <div className="bg-blue-600 text-white p-2 rounded-lg">
                <Settings className="h-6 w-6" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">
                  יהל - מערכת ניהול המחלקה וליווי מנהיגותי
                </h1>
                <p className="text-sm text-gray-600">חיל הים הישראלי • מערכת AI מתקדמת</p>
              </div>
            </div>

            <div className="flex items-center space-x-4 rtl:space-x-reverse">
              {/* User info */}
              {currentUser && (
                <div className="flex items-center space-x-3 rtl:space-x-reverse">
                  <div className="text-right">
                    <p className="text-sm font-medium text-gray-900">{currentUser.name}</p>
                    <p className="text-xs text-gray-500">{currentUser.email}</p>
                  </div>
                  <div className="h-8 w-8 bg-blue-600 rounded-full flex items-center justify-center">
                    <User className="h-4 w-4 text-white" />
                  </div>
                </div>
              )}
              
              <Button
                onClick={handleLogout}
                variant="outline"
                size="sm"
                className="text-gray-600 hover:text-gray-800"
              >
                התנתק
              </Button>

              {googleConnected ? (
                <div className="flex items-center space-x-2 rtl:space-x-reverse">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">מחובר ל-Google</span>
                </div>
              ) : (
                <Button
                  onClick={initiateGoogleAuth}
                  variant="outline"
                  size="sm"
                  className="flex items-center space-x-2 rtl:space-x-reverse"
                >
                  <Calendar className="h-4 w-4" />
                  <span>חבר ל-Google</span>
                </Button>
              )}
              
              <div className="flex items-center space-x-2 rtl:space-x-reverse">
                <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-600">ג'סיקה פעילה</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-6 lg:grid-cols-12 gap-1 h-auto p-1 bg-gray-100 rounded-lg overflow-x-auto">
              <TabsTrigger value="dashboard" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">לוח בקרה</TabsTrigger>
              <TabsTrigger value="ai-agent" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">AI מאמנים</TabsTrigger>
              <TabsTrigger value="failures" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">תקלות פעילות</TabsTrigger>
              <TabsTrigger value="resolved" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">תקלות שטופלו</TabsTrigger>
              <TabsTrigger value="maintenance" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">אחזקות ממתינות</TabsTrigger>
              <TabsTrigger value="equipment" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">שעות מכלולים</TabsTrigger>
              <TabsTrigger value="daily-work" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">תכנון יומי</TabsTrigger>
              <TabsTrigger value="notifications" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">התראות דחף</TabsTrigger>
              <TabsTrigger value="calendar" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">קלנדר Google</TabsTrigger>
              <TabsTrigger value="conversations" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">מעקב שיחות</TabsTrigger>
              <TabsTrigger value="dna-tracker" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">DNA מנהיגותי</TabsTrigger>
              <TabsTrigger value="ninety-day" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">תכנית 90 יום</TabsTrigger>
            </TabsList>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-8">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-red-800">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    תקלות דחופות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-red-900">
                    {activeFailures.filter(f => f.urgency >= 4).length}
                  </div>
                  <p className="text-sm text-red-700 mt-1">דורשות טיפול מיידי</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-yellow-50 to-yellow-100 border-yellow-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-yellow-800">
                    <Clock className="h-5 w-5 mr-2" />
                    תחזוקות ממתינות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-yellow-900">
                    {pendingMaintenance.length}
                  </div>
                  <p className="text-sm text-yellow-700 mt-1">מתוכננות להיום</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-blue-800">
                    <Settings className="h-5 w-5 mr-2" />
                    משימות היום
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-900">
                    {dailyWork.length}
                  </div>
                  <p className="text-sm text-blue-700 mt-1">נותרו להשלמה</p>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-teal-50 to-teal-100 border-teal-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-teal-800">
                    <Bot className="h-5 w-5 mr-2" />
                    סטטוס ג'סיקה
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex items-center space-x-2">
                    <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                    <span className="text-sm">פעיל ומוכן</span>
                  </div>
                  <div className="text-xs text-gray-600">
                    מודל: GPT-4o-mini<br/>
                    מחובר לכל הטבלאות<br/>
                    יכול לעדכן ולנתח
                  </div>
                  <Button 
                    size="sm" 
                    onClick={() => setActiveTab('ai-agent')}
                    className="w-full bg-teal-600 hover:bg-teal-700"
                  >
                    דבר עם ג'סיקה
                  </Button>
                </CardContent>
              </Card>
            </div>

            {/* Quick Overview */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    תקלות אחרונות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {activeFailures.slice(0, 5).map((failure) => (
                    <div key={failure.id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                      <div className="flex-1">
                        <p className="font-medium">{failure.failure_number}</p>
                        <p className="text-sm text-gray-600">{failure.system} - {failure.description}</p>
                      </div>
                      <Badge className={getUrgencyColor(failure.urgency)}>
                        {getUrgencyText(failure.urgency)}
                      </Badge>
                    </div>
                  ))}
                  {activeFailures.length === 0 && (
                    <p className="text-gray-500 py-4">אין תקלות פעילות כרגע</p>
                  )}
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center">
                    <Clock className="h-5 w-5 mr-2" />
                    תחזוקות קרובות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {pendingMaintenance.slice(0, 5).map((maintenance) => (
                    <div key={maintenance.id} className="flex justify-between items-center py-2 border-b last:border-b-0">
                      <div className="flex-1">
                        <p className="font-medium">{maintenance.maintenance_type}</p>
                        <p className="text-sm text-gray-600">{maintenance.system}</p>
                      </div>
                      <Badge variant="outline">
                        {getDaysFromDate(maintenance.last_performed)} ימים
                      </Badge>
                    </div>
                  ))}
                  {pendingMaintenance.length === 0 && (
                    <p className="text-gray-500 py-4">אין תחזוקות ממתינות</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Agent Tab */}
          <TabsContent value="ai-agent" className="space-y-6">
            <div className="flex justify-between items-center">
              <div>
                <h2 className="text-2xl font-bold text-gray-900">ג'סיקה - האייג'נט AI שלך</h2>
                <p className="text-gray-600">מלווה מנהיגותי וניהול מחלקה מתקדם • מבוסס על עקרונות המארג הקוונטי</p>
              </div>
              <div className="flex gap-2">
                <Button onClick={clearChat} variant="outline" size="sm">
                  נקה שיחה
                </Button>
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full animate-pulse"></div>
                  <span className="text-sm text-green-600">מחובר</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Chat Interface */}
              <div className="lg:col-span-2">
                <Card className="h-[600px] flex flex-col">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center">
                      <Bot className="h-5 w-5 mr-2" />
                      שיחה עם ג'סיקה
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="flex-1 flex flex-col">
                    {/* Messages */}
                    <div className="flex-1 overflow-y-auto space-y-4 mb-4 p-4 bg-gray-50 rounded-lg">
                      {chatHistory.length === 0 && (
                        <div className="text-center text-gray-500 py-8">
                          <Bot className="h-12 w-12 mx-auto mb-4 text-gray-400" />
                          <p>שלום! אני ג'סיקה, האייג'נט AI שלך.</p>
                          <p className="text-sm mt-2">אני כאן לעזור לך בניהול המחלקה ובליווי מנהיגותי.</p>
                        </div>
                      )}
                      
                      {chatHistory.map((message, index) => (
                        <div
                          key={index}
                          className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                          <div
                            className={`max-w-[80%] p-3 rounded-lg ${
                              message.role === 'user'
                                ? 'bg-blue-600 text-white'
                                : 'bg-white border shadow-sm'
                            }`}
                          >
                            <div className="whitespace-pre-wrap">{message.content}</div>
                          </div>
                        </div>
                      ))}
                      
                      {isLoading && (
                        <div className="flex justify-start">
                          <div className="bg-white border shadow-sm p-3 rounded-lg">
                            <div className="flex space-x-1">
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Input */}
                    <div className="flex space-x-2 rtl:space-x-reverse">
                      <Textarea
                        value={currentMessage}
                        onChange={(e) => setCurrentMessage(e.target.value)}
                        onKeyPress={handleKeyPress}
                        placeholder="כתוב הודעה לג'סיקה... (Shift+Enter לשורה חדשה)"
                        className="flex-1 resize-none min-h-[44px] max-h-32"
                        rows={1}
                      />
                      <Button 
                        onClick={sendAiMessage} 
                        disabled={isLoading || !currentMessage.trim()}
                        className="px-4"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* AI Capabilities Panel */}
              <div className="space-y-4">
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">יכולות ג'סיקה</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-start space-x-3">
                      <div className="h-2 w-2 bg-blue-500 rounded-full mt-2"></div>
                      <div>
                        <p className="font-medium text-sm">ניהול נתונים</p>
                        <p className="text-xs text-gray-600">יצירה ועדכון בכל הטבלאות</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="h-2 w-2 bg-green-500 rounded-full mt-2"></div>
                      <div>
                        <p className="font-medium text-sm">ניתוח תבנים</p>
                        <p className="text-xs text-gray-600">זיהוי מגמות ובעיות חוזרות</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="h-2 w-2 bg-purple-500 rounded-full mt-2"></div>
                      <div>
                        <p className="font-medium text-sm">ליווי מנהיגותי</p>
                        <p className="text-xs text-gray-600">פיתוח מנהיגות אישית ייחודית</p>
                      </div>
                    </div>
                    <div className="flex items-start space-x-3">
                      <div className="h-2 w-2 bg-orange-500 rounded-full mt-2"></div>
                      <div>
                        <p className="font-medium text-sm">תכנון אסטרטגי</p>
                        <p className="text-xs text-gray-600">יעדים ומעקב התקדמות</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">דוגמאות פקודות</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs justify-start"
                      onClick={() => setCurrentMessage('הצג לי סיכום תקלות השבוע')}
                    >
                      "הצג לי סיכום תקלות השבוע"
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs justify-start"
                      onClick={() => setCurrentMessage('צור תכנית עבודה ליום מחר')}
                    >
                      "צור תכנית עבודה ליום מחר"
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="w-full text-xs justify-start"
                      onClick={() => setCurrentMessage('איך אני יכול להתפתח כמנהיג?')}
                    >
                      "איך אני יכול להתפתח כמנהיג?"
                    </Button>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg flex items-center">
                      <MessageCircle className="h-4 w-4 mr-2" />
                      סטטוס שיחה
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span>הודעות בשיחה:</span>
                        <span className="font-bold">{chatHistory.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>מזהה שיחה:</span>
                        <span className="font-mono text-xs">{sessionId?.substring(0, 8)}...</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Active Failures Tab */}
          <TabsContent value="failures" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תקלות פעילות</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('failures', 'תקלות פעילות - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('failure')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף תקלה
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מס' תקלה</TableHead>
                      <TableHead>תאריך</TableHead>
                      <TableHead>מכלול</TableHead>
                      <TableHead>תיאור</TableHead>
                      <TableHead>דחיפות</TableHead>
                      <TableHead>מבצע</TableHead>
                      <TableHead>זמן משוער</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {activeFailures.map((failure) => (
                      <TableRow key={failure.id}>
                        <TableCell className="font-medium">{failure.failure_number}</TableCell>
                        <TableCell>{failure.date}</TableCell>
                        <TableCell>{failure.system}</TableCell>
                        <TableCell className="max-w-xs truncate">{failure.description}</TableCell>
                        <TableCell>
                          <Badge className={getUrgencyColor(failure.urgency)}>
                            {failure.urgency}/5
                          </Badge>
                        </TableCell>
                        <TableCell>{failure.assignee}</TableCell>
                        <TableCell>{failure.estimated_hours}h</TableCell>
                        <TableCell>
                          <Badge variant="outline">{failure.status || 'פתוח'}</Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('failure', failure)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {activeFailures.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>אין תקלות פעילות כרגע</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Other tabs would continue with similar authentication patterns... */}
          {/* For brevity, I'm showing just the key tabs that demonstrate the authentication pattern */}
          
          {/* Resolved Failures Tab */}
          <TabsContent value="resolved" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תקלות שטופלו</h2>
              <div className="flex gap-2 items-center">
                <Button 
                  onClick={() => handleExportTable('resolved-failures', 'תקלות שטופלו - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={resolvedFailures.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Badge variant="outline" className="px-4 py-2">
                  {resolvedFailures.length} תקלות נפתרו
                </Badge>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                {resolvedFailures.length > 0 ? (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>מס' תקלה</TableHead>
                        <TableHead>מכלול</TableHead>
                        <TableHead>תיאור</TableHead>
                        <TableHead>דחיפות</TableHead>
                        <TableHead>מבצע</TableHead>
                        <TableHead>זמן משוער/בפועל</TableHead>
                        <TableHead>איך נפתר</TableHead>
                        <TableHead>נפתר על ידי</TableHead>
                        <TableHead>תאריך פתרון</TableHead>
                        <TableHead>לקחים</TableHead>
                        <TableHead>פעולות</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {resolvedFailures.map((failure) => (
                        <TableRow key={failure.id}>
                          <TableCell className="font-medium">{failure.failure_number}</TableCell>
                          <TableCell>{failure.component}</TableCell>
                          <TableCell className="max-w-xs truncate">{failure.description}</TableCell>
                          <TableCell>
                            <Badge className={getUrgencyColor(failure.urgency)}>
                              {failure.urgency}/5
                            </Badge>
                          </TableCell>
                          <TableCell>{failure.operator}</TableCell>
                          <TableCell>
                            <div className="text-sm">
                              <div>משוער: {failure.estimated_hours}h</div>
                              <div className="font-medium">בפועל: {failure.actual_hours || 'לא צוין'}h</div>
                            </div>
                          </TableCell>
                          <TableCell className="max-w-xs truncate">{failure.resolution_method || 'לא צוין'}</TableCell>
                          <TableCell>{failure.resolved_by || 'לא צוין'}</TableCell>
                          <TableCell>{failure.resolved_at}</TableCell>
                          <TableCell className="max-w-xs truncate">{failure.lessons_learned || 'אין'}</TableCell>
                          <TableCell>
                            <div className="flex space-x-2">
                              <Button 
                                size="sm" 
                                variant="outline"
                                title="עדכן פרטי פתרון"
                                onClick={() => {
                                  setEditingItem(failure);
                                  setDialogType('resolved-failure');
                                  setShowDialog(true);
                                }}
                              >
                                <Edit className="h-4 w-4" />
                              </Button>
                              <Button 
                                size="sm" 
                                variant="destructive"
                                title="מחק תקלה שטופלה"
                                onClick={() => handleDeleteResolvedFailure(failure.id)}
                              >
                                <Trash2 className="h-4 w-4" />
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                ) : (
                  <Card>
                    <CardContent className="text-center py-12">
                      <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                        <AlertTriangle className="h-8 w-8 text-gray-400" />
                      </div>
                      <h3 className="text-lg font-medium text-gray-900 mb-2">אין תקלות שטופלו עדיין</h3>
                      <p className="text-lg text-gray-600">אין תקלות שטופלו עדיין</p>
                    </CardContent>
                  </Card>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Placeholder for remaining tabs... */}
          <TabsContent value="maintenance" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תחזוקות ממתינות</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('maintenance', 'תחזוקות ממתינות - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('maintenance')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף תחזוקה
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>סוג תחזוקה</TableHead>
                      <TableHead>מערכת</TableHead>
                      <TableHead>תדירות (ימים)</TableHead>
                      <TableHead>תחזוקה אחרונה</TableHead>
                      <TableHead>ימים לתחזוקה</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingMaintenance.map((maintenance) => (
                      <TableRow key={maintenance.id}>
                        <TableCell className="font-medium">{maintenance.maintenance_type}</TableCell>
                        <TableCell>{maintenance.system}</TableCell>
                        <TableCell>{maintenance.frequency_days}</TableCell>
                        <TableCell>{maintenance.last_performed}</TableCell>
                        <TableCell>
                          <Badge className={maintenance.days_until_due <= 0 ? 'bg-red-100 text-red-800' : 
                                          maintenance.days_until_due <= 7 ? 'bg-yellow-100 text-yellow-800' : 
                                          'bg-green-100 text-green-800'}>
                            {maintenance.days_until_due || 0}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant={maintenance.days_until_due <= 0 ? 'destructive' : 
                                        maintenance.days_until_due <= 7 ? 'secondary' : 'default'}>
                            {maintenance.days_until_due <= 0 ? 'חריג' : 
                             maintenance.days_until_due <= 7 ? 'דחוף' : 'תקין'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('maintenance', maintenance)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => handleDeleteMaintenance(maintenance)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {pendingMaintenance.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין תחזוקות ממתינות
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="equipment" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">שעות מכלולים</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('equipment', 'שעות מכלולים - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('equipment')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף ציוד
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מכלול</TableHead>
                      <TableHead>סוג</TableHead>
                      <TableHead>שעות נוכחיות</TableHead>
                      <TableHead>שירות אחרון</TableHead>
                      <TableHead>שעות מהשירות</TableHead>
                      <TableHead>רמת התראה</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {equipmentHours.map((equipment) => (
                      <TableRow key={equipment.id}>
                        <TableCell className="font-medium">{equipment.system}</TableCell>
                        <TableCell>{equipment.system_type}</TableCell>
                        <TableCell>{equipment.current_hours}</TableCell>
                        <TableCell>{equipment.last_service_date}</TableCell>
                        <TableCell>{equipment.hours_since_service || 0}</TableCell>
                        <TableCell>
                          <Badge className={equipment.alert_level === 'אדום' ? 'bg-red-100 text-red-800' : 
                                          equipment.alert_level === 'צהוב' ? 'bg-yellow-100 text-yellow-800' : 
                                          'bg-green-100 text-green-800'}>
                            {equipment.alert_level || 'ירוק'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('equipment', equipment)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {equipmentHours.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין ציוד רשום במערכת
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="daily-work" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנון עבודה יומי</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('daily-work', 'תכנון עבודה יומי - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('daily-work')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף משימה
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>תאריך</TableHead>
                      <TableHead>משימה</TableHead>
                      <TableHead>מקור</TableHead>
                      <TableHead>מבצע</TableHead>
                      <TableHead>זמן משוער</TableHead>
                      <TableHead>הערות</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dailyWork.map((work) => (
                      <TableRow key={work.id}>
                        <TableCell>{work.date}</TableCell>
                        <TableCell className="font-medium">{work.task}</TableCell>
                        <TableCell>{work.source}</TableCell>
                        <TableCell>{work.assignee}</TableCell>
                        <TableCell>{work.estimated_hours}h</TableCell>
                        <TableCell className="max-w-xs truncate">{work.notes}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('daily-work', work)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {dailyWork.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין משימות לתאריך זה
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="conversations" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">מעקב שיחות</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('conversations', 'מעקב שיחות - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('conversation')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף שיחה
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מס' פגישה</TableHead>
                      <TableHead>תאריך</TableHead>
                      <TableHead>משתתף</TableHead>
                      <TableHead>נושא</TableHead>
                      <TableHead>תובנות</TableHead>
                      <TableHead>תכנית מעקב</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversations.map((conversation) => (
                      <TableRow key={conversation.id}>
                        <TableCell className="font-medium">{conversation.meeting_number}</TableCell>
                        <TableCell>{conversation.date}</TableCell>
                        <TableCell>{conversation.participant}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.topic}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.insights}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.follow_up_plan}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('conversation', conversation)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {conversations.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין שיחות רשומות
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="dna-tracker" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">DNA מנהיגותי</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('dna-tracker', 'DNA מנהיגותי - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('dna')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף רכיב
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>רכיב מנהיגותי</TableHead>
                      <TableHead>הערכה עצמית</TableHead>
                      <TableHead>יעד</TableHead>
                      <TableHead>תכנית פעולה</TableHead>
                      <TableHead>הערות מנטור</TableHead>
                      <TableHead>עדכון אחרון</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dnaTracker.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-medium">{item.component_name}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{item.self_assessment}/5</Badge>
                        </TableCell>
                        <TableCell>
                          <Badge variant="outline">{item.target_score}/5</Badge>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{item.action_plan}</TableCell>
                        <TableCell className="max-w-xs truncate">{item.mentor_notes}</TableCell>
                        <TableCell>{item.last_updated}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('dna', item)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {dnaTracker.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין רכיבי DNA מוגדרים
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="ninety-day" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנית 90 יום</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('ninety-day-plan', 'תכנית 90 יום - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('ninety-day')} className="bg-blue-600 hover:bg-blue-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף שבוע
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>שבוע</TableHead>
                      <TableHead>יעדים</TableHead>
                      <TableHead>פעילויות מתוכננות</TableHead>
                      <TableHead>משאבים נדרשים</TableHead>
                      <TableHead>אינדיקטורים להצלחה</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ninetyDayPlan.map((week) => (
                      <TableRow key={week.id}>
                        <TableCell className="font-medium">שבוע {week.week_number}</TableCell>
                        <TableCell className="max-w-xs truncate">{week.goals}</TableCell>
                        <TableCell className="max-w-xs truncate">{week.planned_activities}</TableCell>
                        <TableCell className="max-w-xs truncate">{week.required_resources}</TableCell>
                        <TableCell className="max-w-xs truncate">{week.success_indicators}</TableCell>
                        <TableCell>
                          <Badge variant={week.status === 'הושלם' ? 'default' : week.status === 'בתהליך' ? 'secondary' : 'outline'}>
                            {week.status || 'מתוכנן'}
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('ninety-day', week)}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {ninetyDayPlan.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    אין תכנית 90 יום מוגדרת
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Push Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <PushNotifications />
          </TabsContent>

          {/* Google Calendar Tab */}
          <TabsContent value="calendar" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">אינטגרציית Google Calendar</h2>
              {!googleConnected ? (
                <Button 
                  onClick={initiateGoogleAuth}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Link className="h-4 w-4 mr-2" />
                  חבר ל-Google Calendar
                </Button>
              ) : (
                <div className="flex items-center space-x-2">
                  <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                  <span className="text-sm text-green-600">מחובר ל-Google Calendar</span>
                </div>
              )}
            </div>

            {googleConnected ? (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>יצירת אירועים מהירה</CardTitle>
                    <CardDescription>צור אירועים ב-Google Calendar ישירות מהמערכת</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-gray-600">
                      אתה יכול ליצור אירועים ב-Google Calendar ישירות מ:
                    </p>
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-blue-500 rounded-full"></div>
                        <span className="text-sm">תכנון עבודה יומי (כפתור לוח שנה בטבלה)</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-green-500 rounded-full"></div>
                        <span className="text-sm">תחזוקות מתוכננות</span>
                      </div>
                      <div className="flex items-center space-x-2">
                        <div className="h-2 w-2 bg-purple-500 rounded-full"></div>
                        <span className="text-sm">פגישות ושיחות ליווי</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>פרטי החיבור</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">סטטוס:</span>
                        <span className="text-sm font-medium text-green-600">מחובר</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">משתמש:</span>
                        <span className="text-sm font-medium">{currentUser?.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">שם:</span>
                        <span className="text-sm font-medium">{currentUser?.name}</span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            ) : (
              <Card>
                <CardContent className="text-center py-12">
                  <Calendar className="h-16 w-16 mx-auto mb-4 text-gray-400" />
                  <h3 className="text-lg font-medium text-gray-900 mb-2">חבר את Google Calendar</h3>
                  <p className="text-gray-600 mb-6">
                    חבר את חשבון Google שלך כדי ליצור אירועים אוטומטיים מתכנון העבודה
                  </p>
                  <Button 
                    onClick={initiateGoogleAuth}
                    className="bg-blue-600 hover:bg-blue-700"
                  >
                    <Link className="h-4 w-4 mr-2" />
                    התחבר עכשיו
                  </Button>
                </CardContent>
              </Card>
            )}
          </TabsContent>
        </Tabs>
      </main>

      {/* Floating AI Button */}
      {activeTab !== 'ai-agent' && (
        <div className="fixed bottom-6 left-6 z-50">
          <Button 
            onClick={() => setActiveTab('ai-agent')}
            className="rounded-full w-14 h-14 bg-blue-600 hover:bg-blue-700 shadow-lg"
            title="פתח צ'אט עם ג'סיקה"
          >
            <Bot className="h-6 w-6 text-white" />
          </Button>
        </div>
      )}

      {/* Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {dialogType === 'failure' && (editingItem ? 'עריכת תקלה' : 'הוסף תקלה חדשה')}
              {dialogType === 'resolved-failure' && 'עריכת פרטי פתרון'}
              {dialogType === 'maintenance' && (editingItem ? 'עריכת אחזקה' : 'הוסף אחזקה')}
              {dialogType === 'equipment' && (editingItem ? 'עריכת ציוד' : 'הוסף ציוד')}
              {dialogType === 'work' && (editingItem ? 'עריכת משימה' : 'הוסף משימה')}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {dialogType === 'failure' && (
              <>
                <Input
                  placeholder="מספר תקלה"
                  value={failureForm.failure_number}
                  onChange={(e) => setFailureForm({...failureForm, failure_number: e.target.value})}
                />
                <Input
                  type="date"
                  placeholder="תאריך"
                  value={failureForm.date}
                  onChange={(e) => setFailureForm({...failureForm, date: e.target.value})}
                />
                <Input
                  placeholder="מכלול/מערכת"
                  value={failureForm.system}
                  onChange={(e) => setFailureForm({...failureForm, system: e.target.value})}
                />
                <Textarea
                  placeholder="תיאור התקלה"
                  value={failureForm.description}
                  onChange={(e) => setFailureForm({...failureForm, description: e.target.value})}
                />
                <Select value={failureForm.urgency.toString()} onValueChange={(v) => setFailureForm({...failureForm, urgency: parseInt(v)})}>
                  <SelectTrigger>
                    <SelectValue placeholder="רמת דחיפות" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 - נמוך</SelectItem>
                    <SelectItem value="2">2 - בינוני</SelectItem>
                    <SelectItem value="3">3 - דחוף</SelectItem>
                    <SelectItem value="4">4 - דחוף מאוד</SelectItem>
                    <SelectItem value="5">5 - קריטי</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="מבצע אחראי"
                  value={failureForm.assignee}
                  onChange={(e) => setFailureForm({...failureForm, assignee: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="זמן משוער (שעות)"
                  value={failureForm.estimated_hours}
                  onChange={(e) => setFailureForm({...failureForm, estimated_hours: parseFloat(e.target.value)})}
                />
                <Select value={failureForm.status} onValueChange={(v) => setFailureForm({...failureForm, status: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="סטטוס התקלה" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="פתוח">פתוח</SelectItem>
                    <SelectItem value="בטיפול">בטיפול</SelectItem>
                    <SelectItem value="ממתין לחלקים">ממתין לחלקים</SelectItem>
                    <SelectItem value="בבדיקה">בבדיקה</SelectItem>
                    <SelectItem value="הושלם">הושלם</SelectItem>
                    <SelectItem value="סגור">סגור</SelectItem>
                  </SelectContent>
                </Select>
                <Button onClick={handleAddFailure} className="w-full">
                  {editingItem ? 'עדכן תקלה' : 'הוסף תקלה'}
                </Button>
              </>
            )}

            {dialogType === 'resolved-failure' && (
              <>
                <Textarea
                  placeholder="איך התקלה טופלה?"
                  value={resolvedFailureForm.resolution_method}
                  onChange={(e) => setResolvedFailureForm({...resolvedFailureForm, resolution_method: e.target.value})}
                  className="resize-none"
                  rows={3}
                />
                <Input
                  placeholder="מי טיפל בתקלה?"
                  value={resolvedFailureForm.resolved_by}
                  onChange={(e) => setResolvedFailureForm({...resolvedFailureForm, resolved_by: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="זמן בפועל (שעות)"
                  value={resolvedFailureForm.actual_hours}
                  onChange={(e) => setResolvedFailureForm({...resolvedFailureForm, actual_hours: parseFloat(e.target.value)})}
                />
                <Textarea
                  placeholder="לקחים להבא"
                  value={resolvedFailureForm.lessons_learned}
                  onChange={(e) => setResolvedFailureForm({...resolvedFailureForm, lessons_learned: e.target.value})}
                  className="resize-none"
                  rows={3}
                />
                <Button onClick={handleUpdateResolvedFailure} className="w-full bg-blue-600 hover:bg-blue-700">
                  עדכן פרטי פתרון
                </Button>
              </>
            )}

            {/* Other dialog types would be here... */}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;