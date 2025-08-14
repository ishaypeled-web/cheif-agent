import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import { Card, CardHeader, CardTitle, CardContent } from './components/ui/card';
import { Button } from './components/ui/button';
import { Input } from './components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { Badge } from './components/ui/badge';
import { Alert, AlertDescription } from './components/ui/alert';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from './components/ui/table';
import { Textarea } from './components/ui/textarea';
import { AlertTriangle, Clock, Settings, Calendar, Plus, Edit, Trash2, Bot, Send, MessageCircle, CalendarPlus, Link, Bell } from 'lucide-react';
import PushNotifications from './components/PushNotifications';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [activeFailures, setActiveFailures] = useState([]);
  const [resolvedFailures, setResolvedFailures] = useState([]);
  const [pendingMaintenance, setPendingMaintenance] = useState([]);
  const [equipmentHours, setEquipmentHours] = useState([]);
  const [dailyWork, setDailyWork] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

  // Leadership coaching states
  const [conversations, setConversations] = useState([]);
  const [dnaTracker, setDnaTracker] = useState([]);
  const [ninetyDayPlan, setNinetyDayPlan] = useState([]);
  const [leadershipSummary, setLeadershipSummary] = useState({});

  // AI Chat states
  const [chatMessages, setChatMessages] = useState([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [showAiChat, setShowAiChat] = useState(false);
  const [sessionId, setSessionId] = useState(null);

  // Google Calendar states
  const [googleUser, setGoogleUser] = useState(null);
  const [googleConnected, setGoogleConnected] = useState(false);
  const [calendarEvents, setCalendarEvents] = useState([]);
  const [showCalendarDialog, setShowCalendarDialog] = useState(false);

  // Initialize chat session
  useEffect(() => {
    if (!sessionId) {
      const newSessionId = `yahel_session_${Date.now()}`;
      setSessionId(newSessionId);
      loadChatHistory(newSessionId);
    }
  }, [sessionId]);

  // Load chat history from localStorage
  const loadChatHistory = (session) => {
    try {
      const savedMessages = localStorage.getItem(`chat_history_${session}`);
      if (savedMessages) {
        setChatMessages(JSON.parse(savedMessages));
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  // Save chat history to localStorage
  const saveChatHistory = (messages) => {
    try {
      if (sessionId) {
        localStorage.setItem(`chat_history_${sessionId}`, JSON.stringify(messages));
      }
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  };

  // Handle key press in textarea
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendAiMessage();
    }
  };

  // Form states
  const [failureForm, setFailureForm] = useState({
    failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0
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

  const [editingItem, setEditingItem] = useState(null);
  const [showDialog, setShowDialog] = useState(false);
  const [dialogType, setDialogType] = useState('');

  // API calls
  const fetchData = async () => {
    try {
      setLoading(true);
      const [
        failuresRes, 
        resolvedFailuresRes,
        maintenanceRes, 
        equipmentRes, 
        dailyWorkRes, 
        summaryRes,
        conversationsRes,
        dnaRes,
        planRes,
        leadershipRes
      ] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/failures`),
        axios.get(`${BACKEND_URL}/api/resolved-failures`),
        axios.get(`${BACKEND_URL}/api/maintenance`),
        axios.get(`${BACKEND_URL}/api/equipment`),
        axios.get(`${BACKEND_URL}/api/daily-work/today`),
        axios.get(`${BACKEND_URL}/api/dashboard/summary`),
        axios.get(`${BACKEND_URL}/api/conversations`),
        axios.get(`${BACKEND_URL}/api/dna-tracker`),
        axios.get(`${BACKEND_URL}/api/ninety-day-plan`),
        axios.get(`${BACKEND_URL}/api/leadership-summary`)
      ]);
      
      setActiveFailures(failuresRes.data);
      setResolvedFailures(resolvedFailuresRes.data);
      setPendingMaintenance(maintenanceRes.data);
      setEquipmentHours(equipmentRes.data);
      setDailyWork(dailyWorkRes.data);
      setDashboardSummary(summaryRes.data);
      setConversations(conversationsRes.data);
      setDnaTracker(dnaRes.data);
      setNinetyDayPlan(planRes.data);
      setLeadershipSummary(leadershipRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  // AI Chat functions
  const sendAiMessage = async () => {
    if (!currentMessage.trim()) return;
    
    setAiLoading(true);
    const userMessage = currentMessage;
    setCurrentMessage('');
    
    // Add user message to chat
    const newUserMessage = {
      type: 'user',
      content: userMessage,
      timestamp: new Date().toISOString(),
      sessionId: sessionId
    };
    
    const updatedMessages = [...chatMessages, newUserMessage];
    setChatMessages(updatedMessages);
    saveChatHistory(updatedMessages);
    
    try {
      // Include chat history in the request for context
      const contextMessages = updatedMessages.slice(-10); // Last 10 messages for context
      
      const response = await axios.post(`${BACKEND_URL}/api/ai-chat`, {
        user_message: userMessage,
        session_id: sessionId,
        chat_history: contextMessages
      });
      
      // Add AI response to chat
      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        recommendations: response.data.recommendations || [],
        updated_tables: response.data.updated_tables || [],
        timestamp: new Date().toISOString(),
        sessionId: sessionId
      };
      
      const finalMessages = [...updatedMessages, aiMessage];
      setChatMessages(finalMessages);
      saveChatHistory(finalMessages);
      
      // Refresh data if tables were updated
      if (response.data.updated_tables && response.data.updated_tables.length > 0) {
        fetchData();
      }
      
    } catch (error) {
      console.error('Error sending AI message:', error);
      const errorMessage = {
        type: 'ai',
        content: 'מצטער, הייתה בעיה בחיבור לאייג\'נט AI. נסה שוב.',
        timestamp: new Date().toISOString(),
        sessionId: sessionId
      };
      const errorMessages = [...updatedMessages, errorMessage];
      setChatMessages(errorMessages);
      saveChatHistory(errorMessages);
    } finally {
      setAiLoading(false);
    }
  };

  const clearChatHistory = () => {
    setChatMessages([]);
    if (sessionId) {
      localStorage.removeItem(`chat_history_${sessionId}`);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  // Helper functions
  const getUrgencyColor = (urgency) => {
    if (urgency >= 4) return 'destructive';
    if (urgency >= 3) return 'warning';
    return 'default';
  };

  const getMaintenanceStatusColor = (days) => {
    if (days <= 0) return 'destructive';
    if (days <= 7) return 'warning';
    return 'default';
  };

  const getAlertColor = (level) => {
    if (level === 'אדום') return 'destructive';
    if (level === 'כתום') return 'warning';
    return 'default';
  };

  // Form handlers
  const handleAddFailure = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/failures`, failureForm);
      setFailureForm({
        failure_number: '', date: '', system: '', description: '', urgency: 1, assignee: '', estimated_hours: 0
      });
      setShowDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error adding failure:', error);
    }
  };

  const handleAddMaintenance = async () => {
    try {
      await axios.post(`${BACKEND_URL}/api/maintenance`, maintenanceForm);
      setMaintenanceForm({
        maintenance_type: '', system: '', frequency_days: 30, last_performed: ''
      });
      setShowDialog(false);
      fetchData();
    } catch (error) {
      console.error('Error adding maintenance:', error);
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

  const handleDelete = async (type, id) => {
    try {
      await axios.delete(`${BACKEND_URL}/api/${type}/${id}`);
      fetchData();
    } catch (error) {
      console.error('Error deleting item:', error);
    }
  };

  // Google Calendar functions
  const initiateGoogleLogin = async () => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/google/login`);
      if (response.data.authorization_url) {
        window.open(response.data.authorization_url, '_blank', 'width=500,height=600');
      }
    } catch (error) {
      console.error('Error initiating Google login:', error);
      alert('שגיאה בהתחברות לGoogle Calendar');
    }
  };

  const checkGoogleAuthStatus = async (email) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/auth/user/${email}`);
      setGoogleUser(response.data);
      setGoogleConnected(response.data.google_connected);
      
      if (response.data.google_connected) {
        await fetchCalendarEvents(email);
      }
    } catch (error) {
      console.error('Error checking Google auth status:', error);
    }
  };

  const fetchCalendarEvents = async (email) => {
    try {
      const response = await axios.get(`${BACKEND_URL}/api/calendar/events?user_email=${email}`);
      setCalendarEvents(response.data);
    } catch (error) {
      console.error('Error fetching calendar events:', error);
    }
  };

  const createEventFromMaintenance = async (maintenanceId, userEmail) => {
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/calendar/create-from-maintenance`, 
        null,
        { params: { maintenance_id: maintenanceId, user_email: userEmail } }
      );
      
      if (response.data.success) {
        alert('אירוע נוצר בהצלחה בקלנדר Google!');
        await fetchCalendarEvents(userEmail);
      }
    } catch (error) {
      console.error('Error creating event from maintenance:', error);
      alert('שגיאה ביצירת אירוע מאחזקה');
    }
  };

  const createEventFromDailyPlan = async (workId, userEmail) => {
    try {
      const response = await axios.post(
        `${BACKEND_URL}/api/calendar/create-from-daily-plan`,
        null, 
        { params: { work_id: workId, user_email: userEmail } }
      );
      
      if (response.data.success) {
        alert('אירוע נוצר בהצלחה בקלנדר Google!');
        await fetchCalendarEvents(userEmail);
      }
    } catch (error) {
      console.error('Error creating event from daily plan:', error);
      alert('שגיאה ביצירת אירוע מתכנון יומי');
    }
  };

  // Check for Google auth callback on component mount
  useEffect(() => {
    const urlParams = new URLSearchParams(window.location.search);
    const googleAuth = urlParams.get('google_auth');
    const email = urlParams.get('email');
    
    if (googleAuth === 'success' && email) {
      checkGoogleAuthStatus(email);
      // Clean URL
      window.history.replaceState({}, document.title, window.location.pathname);
    } else if (googleAuth === 'error') {
      alert('שגיאה בהתחברות לGoogle Calendar');
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, []);

  const openDialog = (type) => {
    setDialogType(type);
    setEditingItem(null);
    setShowDialog(true);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-lg text-blue-800">טוען נתונים...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      {/* Header */}
      <header className="bg-white shadow-lg border-b-4 border-blue-600">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="bg-blue-600 p-3 rounded-full">
                <Settings className="h-8 w-8 text-white" />
              </div>
              <div>
                <h1 className="text-3xl font-bold text-gray-900">מערכת יהל</h1>
                <p className="text-lg text-blue-600">ניהול מחלקה - צ'יף באח"י יפו</p>
              </div>
            </div>
            <div className="flex space-x-4">
              <Badge variant="outline" className="px-4 py-2 text-sm">
                <Clock className="h-4 w-4 mr-2" />
                {new Date().toLocaleDateString('he-IL')}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <div className="relative">
            {/* Scroll indicator for mobile */}
            <div className="absolute left-0 top-0 bottom-0 w-4 bg-gradient-to-r from-transparent to-blue-100 pointer-events-none z-10 md:hidden"></div>
            <div className="absolute right-0 top-0 bottom-0 w-4 bg-gradient-to-l from-transparent to-blue-100 pointer-events-none z-10 md:hidden"></div>
            
            <TabsList className="w-full bg-white shadow-md overflow-x-auto flex scrollbar-hide gap-1 p-2" style={{
              display: 'flex',
              overflowX: 'auto',
              gap: '0.25rem',
              scrollbarWidth: 'none',
              msOverflowStyle: 'none',
              WebkitScrollbar: { display: 'none' },
              padding: '0.5rem'
            }}>
              <TabsTrigger value="dashboard" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">לוח בקרה</TabsTrigger>
              <TabsTrigger value="ai-agent" className="flex-shrink-0 whitespace-nowrap px-3 py-2 text-sm border border-gray-200 rounded-md">האייג'נט AI</TabsTrigger>
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
          </div>

          {/* Dashboard Tab */}
          <TabsContent value="dashboard" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
              <Card className="bg-gradient-to-br from-red-50 to-red-100 border-red-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-red-800">
                    <AlertTriangle className="h-5 w-5 mr-2" />
                    תקלות דחופות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-red-600">{dashboardSummary.urgent_failures || 0}</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-orange-50 to-orange-100 border-orange-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-orange-800">
                    <Clock className="h-5 w-5 mr-2" />
                    אחזקות פגות
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-orange-600">{dashboardSummary.overdue_maintenance || 0}</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-blue-800">
                    <Settings className="h-5 w-5 mr-2" />
                    ציוד קריטי
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-blue-600">{dashboardSummary.critical_equipment || 0}</div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-green-50 to-green-100 border-green-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-green-800">
                    <Calendar className="h-5 w-5 mr-2" />
                    משימות היום
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="text-3xl font-bold text-green-600">{dashboardSummary.today_tasks || 0}</div>
                </CardContent>
              </Card>
            </div>

            {/* Leadership Dashboard */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <Card className="bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-purple-800">
                    <MessageCircle className="h-5 w-5 mr-2" />
                    התקדמות מנהיגותית
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>שיחות ליווי</span>
                    <Badge variant="outline">{leadershipSummary.recent_conversations_count || 0}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>רמת אנרגיה ממוצעת</span>
                    <Badge variant={leadershipSummary.avg_energy_level >= 7 ? 'default' : 'warning'}>
                      {leadershipSummary.avg_energy_level || 5}/10
                    </Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>בהירות DNA</span>
                    <Badge variant={leadershipSummary.dna_clarity_average >= 7 ? 'default' : 'warning'}>
                      {leadershipSummary.dna_clarity_average || 0}/10
                    </Badge>
                  </div>
                </CardContent>
              </Card>

              <Card className="bg-gradient-to-br from-indigo-50 to-indigo-100 border-indigo-200">
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center text-indigo-800">
                    <Calendar className="h-5 w-5 mr-2" />
                    תכנית 90 יום
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  <div className="flex justify-between">
                    <span>שבועות מתוכננים</span>
                    <Badge variant="outline">{leadershipSummary.total_weeks_planned || 0}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>שבועות הושלמו</span>
                    <Badge variant="default">{leadershipSummary.weeks_completed || 0}</Badge>
                  </div>
                  <div className="flex justify-between">
                    <span>אחוז ביצוע</span>
                    <Badge variant={leadershipSummary.plan_completion_rate >= 50 ? 'default' : 'warning'}>
                      {leadershipSummary.plan_completion_rate || 0}%
                    </Badge>
                  </div>
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
                  <CardTitle>תקלות דחופות</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {activeFailures.filter(f => f.urgency >= 4).slice(0, 3).map(failure => (
                      <div key={failure.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                        <div>
                          <p className="font-medium">{failure.system}</p>
                          <p className="text-sm text-gray-600">{failure.description}</p>
                        </div>
                        <Badge variant={getUrgencyColor(failure.urgency)}>
                          דחיפות {failure.urgency}
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>שיחות ליווי אחרונות</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {conversations.slice(0, 3).map(conv => (
                      <div key={conv.id} className="flex items-center justify-between p-3 bg-purple-50 rounded-lg">
                        <div>
                          <p className="font-medium">מפגש #{conv.meeting_number}</p>
                          <p className="text-sm text-gray-600">{conv.date}</p>
                          <p className="text-xs text-gray-500">
                            {conv.main_topics?.slice(0, 2).join(', ')}
                          </p>
                        </div>
                        <Badge variant="outline">
                          אנרגיה {conv.yahel_energy_level}/10
                        </Badge>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>

          {/* AI Agent Tab */}
          <TabsContent value="ai-agent" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* AI Chat Interface */}
              <div className="lg:col-span-2">
                <Card className="h-[600px] flex flex-col">
                  <CardHeader className="pb-4">
                    <CardTitle className="flex items-center text-blue-800">
                      <Bot className="h-6 w-6 mr-2" />
                      האייג'נט AI של יהל - ג'סיקה
                    </CardTitle>
                    <p className="text-sm text-gray-600">
                      מערכת ליווי מנהיגותי וניהול מחלקה מבוססת AI
                    </p>
                  </CardHeader>
                  
                  <CardContent className="flex-1 flex flex-col p-4">
                    {/* Chat Messages */}
                    <div className="flex-1 overflow-y-auto mb-4 space-y-4 bg-gray-50 rounded-lg p-4 chat-messages">
                      {chatMessages.length === 0 && (
                        <div className="text-center text-gray-500 mt-8">
                          <Bot className="h-12 w-12 mx-auto mb-4 text-blue-600" />
                          <p className="text-lg font-medium">שלום יהל! 👋</p>
                          <p>אני ג'סיקה, כאן לעזור לך בניהול המחלקה ובליווי מנהיגותי.</p>
                          <div className="mt-4 text-sm text-right">
                            <p>דוגמאות לשאלות:</p>
                            <ul className="mt-2 space-y-1">
                              <li>"מה המצב הנוכחי במחלקה?"</li>
                              <li>"איזה תקלות דחופות יש לי?"</li>
                              <li>"איך אני מתקדם בתפקיד?"</li>
                              <li>"מה העדיפויות שלי השבוע?"</li>
                              <li>"רוצה לתעד שיחה עם הסגן שלי..."</li>
                            </ul>
                          </div>
                        </div>
                      )}
                      
                      {chatMessages.map((message, index) => (
                        <div key={index} className={`flex ${message.type === 'user' ? 'justify-end' : 'justify-start'}`}>
                          <div className={`max-w-[80%] p-3 rounded-lg ${
                            message.type === 'user' 
                              ? 'bg-blue-600 text-white' 
                              : 'bg-white border border-gray-200'
                          }`}>
                            <div className="whitespace-pre-wrap">{message.content}</div>
                            {message.recommendations && message.recommendations.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-gray-200">
                                <p className="font-medium text-sm">המלצות:</p>
                                <ul className="text-sm mt-1">
                                  {message.recommendations.map((rec, i) => (
                                    <li key={i}>• {rec}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            {message.updated_tables && message.updated_tables.length > 0 && (
                              <div className="mt-2 pt-2 border-t border-gray-200">
                                <Badge variant="outline" className="text-xs">
                                  עודכנו: {message.updated_tables.join(', ')}
                                </Badge>
                              </div>
                            )}
                            <div className="text-xs opacity-70 mt-1">
                              {new Date(message.timestamp).toLocaleTimeString('he-IL')}
                            </div>
                          </div>
                        </div>
                      ))}
                      
                      {aiLoading && (
                        <div className="flex justify-start">
                          <div className="bg-white border border-gray-200 p-3 rounded-lg">
                            <div className="flex items-center space-x-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                              <span>ג'סיקה חושבת...</span>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                    
                    {/* Input Area */}
                    <div className="space-y-2">
                      <div className="flex space-x-2">
                        <Textarea
                          value={currentMessage}
                          onChange={(e) => setCurrentMessage(e.target.value)}
                          onKeyPress={handleKeyPress}
                          placeholder="שאל את ג'סיקה על המחלקה או קבל ייעוץ מנהיגותי..."
                          disabled={aiLoading}
                          className="flex-1 chat-textarea"
                          rows={1}
                        />
                        <div className="flex flex-col space-y-1">
                          <Button 
                            onClick={sendAiMessage}
                            disabled={aiLoading || !currentMessage.trim()}
                            className="bg-blue-600 hover:bg-blue-700"
                          >
                            <Send className="h-4 w-4" />
                          </Button>
                          <Button
                            onClick={clearChatHistory}
                            size="sm"
                            variant="outline"
                            className="text-xs"
                            title="נקה היסטוריה"
                          >
                            🗑️
                          </Button>
                        </div>
                      </div>
                      <div className="chat-hint">
                        Enter = שורה חדשה • Shift+Enter = שליחה • יש לג'סיקה זיכרון של השיחה
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
              
              {/* Quick Actions & Context */}
              <div className="space-y-4">
                {/* Quick Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">מצב מחלקה מהיר</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="flex items-center justify-between">
                      <span>תקלות דחופות</span>
                      <Badge variant={dashboardSummary.urgent_failures > 0 ? 'destructive' : 'default'}>
                        {dashboardSummary.urgent_failures || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>ציוד קריטי</span>
                      <Badge variant={dashboardSummary.critical_equipment > 0 ? 'destructive' : 'default'}>
                        {dashboardSummary.critical_equipment || 0}
                      </Badge>
                    </div>
                    <div className="flex items-center justify-between">
                      <span>משימות היום</span>
                      <Badge variant="outline">
                        {dashboardSummary.today_tasks || 0}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>

                {/* Quick Questions */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">שאלות מהירות</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    <Button 
                      variant="outline" 
                      className="w-full text-right justify-start"
                      onClick={() => {
                        setCurrentMessage("מה המצב הנוכחי במחלקה? אני רוצה סקירה מהירה.");
                        sendAiMessage();
                      }}
                    >
                      <MessageCircle className="h-4 w-4 mr-2" />
                      מצב מחלקה עכשיו
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full text-right justify-start"
                      onClick={() => {
                        setCurrentMessage("איזה עדיפויות יש לי השבוע? מה הדחוף ביותר?");
                        sendAiMessage();
                      }}
                    >
                      <AlertTriangle className="h-4 w-4 mr-2" />
                      עדיפויות שבועיות
                    </Button>
                    <Button 
                      variant="outline" 
                      className="w-full text-right justify-start"
                      onClick={() => {
                        setCurrentMessage("איך אני מתקדם כמנהיג? יש לי נקודות לשיפור?");
                        sendAiMessage();
                      }}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      התקדמות מנהיגותית
                    </Button>
                  </CardContent>
                </Card>
                
                {/* AI Status */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">סטטוס האייג'נט</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center space-x-2">
                      <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                      <span className="text-sm">מחובר ופעיל</span>
                    </div>
                    <p className="text-xs text-gray-600 mt-2">
                      מודל: GPT-4o-mini<br/>
                      עדכון אחרון: {new Date().toLocaleTimeString('he-IL')}
                    </p>
                  </CardContent>
                </Card>
              </div>
            </div>
          </TabsContent>

          {/* Active Failures Tab */}
          <TabsContent value="failures" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תקלות פעילות</h2>
              <Button onClick={() => openDialog('failure')} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף תקלה
              </Button>
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
                    {activeFailures.map(failure => (
                      <TableRow key={failure.id}>
                        <TableCell className="font-medium">{failure.failure_number}</TableCell>
                        <TableCell>{failure.date}</TableCell>
                        <TableCell>{failure.system}</TableCell>
                        <TableCell className="max-w-xs truncate">{failure.description}</TableCell>
                        <TableCell>
                          <Badge variant={getUrgencyColor(failure.urgency)}>
                            {failure.urgency}
                          </Badge>
                        </TableCell>
                        <TableCell>{failure.assignee}</TableCell>
                        <TableCell>{failure.estimated_hours} שעות</TableCell>
                        <TableCell>{failure.status}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setEditingItem(failure);
                                setDialogType('failure');
                                setShowDialog(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('failures', failure.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Resolved Failures Tab */}
          <TabsContent value="resolved" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תקלות שטופלו</h2>
              <Badge variant="outline" className="px-4 py-2">
                {resolvedFailures.length} תקלות נפתרו
              </Badge>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מס' תקלה</TableHead>
                      <TableHead>מכלול</TableHead>
                      <TableHead>תיאור</TableHead>
                      <TableHead>דחיפות</TableHead>
                      <TableHead>מבצע</TableHead>
                      <TableHead>זמן משוער</TableHead>
                      <TableHead>זמן בפועל</TableHead>
                      <TableHead>איך טופל?</TableHead>
                      <TableHead>נפתר ע"י</TableHead>
                      <TableHead>תאריך פתירה</TableHead>
                      <TableHead>לקחים</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {resolvedFailures.map(failure => (
                      <TableRow key={failure.id}>
                        <TableCell className="font-medium">{failure.failure_number}</TableCell>
                        <TableCell>{failure.system}</TableCell>
                        <TableCell className="max-w-xs truncate">{failure.description}</TableCell>
                        <TableCell>
                          <Badge variant={getUrgencyColor(failure.urgency)}>
                            {failure.urgency}
                          </Badge>
                        </TableCell>
                        <TableCell>{failure.assignee}</TableCell>
                        <TableCell>{failure.estimated_hours} שעות</TableCell>
                        <TableCell>
                          <Badge variant="outline">
                            {failure.actual_hours || failure.estimated_hours} שעות
                          </Badge>
                        </TableCell>
                        <TableCell className="max-w-xs">
                          <div className="text-sm">
                            {failure.resolution_method ? (
                              <span className="text-green-600">{failure.resolution_method}</span>
                            ) : (
                              <Badge variant="warning" className="text-xs">
                                לא מתועד
                              </Badge>
                            )}
                          </div>
                        </TableCell>
                        <TableCell>{failure.resolved_by}</TableCell>
                        <TableCell>{failure.resolved_date}</TableCell>
                        <TableCell className="max-w-xs">
                          {failure.lessons_learned ? (
                            <div className="text-sm text-blue-600 truncate" title={failure.lessons_learned}>
                              {failure.lessons_learned}
                            </div>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              אין לקחים
                            </Badge>
                          )}
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              title="עדכן פרטי פתרון"
                              onClick={() => {
                                // Open edit dialog for resolution details
                                setCurrentMessage(`אני רוצה לעדכן את פרטי הפתרון של תקלה ${failure.failure_number}. איך היא טופלה בדיוק?`);
                                setActiveTab('ai-agent');
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>

            {resolvedFailures.length === 0 && (
              <Card>
                <CardContent className="text-center py-8">
                  <AlertTriangle className="h-12 w-12 mx-auto text-gray-400 mb-4" />
                  <p className="text-lg text-gray-600">אין תקלות שטופלו עדיין</p>
                  <p className="text-sm text-gray-500 mt-2">
                    כאשר תסמן תקלה כ"הושלם", היא תועבר לכאן אוטומטית
                  </p>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          {/* Maintenance Tab */}
          <TabsContent value="maintenance" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">אחזקות ממתינות</h2>
              <Button onClick={() => openDialog('maintenance')} className="bg-orange-600 hover:bg-orange-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף אחזקה
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>סוג אחזקה</TableHead>
                      <TableHead>מכלול</TableHead>
                      <TableHead>תדירות (ימים)</TableHead>
                      <TableHead>ביצוע אחרון</TableHead>
                      <TableHead>ביצוע הבא</TableHead>
                      <TableHead>ימים עד ביצוע</TableHead>
                      <TableHead>סטטוס</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {pendingMaintenance.map(maintenance => (
                      <TableRow key={maintenance.id}>
                        <TableCell className="font-medium">{maintenance.maintenance_type}</TableCell>
                        <TableCell>{maintenance.system}</TableCell>
                        <TableCell>{maintenance.frequency_days}</TableCell>
                        <TableCell>{maintenance.last_performed}</TableCell>
                        <TableCell>{maintenance.next_due}</TableCell>
                        <TableCell>
                          <Badge variant={getMaintenanceStatusColor(maintenance.days_until_due)}>
                            {maintenance.days_until_due} ימים
                          </Badge>
                        </TableCell>
                        <TableCell>{maintenance.status}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setEditingItem(maintenance);
                                setDialogType('maintenance');
                                setShowDialog(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('maintenance', maintenance.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                            {googleConnected && (
                              <Button 
                                size="sm" 
                                variant="secondary"
                                onClick={() => createEventFromMaintenance(maintenance.id, googleUser?.email)}
                                title="הוסף לקלנדר Google"
                              >
                                <CalendarPlus className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Equipment Hours Tab */}
          <TabsContent value="equipment" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">שעות מכלולים וטיפולים</h2>
              <Button onClick={() => openDialog('equipment')} className="bg-blue-600 hover:bg-blue-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף ציוד
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מכלול</TableHead>
                      <TableHead>סוג מערכת</TableHead>
                      <TableHead>שעות נוכחיות</TableHead>
                      <TableHead>טיפול הבא</TableHead>
                      <TableHead>שעות עד טיפול</TableHead>
                      <TableHead>התרעה</TableHead>
                      <TableHead>טיפול אחרון</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {equipmentHours.map(equipment => (
                      <TableRow key={equipment.id}>
                        <TableCell className="font-medium">{equipment.system}</TableCell>
                        <TableCell>{equipment.system_type}</TableCell>
                        <TableCell>{equipment.current_hours}</TableCell>
                        <TableCell>{equipment.next_service_hours}</TableCell>
                        <TableCell>{equipment.hours_until_service}</TableCell>
                        <TableCell>
                          <Badge variant={getAlertColor(equipment.alert_level)}>
                            {equipment.alert_level}
                          </Badge>
                        </TableCell>
                        <TableCell>{equipment.last_service_date || 'לא ידוע'}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setEditingItem(equipment);
                                setDialogType('equipment');
                                setShowDialog(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('equipment', equipment.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Conversations Tab */}
          <TabsContent value="conversations" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">מעקב שיחות ליווי מנהיגותי</h2>
              <Button onClick={() => openDialog('conversation')} className="bg-purple-600 hover:bg-purple-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף שיחה
              </Button>
            </div>

            <Card>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>מפגש</TableHead>
                      <TableHead>תאריך</TableHead>
                      <TableHead>משך (דקות)</TableHead>
                      <TableHead>נושאים עיקריים</TableHead>
                      <TableHead>תובנות</TableHead>
                      <TableHead>החלטות</TableHead>
                      <TableHead>צעד הבא</TableHead>
                      <TableHead>רמת אנרגיה</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {conversations.map(conv => (
                      <TableRow key={conv.id}>
                        <TableCell className="font-medium">#{conv.meeting_number}</TableCell>
                        <TableCell>{conv.date}</TableCell>
                        <TableCell>{conv.duration_minutes}</TableCell>
                        <TableCell className="max-w-xs">
                          <div className="text-sm">
                            {conv.main_topics?.slice(0, 2).map((topic, i) => (
                              <Badge key={i} variant="outline" className="mr-1 mb-1">
                                {topic}
                              </Badge>
                            ))}
                          </div>
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {conv.insights?.[0] || ''}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">
                          {conv.decisions?.[0] || ''}
                        </TableCell>
                        <TableCell className="max-w-xs truncate">{conv.next_step}</TableCell>
                        <TableCell>
                          <Badge variant={conv.yahel_energy_level >= 7 ? 'default' : 'warning'}>
                            {conv.yahel_energy_level}/10
                          </Badge>
                        </TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setEditingItem(conv);
                                setDialogType('conversation');
                                setShowDialog(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('conversations', conv.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* DNA Tracker Tab */}
          <TabsContent value="dna-tracker" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">DNA מנהיגותי של יהל</h2>
              <Button onClick={() => openDialog('dna')} className="bg-indigo-600 hover:bg-indigo-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף רכיב DNA
              </Button>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {dnaTracker.map(dna => (
                <Card key={dna.id} className="bg-gradient-to-br from-indigo-50 to-purple-50">
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>{dna.component_name}</span>
                      <Badge variant={dna.clarity_level >= 7 ? 'default' : 'warning'}>
                        בהירות {dna.clarity_level}/10
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div>
                      <p className="text-sm font-medium text-gray-700">הגדרה נוכחית:</p>
                      <p className="text-sm">{dna.current_definition}</p>
                    </div>
                    {dna.gaps_identified && dna.gaps_identified.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">פערים שזוהו:</p>
                        <div className="flex flex-wrap gap-1 mt-1">
                          {dna.gaps_identified.map((gap, i) => (
                            <Badge key={i} variant="outline" className="text-xs">
                              {gap}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    )}
                    <div>
                      <p className="text-sm font-medium text-gray-700">תכנית פיתוח:</p>
                      <p className="text-sm">{dna.development_plan}</p>
                    </div>
                    <div className="flex justify-between items-center pt-2">
                      <span className="text-xs text-gray-500">
                        עודכן: {dna.last_updated}
                      </span>
                      <div className="flex space-x-2">
                        <Button 
                          size="sm" 
                          variant="outline"
                          onClick={() => {
                            setEditingItem(dna);
                            setDialogType('dna');
                            setShowDialog(true);
                          }}
                        >
                          <Edit className="h-4 w-4" />
                        </Button>
                        <Button 
                          size="sm" 
                          variant="destructive"
                          onClick={() => handleDelete('dna-tracker', dna.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* 90 Day Plan Tab */}
          <TabsContent value="ninety-day" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנית 90 יום של יהל</h2>
              <Button onClick={() => openDialog('plan')} className="bg-teal-600 hover:bg-teal-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף שבוע
              </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {ninetyDayPlan.map(week => (
                <Card key={week.id} className={`bg-gradient-to-br ${
                  week.status === 'הושלם' ? 'from-green-50 to-green-100 border-green-200' :
                  week.status === 'בביצוע' ? 'from-yellow-50 to-yellow-100 border-yellow-200' :
                  'from-gray-50 to-gray-100 border-gray-200'
                }`}>
                  <CardHeader>
                    <CardTitle className="flex items-center justify-between">
                      <span>שבוע {week.week_number}</span>
                      <Badge variant={
                        week.status === 'הושלם' ? 'default' :
                        week.status === 'בביצוע' ? 'warning' : 'outline'
                      }>
                        {week.status}
                      </Badge>
                    </CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    {week.goals && week.goals.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">יעדים:</p>
                        <ul className="text-sm list-disc list-inside">
                          {week.goals.map((goal, i) => (
                            <li key={i}>{goal}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {week.concrete_actions && week.concrete_actions.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">פעולות קונקרטיות:</p>
                        <ul className="text-sm list-disc list-inside">
                          {week.concrete_actions.map((action, i) => (
                            <li key={i}>{action}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {week.success_metrics && week.success_metrics.length > 0 && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">מדדי הצלחה:</p>
                        <ul className="text-sm list-disc list-inside">
                          {week.success_metrics.map((metric, i) => (
                            <li key={i}>{metric}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {week.reflection && (
                      <div>
                        <p className="text-sm font-medium text-gray-700">רפלקציה:</p>
                        <p className="text-sm">{week.reflection}</p>
                      </div>
                    )}
                    <div className="flex justify-end space-x-2 pt-2">
                      <Button 
                        size="sm" 
                        variant="outline"
                        onClick={() => {
                          setEditingItem(week);
                          setDialogType('ninety-day');
                          setShowDialog(true);
                        }}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button 
                        size="sm" 
                        variant="destructive"
                        onClick={() => handleDelete('ninety-day-plan', week.id)}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </TabsContent>

          {/* Daily Work Tab */}
          <TabsContent value="daily-work" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">תכנון עבודה יומי</h2>
              <Button onClick={() => openDialog('work')} className="bg-green-600 hover:bg-green-700">
                <Plus className="h-4 w-4 mr-2" />
                הוסף משימה
              </Button>
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
                      <TableHead>סטטוס</TableHead>
                      <TableHead>הערות</TableHead>
                      <TableHead>פעולות</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {dailyWork.map(work => (
                      <TableRow key={work.id}>
                        <TableCell>{work.date}</TableCell>
                        <TableCell className="font-medium">{work.task}</TableCell>
                        <TableCell>
                          <Badge variant="outline">{work.source}</Badge>
                        </TableCell>
                        <TableCell>{work.assignee}</TableCell>
                        <TableCell>{work.estimated_hours} שעות</TableCell>
                        <TableCell>{work.status}</TableCell>
                        <TableCell className="max-w-xs truncate">{work.notes}</TableCell>
                        <TableCell>
                          <div className="flex space-x-2">
                            <Button 
                              size="sm" 
                              variant="outline"
                              onClick={() => {
                                setEditingItem(work);
                                setDialogType('work');
                                setShowDialog(true);
                              }}
                            >
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('daily-work', work.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                            {googleConnected && (
                              <Button 
                                size="sm" 
                                variant="secondary"
                                onClick={() => createEventFromDailyPlan(work.id, googleUser?.email)}
                                title="הוסף לקלנדר Google"
                              >
                                <CalendarPlus className="h-4 w-4" />
                              </Button>
                            )}
                          </div>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Push Notifications Tab */}
          <TabsContent value="notifications" className="space-y-6">
            <PushNotifications userId="yahel-naval-user" />
          </TabsContent>

          {/* Google Calendar Tab */}
          <TabsContent value="calendar" className="space-y-6">
            <div className="flex justify-between items-center">
              <h2 className="text-2xl font-bold text-gray-900">קלנדר Google</h2>
              {!googleConnected ? (
                <Button onClick={initiateGoogleLogin} className="bg-red-600 hover:bg-red-700">
                  <Link className="h-4 w-4 mr-2" />
                  התחבר לGoogle Calendar
                </Button>
              ) : (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-green-600">✓ מחובר כ-{googleUser?.name}</span>
                  <Button onClick={() => fetchCalendarEvents(googleUser?.email)} variant="outline" size="sm">
                    רענן אירועים
                  </Button>
                </div>
              )}
            </div>

            {!googleConnected ? (
              <Card>
                <CardContent className="text-center py-12">
                  <Calendar className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">התחבר לGoogle Calendar</h3>
                  <p className="text-gray-600 mb-6">
                    התחבר לחשבון Google שלך כדי ליצור אירועים בקלנדר מאחזקות ומשימות יומיות
                  </p>
                  <Button onClick={initiateGoogleLogin} className="bg-red-600 hover:bg-red-700">
                    <Link className="h-4 w-4 mr-2" />
                    התחבר עכשיו
                  </Button>
                </CardContent>
              </Card>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">יצירת אירועים מהירה</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-gray-600">
                        צור אירועים בקלנדר Google ישירות מהנתונים הקיימים במערכת
                      </p>
                      <div className="space-y-2">
                        <Button 
                          variant="outline" 
                          className="w-full justify-start"
                          onClick={() => setActiveTab('maintenance')}
                        >
                          <CalendarPlus className="h-4 w-4 mr-2" />
                          יצירה מאחזקות ממתינות
                        </Button>
                        <Button 
                          variant="outline" 
                          className="w-full justify-start"
                          onClick={() => setActiveTab('daily-work')}
                        >
                          <CalendarPlus className="h-4 w-4 mr-2" />
                          יצירה מתכנון יומי
                        </Button>
                      </div>
                    </CardContent>
                  </Card>

                  <Card>
                    <CardHeader>
                      <CardTitle className="text-lg">סטטוס חיבור</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        <div className="flex items-center space-x-2">
                          <div className="h-3 w-3 bg-green-500 rounded-full"></div>
                          <span className="text-sm font-medium">מחובר לGoogle Calendar</span>
                        </div>
                        <div className="text-sm text-gray-600">
                          <strong>משתמש:</strong> {googleUser?.name}<br/>
                          <strong>אימייל:</strong> {googleUser?.email}<br/>
                          <strong>חיבור:</strong> פעיל
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                {/* Calendar Events List */}
                <Card>
                  <CardHeader>
                    <CardTitle className="text-lg">האירועים הקרובים שלי</CardTitle>
                  </CardHeader>
                  <CardContent>
                    {calendarEvents?.google_events?.length > 0 ? (
                      <div className="space-y-3">
                        {calendarEvents.google_events.slice(0, 10).map((event, index) => (
                          <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                            <div>
                              <h4 className="font-medium">{event.summary}</h4>
                              <p className="text-sm text-gray-600">
                                {event.start?.dateTime ? 
                                  new Date(event.start.dateTime).toLocaleString('he-IL') :
                                  event.start?.date
                                }
                              </p>
                              {event.location && (
                                <p className="text-sm text-gray-500">{event.location}</p>
                              )}
                            </div>
                            {event.htmlLink && (
                              <Button 
                                variant="outline" 
                                size="sm"
                                onClick={() => window.open(event.htmlLink, '_blank')}
                              >
                                פתח בGoogle
                              </Button>
                            )}
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8">
                        <Calendar className="h-8 w-8 text-gray-400 mx-auto mb-2" />
                        <p className="text-gray-600">אין אירועים קרובים</p>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </>
            )}
          </TabsContent>

        </Tabs>
      </main>

      {/* Floating AI Button */}
      {activeTab !== 'ai-agent' && (
        <div className="fixed bottom-6 right-6 z-50">
          <Button
            onClick={() => setActiveTab('ai-agent')}
            className="h-14 w-14 rounded-full bg-blue-600 hover:bg-blue-700 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <Bot className="h-6 w-6 text-white" />
          </Button>
        </div>
      )}

      {/* Add Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {dialogType === 'failure' && 'הוסף תקלה חדשה'}
              {dialogType === 'maintenance' && 'הוסף אחזקה'}
              {dialogType === 'equipment' && 'הוסף ציוד'}
              {dialogType === 'work' && 'הוסף משימה'}
            </DialogTitle>
          </DialogHeader>
          
          <div className="space-y-4">
            {dialogType === 'failure' && (
              <>
                <Input
                  placeholder="מס' תקלה"
                  value={failureForm.failure_number}
                  onChange={(e) => setFailureForm({...failureForm, failure_number: e.target.value})}
                />
                <Input
                  type="date"
                  value={failureForm.date}
                  onChange={(e) => setFailureForm({...failureForm, date: e.target.value})}
                />
                <Input
                  placeholder="מכלול"
                  value={failureForm.system}
                  onChange={(e) => setFailureForm({...failureForm, system: e.target.value})}
                />
                <Input
                  placeholder="תיאור התקלה"
                  value={failureForm.description}
                  onChange={(e) => setFailureForm({...failureForm, description: e.target.value})}
                />
                <Select value={failureForm.urgency.toString()} onValueChange={(v) => setFailureForm({...failureForm, urgency: parseInt(v)})}>
                  <SelectTrigger>
                    <SelectValue placeholder="דחיפות" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1">1 - נמוכה</SelectItem>
                    <SelectItem value="2">2</SelectItem>
                    <SelectItem value="3">3 - בינונית</SelectItem>
                    <SelectItem value="4">4</SelectItem>
                    <SelectItem value="5">5 - גבוהה</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="מבצע"
                  value={failureForm.assignee}
                  onChange={(e) => setFailureForm({...failureForm, assignee: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="זמן משוער (שעות)"
                  value={failureForm.estimated_hours}
                  onChange={(e) => setFailureForm({...failureForm, estimated_hours: parseFloat(e.target.value)})}
                />
                <Button onClick={handleAddFailure} className="w-full">הוסף תקלה</Button>
              </>
            )}

            {dialogType === 'maintenance' && (
              <>
                <Input
                  placeholder="סוג אחזקה"
                  value={maintenanceForm.maintenance_type}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, maintenance_type: e.target.value})}
                />
                <Input
                  placeholder="מכלול"
                  value={maintenanceForm.system}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, system: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="תדירות (ימים)"
                  value={maintenanceForm.frequency_days}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, frequency_days: parseInt(e.target.value)})}
                />
                <Input
                  type="date"
                  placeholder="ביצוע אחרון"
                  value={maintenanceForm.last_performed}
                  onChange={(e) => setMaintenanceForm({...maintenanceForm, last_performed: e.target.value})}
                />
                <Button onClick={handleAddMaintenance} className="w-full bg-orange-600 hover:bg-orange-700">הוסף אחזקה</Button>
              </>
            )}

            {dialogType === 'equipment' && (
              <>
                <Input
                  placeholder="שם המכלול"
                  value={equipmentForm.system}
                  onChange={(e) => setEquipmentForm({...equipmentForm, system: e.target.value})}
                />
                <Select value={equipmentForm.system_type} onValueChange={(v) => setEquipmentForm({...equipmentForm, system_type: v})}>
                  <SelectTrigger>
                    <SelectValue placeholder="סוג מערכת" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="מנועים">מנועים</SelectItem>
                    <SelectItem value="תשלובות">תשלובות</SelectItem>
                    <SelectItem value="גנרטורים">גנרטורים</SelectItem>
                    <SelectItem value="מדחסים">מדחסים</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  type="number"
                  placeholder="שעות נוכחיות"
                  value={equipmentForm.current_hours}
                  onChange={(e) => setEquipmentForm({...equipmentForm, current_hours: parseFloat(e.target.value)})}
                />
                <Input
                  type="date"
                  placeholder="תאריך טיפול אחרון"
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
                  value={workForm.date}
                  onChange={(e) => setWorkForm({...workForm, date: e.target.value})}
                />
                <Input
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
                    <SelectItem value="אחזקה">אחזקה</SelectItem>
                    <SelectItem value="טיפול">טיפול</SelectItem>
                    <SelectItem value="אחר">אחר</SelectItem>
                  </SelectContent>
                </Select>
                <Input
                  placeholder="מזהה מקור (אופציונלי)"
                  value={workForm.source_id}
                  onChange={(e) => setWorkForm({...workForm, source_id: e.target.value})}
                />
                <Input
                  placeholder="מבצע"
                  value={workForm.assignee}
                  onChange={(e) => setWorkForm({...workForm, assignee: e.target.value})}
                />
                <Input
                  type="number"
                  placeholder="זמן משוער (שעות)"
                  value={workForm.estimated_hours}
                  onChange={(e) => setWorkForm({...workForm, estimated_hours: parseFloat(e.target.value)})}
                />
                <Input
                  placeholder="הערות"
                  value={workForm.notes}
                  onChange={(e) => setWorkForm({...workForm, notes: e.target.value})}
                />
                <Button onClick={handleAddWork} className="w-full bg-green-600 hover:bg-green-700">הוסף משימה</Button>
              </>
            )}
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;