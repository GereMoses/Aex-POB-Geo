import React, { useState } from 'react';
import {
  Row, Col, Button, Select, Table, Space, App,
  Alert, Typography, Tabs, Spin,
} from 'antd';
import {
  BarChartOutlined, PieChartOutlined, LineChartOutlined,
  DownloadOutlined, DollarOutlined,
} from '@ant-design/icons';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTip,
  Legend, ResponsiveContainer, PieChart, Pie, Cell, LineChart, Line,
} from 'recharts';
import { apiCall, fmt, downloadBlob } from '../payrollApi';

const { Option } = Select;
const { Text } = Typography;

const COLORS = ['#1d4ed8', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#be123c', '#ca8a04'];

const ITEM_TYPE_CFG = {
  earning:   { color: '#16a34a', bg: '#f0fdf4', border: '#bbf7d0', label: 'Earning'   },
  deduction: { color: '#dc2626', bg: '#fef2f2', border: '#fecaca', label: 'Deduction' },
};

const TypePill = ({ type }) => {
  const cfg = ITEM_TYPE_CFG[type] || { color: '#64748b', bg: '#f8fafc', border: '#e2e8f0', label: type };
  return (
    <span style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: cfg.color, background: cfg.bg, border: `1px solid ${cfg.border}` }}>
      {cfg.label}
    </span>
  );
};

const MetricBox = ({ label, value, color }) => (
  <div style={{ flex: 1, padding: '10px 14px', borderRadius: 8, background: `${color}0d`, border: `1px solid ${color}30` }}>
    <div style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>{label}</div>
    <div style={{ fontSize: 18, fontWeight: 700, color }}>{value}</div>
  </div>
);

