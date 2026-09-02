/**
 * EmployeeDrawer — full-detail side panel for a personnel record.
 * Shown when a user clicks "View" on the PersonnelList.
 *
 * Tabs: Overview · Medical & Safety · Certifications · Medical Fitness
 *       Status History · Biometrics · MTD Compliance · Activity · Audit Trail
 *
 * Quick actions in the header: Check-In, Check-Out, Quick Status Change, Edit, Deactivate, Delete
 */
import React, { useState } from 'react';
import {
  Drawer, Avatar, Tag, Button, Space, Tabs, Descriptions, Divider,
  Select, Timeline, Table, Spin, Empty, Badge, Tooltip, Popconfirm,
  Alert, Progress, Modal, Form, Input, DatePicker, App, Row, Col,
  Typography, List,
} from 'antd';
import {
  EditOutlined, DeleteOutlined, StopOutlined, ScanOutlined,
  MedicineBoxOutlined, SolutionOutlined, SafetyOutlined,
  MailOutlined, PhoneOutlined, EnvironmentOutlined,
  ThunderboltOutlined, ClockCircleOutlined, CheckCircleOutlined,
  LoginOutlined, LogoutOutlined, SwapOutlined, FileProtectOutlined,
  AuditOutlined, HistoryOutlined, AlertOutlined, ExportOutlined,
  CalendarOutlined, UserOutlined, TeamOutlined, ExclamationCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../../services/api';

dayjs.extend(relativeTime);

const { Option } = Select;
const { Text } = Typography;

const STATUS_PILL = {
  ACTIVE:   { bg: '#f0fdf4', border: '#bbf7d0', text: '#15803d', dot: '#22c55e' },
  INACTIVE: { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c', dot: '#ef4444' },
  ON_LEAVE: { bg: '#fffbeb', border: '#fed7aa', text: '#b45309', dot: '#f59e0b' },
  OFFSHORE: { bg: '#eff6ff', border: '#bfdbfe', text: '#1d4ed8', dot: '#3b82f6' },
  ONSHORE:  { bg: '#f0fdfa', border: '#99f6e4', text: '#0f766e', dot: '#14b8a6' },
  TRANSIT:  { bg: '#fdf4ff', border: '#e9d5ff', text: '#7e22ce', dot: '#a855f7' },
};
const STATUS_OPTIONS = ['ACTIVE', 'INACTIVE', 'ON_LEAVE', 'OFFSHORE', 'ONSHORE', 'TRANSIT'];
const TYPE_COLOR = { STAFF: 'blue', CONTRACTOR: 'orange', VISITOR: 'purple' };
const PUNCH_META = {
  0: { label: 'Check In',  color: '#52c41a', bg: '#f6ffed', icon: <LoginOutlined /> },
  1: { label: 'Check Out', color: '#1677ff', bg: '#e6f4ff', icon: <LogoutOutlined /> },
  2: { label: 'Break Out', color: '#fa8c16', bg: '#fff7e6', icon: '↑' },
  3: { label: 'Break In',  color: '#722ed1', bg: '#f9f0ff', icon: '↓' },
};

const AVATAR_PALETTE = ['#2563eb','#7c3aed','#db2777','#059669','#d97706','#dc2626','#0891b2','#65a30d'];
const avatarColor = (str) => AVATAR_PALETTE[(str || '').charCodeAt(0) % AVATAR_PALETTE.length];
const initials = (name) => (name || '').split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?';

const StatusPill = ({ status }) => {
  const s = (status || '').toUpperCase();
  const c = STATUS_PILL[s] || { bg: '#f4f4f5', border: '#e4e4e7', text: '#52525b', dot: '#a1a1aa' };
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: c.bg, border: `1px solid ${c.border}`, color: c.text, borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 600, whiteSpace: 'nowrap' }}>
      <span style={{ width: 6, height: 6, borderRadius: '50%', background: c.dot, flexShrink: 0 }} />
      {s.replace('_', ' ')}
    </span>
  );
};

