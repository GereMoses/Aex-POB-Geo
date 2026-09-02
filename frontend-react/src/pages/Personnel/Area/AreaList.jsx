import { useState } from 'react';
import {
  Table, Button, Space, Input, Select, Modal, Form, Card,
  Row, Col, Tag, Badge, message, Popconfirm, Tabs, Statistic,
  Alert, Tooltip, Descriptions, Progress,
} from 'antd';
import {
  PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined,
  EyeOutlined, ThunderboltOutlined, EnvironmentOutlined,
  TeamOutlined, WarningOutlined, CheckCircleOutlined,
  CloseCircleOutlined, SyncOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../../services/api';

const ZONE_TYPE_COLORS = {
  RESTRICTED: 'red',
  PUBLIC: 'green',
  SAFE_HAVEN: 'blue',
  WORK_AREA: 'geekblue',
  ACCOMMODATION: 'cyan',
  HELIPAD: 'purple',
  CONTROL_ROOM: 'volcano',
  STORAGE: 'orange',
  EMERGENCY: 'magenta',
};

const ZONE_TYPE_LABELS = {
  RESTRICTED: 'Restricted',
  PUBLIC: 'Public',
  SAFE_HAVEN: 'Safe Haven',
  WORK_AREA: 'Work Area',
  ACCOMMODATION: 'Accommodation',
  HELIPAD: 'Helipad',
  CONTROL_ROOM: 'Control Room',
  STORAGE: 'Storage',
  EMERGENCY: 'Emergency',
};

const HAZARD_COLORS = { LOW: 'success', MEDIUM: 'warning', HIGH: 'error', CRITICAL: 'error' };
const STATUS_BADGE = {
  ACTIVE: 'success', INACTIVE: 'error', MAINTENANCE: 'warning',
  EMERGENCY: 'error', LOCKDOWN: 'warning',
};

// ── Analytics Tab ──────────────────────────────────────────────────────────────
const AnalyticsTab = ({ zones, summary }) => {
  const byType = summary?.by_type || {};
  const byHazard = summary?.by_hazard || {};
  const byStatus = summary?.by_status || {};

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <Row gutter={12}>
        {[
          { label: 'Total Warehouses', value: summary?.total ?? zones.length, color: '#1677ff' },
          { label: 'Active', value: summary?.active ?? zones.filter(z => z.is_active).length, color: '#52c41a' },
          { label: 'Inactive', value: summary?.inactive ?? zones.filter(z => !z.is_active).length, color: '#ff4d4f' },
        ].map(({ label, value, color }) => (
          <Col span={6} key={label}>
            <Card size="small">
              <Statistic title={label} value={value ?? 0} valueStyle={{ color, fontSize: 22 }} />
            </Card>
          </Col>
        ))}
      </Row>

      <Row gutter={12}>
        <Col span={8}>
          <Card size="small" title="By Warehouse Type">
            {Object.entries(byType).map(([type, count]) => (
              <div key={type} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Tag color={ZONE_TYPE_COLORS[type] || 'default'} style={{ margin: 0 }}>{ZONE_TYPE_LABELS[type] || type}</Tag>
                <strong>{count}</strong>
              </div>
            ))}
            {Object.keys(byType).length === 0 && <div style={{ color: '#8c8c8c', fontSize: 12 }}>No data</div>}
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="By Hazard Level">
            {Object.entries(byHazard).map(([hz, count]) => (
              <div key={hz} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Badge status={HAZARD_COLORS[hz] || 'default'} text={<span style={{ fontSize: 12 }}>{hz}</span>} />
                <strong>{count}</strong>
              </div>
            ))}
            {Object.keys(byHazard).length === 0 && <div style={{ color: '#8c8c8c', fontSize: 12 }}>No data</div>}
          </Card>
        </Col>
        <Col span={8}>
          <Card size="small" title="By Status">
            {Object.entries(byStatus).map(([st, count]) => (
              <div key={st} style={{ display: 'flex', justifyContent: 'space-between', padding: '4px 0', borderBottom: '1px solid #f0f0f0' }}>
                <Badge status={STATUS_BADGE[st] || 'default'} text={<span style={{ fontSize: 12 }}>{st}</span>} />
                <strong>{count}</strong>
              </div>
            ))}
            {Object.keys(byStatus).length === 0 && <div style={{ color: '#8c8c8c', fontSize: 12 }}>No data</div>}
          </Card>
        </Col>
      </Row>
    </div>
  );
};

