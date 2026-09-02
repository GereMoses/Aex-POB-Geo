import React, { useState, useEffect, useCallback } from 'react';
import {
  Row, Col, Button, Select, Switch, Table, Space,
  Progress, App, Alert, Modal, Form, Input, InputNumber, Drawer,
  Descriptions, Divider, Typography, Skeleton, Dropdown,
} from 'antd';
import {
  CalculatorOutlined, SyncOutlined, EyeOutlined, EditOutlined,
  CheckCircleOutlined, CloseCircleOutlined,
  AuditOutlined, ReloadOutlined, TeamOutlined, UserOutlined, MoreOutlined,
} from '@ant-design/icons';
import { apiCall, fmt } from '../payrollApi';

const { Option } = Select;
const { Text } = Typography;

const STATUS_CFG = {
  calculated: { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', row: 'rgba(22,163,74,0.04)',   label: 'Calculated' },
  pending:    { color: '#d97706', bg: '#fffbeb', border: '#fde68a', row: 'rgba(217,119,6,0.04)',   label: 'Pending'    },
  failed:     { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', row: 'rgba(220,38,38,0.05)',   label: 'Failed'     },
  open:       { color: '#2563eb', bg: '#eff6ff', border: '#bfdbfe', row: '',                       label: 'Open'       },
  closed:     { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', row: '',                       label: 'Closed'     },
  cancelled:  { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', row: '',                       label: 'Cancelled'  },
  calculating:{ color: '#d97706', bg: '#fffbeb', border: '#fde68a', row: '',                       label: 'Calculating'},
};

const StatusPill = ({ status }) => {
  const cfg = STATUS_CFG[status?.toLowerCase()] || { color: '#64748b', bg: '#f8fafc', border: '#e2e8f0', label: status };
  return <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>{cfg.label}</span>;
};

const ItemTypePill = ({ type }) => {
  const cfg = type === 'earning'
    ? { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0' }
    : { color: '#dc2626', bg: '#fef2f2', border: '#fecaca' };
  return <span style={{ display: 'inline-block', padding: '2px 6px', borderRadius: 999, fontSize: 10, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>{type}</span>;
};

const StatCard = ({ label, value, color }) => (
  <div style={{ flex: 1, background: '#fff', borderRadius: 8, padding: '14px 16px', borderTop: `3px solid ${color}`, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
    <div style={{ fontSize: 12, color: '#64748b', marginBottom: 4 }}>{label}</div>
    <div style={{ fontSize: 22, fontWeight: 700, color }}>{value}</div>
  </div>
);

const CalculationTab = ({ periods, employees, departments = [] }) => {
  const { message } = App.useApp();
  const [selectedPeriodId, setSelectedPeriodId] = useState(null);
  const [selectedEmpIds, setSelectedEmpIds] = useState([]);
  const [selectedDeptIds, setSelectedDeptIds] = useState([]);
  const [forceRecalc, setForceRecalc] = useState(false);
  const [calculating, setCalculating] = useState(false);
  const [calcResult, setCalcResult] = useState(null);
  const [salaries, setSalaries] = useState([]);
  const [loadingSalaries, setLoadingSalaries] = useState(false);
  const [detailDrawer, setDetailDrawer] = useState({ open: false, salary: null });
  const [adjustModal, setAdjustModal] = useState({ open: false, salary: null });
  const [adjustForm] = Form.useForm();
  const [adjusting, setSaving] = useState(false);
  const [logs, setLogs] = useState([]);
  const [logsVisible, setLogsVisible] = useState(false);

  const fetchSalaries = useCallback(async (periodId) => {
    if (!periodId) return;
    setLoadingSalaries(true);
    try {
      const data = await apiCall(`/api/v1/payroll/salaries/?period_id=${periodId}`);
      setSalaries(Array.isArray(data) ? data : []);
    } catch (e) {
      message.error('Failed to load salaries: ' + e.message);
    } finally {
      setLoadingSalaries(false);
    }
  }, []);

  useEffect(() => {
    if (selectedPeriodId) fetchSalaries(selectedPeriodId);
    else setSalaries([]);
  }, [selectedPeriodId, fetchSalaries]);

  const runCalculation = async () => {
    if (!selectedPeriodId) { message.warning('Select a pay period first'); return; }
    setCalculating(true);
    setCalcResult(null);
    try {
      const payload = {
        period_id: selectedPeriodId,
        force_recalc: forceRecalc,
        ...(selectedEmpIds.length > 0 && { emp_ids: selectedEmpIds }),
        ...(selectedDeptIds.length > 0 && { dept_ids: selectedDeptIds }),
      };
      const result = await apiCall('/api/v1/payroll/calculate/', { method: 'POST', body: JSON.stringify(payload) });
      setCalcResult(result);
      const status = result.failed_count > 0 ? 'warning' : 'success';
      message[status](`Calculation complete: ${result.success_count} succeeded, ${result.failed_count} failed`);
      await fetchSalaries(selectedPeriodId);
    } catch (e) {
      message.error('Calculation failed: ' + e.message);
      setCalcResult({ error: e.message });
    } finally {
      setCalculating(false);
    }
  };

  const recalcOne = async (salaryId) => {
    try {
      await apiCall(`/api/v1/payroll/salaries/${salaryId}/recalc/`, { method: 'POST' });
      message.success('Recalculated');
      await fetchSalaries(selectedPeriodId);
    } catch (e) { message.error(e.message); }
  };

  const openDetail = async (salary) => {
    try {
      const detail = await apiCall(`/api/v1/payroll/salaries/${salary.id}`);
      setDetailDrawer({ open: true, salary: detail });
    } catch {
      setDetailDrawer({ open: true, salary });
    }
  };

  const saveAdjustment = async () => {
    try {
      const values = await adjustForm.validateFields();
      setSaving(true);
      await apiCall(`/api/v1/payroll/salaries/${adjustModal.salary.id}/adjust/`, { method: 'POST', body: JSON.stringify(values) });
      message.success('Adjustment saved');
      setAdjustModal({ open: false, salary: null });
      await fetchSalaries(selectedPeriodId);
    } catch (e) {
      if (e.errorFields) return;
      message.error(e.message);
    } finally {
      setSaving(false);
    }
  };

  const fetchLogs = async () => {
    try {
      const data = await apiCall('/api/v1/payroll/calculation-logs/');
      setLogs(Array.isArray(data) ? data : []);
      setLogsVisible(true);
    } catch (e) { message.error(e.message); }
  };

  const totalCount = salaries.length;
  const calcCount = salaries.filter(s => s.calc_status === 'calculated').length;
  const failedCount = salaries.filter(s => s.calc_status === 'failed').length;
  const pendingCount = totalCount - calcCount - failedCount;
  const percent = totalCount > 0 ? Math.round((calcCount / totalCount) * 100) : 0;
  const totalGross = salaries.reduce((s, r) => s + (r.gross_salary || 0), 0);
  const totalNet = salaries.reduce((s, r) => s + (r.net_salary || 0), 0);
  const totalDeduct = salaries.reduce((s, r) => s + (r.total_deductions || 0), 0);

  const columns = [
    { title: 'Employee', dataIndex: 'employee_name', key: 'name', sorter: (a, b) => a.employee_name?.localeCompare(b.employee_name), render: v => <Text strong>{v}</Text> },
    { title: 'Badge', dataIndex: 'employee_badge_id', key: 'badge', width: 90 },
    { title: 'Basic', dataIndex: 'basic_salary', key: 'basic', width: 120, align: 'right', sorter: (a, b) => (a.basic_salary || 0) - (b.basic_salary || 0), render: v => fmt(v) },
    { title: 'Gross', dataIndex: 'gross_salary', key: 'gross', width: 130, align: 'right', sorter: (a, b) => (a.gross_salary || 0) - (b.gross_salary || 0), render: v => <Text style={{ color: '#16a34a' }}>{fmt(v)}</Text> },
    { title: 'Deductions', dataIndex: 'total_deductions', key: 'deduct', width: 130, align: 'right', render: v => <Text style={{ color: '#dc2626' }}>-{fmt(v)}</Text> },
    { title: 'Net Pay', dataIndex: 'net_salary', key: 'net', width: 130, align: 'right', sorter: (a, b) => (a.net_salary || 0) - (b.net_salary || 0), render: v => <Text strong style={{ color: '#2563eb' }}>{fmt(v)}</Text> },
    {
      title: 'OT Hrs', dataIndex: 'ot_hours', key: 'ot', width: 80, align: 'center',
      render: v => v > 0
        ? <span style={{ display: 'inline-block', padding: '1px 7px', borderRadius: 999, fontSize: 11, fontWeight: 700, color: '#d97706', background: '#fffbeb', border: '1px solid #fde68a' }}>{v}</span>
        : <Text type="secondary">0</Text>,
    },
    {
      title: 'Status', dataIndex: 'calc_status', key: 'status', width: 110,
      filters: ['calculated', 'pending', 'failed'].map(s => ({ text: s, value: s })),
      onFilter: (val, r) => r.calc_status === val,
      render: s => <StatusPill status={s} />,
    },
    {
      title: 'Final', dataIndex: 'is_final', key: 'final', width: 65, align: 'center',
      render: v => v ? <CheckCircleOutlined style={{ color: '#16a34a' }} /> : <CloseCircleOutlined style={{ color: '#e2e8f0' }} />,
    },
    {
      title: '', key: 'actions', width: 50,
      render: (_, record) => {
        const items = [
          { key: 'view', icon: <EyeOutlined />, label: 'View Breakdown', onClick: () => openDetail(record) },
          { key: 'recalc', icon: <ReloadOutlined />, label: 'Recalculate', onClick: () => recalcOne(record.id) },
          { key: 'adjust', icon: <EditOutlined />, label: 'Manual Adjust', onClick: () => { adjustForm.resetFields(); setAdjustModal({ open: true, salary: record }); } },
        ];
        return <Dropdown trigger={['click']} menu={{ items }}><Button size="small" type="text" icon={<MoreOutlined />} /></Dropdown>;
      },
    },
  ];

  return (
    <div>
      <Row gutter={16}>
        {/* Control panel */}
        <Col xs={24} md={8}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <Text strong style={{ fontSize: 14 }}><CalculatorOutlined style={{ marginRight: 6 }} />Calculation Control</Text>

            <div style={{ marginTop: 12, marginBottom: 12 }}>
              <div style={{ marginBottom: 4 }}><Text strong>Pay Period <span style={{ color: '#dc2626' }}>*</span></Text></div>
              <Select
                style={{ width: '100%' }}
                placeholder="Select period"
                onChange={v => { setSelectedPeriodId(v); setCalcResult(null); }}
                value={selectedPeriodId}
                showSearch
                filterOption={(input, opt) => opt.label?.toLowerCase().includes(input.toLowerCase())}
                options={periods.map(p => ({ value: p.id, label: `[${p.status}] ${p.period_name}`, status: p.status }))}
                optionRender={opt => {
                  const cfg = STATUS_CFG[opt.data.status] || { color: '#64748b', bg: '#f8fafc', border: '#e2e8f0' };
                  return (
                    <Space size={6}>
                      <span style={{ display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: 10, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>{opt.data.status}</span>
                      {opt.label.replace(/^\[.*?\] /, '')}
                    </Space>
                  );
                }}
              />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ marginBottom: 4 }}><Text strong><UserOutlined /> Employees </Text><Text type="secondary" style={{ fontSize: 12 }}>(blank = all)</Text></div>
              <Select mode="multiple" style={{ width: '100%' }} placeholder="All employees if blank" onChange={setSelectedEmpIds} value={selectedEmpIds} showSearch filterOption={(i, o) => o.label?.toLowerCase().includes(i.toLowerCase())} options={employees.map(e => ({ value: e.id, label: `${e.full_name || e.name} (${e.badge_id})` }))} maxTagCount={2} />
            </div>

            <div style={{ marginBottom: 12 }}>
              <div style={{ marginBottom: 4 }}><Text strong><TeamOutlined /> Departments </Text><Text type="secondary" style={{ fontSize: 12 }}>(blank = all)</Text></div>
              <Select mode="multiple" style={{ width: '100%' }} placeholder="Filter by department…" onChange={setSelectedDeptIds} value={selectedDeptIds} showSearch filterOption={(i, o) => o.label?.toLowerCase().includes(i.toLowerCase())} options={departments.map(d => ({ value: d.id, label: d.name || d.dept_name || `Dept ${d.id}` }))} maxTagCount={2} />
            </div>

            <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 0', borderTop: '1px solid #f0f0f0', borderBottom: '1px solid #f0f0f0', marginBottom: 14 }}>
              <Switch checked={forceRecalc} onChange={setForceRecalc} size="small" />
              <div>
                <Text strong>Force Recalculate</Text>
                <br />
                <Text type="secondary" style={{ fontSize: 11 }}>Overwrite already-calculated records</Text>
              </div>
            </div>

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button type="primary" block icon={<CalculatorOutlined />} onClick={runCalculation} loading={calculating} size="large">
                {calculating ? 'Calculating…' : 'Run Payroll Calculation'}
              </Button>
              <Button block icon={<AuditOutlined />} onClick={fetchLogs}>View Audit Log</Button>
            </Space>

            {calcResult && (
              <div style={{ marginTop: 12 }}>
                {calcResult.error
                  ? <Alert type="error" message={calcResult.error} showIcon />
                  : <Alert type={calcResult.failed_count > 0 ? 'warning' : 'success'} showIcon message={`${calcResult.success_count || 0} calculated`}
                      description={calcResult.failed_count > 0 ? `${calcResult.failed_count} failed — check audit log for details` : 'All employees calculated successfully'} />}
              </div>
            )}
          </div>
        </Col>

        {/* Stats panel */}
        <Col xs={24} md={16}>
          <div style={{ display: 'flex', gap: 10, marginBottom: 12 }}>
            <StatCard label="Employees" value={totalCount} color="#64748b" />
            <StatCard label="Calculated" value={calcCount} color="#16a34a" />
            <StatCard label="Pending" value={pendingCount} color="#d97706" />
            <StatCard label="Failed" value={failedCount} color={failedCount > 0 ? '#dc2626' : '#64748b'} />
          </div>

          {totalCount > 0 && (
            <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
              <Progress percent={percent} status={failedCount > 0 ? 'exception' : percent === 100 ? 'success' : 'active'} format={p => `${p}% calculated`} />
              <div style={{ display: 'flex', gap: 24, marginTop: 10 }}>
                <div><Text type="secondary">Total Gross</Text><br /><Text strong style={{ color: '#16a34a' }}>{fmt(totalGross)}</Text></div>
                <div><Text type="secondary">Total Deductions</Text><br /><Text strong style={{ color: '#dc2626' }}>-{fmt(totalDeduct)}</Text></div>
                <div><Text type="secondary">Total Net</Text><br /><Text strong style={{ color: '#2563eb', fontSize: 16 }}>{fmt(totalNet)}</Text></div>
              </div>
            </div>
          )}

          {!selectedPeriodId && (
            <Alert type="info" showIcon message="Select a pay period to view or run payroll calculations." />
          )}
        </Col>
      </Row>

      {/* Salary table */}
      {selectedPeriodId && loadingSalaries && (
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginTop: 16 }}>
          <Skeleton active paragraph={{ rows: 6 }} />
        </div>
      )}
      {selectedPeriodId && !loadingSalaries && (
        <div style={{ background: '#fff', borderRadius: 8, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', overflow: 'hidden', marginTop: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
            <Text strong style={{ fontSize: 14 }}>Calculated Salaries</Text>
            <Button size="small" icon={<SyncOutlined />} onClick={() => fetchSalaries(selectedPeriodId)} loading={loadingSalaries}>Refresh</Button>
          </div>
          <Table
            dataSource={salaries}
            rowKey="id"
            columns={columns}
            size="small"
            scroll={{ x: 1200 }}
            rowClassName={r => `row-calc-${r.calc_status}`}
            pagination={{ pageSize: 20, showTotal: t => `${t} employees`, showSizeChanger: true }}
            summary={() => totalCount > 0 && (
              <Table.Summary.Row style={{ background: '#fafafa', fontWeight: 600 }}>
                <Table.Summary.Cell index={0} colSpan={4}>TOTAL</Table.Summary.Cell>
                <Table.Summary.Cell index={4} align="right"><Text style={{ color: '#16a34a' }}>{fmt(totalGross)}</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={5} align="right"><Text style={{ color: '#dc2626' }}>-{fmt(totalDeduct)}</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={6} align="right"><Text strong style={{ color: '#2563eb' }}>{fmt(totalNet)}</Text></Table.Summary.Cell>
                <Table.Summary.Cell index={7} colSpan={4} />
              </Table.Summary.Row>
            )}
          />
        </div>
      )}

      {/* Detail Drawer */}
      <Drawer
        title={`Salary Breakdown — ${detailDrawer.salary?.employee_name}`}
        open={detailDrawer.open}
        onClose={() => setDetailDrawer({ open: false, salary: null })}
        width={560}
      >
        {detailDrawer.salary && (
          <>
            <Descriptions column={2} size="small" bordered style={{ marginBottom: 16 }}>
              <Descriptions.Item label="Badge">{detailDrawer.salary.employee_badge_id}</Descriptions.Item>
              <Descriptions.Item label="Status"><StatusPill status={detailDrawer.salary.calc_status} /></Descriptions.Item>
              <Descriptions.Item label="Work Days">{detailDrawer.salary.work_days}</Descriptions.Item>
              <Descriptions.Item label="Present Days">{detailDrawer.salary.present_days}</Descriptions.Item>
              <Descriptions.Item label="OT Hours">{detailDrawer.salary.ot_hours}</Descriptions.Item>
              <Descriptions.Item label="Late Minutes">{detailDrawer.salary.late_minutes}</Descriptions.Item>
              {detailDrawer.salary.zone_hours > 0 && <Descriptions.Item label="Warehouse Hours">{detailDrawer.salary.zone_hours}</Descriptions.Item>}
              {detailDrawer.salary.night_hours > 0 && <Descriptions.Item label="Night Hours">{detailDrawer.salary.night_hours}</Descriptions.Item>}
              {detailDrawer.salary.hazard_days > 0 && <Descriptions.Item label="Hazard Days">{detailDrawer.salary.hazard_days}</Descriptions.Item>}
            </Descriptions>
            {detailDrawer.salary.items?.length > 0 && (
              <>
                <Divider orientation="left">Pay Item Breakdown</Divider>
                <Table
                  dataSource={detailDrawer.salary.items}
                  rowKey="id"
                  size="small"
                  pagination={false}
                  columns={[
                    { title: 'Item', dataIndex: 'item_name', key: 'name' },
                    { title: 'Type', dataIndex: 'item_type', key: 'type', width: 90, render: v => <ItemTypePill type={v} /> },
                    { title: 'Value', dataIndex: 'item_value', key: 'val', align: 'right', width: 130, render: (v, r) => <Text style={{ color: r.item_type === 'earning' ? '#16a34a' : '#dc2626' }}>{r.item_type === 'deduction' ? '-' : ''}{fmt(v)}</Text> },
                    { title: 'Adj', dataIndex: 'is_manual_adjustment', key: 'manual', width: 50, align: 'center', render: v => v ? <span style={{ display: 'inline-block', padding: '1px 5px', borderRadius: 999, fontSize: 9, fontWeight: 700, color: '#d97706', background: '#fffbeb', border: '1px solid #fde68a' }}>ADJ</span> : null },
                  ]}
                  summary={() => (
                    <>
                      <Table.Summary.Row>
                        <Table.Summary.Cell index={0} colSpan={2}><Text strong>Gross Earnings</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={2} align="right"><Text strong style={{ color: '#16a34a' }}>{fmt(detailDrawer.salary.total_earnings)}</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={3} />
                      </Table.Summary.Row>
                      <Table.Summary.Row>
                        <Table.Summary.Cell index={0} colSpan={2}><Text strong>Total Deductions</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={2} align="right"><Text strong style={{ color: '#dc2626' }}>-{fmt(detailDrawer.salary.total_deductions)}</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={3} />
                      </Table.Summary.Row>
                      <Table.Summary.Row style={{ background: '#e6f4ff' }}>
                        <Table.Summary.Cell index={0} colSpan={2}><Text strong style={{ fontSize: 15 }}>NET PAY</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={2} align="right"><Text strong style={{ color: '#2563eb', fontSize: 15 }}>{fmt(detailDrawer.salary.net_salary)}</Text></Table.Summary.Cell>
                        <Table.Summary.Cell index={3} />
                      </Table.Summary.Row>
                    </>
                  )}
                />
              </>
            )}
          </>
        )}
      </Drawer>

      {/* Adjustment Modal */}
      <Modal
        title={`Manual Adjustment — ${adjustModal.salary?.employee_name}`}
        open={adjustModal.open}
        onOk={saveAdjustment}
        onCancel={() => setAdjustModal({ open: false, salary: null })}
        confirmLoading={adjusting}
      >
        <Alert type="warning" message="Manual adjustments mark the salary as non-final. Recalculation will overwrite them unless force_recalc is off." showIcon style={{ marginBottom: 16 }} />
        <Form form={adjustForm} layout="vertical">
          <Form.Item name="item_name" label="Item Name" rules={[{ required: true }]}><Input placeholder="e.g. Bonus, Transport Adjustment" /></Form.Item>
          <Form.Item name="new_value" label="Amount (₦)" rules={[{ required: true }]}><InputNumber style={{ width: '100%' }} /></Form.Item>
          <Form.Item name="reason" label="Reason" rules={[{ required: true }]}><Input.TextArea rows={2} placeholder="Reason for adjustment (required for audit)" /></Form.Item>
        </Form>
      </Modal>

      {/* Audit Log Modal */}
      <Modal
        title={<span><AuditOutlined /> Calculation Audit Log</span>}
        open={logsVisible}
        onCancel={() => setLogsVisible(false)}
        footer={null}
        width={800}
      >
        <Table
          dataSource={logs}
          rowKey="id"
          size="small"
          columns={[
            { title: 'Emp ID', dataIndex: 'emp_id', key: 'emp', width: 80 },
            { title: 'Period', dataIndex: 'period_id', key: 'period', width: 80 },
            { title: 'Type', dataIndex: 'calc_type', key: 'type', width: 100 },
            { title: 'Success', dataIndex: 'success', key: 'ok', width: 80, render: v => v ? <CheckCircleOutlined style={{ color: '#16a34a' }} /> : <CloseCircleOutlined style={{ color: '#dc2626' }} /> },
            { title: 'Time', dataIndex: 'created_at', key: 'time', width: 160, render: v => v ? new Date(v).toLocaleString() : '—' },
            { title: 'Error', dataIndex: 'error_message', key: 'err', render: v => v ? <Text type="danger" style={{ fontSize: 11 }}>{v}</Text> : '—' },
          ]}
          pagination={{ pageSize: 15 }}
        />
      </Modal>

      <style>{`
        .row-calc-calculated > td { background: rgba(22,163,74,0.03) !important; }
        .row-calc-failed > td { background: rgba(220,38,38,0.04) !important; }
        .row-calc-pending > td { background: rgba(217,119,6,0.03) !important; }
      `}</style>
    </div>
  );
};

export default CalculationTab;