// ── Tab: Overview ──────────────────────────────────────────────────────────────
const OverviewTab = ({ rec, zoneMap }) => (
  <>
    <Descriptions column={2} size="small" bordered>
      <Descriptions.Item label="Emp Code">
        <Tag style={{ fontFamily: 'monospace', fontWeight: 700 }}>{rec.emp_code}</Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Badge / Card">
        {rec.badge_id && rec.badge_id !== rec.emp_code ? <code>{rec.badge_id}</code> : <Text type="secondary">—</Text>}
      </Descriptions.Item>
      <Descriptions.Item label="Full Name" span={2}>
        <strong>{rec.full_name || `${rec.first_name || ''} ${rec.last_name || ''}`.trim()}</strong>
      </Descriptions.Item>
      <Descriptions.Item label="Status"><StatusPill status={rec.status} /></Descriptions.Item>
      <Descriptions.Item label="POB">
        <Tag color={rec.is_onboard ? 'green' : 'default'} style={{ fontWeight: 700 }}>
          {rec.is_onboard ? '✓ ON BOARD' : 'OFF BOARD'}
        </Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Personnel Type">
        <Tag color={TYPE_COLOR[rec.personnel_type] || 'default'}>{rec.personnel_type || '—'}</Tag>
      </Descriptions.Item>
      <Descriptions.Item label="Employment Type">{rec.employment_type || '—'}</Descriptions.Item>
      <Descriptions.Item label="Hire Date">{rec.hire_date ? dayjs(rec.hire_date).format('DD MMM YYYY') : '—'}</Descriptions.Item>
      <Descriptions.Item label="Nationality">{rec.nationality || '—'}</Descriptions.Item>
    </Descriptions>

    <Divider orientation="left" style={{ fontSize: 12, margin: '14px 0 10px' }}>Employment</Divider>
    <Descriptions column={2} size="small" bordered>
      <Descriptions.Item label="Company" span={2}>{rec.company || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Department">{rec.department || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Role">{rec.role || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Position">{rec.position || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Warehouse">
        {rec.current_zone_id ? (zoneMap.get(rec.current_zone_id) || `Warehouse #${rec.current_zone_id}`) : <Text type="secondary">—</Text>}
      </Descriptions.Item>
    </Descriptions>

    <Divider orientation="left" style={{ fontSize: 12, margin: '14px 0 10px' }}>Contact</Divider>
    <Descriptions column={1} size="small" bordered>
      <Descriptions.Item label={<><MailOutlined /> Email</>}>{rec.email || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label={<><PhoneOutlined /> Phone</>}>{rec.phone || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label={<><EnvironmentOutlined /> Address</>}>{rec.address || <Text type="secondary">—</Text>}</Descriptions.Item>
    </Descriptions>
  </>
);

// ── Tab: Medical & Safety ──────────────────────────────────────────────────────
const MedicalTab = ({ rec }) => (
  <>
    <Descriptions column={2} size="small" bordered>
      <Descriptions.Item label="Blood Group">
        {rec.blood_group ? <Tag color="red" style={{ fontWeight: 700 }}>{rec.blood_group}</Tag> : <Text type="secondary">—</Text>}
      </Descriptions.Item>
      <Descriptions.Item label="Safety Critical">
        {rec.safety_critical
          ? <Tag color="red" icon={<SafetyOutlined />}>YES — Safety Critical</Tag>
          : <Tag color="default">No</Tag>}
      </Descriptions.Item>
      <Descriptions.Item label="National ID">{rec.id_number || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Passport No.">{rec.passport_number || <Text type="secondary">—</Text>}</Descriptions.Item>
      <Descriptions.Item label="Medical Fitness Date">
        {rec.medical_fitness_date ? dayjs(rec.medical_fitness_date).format('DD MMM YYYY') : <Text type="secondary">Not recorded</Text>}
      </Descriptions.Item>
      <Descriptions.Item label="Compliance Score">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Progress
            percent={rec.compliance_score ?? 0}
            size="small"
            style={{ width: 80, margin: 0 }}
            status={rec.compliance_score >= 90 ? 'success' : rec.compliance_score >= 70 ? 'normal' : 'exception'}
          />
          <span style={{ fontWeight: 700, color: rec.compliance_score >= 90 ? '#22c55e' : rec.compliance_score >= 70 ? '#f59e0b' : '#ef4444' }}>
            {rec.compliance_score ?? 0}%
          </span>
        </div>
      </Descriptions.Item>
    </Descriptions>

    {(rec.emergency_contact_name || rec.emergency_contact_phone) && (
      <>
        <Divider orientation="left" style={{ fontSize: 12, margin: '14px 0 10px' }}>Emergency Contact</Divider>
        <Descriptions column={2} size="small" bordered>
          <Descriptions.Item label="Name">{rec.emergency_contact_name || '—'}</Descriptions.Item>
          <Descriptions.Item label="Phone">{rec.emergency_contact_phone || '—'}</Descriptions.Item>
        </Descriptions>
      </>
    )}

    {rec.medical_conditions && (
      <>
        <Divider orientation="left" style={{ fontSize: 12, margin: '14px 0 10px' }}>Medical Conditions</Divider>
        <Alert
          type="warning"
          showIcon
          icon={<ExclamationCircleOutlined />}
          message={rec.medical_conditions}
          style={{ borderRadius: 8 }}
        />
      </>
    )}
  </>
);

// ── Tab: Certifications ────────────────────────────────────────────────────────
const CertificationsTab = ({ personnelId }) => {
  const [addModal, setAddModal] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['personnel-certs', personnelId],
    queryFn: () => apiService.get(`/api/v1/personnel/${personnelId}/certifications`),
    enabled: !!personnelId,
    staleTime: 60000,
  });

  const addMutation = useMutation({
    mutationFn: (payload) => apiService.post(`/api/v1/personnel/${personnelId}/certifications`, payload),
    onSuccess: () => {
      message.success('Certification added');
      setAddModal(false);
      form.resetFields();
      queryClient.invalidateQueries(['personnel-certs', personnelId]);
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'Failed to add certification'),
  });

  const certs = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  const getStatusColor = (cert) => {
    if (!cert.expiry_date) return 'blue';
    const days = dayjs(cert.expiry_date).diff(dayjs(), 'day');
    if (days < 0) return 'red';
    if (days < 30) return 'orange';
    return 'green';
  };

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
        <Button type="primary" size="small" onClick={() => setAddModal(true)}>
          + Add Certification
        </Button>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>
      ) : certs.length === 0 ? (
        <Empty description="No certifications on record" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <List
          dataSource={certs}
          renderItem={cert => {
            const days = cert.expiry_date ? dayjs(cert.expiry_date).diff(dayjs(), 'day') : null;
            return (
              <List.Item style={{ padding: '10px 0' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <FileProtectOutlined style={{ color: '#1677ff' }} />
                    <Text strong>{cert.cert_name || cert.certification_name}</Text>
                    <Tag color={getStatusColor(cert)} style={{ marginLeft: 'auto' }}>
                      {days === null ? 'No Expiry' : days < 0 ? `Expired ${Math.abs(days)}d ago` : days < 30 ? `Expires in ${days}d` : 'Valid'}
                    </Tag>
                  </div>
                  <div style={{ fontSize: 11, color: '#94a3b8', paddingLeft: 20 }}>
                    {cert.issuing_body && <span>{cert.issuing_body} · </span>}
                    {cert.issue_date && <span>Issued: {dayjs(cert.issue_date).format('DD MMM YYYY')} · </span>}
                    {cert.expiry_date && <span>Expires: {dayjs(cert.expiry_date).format('DD MMM YYYY')}</span>}
                  </div>
                </div>
              </List.Item>
            );
          }}
        />
      )}

      <Modal
        title="Add Certification"
        open={addModal}
        onOk={() => form.validateFields().then(v => addMutation.mutate(v))}
        onCancel={() => { setAddModal(false); form.resetFields(); }}
        confirmLoading={addMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="cert_name" label="Certification Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. BOSIET, H2S Awareness, OPITO" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="issuing_body" label="Issuing Body">
                <Input placeholder="e.g. OPITO, NEBOSH" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="cert_number" label="Certificate No.">
                <Input placeholder="Certificate ID" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="issue_date" label="Issue Date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="expiry_date" label="Expiry Date">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </>
  );
};

// ── Tab: Medical Fitness ───────────────────────────────────────────────────────
const MedicalFitnessTab = ({ personnelId }) => {
  const [addModal, setAddModal] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['personnel-fitness', personnelId],
    queryFn: () => apiService.get(`/api/v1/personnel/${personnelId}/medical-fitness`),
    enabled: !!personnelId,
    staleTime: 60000,
  });

  const addMutation = useMutation({
    mutationFn: (payload) => apiService.post(`/api/v1/personnel/${personnelId}/medical-fitness`, payload),
    onSuccess: () => {
      message.success('Medical fitness record added');
      setAddModal(false);
      form.resetFields();
      queryClient.invalidateQueries(['personnel-fitness', personnelId]);
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'Failed'),
  });

  const records = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 10 }}>
        <Button type="primary" size="small" onClick={() => setAddModal(true)}>+ Add Record</Button>
      </div>

      {isLoading ? (
        <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>
      ) : records.length === 0 ? (
        <Empty description="No medical fitness records on file" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table
          dataSource={records}
          rowKey="id"
          size="small"
          pagination={false}
          columns={[
            { title: 'Examination', dataIndex: 'exam_type', key: 'type', render: v => v || 'Medical Fitness' },
            { title: 'Date', dataIndex: 'exam_date', key: 'date', render: d => d ? dayjs(d).format('DD MMM YYYY') : '—' },
            { title: 'Result', dataIndex: 'result', key: 'result',
              render: v => <Tag color={v === 'FIT' ? 'green' : v === 'UNFIT' ? 'red' : 'orange'}>{v || '—'}</Tag> },
            { title: 'Expiry', dataIndex: 'valid_until', key: 'exp',
              render: d => {
                if (!d) return '—';
                const days = dayjs(d).diff(dayjs(), 'day');
                return <span style={{ color: days < 0 ? '#dc2626' : days < 30 ? '#d97706' : '#16a34a', fontWeight: 600 }}>
                  {dayjs(d).format('DD MMM YYYY')}
                </span>;
              },
            },
            { title: 'Doctor', dataIndex: 'doctor_name', key: 'doc', render: v => v || '—' },
          ]}
        />
      )}

      <Modal
        title="Add Medical Fitness Record"
        open={addModal}
        onOk={() => form.validateFields().then(v => addMutation.mutate({ ...v, exam_date: v.exam_date?.format('YYYY-MM-DD'), valid_until: v.valid_until?.format('YYYY-MM-DD') }))}
        onCancel={() => { setAddModal(false); form.resetFields(); }}
        confirmLoading={addMutation.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="exam_type" label="Examination Type" rules={[{ required: true }]}>
            <Input placeholder="e.g. Pre-employment, Annual, Offshore Medical" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="exam_date" label="Date of Examination" rules={[{ required: true }]}>
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="valid_until" label="Valid Until">
                <DatePicker style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="result" label="Result" initialValue="FIT">
                <Select>
                  <Option value="FIT">Fit</Option>
                  <Option value="FIT_WITH_RESTRICTIONS">Fit with Restrictions</Option>
                  <Option value="UNFIT">Unfit</Option>
                  <Option value="PENDING">Pending</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="doctor_name" label="Examining Doctor">
                <Input placeholder="Doctor's name" />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="notes" label="Notes">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

// ── Tab: Status History ────────────────────────────────────────────────────────
const StatusHistoryTab = ({ personnelId }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['personnel-status-history', personnelId],
    queryFn: () => apiService.get(`/api/v1/personnel/${personnelId}/status-history?limit=30`),
    enabled: !!personnelId,
    staleTime: 60000,
  });

  const history = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>;
  if (history.length === 0) return <Empty description="No status history recorded" image={Empty.PRESENTED_IMAGE_SIMPLE} />;

  return (
    <Timeline
      mode="left"
      items={history.map(h => ({
        color: h.new_status === 'ACTIVE' ? 'green' : h.new_status === 'OFFSHORE' ? 'blue' : h.new_status === 'INACTIVE' ? 'red' : 'orange',
        label: <span style={{ fontSize: 11, color: '#94a3b8' }}>{dayjs(h.changed_at || h.created_at).format('DD MMM HH:mm')}</span>,
        children: (
          <div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {h.old_status && <Tag style={{ fontSize: 10 }}>{h.old_status?.replace('_', ' ')}</Tag>}
              {h.old_status && <span style={{ color: '#94a3b8', fontSize: 12 }}>→</span>}
              <StatusPill status={h.new_status} />
            </div>
            {h.location && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 3 }}><EnvironmentOutlined /> {h.location}</div>}
            {h.notes && <div style={{ fontSize: 11, color: '#64748b', marginTop: 3 }}>{h.notes}</div>}
            {h.changed_by && <div style={{ fontSize: 10, color: '#94a3b8', marginTop: 2 }}>by {h.changed_by}</div>}
          </div>
        ),
      }))}
    />
  );
};

