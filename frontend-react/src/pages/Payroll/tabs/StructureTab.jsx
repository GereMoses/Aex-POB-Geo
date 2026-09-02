import React, { useState, useEffect, useCallback } from 'react';
import {
  Table, Button, Space, Modal, Form, Input, Select,
  Switch, InputNumber, App, Row, Col, Tabs,
  Alert, Empty, Typography, Dropdown,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, EyeOutlined,
  UserOutlined, TeamOutlined, ApartmentOutlined,
  SearchOutlined,
  FireOutlined, EnvironmentOutlined, MoreOutlined,
} from '@ant-design/icons';
import { apiCall, fmt } from '../payrollApi';

const { Option } = Select;
const { Text } = Typography;

const CALC_TYPE_CFG = {
  fixed:      { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe', label: 'Fixed'      },
  formula:    { color: '#7c3aed', bg: '#ede9fe', border: '#ddd6fe', label: 'Formula'    },
  attendance: { color: '#0891b2', bg: '#ecfeff', border: '#a5f3fc', label: 'Attendance' },
};

const ITEM_TYPE_CFG = {
  earning:   { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', label: 'Earning'    },
  deduction: { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', label: 'Deduction'  },
  attendance:{ color: '#d97706', bg: '#fffbeb', border: '#fde68a', label: 'Attendance' },
};

const ASSIGN_TYPE = {
  0: { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe', label: 'Employee',   icon: <UserOutlined /> },
  1: { color: '#7c3aed', bg: '#ede9fe', border: '#ddd6fe', label: 'Department', icon: <TeamOutlined /> },
  2: { color: '#0891b2', bg: '#ecfeff', border: '#a5f3fc', label: 'Position',   icon: <ApartmentOutlined /> },
};

const MiniPill = ({ cfg }) => (
  <span style={{ display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: 10, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>
    {cfg.label}
  </span>
);

const StatusDot = ({ active }) => active
  ? <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#16a34a', background: '#f0fdf4', border: '1px solid #bbf7d0' }}>Active</span>
  : <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#94a3b8', background: '#f8fafc', border: '1px solid #e2e8f0' }}>Off</span>;

const StructureTab = ({ structures: propStructures, employees, onRefresh }) => {
  const { message, modal } = App.useApp();
  const [structures, setStructures] = useState(propStructures || []);
  const [search, setSearch] = useState('');
  const [filterType, setFilterType] = useState('all');
  const [selected, setSelected] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);

  const [structureModal, setStructureModal] = useState({ open: false, record: null });
  const [itemModal, setItemModal] = useState({ open: false, record: null });
  const [assignModal, setAssignModal] = useState(false);
  const [zoneModal, setZoneModal] = useState({ open: false, record: null });

  const [structureForm] = Form.useForm();
  const [itemForm] = Form.useForm();
  const [assignForm] = Form.useForm();
  const [zoneForm] = Form.useForm();

  const [calcType, setCalcType] = useState('fixed');
  const [rightTab, setRightTab] = useState('items');

  useEffect(() => { setStructures(propStructures || []); }, [propStructures]);

  const refreshStructures = useCallback(async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/v1/payroll/structures/');
      const list = Array.isArray(data) ? data : [];
      setStructures(list);
      if (selected) setSelected(list.find(s => s.id === selected.id) || null);
      onRefresh();
    } catch (e) {
      message.error(e.message);
    } finally {
      setLoading(false);
    }
  }, [selected, onRefresh]);

  const saveStructure = async () => {
    try {
      const values = await structureForm.validateFields();
      setSaving(true);
      const { record } = structureModal;
      if (record) {
        await apiCall(`/api/v1/payroll/structures/${record.id}`, { method: 'PUT', body: JSON.stringify(values) });
        message.success('Structure updated');
      } else {
        await apiCall('/api/v1/payroll/structures/', { method: 'POST', body: JSON.stringify(values) });
        message.success('Structure created');
      }
      setStructureModal({ open: false, record: null });
      await refreshStructures();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const deleteStructure = (id) => modal.confirm({
    title: 'Delete this structure?',
    content: 'This will remove all pay items and assignments. This action cannot be undone.',
    okType: 'danger', okText: 'Delete',
    onOk: async () => {
      await apiCall(`/api/v1/payroll/structures/${id}`, { method: 'DELETE' });
      message.success('Structure deleted');
      if (selected?.id === id) setSelected(null);
      await refreshStructures();
    },
  });

  const saveItem = async () => {
    try {
      const values = await itemForm.validateFields();
      setSaving(true);
      const sid = selected.id;
      const { record } = itemModal;
      if (record) {
        await apiCall(`/api/v1/payroll/structures/${sid}/items/${record.id}`, { method: 'PUT', body: JSON.stringify(values) });
        message.success('Item updated');
      } else {
        await apiCall(`/api/v1/payroll/structures/${sid}/items/`, { method: 'POST', body: JSON.stringify(values) });
        message.success('Item added');
      }
      setItemModal({ open: false, record: null });
      await refreshStructures();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const deleteItem = (itemId) => modal.confirm({
    title: 'Remove this pay item?',
    okType: 'danger', okText: 'Remove',
    onOk: async () => {
      await apiCall(`/api/v1/payroll/structures/${selected.id}/items/${itemId}`, { method: 'DELETE' });
      message.success('Item removed');
      await refreshStructures();
    },
  });

  const saveAssignment = async () => {
    try {
      const values = await assignForm.validateFields();
      setSaving(true);
      await apiCall(`/api/v1/payroll/structures/${selected.id}/assign/`, { method: 'POST', body: JSON.stringify(values) });
      message.success('Structure assigned');
      setAssignModal(false);
      assignForm.resetFields();
      await refreshStructures();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const saveZoneAllowance = async () => {
    try {
      const values = await zoneForm.validateFields();
      setSaving(true);
      await apiCall('/api/v1/payroll/zone-allowances/', { method: 'POST', body: JSON.stringify({ ...values, structure_id: selected.id }) });
      message.success('Warehouse allowance created');
      setZoneModal({ open: false, record: null });
      await refreshStructures();
    } catch (e) { if (e.errorFields) return; message.error(e.message); } finally { setSaving(false); }
  };

  const filtered = structures.filter(s => {
    const matchSearch = !search || s.structure_name?.toLowerCase().includes(search.toLowerCase());
    const matchType = filterType === 'all' || s.structure_type === filterType || (filterType === 'active' && s.is_active) || (filterType === 'inactive' && !s.is_active);
    return matchSearch && matchType;
  });

  const items = selected?.items || [];
  const earnings = items.filter(i => i.item_type === 'earning');
  const deductions = items.filter(i => i.item_type === 'deduction');
  const fixedEarnings = earnings.filter(i => i.calc_type === 'fixed').reduce((s, i) => s + (i.amount || 0), 0);

  const TYPE_PILL_CFG = {
    monthly: { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe' },
    daily:   { color: '#0891b2', bg: '#ecfeff', border: '#a5f3fc' },
    hourly:  { color: '#7c3aed', bg: '#ede9fe', border: '#ddd6fe' },
  };

  const structureCols = [
    {
      title: 'Structure', dataIndex: 'structure_name', key: 'name',
      render: (v, r) => (
        <Button type="link" style={{ padding: 0, textAlign: 'left', fontWeight: 500 }} onClick={() => { setSelected(r); setRightTab('items'); }}>
          {v}
        </Button>
      ),
    },
    {
      title: 'Type', dataIndex: 'structure_type', key: 'type', width: 85,
      render: v => {
        const cfg = TYPE_PILL_CFG[v] || { color: '#64748b', bg: '#f8fafc', border: '#e2e8f0' };
        return <span style={{ display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: 10, fontWeight: 700, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`, textTransform: 'uppercase' }}>{v}</span>;
      },
    },
    {
      title: 'Items', dataIndex: 'items_count', key: 'items', width: 60, align: 'center',
      render: v => <span style={{ display: 'inline-block', padding: '1px 7px', borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#2563eb', background: '#eff6ff', border: '1px solid #bfdbfe' }}>{v || 0}</span>,
    },
    { title: 'Status', dataIndex: 'is_active', key: 'active', width: 72, render: v => <StatusDot active={v} /> },
    {
      title: '', key: 'actions', width: 50,
      render: (_, record) => {
        const menuItems = [
          { key: 'edit', icon: <EditOutlined />, label: 'Edit', onClick: () => { structureForm.setFieldsValue(record); setStructureModal({ open: true, record }); } },
          { key: 'delete', icon: <DeleteOutlined />, label: 'Delete', danger: true, onClick: () => deleteStructure(record.id) },
        ];
        return <Dropdown trigger={['click']} menu={{ items: menuItems }}><Button size="small" type="text" icon={<MoreOutlined />} /></Dropdown>;
      },
    },
  ];

  const itemCols = [
    { title: '#', dataIndex: 'sequence', key: 'seq', width: 36, align: 'center', render: v => <Text type="secondary" style={{ fontSize: 11 }}>{v}</Text> },
    { title: 'Item Name', dataIndex: 'item_name', key: 'name', render: v => <Text strong style={{ fontSize: 13 }}>{v}</Text> },
    {
      title: 'Type', key: 'type', width: 100,
      render: (_, r) => (
        <Space size={2} direction="vertical" style={{ gap: 2 }}>
          <MiniPill cfg={ITEM_TYPE_CFG[r.item_type] || ITEM_TYPE_CFG.earning} />
          <MiniPill cfg={CALC_TYPE_CFG[r.calc_type] || CALC_TYPE_CFG.fixed} />
        </Space>
      ),
    },
    {
      title: 'Value', key: 'value',
      render: (_, r) => {
        if (r.calc_type === 'fixed') return <Text style={{ color: r.item_type === 'earning' ? '#16a34a' : '#dc2626' }}>{fmt(r.amount)}</Text>;
        if (r.calc_type === 'formula') return <code style={{ fontSize: 11, color: '#7c3aed', background: '#f5f3ff', padding: '1px 4px', borderRadius: 3 }}>{r.formula?.slice(0, 28)}{r.formula?.length > 28 ? '…' : ''}</code>;
        return <Text type="secondary" style={{ fontSize: 12 }}>{r.attendance_field} × {r.rate}</Text>;
      },
    },
    { title: 'GL', dataIndex: 'gl_account', key: 'gl', width: 80, render: v => v ? <Text code style={{ fontSize: 11 }}>{v}</Text> : <Text type="secondary">—</Text> },
    {
      title: '', key: 'actions', width: 70,
      render: (_, record) => (
        <Space size={2}>
          <Button size="small" icon={<EditOutlined />} onClick={() => { itemForm.setFieldsValue(record); setCalcType(record.calc_type); setItemModal({ open: true, record }); }} />
          <Button size="small" danger icon={<DeleteOutlined />} onClick={() => deleteItem(record.id)} />
        </Space>
      ),
    },
  ];

  const assignCols = [
    {
      title: 'Assigned To', dataIndex: 'assign_type', key: 'type',
      render: v => {
        const cfg = ASSIGN_TYPE[v] || ASSIGN_TYPE[0];
        return <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>{cfg.icon} {cfg.label}</span>;
      },
    },
    { title: 'ID', dataIndex: 'assign_id', key: 'id', width: 70, render: v => <Text code>{v}</Text> },
    { title: 'Priority', dataIndex: 'priority', key: 'prio', width: 80, align: 'center' },
    { title: 'Effective', dataIndex: 'effective_date', key: 'eff', render: d => d ? new Date(d).toLocaleDateString() : <Text type="secondary">Always</Text> },
    { title: 'Expires', dataIndex: 'end_date', key: 'end', render: d => d ? new Date(d).toLocaleDateString() : <Text type="secondary">Never</Text> },
    { title: '', dataIndex: 'is_active', key: 'active', width: 70, render: v => <StatusDot active={v} /> },
  ];

  const zoneAllowanceCols = [
    { title: 'Warehouse/Area', dataIndex: 'area_name', key: 'area', render: (v, r) => v || `Area ${r.area_id}` },
    {
      title: 'Type', dataIndex: 'allowance_type', key: 'type',
      render: v => <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#d97706', background: '#fffbeb', border: '1px solid #fde68a' }}>{['Hourly', 'Daily', 'Fixed'][v] || v}</span>,
    },
    { title: 'Amount', dataIndex: 'amount', key: 'amount', align: 'right', render: v => <Text strong style={{ color: '#16a34a' }}>{fmt(v)}</Text> },
    {
      title: 'Hazard', dataIndex: 'is_hazard', key: 'hazard', align: 'center',
      render: v => v ? <span style={{ display: 'inline-flex', alignItems: 'center', gap: 3, padding: '1px 6px', borderRadius: 999, fontSize: 10, fontWeight: 600, color: '#dc2626', background: '#fef2f2', border: '1px solid #fecaca' }}><FireOutlined />Yes</span> : '—',
    },
    { title: 'Hazard Rate', dataIndex: 'hazard_rate', key: 'hr', render: v => v ? `${v}%` : '—' },
    { title: 'Status', dataIndex: 'is_active', key: 'active', render: v => <StatusDot active={v} /> },
  ];

  const rightPanelTabs = [
    {
      key: 'items',
      label: `Pay Items (${items.length})`,
      children: (
        <div>
          {/* Summary strip */}
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <div style={{ flex: 1, background: '#f0fdf4', borderRadius: 6, padding: '8px 12px' }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Earnings</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#16a34a' }}>{earnings.length}</div>
            </div>
            <div style={{ flex: 1, background: '#fef2f2', borderRadius: 6, padding: '8px 12px' }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Deductions</div>
              <div style={{ fontSize: 18, fontWeight: 700, color: '#dc2626' }}>{deductions.length}</div>
            </div>
            <div style={{ flex: 2, background: '#eff6ff', borderRadius: 6, padding: '8px 12px' }}>
              <div style={{ fontSize: 11, color: '#64748b' }}>Fixed Gross</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#2563eb' }}>{fmt(fixedEarnings)}</div>
            </div>
          </div>
          <div style={{ marginBottom: 8, textAlign: 'right' }}>
            <Button type="primary" size="small" icon={<PlusOutlined />}
              onClick={() => { itemForm.resetFields(); itemForm.setFieldsValue({ item_type: 'earning', calc_type: 'fixed', sequence: items.length, is_taxable: false, is_print: true, is_mandatory: false }); setCalcType('fixed'); setItemModal({ open: true, record: null }); }}>
              Add Item
            </Button>
          </div>
          <Table dataSource={items} rowKey="id" size="small" pagination={false} columns={itemCols} />
        </div>
      ),
    },
    {
      key: 'zone',
      label: <span><EnvironmentOutlined /> Warehouse Allowances</span>,
      children: (
        <div>
          <Alert type="info" showIcon style={{ marginBottom: 10 }} message="Warehouse allowances are auto-applied during payroll calculation when an employee works in the defined area." />
          <div style={{ marginBottom: 8, textAlign: 'right' }}>
            <Button size="small" icon={<PlusOutlined />} onClick={() => { zoneForm.resetFields(); zoneForm.setFieldsValue({ allowance_type: 1, is_hazard: false, is_active: true }); setZoneModal({ open: true, record: null }); }}>
              Add Warehouse Allowance
            </Button>
          </div>
          <Table dataSource={selected?.zone_allowances || []} rowKey="id" size="small" pagination={false} columns={zoneAllowanceCols}
            locale={{ emptyText: <Empty description="No warehouse allowances — add one to give location-based pay automatically" /> }} />
        </div>
      ),
    },
    {
      key: 'assign',
      label: `Assignments (${(selected?.assignments || []).length})`,
      children: (
        <div>
          <Alert
            type={selected?.assignments?.length ? 'success' : 'warning'}
            showIcon
            style={{ marginBottom: 10 }}
            message={selected?.assignments?.length
              ? `${selected.assignments.length} assignment(s) — highest priority wins when employee matches multiple rules.`
              : 'No assignments yet. This structure will not be applied to any employee until assigned.'}
          />
          <div style={{ marginBottom: 8, textAlign: 'right' }}>
            <Button size="small" icon={<PlusOutlined />} onClick={() => { assignForm.resetFields(); setAssignModal(true); }}>
              Add Assignment
            </Button>
          </div>
          <Table dataSource={selected?.assignments || []} rowKey="id" size="small" pagination={false} columns={assignCols} />
        </div>
      ),
    },
  ];

  return (
    <Row gutter={16}>
      {/* Left: structure list */}
      <Col xs={24} lg={9}>
        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <Space>
              <Text strong style={{ fontSize: 14 }}>Salary Structures</Text>
              <span style={{ display: 'inline-block', padding: '1px 7px', borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#2563eb', background: '#eff6ff', border: '1px solid #bfdbfe' }}>{filtered.length}</span>
            </Space>
            <Button type="primary" size="small" icon={<PlusOutlined />}
              onClick={() => { structureForm.resetFields(); structureForm.setFieldsValue({ structure_type: 'monthly', is_active: true }); setStructureModal({ open: true, record: null }); }}>
              New
            </Button>
          </div>

          <div style={{ padding: '10px 12px', borderBottom: '1px solid #f5f5f5' }}>
            <Row gutter={8}>
              <Col flex="auto">
                <Input prefix={<SearchOutlined style={{ color: '#bbb' }} />} placeholder="Search structures…" value={search} onChange={e => setSearch(e.target.value)} allowClear size="small" />
              </Col>
              <Col>
                <Select value={filterType} onChange={setFilterType} size="small" style={{ width: 100 }}>
                  <Option value="all">All</Option>
                  <Option value="active">Active</Option>
                  <Option value="inactive">Inactive</Option>
                  <Option value="monthly">Monthly</Option>
                  <Option value="daily">Daily</Option>
                  <Option value="hourly">Hourly</Option>
                </Select>
              </Col>
            </Row>
          </div>

          <Table
            dataSource={filtered}
            rowKey="id"
            size="small"
            loading={loading}
            columns={structureCols}
            rowClassName={r => r.id === selected?.id ? 'ant-table-row-selected' : ''}
            onRow={r => ({ onClick: () => { setSelected(r); setRightTab('items'); }, style: { cursor: 'pointer' } })}
            pagination={{ pageSize: 10, showTotal: t => `${t} structures`, size: 'small' }}
            locale={{ emptyText: <Empty description="No structures — create your first one" /> }}
          />
        </div>
      </Col>

      {/* Right: detail panel */}
      <Col xs={24} lg={15}>
        {selected ? (
          <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
              <Space>
                <StatusDot active={selected.is_active} />
                <span style={{ ...(() => { const cfg = TYPE_PILL_CFG[selected.structure_type] || { color: '#64748b', bg: '#f8fafc', border: '#e2e8f0' }; return { display: 'inline-block', padding: '1px 7px', borderRadius: 999, fontSize: 10, fontWeight: 700, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}`, textTransform: 'uppercase' }; })() }}>
                  {selected.structure_type}
                </span>
                <Text strong style={{ fontSize: 14 }}>{selected.structure_name}</Text>
              </Space>
              <Button size="small" icon={<EditOutlined />} onClick={() => { structureForm.setFieldsValue(selected); setStructureModal({ open: true, record: selected }); }}>Edit</Button>
            </div>
            <div style={{ padding: '0 16px 16px' }}>
              <Tabs activeKey={rightTab} onChange={setRightTab} size="small" items={rightPanelTabs} />
            </div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 400, color: '#94a3b8' }}>
            <EyeOutlined style={{ fontSize: 48, marginBottom: 12 }} />
            <Text type="secondary">Click a structure on the left to view and manage its items, zone allowances, and assignments.</Text>
          </div>
        )}
      </Col>

      {/* Create/Edit Structure Modal */}
      <Modal
        title={structureModal.record ? 'Edit Structure' : 'Create Salary Structure'}
        open={structureModal.open}
        onOk={saveStructure}
        onCancel={() => setStructureModal({ open: false, record: null })}
        confirmLoading={saving}
        width={500}
      >
        <Form form={structureForm} layout="vertical" style={{ marginTop: 12 }}>
          <Form.Item name="structure_name" label="Name" rules={[{ required: true }]}>
            <Input placeholder="e.g. Monthly Staff, POB Contractor" />
          </Form.Item>
          <Row gutter={12}>
            <Col span={10}>
              <Form.Item name="structure_type" label="Pay Cycle" rules={[{ required: true }]}>
                <Select><Option value="monthly">Monthly</Option><Option value="daily">Daily</Option><Option value="hourly">Hourly</Option></Select>
              </Form.Item>
            </Col>
            <Col span={7}><Form.Item name="effective_date" label="Effective Date"><Input type="date" /></Form.Item></Col>
            <Col span={7}><Form.Item name="is_active" label="Active" valuePropName="checked"><Switch checkedChildren="Yes" unCheckedChildren="No" /></Form.Item></Col>
          </Row>
          <Form.Item name="description" label="Description"><Input.TextArea rows={2} /></Form.Item>
        </Form>
      </Modal>

      {/* Add/Edit Item Modal */}
      <Modal
        title={itemModal.record ? 'Edit Pay Item' : 'Add Pay Item'}
        open={itemModal.open}
        onOk={saveItem}
        onCancel={() => setItemModal({ open: false, record: null })}
        confirmLoading={saving}
        width={580}
      >
        <Form form={itemForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={10}>
            <Col span={12}><Form.Item name="item_name" label="Item Name" rules={[{ required: true }]}><Input placeholder="e.g. Basic Salary, Housing" /></Form.Item></Col>
            <Col span={6}><Form.Item name="item_type" label="Type" rules={[{ required: true }]}><Select><Option value="earning">Earning</Option><Option value="deduction">Deduction</Option><Option value="attendance">Attendance</Option></Select></Form.Item></Col>
            <Col span={6}><Form.Item name="sequence" label="Order"><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
          </Row>
          <Form.Item name="calc_type" label="Calculation Method" rules={[{ required: true }]}>
            <Select onChange={v => { setCalcType(v); itemForm.setFieldsValue({ amount: null, formula: null, attendance_field: null, rate: null }); }}>
              <Option value="fixed"><MiniPill cfg={CALC_TYPE_CFG.fixed} /> — Set amount applied every period</Option>
              <Option value="formula"><MiniPill cfg={CALC_TYPE_CFG.formula} /> — Dynamic expression (Basic * 0.4)</Option>
              <Option value="attendance"><MiniPill cfg={CALC_TYPE_CFG.attendance} /> — Field × Rate from attendance data</Option>
            </Select>
          </Form.Item>
          {calcType === 'fixed' && (
            <Form.Item name="amount" label="Fixed Amount (₦)" rules={[{ required: true }]}>
              <InputNumber min={0} style={{ width: '100%' }} formatter={v => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
            </Form.Item>
          )}
          {calcType === 'formula' && (
            <Form.Item name="formula" label="Formula" rules={[{ required: true }]} help="Variables: Basic, OTHours, ZoneHours, NightHours, HazardDays, LateMinutes, WorkDays, PresentDays">
              <Input.TextArea rows={3} style={{ fontFamily: 'monospace', fontSize: 13 }} placeholder="ROUND(Basic * 0.4, 2)" />
            </Form.Item>
          )}
          {calcType === 'attendance' && (
            <Row gutter={10}>
              <Col span={13}>
                <Form.Item name="attendance_field" label="Attendance Field" rules={[{ required: true }]}>
                  <Select>
                    {['work_days', 'present_days', 'ot_hours', 'late_minutes', 'absent_days', 'zone_hours', 'night_hours', 'hazard_days'].map(f => <Option key={f} value={f}>{f}</Option>)}
                  </Select>
                </Form.Item>
              </Col>
              <Col span={11}><Form.Item name="rate" label="Rate per Unit (₦)" rules={[{ required: true }]}><InputNumber min={0} style={{ width: '100%' }} /></Form.Item></Col>
            </Row>
          )}
          <Row gutter={10}>
            <Col span={8}><Form.Item name="is_taxable" label="Taxable" valuePropName="checked"><Switch size="small" /></Form.Item></Col>
            <Col span={8}><Form.Item name="is_print" label="On Payslip" valuePropName="checked" initialValue={true}><Switch size="small" defaultChecked /></Form.Item></Col>
            <Col span={8}><Form.Item name="is_mandatory" label="Mandatory" valuePropName="checked"><Switch size="small" /></Form.Item></Col>
          </Row>
          <Form.Item name="gl_account" label="GL Account"><Input placeholder="e.g. 6001-100" /></Form.Item>
        </Form>
      </Modal>

      {/* Assign Structure Modal */}
      <Modal
        title={`Assign — ${selected?.structure_name}`}
        open={assignModal}
        onOk={saveAssignment}
        onCancel={() => setAssignModal(false)}
        confirmLoading={saving}
        width={460}
      >
        <Alert type="info" showIcon style={{ marginBottom: 12 }} message="Priority: Employee > Position > Department. Higher number = higher priority." />
        <Form form={assignForm} layout="vertical">
          <Form.Item name="assign_type" label="Assign To" rules={[{ required: true }]}>
            <Select>
              <Option value={0}><UserOutlined /> Employee (individual)</Option>
              <Option value={1}><TeamOutlined /> Department (all members)</Option>
              <Option value={2}><ApartmentOutlined /> Position (all holders)</Option>
            </Select>
          </Form.Item>
          <Form.Item name="assign_id" label="Entity ID" rules={[{ required: true }]}>
            <InputNumber min={1} style={{ width: '100%' }} placeholder="Employee / Department / Position ID" />
          </Form.Item>
          <Row gutter={10}>
            <Col span={8}><Form.Item name="priority" label="Priority"><InputNumber min={0} defaultValue={0} style={{ width: '100%' }} /></Form.Item></Col>
            <Col span={8}><Form.Item name="effective_date" label="From"><Input type="date" /></Form.Item></Col>
            <Col span={8}><Form.Item name="end_date" label="Until (opt.)"><Input type="date" /></Form.Item></Col>
          </Row>
        </Form>
      </Modal>

      {/* Add Warehouse Allowance Modal */}
      <Modal
        title={<span><EnvironmentOutlined /> Add Warehouse Allowance — {selected?.structure_name}</span>}
        open={zoneModal.open}
        onOk={saveZoneAllowance}
        onCancel={() => setZoneModal({ open: false, record: null })}
        confirmLoading={saving}
        width={480}
      >
        <Form form={zoneForm} layout="vertical" style={{ marginTop: 12 }}>
          <Row gutter={10}>
            <Col span={14}><Form.Item name="area_id" label="Area / Warehouse ID" rules={[{ required: true }]}><InputNumber min={1} style={{ width: '100%' }} placeholder="Warehouse ID from Area Management" /></Form.Item></Col>
            <Col span={10}>
              <Form.Item name="allowance_type" label="Rate Type" rules={[{ required: true }]}>
                <Select><Option value={0}>Hourly</Option><Option value={1}>Daily</Option><Option value={2}>Fixed (per period)</Option></Select>
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="amount" label="Amount (₦)" rules={[{ required: true }]}>
            <InputNumber min={0} style={{ width: '100%' }} formatter={v => `${v}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')} />
          </Form.Item>
          <Row gutter={10}>
            <Col span={10}><Form.Item name="is_hazard" label="Hazard Warehouse" valuePropName="checked"><Switch checkedChildren={<FireOutlined />} unCheckedChildren="No" /></Form.Item></Col>
            <Col span={14}><Form.Item name="hazard_rate" label="Hazard Premium (%)"><InputNumber min={0} max={100} style={{ width: '100%' }} placeholder="e.g. 25 for 25%" /></Form.Item></Col>
          </Row>
          <Form.Item name="is_active" label="Active" valuePropName="checked" initialValue={true}><Switch /></Form.Item>
        </Form>
      </Modal>
    </Row>
  );
};

export default StructureTab;
