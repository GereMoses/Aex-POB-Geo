import React, { useState, useMemo } from 'react';
import {
  Tree, Card, Button, Space, Modal, Form, Input, Select,
  Popconfirm, Tooltip, Tag, Table, Row, Col, Statistic,
  Drawer, Descriptions, Badge, Switch, Divider, Empty, Spin, Alert,
  Tabs, Progress, InputNumber, App, Avatar, Typography, Dropdown,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ApartmentOutlined,
  TeamOutlined, ReloadOutlined, SearchOutlined, TableOutlined,
  SafetyOutlined, UserOutlined, PhoneOutlined, MailOutlined,
  BranchesOutlined, InfoCircleOutlined, CheckCircleOutlined,
  ClockCircleOutlined, EyeOutlined, SyncOutlined, ThunderboltOutlined,
  DollarOutlined, BarChartOutlined, DisconnectOutlined, WifiOutlined,
  LinkOutlined, CloudUploadOutlined, WarningOutlined, CalendarOutlined,
  EnvironmentOutlined, MinusCircleOutlined, IdcardOutlined,
  DownloadOutlined, FilterOutlined, ClearOutlined, MoreOutlined,
  ExclamationCircleOutlined, CheckSquareOutlined, RightOutlined,
  CopyOutlined, SwapOutlined, UndoOutlined, DownOutlined,
} from '@ant-design/icons';
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip as RTooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import dayjs from 'dayjs';
import apiService from '../../../services/api';

const { Option } = Select;
const { Text } = Typography;

const DEPT_TYPE_COLORS = {
  operations:     'blue',
  maintenance:    'orange',
  safety:         'red',
  security:       'purple',
  administration: 'cyan',
  logistics:      'green',
  technical:      'geekblue',
  medical:        'magenta',
  training:       'gold',
  contractor:     'lime',
  management:     'volcano',
  support:        'default',
};

const DEPT_TYPE_HEX = {
  operations:     '#1890ff',
  maintenance:    '#fa8c16',
  safety:         '#ff4d4f',
  security:       '#722ed1',
  administration: '#13c2c2',
  logistics:      '#52c41a',
  technical:      '#2f54eb',
  medical:        '#eb2f96',
  training:       '#faad14',
  contractor:     '#7cb305',
  management:     '#d4380d',
  support:        '#8c8c8c',
};

const CHART_COLORS = ['#1890ff','#52c41a','#fa8c16','#722ed1','#13c2c2','#f5222d','#2f54eb','#eb2f96','#faad14','#a0d911'];

const DEPT_TYPES = [
  'operations','maintenance','safety','security','administration',
  'logistics','technical','medical','training','contractor','management','support',
];

const STATUS_CONFIG = {
  active:       { color: 'success',    icon: <CheckCircleOutlined /> },
  inactive:     { color: 'error',      icon: <ClockCircleOutlined /> },
  temporary:    { color: 'warning',    icon: <ClockCircleOutlined /> },
  under_review: { color: 'processing', icon: <InfoCircleOutlined /> },
};

const ZKTECO_CONFIG = {
  synced:         { color: '#52c41a', label: 'Synced',         antColor: 'success',  icon: <SyncOutlined /> },
  pending:        { color: '#fa8c16', label: 'Pending',        antColor: 'warning',  icon: <ClockCircleOutlined /> },
  not_configured: { color: '#8c8c8c', label: 'Not Configured', antColor: 'default',  icon: <DisconnectOutlined /> },
  disabled:       { color: '#bfbfbf', label: 'Disabled',       antColor: 'default',  icon: <DisconnectOutlined /> },
};

const AVATAR_PALETTE = ['#4f46e5','#0891b2','#059669','#d97706','#dc2626','#7c3aed'];
const avatarColor = (s) => AVATAR_PALETTE[(s||'').split('').reduce((a,c) => a + c.charCodeAt(0), 0) % AVATAR_PALETTE.length];
const initials    = (name) => (name||'').split(' ').filter(Boolean).slice(0,2).map(p => p[0].toUpperCase()).join('') || '?';

const TYPE_CFG_PILL = {
  operations:     { color: '#1d4ed8', bg: '#dbeafe', border: '#93c5fd' },
  maintenance:    { color: '#c2410c', bg: '#ffedd5', border: '#fed7aa' },
  safety:         { color: '#dc2626', bg: '#fef2f2', border: '#fecaca' },
  security:       { color: '#6d28d9', bg: '#ede9fe', border: '#ddd6fe' },
  administration: { color: '#0e7490', bg: '#ecfeff', border: '#a5f3fc' },
  logistics:      { color: '#15803d', bg: '#f0fdf4', border: '#bbf7d0' },
  technical:      { color: '#1e40af', bg: '#eff6ff', border: '#bfdbfe' },
  medical:        { color: '#be185d', bg: '#fdf2f8', border: '#fbcfe8' },
  training:       { color: '#b45309', bg: '#fffbeb', border: '#fde68a' },
  contractor:     { color: '#4d7c0f', bg: '#f7fee7', border: '#d9f99d' },
  management:     { color: '#9a3412', bg: '#fff7ed', border: '#fed7aa' },
  support:        { color: '#4b5563', bg: '#f9fafb', border: '#e5e7eb' },
};

const STATUS_CFG_PILL = {
  active:       { color: '#15803d', bg: '#f0fdf4', border: '#bbf7d0', dot: '#16a34a' },
  inactive:     { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', dot: '#dc2626' },
  temporary:    { color: '#b45309', bg: '#fffbeb', border: '#fde68a', dot: '#d97706' },
  under_review: { color: '#1d4ed8', bg: '#eff6ff', border: '#bfdbfe', dot: '#2563eb' },
};

function TypePill({ type }) {
  if (!type) return <span style={{ color: '#bfbfbf' }}>—</span>;
  const cfg = TYPE_CFG_PILL[type] || { color: '#4b5563', bg: '#f9fafb', border: '#e5e7eb' };
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center',
      padding: '2px 8px', borderRadius: 999,
      fontSize: 11, fontWeight: 600, textTransform: 'capitalize',
      color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
    }}>
      {type}
    </span>
  );
}

function StatusPill({ status }) {
  const s = status || 'active';
  const cfg = STATUS_CFG_PILL[s] || STATUS_CFG_PILL.active;
  return (
    <span style={{
      display: 'inline-flex', alignItems: 'center', gap: 5,
      padding: '2px 8px', borderRadius: 999,
      fontSize: 11, fontWeight: 600, textTransform: 'capitalize',
      color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
    }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: cfg.dot, flexShrink: 0 }} />
      {s.replace('_', ' ')}
    </span>
  );
}


// ── Analytics ────────────────────────────────────────────────────────────────