// ── Tab: Activity (punch records) ──────────────────────────────────────────────
const ActivityTab = ({ personnelId, empCode }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['emp-activity', personnelId],
    queryFn: () => apiService.get(`/api/v1/personnel/${personnelId}/activity?limit=30`),
    enabled: !!personnelId,
    staleTime: 30_000,
  });
  const tx = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 24 }}><Spin /></div>;
  if (tx.length === 0) return <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={<span style={{ color: '#94a3b8', fontSize: 12 }}>No recent activity</span>} />;

  return (
    <div>
      {tx.map((r, i) => {
        const m = PUNCH_META[r.punch_state] ?? PUNCH_META[r.event_type === 'check_in' ? 0 : 1] ?? { label: 'Event', color: '#8c8c8c', bg: '#fafafa', icon: '—' };
        const time = r.punch_time || r.timestamp || r.event_time;
        return (
          <div key={r.id ?? i} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 6px', borderBottom: '1px solid #f1f5f9', borderLeft: `3px solid ${m.color}`, paddingLeft: 10 }}>
            <div style={{ width: 28, height: 28, borderRadius: 8, flexShrink: 0, background: m.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', color: m.color, fontSize: 12 }}>
              {m.icon}
            </div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 12, fontWeight: 600, color: '#1a1a2e' }}>{m.label}</div>
              <div style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                {r.device_alias || r.terminal_sn || r.device_name || 'Unknown reader'}
              </div>
            </div>
            {time && (
              <div style={{ textAlign: 'right', flexShrink: 0 }}>
                <div style={{ fontSize: 12, fontWeight: 600, color: '#374151' }}>{dayjs(time).format('HH:mm')}</div>
                <div style={{ fontSize: 10, color: '#94a3b8' }}>{dayjs(time).format('DD MMM')} · {dayjs(time).fromNow()}</div>
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ── Tab: Audit Trail ───────────────────────────────────────────────────────────
const AuditTrailTab = ({ personnelId }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['personnel-audit', personnelId],
    queryFn: () => apiService.get(`/api/v1/personnel/${personnelId}/audit-trail?limit=30`),
    enabled: !!personnelId,
    staleTime: 120_000,
  });

  const logs = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>;
  if (logs.length === 0) return <Empty description="No audit trail entries" image={Empty.PRESENTED_IMAGE_SIMPLE} />;

  return (
    <Table
      dataSource={logs}
      rowKey={r => r.id ?? Math.random()}
      size="small"
      pagination={{ pageSize: 10, size: 'small' }}
      columns={[
        { title: 'Action', dataIndex: 'action', key: 'action', width: 120, render: v => <Tag color="blue">{v}</Tag> },
        { title: 'Field / Detail', dataIndex: 'field_name', key: 'field', render: (v, r) => v || r.description || r.detail || '—' },
        { title: 'Old', dataIndex: 'old_value', key: 'old', width: 90, render: v => v ? <Text type="secondary" style={{ fontSize: 11 }}>{String(v).slice(0, 20)}</Text> : '—' },
        { title: 'New', dataIndex: 'new_value', key: 'new', width: 90, render: v => v ? <Text style={{ fontSize: 11 }}>{String(v).slice(0, 20)}</Text> : '—' },
        { title: 'By', dataIndex: 'user_email', key: 'user', width: 120, render: (v, r) => v || r.changed_by || '—' },
        { title: 'Time', dataIndex: 'created_at', key: 'time', width: 110,
          render: t => t ? <Tooltip title={dayjs(t).format('DD MMM YYYY HH:mm:ss')}><span style={{ fontSize: 11, color: '#94a3b8' }}>{dayjs(t).fromNow()}</span></Tooltip> : '—' },
      ]}
    />
  );
};

// ── Main EmployeeDrawer ────────────────────────────────────────────────────────
const EmployeeDrawer = ({ open, record: rec, onClose, onEdit, onRefresh, zoneMap = new Map() }) => {
  const { message } = App.useApp();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [statusChanging, setStatusChanging] = useState(false);

  const checkInMutation = useMutation({
    mutationFn: () => apiService.post(`/api/v1/personnel/${rec.id}/check-in`, {}),
    onSuccess: () => { message.success(`${rec.first_name} checked in`); queryClient.invalidateQueries(['personnel']); onRefresh?.(); },
    onError: (e) => message.error(e?.response?.data?.detail || 'Check-in failed'),
  });

  const checkOutMutation = useMutation({
    mutationFn: () => apiService.post(`/api/v1/personnel/${rec.id}/check-out`, {}),
    onSuccess: () => { message.success(`${rec.first_name} checked out`); queryClient.invalidateQueries(['personnel']); onRefresh?.(); },
    onError: (e) => message.error(e?.response?.data?.detail || 'Check-out failed'),
  });

  const statusMutation = useMutation({
    mutationFn: (newStatus) => apiService.post(`/api/v1/personnel/${rec.id}/status`, { status: newStatus }),
    onSuccess: () => { message.success('Status updated'); setStatusChanging(false); queryClient.invalidateQueries(['personnel']); onRefresh?.(); },
    onError: (e) => message.error(e?.response?.data?.detail || 'Status update failed'),
  });

  const deactivateMutation = useMutation({
    mutationFn: () => apiService.put(`/api/v1/personnel/${rec.id}/`, { status: 'INACTIVE' }),
    onSuccess: () => { message.success('Set to inactive'); queryClient.invalidateQueries(['personnel']); onClose(); onRefresh?.(); },
    onError: (e) => message.error(e?.response?.data?.detail || 'Deactivate failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: () => apiService.delete(`/api/v1/personnel/${rec.id}`),
    onSuccess: () => { message.success('Employee deleted'); queryClient.invalidateQueries(['personnel']); onClose(); onRefresh?.(); },
    onError: (e) => message.error(e?.response?.data?.detail || 'Delete failed'),
  });

  if (!rec) return null;

  const name = rec.full_name || `${rec.first_name || ''} ${rec.last_name || ''}`.trim();
  const ncCount = 0; // passed via prop or queried separately if needed

  const tabs = [
    {
      key: 'overview',
      label: <><SolutionOutlined /> Overview</>,
      children: <OverviewTab rec={rec} zoneMap={zoneMap} />,
    },
    {
      key: 'medical',
      label: <><MedicineBoxOutlined /> Medical</>,
      children: <MedicalTab rec={rec} />,
    },
    {
      key: 'certifications',
      label: <><FileProtectOutlined /> Certifications</>,
      children: activeTab === 'certifications' ? <CertificationsTab personnelId={rec.id} /> : null,
    },
    {
      key: 'fitness',
      label: <><CalendarOutlined /> Med Fitness</>,
      children: activeTab === 'fitness' ? <MedicalFitnessTab personnelId={rec.id} /> : null,
    },
    {
      key: 'status_history',
      label: <><HistoryOutlined /> Status Log</>,
      children: activeTab === 'status_history' ? <StatusHistoryTab personnelId={rec.id} /> : null,
    },
    {
      key: 'activity',
      label: <><ThunderboltOutlined /> Activity</>,
      children: activeTab === 'activity' ? <ActivityTab personnelId={rec.id} empCode={rec.emp_code} /> : null,
    },
    {
      key: 'audit',
      label: <><AuditOutlined /> Audit Trail</>,
      children: activeTab === 'audit' ? <AuditTrailTab personnelId={rec.id} /> : null,
    },
  ];

  return (
    <Drawer
      open={open}
      onClose={() => { setActiveTab('overview'); onClose(); }}
      width={780}
      styles={{ body: { padding: 0 } }}
      title={null}
      destroyOnHidden
      footer={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space size={6}>
            {/* Check-In / Check-Out */}
            {rec.is_onboard ? (
              <Popconfirm title={`Check out ${rec.first_name}?`} onConfirm={() => checkOutMutation.mutate()} okText="Check Out">
                <Button size="small" icon={<LogoutOutlined />} loading={checkOutMutation.isPending} style={{ color: '#1677ff', borderColor: '#91caff' }}>
                  Check Out
                </Button>
              </Popconfirm>
            ) : (
              <Popconfirm title={`Check in ${rec.first_name}?`} onConfirm={() => checkInMutation.mutate()} okText="Check In">
                <Button size="small" icon={<LoginOutlined />} type="primary" loading={checkInMutation.isPending}>
                  Check In
                </Button>
              </Popconfirm>
            )}

            {/* Quick Status Change */}
            <Select
              size="small"
              value={rec.status}
              style={{ width: 130 }}
              onChange={(v) => statusMutation.mutate(v)}
              loading={statusMutation.isPending}
            >
              {STATUS_OPTIONS.map(s => (
                <Option key={s} value={s}>
                  <span style={{ fontSize: 11 }}>{s.replace('_', ' ')}</span>
                </Option>
              ))}
            </Select>
          </Space>

          <Space size={6}>
            <Tooltip title="Open full profile page">
              <Button
                size="small"
                icon={<ExportOutlined />}
                onClick={() => { onClose(); navigate(`/personnel/${rec.id}`); }}
                style={{ color: '#7c3aed', borderColor: '#c4b5fd' }}
              >
                Full Profile
              </Button>
            </Tooltip>
            <Button icon={<EditOutlined />} size="small" onClick={() => { onClose(); onEdit(rec); }}>Edit</Button>
            <Popconfirm title="Set to inactive?" onConfirm={() => deactivateMutation.mutate()} okText="Deactivate">
              <Button size="small" icon={<StopOutlined />} style={{ color: '#d97706', borderColor: '#fcd34d' }} loading={deactivateMutation.isPending}>
                Deactivate
              </Button>
            </Popconfirm>
            <Popconfirm
              title="Permanently delete?"
              description="This cannot be undone."
              onConfirm={() => deleteMutation.mutate()}
              okText="Delete" okButtonProps={{ danger: true }}
            >
              <Button size="small" danger icon={<DeleteOutlined />} loading={deleteMutation.isPending}>Delete</Button>
            </Popconfirm>
          </Space>
        </div>
      }
    >
      {/* ── Hero header ──────────────────────────────────────────────────── */}
      <div style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', padding: '22px 24px 18px' }}>
        <div style={{ display: 'flex', gap: 16, alignItems: 'flex-start' }}>
          <div style={{ position: 'relative', flexShrink: 0 }}>
            <Avatar
              src={rec.photo_url || undefined}
              size={70}
              style={{ background: avatarColor(name), fontSize: 22, fontWeight: 700, border: '3px solid rgba(255,255,255,0.18)' }}
            >
              {initials(name)}
            </Avatar>
            {rec.is_onboard && (
              <span style={{ position: 'absolute', bottom: 2, right: 2, width: 13, height: 13, borderRadius: '50%', background: '#22c55e', border: '2px solid #1e293b' }} />
            )}
          </div>

          <div style={{ flex: 1, minWidth: 0 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <div style={{ fontSize: 19, fontWeight: 800, color: '#f8fafc', lineHeight: 1.2 }}>{name || '—'}</div>
              <Tooltip title="Open full profile">
                <button
                  type="button"
                  onClick={() => { onClose(); navigate(`/personnel/${rec.id}`); }}
                  style={{ background: 'rgba(255,255,255,0.1)', border: '1px solid rgba(255,255,255,0.2)', borderRadius: 6, color: '#c4b5fd', fontSize: 11, padding: '2px 8px', cursor: 'pointer' }}
                >
                  ↗ Profile
                </button>
              </Tooltip>
            </div>
            <div style={{ fontSize: 12, color: '#94a3b8', marginTop: 3 }}>
              <span style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.08)', padding: '1px 6px', borderRadius: 4 }}>{rec.emp_code}</span>
              {rec.company && <span style={{ marginLeft: 8 }}>· {rec.company}</span>}
            </div>
            <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 3 }}>
              {[rec.role || rec.position, rec.department].filter(Boolean).join(' · ')}
            </div>
            <div style={{ display: 'flex', gap: 6, marginTop: 10, flexWrap: 'wrap' }}>
              <StatusPill status={rec.status} />
              {rec.is_onboard && <span style={{ background: '#22c55e', color: '#fff', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>ON BOARD</span>}
              {rec.safety_critical && <span style={{ background: '#ef4444', color: '#fff', borderRadius: 20, padding: '2px 10px', fontSize: 11, fontWeight: 700 }}>⚠ SAFETY CRITICAL</span>}
              {rec.personnel_type && rec.personnel_type !== 'STAFF' && (
                <Tag color={TYPE_COLOR[rec.personnel_type]} style={{ margin: 0, borderRadius: 10 }}>{rec.personnel_type}</Tag>
              )}
            </div>
          </div>
        </div>

        {/* Quick stats strip */}
        <div style={{ display: 'flex', gap: 16, marginTop: 16, paddingTop: 14, borderTop: '1px solid rgba(255,255,255,0.07)' }}>
          {[
            { label: 'Compliance', value: `${rec.compliance_score ?? 0}%`, color: rec.compliance_score >= 90 ? '#22c55e' : rec.compliance_score >= 70 ? '#f59e0b' : '#ef4444' },
            { label: 'Blood Group', value: rec.blood_group || '—', color: '#f87171' },
            { label: 'Last Seen', value: rec.last_seen ? dayjs(rec.last_seen).fromNow() : '—', color: '#94a3b8' },
            { label: 'Since', value: rec.hire_date ? dayjs(rec.hire_date).format('MMM YYYY') : '—', color: '#94a3b8' },
            { label: 'Warehouse', value: rec.current_zone_id ? (zoneMap.get(rec.current_zone_id) || `#${rec.current_zone_id}`) : '—', color: '#7dd3fc' },
          ].map(({ label, value, color }) => (
            <div key={label} style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.05em' }}>{label}</div>
              <div style={{ fontSize: 13, fontWeight: 700, color, marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{value}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ── Tabs ────────────────────────────────────────────────────────── */}
      <div style={{ padding: '0 24px 24px' }}>
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={tabs}
          size="small"
          style={{ marginTop: 4 }}
        />
      </div>
    </Drawer>
  );
};

export default EmployeeDrawer;