const ReportsTab = ({ periods }) => {
  const { message } = App.useApp();
  const [activeReport, setActiveReport] = useState('summary');
  const [selectedPeriodId, setSelectedPeriodId] = useState(null);
  const [secondPeriodId, setSecondPeriodId] = useState(null);
  const [groupBy, setGroupBy] = useState('department');
  const [loading, setLoading] = useState(false);
  const [reportData, setReportData] = useState(null);

  const generateReport = async () => {
    if (!selectedPeriodId) { message.warning('Select a pay period'); return; }
    setLoading(true);
    setReportData(null);
    try {
      let url;
      switch (activeReport) {
        case 'summary':    url = `/api/v1/payroll/reports/summary/?period_id=${selectedPeriodId}&group_by=${groupBy}`; break;
        case 'zone':       url = `/api/v1/payroll/reports/zone-cost/?period_id=${selectedPeriodId}`; break;
        case 'contractor': url = `/api/v1/payroll/reports/contractor-vs-staff/?period_id=${selectedPeriodId}`; break;
        case 'itemwise':   url = `/api/v1/payroll/reports/item-wise/?period_id=${selectedPeriodId}`; break;
        case 'variance':
          if (!secondPeriodId) { message.warning('Select both periods for variance report'); setLoading(false); return; }
          url = `/api/v1/payroll/reports/variance/?period_id=${selectedPeriodId}&compare_period_id=${secondPeriodId}`; break;
        default: return;
      }
      const data = await apiCall(url);
      setReportData(data);
    } catch (e) {
      message.error('Report failed: ' + e.message);
    } finally {
      setLoading(false);
    }
  };

  const exportReport = async () => {
    if (!selectedPeriodId || !reportData) return;
    try {
      await downloadBlob(
        `/api/v1/payroll/reports/${activeReport}/?period_id=${selectedPeriodId}&format=xlsx`,
        `payroll_${activeReport}_${selectedPeriodId}.xlsx`
      );
    } catch (e) {
      message.error(e.message);
    }
  };

  const renderSummaryReport = () => {
    if (!reportData?.groups) return null;
    const chartData = reportData.groups.map(g => ({
      name: g.group_name?.slice(0, 15) || 'Unknown',
      Gross: g.total_gross, Net: g.total_net, Deductions: g.total_deductions,
    }));
    return (
      <>
        <div style={{ display: 'flex', gap: 12, marginBottom: 16 }}>
          <MetricBox label="Total Employees" value={reportData.total_employees} color="#64748b" />
          <MetricBox label="Total Gross" value={fmt(reportData.total_gross)} color="#16a34a" />
          <MetricBox label="Total Deductions" value={fmt(reportData.total_deductions)} color="#dc2626" />
          <MetricBox label="Total Net" value={fmt(reportData.total_net)} color="#2563eb" />
        </div>
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}>Salary by {groupBy.charAt(0).toUpperCase() + groupBy.slice(1)}</Text>
          <ResponsiveContainer width="100%" height={280}>
            <BarChart data={chartData} margin={{ top: 10, right: 20, left: 20, bottom: 60 }}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" angle={-30} textAnchor="end" interval={0} tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => `₦${(v / 1000).toFixed(0)}k`} />
              <RechartsTip formatter={v => fmt(v)} />
              <Legend />
              <Bar dataKey="Gross" fill="#1d4ed8" />
              <Bar dataKey="Net" fill="#16a34a" />
              <Bar dataKey="Deductions" fill="#dc2626" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <Table
          dataSource={reportData.groups}
          rowKey="group_name"
          size="small"
          pagination={false}
          columns={[
            { title: groupBy === 'department' ? 'Department' : groupBy === 'position' ? 'Position' : 'Type', dataIndex: 'group_name', key: 'name' },
            { title: 'Employees', dataIndex: 'employee_count', key: 'count', align: 'center', width: 100 },
            { title: 'Total Gross', dataIndex: 'total_gross', key: 'gross', align: 'right', render: v => <Text style={{ color: '#16a34a' }}>{fmt(v)}</Text> },
            { title: 'Total Deductions', dataIndex: 'total_deductions', key: 'deduct', align: 'right', render: v => <Text style={{ color: '#dc2626' }}>-{fmt(v)}</Text> },
            { title: 'Total Net', dataIndex: 'total_net', key: 'net', align: 'right', render: v => <Text strong style={{ color: '#2563eb' }}>{fmt(v)}</Text> },
            { title: 'Avg Net', dataIndex: 'avg_net', key: 'avg', align: 'right', render: v => fmt(v) },
          ]}
          summary={() => (
            <Table.Summary.Row style={{ fontWeight: 600 }}>
              <Table.Summary.Cell index={0}>TOTAL</Table.Summary.Cell>
              <Table.Summary.Cell index={1} align="center">{reportData.total_employees}</Table.Summary.Cell>
              <Table.Summary.Cell index={2} align="right" style={{ color: '#16a34a' }}>{fmt(reportData.total_gross)}</Table.Summary.Cell>
              <Table.Summary.Cell index={3} align="right" style={{ color: '#dc2626' }}>-{fmt(reportData.total_deductions)}</Table.Summary.Cell>
              <Table.Summary.Cell index={4} align="right" style={{ color: '#2563eb' }}>{fmt(reportData.total_net)}</Table.Summary.Cell>
              <Table.Summary.Cell index={5} />
            </Table.Summary.Row>
          )}
        />
      </>
    );
  };

  const renderZoneReport = () => {
    if (!reportData?.zones) return null;
    const chartData = reportData.zones.map(z => ({
      name: z.zone_name?.slice(0, 12) || 'Unknown',
      'Warehouse Allowance': z.zone_allowance_cost || 0,
      'Night Premium': z.night_premium || 0,
      'Hazard Premium': z.hazard_premium || 0,
    }));
    return (
      <>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
          <MetricBox label="Total Warehouse Cost" value={fmt(reportData.total_zone_cost)} color="#d97706" />
          <MetricBox label="Total Night Premium" value={fmt(reportData.total_night_premium)} color="#7c3aed" />
          <MetricBox label="Total Hazard Premium" value={fmt(reportData.total_hazard_premium)} color="#dc2626" />
        </div>
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}>Warehouse Cost Breakdown</Text>
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis tickFormatter={v => `₦${(v / 1000).toFixed(0)}k`} />
              <RechartsTip formatter={v => fmt(v)} />
              <Legend />
              <Bar dataKey="Warehouse Allowance" fill="#d97706" stackId="a" />
              <Bar dataKey="Night Premium" fill="#7c3aed" stackId="a" />
              <Bar dataKey="Hazard Premium" fill="#dc2626" stackId="a" />
            </BarChart>
          </ResponsiveContainer>
        </div>
        <Table dataSource={reportData.zones} rowKey="zone_id" size="small" pagination={false}
          columns={[
            { title: 'Warehouse', dataIndex: 'zone_name', key: 'name' },
            { title: 'Employees', dataIndex: 'employee_count', key: 'emp', align: 'center', width: 100 },
            { title: 'Warehouse Hours', dataIndex: 'total_zone_hours', key: 'hrs', align: 'right', width: 110 },
            { title: 'Warehouse Allowance', dataIndex: 'zone_allowance_cost', key: 'allow', align: 'right', render: v => fmt(v) },
            { title: 'Night Premium', dataIndex: 'night_premium', key: 'night', align: 'right', render: v => fmt(v) },
            { title: 'Hazard Premium', dataIndex: 'hazard_premium', key: 'hazard', align: 'right', render: v => fmt(v) },
            { title: 'Total Cost', key: 'total', align: 'right', render: (_, r) => <Text strong>{fmt((r.zone_allowance_cost || 0) + (r.night_premium || 0) + (r.hazard_premium || 0))}</Text> },
          ]}
        />
      </>
    );
  };

  const renderContractorReport = () => {
    if (!reportData) return null;
    const pieData = [
      { name: 'Staff', value: reportData.staff_total_cost || 0 },
      { name: 'Contractors', value: reportData.contractor_total_cost || 0 },
    ];
    return (
      <Row gutter={16}>
        <Col xs={24} md={10}>
          <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <Text strong style={{ fontSize: 13 }}>Cost Split</Text>
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie data={pieData} cx="50%" cy="50%" outerRadius={90} dataKey="value" label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}>
                  {pieData.map((_, i) => <Cell key={i} fill={COLORS[i]} />)}
                </Pie>
                <RechartsTip formatter={v => fmt(v)} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </Col>
        <Col xs={24} md={14}>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10 }}>
            <MetricBox label="Staff Count" value={reportData.staff_count} color="#64748b" />
            <MetricBox label="Contractor Count" value={reportData.contractor_count} color="#7c3aed" />
            <MetricBox label="Staff Cost" value={fmt(reportData.staff_total_cost)} color="#2563eb" />
            <MetricBox label="Contractor Cost" value={fmt(reportData.contractor_total_cost)} color="#d97706" />
            <MetricBox label="Avg Staff Net" value={fmt(reportData.avg_staff_net)} color="#16a34a" />
            <MetricBox label="Avg Contractor Net" value={fmt(reportData.avg_contractor_net)} color="#0891b2" />
          </div>
        </Col>
      </Row>
    );
  };

  const renderItemWiseReport = () => {
    if (!reportData?.items) return null;
    return (
      <Table
        dataSource={reportData.items}
        rowKey="item_name"
        size="small"
        pagination={false}
        columns={[
          { title: 'Pay Item', dataIndex: 'item_name', key: 'name', render: v => <Text strong>{v}</Text> },
          { title: 'Type', dataIndex: 'item_type', key: 'type', width: 110, render: v => <TypePill type={v} /> },
          { title: 'Count', dataIndex: 'count', key: 'cnt', align: 'center', width: 80 },
          { title: 'Total', dataIndex: 'total', key: 'total', align: 'right', render: v => fmt(v) },
          { title: 'Average', dataIndex: 'average', key: 'avg', align: 'right', render: v => fmt(v) },
          { title: 'Min', dataIndex: 'min_value', key: 'min', align: 'right', render: v => fmt(v) },
          { title: 'Max', dataIndex: 'max_value', key: 'max', align: 'right', render: v => fmt(v) },
        ]}
      />
    );
  };

  const renderVarianceReport = () => {
    if (!reportData?.employees) return null;
    const chartData = reportData.employees.slice(0, 20).map(e => ({
      name: e.employee_name?.split(' ')[0] || '',
      Current: e.current_net || 0,
      Previous: e.previous_net || 0,
    }));
    const avgPct = reportData.avg_variance_pct || 0;
    return (
      <>
        <div style={{ display: 'flex', gap: 12, marginBottom: 12 }}>
          <MetricBox label="Avg Change %" value={`${avgPct.toFixed(1)}%`} color={avgPct >= 0 ? '#16a34a' : '#dc2626'} />
          <MetricBox label="Increased" value={reportData.increased_count || 0} color="#16a34a" />
          <MetricBox label="Decreased" value={reportData.decreased_count || 0} color="#dc2626" />
        </div>
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 13 }}>Net Pay Comparison (top 20)</Text>
          <ResponsiveContainer width="100%" height={260}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" tick={{ fontSize: 10 }} />
              <YAxis tickFormatter={v => `₦${(v / 1000).toFixed(0)}k`} />
              <RechartsTip formatter={v => fmt(v)} />
              <Legend />
              <Line type="monotone" dataKey="Previous" stroke="#7c3aed" strokeDasharray="5 5" />
              <Line type="monotone" dataKey="Current" stroke="#2563eb" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
        <Table
          dataSource={reportData.employees}
          rowKey="emp_id"
          size="small"
          pagination={{ pageSize: 15 }}
          columns={[
            { title: 'Employee', dataIndex: 'employee_name', key: 'name' },
            { title: 'Previous Net', dataIndex: 'previous_net', key: 'prev', align: 'right', render: v => fmt(v) },
            { title: 'Current Net', dataIndex: 'current_net', key: 'curr', align: 'right', render: v => <Text strong>{fmt(v)}</Text> },
            { title: 'Variance', key: 'var', align: 'right', render: (_, r) => { const diff = (r.current_net || 0) - (r.previous_net || 0); return <Text style={{ color: diff >= 0 ? '#16a34a' : '#dc2626' }}>{diff >= 0 ? '+' : ''}{fmt(diff)}</Text>; } },
            { title: '% Change', dataIndex: 'variance_pct', key: 'pct', align: 'right', width: 100, render: v => <Text style={{ color: (v || 0) >= 0 ? '#16a34a' : '#dc2626' }}>{(v || 0).toFixed(1)}%</Text> },
          ]}
        />
      </>
    );
  };

  const reportRenders = {
    summary: renderSummaryReport,
    zone: renderZoneReport,
    contractor: renderContractorReport,
    itemwise: renderItemWiseReport,
    variance: renderVarianceReport,
  };

  return (
    <div>
      {/* Controls row */}
      <div style={{ display: 'flex', gap: 10, alignItems: 'center', flexWrap: 'wrap', marginBottom: 16 }}>
        <Select
          placeholder="Select Pay Period"
          style={{ minWidth: 220 }}
          onChange={setSelectedPeriodId}
          value={selectedPeriodId}
          showSearch
        >
          {periods.map(p => <Option key={p.id} value={p.id}>{p.period_name}</Option>)}
        </Select>

        {activeReport === 'variance' && (
          <Select
            placeholder="Compare with Period"
            style={{ minWidth: 200 }}
            onChange={setSecondPeriodId}
            value={secondPeriodId}
            showSearch
          >
            {periods.filter(p => p.id !== selectedPeriodId).map(p => (
              <Option key={p.id} value={p.id}>{p.period_name}</Option>
            ))}
          </Select>
        )}

        {activeReport === 'summary' && (
          <Select value={groupBy} onChange={setGroupBy} style={{ width: 150 }}>
            <Option value="department">By Department</Option>
            <Option value="position">By Position</Option>
            <Option value="employee_type">By Type</Option>
          </Select>
        )}

        <Space>
          <Button type="primary" icon={<BarChartOutlined />} onClick={generateReport} loading={loading}>Generate</Button>
          {reportData && <Button icon={<DownloadOutlined />} onClick={exportReport}>Export</Button>}
        </Space>
      </div>

      <Tabs
        activeKey={activeReport}
        onChange={k => { setActiveReport(k); setReportData(null); }}
        size="small"
        style={{ marginBottom: 12 }}
        items={[
          { key: 'summary',    label: <span><BarChartOutlined /> Salary Summary</span>        },
          { key: 'zone',       label: <span><DollarOutlined /> Warehouse Cost (POB)</span>         },
          { key: 'contractor', label: <span><PieChartOutlined /> Contractor vs Staff</span>   },
          { key: 'itemwise',   label: <span><BarChartOutlined /> Item-wise</span>             },
          { key: 'variance',   label: <span><LineChartOutlined /> Period Variance</span>      },
        ]}
      />

      <div>
        {loading ? (
          <div style={{ textAlign: 'center', padding: 60 }}><Spin size="large" tip="Generating report…" /></div>
        ) : !reportData ? (
          <Alert type="info" showIcon message="Select a period and click Generate to view the report." />
        ) : (
          reportRenders[activeReport]?.()
        )}
      </div>
    </div>
  );
};

export default ReportsTab;
