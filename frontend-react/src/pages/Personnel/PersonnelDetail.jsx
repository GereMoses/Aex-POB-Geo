/**
 * PersonnelDetail — full-page employee profile.
 * Route: /personnel/:id
 *
 * Sections (left sidebar navigation):
 *   Overview · Employment · Contact · Medical & Safety
 *   Certifications · Medical Fitness · Status History
 *   Biometrics · Documents · Audit Trail
 */
import React, { useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Card, Descriptions, Tag, Button, Space, Spin, Typography, Avatar,
  Row, Col, Divider, Timeline, Table, Badge, Tooltip, Progress,
  Alert, Modal, Form, Input, Select, DatePicker, Tabs, App,
  Popconfirm, List, Empty,
} from 'antd';
import {
  ArrowLeftOutlined, EditOutlined, LoginOutlined, LogoutOutlined,
  UserOutlined, FileOutlined, MailOutlined, PhoneOutlined, EnvironmentOutlined,
  MedicineBoxOutlined, SafetyOutlined, ScanOutlined, FileProtectOutlined,
  HistoryOutlined, AuditOutlined, ThunderboltOutlined, IdcardOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, CameraOutlined,
  StopOutlined, DeleteOutlined, BankOutlined, GlobalOutlined, CalendarOutlined,
  WarningOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';
import DocumentManager from '../../components/DocumentManager/DocumentManager';

dayjs.extend(relativeTime);

const { Title, Text } = Typography;
const { Option } = Select;

const STATUS_PILL = {
  ACTIVE:   { bg: '#f0fdf4', border: '#bbf7d0', text: '#15803d', dot: '#22c55e' },
  INACTIVE: { bg: '#fef2f2', border: '#fecaca', text: '#b91c1c', dot: '#ef4444' },
  ON_LEAVE: { bg: '#fffbeb', border: '#fed7aa', text: '#b45309', dot: '#f59e0b' },
  OFFSHORE: { bg: '#eff6ff', border: '#bfdbfe', text: '#1d4ed8', dot: '#3b82f6' },
  ONSHORE:  { bg: '#f0fdfa', border: '#99f6e4', text: '#0f766e', dot: '#14b8a6' },
  TRANSIT:  { bg: '#fdf4ff', border: '#e9d5ff', text: '#7e22ce', dot: '#a855f7' },
};
const STATUS_OPTIONS = ['ACTIVE', 'INACTIVE', 'ON_LEAVE', 'OFFSHORE', 'ONSHORE', 'TRANSIT'];
const BLOOD_GROUPS   = ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-'];
const AVATAR_PALETTE = ['#2563eb','#7c3aed','#db2777','#059669','#d97706','#dc2626','#0891b2','#65a30d'];
const avatarColor = (str) => AVATAR_PALETTE[(str || '').charCodeAt(0) % AVATAR_PALETTE.length];
const initials = (name) => (name || '').split(' ').filter(Boolean).slice(0, 2).map(w => w[0]).join('').toUpperCase() || '?';

const StatusPill = ({ status }) => {
  const s = (status || '').toUpperCase();
  const c = STATUS_PILL[s] || { bg: '#f4f4f5', border: '#e4e4e7', text: '#52525b', dot: '#a1a1aa' };
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 5, background: c.bg, border: `1px solid ${c.border}`, color: c.text, borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}>
      <span style={{ width: 7, height: 7, borderRadius: '50%', background: c.dot, flexShrink: 0 }} />
      {s.replace('_', ' ')}
    </span>
  );
};

