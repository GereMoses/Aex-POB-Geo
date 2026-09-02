import React, { useState, useCallback, useMemo } from 'react';
import {
  Table, Button, Space, Tag, App, Popconfirm,
  Select, DatePicker, Row, Col, Divider, Descriptions,
  Tooltip, Input, Badge, Drawer, Typography,
} from 'antd';
import {
  ReloadOutlined, SearchOutlined, EyeOutlined,
  DatabaseOutlined, SyncOutlined, ClockCircleOutlined,
  DeleteOutlined, DownloadOutlined, FilterOutlined,
  CheckCircleOutlined, WarningOutlined, CloseOutlined,
  TeamOutlined, LoginOutlined, LogoutOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../../services/api';
import dayjs from 'dayjs';
import { VERIFY_TYPE, PUNCH_STATE, vLabel, pState, resolvedPunchState, EmployeeCell, tableContainerStyle } from './shared';

const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text } = Typography;

/* ---- Row highlight rules ---- */
const rowClassName = (r) => {
  if (r.is_first_in)         return 'txn-row-first-in';
  if (r.is_last_out)         return 'txn-row-last-out';
  if (r.verify_type === 200) return 'txn-row-mobile';
  if (r._duplicate)          return 'txn-row-duplicate';
  return '';
};

/* ---- CSV export ---- */
const exportCSV = (rows) => {
  const headers = ['ID','Emp Code','Employee','Punch Time','Type','Verify','Terminal','Area','Work Code','Upload Time','Department'];
  const lines   = rows.map(r => [
    r.id, r.emp_code, r.emp_name,
    r.punch_time ? dayjs(r.punch_time).format('YYYY-MM-DD HH:mm:ss') : '',
    pState(r.punch_state).label,
    vLabel(r.verify_type).label,
    r.terminal_sn || '', r.area_alias || '',
    r.work_code || '',
    r.upload_time ? dayjs(r.upload_time).format('YYYY-MM-DD HH:mm:ss') : '',
    r.dept_name || '',
  ].map(v => `"${String(v).replace(/"/g,'""')}"`).join(','));
  const blob = new Blob([[headers.join(','), ...lines].join('\n')], { type:'text/csv' });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement('a');
  a.href = url;
  a.download = `transactions_${dayjs().format('YYYYMMDD_HHmmss')}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};

const PAGE_SIZE = 100;

const TransactionsTab = () => {
  const { message } = App.useApp();
  const qc = useQueryClient();

  const [search,     setSearch]     = useState('');
  const [terminal,   setTerminal]   = useState('');
  const [areaSearch, setAreaSearch] = useState('');
  const [areaId,     setAreaId]     = useState(null);
  const [verifyType, setVerifyType] = useState(null);
  const [punchState, setPunchState] = useState(null);
  const [deptId,     setDeptId]     = useState(null);
  const [dateRange,  setDateRange]  = useState([dayjs().startOf('week'), dayjs().endOf('week')]);
  const [page,       setPage]       = useState(1);
  const [selected,   setSelected]   = useState([]);
  const [detailOpen, setDetailOpen] = useState(false);
  const [detailId,   setDetailId]   = useState(null);

  const startDate = dateRange?.[0]?.format('YYYY-MM-DD') ?? dayjs().startOf('week').format('YYYY-MM-DD');
  const endDate   = dateRange?.[1]?.format('YYYY-MM-DD') ?? dayjs().endOf('week').format('YYYY-MM-DD');

  const rangePresets = [
    { label: 'Today',      value: [dayjs(), dayjs()] },
    { label: 'Yesterday',  value: [dayjs().subtract(1, 'day'), dayjs().subtract(1, 'day')] },
    { label: 'This Week',  value: [dayjs().startOf('week'),  dayjs().endOf('week')]  },
    { label: 'Last Week',  value: [dayjs().subtract(1, 'week').startOf('week'), dayjs().subtract(1, 'week').endOf('week')] },
    { label: 'This Month', value: [dayjs().startOf('month'), dayjs().endOf('month')] },
    { label: 'Last Month', value: [dayjs().subtract(1, 'month').startOf('month'), dayjs().subtract(1, 'month').endOf('month')] },
  ];

  const buildParams = useCallback(() => {
    const p = new URLSearchParams();
    if (search)               p.append('search',      search);
    if (terminal)             p.append('terminal_sn', terminal);
    if (areaSearch)           p.append('area_alias',  areaSearch);
    if (areaId)               p.append('area_id',     areaId);
    if (verifyType !== null)  p.append('verify_type', verifyType);
    if (punchState !== null)  p.append('punch_state', punchState);
    if (deptId)               p.append('dept_id',     deptId);
    p.append('start_date', startDate);
    p.append('end_date',   endDate);
    return p;
  }, [search, terminal, areaSearch, areaId, verifyType, punchState, deptId, startDate, endDate]);

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['att-transactions', search, terminal, areaSearch, areaId, verifyType, punchState, deptId, startDate, endDate, page],
    queryFn: () => {
      const p = buildParams();
      p.append('page',      page);
      p.append('page_size', PAGE_SIZE);
      return apiService.get(`/api/v1/attendance/transactions?${p}`);
    },
    refetchInterval: 15000,
    staleTime:       10000,
  });
  const rows     = data?.data  || [];
  const total    = data?.total ?? rows.length;
  const stats    = data?.stats ?? {};
  const detailRec = useMemo(() => rows.find(r => r.id === detailId) ?? null, [rows, detailId]);

  const { data: deptData } = useQuery({
    queryKey: ['departments'],
    queryFn:  () => apiService.get('/api/v1/departments/'),
  });
  const departments = Array.isArray(deptData) ? deptData : (deptData?.data || deptData?.results || []);

  const { data: areasData } = useQuery({
    queryKey: ['ta-areas'],
    // Warehouses replaced the old device areas as the location filter.
    queryFn:  () => apiService.get('/api/v1/zones/dashboard'),
    staleTime: 60000,
  });
  const areas = Array.isArray(areasData) ? areasData : [];

  const deleteOneM = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/attendance/transactions/${id}`),
    onSuccess: () => { message.success('Transaction deleted'); setSelected([]); qc.invalidateQueries(['att-transactions']); },
    onError:   (e) => message.error(e?.message || 'Delete failed'),
  });

  const bulkDeleteM = useMutation({
    mutationFn: (ids) => apiService.delete('/api/v1/attendance/transactions', ids),
    onSuccess: (_,ids) => { message.success(`${ids.length} transaction(s) deleted`); setSelected([]); qc.invalidateQueries(['att-transactions']); },
    onError:   (e) => message.error(e?.message || 'Bulk delete failed'),
  });

  const reprocessM = useMutation({
    mutationFn: (row) => {
      const punchDate = dayjs(row.punch_time).format('YYYY-MM-DD');
      return apiService.post('/api/v1/attendance/transactions/reprocess', {
        emp_ids:    row.emp_id ? [row.emp_id] : null,
        start_date: punchDate,
        end_date:   punchDate,
      });
    },
    onSuccess: () => { message.success('Transaction reprocessed'); qc.invalidateQueries(['att-transactions']); },
    onError:   (e) => message.error(e?.message || 'Reprocess failed'),
  });

  const resetFilters = useCallback(() => {
    setSearch(''); setTerminal(''); setAreaSearch(''); setAreaId(null);
    setVerifyType(null); setPunchState(null); setDeptId(null);
    setDateRange([dayjs().startOf('week'), dayjs().endOf('week')]); setPage(1); setSelected([]);
  }, []);

  const defaultStart = dayjs().startOf('week').format('YYYY-MM-DD');
  const defaultEnd   = dayjs().endOf('week').format('YYYY-MM-DD');
  const hasFilters = !!(search || terminal || areaSearch || areaId || verifyType !== null || punchState !== null || deptId
    || startDate !== defaultStart || endDate !== defaultEnd);

  const cols = [
    {
      title: 'Employee', key: 'employee', width: 200,
      render: (_, r) => (
        <EmployeeCell
          name={r.emp_name}
          code={r.emp_code}
          dept={r.dept_name}
          onClick={() => { setDetailId(r.id); setDetailOpen(true); }}
        />
      ),
    },
    {
      title: 'Punch Time', dataIndex: 'punch_time', key: 'pt', width: 170, sorter: true,
      render: d => d ? (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize:13 }}>{dayjs(d).format('DD MMM YYYY')}</Text>
          <Text style={{ fontSize:12, color:'#1890ff', fontFamily:'monospace' }}>{dayjs(d).format('HH:mm:ss')}</Text>
        </Space>
      ) : '—',
    },
    {
      title: 'Type', key: 'ps', width: 160,
      render: (_, r) => {
        const p = resolvedPunchState(r.punch_state, r.classified_direction);
        return (
          <Space direction="vertical" size={1}>
            <Badge status={p.status} text={<span style={{ color:p.color, fontWeight:500 }}>{p.label}</span>} />
            {p.inferred && <span style={{ fontSize:10, color:'#8c8c8c' }}>auto-classified</span>}
            {r.is_first_in && (
              <Tag color="blue" icon={<LoginOutlined />} style={{ fontSize:10, padding:'0 5px', margin:0 }}>
                First In
              </Tag>
            )}
            {r.is_last_out && (
              <Tag color="red" icon={<LogoutOutlined />} style={{ fontSize:10, padding:'0 5px', margin:0 }}>
                Last Out
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Shift', key: 'shift', width: 150,
      render: (_, r) => r.shift_name ? (
        <Space direction="vertical" size={0}>
          <Tag color="blue" style={{ fontSize:11 }}>{r.shift_name}</Tag>
          {(r.shift_start || r.shift_end) && (
            <Text style={{ fontSize:10, color:'#8c8c8c', fontFamily:'monospace' }}>
              {(r.shift_start||'').slice(0,5)} – {(r.shift_end||'').slice(0,5)}
            </Text>
          )}
        </Space>
      ) : <Text type="secondary" style={{ fontSize:11 }}>No shift</Text>,
    },
    {
      title: 'Verify Method', dataIndex: 'verify_type', key: 'vt', width: 130,
      render: v => {
        const t = vLabel(v);
        return <Tag color={t.color} style={{ background: t.bg }}>{t.label}</Tag>;
      },
    },
    {
      title: 'Terminal', dataIndex: 'terminal_sn', key: 'tsn', width: 130,
      render: v => v ? <Tag style={{ fontFamily:'monospace', fontSize:11 }}>{v}</Tag> : <Text type="secondary">—</Text>,
    },
    {
      title: 'Area', key: 'area', width: 130,
      render: (_, r) => {
        const sys = r.area_name;
        const alias = r.area_alias;
        if (sys)   return <Tag color="geekblue">{sys}</Tag>;
        if (alias) return <Tag color="default" style={{ fontSize:11 }}>{alias}</Tag>;
        return <Text type="secondary">—</Text>;
      },
    },
    {
      title: 'Upload Time', dataIndex: 'upload_time', key: 'ut', width: 145,
      render: d => d ? <Text style={{ fontSize:12, color:'#8c8c8c' }}>{dayjs(d).format('DD MMM HH:mm:ss')}</Text> : '—',
    },
    {
      title: 'Actions', key: 'act', fixed: 'right', width: 110,
      render: (_, r) => (
        <Space size={4}>
          <Tooltip title="View details">
            <Button size="small" icon={<EyeOutlined />}
              onClick={() => { setDetailId(r.id); setDetailOpen(true); }} />
          </Tooltip>
          <Tooltip title="Reprocess">
            <Button size="small" icon={<SyncOutlined />}
              onClick={() => reprocessM.mutate(r)}
              loading={reprocessM.isPending && reprocessM.variables?.id === r.id} />
          </Tooltip>
          <Popconfirm title="Delete this transaction?" okText="Delete" okButtonProps={{ danger:true }}
            onConfirm={() => deleteOneM.mutate(r.id)}>
            <Tooltip title="Delete">
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  const rowSelection = {
    selectedRowKeys: selected,
    onChange: setSelected,
    selections: [Table.SELECTION_ALL, Table.SELECTION_INVERT, Table.SELECTION_NONE],
  };

  return (
    <div style={{ padding:24 }}>
      <style>{`
        .txn-row-first-in  td { background: #e6f7ff !important; }
        .txn-row-last-out  td { background: #fff1f0 !important; }
        .txn-row-first-in:hover  td { background: #bae0ff !important; }
        .txn-row-last-out:hover  td { background: #ffd6d6 !important; }
        .txn-row-mobile    td { background: #f6ffed !important; }
        .txn-row-duplicate td { background: #fff2f0 !important; }
        .txn-row-mobile:hover    td { background: #d9f7be !important; }
        .txn-row-duplicate:hover td { background: #ffccc7 !important; }
        .txn-mod-table .ant-table-thead .ant-table-cell {
          background: #f8fafc !important; color: #64748b !important;
          font-size: 11px !important; font-weight: 700 !important;
          text-transform: uppercase !important; letter-spacing: 0.5px !important;
          border-bottom: 2px solid #e2e8f0 !important;
        }
      `}</style>

      {/* ── Stat cards ── */}
      <Row gutter={[10, 10]} style={{ marginBottom: 16 }}>
        {[
          { title: "Today's Punches",  value: stats.today_count      ?? '—', icon: <ClockCircleOutlined />, color: '#722ed1', bg: '#F9F0FF', border: '#D3ADF7' },
          { title: 'Check-ins',        value: stats.checkin_count    ?? '—', icon: <LoginOutlined />,       color: '#52c41a', bg: '#F6FFED', border: '#B7EB8F' },
          { title: 'Check-outs',       value: stats.checkout_count   ?? '—', icon: <LogoutOutlined />,      color: '#f5222d', bg: '#FFF1F0', border: '#FFA39E' },
          { title: 'Employees',        value: stats.unique_employees ?? '—', icon: <TeamOutlined />,        color: '#0891b2', bg: '#ECFEFF', border: '#67E8F9' },
          { title: 'Mobile',           value: stats.mobile_count     ?? '—', icon: <WarningOutlined />,     color: '#fa8c16', bg: '#FFF7E6', border: '#FFD591' },
          { title: 'Total Records',    value: total,                         icon: <DatabaseOutlined />,    color: '#1890ff', bg: '#E6F4FF', border: '#91CAFF' },
        ].map(s => (
          <Col xs={12} sm={8} md={4} key={s.title}>
            <div style={{
              background: '#fff',
              borderRadius: 10,
              border: `1px solid ${s.border}`,
              padding: '14px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              boxShadow: `0 1px 6px ${s.color}12`,
            }}>
              <div style={{
                width: 42, height: 42, borderRadius: 10, flexShrink: 0,
                background: s.bg,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
              }}>
                {React.cloneElement(s.icon, { style: { fontSize: 20, color: s.color } })}
              </div>
              <div>
                <div style={{ fontSize: 26, fontWeight: 800, color: s.color, lineHeight: 1 }}>
                  {isLoading ? '…' : s.value}
                </div>
                <div style={{ color: '#8c8c8c', fontSize: 12, fontWeight: 500, marginTop: 3 }}>
                  {s.title}
                </div>
              </div>
            </div>
          </Col>
        ))}
      </Row>

      {/* ── Filter bar ── */}
      <div style={{ background:'#fff', border:'1px solid #e2e8f0', borderRadius:12, padding:'12px 16px', marginBottom:16 }}>
        <Row gutter={[10,8]} align="middle">
          <Col xs={24} sm={8} md={5}>
            <Input placeholder="Search employee name / code…"
              prefix={<SearchOutlined style={{ color:'#94a3b8' }} />} value={search}
              onChange={e => { setSearch(e.target.value); setPage(1); }} allowClear />
          </Col>
          <Col xs={12} sm={5} md={3}>
            <Select placeholder="Punch type" style={{ width:'100%' }} value={punchState}
              onChange={v => { setPunchState(v); setPage(1); }} allowClear>
              {Object.entries(PUNCH_STATE).map(([k,v]) =>
                <Option key={k} value={Number(k)}>
                  <Badge status={v.status} text={v.label} />
                </Option>
              )}
            </Select>
          </Col>
          <Col xs={12} sm={5} md={3}>
            <Select placeholder="Verify method" style={{ width:'100%' }} value={verifyType}
              onChange={v => { setVerifyType(v); setPage(1); }} allowClear>
              {[...new Map(Object.entries(VERIFY_TYPE).map(([k,v]) => [v.label, {k,v}])).values()]
                .map(({k,v}) => <Option key={k} value={Number(k)}><Tag color={v.color}>{v.label}</Tag></Option>)}
            </Select>
          </Col>
          <Col xs={12} sm={5} md={3}>
            <Select placeholder="Department" style={{ width:'100%' }} value={deptId}
              onChange={v => { setDeptId(v); setPage(1); }} allowClear showSearch optionFilterProp="children">
              {departments.map(d => <Option key={d.id} value={d.id}>{d.dept_name||d.name}</Option>)}
            </Select>
          </Col>
          <Col xs={12} sm={5} md={3}>
            <Input placeholder="Terminal S/N…" value={terminal}
              onChange={e => { setTerminal(e.target.value); setPage(1); }} allowClear />
          </Col>
          <Col xs={12} sm={5} md={3}>
            <Select placeholder="Filter by Area" style={{ width: '100%' }} value={areaId}
              onChange={v => { setAreaId(v); setPage(1); }} allowClear showSearch optionFilterProp="children">
              {areas.map(a => <Option key={a.id} value={a.id}>{a.name}</Option>)}
            </Select>
          </Col>
          <Col xs={24} sm={10} md={6}>
            <RangePicker
              style={{ width:'100%' }}
              value={dateRange}
              presets={rangePresets}
              onChange={v => { if (v) { setDateRange(v); setPage(1); } }}
              format="DD MMM YYYY"
              allowClear={false}
            />
          </Col>
          <Col>
            <Space>
              {hasFilters && (
                <Tooltip title="Clear all filters">
                  <Button icon={<FilterOutlined />} onClick={resetFilters}>Clear</Button>
                </Tooltip>
              )}
              <Button icon={<ReloadOutlined />} onClick={() => refetch()} loading={isLoading}>Refresh</Button>
            </Space>
          </Col>
        </Row>
      </div>

      {/* ── Bulk action bar ── */}
      {selected.length > 0 && (
        <div style={{ background:'#1d4ed8', borderRadius:10, padding:'10px 16px', marginBottom:12, display:'flex', alignItems:'center', justifyContent:'space-between' }}>
          <span style={{ color:'#fff', fontWeight:600, fontSize:13 }}>
            {selected.length} transaction{selected.length !== 1 ? 's' : ''} selected
          </span>
          <Space>
            <Button icon={<DownloadOutlined />} size="small"
              style={{ background:'rgba(255,255,255,0.15)', border:'1px solid rgba(255,255,255,0.3)', color:'#fff' }}
              onClick={() => exportCSV(rows.filter(r => selected.includes(r.id)))}>
              Export Selected
            </Button>
            <Popconfirm
              title={`Delete ${selected.length} selected transaction(s)?`}
              description="This action cannot be undone."
              okText="Delete All" okButtonProps={{ danger:true }}
              onConfirm={() => bulkDeleteM.mutate(selected)}>
              <Button danger size="small" icon={<DeleteOutlined />}
                style={{ background:'rgba(239,68,68,0.2)', border:'1px solid rgba(239,68,68,0.4)', color:'#fca5a5' }}
                loading={bulkDeleteM.isPending}>
                Delete {selected.length}
              </Button>
            </Popconfirm>
            <Button size="small" icon={<CloseOutlined />}
              style={{ background:'rgba(255,255,255,0.15)', border:'none', color:'#fff' }}
              onClick={() => setSelected([])}>
              Clear
            </Button>
          </Space>
        </div>
      )}

      {/* ── Table ── */}
      <div style={tableContainerStyle}>
        <div style={{ padding:'10px 16px', borderBottom:'1px solid #e2e8f0', display:'flex', justifyContent:'space-between', alignItems:'center', background:'#fafafa' }}>
          <Text style={{ color:'#64748b', fontSize:13 }}>
            Showing <strong>{rows.length}</strong> of <strong>{total}</strong> records
            {selected.length > 0 && <> · <strong style={{ color:'#1890ff' }}>{selected.length} selected</strong></>}
          </Text>
          <Button icon={<DownloadOutlined />} size="small" onClick={() => exportCSV(rows)} disabled={rows.length === 0}>
            Export CSV
          </Button>
        </div>
        <Table
          className="txn-mod-table"
          columns={cols}
          dataSource={rows}
          loading={isLoading}
          rowKey="id"
          size="middle"
          scroll={{ x:1200 }}
          rowSelection={rowSelection}
          rowClassName={rowClassName}
          pagination={{
            current: page,
            pageSize: PAGE_SIZE,
            total,
            showSizeChanger: false,
            showTotal: (t, r) => `${r[0]}–${r[1]} of ${t}`,
            onChange: setPage,
          }}
        />
      </div>

      {/* ── Legend ── */}
      <div style={{ marginTop:10, display:'flex', gap:16, flexWrap:'wrap' }}>
        <Space size={4}><span style={{ display:'inline-block', width:12, height:12, background:'#e6f7ff', border:'1px solid #91caff', borderRadius:2 }} /><Text style={{ fontSize:12, color:'#8c8c8c' }}>First check-in (effective)</Text></Space>
        <Space size={4}><span style={{ display:'inline-block', width:12, height:12, background:'#fff1f0', border:'1px solid #ffa39e', borderRadius:2 }} /><Text style={{ fontSize:12, color:'#8c8c8c' }}>Last check-out (effective)</Text></Space>
        <Space size={4}><span style={{ display:'inline-block', width:12, height:12, background:'#f6ffed', border:'1px solid #b7eb8f', borderRadius:2 }} /><Text style={{ fontSize:12, color:'#8c8c8c' }}>Mobile punch</Text></Space>
        <Space size={4}><span style={{ display:'inline-block', width:12, height:12, background:'#fff2f0', border:'1px solid #ffa39e', borderRadius:2 }} /><Text style={{ fontSize:12, color:'#8c8c8c' }}>Duplicate / flagged</Text></Space>
      </div>

      {/* ── Detail Drawer ── */}
      <Drawer
        title={<Space><EyeOutlined />Transaction Details</Space>}
        open={detailOpen} onClose={() => setDetailOpen(false)} width={480} destroyOnHidden>
        {detailRec && (
          <>
            <Divider orientation="left" style={{ fontSize:12 }}>Employee</Divider>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Name" span={2}>
                <strong>{detailRec.emp_name || detailRec.emp_code}</strong>
              </Descriptions.Item>
              <Descriptions.Item label="Emp Code">{detailRec.emp_code || '—'}</Descriptions.Item>
              <Descriptions.Item label="Department">{detailRec.dept_name || '—'}</Descriptions.Item>
            </Descriptions>

            <Divider orientation="left" style={{ fontSize:12, marginTop:14 }}>Punch Details</Divider>
            <Descriptions column={2} size="small" bordered>
              <Descriptions.Item label="Punch Time" span={2}>
                <Text style={{ fontFamily:'monospace', fontSize:13 }}>
                  {detailRec.punch_time ? dayjs(detailRec.punch_time).format('DD MMM YYYY HH:mm:ss') : '—'}
                </Text>
              </Descriptions.Item>
              <Descriptions.Item label="Punch Type">
                {(() => {
                  const p = resolvedPunchState(detailRec.punch_state, detailRec.classified_direction);
                  return (
                    <Space direction="vertical" size={0}>
                      <Badge status={p.status} text={<span style={{ color:p.color, fontWeight:500 }}>{p.label}</span>} />
                      {p.inferred && <span style={{ fontSize:10, color:'#8c8c8c' }}>auto-classified</span>}
                    </Space>
                  );
                })()}
              </Descriptions.Item>
              <Descriptions.Item label="Verify Method">
                {(() => { const t = vLabel(detailRec.verify_type); return <Tag color={t.color}>{t.label}</Tag>; })()}
              </Descriptions.Item>
              <Descriptions.Item label="Terminal S/N">{detailRec.terminal_sn || '—'}</Descriptions.Item>
              <Descriptions.Item label="Area">
                {detailRec.area_name
                  ? <Tag color="geekblue">{detailRec.area_name}</Tag>
                  : (detailRec.area_alias || '—')}
              </Descriptions.Item>
              <Descriptions.Item label="Work Code">{detailRec.work_code ?? '—'}</Descriptions.Item>
              <Descriptions.Item label="Upload Time">
                {detailRec.upload_time ? dayjs(detailRec.upload_time).format('DD MMM YYYY HH:mm:ss') : '—'}
              </Descriptions.Item>
              <Descriptions.Item label="Transaction ID" span={2}>
                <Text code>{detailRec.id}</Text>
              </Descriptions.Item>
            </Descriptions>

            <div style={{ marginTop:20, display:'flex', gap:10 }}>
              <Popconfirm title="Delete this transaction?" okText="Delete" okButtonProps={{ danger:true }}
                onConfirm={() => { deleteOneM.mutate(detailRec.id); setDetailOpen(false); }}>
                <Button danger icon={<DeleteOutlined />} block>Delete Transaction</Button>
              </Popconfirm>
              <Button icon={<SyncOutlined />} block
                onClick={() => reprocessM.mutate(detailRec)}
                loading={reprocessM.isPending}>
                Reprocess
              </Button>
            </div>
          </>
        )}
      </Drawer>
    </div>
  );
};
export default TransactionsTab;
