import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
    Card,
    Row,
    Col,
    Button,
    Select,
    Input,
    Table,
    Space,
    Modal,
    Form,
    DatePicker,
    TimePicker,
    Switch,
    Tabs,
    Divider,
    Tag,
    Tooltip,
    Popconfirm,
    Menu,
    Layout,
    Typography,
    Badge,
    Spin,
    Checkbox,
    Tree,
    Alert,
    Timeline,
    Progress,
    Drawer,
    Empty,
    Segmented,
    App,
} from 'antd';
import {
    FileExcelOutlined,
    FilePdfOutlined,
    FileOutlined,
    DownloadOutlined,
    ScheduleOutlined,
    SettingOutlined,
    StarOutlined,
    StarFilled,
    FilterOutlined,
    ReloadOutlined,
    BarChartOutlined,
    LineChartOutlined,
    PieChartOutlined,
    TableOutlined,
    ToolOutlined,
    BuildOutlined,
    UserOutlined,
    CalendarOutlined,
    SafetyCertificateOutlined,
    IdcardOutlined,
    TeamOutlined,
    FileTextOutlined,
    MailOutlined,
    ClockCircleOutlined,
    PlusOutlined,
    HistoryOutlined,
    CheckCircleOutlined,
    ExclamationCircleOutlined,
    WarningOutlined,
    LoginOutlined,
    LogoutOutlined,
    FullscreenOutlined,
    FullscreenExitOutlined,
    EyeOutlined,
    EyeInvisibleOutlined,
    GlobalOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    SearchOutlined,
    TrophyOutlined,
} from '@ant-design/icons';
import axios from 'axios';
import CustomReportBuilder from './components/CustomReportBuilder';
import { AgGridReact } from 'ag-grid-react';
import 'ag-grid-community/styles/ag-grid.css';
import 'ag-grid-community/styles/ag-theme-alpine.css';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip as RechartTooltip, Legend, ResponsiveContainer,
} from 'recharts';
import dayjs from 'dayjs';