function AnalyticsTab({ departments, summary }) {
  const stats = useMemo(() => {
    const byType   = {};
    const byStatus = {};
    departments.forEach(d => {
      const dt = d.department_type || 'other';
      byType[dt]   = (byType[dt]   || 0) + 1;
      const st = d.status || 'active';
      byStatus[st] = (byStatus[st] || 0) + 1;
    });
    const typeData   = Object.entries(byType).map(([name, value]) => ({ name, value }));
    const statusData = Object.entries(byStatus).map(([name, value]) => ({ name, value }));
    const zkData = [
      { name: 'Synced',         value: summary.zkteco_synced  || 0, fill: '#52c41a' },
      { name: 'Pending',        value: summary.zkteco_pending || 0, fill: '#fa8c16' },
      { name: 'Not Configured', value: Math.max(0, (summary.total_departments || departments.length) - (summary.zkteco_synced || 0) - (summary.zkteco_pending || 0)), fill: '#8c8c8c' },
    ].filter(d => d.value > 0);
    const budgetDepts = departments.filter(d => d.budget_allocated > 0);
    return { typeData, statusData, zkData, budgetDepts };
  }, [departments, summary]);

  if (!departments.length) return <Card><Empty description="No departments yet." /></Card>;

  const budgetUtil = summary.total_budget_allocated > 0
    ? Math.round((summary.total_budget_used / summary.total_budget_allocated) * 100)
    : 0;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Card title={<Space><WifiOutlined style={{ color: '#1890ff' }} />ZKTeco Sync State</Space>} size="small">
        <Row gutter={24}>
          {[
            { label: 'Synced',         value: summary.zkteco_synced  || 0, color: '#52c41a' },
            { label: 'Pending',        value: summary.zkteco_pending || 0, color: '#fa8c16' },
            { label: 'Not Configured', value: Math.max(0, (summary.total_departments || departments.length) - (summary.zkteco_synced || 0) - (summary.zkteco_pending || 0)), color: '#8c8c8c' },
          ].map(({ label, value, color }) => (
            <Col key={label} xs={8}>
              <Statistic title={label} value={value} valueStyle={{ color, fontSize: 20 }} />
            </Col>
          ))}
          {summary.total_budget_allocated > 0 && (
            <Col xs={24} style={{ marginTop: 12 }}>
              <span style={{ fontSize: 12, color: '#8c8c8c' }}>Overall Budget Utilization</span>
              <Progress percent={budgetUtil} style={{ marginTop: 4 }}
                status={budgetUtil > 90 ? 'exception' : budgetUtil > 75 ? 'active' : 'normal'} />
            </Col>
          )}
        </Row>
      </Card>
      <Row gutter={16}>
        <Col xs={24} md={12}>
          <Card title="Distribution by Type" size="small">
            {stats.typeData.length ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={stats.typeData} cx="50%" cy="50%" outerRadius={90} dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {stats.typeData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
                  </Pie>
                  <RTooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : <Empty />}
          </Card>
        </Col>
        <Col xs={24} md={12}>
          <Card title="ZKTeco Sync Distribution" size="small">
            {stats.zkData.length ? (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={stats.zkData} cx="50%" cy="50%" outerRadius={90} dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {stats.zkData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                  </Pie>
                  <RTooltip /><Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : <Empty />}
          </Card>
        </Col>
      </Row>
      {stats.statusData.length > 0 && (
        <Card title="Departments by Status" size="small">
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={stats.statusData} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" /><YAxis allowDecimals={false} />
              <RTooltip />
              <Bar dataKey="value" name="Departments" radius={[4, 4, 0, 0]}>
                {stats.statusData.map((_, i) => <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>
      )}
      {stats.budgetDepts.length > 0 && (
        <Card title="Budget Utilization per Department" size="small">
          <Table dataSource={stats.budgetDepts} rowKey="id" size="small" pagination={false}
            columns={[
              { title: 'Department', dataIndex: 'name', key: 'name' },
              { title: 'Type', dataIndex: 'department_type', key: 'type', render: (t) => <TypePill type={t} /> },
              { title: 'Allocated', dataIndex: 'budget_allocated', key: 'alloc', render: (v) => `$${Number(v || 0).toLocaleString()}` },
              { title: 'Used',      dataIndex: 'budget_used',      key: 'used',  render: (v) => `$${Number(v || 0).toLocaleString()}` },
              { title: 'Utilization', key: 'util', render: (_, r) => (
                <Progress percent={r.budget_utilization || 0} size="small"
                  status={r.budget_utilization > 90 ? 'exception' : r.budget_utilization > 75 ? 'active' : 'normal'} />
              )},
            ]}
          />
        </Card>
      )}
    </div>
  );
}


// ── ZKTeco Sync tab ──────────────────────────────────────────────────────────

function ZktecoSyncTab({ departments, onPushAll, pushingId }) {
  const { data: comparison = { matched: [], local_only: [], biotime_only: [], total_local: 0, total_biotime: 0, total_matched: 0 }, isLoading, refetch } = useQuery({
    queryKey: ['departments-zkteco-compare'],
    queryFn:  () => Promise.resolve({ data: [] }),
    staleTime: 15000,
  });

  const allRows = useMemo(() => {
    const matched = (comparison.matched || []).map(r => ({ ...r, _status: 'linked' }));
    const local   = (comparison.local_only || []).map(r => ({ ...r, _status: 'local_only' }));
    const bt      = (comparison.biotime_only || []).map(r => ({ ...r, _status: 'biotime_only' }));
    return [...matched, ...local, ...bt];
  }, [comparison]);

  const syncColumns = [
    {
      title: 'Local Department', key: 'local',
      render: (_, r) => r.local_name
        ? <Space><ApartmentOutlined style={{ color: '#1890ff' }} /><strong>{r.local_name}</strong><Tag style={{ fontSize: 11 }}>{r.local_code}</Tag></Space>
        : <span style={{ color: '#bfbfbf' }}>—</span>,
    },
    {
      title: 'BioTime Department', key: 'biotime',
      render: (_, r) => r.biotime_name
        ? (
          <Space>
            <ThunderboltOutlined style={{ color: '#722ed1' }} />
            <span>{r.biotime_name}</span>
            {r.biotime_code && <Tag color="purple" style={{ fontSize: 11 }}>{r.biotime_code}</Tag>}
            <Tag color="purple" style={{ fontSize: 10 }}>ID #{r.biotime_id}</Tag>
          </Space>
        )
        : <span style={{ color: '#bfbfbf' }}>—</span>,
    },
    {
      title: 'Sync Status', key: 'sync_status',
      render: (_, r) => {
        if (r._status === 'linked') {
          const allMatch = r.name_match && r.code_match;
          const partial  = r.name_match || r.code_match;
          if (allMatch) return <Tag color="success" icon={<CheckCircleOutlined />}>Fully Matched</Tag>;
          if (partial)  return <Tag color="warning" icon={<WarningOutlined />}>Partial Match</Tag>;
          return <Tag color="warning" icon={<WarningOutlined />}>Linked (Name Differs)</Tag>;
        }
        if (r._status === 'local_only')   return <Tag color="default" icon={<DisconnectOutlined />}>Not in BioTime</Tag>;
        if (r._status === 'biotime_only') return <Tag color="purple"  icon={<ThunderboltOutlined />}>BioTime Only</Tag>;
        return null;
      },
    },
    {
      title: 'Action', key: 'action',
      render: (_, r) => {
        if (r._status === 'local_only') {
          return (
            <Button size="small" type="primary" icon={<CloudUploadOutlined />}
              loading={pushingId === r.local_id} onClick={() => onPushAll(r.local_id)}>
              Push to BioTime
            </Button>
          );
        }
        if (r._status === 'linked') return <Tag color="success" icon={<CheckCircleOutlined />}>Synced</Tag>;
        return null;
      },
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      <Row gutter={16}>
        {[
          { title: 'Local Departments',   value: comparison.total_local,   color: '#1890ff', icon: <ApartmentOutlined /> },
          { title: 'BioTime Departments', value: comparison.total_biotime, color: '#722ed1', icon: <ThunderboltOutlined /> },
          { title: 'Linked / Matched',    value: comparison.total_matched, color: '#52c41a', icon: <LinkOutlined /> },
          { title: 'Not Synced',          value: (comparison.local_only || []).length, color: '#fa8c16', icon: <DisconnectOutlined /> },
        ].map(({ title, value, color, icon }) => (
          <Col key={title} xs={24} sm={12} md={6}>
            <Card size="small">
              <Statistic title={title} value={value || 0} valueStyle={{ color }}
                prefix={React.cloneElement(icon, { style: { color } })} />
            </Card>
          </Col>
        ))}
      </Row>
      {(comparison.local_only || []).length > 0 && (
        <Alert type="warning" showIcon icon={<WarningOutlined />}
          message={`${(comparison.local_only || []).length} department(s) not yet in BioTime`}
          description="Use 'Push to BioTime' to create them in the BioTime personnel_department table and link them automatically."
          action={
            <Button size="small" type="primary" icon={<CloudUploadOutlined />} loading={!!pushingId}
              onClick={() => (comparison.local_only || []).forEach(r => onPushAll(r.local_id))}>
              Push All
            </Button>
          }
        />
      )}
      {(comparison.local_only || []).length === 0 && comparison.total_biotime > 0 && (
        <Alert type="success" showIcon message="All local departments are linked to BioTime." />
      )}
      {comparison.total_biotime === 0 && comparison.total_local > 0 && (
        <Alert type="info" showIcon message="BioTime has no department records yet."
          description="Push your local departments to BioTime to establish sync." />
      )}
      <Card title={<Space><LinkOutlined />Department Sync Comparison</Space>} size="small"
        extra={<Button size="small" icon={<ReloadOutlined />} onClick={refetch}>Refresh</Button>}>
        <Spin spinning={isLoading}>
          <Table dataSource={allRows}
            rowKey={(r, i) => `${r._status}-${r.local_id || r.biotime_id || i}`}
            columns={syncColumns} size="small" pagination={false}
            rowClassName={(r) =>
              r._status === 'linked' ? 'row-linked' :
              r._status === 'biotime_only' ? 'row-bt-only' : ''
            }
          />
        </Spin>
      </Card>
    </div>
  );
}


// ── Personnel tab inside the drawer ─────────────────────────────────────────

function DeptPersonnelTab({ deptId, departments, onEdit }) {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [assignModal, setAssignModal] = useState(false);
  const [assignForm] = Form.useForm();
  const [transferModal, setTransferModal] = useState(false);
  const [transferTarget, setTransferTarget] = useState(null);
  const [transferForm] = Form.useForm();

  const { data: members = [], isLoading, refetch } = useQuery({
    queryKey: ['dept-personnel', deptId],
    queryFn:  () => apiService.get(`/api/v1/departments/${deptId}/personnel?status=active`),
    staleTime: 15000,
    enabled: !!deptId,
  });

  const { data: personnelList = [] } = useQuery({
    queryKey: ['personnel-list-minimal'],
    queryFn:  () => apiService.get('/api/v1/personnel/?limit=500').then(r => Array.isArray(r) ? r : (r?.data ?? r?.results ?? [])),
    staleTime: 60000,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['dept-personnel', deptId] });
    queryClient.invalidateQueries({ queryKey: ['departments'] });
    queryClient.invalidateQueries({ queryKey: ['departments-summary'] });
  };

  const removeMutation = useMutation({
    mutationFn: ({ pid }) => apiService.delete(`/api/v1/departments/${deptId}/personnel/${pid}`),
    onSuccess: () => { message.success('Removed from department'); invalidate(); },
    onError: (e) => message.error('Remove failed: ' + (e?.response?.data?.detail || e?.message)),
  });

  const assignMutation = useMutation({
    mutationFn: (data) => apiService.post(`/api/v1/departments/${deptId}/assign-personnel`, data),
    onSuccess: () => { message.success('Personnel assigned'); setAssignModal(false); assignForm.resetFields(); invalidate(); },
    onError: (e) => message.error('Assign failed: ' + (e?.response?.data?.detail || e?.message)),
  });

  const transferMutation = useMutation({
    mutationFn: (data) => apiService.post(`/api/v1/departments/${deptId}/transfer-personnel`, data),
    onSuccess: () => {
      message.success('Personnel transferred successfully');
      setTransferModal(false);
      setTransferTarget(null);
      transferForm.resetFields();
      invalidate();
    },
    onError: (e) => message.error('Transfer failed: ' + (e?.response?.data?.detail || e?.message)),
  });

  const openTransfer = (member) => {
    setTransferTarget(member);
    transferForm.setFieldsValue({ role: member.role, position: member.position });
    setTransferModal(true);
  };

  const assignedIds = new Set(members.map(m => m.personnel_id));
  const available   = personnelList.filter(p => !assignedIds.has(p.id));
  const otherDepts  = (departments || []).filter(d => d.id !== deptId && (d.status || 'active') === 'active');

  const cols = [
    {
      title: 'Employee', key: 'emp', width: 200,
      render: (_, r) => (
        <Space>
          <Avatar size={28} style={{ background: avatarColor(r.personnel_name), fontSize: 11, fontWeight: 600 }}>
            {initials(r.personnel_name)}
          </Avatar>
          <div>
            <div style={{ fontWeight: 500, fontSize: 13 }}>{r.personnel_name || `#${r.personnel_id}`}</div>
            <div style={{ fontSize: 11, color: '#8c8c8c', fontFamily: 'monospace' }}>{r.emp_code}</div>
          </div>
        </Space>
      ),
    },
    { title: 'Role',     dataIndex: 'role',     key: 'role',     width: 130 },
    { title: 'Position', dataIndex: 'position', key: 'position', width: 130, render: v => v || <span style={{ color: '#bfbfbf' }}>—</span> },
    {
      title: 'Flags', key: 'flags', width: 100,
      render: (_, r) => (
        <Space>
          {r.is_manager && <Tag color="blue"  style={{ fontSize: 10 }}>Manager</Tag>}
          {r.is_primary && <Tag color="green" style={{ fontSize: 10 }}>Primary</Tag>}
        </Space>
      ),
    },
    {
      title: '', key: 'actions', width: 90, align: 'center',
      render: (_, r) => (
        <Space size={2}>
          <Tooltip title="Transfer to another dept">
            <Button type="text" size="small" icon={<SwapOutlined />} onClick={() => openTransfer(r)} />
          </Tooltip>
          <Popconfirm title="Remove from department?" onConfirm={() => removeMutation.mutate({ pid: r.personnel_id })} okText="Remove" okType="danger">
            <Tooltip title="Remove"><Button type="text" danger size="small" icon={<MinusCircleOutlined />} /></Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Text style={{ fontSize: 13, color: '#595959' }}>{members.length} active member{members.length !== 1 ? 's' : ''}</Text>
        <Space>
          <Button size="small" icon={<ReloadOutlined />} onClick={refetch}>Refresh</Button>
          <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => setAssignModal(true)}>Assign Personnel</Button>
        </Space>
      </div>
      <Spin spinning={isLoading}>
        {members.length === 0
          ? <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No personnel assigned" style={{ padding: '20px 0' }} />
          : <Table dataSource={members} rowKey="id" columns={cols} size="small" pagination={false} scroll={{ y: 320 }} />
        }
      </Spin>

      {/* Assign modal */}
      <Modal title="Assign Personnel" open={assignModal} onCancel={() => { setAssignModal(false); assignForm.resetFields(); }}
        onOk={() => assignForm.validateFields().then(v => assignMutation.mutate(v))}
        confirmLoading={assignMutation.isPending} okText="Assign" width={480}>
        <Form form={assignForm} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item label="Personnel" name="personnel_id" rules={[{ required: true, message: 'Select a person' }]}>
            <Select showSearch placeholder="Search by name or code" optionFilterProp="label"
              options={available.map(p => ({
                value: p.id,
                label: `${p.first_name || ''} ${p.last_name || ''}`.trim() || p.full_name || `#${p.id}`,
                title: p.emp_code,
              }))}
              optionRender={(opt) => (
                <Space>
                  <Avatar size={20} style={{ background: avatarColor(opt.label), fontSize: 9 }}>{initials(opt.label)}</Avatar>
                  <span>{opt.label}</span>
                  <Tag style={{ fontSize: 10 }}>{opt.data.title}</Tag>
                </Space>
              )}
            />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Role" name="role" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="e.g. Engineer, Technician" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Position" name="position">
                <Input placeholder="e.g. Senior, Lead" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Primary Contact" name="is_primary" valuePropName="checked" initialValue={false}>
                <Switch size="small" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Department Manager" name="is_manager" valuePropName="checked" initialValue={false}>
                <Switch size="small" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* Transfer modal */}
      <Modal
        title={
          <Space>
            <SwapOutlined style={{ color: '#722ed1' }} />
            Transfer {transferTarget?.personnel_name || 'Personnel'}
          </Space>
        }
        open={transferModal}
        onCancel={() => { setTransferModal(false); setTransferTarget(null); transferForm.resetFields(); }}
        onOk={() => transferForm.validateFields().then(v =>
          transferMutation.mutate({ ...v, personnel_id: transferTarget?.personnel_id })
        )}
        confirmLoading={transferMutation.isPending}
        okText="Transfer"
        width={460}
      >
        <Alert
          type="info" showIcon style={{ marginBottom: 16 }}
          message={`Transferring ${transferTarget?.personnel_name || 'this person'} will unassign them from the current department and assign them to the selected one.`}
        />
        <Form form={transferForm} layout="vertical">
          <Form.Item label="Target Department" name="target_department_id" rules={[{ required: true, message: 'Select target department' }]}>
            <Select
              showSearch placeholder="Select department"
              optionFilterProp="label"
              options={otherDepts.map(d => ({
                value: d.id,
                label: `${d.name} (${d.code})`,
              }))}
            />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="New Role" name="role" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="Role in new department" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Position" name="position">
                <Input placeholder="e.g. Senior" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item label="Primary Contact" name="is_primary" valuePropName="checked" initialValue={false}>
                <Switch size="small" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item label="Department Manager" name="is_manager" valuePropName="checked" initialValue={false}>
                <Switch size="small" />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
}


// ── Sub-departments drawer tab ────────────────────────────────────────────────

function SubDepartmentsTab({ deptId, departments, onView, onEdit, onAdd }) {
  const children = departments.filter(d => d.parent_id === deptId);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <Text style={{ fontSize: 13, color: '#595959' }}>
          {children.length} sub-department{children.length !== 1 ? 's' : ''}
        </Text>
        <Button size="small" type="primary" icon={<PlusOutlined />} onClick={() => onAdd(deptId)}>
          Add Sub-department
        </Button>
      </div>

      {children.length === 0 ? (
        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description="No sub-departments" style={{ padding: '20px 0' }} />
      ) : (
        children.map(child => {
          const zk = ZKTECO_CONFIG[child.zkteco_status] || ZKTECO_CONFIG.not_configured;
          const isInactive = (child.status || 'active') !== 'active';
          return (
            <div
              key={child.id}
              style={{
                display: 'flex', alignItems: 'center', gap: 12, padding: '10px 14px',
                border: `1px solid ${isInactive ? '#faad14' : '#e8e8e8'}`,
                borderRadius: 8, background: isInactive ? '#fffbe6' : '#fff',
                cursor: 'pointer', transition: 'all 0.15s',
              }}
              onClick={() => onView(child)}
              onMouseEnter={e => { e.currentTarget.style.borderColor = '#91caff'; e.currentTarget.style.boxShadow = '0 2px 8px rgba(24,144,255,0.1)'; }}
              onMouseLeave={e => { e.currentTarget.style.borderColor = isInactive ? '#faad14' : '#e8e8e8'; e.currentTarget.style.boxShadow = 'none'; }}
            >
              <div style={{
                width: 36, height: 36, borderRadius: 8, flexShrink: 0,
                background: DEPT_TYPE_HEX[child.department_type] || '#bfbfbf',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                opacity: 0.85,
              }}>
                <ApartmentOutlined style={{ color: '#fff', fontSize: 16 }} />
              </div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontWeight: 600, fontSize: 13, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                  {child.name}
                </div>
                <div style={{ fontSize: 11, color: '#8c8c8c', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                  <span style={{ fontFamily: 'monospace' }}>{child.code}</span>
                  {child.department_type && <TypePill type={child.department_type} />}
                  {isInactive && <StatusPill status={child.status || 'inactive'} />}
                </div>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexShrink: 0 }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 700, color: '#1890ff', lineHeight: 1 }}>{child.current_personnel_count || 0}</div>
                  <div style={{ fontSize: 10, color: '#bfbfbf' }}>people</div>
                </div>
                <Tooltip title={`ZKTeco: ${zk.label}`}>
                  <span style={{ color: zk.color, fontSize: 14 }}>{zk.icon}</span>
                </Tooltip>
              </div>
              <Space size={2} onClick={e => e.stopPropagation()}>
                <Tooltip title="Edit"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(child)} /></Tooltip>
                <Tooltip title="Add child"><Button type="text" size="small" icon={<PlusOutlined />} onClick={() => onAdd(child.id)} /></Tooltip>
              </Space>
            </div>
          );
        })
      )}
    </div>
  );
}


// ── Hierarchy Card view ──────────────────────────────────────────────────────

function HierarchyCardNode({ dept, departments, onView, onEdit, onAdd, onClone, onReactivate, onDeactivate, depth = 0 }) {
  const [expanded, setExpanded] = useState(depth < 2);
  const children = departments.filter(d => d.parent_id === dept.id);
  const zk = ZKTECO_CONFIG[dept.zkteco_status] || ZKTECO_CONFIG.not_configured;
  const isInactive = (dept.status || 'active') !== 'active' || dept.is_active === false;
  const vacancy = dept.max_personnel ? Math.max(0, dept.max_personnel - (dept.current_personnel_count || 0)) : null;

  return (
    <div style={{ position: 'relative' }}>
      {/* Card row */}
      <div style={{ display: 'flex', alignItems: 'stretch', marginBottom: 6, position: 'relative' }}>
        {/* Horizontal connector from parent line */}
        {depth > 0 && (
          <div style={{ position: 'absolute', left: -18, top: 18, width: 16, height: 2, background: '#dde1e7' }} />
        )}

        {/* Type colour strip + expand control */}
        <div
          onClick={children.length > 0 ? () => setExpanded(e => !e) : undefined}
          style={{
            width: 30, flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center',
            background: isInactive ? '#d9d9d9' : (DEPT_TYPE_HEX[dept.department_type] || '#bfbfbf'),
            borderRadius: '8px 0 0 8px',
            cursor: children.length > 0 ? 'pointer' : 'default',
            opacity: isInactive ? 0.7 : 0.9,
          }}
        >
          {children.length > 0
            ? (expanded
                ? <DownOutlined style={{ fontSize: 10, color: '#fff' }} />
                : <RightOutlined style={{ fontSize: 10, color: '#fff' }} />
              )
            : <ApartmentOutlined style={{ fontSize: 11, color: 'rgba(255,255,255,0.7)' }} />
          }
        </div>

        {/* Main info */}
        <div
          style={{
            flex: 1, padding: '9px 12px', display: 'flex', alignItems: 'center', gap: 12,
            border: `1px solid ${isInactive ? '#faad14' : '#e8e8e8'}`,
            borderLeft: 'none',
            background: isInactive ? '#fffbe6' : '#fff',
            cursor: 'pointer', transition: 'background 0.13s',
          }}
          onClick={() => onView(dept)}
          onMouseEnter={e => e.currentTarget.style.background = isInactive ? '#fff8e1' : '#f8faff'}
          onMouseLeave={e => e.currentTarget.style.background = isInactive ? '#fffbe6' : '#fff'}
        >
          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 600, fontSize: 13, color: isInactive ? '#8c8c8c' : '#1a1a2e' }}>{dept.name}</span>
              <Tag style={{ fontSize: 10, fontFamily: 'monospace', margin: 0 }}>{dept.code}</Tag>
              {dept.department_type && <TypePill type={dept.department_type} />}
              {dept.safety_critical && <Tooltip title="Safety Critical"><SafetyOutlined style={{ color: '#dc2626', fontSize: 12 }} /></Tooltip>}
              {isInactive && <StatusPill status={dept.status || 'inactive'} />}
              {children.length > 0 && <Tag icon={<ApartmentOutlined />} color="geekblue" style={{ fontSize: 10, margin: 0 }}>{children.length} sub</Tag>}
            </div>
            {dept.manager_name && (
              <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginTop: 3 }}>
                <Avatar size={16} style={{ background: avatarColor(dept.manager_name), fontSize: 8, flexShrink: 0 }}>
                  {initials(dept.manager_name)}
                </Avatar>
                <span style={{ fontSize: 11, color: '#8c8c8c' }}>{dept.manager_name}</span>
              </div>
            )}
          </div>

          {/* Stats */}
          <div style={{ display: 'flex', alignItems: 'center', gap: 14, flexShrink: 0 }}>
            <div style={{ textAlign: 'center', minWidth: 38 }}>
              <div style={{ fontSize: 16, fontWeight: 700, color: '#1890ff', lineHeight: 1 }}>{dept.current_personnel_count || 0}</div>
              <div style={{ fontSize: 10, color: '#bfbfbf', lineHeight: 1.3 }}>people</div>
            </div>
            {vacancy !== null && (
              <Tooltip title={`${vacancy} open position${vacancy !== 1 ? 's' : ''}`}>
                <div style={{ textAlign: 'center', minWidth: 34 }}>
                  <div style={{ fontSize: 16, fontWeight: 700, color: vacancy === 0 ? '#ff4d4f' : vacancy <= 3 ? '#faad14' : '#52c41a', lineHeight: 1 }}>{vacancy}</div>
                  <div style={{ fontSize: 10, color: '#bfbfbf', lineHeight: 1.3 }}>vacant</div>
                </div>
              </Tooltip>
            )}
            <Tooltip title={`ZKTeco: ${zk.label}`}>
              <span style={{ color: zk.color, fontSize: 14 }}>{zk.icon}</span>
            </Tooltip>
          </div>
        </div>

        {/* Action buttons */}
        <div
          style={{
            display: 'flex', alignItems: 'center', padding: '0 8px', gap: 2,
            border: `1px solid ${isInactive ? '#faad14' : '#e8e8e8'}`,
            borderLeft: 'none', borderRadius: '0 8px 8px 0',
            background: isInactive ? '#fffbe6' : '#fafafa',
          }}
          onClick={e => e.stopPropagation()}
        >
          <Tooltip title="View"><Button type="text" size="small" icon={<EyeOutlined />} onClick={() => onView(dept)} /></Tooltip>
          <Tooltip title="Edit"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => onEdit(dept)} /></Tooltip>
          <Tooltip title="Add child dept"><Button type="text" size="small" icon={<PlusOutlined />} onClick={() => onAdd(dept.id)} /></Tooltip>
          <Dropdown trigger={['click']} menu={{
            items: [
              { key: 'clone', label: 'Clone', icon: <CopyOutlined />, onClick: () => onClone(dept) },
              ...(isInactive
                ? [{ key: 'reactivate', label: 'Reactivate', icon: <UndoOutlined />, onClick: () => onReactivate(dept.id) }]
                : [{
                    key: 'deactivate', label: 'Deactivate', icon: <DeleteOutlined />, danger: true,
                    onClick: () => Modal.confirm({
                      title: 'Deactivate department?',
                      icon: <ExclamationCircleOutlined />,
                      content: 'Sub-departments and personnel will be affected.',
                      okText: 'Deactivate', okType: 'danger',
                      onOk: () => onDeactivate(dept.id),
                    }),
                  }]
              ),
            ],
          }}>
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </div>
      </div>

      {/* Children */}
      {expanded && children.length > 0 && (
        <div style={{ marginLeft: 28, position: 'relative' }}>
          {/* Vertical connector line */}
          <div style={{
            position: 'absolute', left: -18, top: 0,
            width: 2,
            bottom: 14,
            background: '#dde1e7',
          }} />
          {children.map(child => (
            <HierarchyCardNode
              key={child.id}
              dept={child}
              departments={departments}
              onView={onView}
              onEdit={onEdit}
              onAdd={onAdd}
              onClone={onClone}
              onReactivate={onReactivate}
              onDeactivate={onDeactivate}
              depth={depth + 1}
            />
          ))}
        </div>
      )}
    </div>
  );
}