// ── Section: Certifications ────────────────────────────────────────────────────
const CertificationsSection = ({ id }) => {
  const [addModal, setAddModal] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['detail-certs', id],
    queryFn: () => apiService.get(`/api/v1/personnel/${id}/certifications`),
    enabled: !!id, staleTime: 60000,
  });
  const add = useMutation({
    mutationFn: v => apiService.post(`/api/v1/personnel/${id}/certifications`, v),
    onSuccess: () => { message.success('Certification added'); setAddModal(false); form.resetFields(); qc.invalidateQueries(['detail-certs', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Failed'),
  });

  const certs = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);
  const expired = certs.filter(c => c.expiry_date && dayjs(c.expiry_date).isBefore(dayjs()));
  const expiringSoon = certs.filter(c => c.expiry_date && dayjs(c.expiry_date).diff(dayjs(), 'day') >= 0 && dayjs(c.expiry_date).diff(dayjs(), 'day') <= 30);

  return (
    <>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
        <div>
          {expired.length > 0 && <Tag color="red">{expired.length} expired</Tag>}
          {expiringSoon.length > 0 && <Tag color="orange">{expiringSoon.length} expiring soon</Tag>}
        </div>
        <Button type="primary" size="small" onClick={() => setAddModal(true)}>+ Add Certification</Button>
      </div>

      {isLoading ? <Spin /> : certs.length === 0 ? (
        <Empty description="No certifications on record" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Row gutter={[12, 12]}>
          {certs.map(cert => {
            const days = cert.expiry_date ? dayjs(cert.expiry_date).diff(dayjs(), 'day') : null;
            const status = days === null ? 'valid' : days < 0 ? 'expired' : days < 30 ? 'expiring' : 'valid';
            return (
              <Col key={cert.id} xs={24} sm={12} md={8}>
                <div style={{
                  background: status === 'expired' ? '#fff5f5' : status === 'expiring' ? '#fffbe6' : '#f6ffed',
                  border: `1px solid ${status === 'expired' ? '#fecaca' : status === 'expiring' ? '#ffe58f' : '#b7eb8f'}`,
                  borderRadius: 10, padding: '12px 14px',
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <FileProtectOutlined style={{ color: status === 'expired' ? '#dc2626' : status === 'expiring' ? '#d97706' : '#16a34a', fontSize: 16 }} />
                    <Text strong style={{ fontSize: 13 }}>{cert.cert_name || cert.certification_name}</Text>
                  </div>
                  {cert.issuing_body && <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>{cert.issuing_body}</div>}
                  {cert.cert_number && <div style={{ fontSize: 11, color: '#94a3b8', fontFamily: 'monospace' }}>#{cert.cert_number}</div>}
                  <div style={{ marginTop: 8, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    {cert.expiry_date ? (
                      <span style={{ fontSize: 11, fontWeight: 600, color: status === 'expired' ? '#dc2626' : status === 'expiring' ? '#d97706' : '#16a34a' }}>
                        {days < 0 ? `Expired ${Math.abs(days)}d ago` : days === 0 ? 'Expires today!' : days < 30 ? `Expires in ${days}d` : dayjs(cert.expiry_date).format('DD MMM YYYY')}
                      </span>
                    ) : <span style={{ fontSize: 11, color: '#94a3b8' }}>No expiry</span>}
                    {cert.issue_date && <span style={{ fontSize: 10, color: '#94a3b8' }}>{dayjs(cert.issue_date).format('DD MMM YYYY')}</span>}
                  </div>
                </div>
              </Col>
            );
          })}
        </Row>
      )}

      <Modal
        title="Add Certification"
        open={addModal}
        onOk={() => form.validateFields().then(v => add.mutate({ ...v, issue_date: v.issue_date?.format('YYYY-MM-DD'), expiry_date: v.expiry_date?.format('YYYY-MM-DD') }))}
        onCancel={() => { setAddModal(false); form.resetFields(); }}
        confirmLoading={add.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="cert_name" label="Certification Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. BOSIET, H2S Awareness, OPITO" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="issuing_body" label="Issuing Body"><Input placeholder="OPITO, NEBOSH…" /></Form.Item></Col>
            <Col span={12}><Form.Item name="cert_number" label="Certificate No."><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="issue_date" label="Issue Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><Form.Item name="expiry_date" label="Expiry Date"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </>
  );
};

// ── Section: Medical Fitness ───────────────────────────────────────────────────
const MedicalFitnessSection = ({ id }) => {
  const [addModal, setAddModal] = useState(false);
  const [form] = Form.useForm();
  const { message } = App.useApp();
  const qc = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['detail-fitness', id],
    queryFn: () => apiService.get(`/api/v1/personnel/${id}/medical-fitness`),
    enabled: !!id, staleTime: 60000,
  });
  const add = useMutation({
    mutationFn: v => apiService.post(`/api/v1/personnel/${id}/medical-fitness`, v),
    onSuccess: () => { message.success('Record added'); setAddModal(false); form.resetFields(); qc.invalidateQueries(['detail-fitness', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Failed'),
  });

  const records = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  return (
    <>
      <div style={{ textAlign: 'right', marginBottom: 10 }}>
        <Button type="primary" size="small" onClick={() => setAddModal(true)}>+ Add Record</Button>
      </div>
      {isLoading ? <Spin /> : records.length === 0 ? (
        <Empty description="No medical fitness records" image={Empty.PRESENTED_IMAGE_SIMPLE} />
      ) : (
        <Table
          dataSource={records} rowKey="id" size="small" pagination={{ pageSize: 8, size: 'small' }}
          columns={[
            { title: 'Examination', dataIndex: 'exam_type', key: 'type', render: v => v || 'Medical Fitness' },
            { title: 'Date', dataIndex: 'exam_date', key: 'date', render: d => d ? dayjs(d).format('DD MMM YYYY') : '—' },
            { title: 'Result', dataIndex: 'result', key: 'result', render: v => <Tag color={v === 'FIT' ? 'green' : v === 'UNFIT' ? 'red' : 'orange'}>{v || '—'}</Tag> },
            { title: 'Valid Until', dataIndex: 'valid_until', key: 'exp', render: d => {
              if (!d) return '—';
              const days = dayjs(d).diff(dayjs(), 'day');
              return <span style={{ fontWeight: 600, color: days < 0 ? '#dc2626' : days < 30 ? '#d97706' : '#16a34a' }}>{dayjs(d).format('DD MMM YYYY')}</span>;
            }},
            { title: 'Doctor', dataIndex: 'doctor_name', key: 'doc', render: v => v || '—' },
          ]}
        />
      )}
      <Modal
        title="Add Medical Fitness Record"
        open={addModal}
        onOk={() => form.validateFields().then(v => add.mutate({ ...v, exam_date: v.exam_date?.format('YYYY-MM-DD'), valid_until: v.valid_until?.format('YYYY-MM-DD') }))}
        onCancel={() => { setAddModal(false); form.resetFields(); }}
        confirmLoading={add.isPending}
      >
        <Form form={form} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="exam_type" label="Examination Type" rules={[{ required: true }]}><Input placeholder="Pre-employment, Annual, Offshore Medical…" /></Form.Item>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="exam_date" label="Date" rules={[{ required: true }]}><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={12}><Form.Item name="valid_until" label="Valid Until"><DatePicker style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="result" label="Result" initialValue="FIT">
                <Select><Option value="FIT">Fit</Option><Option value="FIT_WITH_RESTRICTIONS">Fit with Restrictions</Option><Option value="UNFIT">Unfit</Option><Option value="PENDING">Pending</Option></Select>
              </Form.Item>
            </Col>
            <Col span={12}><Form.Item name="doctor_name" label="Doctor"><Input /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>
    </>
  );
};

// ── Section: Status History ────────────────────────────────────────────────────
const StatusHistorySection = ({ id }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['detail-status-history', id],
    queryFn: () => apiService.get(`/api/v1/personnel/${id}/status-history?limit=40`),
    enabled: !!id, staleTime: 60000,
  });
  const history = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>;
  if (history.length === 0) return <Empty description="No status history" image={Empty.PRESENTED_IMAGE_SIMPLE} />;

  return (
    <Timeline
      mode="left"
      items={history.map(h => ({
        color: h.new_status === 'ACTIVE' ? 'green' : h.new_status === 'OFFSHORE' ? 'blue' : h.new_status === 'INACTIVE' ? 'red' : 'orange',
        label: <span style={{ fontSize: 11, color: '#94a3b8', whiteSpace: 'nowrap' }}>{dayjs(h.changed_at || h.created_at).format('DD MMM YYYY HH:mm')}</span>,
        children: (
          <div style={{ paddingBottom: 4 }}>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              {h.old_status && <><Tag style={{ fontSize: 11 }}>{h.old_status?.replace('_', ' ')}</Tag><span style={{ color: '#94a3b8' }}>→</span></>}
              <StatusPill status={h.new_status} />
            </div>
            {h.location && <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}><EnvironmentOutlined /> {h.location}</div>}
            {h.notes && <div style={{ fontSize: 12, color: '#64748b', marginTop: 3 }}>{h.notes}</div>}
            {h.changed_by && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>by {h.changed_by}</div>}
          </div>
        ),
      }))}
    />
  );
};

// ── Section: Audit Trail ───────────────────────────────────────────────────────
const AuditSection = ({ id }) => {
  const { data, isLoading } = useQuery({
    queryKey: ['detail-audit', id],
    queryFn: () => apiService.get(`/api/v1/personnel/${id}/audit-trail?limit=50`),
    enabled: !!id, staleTime: 120_000,
  });
  const logs = Array.isArray(data?.data) ? data.data : (Array.isArray(data) ? data : []);

  if (isLoading) return <div style={{ textAlign: 'center', padding: 32 }}><Spin /></div>;
  if (logs.length === 0) return <Empty description="No audit entries" image={Empty.PRESENTED_IMAGE_SIMPLE} />;

  return (
    <Table
      dataSource={logs}
      rowKey={r => r.id ?? Math.random()}
      size="small"
      pagination={{ pageSize: 15, size: 'small' }}
      columns={[
        { title: 'Action', dataIndex: 'action', key: 'action', width: 120, render: v => <Tag color="blue">{v}</Tag> },
        { title: 'Field', dataIndex: 'field_name', key: 'field', render: (v, r) => v || r.description || '—' },
        { title: 'Old Value', dataIndex: 'old_value', key: 'old', width: 110, render: v => v ? <Text type="secondary" style={{ fontSize: 11 }}>{String(v).slice(0, 24)}</Text> : '—' },
        { title: 'New Value', dataIndex: 'new_value', key: 'new', width: 110, render: v => v ? <Text style={{ fontSize: 11 }}>{String(v).slice(0, 24)}</Text> : '—' },
        { title: 'Changed By', dataIndex: 'user_email', key: 'user', width: 140, render: (v, r) => v || r.changed_by || '—' },
        { title: 'Time', dataIndex: 'created_at', key: 'time', width: 120, render: t => t ? <Tooltip title={dayjs(t).format('DD MMM YYYY HH:mm')}><span style={{ fontSize: 11, color: '#94a3b8' }}>{dayjs(t).fromNow()}</span></Tooltip> : '—' },
      ]}
    />
  );
};

// ── Main PersonnelDetail ───────────────────────────────────────────────────────
const PersonnelDetail = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { message } = App.useApp();
  const qc = useQueryClient();
  const photoInputRef = useRef(null);
  const [editModal, setEditModal] = useState(false);
  const [form] = Form.useForm();
  const [photoFile, setPhotoFile] = useState(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['personnel-detail', id],
    queryFn: () => apiService.get(`/api/v1/personnel/${id}`),
    enabled: !!id,
    staleTime: 60000,
  });

  const { data: zonesData } = useQuery({
    queryKey: ['zones'],
    queryFn: () => apiService.get('/api/v1/zones/'),
    staleTime: 300000,
  });
  const { data: deptsData } = useQuery({
    queryKey: ['departments'],
    queryFn: () => apiService.get('/api/v1/departments/'),
    staleTime: 300000,
  });

  const zoneList  = Array.isArray(zonesData) ? zonesData : (zonesData?.results || []);
  const deptList  = Array.isArray(deptsData) ? deptsData : (deptsData?.results || []);
  const zoneMap   = new Map(zoneList.map(z => [z.id, z.name || z.zone_name || `Warehouse ${z.id}`]));

  const checkInMutation = useMutation({
    mutationFn: () => apiService.post(`/api/v1/personnel/${id}/check-in`, {}),
    onSuccess: () => { message.success('Checked in'); qc.invalidateQueries(['personnel-detail', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Check-in failed'),
  });
  const checkOutMutation = useMutation({
    mutationFn: () => apiService.post(`/api/v1/personnel/${id}/check-out`, {}),
    onSuccess: () => { message.success('Checked out'); qc.invalidateQueries(['personnel-detail', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Check-out failed'),
  });
  const statusMutation = useMutation({
    mutationFn: (status) => apiService.post(`/api/v1/personnel/${id}/status`, { status }),
    onSuccess: () => { message.success('Status updated'); qc.invalidateQueries(['personnel-detail', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Failed'),
  });
  const saveMutation = useMutation({
    mutationFn: (payload) => apiService.put(`/api/v1/personnel/${id}/`, payload),
    onSuccess: () => {
      message.success('Profile updated');
      setEditModal(false);
      if (photoFile) {
        apiService.upload(`/api/v1/personnel/${id}/upload-photo`, photoFile)
          .then(() => { setPhotoFile(null); qc.invalidateQueries(['personnel-detail', id]); })
          .catch(() => message.warning('Profile saved, photo upload failed'));
      } else {
        qc.invalidateQueries(['personnel-detail', id]);
      }
    },
    onError: e => message.error(e?.response?.data?.detail || 'Save failed'),
  });
  const deactivateMutation = useMutation({
    mutationFn: () => apiService.put(`/api/v1/personnel/${id}/`, { status: 'INACTIVE' }),
    onSuccess: () => { message.success('Set to inactive'); qc.invalidateQueries(['personnel-detail', id]); },
    onError: e => message.error(e?.response?.data?.detail || 'Failed'),
  });

  const p = data?.data ?? data;

  if (isLoading) return <div style={{ textAlign: 'center', padding: 80 }}><Spin size="large" /></div>;
  if (error || !p) return (
    <div style={{ padding: 32 }}>
      <Alert type="error" message="Employee not found" description={`No personnel record found for ID: ${id}`} showIcon
        action={<Button onClick={() => navigate(-1)}>Go Back</Button>} />
    </div>
  );

  const name = p.full_name || `${p.first_name || ''} ${p.last_name || ''}`.trim();

  const openEdit = () => {
    form.setFieldsValue({
      first_name: p.first_name, last_name: p.last_name,
      email: p.email, phone: p.phone, address: p.address,
      company: p.company, dept_id: p.department_id, role: p.role, position: p.position,
      employment_type: p.employment_type || 'EMPLOYEE', personnel_type: p.personnel_type || 'STAFF',
      status: (p.status || 'ACTIVE').toUpperCase(), is_onboard: p.is_onboard || false,
      safety_critical: p.safety_critical || false, zone_id: p.current_zone_id,
      blood_group: p.blood_group, nationality: p.nationality,
      id_number: p.id_number, passport_number: p.passport_number,
      emergency_contact_name: p.emergency_contact_name, emergency_contact_phone: p.emergency_contact_phone,
      medical_conditions: p.medical_conditions,
    });
    setEditModal(true);
  };

  const handleSave = () => {
    form.validateFields().then(values => {
      const dept = deptList.find(d => d.id === values.dept_id);
      saveMutation.mutate({
        first_name: values.first_name, last_name: values.last_name,
        email: values.email || null, phone: values.phone || null, address: values.address || null,
        company: values.company || null, department_id: values.dept_id || null,
        department: dept ? (dept.name || dept.dept_name) : null,
        role: values.role || null, position: values.position || null,
        employment_type: values.employment_type || 'EMPLOYEE', personnel_type: values.personnel_type || 'STAFF',
        status: values.status || 'ACTIVE', is_onboard: values.is_onboard || false,
        safety_critical: values.safety_critical || false, current_zone_id: values.zone_id || null,
        blood_group: values.blood_group || null, nationality: values.nationality || null,
        id_number: values.id_number || null, passport_number: values.passport_number || null,
        emergency_contact_name: values.emergency_contact_name || null,
        emergency_contact_phone: values.emergency_contact_phone || null,
        medical_conditions: values.medical_conditions || null,
      });
    });
  };

  const tabItems = [
    {
      key: 'overview',
      label: <><UserOutlined /> Overview</>,
      children: (
        <div style={{ padding: '0 4px' }}>
          <Descriptions column={{ xs: 1, sm: 2 }} size="small" bordered>
            <Descriptions.Item label="Employee Code"><Tag style={{ fontFamily: 'monospace', fontWeight: 700 }}>{p.emp_code}</Tag></Descriptions.Item>
            <Descriptions.Item label="Badge / Card">{p.badge_id && p.badge_id !== p.emp_code ? <code>{p.badge_id}</code> : <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Hire Date">{p.hire_date ? dayjs(p.hire_date).format('DD MMM YYYY') : '—'}</Descriptions.Item>
            <Descriptions.Item label="Nationality">{p.nationality || '—'}</Descriptions.Item>
            <Descriptions.Item label="Employment Type">{p.employment_type || '—'}</Descriptions.Item>
            <Descriptions.Item label="Personnel Type"><Tag color={{ STAFF: 'blue', CONTRACTOR: 'orange', VISITOR: 'purple' }[p.personnel_type]}>{p.personnel_type || '—'}</Tag></Descriptions.Item>
          </Descriptions>

          <Divider orientation="left" style={{ fontSize: 12, margin: '16px 0 12px' }}><BankOutlined /> Employment</Divider>
          <Descriptions column={{ xs: 1, sm: 2 }} size="small" bordered>
            <Descriptions.Item label="Company" span={2}>{p.company || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Department">{p.department || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Role">{p.role || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Position">{p.position || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Current Warehouse">{p.current_zone_id ? (zoneMap.get(p.current_zone_id) || `Warehouse #${p.current_zone_id}`) : <Text type="secondary">—</Text>}</Descriptions.Item>
          </Descriptions>

          <Divider orientation="left" style={{ fontSize: 12, margin: '16px 0 12px' }}><GlobalOutlined /> Contact</Divider>
          <Descriptions column={1} size="small" bordered>
            <Descriptions.Item label={<><MailOutlined /> Email</>}>{p.email || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label={<><PhoneOutlined /> Phone</>}>{p.phone || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label={<><EnvironmentOutlined /> Address</>}>{p.address || <Text type="secondary">—</Text>}</Descriptions.Item>
          </Descriptions>
        </div>
      ),
    },
    {
      key: 'medical',
      label: <><MedicineBoxOutlined /> Medical</>,
      children: (
        <div style={{ padding: '0 4px' }}>
          <Descriptions column={{ xs: 1, sm: 2 }} size="small" bordered>
            <Descriptions.Item label="Blood Group">
              {p.blood_group ? <Tag color="red" style={{ fontWeight: 700 }}>{p.blood_group}</Tag> : <Text type="secondary">—</Text>}
            </Descriptions.Item>
            <Descriptions.Item label="Safety Critical">
              {p.safety_critical ? <Tag color="red" icon={<SafetyOutlined />}>YES</Tag> : <Tag>No</Tag>}
            </Descriptions.Item>
            <Descriptions.Item label="National ID">{p.id_number || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Passport">{p.passport_number || <Text type="secondary">—</Text>}</Descriptions.Item>
            <Descriptions.Item label="Compliance Score">
              <Progress percent={p.compliance_score ?? 0} size="small" style={{ width: 120, display: 'inline-flex' }}
                status={p.compliance_score >= 90 ? 'success' : p.compliance_score >= 70 ? 'normal' : 'exception'} />
            </Descriptions.Item>
            <Descriptions.Item label="Medical Fitness">
              {p.medical_fitness_date ? dayjs(p.medical_fitness_date).format('DD MMM YYYY') : <Text type="secondary">Not recorded</Text>}
            </Descriptions.Item>
          </Descriptions>

          {(p.emergency_contact_name || p.emergency_contact_phone) && (
            <>
              <Divider orientation="left" style={{ fontSize: 12, margin: '16px 0 12px' }}>Emergency Contact</Divider>
              <Descriptions column={2} size="small" bordered>
                <Descriptions.Item label="Name">{p.emergency_contact_name || '—'}</Descriptions.Item>
                <Descriptions.Item label="Phone">{p.emergency_contact_phone || '—'}</Descriptions.Item>
              </Descriptions>
            </>
          )}

          {p.medical_conditions && (
            <>
              <Divider orientation="left" style={{ fontSize: 12, margin: '16px 0 12px' }}>Medical Conditions</Divider>
              <Alert type="warning" showIcon icon={<ExclamationCircleOutlined />} message={p.medical_conditions} style={{ borderRadius: 8 }} />
            </>
          )}
        </div>
      ),
    },
    {
      key: 'certifications',
      label: <><FileProtectOutlined /> Certifications</>,
      children: <CertificationsSection id={id} />,
    },
    {
      key: 'fitness',
      label: <><CalendarOutlined /> Med Fitness</>,
      children: <MedicalFitnessSection id={id} />,
    },
    {
      key: 'status_history',
      label: <><HistoryOutlined /> Status Log</>,
      children: <StatusHistorySection id={id} />,
    },
    {
      key: 'documents',
      label: <><FileOutlined /> Documents</>,
      children: <App><DocumentManager personnelId={Number(id)} /></App>,
    },
    {
      key: 'audit',
      label: <><AuditOutlined /> Audit Trail</>,
      children: <AuditSection id={id} />,
    },
  ];

  return (
    <div style={{ background: '#f8fafc', minHeight: '100vh' }}>
      {/* ── Profile hero ───────────────────────────────────────────────────── */}
      <div style={{ background: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)', padding: '28px 32px 0' }}>
        {/* Back + actions */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
          <Button icon={<ArrowLeftOutlined />} onClick={() => navigate(-1)} ghost size="small">
            Back to Directory
          </Button>
          <Space size={6}>
            {p.is_onboard ? (
              <Popconfirm title={`Check out ${p.first_name}?`} onConfirm={() => checkOutMutation.mutate()} okText="Check Out">
                <Button size="small" icon={<LogoutOutlined />} ghost loading={checkOutMutation.isPending}>Check Out</Button>
              </Popconfirm>
            ) : (
              <Popconfirm title={`Check in ${p.first_name}?`} onConfirm={() => checkInMutation.mutate()} okText="Check In">
                <Button size="small" icon={<LoginOutlined />} type="primary" loading={checkInMutation.isPending}>Check In</Button>
              </Popconfirm>
            )}
            <Select size="small" value={p.status} style={{ width: 130 }} onChange={v => statusMutation.mutate(v)} loading={statusMutation.isPending}>
              {STATUS_OPTIONS.map(s => <Option key={s} value={s}><span style={{ fontSize: 11 }}>{s.replace('_', ' ')}</span></Option>)}
            </Select>
            <Button size="small" icon={<EditOutlined />} onClick={openEdit} ghost>Edit Profile</Button>
            <Popconfirm title="Set to inactive?" onConfirm={() => deactivateMutation.mutate()} okText="Deactivate">
              <Button size="small" icon={<StopOutlined />} ghost style={{ color: '#fbbf24', borderColor: '#fbbf24' }} loading={deactivateMutation.isPending}>Deactivate</Button>
            </Popconfirm>
          </Space>
        </div>

        {/* Profile card */}
        <div style={{ display: 'flex', gap: 20, alignItems: 'flex-end' }}>
          {/* Avatar + photo upload */}
          <div style={{ position: 'relative', flexShrink: 0, marginBottom: -20 }}>
            <Avatar
              src={p.photo_url || undefined}
              size={96}
              style={{ background: avatarColor(name), fontSize: 28, fontWeight: 800, border: '4px solid rgba(255,255,255,0.15)', boxShadow: '0 4px 20px rgba(0,0,0,0.3)' }}
            >
              {initials(name)}
            </Avatar>
            <button
              type="button"
              title="Change photo"
              onClick={() => photoInputRef.current?.click()}
              style={{
                position: 'absolute', bottom: 0, right: 0, width: 26, height: 26,
                borderRadius: '50%', background: '#1677ff', border: '2px solid #0f172a',
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                cursor: 'pointer', color: '#fff', fontSize: 11,
              }}
            >
              <CameraOutlined />
            </button>
            <input ref={photoInputRef} type="file" accept=".jpg,.jpeg,.png,.gif,.webp" style={{ display: 'none' }}
              onChange={e => {
                const f = e.target.files?.[0];
                if (f) {
                  setPhotoFile(f);
                  apiService.upload(`/api/v1/personnel/${id}/upload-photo`, f)
                    .then(() => { message.success('Photo updated'); qc.invalidateQueries(['personnel-detail', id]); })
                    .catch(() => message.error('Photo upload failed'));
                }
              }}
            />
            {p.is_onboard && (
              <span style={{ position: 'absolute', top: 4, right: 4, width: 14, height: 14, borderRadius: '50%', background: '#22c55e', border: '2px solid #0f172a' }} />
            )}
          </div>

          <div style={{ flex: 1, minWidth: 0, paddingBottom: 20 }}>
            <Title level={3} style={{ color: '#f8fafc', margin: 0, lineHeight: 1.2 }}>{name}</Title>
            <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 4 }}>
              <span style={{ fontFamily: 'monospace', background: 'rgba(255,255,255,0.08)', padding: '2px 8px', borderRadius: 5 }}>{p.emp_code}</span>
              {p.company && <span style={{ marginLeft: 10 }}>· {p.company}</span>}
            </div>
            <div style={{ color: '#cbd5e1', fontSize: 13, marginTop: 4 }}>
              {[p.role || p.position, p.department].filter(Boolean).join(' · ')}
            </div>
            <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap', alignItems: 'center' }}>
              <StatusPill status={p.status} />
              {p.is_onboard && <span style={{ background: '#22c55e', color: '#fff', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 700 }}>ON BOARD</span>}
              {p.safety_critical && <span style={{ background: '#ef4444', color: '#fff', borderRadius: 20, padding: '3px 12px', fontSize: 12, fontWeight: 700 }}>⚠ SAFETY CRITICAL</span>}
            </div>
          </div>

          {/* Quick stats */}
          <div style={{ display: 'flex', gap: 20, paddingBottom: 20, flexShrink: 0 }}>
            {[
              { label: 'Compliance', value: `${p.compliance_score ?? 0}%`, color: p.compliance_score >= 90 ? '#22c55e' : p.compliance_score >= 70 ? '#f59e0b' : '#ef4444' },
              { label: 'Blood', value: p.blood_group || '—', color: '#f87171' },
              { label: 'Last Seen', value: p.last_seen ? dayjs(p.last_seen).fromNow() : '—', color: '#94a3b8' },
              { label: 'Warehouse', value: p.current_zone_id ? (zoneMap.get(p.current_zone_id) || `#${p.current_zone_id}`) : '—', color: '#7dd3fc' },
            ].map(({ label, value, color }) => (
              <div key={label} style={{ textAlign: 'center' }}>
                <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', fontWeight: 600, letterSpacing: '0.06em' }}>{label}</div>
                <div style={{ fontSize: 16, fontWeight: 800, color, marginTop: 2 }}>{value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* ── Tabs ─────────────────────────────────────────────────────────────── */}
      <div style={{ padding: '24px 32px' }}>
        <Card bodyStyle={{ padding: 0 }} style={{ borderRadius: 12, overflow: 'hidden' }}>
          <Tabs
            defaultActiveKey="overview"
            items={tabItems}
            tabBarStyle={{ padding: '0 20px', margin: 0, background: '#fafafa', borderBottom: '1px solid #f0f0f0' }}
            style={{ minHeight: 400 }}
            tabBarGutter={4}
          />
        </Card>
      </div>

      {/* ── Edit Modal ────────────────────────────────────────────────────────── */}
      <Modal
        title={<><EditOutlined /> Edit Profile — {name}</>}
        open={editModal}
        onOk={handleSave}
        onCancel={() => setEditModal(false)}
        confirmLoading={saveMutation.isPending}
        width={780}
        okText="Save Changes"
      >
        <Form form={form} layout="vertical" size="small" style={{ marginTop: 12 }}>
          <Divider orientation="left" style={{ fontSize: 12 }}>Personal</Divider>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="first_name" label="First Name" rules={[{ required: true }]}><Input /></Form.Item></Col>
            <Col span={8}><Form.Item name="last_name" label="Last Name"><Input /></Form.Item></Col>
            <Col span={8}><Form.Item name="nationality" label="Nationality"><Input /></Form.Item></Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: 12 }}>Employment</Divider>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="company" label="Company"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="dept_id" label="Department"><Select allowClear showSearch optionFilterProp="children">{deptList.map(d => <Option key={d.id} value={d.id}>{d.name || d.dept_name}</Option>)}</Select></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={8}><Form.Item name="role" label="Role"><Input /></Form.Item></Col>
            <Col span={8}><Form.Item name="position" label="Position"><Input /></Form.Item></Col>
            <Col span={8}><Form.Item name="employment_type" label="Employment Type"><Select><Option value="EMPLOYEE">Employee</Option><Option value="CONTRACTOR">Contractor</Option><Option value="SUBCONTRACTOR">Subcontractor</Option></Select></Form.Item></Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: 12 }}>Status & Warehouse</Divider>
          <Row gutter={12}>
            <Col span={6}><Form.Item name="personnel_type" label="Personnel Type"><Select><Option value="STAFF">Staff</Option><Option value="CONTRACTOR">Contractor</Option><Option value="VISITOR">Visitor</Option></Select></Form.Item></Col>
            <Col span={6}><Form.Item name="status" label="Status"><Select>{STATUS_OPTIONS.map(s => <Option key={s} value={s}>{s.replace('_', ' ')}</Option>)}</Select></Form.Item></Col>
            <Col span={8}><Form.Item name="zone_id" label="Warehouse"><Select allowClear showSearch optionFilterProp="children">{zoneList.map(z => <Option key={z.id} value={z.id}>{z.name}</Option>)}</Select></Form.Item></Col>
            <Col span={4}><Form.Item name="safety_critical" label="Safety Critical" valuePropName="checked"><input type="checkbox" /></Form.Item></Col>
          </Row>

          <Divider orientation="left" style={{ fontSize: 12 }}>Contact</Divider>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="email" label="Email" rules={[{ type: 'email' }]}><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="phone" label="Phone"><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="address" label="Address"><Input /></Form.Item>

          <Divider orientation="left" style={{ fontSize: 12 }}>Medical & Identity</Divider>
          <Row gutter={12}>
            <Col span={6}><Form.Item name="blood_group" label="Blood Group"><Select allowClear>{BLOOD_GROUPS.map(b => <Option key={b} value={b}>{b}</Option>)}</Select></Form.Item></Col>
            <Col span={9}><Form.Item name="id_number" label="National ID"><Input /></Form.Item></Col>
            <Col span={9}><Form.Item name="passport_number" label="Passport"><Input /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="emergency_contact_name" label="Emergency Contact Name"><Input /></Form.Item></Col>
            <Col span={12}><Form.Item name="emergency_contact_phone" label="Emergency Contact Phone"><Input /></Form.Item></Col>
          </Row>
          <Form.Item name="medical_conditions" label="Medical Conditions">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default PersonnelDetail;