// ── Main Component ─────────────────────────────────────────────────────────────
const AreaList = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [searchText, setSearchText] = useState('');
  const [selectedType, setSelectedType] = useState(null);
  const [selectedStatus, setSelectedStatus] = useState(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingZone, setEditingZone] = useState(null);
  const [viewZone, setViewZone] = useState(null);
  const [form] = Form.useForm();
  const queryClient = useQueryClient();

  const { data: zonesData, isLoading, refetch } = useQuery({
    queryKey: ['zones', searchText, selectedType, selectedStatus],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (searchText) params.append('search', searchText);
      if (selectedType) params.append('zone_type', selectedType);
      if (selectedStatus) params.append('status', selectedStatus);
      params.append('limit', '200');
      return await apiService.get(`/api/v1/zones/?${params}`);
    },
    refetchInterval: 30000,
  });

  const { data: summary } = useQuery({
    queryKey: ['zones-summary'],
    queryFn: () => apiService.get('/api/v1/zones/meta/summary'),
    refetchInterval: 60000,
  });

  const saveMutation = useMutation({
    mutationFn: async (values) => {
      if (editingZone) {
        return await apiService.put(`/api/v1/zones/${editingZone.id}/`, values);
      }
      return await apiService.post('/api/v1/zones/', values);
    },
    onSuccess: () => {
      message.success(editingZone ? 'Warehouse updated' : 'Warehouse created');
      setIsModalOpen(false);
      setEditingZone(null);
      form.resetFields();
      queryClient.invalidateQueries(['zones']);
      queryClient.invalidateQueries(['zones-summary']);
    },
    onError: (err) => message.error(err?.response?.data?.detail || err.message || 'Operation failed'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/zones/${id}`),
    onSuccess: () => {
      message.success('Warehouse deactivated');
      queryClient.invalidateQueries(['zones']);
      queryClient.invalidateQueries(['zones-summary']);
    },
    onError: (err) => message.error(err?.response?.data?.detail || err.message || 'Deactivate failed'),
  });

  const zones = Array.isArray(zonesData) ? zonesData : (zonesData?.data || []);

  const handleAdd = () => { setEditingZone(null); form.resetFields(); setIsModalOpen(true); };
  const handleEdit = (record) => {
    setEditingZone(record);
    form.setFieldsValue(record);
    setIsModalOpen(true);
  };
  const handleSave = () => form.validateFields().then((v) => saveMutation.mutate(v));

  const columns = [
    {
      title: 'Warehouse / Area',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (name, rec) => (
        <div>
          <div style={{ fontWeight: 500 }}>{name}</div>
          <div style={{ fontSize: 11, color: '#8c8c8c', fontFamily: 'monospace' }}>{rec.code}</div>
        </div>
      ),
    },
    {
      title: 'Type',
      dataIndex: 'zone_type',
      key: 'zone_type',
      width: 130,
      render: (t) => <Tag color={ZONE_TYPE_COLORS[t] || 'default'}>{ZONE_TYPE_LABELS[t] || t}</Tag>,
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 110,
      render: (s) => <Badge status={STATUS_BADGE[s] || 'default'} text={<span style={{ fontSize: 12 }}>{s}</span>} />,
    },
    {
      title: 'Hazard',
      dataIndex: 'hazard_level',
      key: 'hazard_level',
      width: 100,
      render: (h) => <Badge status={HAZARD_COLORS[h] || 'default'} text={<span style={{ fontSize: 12 }}>{h}</span>} />,
    },
    {
      title: 'State',
      dataIndex: 'state',
      key: 'state',
      width: 100,
      render: (s) => s ? <Tag style={{ fontSize: 11 }}>{s}</Tag> : '—',
    },
    {
      title: 'Personnel',
      dataIndex: 'assigned_personnel',
      key: 'assigned_personnel',
      width: 100,
      render: (n) => (
        <Space size={4}>
          <TeamOutlined style={{ color: '#1677ff' }} />
          <span>{n ?? 0}</span>
        </Space>
      ),
    },
    {
      title: 'Occupancy',
      key: 'occupancy',
      width: 130,
      render: (_, rec) => {
        if (!rec.max_capacity) return <span style={{ color: '#bfbfbf', fontSize: 11 }}>—</span>;
        const pct = rec.occupancy_rate ?? 0;
        return (
          <Tooltip title={`${rec.current_occupancy} / ${rec.max_capacity}`}>
            <Progress
              percent={pct}
              size="small"
              status={pct >= 90 ? 'exception' : pct >= 70 ? 'active' : 'normal'}
              format={() => `${pct}%`}
            />
          </Tooltip>
        );
      },
    },
    {
      title: 'ZKTeco',
      key: 'zkteco',
      width: 100,
      render: (_, rec) => rec.last_sync_at ? (
        <Tag icon={<SyncOutlined />} color="purple">Synced</Tag>
      ) : rec.zkteco_sync_enabled ? (
        <Tag color="orange">Pending</Tag>
      ) : (
        <Tag color="default">Disabled</Tag>
      ),
    },
    {
      title: 'Actions',
      key: 'actions',
      fixed: 'right',
      width: 220,
      render: (_, record) => (
        <Space size={4}>
          <Button size="small" icon={<EyeOutlined />} onClick={() => setViewZone(record)}>View</Button>
          <Button size="small" icon={<EditOutlined />} onClick={() => handleEdit(record)}>Edit</Button>
          <Popconfirm
            title="Deactivate this zone?"
            description="Active personnel assignments must be cleared first."
            onConfirm={() => deleteMutation.mutate(record.id)}
            okText="Deactivate"
            okButtonProps={{ danger: true }}
          >
            <Button size="small" danger icon={<DeleteOutlined />}>Deactivate</Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '16px 24px' }}>
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'overview',
            label: 'Areas / Warehouses',
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {/* KPI strip */}
                <Row gutter={12}>
                  {[
                    { label: 'Total Warehouses', value: summary?.total ?? zones.length, color: '#1677ff', icon: <EnvironmentOutlined /> },
                    { label: 'Active', value: summary?.active ?? zones.filter(z => z.is_active).length, color: '#52c41a', icon: <CheckCircleOutlined /> },
                    { label: 'Inactive', value: summary?.inactive ?? zones.filter(z => !z.is_active).length, color: '#ff4d4f', icon: <CloseCircleOutlined /> },
                    { label: 'BioTime Synced', value: summary?.zkteco_synced ?? 0, color: '#722ed1', icon: <ThunderboltOutlined /> },
                  ].map(({ label, value, color, icon }) => (
                    <Col span={6} key={label}>
                      <Card size="small" style={{ borderTop: `3px solid ${color}` }}>
                        <Statistic
                          title={<Space size={4}>{icon}<span>{label}</span></Space>}
                          value={value ?? 0}
                          valueStyle={{ color, fontSize: 20 }}
                        />
                      </Card>
                    </Col>
                  ))}
                </Row>

                {/* Filter card */}
                <Card size="small">
                  <Row gutter={12} align="middle">
                    <Col flex="1">
                      <Input.Search
                        placeholder="Search zones..."
                        value={searchText}
                        onChange={(e) => setSearchText(e.target.value)}
                        onSearch={setSearchText}
                        allowClear
                      />
                    </Col>
                    <Col>
                      <Select
                        placeholder="Warehouse Type"
                        style={{ width: 150 }}
                        value={selectedType}
                        onChange={setSelectedType}
                        allowClear
                      >
                        {Object.entries(ZONE_TYPE_LABELS).map(([v, l]) => (
                          <Select.Option key={v} value={v}>{l}</Select.Option>
                        ))}
                      </Select>
                    </Col>
                    <Col>
                      <Select
                        placeholder="Status"
                        style={{ width: 120 }}
                        value={selectedStatus}
                        onChange={setSelectedStatus}
                        allowClear
                      >
                        {['ACTIVE', 'INACTIVE', 'MAINTENANCE', 'EMERGENCY', 'LOCKDOWN'].map(s => (
                          <Select.Option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</Select.Option>
                        ))}
                      </Select>
                    </Col>
                    <Col>
                      <Space>
                        <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>New Warehouse</Button>
                        <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
                      </Space>
                    </Col>
                  </Row>
                </Card>

                {/* Table card */}
                <Card size="small">
                  <Table
                    columns={columns}
                    dataSource={zones}
                    loading={isLoading}
                    rowKey="id"
                    size="small"
                    scroll={{ x: 1400 }}
                    pagination={{
                      pageSize: 50,
                      showSizeChanger: true,
                      showQuickJumper: true,
                      showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} zones`,
                    }}
                  />
                </Card>
              </div>
            ),
          },
          {
            key: 'analytics',
            label: 'Analytics',
            children: <AnalyticsTab zones={zones} summary={summary} />,
          },
        ]}
      />

      {/* View Modal */}
      <Modal
        title={viewZone ? `${viewZone.name} (${viewZone.code})` : ''}
        open={!!viewZone}
        onCancel={() => setViewZone(null)}
        footer={[
          <Button key="edit" type="primary" onClick={() => { handleEdit(viewZone); setViewZone(null); }}>Edit</Button>,
          <Button key="close" onClick={() => setViewZone(null)}>Close</Button>,
        ]}
        width={680}
      >
        {viewZone && (
          <Descriptions column={2} size="small" bordered>
            <Descriptions.Item label="Code">{viewZone.code}</Descriptions.Item>
            <Descriptions.Item label="Name">{viewZone.name}</Descriptions.Item>
            <Descriptions.Item label="Type">
              <Tag color={ZONE_TYPE_COLORS[viewZone.zone_type]}>{ZONE_TYPE_LABELS[viewZone.zone_type] || viewZone.zone_type}</Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Status">
              <Badge status={STATUS_BADGE[viewZone.status]} text={viewZone.status} />
            </Descriptions.Item>
            <Descriptions.Item label="Hazard Level">
              <Badge status={HAZARD_COLORS[viewZone.hazard_level]} text={viewZone.hazard_level} />
            </Descriptions.Item>
            <Descriptions.Item label="Access Level">{viewZone.access_level}</Descriptions.Item>
            <Descriptions.Item label="State">{viewZone.state || '—'}</Descriptions.Item>
            <Descriptions.Item label="Assigned Personnel">{viewZone.assigned_personnel}</Descriptions.Item>
            <Descriptions.Item label="Max Capacity">{viewZone.max_capacity ?? '—'}</Descriptions.Item>
            <Descriptions.Item label="Current Occupancy">{viewZone.current_occupancy}</Descriptions.Item>
            <Descriptions.Item label="ZKTeco Sync">{viewZone.last_sync_at ? `Synced ${new Date(viewZone.last_sync_at).toLocaleDateString()}` : viewZone.zkteco_sync_enabled ? 'Pending' : 'Disabled'}</Descriptions.Item>
            <Descriptions.Item label="Contact">{viewZone.contact_person || '—'}</Descriptions.Item>
            {viewZone.description && (
              <Descriptions.Item label="Description" span={2}>{viewZone.description}</Descriptions.Item>
            )}
            {viewZone.address && (
              <Descriptions.Item label="Address" span={2}>{viewZone.address}</Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>

      {/* Create / Edit Modal */}
      <Modal
        title={editingZone ? `Edit Warehouse — ${editingZone.name}` : 'New Warehouse / Area'}
        open={isModalOpen}
        onOk={handleSave}
        onCancel={() => { setIsModalOpen(false); setEditingZone(null); form.resetFields(); }}
        okText={editingZone ? 'Update' : 'Create'}
        confirmLoading={saveMutation.isPending}
        width={760}
        destroyOnHidden
      >
        <Form form={form} layout="vertical" style={{ marginTop: 8 }}>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="name" label="Warehouse Name" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="e.g. Platform A" />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="code" label="Warehouse Code" rules={[{ required: true, message: 'Required' }]}>
                <Input placeholder="e.g. OFF-PLAT-A-001" disabled={!!editingZone} />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="zone_type" label="Warehouse Type" initialValue="WORK_AREA" rules={[{ required: true }]}>
                <Select>
                  {Object.entries(ZONE_TYPE_LABELS).map(([v, l]) => (
                    <Select.Option key={v} value={v}>{l}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="status" label="Status" initialValue="ACTIVE">
                <Select>
                  {['ACTIVE', 'INACTIVE', 'MAINTENANCE', 'EMERGENCY', 'LOCKDOWN'].map(s => (
                    <Select.Option key={s} value={s}>{s.charAt(0) + s.slice(1).toLowerCase()}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="hazard_level" label="Hazard Level" initialValue="LOW">
                <Select>
                  {['LOW', 'MEDIUM', 'HIGH', 'CRITICAL'].map(h => (
                    <Select.Option key={h} value={h}>{h}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="access_level" label="Access Level" initialValue="RESTRICTED">
                <Select>
                  {['PUBLIC', 'RESTRICTED', 'SECURE'].map(a => (
                    <Select.Option key={a} value={a}>{a}</Select.Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="state" label="State / Location">
                <Input placeholder="e.g. offshore, Lagos" />
              </Form.Item>
            </Col>
          </Row>

          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="max_capacity" label="Max Capacity">
                <Input type="number" min={0} placeholder="Max persons" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contact_person" label="Contact Person">
                <Input placeholder="Name" />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="contact_phone" label="Contact Phone">
                <Input placeholder="+234..." />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="address" label="Address">
            <Input placeholder="Physical address or location description" />
          </Form.Item>

          <Form.Item name="description" label="Description">
            <Input.TextArea rows={2} placeholder="Warehouse / area description" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="zkteco_sync_enabled" label="ZKTeco Sync" initialValue={true}>
                <Select>
                  <Select.Option value={true}>Enabled</Select.Option>
                  <Select.Option value={false}>Disabled</Select.Option>
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="is_active" label="Active" initialValue={true}>
                <Select>
                  <Select.Option value={true}>Yes</Select.Option>
                  <Select.Option value={false}>No</Select.Option>
                </Select>
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>
    </div>
  );
};

export default AreaList;
