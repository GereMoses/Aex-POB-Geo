import React, { useState } from 'react';
import {
  Card, Row, Col, Statistic, Button, Space, Typography, Switch, InputNumber,
  Divider, Table, Tag, Alert, App, Tooltip, Spin, Empty,
} from 'antd';
import {
  DatabaseOutlined, ReloadOutlined, ThunderboltOutlined, RollbackOutlined,
  ClearOutlined, SafetyCertificateOutlined, ClockCircleOutlined, TeamOutlined,
  ApiOutlined, ExclamationCircleOutlined, ToolOutlined, DeleteOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text, Title } = Typography;

const DatabaseTab = () => {
  const { message: msg, modal } = App.useApp();
  const qc = useQueryClient();
  const [busy, setBusy] = useState('');           // which action is running
  const [autoEnabled, setAutoEnabled] = useState(false);
  const [autoDays, setAutoDays] = useState(1);
  const [retentionDraft, setRetentionDraft] = useState({});
  const [initedFromServer, setInited] = useState(false);

  // ── Queries ──
  const { data: overview, isLoading: ovLoading, refetch: refetchOverview } = useQuery({
    queryKey: ['db-overview'],
    queryFn: () => apiService.get('/api/v1/database/overview'),
    refetchInterval: 30_000,
  });
  const { data: settings } = useQuery({
    queryKey: ['db-settings'],
    queryFn: () => apiService.get('/api/v1/database/settings'),
  });
  const { data: integrity, refetch: refetchIntegrity, isFetching: integFetching } = useQuery({
    queryKey: ['db-integrity'],
    queryFn: () => apiService.get('/api/v1/database/integrity/scan'),
  });
  const { data: retentionPrev, refetch: refetchRetention, isFetching: retFetching } = useQuery({
    queryKey: ['db-retention-preview'],
    queryFn: () => apiService.get('/api/v1/database/retention/preview'),
  });

  // Seed local editable state once settings arrive
  React.useEffect(() => {
    if (settings && !initedFromServer) {
      setAutoEnabled(!!settings.auto_checkout_enabled);
      setAutoDays(settings.auto_checkout_days ?? 1);
      const rd = {};
      Object.entries(settings.retention || {}).forEach(([k, v]) => { rd[k] = v.days ?? 0; });
      setRetentionDraft(rd);
      setInited(true);
    }
  }, [settings, initedFromServer]);

  const run = async (label, fn, { danger, confirm } = {}) => {
    const go = async () => {
      setBusy(label);
      try {
        const res = await fn();
        msg.success(res?.message || 'Done');
        qc.invalidateQueries({ queryKey: ['db-overview'] });
        qc.invalidateQueries({ queryKey: ['db-integrity'] });
        qc.invalidateQueries({ queryKey: ['db-retention-preview'] });
      } catch (e) {
        msg.error(e.message || 'Failed');
      } finally { setBusy(''); }
    };
    if (confirm) {
      modal.confirm({
        title: confirm.title,
        icon: <ExclamationCircleOutlined style={{ color: danger ? '#cf1322' : undefined }} />,
        content: confirm.content,
        okText: confirm.okText || 'Proceed',
        okButtonProps: { danger },
        onOk: go,
      });
    } else { await go(); }
  };

  const saveSettings = () => run('save-settings', async () => {
    const retention = {};
    Object.entries(retentionDraft).forEach(([k, days]) => { retention[k] = { days: Number(days) || 0 }; });
    return apiService.put('/api/v1/database/settings', {
      auto_checkout_enabled: autoEnabled,
      auto_checkout_days: Number(autoDays) || 0,
      retention,
    });
  });

  const ov = overview || {};

  return (
    <div style={{ padding: 24 }}>
      {/* ── Overview ── */}
      <Title level={5}><DatabaseOutlined /> Database Overview</Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 8 }}>
        <Col xs={12} md={6}><Card size="small"><Statistic title="Database Size" value={ov.db_size || '—'} prefix={<DatabaseOutlined />} valueStyle={{ fontSize: 18 }} /></Card></Col>
        <Col xs={12} md={6}><Card size="small"><Statistic title="Tables" value={ov.table_count ?? '—'} /></Card></Col>
        <Col xs={12} md={6}><Card size="small"><Statistic title="Active Connections" value={ov.active_connections ?? '—'} prefix={<ApiOutlined />} /></Card></Col>
        <Col xs={12} md={6}><Card size="small"><Statistic title="Personnel On Board" value={ov.personnel_onboard ?? '—'} prefix={<TeamOutlined />} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={12} md={6}><Card size="small"><Statistic title="Live Warehouse Occupancy" value={ov.live_occupancy ?? '—'} prefix={<TeamOutlined />} valueStyle={{ color: (ov.live_occupancy ?? 0) === (ov.personnel_onboard ?? 0) ? undefined : '#faad14' }} /></Card></Col>
        <Col xs={12} md={6}><Card size="small"><Statistic title="PostgreSQL" value={ov.postgres_version || '—'} valueStyle={{ fontSize: 18 }} /></Card></Col>
        <Col xs={24} md={12}>
          <Button icon={<ReloadOutlined />} onClick={() => refetchOverview()} loading={ovLoading} style={{ marginTop: 4 }}>Refresh overview</Button>
          {(ov.live_occupancy ?? 0) !== (ov.personnel_onboard ?? 0) && (
            <Text type="warning" style={{ marginLeft: 12, fontSize: 12 }}>
              On-board flag ({ov.personnel_onboard}) and live occupancy ({ov.live_occupancy}) disagree — a reset will reconcile them.
            </Text>
          )}
        </Col>
      </Row>

      {/* ── Occupancy / Auto-checkout ── */}
      <Divider />
      <Title level={5}><ClockCircleOutlined /> Occupancy &amp; Auto-Checkout</Title>
      <Card size="small">
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Space wrap>
            <Switch checked={autoEnabled} onChange={setAutoEnabled} />
            <Text strong>Auto-checkout stale entries</Text>
            <Text type="secondary">— each day, check out anyone whose last punch was an entry more than</Text>
            <InputNumber min={0} max={365} value={autoDays} onChange={(v) => setAutoDays(v)} style={{ width: 70 }} disabled={!autoEnabled} addonAfter="days" />
            <Text type="secondary">ago.</Text>
          </Space>
          <Text type="secondary" style={{ fontSize: 12 }}>
            Runs daily at 03:00. People with any recent activity are never touched — only forgotten check-ins are cleared. Set days to 0 to check out same-day stragglers.
          </Text>
          <Space wrap>
            <Button type="primary" onClick={saveSettings} loading={busy === 'save-settings'}>Save settings</Button>
            <Button icon={<ThunderboltOutlined />} loading={busy === 'auto-now'}
              onClick={() => run('auto-now', () => apiService.post(`/api/v1/database/occupancy/auto-checkout?days=${Number(autoDays) || 0}`))}>
              Run auto-checkout now
            </Button>
            <Tooltip title="Instant full reset — check EVERYONE out and clear all on-board flags. Use when the facility is empty.">
              <Button danger icon={<RollbackOutlined />} loading={busy === 'reset-all'}
                onClick={() => run('reset-all', () => apiService.post('/api/v1/database/occupancy/reset'), {
                  danger: true,
                  confirm: {
                    title: 'Reset ALL occupancy?',
                    content: 'This clocks out every person and clears all on-site flags. Dashboard and Warehouse occupancy go to 0. Use only when nobody is actually on site.',
                    okText: 'Reset everything',
                  },
                })}>
                Reset all occupancy now
              </Button>
            </Tooltip>
          </Space>
        </Space>
      </Card>

      {/* ── Maintenance ── */}
      <Divider />
      <Title level={5}><ToolOutlined /> Maintenance</Title>
      <Card size="small">
        <Space wrap>
          <Tooltip title="Reclaim dead space and refresh query-planner statistics. Safe to run anytime (online).">
            <Button icon={<ThunderboltOutlined />} loading={busy === 'vacuum'}
              onClick={() => run('vacuum', () => apiService.post('/api/v1/database/maintenance/vacuum'))}>
              Optimize (VACUUM ANALYZE)
            </Button>
          </Tooltip>
          <Tooltip title="Rebuild indexes concurrently. Online but can take a while on large databases.">
            <Button icon={<ToolOutlined />} loading={busy === 'reindex'}
              onClick={() => run('reindex', () => apiService.post('/api/v1/database/maintenance/reindex'), {
                confirm: { title: 'Reindex database?', content: 'Rebuilds all indexes concurrently. This is online but may take a while.', okText: 'Reindex' },
              })}>
              Reindex
            </Button>
          </Tooltip>
        </Space>
      </Card>

      {/* ── Data retention ── */}
      <Divider />
      <Title level={5}><DeleteOutlined /> Data Retention</Title>
      <Card size="small">
        <Text type="secondary" style={{ fontSize: 12 }}>Automatically purge old records. Set days to 0 to keep forever. Applied when you click “Purge now”.</Text>
        <div style={{ marginTop: 12 }}>
          {Object.entries(settings?.retention || {}).map(([k, v]) => (
            <div key={k} style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
              <Text style={{ width: 200 }}>{v.label}</Text>
              <Text type="secondary">delete after</Text>
              <InputNumber min={0} max={3650} value={retentionDraft[k] ?? 0}
                onChange={(val) => setRetentionDraft((d) => ({ ...d, [k]: val }))} style={{ width: 90 }} addonAfter="days" />
              {retentionPrev?.items?.find((i) => i.key === k) && (
                <Tag color="orange">{retentionPrev.items.find((i) => i.key === k).rows_to_delete} to delete</Tag>
              )}
            </div>
          ))}
        </div>
        <Space wrap style={{ marginTop: 8 }}>
          <Button type="primary" onClick={saveSettings} loading={busy === 'save-settings'}>Save retention</Button>
          <Button icon={<ReloadOutlined />} loading={retFetching} onClick={() => refetchRetention()}>Preview</Button>
          <Button danger icon={<DeleteOutlined />} loading={busy === 'purge'}
            disabled={!(retentionPrev?.total_rows > 0)}
            onClick={() => run('purge', () => apiService.post('/api/v1/database/retention/purge'), {
              danger: true,
              confirm: { title: 'Purge old records?', content: `This permanently deletes ${retentionPrev?.total_rows || 0} record(s) per your retention policy. This cannot be undone.`, okText: 'Purge' },
            })}>
            Purge now {retentionPrev?.total_rows > 0 ? `(${retentionPrev.total_rows})` : ''}
          </Button>
        </Space>
      </Card>

      {/* ── Integrity ── */}
      <Divider />
      <Title level={5}><SafetyCertificateOutlined /> Integrity &amp; Self-Heal</Title>
      <Card size="small">
        {integFetching ? <Spin /> : (integrity?.items?.length ? (
          <Table
            size="small" pagination={false} rowKey="key"
            dataSource={integrity.items}
            columns={[
              { title: 'Check', dataIndex: 'label', key: 'label' },
              { title: 'Found', dataIndex: 'count', key: 'count', width: 90,
                render: (c) => <Tag color={c > 0 ? 'red' : 'green'}>{c}</Tag> },
              { title: '', key: 'fixable', width: 110,
                render: (_, r) => r.fixable ? <Text type="secondary" style={{ fontSize: 11 }}>auto-fixable</Text>
                  : <Text type="secondary" style={{ fontSize: 11 }}>informational</Text> },
            ]}
          />
        ) : <Empty description="No scan yet" image={Empty.PRESENTED_IMAGE_SIMPLE} />)}
        <Space wrap style={{ marginTop: 12 }}>
          <Button icon={<ReloadOutlined />} loading={integFetching} onClick={() => refetchIntegrity()}>Scan now</Button>
          <Button type="primary" icon={<SafetyCertificateOutlined />} loading={busy === 'fix'}
            disabled={!(integrity?.items?.some((i) => i.fixable && i.count > 0))}
            onClick={() => run('fix', () => apiService.post('/api/v1/database/integrity/fix'), {
              confirm: { title: 'Fix issues?', content: 'Repairs the auto-fixable items (removes future-dated punches, nulls references to deleted zones). Informational items are left alone.', okText: 'Fix' },
            })}>
            Fix issues
          </Button>
        </Space>
      </Card>

      {/* ── Largest tables ── */}
      <Divider />
      <Title level={5}>Largest Tables</Title>
      <Table
        size="small" pagination={false} rowKey="name" loading={ovLoading}
        dataSource={ov.largest_tables || []}
        columns={[
          { title: 'Table', dataIndex: 'name', key: 'name', render: (v) => <Text style={{ fontFamily: 'monospace', fontSize: 12 }}>{v}</Text> },
          { title: 'Size', dataIndex: 'size', key: 'size', width: 120 },
          { title: 'Rows', dataIndex: 'rows', key: 'rows', width: 120, render: (v) => v.toLocaleString() },
        ]}
      />
    </div>
  );
};

export default DatabaseTab;