const { Header, Sider, Content } = Layout;
const { RangePicker } = DatePicker;
const { Option } = Select;
const { Search } = Input;
const { Title, Text } = Typography;
const Reports = () => {
  const { message } = App.useApp();
  // State management
  const [loading, setLoading] = useState(false);
  const [selectedReport, setSelectedReport] = useState(null);
  const [reportData, setReportData] = useState(null);
  const [filters, setFilters] = useState({});
  const [columns, setColumns] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [chartType, setChartType] = useState('bar');
  const [activeTab, setActiveTab] = useState('reports');
  const [showChart, setShowChart] = useState(false);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [favorites, setFavorites] = useState([]);
  const [presets, setPresets] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [zones, setZones] = useState([]);
  const [schedules, setSchedules] = useState([]);

  // Enhanced features state
  const [viewMode, setViewMode] = useState('table');  // 'table' | 'timeline'
  const [hiddenColumns, setHiddenColumns] = useState(new Set());
  const [sidebarSearch, setSidebarSearch] = useState('');
  const [autoRefreshOn, setAutoRefreshOn] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [favDrawerOpen, setFavDrawerOpen] = useState(false);
  const autoRefreshRef = useRef(null);
  const [recentReports, setRecentReports] = useState(() => {
    try { return JSON.parse(localStorage.getItem('pob_rpt_recent') || '[]'); }
    catch { return []; }
  });
  const [favReports, setFavReports] = useState(() => {
    try { return new Set(JSON.parse(localStorage.getItem('pob_rpt_favs') || '[]')); }
    catch { return new Set(); }
  });
  
  // Modal states
  const [templateModalVisible, setTemplateModalVisible] = useState(false);
  const [scheduleModalVisible, setScheduleModalVisible] = useState(false);
  const [columnModalVisible, setColumnModalVisible] = useState(false);
  const [exportModalVisible, setExportModalVisible] = useState(false);
  
  // Form instances
  const [scheduleForm] = Form.useForm();

  // Report categories with BioTime 9.5 structure
  const reportCategories = [
    {
      key: 'personnel',
      title: 'Personnel',
      icon: <UserOutlined />,
      reports: [
        { key: 'personnel.employee_list', title: 'Employee List', description: 'Complete employee listing with details' },
        { key: 'personnel.dept_summary', title: 'Department Summary', description: 'Personnel count by department' },
        { key: 'personnel.birthday', title: 'Birthday List', description: 'Employee birthdays by month' },
        { key: 'personnel.anniversary', title: 'Work Anniversary', description: 'Service anniversary tracking' },
        { key: 'personnel.contractor', title: 'Contractor List', description: 'Contractor personnel listing' },
      ]
    },
    {
      key: 'attendance',
      title: 'Attendance',
      icon: <CalendarOutlined />,
      reports: [
        { key: 'att.daily', title: 'Daily Attendance', description: 'Daily attendance report with in/out times' },
        { key: 'att.monthly', title: 'Monthly Summary', description: 'Monthly attendance summary by employee' },
        { key: 'att.summary', title: 'Attendance Summary', description: 'Overall attendance statistics' },
        { key: 'att.late', title: 'Late Arrival', description: 'Late arrival analysis' },
        { key: 'att.early', title: 'Early Departure', description: 'Early departure tracking' },
        { key: 'att.absent', title: 'Absenteeism', description: 'Absenteeism analysis' },
        { key: 'att.ot', title: 'Overtime', description: 'Overtime hours tracking' },
        { key: 'att.leave', title: 'Leave Report', description: 'Leave balance and usage' },
        { key: 'att.shift', title: 'Shift Schedule', description: 'Shift scheduling report' },
        { key: 'att.exceptions', title: 'Exceptions', description: 'Attendance exceptions and anomalies' },
      ]
    },
    {
      key: 'payroll',
      title: 'Payroll',
      icon: <FileTextOutlined />,
      reports: [
        { key: 'pay.salary_summary', title: 'Salary Summary', description: 'Payroll salary summary by department' },
        { key: 'pay.payslip_bulk', title: 'Payslip Bulk', description: 'Bulk payslip generation' },
        { key: 'pay.bank_sheet', title: 'Bank Sheet', description: 'Bank payment sheet export' },
        { key: 'pay.item_wise', title: 'Item-wise', description: 'Detailed payroll item breakdown' },
        { key: 'pay.variance', title: 'Variance', description: 'Payroll variance analysis' },
        { key: 'pay.zone_cost', title: 'Warehouse Cost', description: 'POB zone cost analysis' },
        { key: 'pay.contractor_cost', title: 'Contractor Cost', description: 'Contractor cost tracking' },
      ]
    },
    {
      key: 'system',
      title: 'System',
      icon: <SettingOutlined />,
      reports: [
        { key: 'system.operation_log', title: 'Operation Log', description: 'System operation audit trail' },
        { key: 'system.login_log', title: 'Login Log', description: 'User login history' },
        { key: 'system.data_audit', title: 'Data Audit', description: 'Data change audit log' },
        { key: 'system.license_usage', title: 'License Usage', description: 'License utilization' },
        { key: 'system.api_usage', title: 'API Usage', description: 'API call statistics' },
      ]
    },
  ];

  // Initialize component
  useEffect(() => {
    loadTemplates();
    loadFavorites();
    loadPresets();
    loadDepartments();
    loadZones();
    loadSchedules();
  }, []);

  // Load templates
  const loadTemplates = async () => {
    try {
      const response = await fetch('/api/v1/report/templates/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setTemplates(data);
    } catch (error) {
      console.error('Error loading templates:', error);
    }
  };

  // Load favorites
  const loadFavorites = async () => {
    try {
      const response = await fetch('/api/v1/report/favorites/', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      const data = await response.json();
      setFavorites(data);
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  // Load presets
  const loadPresets = async () => {
    try {
      const response = await fetch('/api/v1/report/presets/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      const data = await response.json();
      setPresets(data);
    } catch (error) {
      console.error('Error loading presets:', error);
    }
  };

  // Load departments dynamically
  const loadDepartments = async () => {
    try {
      const response = await fetch('/api/v1/departments/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        const depts = Array.isArray(data) ? data : (data.results || data.data || []);
        setDepartments(depts.map(d => typeof d === 'string' ? d : (d.dept_name || d.name || d)));
      }
    } catch (error) {
      console.error('Error loading departments:', error);
    }
  };

  // Load zones for POB reports
  const loadZones = async () => {
    try {
      const response = await fetch('/api/v1/zones/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        const zList = Array.isArray(data) ? data : (data.results || data.zones || data.data || []);
        setZones(zList.filter(z => z && z.id).map(z => ({ id: z.id, name: z.name || `Warehouse ${z.id}` })));
      }
    } catch (error) {
      console.error('Error loading zones:', error);
    }
  };

  // Load schedules
  const loadSchedules = async () => {
    try {
      const response = await fetch('/api/v1/report/schedules/', {
        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` }
      });
      if (response.ok) {
        const data = await response.json();
        setSchedules(Array.isArray(data) ? data : []);
      }
    } catch (error) {
      console.error('Error loading schedules:', error);
    }
  };

  // Convert simple frequency + time + dow to a cron expression
  const buildCron = (frequency, timeVal, dow) => {
    const h = timeVal ? timeVal.hour() : 8;
    const m = timeVal ? timeVal.minute() : 0;
    if (frequency === 'hourly')  return `${m} * * * *`;
    if (frequency === 'daily')   return `${m} ${h} * * *`;
    if (frequency === 'weekly')  return `${m} ${h} * * ${dow ?? 1}`;
    if (frequency === 'monthly') return `${m} ${h} 1 * *`;
    return `${m} ${h} * * *`; // fallback daily
  };

  // Create a schedule via the API
  const createSchedule = async (values) => {
    if (!values.template_id) {
      message.warning('Select a report template to schedule');
      return;
    }
    const cron = buildCron(values.frequency, values.run_time, values.dow);
    const recipients = {
      users:  [],
      emails: (values.recipient_emails || []).filter(Boolean),
      roles:  [],
    };
    const token = localStorage.getItem('token') || localStorage.getItem('auth_token') || '';
    try {
      const res = await fetch('/api/v1/report/schedules/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({
          template_id: values.template_id,
          schedule_name: values.schedule_name,
          cron,
          format: values.format || 'xlsx',
          recipients,
        }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `HTTP ${res.status}`);
      }
      message.success('Schedule created');
      setScheduleModalVisible(false);
      scheduleForm.resetFields();
      loadSchedules();
    } catch (e) {
      message.error(`Failed to create schedule: ${e.message}`);
    }
  };

  // Load report data
  const loadReportData = async (reportCode, reportFilters = {}) => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/report/data/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          report_code: reportCode,
          filters: reportFilters,
          page: 1,
          page_size: 100
        })
      });

      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.detail || `HTTP ${response.status}`);
      }
      setReportData(data);
      setColumns(data.columns || []);
      setChartData(data.chart_data || {});
      setChartType(data.chart_data && Object.keys(data.chart_data).length ? 'bar' : 'none');
    } catch (error) {
      console.error('Error loading report data:', error);
      message.error(`Failed to load report: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Handle report selection
  const handleReportSelect = (reportInfo) => {
    setSelectedReport(reportInfo);
    setFilters({});
    setViewMode('table');
    loadReportData(reportInfo.key, {});
    // Push to recent (deduplicated, max 8)
    setRecentReports(prev => {
      const next = [reportInfo, ...prev.filter(r => r.key !== reportInfo.key)].slice(0, 8);
      localStorage.setItem('pob_rpt_recent', JSON.stringify(next));
      return next;
    });
  };

  // Toggle favourite at report level (localStorage, no backend needed)
  const handleFavReportToggle = (reportInfo, e) => {
    e.stopPropagation();
    setFavReports(prev => {
      const next = new Set(prev);
      if (next.has(reportInfo.key)) next.delete(reportInfo.key);
      else next.add(reportInfo.key);
      localStorage.setItem('pob_rpt_favs', JSON.stringify([...next]));
      return next;
    });
  };

  // Auto-refresh effect
  useEffect(() => {
    if (autoRefreshOn && selectedReport) {
      autoRefreshRef.current = setInterval(() => {
        loadReportData(selectedReport.key, filters);
      }, 30000); // 30s
    }
    return () => { if (autoRefreshRef.current) clearInterval(autoRefreshRef.current); };
  }, [autoRefreshOn, selectedReport?.key]);

  // Handle filter change
  const handleFilterChange = (key, value) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    
    if (selectedReport) {
      loadReportData(selectedReport.key, newFilters);
    }
  };

  // Handle export
  const handleExport = async (format) => {
    if (!selectedReport) {
      message.warning('Please select a report first');
      return;
    }

    try {
      const response = await fetch('/api/v1/report/export/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          report_code: selectedReport.key,
          filters: filters,
          format: format
        })
      });
      
      const data = await response.json();
      
      if (data.task_id) {
        message.success(`Export queued. Task ID: ${data.task_id}`);
        // Poll for completion
        pollExportStatus(data.task_id);
      }
    } catch (error) {
      console.error('Error exporting report:', error);
      message.error('Failed to export report');
    }
  };

  // Poll export status
  const pollExportStatus = async (taskId) => {
    const interval = setInterval(async () => {
      try {
        const response = await fetch(`/api/v1/report/export/${taskId}/status/`, {
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });
        
        const data = await response.json();
        
        if (data.status === 'completed') {
          clearInterval(interval);
          message.success('Export completed successfully');
          // Download file
          window.open(`/api/v1/report/export/${taskId}/download/`, '_blank');
        } else if (data.status === 'failed') {
          clearInterval(interval);
          message.error(`Export failed: ${data.error_message}`);
        }
      } catch (error) {
        console.error('Error polling export status:', error);
      }
    }, 2000);
  };

  // Handle favorite toggle
  const handleFavoriteToggle = async (templateId) => {
    try {
      const response = await fetch(`/api/v1/report/favorites/${templateId}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        message.success('Added to favorites');
        loadFavorites();
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  // Render sidebar tree with search, favorites, recent
  const renderSidebarTree = () => {
    const q = sidebarSearch.toLowerCase();
    const allReports = reportCategories.flatMap(cat => cat.reports);

    const makeLeaf = (report) => ({
      title: (
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis' }}>{report.title}</span>
          <span
            onClick={(e) => handleFavReportToggle(report, e)}
            style={{ marginLeft: 6, cursor: 'pointer', color: favReports.has(report.key) ? '#faad14' : '#d9d9d9', flexShrink: 0 }}
          >
            {favReports.has(report.key) ? <StarFilled /> : <StarOutlined />}
          </span>
        </div>
      ),
      key: report.key,
      isLeaf: true,
    });

    // makeLeaf with optional key prefix to avoid duplicate keys across fav/recent/main sections
    const makePrefixedLeaf = (prefix) => (report) => ({
      ...makeLeaf(report),
      key: `${prefix}${report.key}`,
    });

    // Favorites section
    const favItems = allReports.filter(r => favReports.has(r.key));
    const favNode = favItems.length > 0 ? [{
      title: (
        <span style={{ fontWeight: 600, color: '#faad14' }}>
          <StarFilled style={{ marginRight: 6 }} />Favorites
        </span>
      ),
      key: '__favs__',
      selectable: false,
      children: favItems.map(makePrefixedLeaf('fav__')),
    }] : [];

    // Recent section
    const recentNode = recentReports.length > 0 && !q ? [{
      title: (
        <span style={{ fontWeight: 600, color: '#1677ff' }}>
          <HistoryOutlined style={{ marginRight: 6 }} />Recent
        </span>
      ),
      key: '__recent__',
      selectable: false,
      children: recentReports.map(makePrefixedLeaf('rec__')),
    }] : [];

    // Category tree, filtered by search
    const categoryNodes = reportCategories
      .map(category => {
        const filtered = q
          ? category.reports.filter(r =>
              r.title.toLowerCase().includes(q) || r.description.toLowerCase().includes(q))
          : category.reports;
        if (filtered.length === 0) return null;
        return {
          title: (
            <span style={{ fontWeight: 500 }}>
              {category.icon}
              <span style={{ marginLeft: 8 }}>{category.title}</span>
              <Tag style={{ marginLeft: 8, fontSize: 10 }}>{filtered.length}</Tag>
            </span>
          ),
          key: category.key,
          selectable: false,
          children: filtered.map(makeLeaf),
        };
      })
      .filter(Boolean);

    const treeData = [...favNode, ...recentNode, ...categoryNodes];

    return (
      <Tree
        treeData={treeData}
        defaultExpandAll={!!q}
        selectedKeys={selectedReport ? [selectedReport.key] : []}
        onSelect={(selectedKeys) => {
          if (selectedKeys.length > 0) {
            // Strip fav__ / rec__ prefix added to avoid duplicate tree keys
            const raw = String(selectedKeys[0]).replace(/^(fav__|rec__)/, '');
            const reportInfo = allReports.find(r => r.key === raw);
            if (reportInfo) handleReportSelect(reportInfo);
          }
        }}
        style={{ userSelect: 'none' }}
      />
    );
  };

  // Render AG-Grid column definitions — respects hiddenColumns set
  const getGridColumnDefs = () => {
    return columns.map(col => ({
      headerName: col.label,
      field: col.field,
      hide: hiddenColumns.has(col.field),
      sortable: true,
      filter: true,
      resizable: true,
      width: col.width || 150,
      type: col.type === 'number' ? 'numericColumn' : undefined,
      cellRenderer: (params) => {
        const value = params.value;
        if (col.type === 'currency') return `$${Number(value).toLocaleString()}`;
        if (col.type === 'percentage') return `${Number(value).toFixed(1)}%`;
        if (col.type === 'date' && value) return dayjs(value).format('YYYY-MM-DD');
        if (col.type === 'datetime' && value) return dayjs(value).format('YYYY-MM-DD HH:mm');
        if (col.type === 'boolean') return value ? 'Yes' : 'No';
        return value;
      }
    }));
  };

  // Derive chart data from report rows when the backend sends no chart_data
  const getAutoChartData = () => {
    if (!reportData?.data?.length || !columns?.length) return null;
    const labelCol = columns.find(c => !c.type || c.type === 'string' || c.type === 'text');
    const valueCol = columns.find(c => c.type === 'number' || c.type === 'currency' || c.type === 'integer');
    if (!labelCol || !valueCol) return null;
    return reportData.data
      .slice(0, 20)
      .map(row => ({
        category: String(row[labelCol.field] ?? ''),
        value: Number(row[valueCol.field] ?? 0),
      }))
      .filter(d => d.category);
  };

  // Render chart based on type — using recharts (consistent with rest of app)
  const renderChart = () => {
    if (!showChart) return null;

    let data;
    const labels = chartData?.labels || [];
    if (labels.length > 0) {
      const dataset = chartData.datasets?.[0] || {};
      const values = dataset.data || [];
      data = labels.map((label, i) => ({
        category: String(label || ''),
        value: Number(values[i] ?? 0),
      }));
    } else {
      data = getAutoChartData();
    }
    if (!data?.length) return null;

    const COLORS = ['#3B82F6', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6',
                    '#06B6D4', '#F97316', '#84CC16', '#EC4899', '#6366F1'];

    const commonProps = {
      data,
      margin: { top: 10, right: 20, left: 10, bottom: 60 },
    };

    const xAxisProps = {
      dataKey: 'category',
      tick: { fontSize: 11, fill: '#555' },
      angle: -30,
      textAnchor: 'end',
      interval: 0,
    };

    switch (chartType) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis {...xAxisProps} />
              <YAxis tick={{ fontSize: 11 }} />
              <RechartTooltip />
              <Legend />
              <Line type="monotone" dataKey="value" stroke="#3B82F6" strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        );
      case 'pie':
        return (
          <ResponsiveContainer width="100%" height={320}>
            <PieChart>
              <Pie
                data={data}
                dataKey="value"
                nameKey="category"
                cx="50%"
                cy="45%"
                outerRadius={110}
                label={({ category, percent }) => `${category} (${(percent * 100).toFixed(0)}%)`}
                labelLine
              >
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Pie>
              <RechartTooltip formatter={(v) => v.toLocaleString()} />
              <Legend />
            </PieChart>
          </ResponsiveContainer>
        );
      case 'bar':
      case 'heatmap':
      default:
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis {...xAxisProps} />
              <YAxis tick={{ fontSize: 11 }} />
              <RechartTooltip formatter={(v) => v.toLocaleString()} />
              <Legend />
              <Bar dataKey="value" name={chartData?.datasets?.[0]?.label || 'Value'} radius={[4, 4, 0, 0]}>
                {data.map((_, i) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        );
    }
  };

  // Determine if the selected report supports timeline view
  const isTimelineReport = () => {
    const key = selectedReport?.key || '';
    return ['zone.access_log', 'zone.person_trail', 'zone.security_events',
            'ac.events', 'ac.antipassback', 'att.daily', 'att.exceptions',
            'att.late', 'att.absent', 'muster.event'].includes(key);
  };

  // Derive the time field name from report columns
  const getTimeField = () => {
    const timeFields = ['punch_time', 'event_time', 'timestamp', 'check_time', 'in_time', 'date'];
    const colFields = columns.map(c => c.field);
    return timeFields.find(f => colFields.includes(f)) || colFields[0];
  };

  // Event color by type/field value
  const eventColor = (row) => {
    const et = (row.event_type || '').toLowerCase();
    if (et.includes('clock_in') || et.includes('entry') || et.includes('in')) return 'green';
    if (et.includes('clock_out') || et.includes('exit') || et.includes('out')) return 'red';
    if (et.includes('alarm') || et.includes('tamper') || et.includes('duress')) return '#cf1322';
    if (et.includes('anti') || et.includes('passback')) return 'orange';
    if (et.includes('late')) return 'orange';
    if (et.includes('absent')) return 'red';
    return 'blue';
  };

  const eventIcon = (row) => {
    const et = (row.event_type || '').toLowerCase();
    if (et.includes('clock_in') || et.includes('entry')) return <LoginOutlined />;
    if (et.includes('clock_out') || et.includes('exit')) return <LogoutOutlined />;
    if (et.includes('alarm') || et.includes('tamper') || et.includes('duress')) return <ExclamationCircleOutlined />;
    if (et.includes('anti') || et.includes('passback') || et.includes('late')) return <WarningOutlined />;
    return <CheckCircleOutlined />;
  };

  // Render timeline view for event-based reports
  const renderTimeline = () => {
    const rows = reportData?.data || [];
    if (!rows.length) return <Empty description="No events to display" style={{ padding: 40 }} />;

    const timeField = getTimeField();
    const nameField = columns.find(c => ['full_name', 'emp_code', 'name', 'user'].includes(c.field))?.field || columns[1]?.field;
    const zoneField = columns.find(c => ['zone_name', 'location', 'area'].includes(c.field))?.field;
    const detailField = columns.find(c => ['event_type', 'type', 'status'].includes(c.field))?.field;

    // Sort by time descending for timeline display
    const sorted = [...rows].sort((a, b) => {
      const ta = a[timeField] ? new Date(a[timeField]) : 0;
      const tb = b[timeField] ? new Date(b[timeField]) : 0;
      return tb - ta;
    });

    // Group by date
    const groups = {};
    sorted.forEach(row => {
      const dt = row[timeField] ? new Date(row[timeField]) : null;
      const dateKey = dt ? dt.toLocaleDateString('en-GB', { weekday: 'short', day: '2-digit', month: 'short', year: 'numeric' }) : 'Unknown Date';
      if (!groups[dateKey]) groups[dateKey] = [];
      groups[dateKey].push(row);
    });

    return (
      <div style={{ maxHeight: fullscreen ? 'calc(100vh - 200px)' : 520, overflowY: 'auto', paddingRight: 8 }}>
        {Object.entries(groups).map(([dateKey, dateRows]) => (
          <div key={dateKey} style={{ marginBottom: 24 }}>
            <Divider orientation="left">
              <Tag color="blue" style={{ fontSize: 12 }}>{dateKey} — {dateRows.length} event{dateRows.length !== 1 ? 's' : ''}</Tag>
            </Divider>
            <Timeline
              items={dateRows.map((row, i) => {
                const dt = row[timeField] ? new Date(row[timeField]) : null;
                const timeStr = dt ? dt.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' }) : '';
                const name = nameField ? row[nameField] : '';
                const zone = zoneField ? row[zoneField] : '';
                const detail = detailField ? row[detailField] : '';
                const color = eventColor(row);
                const icon = eventIcon(row);

                return {
                  key: i,
                  color,
                  dot: <span style={{ fontSize: 14, color }}>{icon}</span>,
                  children: (
                    <div style={{ paddingBottom: 4 }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                        <span style={{ fontWeight: 600, fontSize: 13 }}>{timeStr}</span>
                        {name && <Tag>{name}</Tag>}
                        {zone && <Tag color="geekblue">{zone}</Tag>}
                        {detail && <Tag color={color === 'green' ? 'success' : color === 'red' ? 'error' : 'warning'}>{detail}</Tag>}
                      </div>
                      {/* Extra fields */}
                      <div style={{ marginTop: 2, fontSize: 12, color: '#888' }}>
                        {columns
                          .filter(c => ![timeField, nameField, zoneField, detailField].includes(c.field) && row[c.field])
                          .map(c => <span key={c.field} style={{ marginRight: 12 }}>{c.label}: <strong>{String(row[c.field])}</strong></span>)
                        }
                      </div>
                    </div>
                  ),
                };
              })}
            />
          </div>
        ))}
      </div>
    );
  };

  // Render filter bar
  // Quick date preset helper
  const applyDatePreset = (preset) => {
    const today = dayjs();
    let from, to;
    if (preset === 'today')       { from = today;                      to = today; }
    if (preset === 'yesterday')   { from = today.subtract(1, 'day');   to = today.subtract(1, 'day'); }
    if (preset === 'last7')       { from = today.subtract(6, 'day');   to = today; }
    if (preset === 'last30')      { from = today.subtract(29, 'day');  to = today; }
    if (preset === 'thismonth')   { from = today.startOf('month');     to = today.endOf('month'); }
    if (preset === 'lastmonth')   { from = today.subtract(1,'month').startOf('month'); to = today.subtract(1,'month').endOf('month'); }
    const fmt = 'YYYY-MM-DD';
    const newFilters = { ...filters, date_from: from.format(fmt), date_to: to.format(fmt) };
    setFilters(newFilters);
    if (selectedReport) loadReportData(selectedReport.key, newFilters);
  };

  const DatePresets = () => (
    <Space size={4} wrap style={{ marginBottom: 8 }}>
      {[
        { k: 'today',     label: 'Today' },
        { k: 'yesterday', label: 'Yesterday' },
        { k: 'last7',     label: 'Last 7d' },
        { k: 'last30',    label: 'Last 30d' },
        { k: 'thismonth', label: 'This Month' },
        { k: 'lastmonth', label: 'Last Month' },
      ].map(p => (
        <Button key={p.k} size="small" type="default" onClick={() => applyDatePreset(p.k)}>
          {p.label}
        </Button>
      ))}
    </Space>
  );

  // Single-date attendance reports
  const ATT_SINGLE_DATE = ['att.late', 'att.early', 'att.absent', 'att.ot'];
  // Range-based attendance reports
  const ATT_RANGE = ['att.daily', 'att.summary', 'att.leave', 'att.exceptions', 'att.shift'];

  const ATT_STATUSES = ['Present', 'Late', 'Early Leave', 'Absent', 'Leave'];

  const renderFilterBar = () => {
    const reportKey = selectedReport?.key || '';
    const isZoneReport = reportKey.startsWith('zone.');
    const isAttReport  = reportKey.startsWith('att.');

    if (isZoneReport) {
      return (
        <Card size="small" style={{ marginBottom: 16 }}>
          <DatePresets />
          <Row gutter={[16, 8]} align="middle">
            <Col>
              <RangePicker
                placeholder={['Date From', 'Date To']}
                value={filters.date_from ? [dayjs(filters.date_from), dayjs(filters.date_to)] : null}
                onChange={(dates) => {
                  if (dates) {
                    const nf = { ...filters, date_from: dates[0].format('YYYY-MM-DD'), date_to: dates[1].format('YYYY-MM-DD') };
                    setFilters(nf);
                    if (selectedReport) loadReportData(selectedReport.key, nf);
                  } else {
                    const nf = { ...filters };
                    delete nf.date_from; delete nf.date_to;
                    setFilters(nf);
                    if (selectedReport) loadReportData(selectedReport.key, nf);
                  }
                }}
              />
            </Col>

            {(reportKey === 'zone.access_log' || reportKey === 'zone.person_trail') && (
              <Col>
                <Input
                  placeholder="Employee Code"
                  style={{ width: 160 }}
                  allowClear
                  onPressEnter={(e) => handleFilterChange('emp_code', e.target.value || undefined)}
                  onBlur={(e) => handleFilterChange('emp_code', e.target.value || undefined)}
                  suffix={
                    <Tooltip title="Enter the employee badge/code number">
                      <UserOutlined style={{ color: '#999' }} />
                    </Tooltip>
                  }
                />
              </Col>
            )}

            {reportKey === 'zone.security_events' && (
              <Col>
                <Select
                  placeholder="Event Type"
                  style={{ width: 170 }}
                  allowClear
                  onChange={(value) => handleFilterChange('event_type', value)}
                >
                  <Option value="Alarm">Alarm</Option>
                  <Option value="Tamper">Tamper</Option>
                  <Option value="Anti-Passback">Anti-Passback</Option>
                  <Option value="Duress">Duress</Option>
                  <Option value="Fire Unlock">Fire Unlock</Option>
                  <Option value="Emergency Lock">Emergency Lock</Option>
                  <Option value="Door Open Too Long">Door Open Too Long</Option>
                </Select>
              </Col>
            )}
          </Row>
        </Card>
      );
    }

    // POB Operations filter bar
    if (reportKey.startsWith('pob.')) {
      const isCrewChange   = reportKey === 'pob.crew_change';
      const isManifest     = reportKey === 'pob.daily_manifest';
      const isOverdue      = reportKey === 'pob.rotation_overdue';
      const isOccHistory   = reportKey === 'pob.zone_occupancy_history';
      const isHeadByCompany = reportKey === 'pob.headcount_by_company';
      return (
        <Card size="small" style={{ marginBottom: 16 }}>
          <Row gutter={[16, 8]} align="middle" wrap>
            {/* Date picker — single date for crew change */}
            {isCrewChange && (
              <Col>
                <DatePicker
                  placeholder="Crew Change Date"
                  value={filters.date ? dayjs(filters.date) : dayjs()}
                  onChange={(d) => handleFilterChange('date', d ? d.format('YYYY-MM-DD') : undefined)}
                />
              </Col>
            )}
            {/* Date range for zone occupancy history */}
            {isOccHistory && (
              <Col>
                <RangePicker
                  placeholder={['Date From', 'Date To']}
                  value={filters.date_from ? [dayjs(filters.date_from), dayjs(filters.date_to || filters.date_from)] : null}
                  onChange={(dates) => {
                    if (dates) {
                      const nf = { ...filters, date_from: dates[0].format('YYYY-MM-DD'), date_to: dates[1].format('YYYY-MM-DD') };
                      setFilters(nf); if (selectedReport) loadReportData(selectedReport.key, nf);
                    } else {
                      const nf = { ...filters }; delete nf.date_from; delete nf.date_to;
                      setFilters(nf); if (selectedReport) loadReportData(selectedReport.key, nf);
                    }
                  }}
                />
              </Col>
            )}
            {/* Change type for crew change */}
            {isCrewChange && (
              <Col>
                <Select placeholder="All Changes" style={{ width: 160 }} allowClear
                  onChange={(v) => handleFilterChange('change_type', v)}>
                  <Option value="MOBILIZE">Mobilize (Check-In)</Option>
                  <Option value="DEMOBILIZE">Demobilize (Check-Out)</Option>
                </Select>
              </Col>
            )}
            {/* Warehouse filter for manifest and occupancy history */}
            {(isManifest || isOccHistory) && (
              <Col>
                <Select placeholder="All Warehouses" style={{ width: 160 }} allowClear showSearch
                  filterOption={(inp, opt) => opt.children.toLowerCase().includes(inp.toLowerCase())}
                  onChange={(v) => handleFilterChange('zone_id', v)}>
                  {zones.map(z => <Option key={z.id} value={z.id}>{z.name}</Option>)}
                </Select>
              </Col>
            )}
            {/* Department filter */}
            {(isManifest || isOverdue) && (
              <Col>
                <Select placeholder="Department" style={{ width: 150 }} allowClear showSearch
                  filterOption={(inp, opt) => opt.children.toLowerCase().includes(inp.toLowerCase())}
                  onChange={(v) => handleFilterChange('department', v)}>
                  {departments.map(d => <Option key={d} value={d}>{d}</Option>)}
                </Select>
              </Col>
            )}
            {/* Personnel type for manifest */}
            {isManifest && (
              <Col>
                <Select placeholder="Type" style={{ width: 130 }} allowClear
                  onChange={(v) => handleFilterChange('personnel_type', v)}>
                  <Option value="STAFF">Staff</Option>
                  <Option value="CONTRACTOR">Contractor</Option>
                  <Option value="VISITOR">Visitor</Option>
                </Select>
              </Col>
            )}
            {/* Company filter (text) */}
            {(isManifest || isOverdue || isHeadByCompany) && (
              <Col>
                <Input placeholder="Company" style={{ width: 160 }} allowClear
                  onPressEnter={(e) => handleFilterChange('company', e.target.value || undefined)}
                  onBlur={(e) => handleFilterChange('company', e.target.value || undefined)}
                />
              </Col>
            )}
            {/* Threshold days for rotation overdue */}
            {isOverdue && (
              <Col>
                <Input
                  type="number" min={1} placeholder="Threshold (days)" style={{ width: 160 }}
                  defaultValue={28}
                  onPressEnter={(e) => handleFilterChange('threshold_days', parseInt(e.target.value) || 28)}
                  onBlur={(e) => handleFilterChange('threshold_days', parseInt(e.target.value) || 28)}
                />
              </Col>
            )}
            <Col>
              <Button type="primary" onClick={() => { if (selectedReport) loadReportData(selectedReport.key, filters); }}>
                Run Report
              </Button>
            </Col>
          </Row>
        </Card>
      );
    }

    // Attendance filter bar
    if (isAttReport) {
      const isSingleDate = ATT_SINGLE_DATE.includes(reportKey);
      const isMonthly    = reportKey === 'att.monthly';

      return (
        <Card size="small" style={{ marginBottom: 16 }}>
          {!isSingleDate && !isMonthly && <DatePresets />}
          <Row gutter={[16, 8]} align="middle" wrap>
            {/* Date picker: range, single, or month depending on report */}
            <Col>
              {isMonthly ? (
                <DatePicker
                  picker="month"
                  placeholder="Select Month"
                  value={filters.month ? dayjs(filters.month + '-01') : null}
                  onChange={(d) => {
                    const val = d ? d.format('YYYY-MM') : undefined;
                    handleFilterChange('month', val);
                  }}
                />
              ) : isSingleDate ? (
                <DatePicker
                  placeholder="Select Date"
                  value={filters.date ? dayjs(filters.date) : dayjs().subtract(1, 'day')}
                  onChange={(d) => handleFilterChange('date', d ? d.format('YYYY-MM-DD') : undefined)}
                />
              ) : (
                <RangePicker
                  placeholder={['Date From', 'Date To']}
                  value={filters.date_from ? [dayjs(filters.date_from), dayjs(filters.date_to || filters.date_from)] : null}
                  onChange={(dates) => {
                    if (dates) {
                      const nf = { ...filters, date_from: dates[0].format('YYYY-MM-DD'), date_to: dates[1].format('YYYY-MM-DD') };
                      setFilters(nf);
                      if (selectedReport) loadReportData(selectedReport.key, nf);
                    } else {
                      const nf = { ...filters };
                      delete nf.date_from; delete nf.date_to;
                      setFilters(nf);
                      if (selectedReport) loadReportData(selectedReport.key, nf);
                    }
                  }}
                />
              )}
            </Col>

            {/* Department filter */}
            <Col>
              <Select
                placeholder="Department"
                style={{ width: 150 }}
                onChange={(value) => handleFilterChange('department', value)}
                allowClear
                showSearch
                filterOption={(inp, opt) => opt.children.toLowerCase().includes(inp.toLowerCase())}
              >
                {departments.map(dept => (
                  <Option key={dept} value={dept}>{dept}</Option>
                ))}
              </Select>
            </Col>

            {/* Emp Code filter — for daily and monthly */}
            {(reportKey === 'att.daily' || reportKey === 'att.monthly') && (
              <Col>
                <Input
                  placeholder="Employee Code"
                  style={{ width: 150 }}
                  allowClear
                  value={filters.emp_code || ''}
                  onChange={(e) => {
                    const val = e.target.value;
                    const nf = { ...filters };
                    if (val) nf.emp_code = val; else delete nf.emp_code;
                    setFilters(nf);
                  }}
                  onPressEnter={() => {
                    if (selectedReport) loadReportData(selectedReport.key, filters);
                  }}
                  suffix={<UserOutlined style={{ color: '#999' }} />}
                />
              </Col>
            )}

            {/* Status filter — for daily report */}
            {reportKey === 'att.daily' && (
              <Col>
                <Select
                  placeholder="Status"
                  style={{ width: 130 }}
                  onChange={(value) => handleFilterChange('status', value)}
                  allowClear
                >
                  {ATT_STATUSES.map(s => <Option key={s} value={s}>{s}</Option>)}
                </Select>
              </Col>
            )}

            <Col>
              <Button
                type="primary"
                onClick={() => { if (selectedReport) loadReportData(selectedReport.key, filters); }}
              >
                Run Report
              </Button>
            </Col>
          </Row>
        </Card>
      );
    }

    // Default filter bar (non-zone, non-attendance reports)
    return (
      <Card size="small" style={{ marginBottom: 16 }}>
        <DatePresets />
        <Row gutter={16} align="middle">
          <Col>
            <RangePicker
              value={filters.date_from ? [dayjs(filters.date_from), dayjs(filters.date_to)] : null}
              onChange={(dates) => {
                if (dates) {
                  handleFilterChange('date_from', dates[0].format('YYYY-MM-DD'));
                  handleFilterChange('date_to',   dates[1].format('YYYY-MM-DD'));
                } else {
                  const nf = { ...filters };
                  delete nf.date_from; delete nf.date_to;
                  setFilters(nf);
                  if (selectedReport) loadReportData(selectedReport.key, nf);
                }
              }}
            />
          </Col>
          <Col>
            <Select
              placeholder="Department"
              style={{ width: 150 }}
              onChange={(value) => handleFilterChange('department', value)}
              allowClear
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().includes(input.toLowerCase())
              }
            >
              {departments.map(dept => (
                <Option key={dept} value={dept}>{dept}</Option>
              ))}
            </Select>
          </Col>
          <Col>
            <Select
              placeholder="Personnel Type"
              style={{ width: 150 }}
              onChange={(value) => handleFilterChange('personnel_type', value)}
              allowClear
            >
              <Option value="Staff">Staff</Option>
              <Option value="Contractor">Contractor</Option>
              <Option value="Visitor">Visitor</Option>
            </Select>
          </Col>
          <Col flex={1}>
            <Search
              placeholder="Search..."
              onSearch={(value) => handleFilterChange('search', value)}
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </Card>
    );
  };

  // Compact dark action toolbar
  const renderActionBar = () => (
    <Card size="small" style={{ marginBottom: 16 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
        <Space size={8} wrap>
          <Button size="small" icon={<DownloadOutlined />} onClick={() => setExportModalVisible(true)}>Export</Button>
          <Button size="small" icon={<MailOutlined />} onClick={() => setScheduleModalVisible(true)}>Schedule</Button>
          <Divider type="vertical" />
          <Segmented
            value={viewMode}
            onChange={setViewMode}
            size="small"
            options={[
              { value: 'table',    label: <span><TableOutlined /> Table</span> },
              ...(isTimelineReport() ? [{ value: 'timeline', label: <span><HistoryOutlined /> Timeline</span> }] : []),
            ]}
          />
          <Button
            size="small"
            icon={showChart ? <EyeInvisibleOutlined /> : <BarChartOutlined />}
            type={showChart ? 'primary' : 'default'}
            onClick={() => setShowChart(v => !v)}
          >
            {showChart ? 'Hide Chart' : 'Chart'}
          </Button>
          <Button size="small" icon={<SettingOutlined />} onClick={() => setColumnModalVisible(true)}>Columns</Button>
        </Space>
        <Space size={8}>
          <Tooltip title="Auto-refresh every 30 seconds">
            <Switch checkedChildren="Auto" unCheckedChildren="Manual" checked={autoRefreshOn} size="small"
              onChange={(checked) => { setAutoRefreshOn(checked); message.info(checked ? 'Auto-refresh ON (30s)' : 'Auto-refresh OFF'); }} />
          </Tooltip>
          <Button size="small" icon={<ReloadOutlined />} loading={loading} onClick={() => loadReportData(selectedReport?.key, filters)}>Refresh</Button>
          <Tooltip title={fullscreen ? 'Exit fullscreen' : 'Fullscreen'}>
            <Button size="small" icon={fullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />} onClick={() => setFullscreen(v => !v)} />
          </Tooltip>
        </Space>
      </div>
    </Card>
  );

  const renderSummaryCards = () => {
    if (!reportData?.summary) return null;
    const summaryItems = Object.entries(reportData.summary)
      .filter(([, v]) => v !== null && typeof v !== 'object')
      .map(([key, value]) => ({
        title: key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()),
        value: typeof value === 'number' ? value.toLocaleString() : String(value),
        suffix: typeof value === 'number' && key.includes('rate') ? '%' : '',
      }));
    if (!summaryItems.length) return null;
    const PALETTE = [
      { color: '#2563eb', bg: '#eff6ff' }, { color: '#16a34a', bg: '#f0fdf4' },
      { color: '#d97706', bg: '#fffbeb' }, { color: '#7c3aed', bg: '#ede9fe' },
      { color: '#0891b2', bg: '#ecfeff' }, { color: '#dc2626', bg: '#fef2f2' },
    ];
    return (
      <Row gutter={[12, 12]} style={{ marginBottom: 16 }}>
        {summaryItems.map((item, i) => {
          const c = PALETTE[i % PALETTE.length];
          return (
            <Col xs={12} sm={8} md={6} key={i}>
              <div style={{
                background: '#fff', borderRadius: 12, padding: '14px 16px',
                border: '1px solid #e2e8f0', boxShadow: '0 1px 3px rgba(0,0,0,0.04)',
                display: 'flex', alignItems: 'center', gap: 12,
              }}>
                <div style={{
                  width: 40, height: 40, borderRadius: 10, flexShrink: 0, background: c.bg,
                  display: 'flex', alignItems: 'center', justifyContent: 'center', color: c.color, fontSize: 18,
                }}>
                  <BarChartOutlined />
                </div>
                <div style={{ minWidth: 0 }}>
                  <div style={{ fontSize: 22, fontWeight: 800, color: '#0f172a', lineHeight: 1 }}>
                    {item.value}{item.suffix}
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 3, fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {item.title}
                  </div>
                </div>
              </div>
            </Col>
          );
        })}
      </Row>
    );
  };

  return (
    <>
    <Layout className="reports-module" style={{ height: '100vh' }}>
      <Sider
        width={300}
        collapsible
        collapsed={sidebarCollapsed}
        onCollapse={setSidebarCollapsed}
        style={{ background: '#fff', borderRight: '1px solid #e2e8f0' }}
      >
        <div style={{ padding: '16px 16px 8px' }}>
          <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a', marginBottom: 2 }}>Reports</div>
          <div style={{ fontSize: 11, color: '#94a3b8', marginBottom: 10 }}>Browse, run, export & schedule reports</div>
          <Search
            placeholder="Search reports..."
            style={{ marginBottom: 4 }}
            size="small"
            allowClear
            value={sidebarSearch}
            onChange={e => setSidebarSearch(e.target.value)}
          />
        </div>
        <div style={{ padding: '0 8px', overflowY: 'auto', flex: 1 }}>
          {renderSidebarTree()}
        </div>
      </Sider>

      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', borderBottom: '1px solid #e2e8f0', height: 'auto', lineHeight: 1.4, paddingTop: 12, paddingBottom: 12 }}>
          <Row justify="space-between" align="middle">
            <Col>
              <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>
                {selectedReport ? selectedReport.title : 'Select a Report'}
              </div>
              <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                {selectedReport ? selectedReport.description : 'Choose a report from the sidebar to begin'}
              </div>
            </Col>
            <Col>
              <Space>
                <Badge count={favReports.size} color="gold">
                  <Button icon={<StarFilled style={{ color: '#faad14' }} />} onClick={() => setFavDrawerOpen(true)}>
                    Favorites
                  </Button>
                </Badge>
                <Button icon={<PlusOutlined />} type="primary" ghost onClick={() => setActiveTab('custom')}>
                  Custom Builder
                </Button>
              </Space>
            </Col>
          </Row>
        </Header>

        <Content style={{ padding: '24px', overflow: 'auto' }}>
          <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            items={[
              {
                key: 'reports',
                label: <span><TableOutlined /> Reports</span>,
                children: selectedReport ? (
                  <div style={fullscreen ? { position: 'fixed', top: 0, left: 0, width: '100vw', height: '100vh', background: '#fff', zIndex: 1000, padding: 16, overflow: 'auto' } : {}}>
                    {renderFilterBar()}
                    {renderActionBar()}
                    {renderSummaryCards()}

                    {/* Chart — always renders when toggled on; auto-derives data when backend sends none */}
                    {showChart && (
                      <Card
                        title={<span><BarChartOutlined style={{ marginRight: 8, color: '#1677ff' }} />Chart View</span>}
                        style={{ marginBottom: 16 }}
                        extra={
                          <Segmented
                            value={chartType === 'none' ? 'bar' : chartType}
                            onChange={setChartType}
                            size="small"
                            options={[
                              { value: 'bar',  label: <BarChartOutlined /> },
                              { value: 'line', label: <LineChartOutlined /> },
                              { value: 'pie',  label: <PieChartOutlined /> },
                            ]}
                          />
                        }
                      >
                        {renderChart() || (
                          <Empty
                            image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description="No chartable data — run a report with numeric columns to see a chart"
                            style={{ padding: '24px 0' }}
                          />
                        )}
                      </Card>
                    )}

                    {viewMode === 'timeline' ? (
                      <Card
                        title={<span><HistoryOutlined style={{ marginRight: 8 }} />Event Timeline</span>}
                        extra={<Tag color="blue">{(reportData?.data || []).length} events</Tag>}
                      >
                        <Spin spinning={loading}>{renderTimeline()}</Spin>
                      </Card>
                    ) : (
                      <Card
                        title="Report Data"
                        extra={reportData?.total != null ? <Tag>{Number(reportData.total).toLocaleString()} rows</Tag> : null}
                      >
                        <Spin spinning={loading}>
                          <div style={{ height: fullscreen ? 'calc(100vh - 380px)' : 520 }} className="ag-theme-alpine">
                            <AgGridReact
                              rowData={reportData?.data || []}
                              columnDefs={getGridColumnDefs()}
                              defaultColDef={{ sortable: true, filter: true, resizable: true }}
                              pagination={true}
                              paginationPageSize={50}
                              domLayout="normal"
                            />
                          </div>
                        </Spin>
                      </Card>
                    )}
                  </div>
                ) : (
                  <Card>
                    <div style={{ textAlign: 'center', padding: '40px 0 20px' }}>
                      <FileTextOutlined style={{ fontSize: 56, color: '#d9d9d9', marginBottom: 16 }} />
                      <Title level={4} type="secondary">Select a Report</Title>
                      <Text type="secondary">Choose from the sidebar, or pick a category below</Text>
                    </div>
                    <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
                      {reportCategories.map(cat => (
                        <Col xs={24} sm={12} lg={8} xl={6} key={cat.key}>
                          <Card
                            size="small"
                            hoverable
                            style={{ cursor: 'default', borderLeft: '3px solid #1677ff' }}
                            title={<span>{cat.icon}<span style={{ marginLeft: 8 }}>{cat.title}</span></span>}
                          >
                            <Space direction="vertical" size={2} style={{ width: '100%' }}>
                              {cat.reports.map(r => (
                                <Button
                                  key={r.key}
                                  type="link"
                                  size="small"
                                  style={{ padding: 0, height: 'auto', textAlign: 'left', whiteSpace: 'normal' }}
                                  onClick={() => handleReportSelect(r)}
                                >
                                  {r.title}
                                </Button>
                              ))}
                            </Space>
                          </Card>
                        </Col>
                      ))}
                    </Row>
                  </Card>
                )
              },
              { key: 'custom', label: <span><BuildOutlined />Custom Builder</span>, children: <CustomReportBuilder /> },
              {
                key: 'templates',
                label: <span><SettingOutlined /> Templates</span>,
                children: (
                  <Card
                    title="Saved Report Templates"
                    extra={
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setTemplateModalVisible(true)}
                      >
                        New Template
                      </Button>
                    }
                  >
                    <Table
                      dataSource={templates}
                      rowKey="id"
                      pagination={{ pageSize: 20 }}
                      columns={[
                        {
                          title: 'Name',
                          dataIndex: 'template_name',
                          sorter: (a, b) => a.template_name.localeCompare(b.template_name),
                        },
                        {
                          title: 'Module',
                          dataIndex: 'module',
                          render: (v) => <Tag>{v}</Tag>,
                          filters: [...new Set(templates.map(t => t.module))].map(m => ({ text: m, value: m })),
                          onFilter: (v, r) => r.module === v,
                        },
                        { title: 'Report Code', dataIndex: 'report_code' },
                        {
                          title: 'Description',
                          dataIndex: 'description',
                          ellipsis: true,
                        },
                        {
                          title: 'Flags',
                          render: (_, r) => (
                            <Space>
                              {r.is_system && <Tag color="blue">System</Tag>}
                              {r.is_public && <Tag color="green">Public</Tag>}
                              {r.is_favorite && <StarFilled style={{ color: '#faad14' }} />}
                            </Space>
                          ),
                        },
                        {
                          title: 'Created',
                          dataIndex: 'created_at',
                          render: (v) => v ? dayjs(v).format('YYYY-MM-DD') : '',
                          sorter: (a, b) => new Date(a.created_at) - new Date(b.created_at),
                        },
                        {
                          title: 'Actions',
                          render: (_, r) => (
                            <Space>
                              <Tooltip title="Run this report">
                                <Button
                                  size="small"
                                  icon={<TableOutlined />}
                                  onClick={() => {
                                    setActiveTab('reports');
                                    const report = reportCategories
                                      .flatMap(c => c.reports)
                                      .find(rep => rep.key === r.report_code);
                                    if (report) handleReportSelect(report);
                                    else message.info(`Running: ${r.report_code}`);
                                  }}
                                >
                                  Run
                                </Button>
                              </Tooltip>
                              <Tooltip title={r.is_favorite ? 'Remove from favorites' : 'Add to favorites'}>
                                <Button
                                  size="small"
                                  icon={r.is_favorite ? <StarFilled style={{ color: '#faad14' }} /> : <StarOutlined />}
                                  onClick={() => handleFavoriteToggle(r.id)}
                                />
                              </Tooltip>
                              {!r.is_system && (
                                <Popconfirm
                                  title="Delete this template?"
                                  onConfirm={async () => {
                                    try {
                                      await fetch(`/api/v1/report/templates/${r.id}`, {
                                        method: 'DELETE',
                                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
                                      });
                                      message.success('Template deleted');
                                      loadTemplates();
                                    } catch { message.error('Failed to delete'); }
                                  }}
                                >
                                  <Button size="small" danger>Delete</Button>
                                </Popconfirm>
                              )}
                            </Space>
                          ),
                        },
                      ]}
                      locale={{ emptyText: 'No templates yet. Run a report and save it as a template.' }}
                    />
                  </Card>
                ),
              },
              {
                key: 'schedules',
                label: <span><ScheduleOutlined /> Schedules</span>,
                children: (
                  <Card
                    title="Report Schedules"
                    extra={
                      <Button
                        type="primary"
                        icon={<PlusOutlined />}
                        onClick={() => setScheduleModalVisible(true)}
                      >
                        New Schedule
                      </Button>
                    }
                  >
                    <Table
                      dataSource={schedules}
                      rowKey="id"
                      pagination={{ pageSize: 20 }}
                      columns={[
                        { title: 'Name', dataIndex: 'schedule_name' },
                        { title: 'Cron', dataIndex: 'cron', render: (v) => <code>{v}</code> },
                        {
                          title: 'Format',
                          dataIndex: 'format',
                          render: (v) => {
                            const icons = { pdf: <FilePdfOutlined />, xlsx: <FileExcelOutlined />, csv: <FileOutlined /> };
                            return <Space>{icons[v]}<span>{v?.toUpperCase()}</span></Space>;
                          },
                        },
                        {
                          title: 'Active',
                          dataIndex: 'is_active',
                          render: (v, r) => (
                            <Switch
                              checked={v}
                              size="small"
                              onChange={async (checked) => {
                                try {
                                  await fetch(`/api/v1/report/schedules/${r.id}`, {
                                    method: 'PUT',
                                    headers: {
                                      'Content-Type': 'application/json',
                                      'Authorization': `Bearer ${localStorage.getItem('token')}`,
                                    },
                                    body: JSON.stringify({ is_active: checked }),
                                  });
                                  loadSchedules();
                                } catch { message.error('Failed to update'); }
                              }}
                            />
                          ),
                        },
                        {
                          title: 'Last Run',
                          dataIndex: 'last_run',
                          render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '—',
                        },
                        {
                          title: 'Next Run',
                          dataIndex: 'next_run',
                          render: (v) => v ? dayjs(v).format('YYYY-MM-DD HH:mm') : '—',
                        },
                        {
                          title: 'Actions',
                          render: (_, r) => (
                            <Space>
                              <Tooltip title="Run now">
                                <Button
                                  size="small"
                                  icon={<ReloadOutlined />}
                                  onClick={async () => {
                                    try {
                                      await fetch(`/api/v1/report/schedules/${r.id}/run-now/`, {
                                        method: 'POST',
                                        headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
                                      });
                                      message.success('Schedule triggered');
                                    } catch { message.error('Failed to trigger'); }
                                  }}
                                />
                              </Tooltip>
                              <Popconfirm
                                title="Delete this schedule?"
                                onConfirm={async () => {
                                  try {
                                    await fetch(`/api/v1/report/schedules/${r.id}`, {
                                      method: 'DELETE',
                                      headers: { 'Authorization': `Bearer ${localStorage.getItem('token')}` },
                                    });
                                    message.success('Schedule deleted');
                                    loadSchedules();
                                  } catch { message.error('Failed to delete'); }
                                }}
                              >
                                <Button size="small" danger>Delete</Button>
                              </Popconfirm>
                            </Space>
                          ),
                        },
                      ]}
                      locale={{ emptyText: 'No schedules yet. Create a schedule to auto-send reports.' }}
                    />
                  </Card>
                ),
              },
            ]}
          />
        </Content>
      </Layout>
    </Layout>

      {/* Favorites Drawer */}
      <Drawer
        title={<span><StarFilled style={{ color: '#faad14', marginRight: 8 }} />Favourite Reports</span>}
        open={favDrawerOpen}
        onClose={() => setFavDrawerOpen(false)}
        width={340}
        placement="right"
      >
        {favReports.size === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              <span>
                No favourites yet.<br />
                Click the <StarOutlined /> next to any report in the sidebar to pin it here.
              </span>
            }
          />
        ) : (
          <Space direction="vertical" style={{ width: '100%' }} size={6}>
            {reportCategories.flatMap(cat => cat.reports)
              .filter(r => favReports.has(r.key))
              .map(r => (
                <Card
                  key={r.key}
                  size="small"
                  hoverable
                  style={{ borderLeft: '3px solid #faad14', cursor: 'pointer' }}
                  onClick={() => {
                    handleReportSelect(r);
                    setActiveTab('reports');
                    setFavDrawerOpen(false);
                  }}
                  extra={
                    <Tooltip title="Remove from favourites">
                      <StarFilled
                        style={{ color: '#faad14', cursor: 'pointer' }}
                        onClick={(e) => { e.stopPropagation(); handleFavReportToggle(r, e); }}
                      />
                    </Tooltip>
                  }
                >
                  <div style={{ fontWeight: 500 }}>{r.title}</div>
                  <div style={{ fontSize: 12, color: '#888', marginTop: 2 }}>{r.description}</div>
                </Card>
              ))
            }
          </Space>
        )}
      </Drawer>

      {/* Export Modal */}
      <Modal
        title="Export Report"
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        footer={null}
        width={480}
      >
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          {/* Quick Direct Downloads */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#6B7A8D', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              Quick Download (Direct PDF/CSV)
            </div>
            <Row gutter={[8, 8]}>
              {[
                { label: 'Attendance PDF',  url: '/api/v1/reports/attendance/pdf',  icon: <FilePdfOutlined style={{ color: '#EF4444' }} /> },
                { label: 'Attendance CSV',  url: '/api/v1/reports/attendance/csv',  icon: <FileTextOutlined style={{ color: '#10B981' }} /> },
                { label: 'Compliance PDF',  url: '/api/v1/reports/compliance/pdf',  icon: <FilePdfOutlined style={{ color: '#EF4444' }} /> },
                { label: 'Compliance CSV',  url: '/api/v1/reports/compliance/csv',  icon: <FileTextOutlined style={{ color: '#10B981' }} /> },
                { label: 'POB Report PDF',  url: '/api/v1/reports/pob/pdf',         icon: <FilePdfOutlined style={{ color: '#EF4444' }} /> },
                { label: 'POB Report CSV',  url: '/api/v1/reports/pob/csv',         icon: <FileTextOutlined style={{ color: '#10B981' }} /> },
                { label: 'Visitors PDF',    url: '/api/v1/reports/visitors/pdf',    icon: <FilePdfOutlined style={{ color: '#EF4444' }} /> },
                { label: 'Visitors CSV',    url: '/api/v1/reports/visitors/csv',    icon: <FileTextOutlined style={{ color: '#10B981' }} /> },
              ].map(item => (
                <Col span={12} key={item.url}>
                  <Button
                    block
                    icon={item.icon}
                    size="small"
                    onClick={() => {
                      const token = localStorage.getItem('token');
                      const a = document.createElement('a');
                      a.href = item.url + (item.url.includes('?') ? '&' : '?') + `_auth=${token}`;
                      // Use fetch to add auth header and trigger download
                      fetch(item.url, { headers: { Authorization: `Bearer ${token}` } })
                        .then(r => r.blob())
                        .then(blob => {
                          const url = URL.createObjectURL(blob);
                          const dl = document.createElement('a');
                          dl.href = url;
                          dl.download = item.label.replace(/ /g, '_').toLowerCase() + item.url.split('.').pop();
                          dl.click();
                          URL.revokeObjectURL(url);
                        });
                    }}
                    style={{ textAlign: 'left' }}
                  >
                    {item.label}
                  </Button>
                </Col>
              ))}
            </Row>
          </div>

          <Divider style={{ margin: '4px 0' }} />

          {/* Task-based export for selected report */}
          <div>
            <div style={{ fontSize: 12, fontWeight: 600, color: '#6B7A8D', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 8 }}>
              Export Selected Report
            </div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Button block icon={<FilePdfOutlined />} onClick={() => handleExport('pdf')}>Export as PDF</Button>
              <Button block icon={<FileExcelOutlined />} onClick={() => handleExport('xlsx')}>Export as Excel</Button>
              <Button block icon={<FileTextOutlined />} onClick={() => handleExport('csv')}>Export as CSV</Button>
            </Space>
          </div>
        </Space>
      </Modal>
      
      {/* Column Configuration Modal */}
      <Modal
        title="Show / Hide Columns"
        open={columnModalVisible}
        onCancel={() => setColumnModalVisible(false)}
        onOk={() => setColumnModalVisible(false)}
        okText="Done"
        width={500}
      >
        <div style={{ marginBottom: 8 }}>
          <Button size="small" onClick={() => setHiddenColumns(new Set())}>Show All</Button>
          <Button size="small" style={{ marginLeft: 8 }} onClick={() => setHiddenColumns(new Set(columns.map(c => c.field)))}>Hide All</Button>
        </div>
        <Row gutter={[8, 8]}>
          {columns.map((col) => (
            <Col span={12} key={col.field}>
              <Checkbox
                checked={!hiddenColumns.has(col.field)}
                onChange={(e) => {
                  setHiddenColumns(prev => {
                    const next = new Set(prev);
                    if (e.target.checked) next.delete(col.field);
                    else next.add(col.field);
                    return next;
                  });
                }}
              >
                {col.label}
              </Checkbox>
            </Col>
          ))}
        </Row>
        {columns.length === 0 && <Text type="secondary">Run a report first to configure columns.</Text>}
      </Modal>
      
      {/* Schedule Modal */}
      <Modal
        title="Schedule Report"
        open={scheduleModalVisible}
        onCancel={() => { setScheduleModalVisible(false); scheduleForm.resetFields(); }}
        onOk={() => scheduleForm.validateFields().then(createSchedule)}
        okText="Create Schedule"
        width={560}
        destroyOnHidden
      >
        <Form form={scheduleForm} layout="vertical" style={{ marginTop: 8 }}>
          {/* Template selector — pre-fill with selectedReport if available */}
          <Form.Item
            name="template_id"
            label="Report Template"
            rules={[{ required: true, message: 'Select a template to schedule' }]}
            initialValue={selectedReport?.templateId ?? undefined}
          >
            <Select
              showSearch
              placeholder="Choose a saved report template"
              optionFilterProp="children"
            >
              {templates.map(t => (
                <Option key={t.id} value={t.id}>{t.template_name} <Tag style={{ marginLeft: 4, fontSize: 10 }}>{t.module}</Tag></Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item name="schedule_name" label="Schedule Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Weekly Attendance Summary" />
          </Form.Item>

          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="frequency" label="Frequency" rules={[{ required: true }]} initialValue="daily">
                <Select>
                  <Option value="hourly">Every Hour</Option>
                  <Option value="daily">Daily</Option>
                  <Option value="weekly">Weekly</Option>
                  <Option value="monthly">Monthly (1st)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="run_time" label="Run At" initialValue={dayjs().hour(8).minute(0)}>
                <TimePicker format="HH:mm" minuteStep={15} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>

          {/* Day-of-week selector — shown only for weekly */}
          <Form.Item noStyle shouldUpdate={(prev, cur) => prev.frequency !== cur.frequency}>
            {({ getFieldValue }) => getFieldValue('frequency') === 'weekly' ? (
              <Form.Item name="dow" label="Day of Week" initialValue={1}>
                <Select>
                  {['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'].map((d, i) => (
                    <Option key={i} value={i}>{d}</Option>
                  ))}
                </Select>
              </Form.Item>
            ) : null}
          </Form.Item>

          <Form.Item name="format" label="Export Format" rules={[{ required: true }]} initialValue="xlsx">
            <Select>
              <Option value="pdf"><FilePdfOutlined /> PDF</Option>
              <Option value="xlsx"><FileExcelOutlined /> Excel</Option>
              <Option value="csv"><FileOutlined /> CSV</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="recipient_emails"
            label="Recipient Emails"
            help="Press Enter after each address to add it"
            rules={[{ required: true, type: 'array', min: 1, message: 'Add at least one recipient email' }]}
          >
            <Select
              mode="tags"
              placeholder="name@company.com"
              tokenSeparators={[',', ' ']}
              open={false}
            />
          </Form.Item>

          <Form.Item noStyle shouldUpdate>
            {(form) => (
              <Alert
                type="info"
                showIcon
                style={{ marginTop: 4 }}
                message={(() => {
                  const f = form.getFieldValue('frequency') || 'daily';
                  const t = form.getFieldValue('run_time');
                  const d = form.getFieldValue('dow');
                  return `Cron: ${buildCron(f, t, d)}`;
                })()}
              />
            )}
          </Form.Item>
        </Form>
      </Modal>

      <style>{`
        .reports-module .ant-card { border-radius: 12px; border-color: #e2e8f0; }
        .reports-module .ant-card-small > .ant-card-body { border-radius: 12px; }
        .reports-module .ant-table-thead > tr > th {
          background: #f8fafc !important;
          color: #64748b !important;
          font-size: 11px !important;
          font-weight: 700 !important;
          text-transform: uppercase !important;
          letter-spacing: 0.05em !important;
          border-bottom: 2px solid #e2e8f0 !important;
        }
        .reports-module .ant-table-tbody > tr > td { border-bottom: 1px solid #f1f5f9 !important; }
        .reports-module .ant-tabs-nav { margin-bottom: 12px !important; }
        /* AG-Grid header themed to match the slate palette */
        .reports-module .ag-theme-alpine {
          --ag-header-background-color: #f8fafc;
          --ag-header-foreground-color: #64748b;
          --ag-border-color: #e2e8f0;
          --ag-row-hover-color: #f8fafc;
          --ag-font-size: 13px;
        }
        .reports-module .ag-theme-alpine .ag-header-cell-text {
          text-transform: uppercase;
          letter-spacing: 0.04em;
          font-size: 11px;
          font-weight: 700;
        }
      `}</style>
    </>
  );
};

export default Reports;
