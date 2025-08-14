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
import { AlertTriangle, Clock, Settings, Calendar, Plus, Edit, Trash2, Bot, Send, MessageCircle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [activeFailures, setActiveFailures] = useState([]);
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
      const [failuresRes, maintenanceRes, equipmentRes, dailyWorkRes, summaryRes] = await Promise.all([
        axios.get(`${BACKEND_URL}/api/failures`),
        axios.get(`${BACKEND_URL}/api/maintenance`),
        axios.get(`${BACKEND_URL}/api/equipment`),
        axios.get(`${BACKEND_URL}/api/daily-work/today`),
        axios.get(`${BACKEND_URL}/api/dashboard/summary`)
      ]);
      
      setActiveFailures(failuresRes.data);
      setPendingMaintenance(maintenanceRes.data);
      setEquipmentHours(equipmentRes.data);
      setDailyWork(dailyWorkRes.data);
      setDashboardSummary(summaryRes.data);
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
      timestamp: new Date().toISOString()
    };
    setChatMessages(prev => [...prev, newUserMessage]);
    
    try {
      const response = await axios.post(`${BACKEND_URL}/api/ai-chat`, {
        user_message: userMessage
      });
      
      // Add AI response to chat
      const aiMessage = {
        type: 'ai',
        content: response.data.response,
        recommendations: response.data.recommendations || [],
        updated_tables: response.data.updated_tables || [],
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, aiMessage]);
      
      // Refresh data if tables were updated
      if (response.data.updated_tables && response.data.updated_tables.length > 0) {
        fetchData();
      }
      
    } catch (error) {
      console.error('Error sending AI message:', error);
      const errorMessage = {
        type: 'ai',
        content: 'מצטער, הייתה בעיה בחיבור לאייג\'נט AI. נסה שוב.',
        timestamp: new Date().toISOString()
      };
      setChatMessages(prev => [...prev, errorMessage]);
    } finally {
      setAiLoading(false);
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
          <TabsList className="grid w-full grid-cols-6 bg-white shadow-md">
            <TabsTrigger value="dashboard">לוח בקרה</TabsTrigger>
            <TabsTrigger value="ai-agent">האייג'נט AI</TabsTrigger>
            <TabsTrigger value="failures">תקלות פעילות</TabsTrigger>
            <TabsTrigger value="maintenance">אחזקות ממתינות</TabsTrigger>
            <TabsTrigger value="equipment">שעות מכלולים</TabsTrigger>
            <TabsTrigger value="daily-work">תכנון יומי</TabsTrigger>
          </TabsList>

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
                  <CardTitle>ציוד דורש טיפול</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {equipmentHours.filter(eq => eq.alert_level === 'אדום').slice(0, 3).map(equipment => (
                      <div key={equipment.id} className="flex items-center justify-between p-3 bg-red-50 rounded-lg">
                        <div>
                          <p className="font-medium">{equipment.system}</p>
                          <p className="text-sm text-gray-600">{equipment.current_hours} שעות נוכחיות</p>
                        </div>
                        <Badge variant={getAlertColor(equipment.alert_level)}>
                          {equipment.alert_level}
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
                    <div className="flex-1 overflow-y-auto mb-4 space-y-4 bg-gray-50 rounded-lg p-4">
                      {chatMessages.length === 0 && (
                        <div className="text-center text-gray-500 mt-8">
                          <Bot className="h-12 w-12 mx-auto mb-4 text-blue-600" />
                          <p className="text-lg font-medium">שלום יהל! 👋</p>
                          <p>אני כאן לעזור לך בניהול המחלקה ובליווי מנהיגותי.</p>
                          <div className="mt-4 text-sm text-right">
                            <p>דוגמאות לשאלות:</p>
                            <ul className="mt-2 space-y-1">
                              <li>"מה המצב הנוכחי במחלקה?"</li>
                              <li>"איזה תקלות דחופות יש לי?"</li>
                              <li>"איך אני מתקדם בתפקיד?"</li>
                              <li>"מה העדיפויות שלי השבוע?"</li>
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
                    <div className="flex space-x-2">
                      <Input
                        value={currentMessage}
                        onChange={(e) => setCurrentMessage(e.target.value)}
                        placeholder="שאל את ג'סיקה על המחלקה או קבל ייעוץ מנהיגותי..."
                        onKeyPress={(e) => e.key === 'Enter' && !e.shiftKey && sendAiMessage()}
                        disabled={aiLoading}
                        className="flex-1"
                      />
                      <Button 
                        onClick={sendAiMessage}
                        disabled={aiLoading || !currentMessage.trim()}
                        className="bg-blue-600 hover:bg-blue-700"
                      >
                        <Send className="h-4 w-4" />
                      </Button>
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
                            <Button size="sm" variant="outline">
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
                            <Button size="sm" variant="outline">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('maintenance', maintenance.id)}
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
                            <Button size="sm" variant="outline">
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
                            <Button size="sm" variant="outline">
                              <Edit className="h-4 w-4" />
                            </Button>
                            <Button 
                              size="sm" 
                              variant="destructive"
                              onClick={() => handleDelete('daily-work', work.id)}
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