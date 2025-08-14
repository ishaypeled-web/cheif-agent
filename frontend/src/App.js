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
import { AlertTriangle, Clock, Settings, Calendar, Plus, Edit, Trash2 } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [activeFailures, setActiveFailures] = useState([]);
  const [pendingMaintenance, setPendingMaintenance] = useState([]);
  const [equipmentHours, setEquipmentHours] = useState([]);
  const [dailyWork, setDailyWork] = useState([]);
  const [dashboardSummary, setDashboardSummary] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');

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
          <TabsList className="grid w-full grid-cols-5 bg-white shadow-md">
            <TabsTrigger value="dashboard">לוח בקרה</TabsTrigger>
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
          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}

export default App;