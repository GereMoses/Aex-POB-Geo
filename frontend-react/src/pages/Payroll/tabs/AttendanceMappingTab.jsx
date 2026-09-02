import React, { useState, useEffect } from 'react';
import {
  Table, Button, Input, InputNumber, Space, App,
  Tooltip, Alert, Typography, Modal, Form, Select, Row, Col,
} from 'antd';
import {
  EditOutlined, SaveOutlined, CloseOutlined, PlusOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { apiCall } from '../payrollApi';

const { Text } = Typography;
const { Option } = Select;

const FIELD_DESCRIPTIONS = {
  work_time:    'Total work minutes recorded in attendance system',
  ot_minutes:   'Overtime minutes beyond standard shift',
  late_minutes: 'Minutes arrived late (used for Late Deduction)',
  leave_days:   'Approved leave days in the period',
  absent_days:  'Absent days without approved leave',
  work_days:    'Total scheduled work days in period',
  present_days: 'Days employee was actually present',
  zone_hours:   'Hours worked on site at a warehouse',
  night_hours:  'Hours worked between 22:00 and 06:00',
  hazard_days:  'Days worked at a hazard-rated warehouse',
};

const POB_FIELDS = new Set(['zone_hours', 'night_hours', 'hazard_days']);

const CodePill = ({ value, variant = 'blue' }) => {
  const variants = {
    blue:   { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    orange: { color: '#c2410c', bg: '#ffedd5', border: '#fed7aa' },
    gray:   { color: '#475569', bg: '#f1f5f9', border: '#e2e8f0' },
  };
  const cfg = variants[variant] || variants.blue;
  return (
    <code style={{
      display: 'inline-block', padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600,
      fontFamily: 'monospace', color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`,
    }}>
      {value}
    </code>
  );
};

const UnitPill = ({ value }) => (
  <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#0891b2', background: '#ecfeff', border: '1px solid #a5f3fc' }}>
    {value || '—'}
  </span>
);

const AttendanceMappingTab = () => {
  const { message } = App.useApp();
  const [mappings, setMappings] = useState([]);
  const [loading, setLoading] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [editValues, setEditValues] = useState({});
  const [saving, setSaving] = useState(false);
  const [addModal, setAddModal] = useState(false);
  const [addForm] = Form.useForm();

  useEffect(() => { fetchMappings(); }, []);

  const fetchMappings = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/v1/payroll/attendance-mapping/');
      setMappings(Array.isArray(data) ? data : []);
    } catch (e) {
      message.error('Failed to load attendance mappings: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const saveEdit = async () => {
    setSaving(true);
    try {
      await apiCall('/api/v1/payroll/attendance-mapping/', { method: 'PUT', body: JSON.stringify(editValues) });
      message.success('Mapping updated');
      setEditingId(null);
      await fetchMappings();
    } catch (e) {
      message.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  const handleAddMapping = async () => {
    try {
      const values = await addForm.validateFields();
      setSaving(true);
      await apiCall('/api/v1/payroll/attendance-mapping/', { method: 'PUT', body: JSON.stringify(values) });
      message.success('Mapping added');
      setAddModal(false);
      addForm.resetFields();
      await fetchMappings();
    } catch (e) {
      if (e.errorFields) return;
      message.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  const columns = [
    {
      title: 'Attendance Field', dataIndex: 'attendance_field', key: 'field', width: 200,
      render: v => (
        <Space>
          <CodePill value={v} variant={POB_FIELDS.has(v) ? 'orange' : 'blue'} />
          {FIELD_DESCRIPTIONS[v] && (
            <Tooltip title={FIELD_DESCRIPTIONS[v]}><InfoCircleOutlined style={{ color: '#94a3b8', fontSize: 13 }} /></Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Maps To (Payroll Item)', dataIndex: 'payroll_item_name', key: 'item', width: 200,
      render: (v, record) =>
        editingId === record.id ? (
          <Input value={editValues.payroll_item_name} onChange={e => setEditValues(prev => ({ ...prev, payroll_item_name: e.target.value }))} size="small" style={{ width: 160 }} />
        ) : (
          <Text strong>{v || '—'}</Text>
        ),
    },
    {
      title: 'Rate (₦ per unit)', dataIndex: 'rate', key: 'rate', width: 150,
      render: (v, record) =>
        editingId === record.id ? (
          <InputNumber value={editValues.rate} onChange={val => setEditValues(prev => ({ ...prev, rate: val }))} min={0} size="small" style={{ width: 110 }} />
        ) : (
          <Text>{v != null ? <span style={{ fontWeight: 600, color: '#15803d' }}>₦{Number(v).toLocaleString()}</span> : '—'}</Text>
        ),
    },
    {
      title: 'Unit', dataIndex: 'unit', key: 'unit', width: 110,
      render: (v, record) =>
        editingId === record.id ? (
          <Select value={editValues.unit || 'minutes'} onChange={val => setEditValues(prev => ({ ...prev, unit: val }))} size="small" style={{ width: 100 }}>
            <Option value="minutes">minutes</Option>
            <Option value="hours">hours</Option>
            <Option value="days">days</Option>
          </Select>
        ) : (
          <UnitPill value={v} />
        ),
    },
    {
      title: 'Description', dataIndex: 'description', key: 'desc',
      render: (v, record) =>
        editingId === record.id ? (
          <Input value={editValues.description} onChange={e => setEditValues(prev => ({ ...prev, description: e.target.value }))} size="small" placeholder="Optional note" />
        ) : (
          <Text type="secondary" style={{ fontSize: 12 }}>{v || FIELD_DESCRIPTIONS[record.attendance_field] || '—'}</Text>
        ),
    },
    {
      title: 'Actions', key: 'actions', width: 110,
      render: (_, record) =>
        editingId === record.id ? (
          <Space size={4}>
            <Button size="small" type="primary" icon={<SaveOutlined />} onClick={saveEdit} loading={saving}>Save</Button>
            <Button size="small" icon={<CloseOutlined />} onClick={() => { setEditingId(null); setEditValues({}); }} />
          </Space>
        ) : (
          <Button size="small" icon={<EditOutlined />} onClick={() => { setEditingId(record.id); setEditValues({ ...record }); }}>Edit</Button>
        ),
    },
  ];

  return (
    <div>
      <Alert
        type="info"
        showIcon
        style={{ marginBottom: 16 }}
        message="Attendance Field Mapping"
        description={
          <span>
            These mappings define how raw attendance data (from BioTime) flows into payroll calculations.
            The <b>Rate</b> is multiplied by the field value to produce a payroll item value when using{' '}
            <b>Attendance</b> calc type on a pay item.
          </span>
        }
      />

      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden', marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
          <Text strong style={{ fontSize: 14 }}>Field Mappings</Text>
          <Button type="primary" size="small" icon={<PlusOutlined />} onClick={() => { addForm.resetFields(); setAddModal(true); }}>
            Add Mapping
          </Button>
        </div>
        <Table
          dataSource={mappings}
          rowKey="id"
          loading={loading}
          columns={columns}
          size="small"
          pagination={false}
          bordered={false}
        />
      </div>

      <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0', borderTop: '3px solid #c2410c' }}>
          <Text strong style={{ fontSize: 14, color: '#c2410c' }}>POB-Specific Fields</Text>
        </div>
        <Table
          size="small"
          pagination={false}
          dataSource={[
            { key: 'zone_hours',  field: 'zone_hours',  desc: 'Hours on site at a warehouse',     used_for: 'Warehouse Allowance calculations' },
            { key: 'night_hours', field: 'night_hours', desc: 'Night shift hours (22:00–06:00)',             used_for: 'Night differential pay'      },
            { key: 'hazard_days', field: 'hazard_days', desc: 'Days at a hazard-rated warehouse',      used_for: 'Hazard premium'              },
          ]}
          columns={[
            { title: 'Field', dataIndex: 'field', render: v => <CodePill value={v} variant="orange" /> },
            { title: 'Description', dataIndex: 'desc' },
            { title: 'Used For', dataIndex: 'used_for', render: v => <Text type="secondary">{v}</Text> },
          ]}
        />
      </div>

      <Modal
        title="Add Attendance Mapping"
        open={addModal}
        onOk={handleAddMapping}
        onCancel={() => setAddModal(false)}
        confirmLoading={saving}
        width={480}
      >
        <Form form={addForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item name="attendance_field" label="Attendance Field" rules={[{ required: true }]}>
            <Select placeholder="Select BioTime field">
              {Object.keys(FIELD_DESCRIPTIONS).map(f => (
                <Option key={f} value={f}>{f} — {FIELD_DESCRIPTIONS[f]}</Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="payroll_item_name" label="Payroll Item Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Overtime Pay, Late Deduction" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="rate" label="Rate (₦ per unit)">
                <InputNumber min={0} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="unit" label="Unit" initialValue="hours">
                <Select>
                  <Option value="minutes">Minutes</Option>
                  <Option value="hours">Hours</Option>
                  <Option value="days">Days</Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default AttendanceMappingTab;