// ── Main component ────────────────────────────────────────────────────────────

const DepartmentTree = () => {
  const { message } = App.useApp();
  const queryClient = useQueryClient();
  const [form]      = Form.useForm();
  const [cloneForm] = Form.useForm();
  const [budgetForm] = Form.useForm();

  const [treeData, setTreeData]               = useState([]);
  const [isModalVisible, setIsModalVisible]   = useState(false);
  const [editingDept, setEditingDept]         = useState(null);
  const [expandedKeys, setExpandedKeys]       = useState([]);
  const [searchText, setSearchText]           = useState('');
  const [filterType, setFilterType]           = useState(null);
  const [filterStatus, setFilterStatus]       = useState(null);
  const [viewMode, setViewMode]               = useState('tree');
  const [drawerDept, setDrawerDept]           = useState(null);
  const [drawerVisible, setDrawerVisible]     = useState(false);
  const [drawerTab, setDrawerTab]             = useState('overview');
  const [activeTab, setActiveTab]             = useState('overview');
  const [pushingId, setPushingId]             = useState(null);
  const [selectedRowKeys, setSelectedRowKeys] = useState([]);
  const [bulkDeactivating, setBulkDeactivating] = useState(false);
  const [cloneModal, setCloneModal]           = useState(false);
  const [cloneSource, setCloneSource]         = useState(null);
  const [budgetModal, setBudgetModal]         = useState(false);
  const [budgetTarget, setBudgetTarget]       = useState(null);

  // ── Queries ────────────────────────────────────────────────────────────────

  const { data: departments = [], isLoading, refetch } = useQuery({
    queryKey: ['departments'],
    queryFn:  () => apiService.get('/api/v1/departments/').then(r => Array.isArray(r) ? r : (r?.data || r?.results || [])),
    staleTime: 30000,
  });

  const { data: summary = {} } = useQuery({
    queryKey: ['departments-summary'],
    queryFn:  () => apiService.get('/api/v1/departments/meta/summary'),
    staleTime: 30000,
  });

  const { data: shiftsRaw } = useQuery({
    queryKey: ['att-shifts-list'],
    queryFn:  () => apiService.get('/api/v1/attendance/shifts'),
    staleTime: 60_000,
  });
  const shifts = Array.isArray(shiftsRaw) ? shiftsRaw : (shiftsRaw?.data ?? []);

  const { data: personnelRaw } = useQuery({
    queryKey: ['personnel-list-minimal'],
    queryFn:  () => apiService.get('/api/v1/personnel/?limit=500').then(r => Array.isArray(r) ? r : (r?.data ?? r?.results ?? [])),
    staleTime: 60_000,
  });
  const personnelList = Array.isArray(personnelRaw) ? personnelRaw : [];

  // Build tree from flat list
  React.useEffect(() => {
    if (!departments.length) { setTreeData([]); return; }
    const build = (list, parentId = null) =>
      list.filter(d => (d.parent_id ?? null) === parentId)
          .map(d => ({ key: d.id, title: d.name, data: d, children: build(list, d.id) }));
    setTreeData(build(departments));
    setExpandedKeys(departments.filter(d => !d.parent_id).map(d => d.id));
  }, [departments]);

  // Sync drawer record with latest data
  React.useEffect(() => {
    if (drawerDept && departments.length) {
      const updated = departments.find(d => d.id === drawerDept.id);
      if (updated) setDrawerDept(updated);
    }
  }, [departments]);

  // ── Mutations ──────────────────────────────────────────────────────────────

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ['departments'] });
    queryClient.invalidateQueries({ queryKey: ['departments-summary'] });
    queryClient.invalidateQueries({ queryKey: ['departments-zkteco-compare'] });
  };

  const createMutation = useMutation({
    mutationFn: (data) => apiService.post('/api/v1/departments/', data),
    onSuccess:  () => { message.success('Department created'); setIsModalVisible(false); form.resetFields(); invalidate(); },
    onError:    (e) => message.error('Create failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, ...data }) => apiService.put(`/api/v1/departments/${id}/`, data),
    onSuccess:  () => { message.success('Department updated'); setIsModalVisible(false); form.resetFields(); invalidate(); },
    onError:    (e) => message.error('Update failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/departments/${id}`),
    onSuccess:  () => { message.success('Department deactivated'); invalidate(); },
    onError:    (e) => message.error('Deactivate failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const reactivateMutation = useMutation({
    mutationFn: (id) => apiService.patch(`/api/v1/departments/${id}/reactivate`),
    onSuccess:  () => { message.success('Department reactivated'); invalidate(); },
    onError:    (e) => message.error('Reactivate failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const cloneMutation = useMutation({
    mutationFn: ({ id, ...data }) => apiService.post(`/api/v1/departments/${id}/clone`, data),
    onSuccess:  () => { message.success('Department cloned'); setCloneModal(false); cloneForm.resetFields(); setCloneSource(null); invalidate(); },
    onError:    (e) => message.error('Clone failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const budgetSpendMutation = useMutation({
    mutationFn: ({ id, ...data }) => apiService.post(`/api/v1/departments/${id}/log-budget-spend`, data),
    onSuccess:  () => { message.success('Budget expense logged'); setBudgetModal(false); budgetForm.resetFields(); setBudgetTarget(null); invalidate(); },
    onError:    (e) => message.error('Failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error')),
  });

  const handlePushToBiotime = async (deptId) => {
    setPushingId(deptId);
    try {
      await apiService.post(`/api/v1/departments/${deptId}/push-to-biotime`);
      message.success('Department pushed to BioTime and linked');
      invalidate();
    } catch (e) {
      message.error('Push failed: ' + (e?.response?.data?.detail || e?.message || 'Unknown error'));
    } finally {
      setPushingId(null);
    }
  };

  // ── Bulk actions ───────────────────────────────────────────────────────────

  const handleBulkDeactivate = async () => {
    setBulkDeactivating(true);
    try {
      await Promise.all(selectedRowKeys.map(id => apiService.delete(`/api/v1/departments/${id}`)));
      message.success(`${selectedRowKeys.length} department(s) deactivated`);
      setSelectedRowKeys([]);
      invalidate();
    } catch (e) {
      message.error('Some deactivations failed: ' + (e?.response?.data?.detail || e?.message));
    } finally {
      setBulkDeactivating(false);
    }
  };

  const handleExportCSV = (rows) => {
    const cols = ['name', 'code', 'department_type', 'status', 'manager_name', 'current_personnel_count', 'max_personnel', 'vacancy', 'zkteco_status', 'contact_person', 'contact_email', 'contact_phone'];
    const headers = ['Name', 'Code', 'Type', 'Status', 'Manager', 'Personnel', 'Max Personnel', 'Vacancies', 'ZKTeco Status', 'Contact Person', 'Contact Email', 'Contact Phone'];
    const enriched = rows.map(r => ({ ...r, vacancy: r.max_personnel ? Math.max(0, r.max_personnel - (r.current_personnel_count || 0)) : '' }));
    const csv = [
      headers.join(','),
      ...enriched.map(r => cols.map(c => `"${(r[c] ?? '').toString().replace(/"/g, '""')}"`).join(',')),
    ].join('\n');
    const blob = new Blob([csv], { type: 'text/csv' });
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = 'departments.csv'; a.click();
    URL.revokeObjectURL(url);
  };

  const hasActiveFilters = !!(searchText || filterType || filterStatus);
  const clearFilters = () => { setSearchText(''); setFilterType(null); setFilterStatus(null); };

  // ── Form handlers ───────────────────────────────────────────────────────────

  const handleAdd = (parentId = null) => {
    setEditingDept(null);
    setTimeout(() => { form.resetFields(); form.setFieldsValue({ parent_id: parentId }); }, 0);
    setIsModalVisible(true);
  };

  const handleEdit = (dept) => {
    setEditingDept(dept);
    setTimeout(() => {
      form.resetFields();
      form.setFieldsValue({
        name: dept.name, code: dept.code, description: dept.description,
        department_type: dept.department_type, parent_id: dept.parent_id,
        manager_id: dept.manager_id ?? null,
        zone_id: dept.zone_id ?? null,
        contact_person: dept.contact_person, contact_email: dept.contact_email,
        contact_phone: dept.contact_phone, max_personnel: dept.max_personnel,
        budget_allocated: dept.budget_allocated || 0,
        safety_critical: dept.safety_critical ?? false,
        zkteco_sync_enabled: dept.zkteco_sync_enabled ?? true,
        zkteco_department_id: dept.zkteco_department_id,
        default_shift_id: dept.default_shift_id ?? null,
        status: dept.status,
      });
    }, 0);
    setIsModalVisible(true);
  };

  const handleSubmit = (values) => {
    if (editingDept) updateMutation.mutate({ id: editingDept.id, ...values });
    else createMutation.mutate(values);
  };

  const openDrawer = (dept) => { setDrawerDept(dept); setDrawerTab('overview'); setDrawerVisible(true); };

  const handleClone = (dept) => {
    setCloneSource(dept);
    cloneForm.setFieldsValue({ name: `${dept.name} (Copy)`, code: '' });
    setCloneModal(true);
  };

  const openBudgetModal = (dept) => {
    setBudgetTarget(dept);
    budgetForm.resetFields();
    setBudgetModal(true);
  };

  // ── Filter helpers ─────────────────────────────────────────────────────────

  const filteredDepts = departments.filter(d => {
    const text   = !searchText || d.name?.toLowerCase().includes(searchText.toLowerCase()) || d.code?.toLowerCase().includes(searchText.toLowerCase());
    const type   = !filterType   || d.department_type === filterType;
    const status = !filterStatus || d.status === filterStatus;
    return text && type && status;
  });

  const filterTree = (nodes) =>
    nodes.map(n => ({ ...n, children: n.children ? filterTree(n.children) : [] }))
         .filter(n => {
           const text   = !searchText || n.data?.name?.toLowerCase().includes(searchText.toLowerCase()) || n.data?.code?.toLowerCase().includes(searchText.toLowerCase());
           const type   = !filterType   || n.data?.department_type === filterType;
           const status = !filterStatus || n.data?.status === filterStatus;
           return text || type || status || n.children.length > 0;
         });

  const isMutating = createMutation.isPending || updateMutation.isPending;

  // ── Tree title ─────────────────────────────────────────────────────────────

  const renderTreeTitle = (node) => {
    const dept = node.data;
    const zk   = ZKTECO_CONFIG[dept.zkteco_status] || ZKTECO_CONFIG.not_configured;
    const isInactive = (dept.status || 'active') !== 'active';
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%', paddingRight: 8 }}>
        <Space size={6}>
          <ApartmentOutlined style={{ color: isInactive ? '#bfbfbf' : '#1890ff' }} />
          <span style={{ fontWeight: 500, color: isInactive ? '#8c8c8c' : undefined }}>{dept.name}</span>
          <Tag style={{ fontSize: 11 }}>{dept.code}</Tag>
          {dept.department_type && <TypePill type={dept.department_type} />}
          {dept.safety_critical && <Tooltip title="Safety Critical"><SafetyOutlined style={{ color: '#dc2626' }} /></Tooltip>}
          <Tooltip title={`ZKTeco: ${zk.label}`}><span style={{ color: zk.color, fontSize: 12 }}>{zk.icon}</span></Tooltip>
          {dept.current_personnel_count !== undefined && (
            <Tag icon={<TeamOutlined />} color="default" style={{ fontSize: 11 }}>{dept.current_personnel_count}/{dept.max_personnel || '∞'}</Tag>
          )}
          {dept.manager_name && (
            <Tag icon={<UserOutlined />} color="geekblue" style={{ fontSize: 11 }}>{dept.manager_name}</Tag>
          )}
          {isInactive && <StatusPill status={dept.status || 'inactive'} />}
        </Space>
        <Space size={2} onClick={(e) => e.stopPropagation()}>
          <Tooltip title="View Details"><Button type="text" size="small" icon={<EyeOutlined />} onClick={() => openDrawer(dept)} /></Tooltip>
          <Tooltip title="Add Sub-department"><Button type="text" size="small" icon={<PlusOutlined />} onClick={() => handleAdd(dept.id)} /></Tooltip>
          <Tooltip title="Edit"><Button type="text" size="small" icon={<EditOutlined />} onClick={() => handleEdit(dept)} /></Tooltip>
          <Dropdown trigger={['click']} menu={{
            items: [
              { key: 'clone', label: 'Clone', icon: <CopyOutlined />, onClick: () => handleClone(dept) },
              ...(isInactive
                ? [{ key: 'reactivate', label: 'Reactivate', icon: <UndoOutlined />, onClick: () => reactivateMutation.mutate(dept.id) }]
                : [{ key: 'deactivate', label: 'Deactivate', icon: <DeleteOutlined />, danger: true,
                    onClick: () => Modal.confirm({
                      title: 'Deactivate department?', icon: <ExclamationCircleOutlined />,
                      content: 'Sub-departments and personnel will be affected.',
                      okText: 'Deactivate', okType: 'danger',
                      onOk: () => deleteMutation.mutate(dept.id),
                    }),
                  }]
              ),
            ],
          }}>
            <Button type="text" size="small" icon={<MoreOutlined />} />
          </Dropdown>
        </Space>
      </div>
    );
  };

  const renderTreeNodes = (nodes) =>
    nodes.map(n => ({ ...n, title: renderTreeTitle(n), children: n.children ? renderTreeNodes(n.children) : [] }));

  // ── Row selection ──────────────────────────────────────────────────────────

  const rowSelection = {
    selectedRowKeys,
    onChange: (keys) => setSelectedRowKeys(keys),
    selections: [
      Table.SELECTION_ALL,
      Table.SELECTION_INVERT,
      Table.SELECTION_NONE,
      { key: 'active', text: 'Select Active Only', onSelect: () => setSelectedRowKeys(filteredDepts.filter(d => (d.status || 'active') === 'active').map(d => d.id)) },
      { key: 'safety', text: 'Select Safety Critical', onSelect: () => setSelectedRowKeys(filteredDepts.filter(d => d.safety_critical).map(d => d.id)) },
    ],
    getCheckboxProps: (record) => ({ name: record.name }),
  };

  // ── Table columns ──────────────────────────────────────────────────────────

  const tableColumns = [
    {
      title: 'Department', dataIndex: 'name', key: 'name', width: 230,
      sorter: (a, b) => (a.name || '').localeCompare(b.name || ''),
      defaultSortOrder: 'ascend',
      render: (name, rec) => {
        const typeCfg = TYPE_CFG_PILL[rec.department_type] || { color: '#6b7280', bg: '#f3f4f6', border: '#e5e7eb' };
        return (
          <Space size={10}>
            <div style={{
              width: 34, height: 34, borderRadius: 8, flexShrink: 0,
              background: typeCfg.bg, border: `1px solid ${typeCfg.border}`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
            }}>
              <ApartmentOutlined style={{ color: typeCfg.color, fontSize: 15 }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <button type="button"
                  style={{ background: 'none', border: 'none', padding: 0, color: '#1d4ed8', cursor: 'pointer', fontWeight: 600, fontSize: 13 }}
                  onClick={() => openDrawer(rec)}>{name}</button>
                {rec.safety_critical && (
                  <Tooltip title="Safety Critical"><SafetyOutlined style={{ color: '#dc2626', fontSize: 11 }} /></Tooltip>
                )}
              </div>
              <div style={{ fontSize: 11, color: '#8c8c8c', fontFamily: 'monospace' }}>{rec.code}</div>
              {rec.parent_name && (
                <div style={{ fontSize: 11, color: '#8c8c8c', marginTop: 1 }}>
                  <ApartmentOutlined style={{ marginRight: 3, fontSize: 10 }} />{rec.parent_name}
                </div>
              )}
            </div>
          </Space>
        );
      },
    },
    {
      title: 'Type', dataIndex: 'department_type', key: 'type', width: 130,
      sorter: (a, b) => (a.department_type || '').localeCompare(b.department_type || ''),
      filters: DEPT_TYPES.map(t => ({ text: t.charAt(0).toUpperCase() + t.slice(1), value: t })),
      onFilter: (value, record) => record.department_type === value,
      render: (t) => <TypePill type={t} />,
    },
    {
      title: 'Status', dataIndex: 'status', key: 'status', width: 120,
      sorter: (a, b) => (a.status || 'active').localeCompare(b.status || 'active'),
      filters: Object.keys(STATUS_CFG_PILL).map(s => ({ text: s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()), value: s })),
      onFilter: (value, record) => (record.status || 'active') === value,
      render: (s) => <StatusPill status={s} />,
    },
    {
      title: 'Manager', key: 'manager', width: 150,
      sorter: (a, b) => (a.manager_name || '').localeCompare(b.manager_name || ''),
      render: (_, rec) => rec.manager_name
        ? (
          <Space size={6}>
            <Avatar size={22} style={{ background: avatarColor(rec.manager_name), fontSize: 9, fontWeight: 600, flexShrink: 0 }}>
              {initials(rec.manager_name)}
            </Avatar>
            <span style={{ fontSize: 12 }}>{rec.manager_name}</span>
          </Space>
        )
        : <span style={{ color: '#bfbfbf', fontSize: 12 }}>—</span>,
    },
    {
      title: 'Personnel', key: 'personnel', width: 100, align: 'center',
      sorter: (a, b) => (a.current_personnel_count || 0) - (b.current_personnel_count || 0),
      render: (_, rec) => (
        <span style={{ fontSize: 13 }}>
          <strong>{rec.current_personnel_count || 0}</strong>
          <span style={{ color: '#bfbfbf' }}> / {rec.max_personnel || '∞'}</span>
        </span>
      ),
    },
    {
      title: 'Vacancies', key: 'vacancy', width: 90, align: 'center',
      sorter: (a, b) => {
        const va = a.max_personnel ? Math.max(0, a.max_personnel - (a.current_personnel_count || 0)) : null;
        const vb = b.max_personnel ? Math.max(0, b.max_personnel - (b.current_personnel_count || 0)) : null;
        return (va ?? -1) - (vb ?? -1);
      },
      render: (_, rec) => {
        if (!rec.max_personnel) return <span style={{ color: '#bfbfbf' }}>—</span>;
        const v = Math.max(0, rec.max_personnel - (rec.current_personnel_count || 0));
        return (
          <Tag color={v === 0 ? 'error' : v <= 3 ? 'warning' : 'success'} style={{ fontWeight: 600 }}>
            {v} open
          </Tag>
        );
      },
    },
    {
      title: 'Sub-depts', key: 'subdepts', width: 90, align: 'center',
      sorter: (a, b) => (a.sub_departments_count || 0) - (b.sub_departments_count || 0),
      render: (_, rec) => rec.sub_departments_count > 0
        ? <Tag icon={<ApartmentOutlined />} color="geekblue" style={{ fontSize: 11 }}>{rec.sub_departments_count}</Tag>
        : <span style={{ color: '#bfbfbf' }}>—</span>,
    },
    {
      title: 'Default Shift', key: 'shift', width: 140,
      render: (_, rec) => rec.default_shift_name
        ? <Tag icon={<ClockCircleOutlined />} color="purple" style={{ fontSize: 11 }}>{rec.default_shift_name}</Tag>
        : <span style={{ color: '#bfbfbf', fontSize: 12 }}>—</span>,
    },
    {
      title: 'ZKTeco', dataIndex: 'zkteco_status', key: 'zkteco', width: 130,
      filters: Object.entries(ZKTECO_CONFIG).map(([k, v]) => ({ text: v.label, value: k })),
      onFilter: (value, record) => (record.zkteco_status || 'not_configured') === value,
      render: (zs) => {
        const zk = ZKTECO_CONFIG[zs] || ZKTECO_CONFIG.not_configured;
        return <Tag icon={zk.icon} color={zk.antColor}>{zk.label}</Tag>;
      },
    },
    {
      title: 'Budget', key: 'budget', width: 120,
      sorter: (a, b) => (a.budget_utilization || 0) - (b.budget_utilization || 0),
      render: (_, rec) => {
        if (!rec.budget_allocated) return <span style={{ color: '#bfbfbf' }}>—</span>;
        return (
          <Tooltip title={`Used: $${Number(rec.budget_used || 0).toLocaleString()} of $${Number(rec.budget_allocated).toLocaleString()}`}>
            <Progress percent={rec.budget_utilization || 0} size="small"
              status={rec.budget_utilization > 90 ? 'exception' : rec.budget_utilization > 75 ? 'active' : 'normal'} />
          </Tooltip>
        );
      },
    },
    {
      title: '', key: 'actions', fixed: 'right', width: 140,
      render: (_, rec) => {
        const isInactive = (rec.status || 'active') !== 'active';
        return (
          <Space size={4}>
            <Tooltip title="View details">
              <Button size="small" type="text" icon={<EyeOutlined />} onClick={() => openDrawer(rec)} />
            </Tooltip>
            <Tooltip title="Edit">
              <Button size="small" type="text" icon={<EditOutlined />} onClick={() => handleEdit(rec)} />
            </Tooltip>
            <Tooltip title="Add sub-department">
              <Button size="small" type="text" icon={<PlusOutlined />} onClick={() => handleAdd(rec.id)} />
            </Tooltip>
            <Dropdown
              trigger={['click']}
              menu={{
                items: [
                  { key: 'clone', label: 'Clone', icon: <CopyOutlined />, onClick: () => handleClone(rec) },
                  { key: 'push', label: 'Push to BioTime', icon: <CloudUploadOutlined />,
                    disabled: rec.zkteco_status === 'synced', onClick: () => handlePushToBiotime(rec.id) },
                  ...(rec.budget_allocated > 0 ? [{ key: 'budget', label: 'Log Expense', icon: <DollarOutlined />, onClick: () => openBudgetModal(rec) }] : []),
                  { type: 'divider' },
                  ...(isInactive
                    ? [{ key: 'reactivate', label: 'Reactivate', icon: <UndoOutlined />, onClick: () => reactivateMutation.mutate(rec.id) }]
                    : [{
                        key: 'deactivate', label: 'Deactivate', icon: <DeleteOutlined />, danger: true,
                        onClick: () => Modal.confirm({
                          title: 'Deactivate department?', icon: <ExclamationCircleOutlined />,
                          content: 'Sub-departments and personnel assignments will be affected.',
                          okText: 'Deactivate', okType: 'danger',
                          onOk: () => deleteMutation.mutate(rec.id),
                        }),
                      }]
                  ),
                ],
              }}
            >
              <Button size="small" type="text" icon={<MoreOutlined />} />
            </Dropdown>
          </Space>
        );
      },
    },
  ];

  const displayedTree = renderTreeNodes(filterTree(treeData));
  const handleModalOk = () => { form.validateFields().then(values => handleSubmit(values)); };
  const selectedDepts = filteredDepts.filter(d => selectedRowKeys.includes(d.id));
  const rootDepts = departments.filter(d => !d.parent_id);

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="personnel-module">
      <Card
        title={
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', overflow: 'visible' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>Department Management</div>
              <div style={{ fontSize: 12, color: '#64748b', fontWeight: 400, marginTop: 2 }}>
                Manage organisational departments, hierarchy, personnel and ZKTeco sync
              </div>
            </div>
            <Space size="middle" style={{ overflow: 'visible' }}>
              <Button icon={<ReloadOutlined />} size="small" onClick={() => { refetch(); queryClient.invalidateQueries({ queryKey: ['departments-summary'] }); }}>
                Refresh
              </Button>
              <Button type="primary" icon={<PlusOutlined />} size="small" onClick={() => handleAdd()}>
                New Department
              </Button>
            </Space>
          </div>
        }
        styles={{ header: { overflow: 'visible' } }}
      >

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          // ── Departments tab ──────────────────────────────────────────────
          {
            key: 'overview',
            label: 'Departments',
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* KPI strip */}
                <Row gutter={12}>
                  {[
                    { title: 'Total Departments', value: summary.total_departments || departments.length, color: '#2563eb', icon: <ApartmentOutlined /> },
                    { title: 'Active',            value: summary.active || 0,          color: '#16a34a', icon: <CheckCircleOutlined /> },
                    { title: 'Safety Critical',   value: summary.safety_critical || 0, color: '#dc2626', icon: <SafetyOutlined /> },
                    { title: 'ZKTeco Synced',     value: summary.zkteco_synced || 0,   color: '#0891b2', icon: <SyncOutlined /> },
                  ].map(({ title, value, color, icon }) => (
                    <Col key={title} xs={12} sm={6}>
                      <div style={{
                        background: '#fff', borderRadius: 10, padding: '14px 18px',
                        border: '1px solid #f0f0f0', borderTop: `3px solid ${color}`,
                        boxShadow: '0 1px 4px rgba(0,0,0,0.04)',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <div>
                            <div style={{ fontSize: 11, color: '#8c8c8c', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.5px' }}>{title}</div>
                            <div style={{ fontSize: 26, fontWeight: 700, color, lineHeight: 1.2, marginTop: 4 }}>{value}</div>
                          </div>
                          <div style={{ width: 40, height: 40, borderRadius: 10, background: `${color}18`, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                            {React.cloneElement(icon, { style: { color, fontSize: 18 } })}
                          </div>
                        </div>
                      </div>
                    </Col>
                  ))}
                </Row>

                {/* Filters + View toggle */}
                <Card size="small" bodyStyle={{ padding: '10px 16px' }}>
                  <Row gutter={10} align="middle" wrap={false}>
                    <Col flex="1" style={{ minWidth: 180 }}>
                      <Input.Search
                        placeholder="Search name or code…"
                        value={searchText}
                        onChange={e => setSearchText(e.target.value)}
                        allowClear
                        prefix={<FilterOutlined style={{ color: '#bfbfbf' }} />}
                      />
                    </Col>
                    <Col>
                      <Select placeholder="All types" style={{ width: 150 }} value={filterType} onChange={setFilterType} allowClear
                        options={DEPT_TYPES.map(t => ({ value: t, label: t.charAt(0).toUpperCase() + t.slice(1) }))} />
                    </Col>
                    <Col>
                      <Select placeholder="All statuses" style={{ width: 140 }} value={filterStatus} onChange={setFilterStatus} allowClear
                        options={Object.keys(STATUS_CONFIG).map(s => ({ value: s, label: s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }))} />
                    </Col>
                    {hasActiveFilters && (
                      <Col>
                        <Button icon={<ClearOutlined />} onClick={clearFilters} size="small" type="link">Clear</Button>
                      </Col>
                    )}
                    {/* View mode toggle */}
                    <Col>
                      <Space.Compact>
                        <Tooltip title="Tree view">
                          <Button
                            type={viewMode === 'tree' ? 'primary' : 'default'}
                            icon={<ApartmentOutlined />}
                            onClick={() => { setViewMode('tree'); setSelectedRowKeys([]); }}
                            size="middle"
                          />
                        </Tooltip>
                        <Tooltip title="Hierarchy cards">
                          <Button
                            type={viewMode === 'cards' ? 'primary' : 'default'}
                            icon={<BranchesOutlined />}
                            onClick={() => { setViewMode('cards'); setSelectedRowKeys([]); }}
                            size="middle"
                          />
                        </Tooltip>
                        <Tooltip title="Table view">
                          <Button
                            type={viewMode === 'table' ? 'primary' : 'default'}
                            icon={<TableOutlined />}
                            onClick={() => { setViewMode('table'); }}
                            size="middle"
                          />
                        </Tooltip>
                      </Space.Compact>
                    </Col>
                  </Row>
                </Card>

                {/* Active filter pills */}
                {hasActiveFilters && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <span style={{ fontSize: 11, color: '#8c8c8c' }}>Active filters:</span>
                    {searchText && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, background: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe' }}>
                        Search: "{searchText}"
                        <button type="button" onClick={() => setSearchText('')} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: '#2563eb', fontSize: 12, lineHeight: 1 }}>×</button>
                      </span>
                    )}
                    {filterType && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, background: TYPE_CFG_PILL[filterType]?.bg || '#f9fafb', color: TYPE_CFG_PILL[filterType]?.color || '#4b5563', border: `1px solid ${TYPE_CFG_PILL[filterType]?.border || '#e5e7eb'}` }}>
                        Type: {filterType}
                        <button type="button" onClick={() => setFilterType(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit', fontSize: 12, lineHeight: 1 }}>×</button>
                      </span>
                    )}
                    {filterStatus && (
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, background: STATUS_CFG_PILL[filterStatus]?.bg || '#f9fafb', color: STATUS_CFG_PILL[filterStatus]?.color || '#4b5563', border: `1px solid ${STATUS_CFG_PILL[filterStatus]?.border || '#e5e7eb'}` }}>
                        Status: {filterStatus.replace('_', ' ')}
                        <button type="button" onClick={() => setFilterStatus(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: 0, color: 'inherit', fontSize: 12, lineHeight: 1 }}>×</button>
                      </span>
                    )}
                    <button type="button" onClick={clearFilters} style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '2px 6px', fontSize: 11, color: '#8c8c8c', textDecoration: 'underline' }}>Clear all</button>
                  </div>
                )}

                {/* Bulk-actions bar — only visible in table mode when rows are selected */}
                {viewMode === 'table' && selectedRowKeys.length > 0 && (
                  <Card size="small" bodyStyle={{ padding: '8px 16px' }} style={{ border: '1px solid #1890ff', background: '#e6f4ff' }}>
                    <Row align="middle" gutter={12}>
                      <Col><CheckSquareOutlined style={{ color: '#1890ff', fontSize: 16 }} /></Col>
                      <Col><Text strong style={{ color: '#1890ff' }}>{selectedRowKeys.length} row{selectedRowKeys.length !== 1 ? 's' : ''} selected</Text></Col>
                      <Col flex="1" />
                      <Col>
                        <Space size={8}>
                          <Button size="small" icon={<DownloadOutlined />} onClick={() => handleExportCSV(selectedDepts)}>Export CSV</Button>
                          <Popconfirm
                            title={`Deactivate ${selectedRowKeys.length} department(s)?`}
                            description="This action affects personnel assignments and sub-departments."
                            icon={<ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />}
                            onConfirm={handleBulkDeactivate} okText="Deactivate All" okType="danger"
                          >
                            <Button size="small" danger icon={<DeleteOutlined />} loading={bulkDeactivating}>Deactivate Selected</Button>
                          </Popconfirm>
                          <Button size="small" type="text" onClick={() => setSelectedRowKeys([])}>Clear selection</Button>
                        </Space>
                      </Col>
                    </Row>
                  </Card>
                )}

                {/* Content */}
                <Card size="small" bodyStyle={{ padding: viewMode === 'cards' ? '16px 20px' : 0 }}>
                  <Spin spinning={isLoading}>
                    {viewMode === 'tree' && (
                      displayedTree.length > 0 ? (
                        <div style={{ padding: '12px 16px' }}>
                          <Tree
                            treeData={displayedTree}
                            expandedKeys={expandedKeys}
                            onExpand={setExpandedKeys}
                            showLine={{ showLeafIcon: false }}
                            blockNode
                            style={{ fontSize: 13 }}
                          />
                        </div>
                      ) : (
                        <div style={{ padding: 24 }}>
                          <Empty image={Empty.PRESENTED_IMAGE_SIMPLE}
                            description={departments.length === 0 ? 'No departments yet. Create your first department.' : 'No results match your filters.'}>
                            {departments.length === 0 && <Button type="primary" icon={<PlusOutlined />} onClick={() => handleAdd()}>Create Department</Button>}
                            {departments.length > 0 && hasActiveFilters && <Button onClick={clearFilters}>Clear Filters</Button>}
                          </Empty>
                        </div>
                      )
                    )}

                    {viewMode === 'cards' && (
                      rootDepts.length > 0 ? (
                        <div style={{ minHeight: 200 }}>
                          {(hasActiveFilters ? filteredDepts.filter(d => !d.parent_id || !filteredDepts.find(p => p.id === d.parent_id)) : rootDepts).map(dept => (
                            <HierarchyCardNode
                              key={dept.id}
                              dept={dept}
                              departments={hasActiveFilters ? filteredDepts : departments}
                              onView={openDrawer}
                              onEdit={handleEdit}
                              onAdd={handleAdd}
                              onClone={handleClone}
                              onReactivate={(id) => reactivateMutation.mutate(id)}
                              onDeactivate={(id) => deleteMutation.mutate(id)}
                            />
                          ))}
                        </div>
                      ) : (
                        <Empty image={Empty.PRESENTED_IMAGE_SIMPLE}
                          description={departments.length === 0 ? 'No departments yet.' : 'No results match your filters.'}>
                          {departments.length === 0 && <Button type="primary" icon={<PlusOutlined />} onClick={() => handleAdd()}>Create Department</Button>}
                          {departments.length > 0 && hasActiveFilters && <Button onClick={clearFilters}>Clear Filters</Button>}
                        </Empty>
                      )
                    )}

                    {viewMode === 'table' && (
                      <Table
                        columns={tableColumns}
                        dataSource={filteredDepts}
                        loading={isLoading}
                        rowKey="id"
                        rowSelection={rowSelection}
                        size="small"
                        rowClassName={(r) => (r.status || 'active') !== 'active' ? 'row-inactive' : ''}
                        onChange={() => setSelectedRowKeys([])}
                        pagination={{
                          pageSize: 20, showSizeChanger: true, showQuickJumper: true,
                          showTotal: (total, range) => (
                            <span>
                              {range[0]}–{range[1]} of <strong>{total}</strong> departments
                              {selectedRowKeys.length > 0 && <span style={{ color: '#1890ff', marginLeft: 8 }}>({selectedRowKeys.length} selected)</span>}
                            </span>
                          ),
                        }}
                        scroll={{ x: 1500 }}
                        locale={{
                          emptyText: (
                            <Empty image={Empty.PRESENTED_IMAGE_SIMPLE}
                              description={hasActiveFilters ? 'No departments match your filters.' : 'No departments yet.'}>
                              {hasActiveFilters
                                ? <Button onClick={clearFilters}>Clear Filters</Button>
                                : <Button type="primary" icon={<PlusOutlined />} onClick={() => handleAdd()}>Create Department</Button>}
                            </Empty>
                          ),
                        }}
                        footer={filteredDepts.length > 0 ? () => (
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 12, color: '#8c8c8c' }}>
                            <span>
                              Showing {filteredDepts.length} of {departments.length} departments
                              {hasActiveFilters && <Button type="link" size="small" onClick={clearFilters} style={{ padding: '0 4px', fontSize: 12 }}>Clear filters</Button>}
                            </span>
                            <Button size="small" type="text" icon={<DownloadOutlined />} onClick={() => handleExportCSV(filteredDepts)} style={{ color: '#8c8c8c' }}>
                              Export all ({filteredDepts.length})
                            </Button>
                          </div>
                        ) : undefined}
                      />
                    )}
                  </Spin>
                </Card>
              </div>
            ),
          },

          // ── Analytics tab ────────────────────────────────────────────────
          {
            key: 'analytics',
            label: 'Analytics',
            children: <AnalyticsTab departments={departments} summary={summary} />,
          },

          // ── ZKTeco Sync tab ──────────────────────────────────────────────
          {
            key: 'zkteco',
            label: <Space><ThunderboltOutlined />ZKTeco Sync</Space>,
            children: <ZktecoSyncTab departments={departments} onPushAll={handlePushToBiotime} pushingId={pushingId} />,
          },
        ]}
      />

      {/* ── Create / Edit Modal ── */}
      <Modal
        title={editingDept ? `Edit Department — ${editingDept.name}` : 'New Department'}
        open={isModalVisible}
        onOk={handleModalOk}
        onCancel={() => { setIsModalVisible(false); form.resetFields(); }}
        okText={editingDept ? 'Save Changes' : 'Create'}
        confirmLoading={isMutating}
        width={760}
        forceRender
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item label="Department Name" name="name" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="e.g., Operations" />
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item label="Code" name="code" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="e.g., OPS-001" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Type" name="department_type">
                <Select placeholder="Select type" allowClear
                  options={DEPT_TYPES.map(t => ({ value: t, label: t.charAt(0).toUpperCase() + t.slice(1) }))} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Parent Department" name="parent_id">
                <Select placeholder="Root (no parent)" allowClear showSearch optionFilterProp="children">
                  {departments.filter(d => !editingDept || d.id !== editingDept.id).map(d => (
                    <Option key={d.id} value={d.id}>{d.name} <Tag style={{ fontSize: 10 }}>{d.code}</Tag></Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Manager" name="manager_id">
                <Select placeholder="— none —" allowClear showSearch optionFilterProp="label"
                  options={personnelList.map(p => ({
                    value: p.id,
                    label: `${p.first_name || ''} ${p.last_name || ''}`.trim() || p.full_name || `#${p.id}`,
                  }))}
                  optionRender={(opt) => (
                    <Space>
                      <Avatar size={20} style={{ background: avatarColor(opt.label), fontSize: 9 }}>{initials(opt.label)}</Avatar>
                      <span>{opt.label}</span>
                    </Space>
                  )}
                />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item label="Description" name="description">
            <Input.TextArea rows={2} placeholder="Brief description…" />
          </Form.Item>

          <Divider style={{ margin: '12px 0' }}>Contact</Divider>
          <Row gutter={16}>
            <Col span={8}><Form.Item label="Contact Person" name="contact_person"><Input prefix={<UserOutlined />} placeholder="Name" /></Form.Item></Col>
            <Col span={8}><Form.Item label="Email" name="contact_email"><Input prefix={<MailOutlined />} placeholder="email@company.com" /></Form.Item></Col>
            <Col span={8}><Form.Item label="Phone" name="contact_phone"><Input prefix={<PhoneOutlined />} placeholder="+1234567890" /></Form.Item></Col>
          </Row>

          <Divider style={{ margin: '12px 0' }}>Capacity & Budget</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Max Personnel" name="max_personnel">
                <InputNumber min={0} placeholder="50" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="Budget Allocated ($)" name="budget_allocated">
                <InputNumber min={0} style={{ width: '100%' }}
                  formatter={v => `$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                  parser={v => v.replace(/\$\s?|(,*)/g, '')} />
              </Form.Item>
            </Col>
            {editingDept && (
              <Col span={8}>
                <Form.Item label="Status" name="status">
                  <Select options={Object.keys(STATUS_CONFIG).map(s => ({ value: s, label: s.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase()) }))} />
                </Form.Item>
              </Col>
            )}
          </Row>

          <Divider style={{ margin: '12px 0' }}>Safety & ZKTeco</Divider>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item label="Safety Critical" name="safety_critical" valuePropName="checked">
                <Switch checkedChildren={<SafetyOutlined />} unCheckedChildren="No" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item label="ZKTeco Sync" name="zkteco_sync_enabled" valuePropName="checked">
                <Switch checkedChildren={<SyncOutlined />} unCheckedChildren="Off" />
              </Form.Item>
            </Col>
            {editingDept && (
              <Col span={8}>
                <Form.Item label="ZKTeco Dept ID" name="zkteco_department_id">
                  <InputNumber min={1} placeholder="BioTime ID" style={{ width: '100%' }} />
                </Form.Item>
              </Col>
            )}
          </Row>

          <Divider style={{ margin: '12px 0' }}>Attendance</Divider>
          <Row gutter={16}>
            <Col span={14}>
              <Form.Item label="Default Shift" name="default_shift_id"
                tooltip="Employees in this department with no direct shift assignment will use this shift for attendance calculation">
                <Select placeholder="— inherit global default —" allowClear showSearch optionFilterProp="children" style={{ width: '100%' }}>
                  {shifts.map(s => <Option key={s.id} value={s.id}>{s.name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* ── Clone Modal ── */}
      <Modal
        title={
          <Space>
            <CopyOutlined style={{ color: '#722ed1' }} />
            Clone Department {cloneSource ? `— ${cloneSource.name}` : ''}
          </Space>
        }
        open={cloneModal}
        onCancel={() => { setCloneModal(false); setCloneSource(null); cloneForm.resetFields(); }}
        onOk={() => cloneForm.validateFields().then(v => cloneMutation.mutate({ id: cloneSource.id, ...v }))}
        confirmLoading={cloneMutation.isPending}
        okText="Clone"
        width={440}
      >
        <Alert type="info" showIcon style={{ marginBottom: 16 }}
          message="A copy of all department settings will be created. Personnel assignments and ZKTeco linkage are not cloned." />
        <Form form={cloneForm} layout="vertical">
          <Form.Item label="New Department Name" name="name" rules={[{ required: true, message: 'Required' }]}>
            <Input placeholder="Name for the cloned department" />
          </Form.Item>
          <Form.Item label="New Code" name="code" rules={[{ required: true, message: 'Required' }, { max: 20, message: 'Max 20 characters' }]}>
            <Input placeholder="Unique code (e.g. OPS-002)" style={{ fontFamily: 'monospace' }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Budget Spend Modal ── */}
      <Modal
        title={
          <Space>
            <DollarOutlined style={{ color: '#52c41a' }} />
            Log Budget Expense — {budgetTarget?.name}
          </Space>
        }
        open={budgetModal}
        onCancel={() => { setBudgetModal(false); setBudgetTarget(null); budgetForm.resetFields(); }}
        onOk={() => budgetForm.validateFields().then(v => budgetSpendMutation.mutate({ id: budgetTarget.id, ...v }))}
        confirmLoading={budgetSpendMutation.isPending}
        okText="Log Expense"
        width={400}
      >
        {budgetTarget && (
          <div style={{ marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 4 }}>
              <span style={{ color: '#595959' }}>Allocated</span>
              <strong>${Number(budgetTarget.budget_allocated || 0).toLocaleString()}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 13, marginBottom: 8 }}>
              <span style={{ color: '#595959' }}>Used so far</span>
              <strong>${Number(budgetTarget.budget_used || 0).toLocaleString()}</strong>
            </div>
            <Progress
              percent={budgetTarget.budget_utilization || 0}
              status={budgetTarget.budget_utilization > 90 ? 'exception' : budgetTarget.budget_utilization > 75 ? 'active' : 'normal'}
            />
          </div>
        )}
        <Form form={budgetForm} layout="vertical">
          <Form.Item label="Amount ($)" name="amount" rules={[{ required: true, message: 'Required' }, { type: 'number', min: 0.01, message: 'Must be > 0' }]}>
            <InputNumber
              min={0.01} precision={2} style={{ width: '100%' }}
              formatter={v => `$ ${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
              parser={v => v.replace(/\$\s?|(,*)/g, '')}
              placeholder="0.00"
            />
          </Form.Item>
          <Form.Item label="Description (optional)" name="description">
            <Input placeholder="e.g. Equipment purchase, maintenance supplies…" />
          </Form.Item>
        </Form>
      </Modal>

      {/* ── Details Drawer ── */}
      <Drawer
        title={
          <Space>
            <ApartmentOutlined style={{ color: '#1890ff' }} />
            <span>{drawerDept?.name}</span>
            {drawerDept?.code && <Tag style={{ fontFamily: 'monospace', fontSize: 11 }}>{drawerDept.code}</Tag>}
            {drawerDept?.department_type && <TypePill type={drawerDept.department_type} />}
          </Space>
        }
        open={drawerVisible}
        onClose={() => setDrawerVisible(false)}
        width={580}
        extra={
          <Space>
            {drawerDept && (drawerDept.status || 'active') !== 'active' && (
              <Button icon={<UndoOutlined />} onClick={() => { reactivateMutation.mutate(drawerDept.id); setDrawerVisible(false); }}
                loading={reactivateMutation.isPending}>
                Reactivate
              </Button>
            )}
            <Button icon={<CopyOutlined />} onClick={() => { setDrawerVisible(false); handleClone(drawerDept); }}>Clone</Button>
            <Button icon={<EditOutlined />} type="primary" onClick={() => { setDrawerVisible(false); handleEdit(drawerDept); }}>Edit</Button>
          </Space>
        }
      >
        {drawerDept && (
          <Tabs activeKey={drawerTab} onChange={setDrawerTab} size="small" items={[

            // ── Overview tab ──────────────────────────────────────────────
            {
              key: 'overview',
              label: <Space><InfoCircleOutlined />Overview</Space>,
              children: (() => {
                const zk = ZKTECO_CONFIG[drawerDept.zkteco_status] || ZKTECO_CONFIG.not_configured;
                const vacancy = drawerDept.max_personnel ? Math.max(0, drawerDept.max_personnel - (drawerDept.current_personnel_count || 0)) : null;
                const isInactive = (drawerDept.status || 'active') !== 'active';
                return (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                    {isInactive && (
                      <Alert
                        message="This department is inactive"
                        type="warning"
                        showIcon
                        action={
                          <Button size="small" icon={<UndoOutlined />} onClick={() => { reactivateMutation.mutate(drawerDept.id); setDrawerVisible(false); }}
                            loading={reactivateMutation.isPending}>
                            Reactivate
                          </Button>
                        }
                      />
                    )}
                    {drawerDept.safety_critical && (
                      <Alert message="Safety Critical Department" type="error" icon={<SafetyOutlined />} showIcon />
                    )}
                    <Alert
                      message={<Space>{zk.icon}<span>ZKTeco: <strong>{zk.label}</strong></span>{drawerDept.zkteco_department_id && <Tag>ID #{drawerDept.zkteco_department_id}</Tag>}</Space>}
                      type={drawerDept.zkteco_status === 'synced' ? 'success' : drawerDept.zkteco_status === 'pending' ? 'warning' : 'info'}
                    />

                    {/* Key metrics */}
                    <Row gutter={10}>
                      <Col span={6}>
                        <Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #1890ff' }}>
                          <Statistic title="Personnel" value={drawerDept.current_personnel_count || 0}
                            suffix={drawerDept.max_personnel ? `/ ${drawerDept.max_personnel}` : ''}
                            valueStyle={{ color: '#1890ff', fontSize: 18 }} prefix={<TeamOutlined />} />
                        </Card>
                      </Col>
                      {vacancy !== null && (
                        <Col span={6}>
                          <Card size="small" style={{ textAlign: 'center', borderTop: `3px solid ${vacancy === 0 ? '#ff4d4f' : vacancy <= 3 ? '#faad14' : '#52c41a'}` }}>
                            <Statistic title="Vacancies" value={vacancy}
                              valueStyle={{ color: vacancy === 0 ? '#ff4d4f' : vacancy <= 3 ? '#faad14' : '#52c41a', fontSize: 18 }} />
                          </Card>
                        </Col>
                      )}
                      <Col span={vacancy !== null ? 6 : 8}>
                        <Card size="small" style={{ textAlign: 'center', borderTop: '3px solid #722ed1' }}>
                          <Statistic title="Sub-depts" value={drawerDept.sub_departments_count || 0}
                            valueStyle={{ color: '#722ed1', fontSize: 18 }} prefix={<ApartmentOutlined />} />
                        </Card>
                      </Col>
                      <Col span={vacancy !== null ? 6 : 8}>
                        <Card size="small" style={{ textAlign: 'center', borderTop: isInactive ? '3px solid #dc2626' : '3px solid #16a34a' }}>
                          <div style={{ fontSize: 12, color: '#8c8c8c', marginBottom: 6 }}>Status</div>
                          <StatusPill status={drawerDept.status} />
                        </Card>
                      </Col>
                    </Row>

                    <Descriptions column={2} size="small" bordered>
                      {drawerDept.parent_name && (
                        <Descriptions.Item label="Parent Dept" span={2}>
                          <Space><ApartmentOutlined style={{ color: '#8c8c8c' }} />{drawerDept.parent_name}</Space>
                        </Descriptions.Item>
                      )}
                      <Descriptions.Item label="Manager" span={2}>
                        {drawerDept.manager_name
                          ? <Space>
                              <Avatar size={24} style={{ background: avatarColor(drawerDept.manager_name), fontSize: 10 }}>{initials(drawerDept.manager_name)}</Avatar>
                              <span>{drawerDept.manager_name}</span>
                            </Space>
                          : <span style={{ color: '#bfbfbf' }}>—</span>
                        }
                      </Descriptions.Item>
                      {drawerDept.zone_name && (
                        <Descriptions.Item label="Warehouse" span={2}>
                          <Space><EnvironmentOutlined style={{ color: '#13c2c2' }} />{drawerDept.zone_name}</Space>
                        </Descriptions.Item>
                      )}
                      <Descriptions.Item label="Default Shift" span={2}>
                        {drawerDept.default_shift_name
                          ? <Tag icon={<ClockCircleOutlined />} color="purple">{drawerDept.default_shift_name}</Tag>
                          : <span style={{ color: '#bfbfbf' }}>—</span>
                        }
                      </Descriptions.Item>
                      {drawerDept.description && (
                        <Descriptions.Item label="Description" span={2}>{drawerDept.description}</Descriptions.Item>
                      )}
                    </Descriptions>

                    {drawerDept.budget_allocated > 0 && (
                      <>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                          <Divider style={{ margin: '4px 0', flex: 1 }}>Budget</Divider>
                          <Button size="small" icon={<DollarOutlined />} style={{ marginLeft: 10 }}
                            onClick={() => openBudgetModal(drawerDept)}>
                            Log Expense
                          </Button>
                        </div>
                        <Row gutter={12} style={{ marginBottom: 8 }}>
                          <Col span={12}><Statistic title="Allocated" value={drawerDept.budget_allocated} prefix="$" precision={0} valueStyle={{ fontSize: 16 }} /></Col>
                          <Col span={12}><Statistic title="Used"      value={drawerDept.budget_used || 0} prefix="$" precision={0} valueStyle={{ fontSize: 16 }} /></Col>
                        </Row>
                        <Progress percent={drawerDept.budget_utilization || 0}
                          status={drawerDept.budget_utilization > 90 ? 'exception' : drawerDept.budget_utilization > 75 ? 'active' : 'normal'} />
                      </>
                    )}

                    <Divider style={{ margin: '8px 0' }}>Contact</Divider>
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label={<Space><UserOutlined />Person</Space>}>{drawerDept.contact_person || <span style={{ color: '#bfbfbf' }}>—</span>}</Descriptions.Item>
                      <Descriptions.Item label={<Space><MailOutlined />Email</Space>}>
                        {drawerDept.contact_email ? <a href={`mailto:${drawerDept.contact_email}`}>{drawerDept.contact_email}</a> : <span style={{ color: '#bfbfbf' }}>—</span>}
                      </Descriptions.Item>
                      <Descriptions.Item label={<Space><PhoneOutlined />Phone</Space>}>{drawerDept.contact_phone || <span style={{ color: '#bfbfbf' }}>—</span>}</Descriptions.Item>
                    </Descriptions>

                    <Divider style={{ margin: '8px 0' }}>Audit</Divider>
                    <Descriptions column={1} size="small">
                      <Descriptions.Item label="Created">{drawerDept.created_at ? dayjs(drawerDept.created_at).format('DD MMM YYYY HH:mm') : '—'}</Descriptions.Item>
                      <Descriptions.Item label="Last Updated">{drawerDept.updated_at ? dayjs(drawerDept.updated_at).format('DD MMM YYYY HH:mm') : '—'}</Descriptions.Item>
                    </Descriptions>

                    <div style={{ paddingTop: 8 }}>
                      <Space wrap>
                        <Button type="primary" icon={<PlusOutlined />} onClick={() => { setDrawerVisible(false); handleAdd(drawerDept.id); }}>
                          Add Sub-department
                        </Button>
                        {drawerDept.zkteco_status === 'not_configured' && (
                          <Button icon={<CloudUploadOutlined />} loading={pushingId === drawerDept.id}
                            onClick={() => { handlePushToBiotime(drawerDept.id); setDrawerVisible(false); }}>
                            Push to BioTime
                          </Button>
                        )}
                        {!isInactive && (
                          <Popconfirm title="Deactivate this department?"
                            onConfirm={() => { deleteMutation.mutate(drawerDept.id); setDrawerVisible(false); }}
                            okText="Deactivate" okType="danger">
                            <Button danger icon={<DeleteOutlined />}>Deactivate</Button>
                          </Popconfirm>
                        )}
                      </Space>
                    </div>
                  </div>
                );
              })(),
            },

            // ── Personnel tab ─────────────────────────────────────────────
            {
              key: 'personnel',
              label: (
                <Space>
                  <TeamOutlined />
                  Personnel
                  {drawerDept.current_personnel_count > 0 && (
                    <Tag style={{ fontSize: 10, marginLeft: 0 }}>{drawerDept.current_personnel_count}</Tag>
                  )}
                </Space>
              ),
              children: <DeptPersonnelTab deptId={drawerDept.id} departments={departments} onEdit={handleEdit} />,
            },

            // ── Sub-departments tab ───────────────────────────────────────
            {
              key: 'subdepts',
              label: (
                <Space>
                  <ApartmentOutlined />
                  Sub-depts
                  {(drawerDept.sub_departments_count || 0) > 0 && (
                    <Tag style={{ fontSize: 10, marginLeft: 0 }}>{drawerDept.sub_departments_count}</Tag>
                  )}
                </Space>
              ),
              children: (
                <SubDepartmentsTab
                  deptId={drawerDept.id}
                  departments={departments}
                  onView={(d) => { setDrawerDept(d); setDrawerTab('overview'); }}
                  onEdit={(d) => { setDrawerVisible(false); handleEdit(d); }}
                  onAdd={handleAdd}
                />
              ),
            },

          ]} />
        )}
      </Drawer>

      <style>{`
        .pob-sidebar-scroll::-webkit-scrollbar { width: 4px; }
        .pob-sidebar-scroll::-webkit-scrollbar-track { background: transparent; }
        .pob-sidebar-scroll::-webkit-scrollbar-thumb { background: rgba(0,0,0,0.12); border-radius: 2px; }
        .ant-table-tbody .row-inactive > td { background: #fff8f8 !important; }
        .ant-table-tbody .row-inactive:hover > td { background: #fff1f1 !important; }
        .ant-table-tbody .row-inactive > td:first-child { border-left: 3px solid #fca5a5 !important; }
      `}</style>
      </Card>
    </div>
  );
};

export default DepartmentTree;
