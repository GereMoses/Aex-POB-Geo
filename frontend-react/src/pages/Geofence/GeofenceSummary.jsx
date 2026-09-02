import { useState } from 'react';
import {
  Card, Row, Col, Table, Tag, Typography, Select, Space, Empty, Progress, Alert,
} from 'antd';
import { BarChart, Bar, XAxis, YAxis, Tooltip as RTooltip, ResponsiveContainer, Cell } from 'recharts';
import { UserOutlined, ShopOutlined, WarningOutlined, LoginOutlined } from '@ant-design/icons';
import { useQuery } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

const REASON_LABEL = {
  OUTSIDE_FENCE: 'Outside boundary',
  LOW_GPS_ACCURACY: 'Weak GPS signal',
  MOCK_LOCATION: 'Fake GPS app',
  ROOTED_DEVICE: 'Modified device',
  EMULATOR: 'Emulator',
  ATTESTATION_FAILED: 'Failed integrity check',
  NO_ASSIGNMENT: 'No warehouse assigned',
  NO_FENCE_CONFIGURED: 'Fence not set up',
  IMPOSSIBLE_TRAVEL: 'Impossible travel',
  STATIC_GPS: 'No GPS drift',
  IMPLAUSIBLE_ALTITUDE: 'Altitude mismatch',
  APPROACH_TELEPORT: 'Teleported to site',
  COMPOSITE_RISK: 'Multiple spoof signals',
  MISSING_SELFIE: 'Photo not provided',
};

// Signals that indicate deliberate tampering rather than a bad signal or a
// misplaced fence. These are the ones worth putting in front of HR.
const DELIBERATE = new Set([
  'MOCK_LOCATION', 'EMULATOR', 'ATTESTATION_FAILED', 'IMPOSSIBLE_TRAVEL',
  'STATIC_GPS', 'IMPLAUSIBLE_ALTITUDE', 'APPROACH_TELEPORT', 'COMPOSITE_RISK',
]);

