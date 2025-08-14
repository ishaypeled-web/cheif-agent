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
import { AlertTriangle, Clock, Settings, Calendar, Plus, Edit, Trash2, Bot, Send, MessageCircle, CalendarPlus, Link, Bell, Download } from 'lucide-react';
import PushNotifications from './components/PushNotifications';

function App() {
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

  const [editingItem, setEditingItem] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');

  // Initialize chat session
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substring(2, 15);
      setSessionId(newSessionId);
    }
  }, []);

  // Chat states
  const [sessionId, setSessionId] = useState(null);
  const [currentMessage, setCurrentMessage] = useState('');
  const [chatHistory, setChatHistory] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Load chat history
  useEffect(() => {
    if (sessionId) {
      loadChatHistory();
    }
  }, [sessionId]);

  const loadChatHistory = async () => {
    try {
      const response = await axios.get(`${process.env.REACT_APP_BACKEND_URL}/api/chat/history/${sessionId}`);
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

  // API calls
  const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

  const fetchData = async () => {
    try {
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
        axios.get(`${BACKEND_URL}/api/failures`),
        axios.get(`${BACKEND_URL}/api/resolved-failures`),
        axios.get(`${BACKEND_URL}/api/maintenance`),
        axios.get(`${BACKEND_URL}/api/equipment`),
        axios.get(`${BACKEND_URL}/api/daily-work`),
        axios.get(`${BACKEND_URL}/api/conversations`),
        axios.get(`${BACKEND_URL}/api/dna-tracker`),
        axios.get(`${BACKEND_URL}/api/ninety-day-plan`),
        axios.get(`${BACKEND_URL}/api/summary`),
        axios.get(`${BACKEND_URL}/api/auth/google/user`).catch(() => ({ data: null }))
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
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

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
    try {
      if (editingItem) {
        // עריכה - עדכון קיים
        await axios.put(`${BACKEND_URL}/api/failures/${editingItem.id}`, failureForm);
      } else {
        // הוספה חדשה
        await axios.post(`${BACKEND_URL}/api/failures`, failureForm);
      }
      setFailureForm({
        failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0, status: 'פתוח'
      });
      setShowDialog(false);
      setEditingItem(null);
      fetchData();
    } catch (error) {
      console.error('Error saving failure:', error);
    }
  };

  const handleUpdateResolvedFailure = async () => {
    try {
      if (editingItem) {
        // עדכון תקלה שטופלה
        await axios.put(`${BACKEND_URL}/api/resolved-failures/${editingItem.id}`, resolvedFailureForm);
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
    try {
      if (window.confirm('האם אתה בטוח שברצונך למחוק תקלה שטופלה זו?')) {
        await axios.delete(`${BACKEND_URL}/api/resolved-failures/${failureId}`);
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting resolved failure:', error);
      alert('שגיאה במחיקת התקלה השטופלה');
    }
  };

  // Export functions
  const handleExportTable = async (tableName, customTitle = null) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/export/${tableName}`, {
        table_name: tableName,
        sheet_title: customTitle || `${tableName} Export - ${new Date().toLocaleString('he-IL')}`
      });

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
    try {
      if (editingItem) {
        // עריכה - עדכון קיים
        await axios.put(`${BACKEND_URL}/api/maintenance/${editingItem.id}`, maintenanceForm);
      } else {
        // הוספה חדשה
        await axios.post(`${BACKEND_URL}/api/maintenance`, maintenanceForm);
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

  const handleAddEquipment = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/equipment`, equipmentForm);
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
    try {
      await axios.post(`${BACKEND_URL}/api/daily-work`, workForm);
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
  const initiateGoogleAuth = () => {
    window.location.href = `${BACKEND_URL}/api/auth/google/login`;
  };

  const createCalendarEvent = async (eventData, source = null) => {
    try {
      const response = await axios.post(`${BACKEND_URL}/api/calendar/events`, {
        summary: eventData.summary,
        description: eventData.description,
        start_time: eventData.start_time,
        end_time: eventData.end_time
      });

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
    if (!currentMessage.trim() || isLoading) return;
    
    setIsLoading(true);
    const userMessage = currentMessage;
    setCurrentMessage('');
    
    // Add user message to chat
    const newUserMessage = { role: 'user', content: userMessage };
    setChatHistory(prev => [...prev, newUserMessage]);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/chat`, {
        message: userMessage,
        session_id: sessionId
      });
      
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
    }
    
    setIsLoading(false);
  };

  const clearChat = async () => {
    try {
      await axios.delete(`${BACKEND_URL}/api/chat/history/${sessionId}`);
      setChatHistory([]);
    } catch (error) {
      console.error('Error clearing chat:', error);
    }
  };

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

          {/* Maintenance Tab */}
          <TabsContent value="maintenance" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">אחזקות ממתינות</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('maintenance', 'אחזקות ממתינות - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={pendingMaintenance.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('maintenance')} className="bg-orange-600 hover:bg-orange-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף אחזקה
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
                      <TableHead>ימים מאז</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingMaintenance.map((maintenance) => {
                      const daysSince = getDaysFromDate(maintenance.last_performed);
                      return (
                        <TableRow key={maintenance.id}>
                          <TableCell className="font-medium">{maintenance.maintenance_type}</TableCell>
                          <TableCell>{maintenance.system}</TableCell>
                          <TableCell>{maintenance.frequency_days}</TableCell>
                          <TableCell>{maintenance.last_performed}</TableCell>
                          <TableCell>{daysSince}</TableCell>
                          <TableCell>
                            <Badge className={getMaintenanceStatusColor(daysSince - maintenance.frequency_days)}>
                              {daysSince > maintenance.frequency_days ? 'מאוחר' : 
                               daysSince > maintenance.frequency_days - 7 ? 'דחוף' : 'תקין'}
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
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
                {pendingMaintenance.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>אין תחזוקות ממתינות</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Equipment Tab */}
          <TabsContent value="equipment" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">שעות מכלולים וטיפולים</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('equipment', 'שעות מכלולים וטיפולים - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={equipmentHours.length === 0}
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
                      <TableHead>מערכת</TableHead>
                      <TableHead>סוג מערכת</TableHead>
                      <TableHead>שעות נוכחיות</TableHead>
                      <TableHead>תאריך שירות אחרון</TableHead>
                      <TableHead>ימים מאז שירות</TableHead>
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
                        <TableCell>{getDaysFromDate(equipment.last_service_date)}</TableCell>
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
                    <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>אין ציוד רשום</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Conversations Tab */}
          <TabsContent value="conversations" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">מעקב שיחות ליווי מנהיגותי</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('conversations', 'מעקב שיחות ליווי מנהיגותי - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={conversations.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('conversation')} className="bg-purple-600 hover:bg-purple-700">
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
                      <TableHead>מפגש מס'</TableHead>
                      <TableHead>תאריך</TableHead>
                      <TableHead>משך (דקות)</TableHead>
                      <TableHead>נושאים עיקריים</TableHead>
                      <TableHead>תובנות</TableHead>
                      <TableHead>החלטות</TableHead>
                      <TableHead>צעד הבא</TableHead>
                      <TableHead>רמת אנרגיה</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversations.map((conversation) => (
                      <TableRow key={conversation.id}>
                        <TableCell className="font-medium">{conversation.meeting_number}</TableCell>
                        <TableCell>{conversation.date}</TableCell>
                        <TableCell>{conversation.duration_minutes}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.main_topics}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.insights}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.decisions}</TableCell>
                        <TableCell className="max-w-xs truncate">{conversation.next_step}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{conversation.energy_level || conversation.yahel_energy_level}/10</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {conversations.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <MessageCircle className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>אין שיחות ליווי מתועדות</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* DNA Tracker Tab */}
          <TabsContent value="dna-tracker" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">DNA מנהיגותי - בניית זהות ייחודית</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('dna-tracker', 'DNA מנהיגותי - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={dnaTracker.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('dna')} className="bg-indigo-600 hover:bg-indigo-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף רכיב DNA
                </Button>
              </div>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>רכיב</TableHead>
                      <TableHead>הגדרה נוכחית</TableHead>
                      <TableHead>רמת בהירות</TableHead>
                      <TableHead>פערים מזוהים</TableHead>
                      <TableHead>תכנית פיתוח</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dnaTracker.map((dna) => (
                      <TableRow key={dna.id}>
                        <TableCell className="font-medium">{dna.component_name}</TableCell>
                        <TableCell className="max-w-xs truncate">{dna.current_definition}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{dna.clarity_level}/10</Badge>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{dna.gaps_identified}</TableCell>
                        <TableCell className="max-w-xs truncate">{dna.development_plan}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {dnaTracker.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Settings className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>עדיין לא התחלת לבנות את ה-DNA המנהיגותי שלך</p>
                    <p className="text-sm mt-2">דבר עם ג'סיקה כדי להתחיל בתהליך</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* 90 Day Plan Tab */}
          <TabsContent value="ninety-day" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנית 90 יום - מעקב התקדמות</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('ninety-day-plan', 'תכנית 90 יום - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={ninetyDayPlan.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('plan')} className="bg-emerald-600 hover:bg-emerald-700">
                  <Plus className="h-4 w-4 mr-2" />
                  הוסף יעד שבועי
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
                      <TableHead>פעולות קונקרטיות</TableHead>
                      <TableHead>מדדי הצלחה</TableHead>
                      <TableHead>סטטוס</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ninetyDayPlan.map((plan) => (
                      <TableRow key={plan.id}>
                        <TableCell className="font-medium">שבוע {plan.week_number}</TableCell>
                        <TableCell className="max-w-xs truncate">{plan.goals}</TableCell>
                        <TableCell className="max-w-xs truncate">{plan.concrete_actions}</TableCell>
                        <TableCell className="max-w-xs truncate">{plan.success_metrics}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{plan.status}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                {ninetyDayPlan.length === 0 && (
                  <div className="text-center py-8 text-gray-500">
                    <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>עדיין לא יצרת תכנית 90 יום</p>
                    <p className="text-sm mt-2">דבר עם ג'סיקה כדי לבנות תכנית אסטרטגית</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Daily Work Tab */}
          <TabsContent value="daily-work" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנון עבודה יומי</h2>
              <div className="flex gap-2">
                <Button 
                  onClick={() => handleExportTable('daily-work', 'תכנון עבודה יומי - יציאה')}
                  className="bg-green-600 hover:bg-green-700"
                  title="יצוא לגוגל שיטס"
                  disabled={dailyWork.length === 0}
                >
                  <Download className="h-4 w-4 mr-2" />
                  יצוא לשיטס
                </Button>
                <Button onClick={() => openDialog('work')} className="bg-blue-600 hover:bg-blue-700">
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
                      <TableHead>מזהה מקור</TableHead>
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
                        <TableCell className="font-medium max-w-xs truncate">{work.task}</TableCell>
                        <TableCell>{work.source}</TableCell>
                        <TableCell>{work.source_id}</TableCell>
                        <TableCell>{work.assignee}</TableCell>
                        <TableCell>{work.estimated_hours}h</TableCell>
                        <TableCell className="max-w-xs truncate">{work.notes}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            {googleConnected && (
                              <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                  const eventData = {
                                    summary: `משימה: ${work.task}`,
                                    description: `מקור: ${work.source}\nמבצע: ${work.assignee}\nהערות: ${work.notes}`,
                                    start_time: new Date(work.date + 'T09:00:00').toISOString(),
                                    end_time: new Date(work.date + 'T' + (9 + parseInt(work.estimated_hours)).toString().padStart(2, '0') + ':00:00').toISOString()
                                  };
                                  createCalendarEvent(eventData, 'daily-work');
                                }}
                                title="יצירה מתכנון יומי"
                              >
                                <CalendarPlus className="h-4 w-4" />
                              </Button>
                            )}
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => openDialog('work', work)}
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
                    <Calendar className="h-12 w-12 mx-auto mb-4 text-gray-300" />
                    <p>אין משימות מתוכננות להיום</p>
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
                        <span className="text-sm font-medium">{googleUser?.email}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-sm text-gray-600">שם:</span>
                        <span className="text-sm font-medium">{googleUser?.name}</span>
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

            {dialogType === 'maintenance' && (
              <>
                <Input
                  placeholder="סוג תחזוקה"
                  value={maintenanceForm.maintenance_type}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, maintenance_type: e.target.value})}
                />
                <Input
                  placeholder="מערכת"
                  value={maintenanceForm.system}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, system: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="תדירות בימים"
                  value={maintenanceForm.frequency_days}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, frequency_days: parseInt(e.target.value)})}
                />
                <Input
                  type="date"
                  placeholder="תחזוקה אחרונה"
                  value={maintenanceForm.last_performed}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, last_performed: e.target.value})}
                />
                <Button onClick={handleAddMaintenance} className="w-full bg-orange-600 hover:bg-orange-700">{editingItem ? 'עדכן אחזקה' : 'הוסף אחזקה'}</Button>
              </>
            )}

            {dialogType === 'equipment' && (
              <>
                <Input
                  placeholder="שם המערכת"
                  value={equipmentForm.system}
                  onChange={(e) => setEquipmentForm({...equipmentForm, system: e.target.value})}
                />
                <Select value={equipmentForm.system_type} onValueChange={(v) => setEquipmentForm({...equipmentForm, system_type: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="סוג מערכת" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="מנועים">מנועים</SelectItem>
                    <SelectItem value="גנרטורים">גנרטורים</SelectItem>
                    <SelectItem value="מדחסים">מדחסים</SelectItem>
                    <SelectItem value="רכיבים אחרים">רכיבים אחרים</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  placeholder="שעות נוכחיות"
                  value={equipmentForm.current_hours}
                  onChange={(e) => setEquipmentForm({...equipmentForm, current_hours: parseInt(e.target.value)})}
                />
                <Input
                  type="date"
                  placeholder="תאריך שירות אחרון"
                  value={equipmentForm.last_service_date}
                  onChange={(e) => setEquipmentForm({...equipmentForm, last_service_date: e.target.value})}
                />
                <Button onClick={handleAddEquipment} className="w-full">הוסף ציוד</Button>
              </>
            )}

            {dialogType === 'work' && (
              <>
                <Input
                  type="date"
                  placeholder="תאריך"
                  value={workForm.date}
                  onChange={(e) => setWorkForm({...workForm, date: e.target.value})}
                />
                <Textarea
                  placeholder="תיאור המשימה"
                  value={workForm.task}
                  onChange={(e) => setWorkForm({...workForm, task: e.target.value})}
                />
                <Select value={workForm.source} onValueChange={(v) => setWorkForm({...workForm, source: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="מקור המשימה" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="תקלה">תקלה</SelectItem>
                    <SelectItem value="תחזוקה">תחזוקה</SelectItem>
                    <SelectItem value="שיפור">שיפור</SelectItem>
                    <SelectItem value="אימון">אימון</SelectItem>
                    <SelectItem value="אחר">אחר</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="מזהה מקור (אם רלוונטי)"
                  value={workForm.source_id}
                  onChange={(e) => setWorkForm({...workForm, source_id: e.target.value})}
                />
                <Input
                  placeholder="מבצע אחראי"
                  value={workForm.assignee}
                  onChange={(e) => setWorkForm({...workForm, assignee: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="זמן משוער (שעות)"
                  value={workForm.estimated_hours}
                  onChange={(e) => setWorkForm({...workForm, estimated_hours: parseFloat(e.target.value)})}
                />
                <Textarea
                  placeholder="הערות נוספות"
                  value={workForm.notes}
                  onChange={(e) => setWorkForm({...workForm, notes: e.target.value})}
                />
                <Button onClick={handleAddWork} className="w-full bg-green-600 hover:bg-green-700">הוסף משימה</Button>
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
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;