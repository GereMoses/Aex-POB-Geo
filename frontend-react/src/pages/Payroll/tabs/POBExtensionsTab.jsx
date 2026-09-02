import React, { useState, useEffect, useCallback } from 'react';
import {
  Row, Col, Table, Button, Space, Modal, Form, Input,
  InputNumber, Switch, Select, App, Alert, Typography, Tabs, Divider, Tooltip,
} from 'antd';
import {
  PlusOutlined, EditOutlined, FireOutlined,
  EnvironmentOutlined, TeamOutlined, DollarOutlined, SafetyOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { apiCall, fmt } from '../payrollApi';

const { Option } = Select;
const { Text } = Typography;

const RATE_TYPE_CFG = {
  0: { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe', label: 'Hourly' },
  1: { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', label: 'Daily'  },
  2: { color: '#7c3aed', bg: '#ede9fe', border: '#ddd6fe', label: 'Fixed'  },
};

const MultPill = ({ value, color }) => value ? (
  <span style={{ display: 'inline-block', padding: '2px 7px', borderRadius: 999, fontSize: 11, fontWeight: 700, color, background: `${color}15`, border: `1px solid ${color}40` }}>×{value}</span>
) : <Text type="secondary">—</Text>;

const StatusPill = ({ active }) => active
  ? <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#16a34a', background: '#f0fdf4', border: '1px solid #bbf7d0' }}>Active</span>
  : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#94a3b8', background: '#f8fafc', border: '1px solid #e2e8f0' }}>Off</span>;

const StatCard = ({ label, value, color, icon, sub }) => (
  <div style={{ flex: 1, background: '#fff', borderRadius: 8, padding: '14px 16px', borderTop: `3px solid ${color}`, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
      <span style={{ fontSize: 12, color: '#64748b' }}>{label}</span>
      {icon && <span style={{ color, fontSize: 15, background: `${color}18`, borderRadius: 6, padding: '3px 6px', display: 'flex' }}>{icon}</span>}
    </div>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
    {sub && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{sub}</div>}
  </div>
);

const POBExtensionsTab = ({ structures }) => {
  const { message } = App.useApp();
  const [activeSection, setActiveSection] = useState('zone');
  const [zones, setZones] = useState([]);
  const [loadingZones, setLoadingZones] = useState(false);
  const [zoneModal, setZoneModal] = useState({ open: false, record: null });
  const [zoneForm] = Form.useForm();
  const [rates, setRates] = useState([]);
  const [loadingRates, setLoadingRates] = useState(false);
  const [rateModal, setRateModal] = useState({ open: false, record: null });
  const [rateForm] = Form.useForm();
  const [saving, setSaving] = useState(false);

  const fetchZones = useCallback(async () => {
    setLoadingZones(true);
    try {
      const data = await apiCall('/api/v1/payroll/zone-allowances/');
      setZones(Array.isArray(data) ? data : []);
    } catch (e) { message.error(e.message); } finally { setLoadingZones(false); }
  }, []);

  const fetchRates = useCallback(async () => {
    setLoadingRates(true);
    try {
      const data = await apiCall('/api/v1/payroll/contractor-rates/');
      setRates(Array.isArray(data) ? data : []);
    } catch (e) { message.error(e.message); } finally { setLoadingRates(false); }
  }, []);

  useEffect(() => { fetchZones(); fetchRates(); }, [fetchZones, fetchRates]);

  const saveZone = async () => {
    try {
      const values = await zoneForm.validateFields();
      setSaving(true);
      const { record } = zoneModal;
      if (record) {
        await apiCall(`/api/v1/payroll/zone-allowances/${record.id}`, { method: 'PUT', body: JSON.stringify(values) });
        message.success('Warehouse allowance updated');
      } else {
        await apiCall('/api/v1/payroll/zone-allowances/', { method: 'POST', body: JSON.stringify(values) });
        message.success('Warehouse allowance created');
      }
      setZoneModal({ open: false, record: null });
      await fetchZones();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const saveRate = async () => {
    try {
      const values = await rateForm.validateFields();
      setSaving(true);
      const { record } = rateModal;
      if (record) {
        await apiCall(`/api/v1/payroll/contractor-rates/${record.id}`, { method: 'PUT', body: JSON.stringify(values) });
        message.success('Rate updated');
      } else {
        await apiCall('/api/v1/payroll/contractor-rates/', { method: 'POST', body: JSON.stringify(values) });
        message.success('Rate created');
      }
      setRateModal({ open: false, record: null });
      await fetchRates();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const hazardZones = zones.filter(z => z.is_hazard);
  const activeRates = rates.filter(r => r.is_active);

  const zoneCols = [
    {
      title: 'Structure', dataIndex: 'structure_id', key: 'struct', width: 160,
      render: v => {
        const s = structures.find(s => s.id === v);
        return s
          ? <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#2563eb', background: '#eff6ff', border: '1px solid #bfdbfe' }}>{s.structure_name}</span>
          : <Text type="secondary">ID: {v}</Text>;
      },
    },
    {
      title: 'Warehouse / Area', key: 'area',
      render: (_, r) => (
        <Space>
          {r.is_hazard && <FireOutlined style={{ color: '#dc2626' }} />}
          <Text strong>{r.area_name || `Area ${r.area_id}`}</Text>
          <Text type="secondary" style={{ fontSize: 11 }}>ID: {r.area_id}</Text>
        </Space>
      ),
    },
    {
      title: 'Rate Type', dataIndex: 'allowance_type', key: 'type', width: 100,
      render: v => {
        const cfg = RATE_TYPE_CFG[v] || RATE_TYPE_CFG[1];
        return <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>{cfg.label}</span>;
      },
    },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', align: 'right', width: 120, render: v => <Text strong style={{ color: '#16a34a' }}>{fmt(v)}</Text> },
    {
      title: 'Hazard Premium', key: 'hazard', width: 140,
      render: (_, r) => r.is_hazard
        ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca' }}><FireOutlined />+{r.hazard_rate}%</span>
        : <Text type="secondary">—</Text>,
    },
    { title: 'Effective', dataIndex: 'effective_date', key: 'eff', width: 110, render: d => d ? new Date(d).toLocaleDateString() : <Text type="secondary">Always</Text> },
    { title: 'Status', dataIndex: 'is_active', key: 'active', width: 80, render: v => <StatusPill active={v} /> },
    {
      title: '', key: 'actions', width: 60,
      render: (_, record) => (
        <Button size="small" icon={<EditOutlined />} onClick={() => { zoneForm.setFieldsValue({ ...record, allowance_type: record.allowance_type ?? 1 }); setZoneModal({ open: true, record }); }} />
      ),
    },
  ];

  const rateCols = [
    { title: 'Vendor', dataIndex: 'vendor_name', key: 'vendor', render: (v, r) => <Text strong>{v || `Vendor ${r.vendor_id}`}</Text> },
    {
      title: 'Position', dataIndex: 'position_name', key: 'pos',
      render: v => v
        ? <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#7c3aed', background: '#ede9fe', border: '1px solid #ddd6fe' }}>{v}</span>
        : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#94a3b8', background: '#f8fafc', border: '1px solid #e2e8f0' }}>All Positions</span>,
    },
    { title: 'Hourly', dataIndex: 'hourly_rate', key: 'hr', align: 'right', width: 100, render: v => v ? fmt(v) : <Text type="secondary">—</Text> },
    { title: 'Daily', dataIndex: 'daily_rate', key: 'dr', align: 'right', width: 100, render: v => v ? <Text strong>{fmt(v)}</Text> : <Text type="secondary">—</Text> },
    { title: 'Monthly', dataIndex: 'monthly_rate', key: 'mr', align: 'right', width: 120, render: v => v ? <Text strong style={{ color: '#2563eb' }}>{fmt(v)}</Text> : <Text type="secondary">—</Text> },
    { title: 'OT Mult.', dataIndex: 'ot_multiplier', key: 'ot', align: 'center', width: 90, render: v => <MultPill value={v} color="#d97706" /> },
    { title: 'Night Mult.', dataIndex: 'night_multiplier', key: 'night', align: 'center', width: 100, render: v => <MultPill value={v} color="#7c3aed" /> },
    { title: 'Holiday Mult.', dataIndex: 'holiday_multiplier', key: 'hol', align: 'center', width: 110, render: v => <MultPill value={v} color="#dc2626" /> },
    { title: 'Status', dataIndex: 'is_active', key: 'active', width: 80, render: v => <StatusPill active={v} /> },
    {
      title: '', key: 'actions', width: 60,
      render: (_, record) => <Button size="small" icon={<EditOutlined />} onClick={() => { rateForm.setFieldsValue(record); setRateModal({ open: true, record }); }} />,
    },
  ];

  return (
    <div>
      <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
        <StatCard label="Warehouse Rules" value={zones.length} color="#d97706" icon={<EnvironmentOutlined />} sub={`${hazardZones.length} hazard`} />
        <StatCard label="Hazard Warehouses" value={hazardZones.length} color="#dc2626" icon={<FireOutlined />} />
        <StatCard label="Contractor Rate Rules" value={rates.length} color="#7c3aed" icon={<TeamOutlined />} sub={`${activeRates.length} active`} />
        <StatCard label="Active POB Structures" value={structures.filter(s => s.is_active).length} color="#2563eb" icon={<SafetyOutlined />} />
      </div>

      <Tabs
        activeKey={activeSection}
        onChange={setActiveSection}
        size="small"
        items={[
          {
            key: 'zone',
            label: (
              <span>
                <EnvironmentOutlined /> Warehouse Allowances{' '}
                <span style={{ display: 'inline-block', padding: '0 6px', borderRadius: 999, fontSize: 10, fontWeight: 700, color: '#fff', background: '#d97706', marginLeft: 4 }}>{zones.length}</span>
              </span>
            ),
            children: (
              <div style={{ paddingTop: 12 }}>
                <Alert type="info" showIcon style={{ marginBottom: 12 }} message="Warehouse Allowances"
                  description={<span>Define location-based pay that is <b>automatically added</b> during payroll calculation when an employee has recorded attendance in a matching area/zone. Supports hourly, daily, and fixed rates plus hazard premiums.</span>} />
                <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
                    <Text strong><EnvironmentOutlined style={{ marginRight: 4 }} />Warehouse Allowance Rules</Text>
                    <Button type="primary" size="small" icon={<PlusOutlined />}
                      onClick={() => { zoneForm.resetFields(); zoneForm.setFieldsValue({ allowance_type: 1, is_hazard: false, is_active: true }); setZoneModal({ open: true, record: null }); }}>
                      New Rule
                    </Button>
                  </div>
                  <Table dataSource={zones} rowKey="id" loading={loadingZones} columns={zoneCols} size="small" scroll={{ x: 900 }} pagination={{ pageSize: 15, showTotal: t => `${t} rules` }} />
                </div>
              </div>
            ),
          },
          {
            key: 'contractor',
            label: (
              <span>
                <TeamOutlined /> Contractor Rates{' '}
                <span style={{ display: 'inline-block', padding: '0 6px', borderRadius: 999, fontSize: 10, fontWeight: 700, color: '#fff', background: '#7c3aed', marginLeft: 4 }}>{rates.length}</span>
              </span>
            ),
            children: (
              <div style={{ paddingTop: 12 }}>
                <Alert type="info" showIcon style={{ marginBottom: 12 }} message="Contractor Rates"
                  description={<span>Set <b>vendor-specific pay rates</b> used when calculating contractor payroll. Rates cascade: Position-specific overrides vendor-wide. Multipliers for OT, night, and holiday shifts are applied on top of the base rate.</span>} />
                <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
                    <Text strong><TeamOutlined style={{ marginRight: 4 }} />Vendor / Position Rate Matrix</Text>
                    <Button type="primary" size="small" icon={<PlusOutlined />}
                      onClick={() => { rateForm.resetFields(); rateForm.setFieldsValue({ ot_multiplier: 1.5, night_multiplier: 1.25, holiday_multiplier: 2.0, is_active: true }); setRateModal({ open: true, record: null }); }}>
                      Add Rate
                    </Button>
                  </div>
                  <Table dataSource={rates} rowKey="id" loading={loadingRates} columns={rateCols} size="small" scroll={{ x: 1000 }} pagination={{ pageSize: 15, showTotal: t => `${t} rates` }} />
                </div>
              </div>
            ),
          },
        ]}
      />

      {/* Warehouse Allowance Modal */}
      <Modal
        title={<span><EnvironmentOutlined /> {zoneModal.record ? 'Edit' : 'New'} Warehouse Allowance Rule</span>}
        open={zoneModal.open}
        onOk={saveZone}
        onCancel={() => setZoneModal({ open: false, record: null })}
        confirmLoading={saving}
        width={520}
      >
        <Form form={zoneForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={12}>
            <Col span={14}>
              <Form.Item name="structure_id" label="Salary Structure" rules={[{ required: true }]}>
                <Select placeholder="Select structure">
                  {structures.map(s => <Option key={s.id} value={s.id}>{s.structure_name}</Option>)}
                </Select>
              </Form.Item>
            </Col>
            <Col span={10}>
              <Form.Item name="area_id" label="Area / Warehouse ID" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} placeholder="Warehouse ID" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="allowance_type" label="Rate Type" rules={[{ required: true }]}>
                <Select>
                  <Option value={0}>Hourly</Option>
                  <Option value={1}>Daily</Option>
                  <Option value={2}>Fixed (per period)</Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="amount" label="Amount (₦)" rules={[{ required: true }]}>
                <InputNumber min={0} style={{ width: '100%' }} formatter={v => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
              </Form.Item>
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0' }}>Hazard Premium</Divider>
          <Row gutter={12} align="middle">
            <Col span={10}>
              <Form.Item name="is_hazard" label="Hazard Warehouse" valuePropName="checked">
                <Switch checkedChildren={<><FireOutlined /> Yes</>} unCheckedChildren="No" />
              </Form.Item>
            </Col>
            <Col span={14}>
              <Form.Item name="hazard_rate" label="Premium %" help="% added on top of base amount">
                <InputNumber min={0} max={500} step={5} style={{ width: '100%' }} placeholder="e.g. 25 for +25%" />
              </Form.Item>
            </Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="effective_date" label="Effective Date"><Input type="date" /></Form.Item></Col>
            <Col span={12}><Form.Item name="end_date" label="End Date (optional)"><Input type="date" /></Form.Item></Col>
          </Row>
          <Form.Item name="is_active" label="Active" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* Contractor Rate Modal */}
      <Modal
        title={<span><TeamOutlined /> {rateModal.record ? 'Edit' : 'New'} Contractor Rate</span>}
        open={rateModal.open}
        onOk={saveRate}
        onCancel={() => setRateModal({ open: false, record: null })}
        confirmLoading={saving}
        width={580}
      >
        <Form form={rateForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={12}>
            <Col span={12}>
              <Form.Item name="vendor_id" label="Vendor ID" rules={[{ required: true }]}>
                <InputNumber min={1} style={{ width: '100%' }} placeholder="Vendor/Company ID" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="position_id" label="Position ID (optional)" help="Leave blank for all positions">
                <InputNumber min={1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Divider style={{ margin: '8px 0' }}>Base Rates (₦)</Divider>
          <Row gutter={10}>
            <Col span={8}><Form.Item name="hourly_rate" label="Hourly Rate"><InputNumber min={0} style={{ width: '100%' }} placeholder="0" /></Form.Item></Col>
            <Col span={8}><Form.Item name="daily_rate" label="Daily Rate"><InputNumber min={0} style={{ width: '100%' }} placeholder="0" /></Form.Item></Col>
            <Col span={8}><Form.Item name="monthly_rate" label="Monthly Rate"><InputNumber min={0} style={{ width: '100%' }} placeholder="0" /></Form.Item></Col>
          </Row>
          <Divider style={{ margin: '8px 0' }}>
            Multipliers{' '}
            <Tooltip title="Applied on top of the hourly rate: OT pay = hourly × OT multiplier × OT hours">
              <InfoCircleOutlined style={{ color: '#2563eb' }} />
            </Tooltip>
          </Divider>
          <Row gutter={10}>
            <Col span={8}><Form.Item name="ot_multiplier" label="OT Multiplier"><InputNumber min={1} max={5} step={0.25} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="night_multiplier" label="Night Multiplier"><InputNumber min={1} max={5} step={0.25} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="holiday_multiplier" label="Holiday Multiplier"><InputNumber min={1} max={5} step={0.25} style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Row gutter={12}>
            <Col span={12}><Form.Item name="effective_date" label="Effective From"><Input type="date" /></Form.Item></Col>
            <Col span={12}><Form.Item name="end_date" label="Valid Until"><Input type="date" /></Form.Item></Col>
          </Row>
          <Form.Item name="is_active" label="Active" valuePropName="checked" initialValue={true}>
            <Switch />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default POBExtensionsTab;