export default function GeofenceSummary() {
  const [days, setDays] = useState(7);
  const [zoneFilter, setZoneFilter] = useState(null);

  const { data, isLoading } = useQuery({
    queryKey: ['geofence-summary', days],
    queryFn: () => apiService.get('/api/v1/geofence/exceptions/summary', { days }),
  });

  // Derived from punches, not a stored counter — so it cannot drift out of
  // step with the attendance record.
  const { data: occupancy } = useQuery({
    queryKey: ['geofence-occupancy'],
    queryFn: () => apiService.get('/api/v1/geofence/occupancy'),
    refetchInterval: 30000,
  });

  const byReason = data?.by_reason ?? [];
  const bySiteAll = data?.by_site ?? [];
  // Narrow the per-warehouse breakdown; the headline counts stay estate-wide so
  // a filtered view still shows what it is a share of.
  const bySite = zoneFilter ? bySiteAll.filter((r) => r.code === zoneFilter) : bySiteAll;
  const offenders = data?.repeat_offenders ?? [];

  const deliberate = byReason.filter((r) => DELIBERATE.has(r.reason))
                             .reduce((sum, r) => sum + r.count, 0);
  const total = byReason.reduce((sum, r) => sum + r.count, 0);

  const chartData = byReason.map((r) => ({
    name: REASON_LABEL[r.reason] || r.reason,
    count: r.count,
    deliberate: DELIBERATE.has(r.reason),
  }));

  return (
    <Space direction="vertical" size={16} style={{ width: '100%' }}>
      <Row justify="end">
        <Space wrap>
        <Select size="small" allowClear placeholder="All warehouses" value={zoneFilter}
                onChange={setZoneFilter} style={{ width: 190 }} showSearch
                optionFilterProp="label"
                options={bySiteAll.map((r) => ({ value: r.code, label: r.name }))} />
        <Select size="small" value={days} onChange={setDays} style={{ width: 140 }}
                options={[
                  { value: 1, label: 'Last 24 hours' },
                  { value: 7, label: 'Last 7 days' },
                  { value: 30, label: 'Last 30 days' },
                  { value: 90, label: 'Last 90 days' },
                ]} />
        </Space>
      </Row>

      {deliberate > 0 && (
        <Alert
          type="warning" showIcon
          message={`${deliberate} of ${total} blocked punches show signs of deliberate tampering`}
          description="Weak-signal and unconfigured-fence rejections are operational problems. The ones counted here are not — they indicate an attempt to defeat the location check."
        />
      )}

      <Card size="small" title={<Space><LoginOutlined />On site right now</Space>}
            extra={<Text type="secondary" style={{ fontSize: 12 }}>
              {occupancy?.total_on_site ?? 0} of {occupancy?.total_assigned ?? 0} assigned staff
            </Text>}>
        <Row gutter={12}>
          {(occupancy?.sites ?? []).map((s) => (
            <Col key={s.zone_id} xs={12} sm={8} md={6} lg={4}>
              <Card size="small" styles={{ body: { padding: 12, textAlign: 'center' } }}>
                <Text type="secondary" style={{ fontSize: 11 }}>{s.code}</Text>
                <div style={{ fontSize: 26, fontWeight: 600, lineHeight: 1.2 }}>
                  {s.on_site}
                  <Text type="secondary" style={{ fontSize: 14 }}> / {s.assigned}</Text>
                </div>
                <Text style={{ fontSize: 11 }} ellipsis>{s.name}</Text>
              </Card>
            </Col>
          ))}
          {!occupancy?.sites?.length && (
            <Col span={24}><Empty description="No fenced warehouses yet" /></Col>
          )}
        </Row>
        <Text type="secondary" style={{ fontSize: 11 }}>
          Counted from today's punches — someone whose last punch was a clock-in. Resets
          daily, so a missed clock-out on Friday is not still counted on Monday.
        </Text>
      </Card>

      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card size="small" title={<Space><WarningOutlined />Why punches were blocked</Space>}
                loading={isLoading}>
            {chartData.length ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={chartData} layout="vertical" margin={{ left: 20, right: 16 }}>
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={150} tick={{ fontSize: 12 }} />
                  <RTooltip />
                  <Bar dataKey="count" radius={[0, 4, 4, 0]}>
                    {chartData.map((entry, i) => (
                      <Cell key={i} fill={entry.deliberate ? '#EF4444' : '#F59E0B'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            ) : <Empty description="No blocked punches in this period" />}
            <Text type="secondary" style={{ fontSize: 11 }}>
              Red indicates suspected tampering; amber indicates a signal or configuration problem.
            </Text>
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card size="small" title={<Space><ShopOutlined />Warehouses by block rate</Space>}
                loading={isLoading}>
            <Table
              rowKey="zone_id" size="small" pagination={false} dataSource={bySite}
              scroll={{ y: 260 }}
              locale={{ emptyText: <Empty description="No blocked punches" /> }}
              columns={[
                { title: 'Warehouse', dataIndex: 'zone_name', render: (n) => n || '—' },
                { title: 'Blocked', dataIndex: 'blocked', width: 90,
                  render: (b, r) => <Text>{b} / {r.total_punches}</Text> },
                { title: 'Rate', dataIndex: 'blocked_rate', width: 130,
                  render: (rate) => (
                    <Progress percent={Math.round(rate * 100)} size="small"
                              status={rate > 0.5 ? 'exception' : 'normal'} />
                  ) },
              ]}
            />
            <Text type="secondary" style={{ fontSize: 11 }}>
              A site blocking most of its punches almost always has a badly placed or
              undersized fence rather than a workforce problem — check the boundary first.
            </Text>
          </Card>
        </Col>
      </Row>

      <Card size="small" title={<Space><UserOutlined />Repeat blocked clock-ins</Space>}
            loading={isLoading}>
        <Table
          rowKey="emp_code" size="small" dataSource={offenders}
          pagination={{ pageSize: 10, showSizeChanger: false }}
          locale={{ emptyText: <Empty description="Nobody has been blocked on more than one day" /> }}
          columns={[
            { title: 'Employee', dataIndex: 'employee_name',
              render: (n, r) => (
                <Space direction="vertical" size={0}>
                  <Text strong style={{ fontSize: 13 }}>{n || '—'}</Text>
                  <Text type="secondary" style={{ fontSize: 11 }}>{r.emp_code}</Text>
                </Space>
              ) },
            { title: 'Days affected', dataIndex: 'days_affected', width: 130,
              sorter: (a, b) => a.days_affected - b.days_affected, defaultSortOrder: 'descend',
              render: (d) => <Tag color={d >= 3 ? 'red' : 'orange'}>{d} days</Tag> },
            { title: 'Attempts', dataIndex: 'attempts', width: 100 },
            { title: 'Peak risk', dataIndex: 'peak_risk', width: 110,
              render: (r) => <Tag color={r >= 80 ? 'red' : r >= 40 ? 'orange' : 'default'}>{r}</Tag> },
            { title: 'Last seen', dataIndex: 'last_seen', width: 180,
              render: (t) => t ? new Date(t).toLocaleString() : '—' },
          ]}
        />
        <Text type="secondary" style={{ fontSize: 11 }}>
          Counted by distinct days, not raw attempts — somebody retrying five times one
          morning is one day's problem, not five.
        </Text>
      </Card>
    </Space>
  );
}
