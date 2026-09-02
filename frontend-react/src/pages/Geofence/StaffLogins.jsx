import { useState, useMemo } from 'react';
import {
  Card, Row, Col, Table, Button, Space, Tag, Typography, Modal, Input,
  message, Alert, Statistic, Radio, Form, Result, Segmented, Tooltip,
} from 'antd';
import {
  KeyOutlined, ReloadOutlined, DownloadOutlined, UserAddOutlined, CopyOutlined,
  CheckCircleOutlined, MinusCircleOutlined, ClockCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text, Paragraph } = Typography;

export default function StaffLogins() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState([]);
  const [filter, setFilter] = useState('all');
  const [open, setOpen] = useState(false);
  const [mode, setMode] = useState('random');
  const [fixed, setFixed] = useState('');
  const [issued, setIssued] = useState(null); // credentials returned once

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['staff-access'],
    queryFn: () => apiService.get('/api/v1/settings/users/staff-access'),
  });

  const staff = useMemo(() => data?.staff ?? [], [data]);
  const noLogin = useMemo(() => staff.filter((s) => !s.has_login), [staff]);

  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return staff.filter((s) => {
      if (filter === 'nologin' && s.has_login) return false;
      if (filter === 'neverused' && (!s.has_login || s.signed_in_before)) return false;
      if (filter === 'active' && !s.signed_in_before) return false;
      if (!q) return true;
      return `${s.full_name} ${s.emp_code}`.toLowerCase().includes(q);
    });
  }, [staff, search, filter]);

  const provision = useMutation({
    mutationFn: (body) => apiService.post('/api/v1/settings/users/provision-staff', body),
    onSuccess: (res) => {
      const d = res?.data ?? res;
      setIssued(d);
      setOpen(false);
      setSelected([]);
      qc.invalidateQueries({ queryKey: ['staff-access'] });
      if (d.failed) message.warning(`${d.created} created, ${d.failed} failed.`);
      else message.success(`${d.created} login(s) created.`);
    },
    onError: (e) => message.error(
      e?.response?.data?.detail || 'Could not create the logins.'),
  });

  const submit = () => {
    if (mode === 'fixed' && fixed.length < 12) {
      message.error('A shared password must be at least 12 characters.');
      return;
    }
    provision.mutate({
      personnel_ids: selected.length ? selected : null,
      password_mode: mode,
      password: mode === 'fixed' ? fixed : null,
    });
  };

  const downloadCsv = () => {
    const header = 'employee_code,name,username,password\n';
    const body = issued.accounts.map((a) =>
      [a.emp_code, a.full_name, a.username, a.password]
        .map((v) => `"${String(v ?? '').replace(/"/g, '""')}"`).join(',')
    ).join('\n');
    const url = URL.createObjectURL(new Blob([header + body], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `apex-staff-logins-${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const copyAll = async () => {
    const txt = issued.accounts
      .map((a) => `${a.emp_code}\t${a.full_name}\t${a.username}\t${a.password}`).join('\n');
    try {
      await navigator.clipboard.writeText(txt);
      message.success('Copied to the clipboard.');
    } catch {
      message.error('The browser blocked clipboard access. Use Download CSV.');
    }
  };

  const fmt = (iso) => {
    if (!iso) return null;
    const d = new Date(iso);
    const mins = Math.round((Date.now() - d.getTime()) / 60000);
    if (mins < 1) return 'just now';
    if (mins < 60) return `${mins} min ago`;
    if (mins < 60 * 24) return `${Math.round(mins / 60)} h ago`;
    return d.toLocaleString();
  };

  const columns = [
    { title: 'Employee code', dataIndex: 'emp_code', key: 'emp_code', width: 150,
      render: (v) => <Text strong>{v}</Text> },
    { title: 'Name', dataIndex: 'full_name', key: 'full_name' },
    { title: 'Department', dataIndex: 'department', key: 'department',
      render: (v) => v || <Text type="secondary">—</Text> },
    { title: 'App login', key: 'has_login', width: 150,
      render: (_, r) => (r.has_login
        ? <Space direction="vertical" size={0}>
            <Tag color="green" icon={<CheckCircleOutlined />}>Has login</Tag>
            <Text type="secondary" style={{ fontSize: 11 }}>{r.username}</Text>
          </Space>
        : <Tag color="orange" icon={<MinusCircleOutlined />}>No login</Tag>) },
    { title: 'Last signed in', key: 'last_login', width: 190,
      sorter: (a, b) => (a.last_login || '').localeCompare(b.last_login || ''),
      render: (_, r) => {
        if (!r.has_login) return <Text type="secondary">—</Text>;
        if (!r.signed_in_before) {
          return <Tooltip title="The account exists but has never been used">
            <Tag icon={<ClockCircleOutlined />}>Never used</Tag></Tooltip>;
        }
        return <Tooltip title={new Date(r.last_login).toLocaleString()}>
          <Text>{fmt(r.last_login)}</Text></Tooltip>;
      } },
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={5}>
          <Card size="small"><Statistic title="Staff" value={data?.total ?? 0} /></Card>
        </Col>
        <Col xs={12} md={5}>
          <Card size="small"><Statistic title="Have a login" value={data?.with_login ?? 0}
            valueStyle={{ color: '#16a34a' }} /></Card>
        </Col>
        <Col xs={12} md={5}>
          <Card size="small"><Statistic title="Have signed in" value={data?.signed_in ?? 0}
            valueStyle={{ color: '#2563eb' }} /></Card>
        </Col>
        <Col xs={12} md={9}>
          <Card size="small">
            <Text type="secondary" style={{ fontSize: 12 }}>
              Who can get into the app, and who has actually used it. The username is the
              employee code, so a punch ties back to the right record; sign-in is not
              case-sensitive. "Never used" means the account exists but nobody has signed
              in with it yet.
            </Text>
          </Card>
        </Col>
      </Row>

      <Card size="small">
        <Space wrap style={{ marginBottom: 12 }}>
          <Input.Search placeholder="Search name or employee code" allowClear
            style={{ width: 260 }} value={search}
            onChange={(e) => setSearch(e.target.value)} />
          <Segmented value={filter} onChange={setFilter} options={[
            { label: 'All', value: 'all' },
            { label: `No login${noLogin.length ? ` (${noLogin.length})` : ''}`, value: 'nologin' },
            { label: 'Never used', value: 'neverused' },
            { label: 'Has signed in', value: 'active' },
          ]} />
          <Button type="primary" icon={<UserAddOutlined />}
            disabled={!noLogin.length} onClick={() => setOpen(true)}>
            {selected.length ? `Create ${selected.length} login(s)` : 'Create missing logins'}
          </Button>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        </Space>

        <Table rowKey="personnel_id" size="small" loading={isLoading}
          dataSource={rows} columns={columns}
          rowSelection={{ selectedRowKeys: selected, onChange: setSelected,
                          getCheckboxProps: (r) => ({ disabled: r.has_login }) }}
          locale={{ emptyText: 'No staff match this filter.' }}
          pagination={{ pageSize: 20, showSizeChanger: true,
                        showTotal: (t) => `${t} staff` }} />
      </Card>

      {/* ── confirm ─────────────────────────────────────────────────────────── */}
      <Modal open={open} onCancel={() => setOpen(false)} onOk={submit}
        okText="Create logins" confirmLoading={provision.isPending}
        title={<Space><KeyOutlined />Create staff logins</Space>}>
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Text>
            {selected.length
              ? `Creating logins for the ${selected.length} selected employee(s).`
              : `Creating logins for all ${noLogin.length} employee(s) without one.`}
          </Text>
          <Form layout="vertical">
            <Form.Item label="Passwords">
              <Radio.Group value={mode} onChange={(e) => setMode(e.target.value)}>
                <Space direction="vertical">
                  <Radio value="random">
                    Generate a unique password for each person <Tag color="green">recommended</Tag>
                  </Radio>
                  <Radio value="fixed">Use one shared password for everyone</Radio>
                </Space>
              </Radio.Group>
            </Form.Item>
            {mode === 'fixed' && (
              <Form.Item label="Shared password" style={{ marginBottom: 0 }}>
                <Input.Password value={fixed} onChange={(e) => setFixed(e.target.value)}
                  placeholder="At least 12 characters" />
                <Text type="secondary" style={{ fontSize: 12 }}>
                  Everyone can then sign in as everyone else. Only reasonable for a short pilot.
                </Text>
              </Form.Item>
            )}
          </Form>
          <Alert type="info" showIcon
            message="Passwords are shown once"
            description="They are stored only as hashes, so this is the single opportunity to
                         export them. Afterwards they can be reset, not recovered." />
        </Space>
      </Modal>

      {/* ── credentials, shown once ─────────────────────────────────────────── */}
      <Modal open={!!issued} onCancel={() => setIssued(null)} width={720} footer={[
        <Button key="copy" icon={<CopyOutlined />} onClick={copyAll}>Copy</Button>,
        <Button key="csv" type="primary" icon={<DownloadOutlined />} onClick={downloadCsv}>
          Download CSV
        </Button>,
        <Button key="done" onClick={() => setIssued(null)}>Done</Button>,
      ]}>
        {issued && (
          <>
            <Result status="success" style={{ paddingBottom: 8 }}
              title={`${issued.created} login(s) created`}
              subTitle="Export these now — the passwords cannot be shown again." />
            {!!issued.failed && (
              <Alert type="warning" showIcon style={{ marginBottom: 12 }}
                message={`${issued.failed} could not be created`}
                description={(issued.errors || []).slice(0, 5)
                  .map((e) => `${e.emp_code}: ${e.error}`).join(' · ')} />
            )}
            <Table rowKey="emp_code" size="small" pagination={{ pageSize: 8 }}
              dataSource={issued.accounts} columns={[
                { title: 'Code', dataIndex: 'emp_code', width: 100 },
                { title: 'Name', dataIndex: 'full_name' },
                { title: 'Username', dataIndex: 'username', width: 120 },
                { title: 'Password', dataIndex: 'password', width: 170,
                  render: (v) => <Text code copyable>{v}</Text> },
              ]} />
            <Paragraph type="secondary" style={{ fontSize: 12, marginTop: 12, marginBottom: 0 }}>
              Hand each person their own line. They sign in with the employee code and the
              password shown, then register their face on first use if self-registration is on.
            </Paragraph>
          </>
        )}
      </Modal>
    </div>
  );
}
