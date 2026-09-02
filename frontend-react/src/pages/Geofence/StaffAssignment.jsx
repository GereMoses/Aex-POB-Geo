import { useState, useMemo } from 'react';
import {
  Card, Row, Col, Select, Table, Button, Space, Tag, Typography, Modal, Input,
  Upload, message, Empty, Popconfirm, Alert, Transfer, Tooltip,
} from 'antd';
import {
  TeamOutlined, UserAddOutlined, UploadOutlined, WarningOutlined, DeleteOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

export default function StaffAssignment() {
  const qc = useQueryClient();
  const [siteId, setSiteId] = useState(null);
  const [adding, setAdding] = useState(false);
  const [picked, setPicked] = useState([]);
  const [selected, setSelected] = useState([]);
  const [search, setSearch] = useState('');

  const { data: sitesData } = useQuery({
    queryKey: ['geofence-sites'],
    queryFn: () => apiService.get('/api/v1/geofence/sites'),
  });
  const sites = useMemo(() => sitesData?.sites ?? [], [sitesData]);

  const { data: staffData, isLoading } = useQuery({
    queryKey: ['site-staff', siteId],
    queryFn: () => apiService.get(`/api/v1/geofence/sites/${siteId}/staff`),
    enabled: !!siteId,
  });

  const { data: unassignedData } = useQuery({
    queryKey: ['unassigned-staff', search],
    queryFn: () => apiService.get('/api/v1/geofence/staff/unassigned', search ? { search } : {}),
  });
  const unassigned = unassignedData?.staff ?? [];

  const assign = useMutation({
    mutationFn: ({ ids }) =>
      apiService.post(`/api/v1/geofence/sites/${siteId}/staff`, { personnel_ids: ids, is_primary: true }),
    onSuccess: (r) => {
      message.success(
        r.already_assigned
          ? `${r.assigned} assigned, ${r.already_assigned} already there`
          : `${r.assigned} assigned to ${r.warehouse}`,
      );
      qc.invalidateQueries({ queryKey: ['site-staff'] });
      qc.invalidateQueries({ queryKey: ['unassigned-staff'] });
      qc.invalidateQueries({ queryKey: ['geofence-sites'] });
      setAdding(false);
      setPicked([]);
    },
    onError: (e) => message.error(e?.message || 'Could not assign staff'),
  });

  const bulkUnassign = useMutation({
    // The single-remove endpoint takes one person, so this fans out. Bounded by
    // the page size, and partial failures are reported rather than swallowed.
    mutationFn: async (ids) => {
      const res = await Promise.allSettled(ids.map((id) =>
        apiService.delete(`/api/v1/geofence/sites/${siteId}/staff/${id}`)));
      return { ok: res.filter((r) => r.status === 'fulfilled').length,
               failed: res.filter((r) => r.status === 'rejected').length };
    },
    onSuccess: ({ ok, failed }) => {
      if (failed) message.warning(`${ok} removed, ${failed} failed.`);
      else message.success(`${ok} removed from this warehouse.`);
      setSelected([]);
      qc.invalidateQueries({ queryKey: ['site-staff'] });
      qc.invalidateQueries({ queryKey: ['unassigned-staff'] });
    },
    onError: () => message.error('Could not remove the selected staff.'),
  });

  const unassign = useMutation({
    mutationFn: (personnelId) =>
      apiService.delete(`/api/v1/geofence/sites/${siteId}/staff/${personnelId}`),
    onSuccess: () => {
      message.success('Removed from this warehouse');
      qc.invalidateQueries({ queryKey: ['site-staff'] });
      qc.invalidateQueries({ queryKey: ['unassigned-staff'] });
      qc.invalidateQueries({ queryKey: ['geofence-sites'] });
    },
    onError: (e) => message.error(e?.message || 'Could not remove'),
  });

  const bulkImport = async (file) => {
    try {
      const r = await apiService.upload('/api/v1/geofence/staff/bulk-assign', file);
      message[r.failed ? 'warning' : 'success'](
        `${r.assigned} assigned${r.already_assigned ? `, ${r.already_assigned} already there` : ''}` +
        `${r.failed ? `, ${r.failed} rejected` : ''}`,
      );
      if (r.failed) {
        Modal.info({
          title: 'Rows that could not be assigned',
          width: 620,
          content: (
            <Table
              size="small" rowKey="line" pagination={false} dataSource={r.errors}
              columns={[
                { title: 'Line', dataIndex: 'line', width: 70 },
                { title: 'Employee', dataIndex: 'emp_code', width: 110 },
                { title: 'Warehouse', dataIndex: 'site_code', width: 110 },
                { title: 'Reason', dataIndex: 'error' },
              ]}
            />
          ),
        });
      }
      qc.invalidateQueries({ queryKey: ['site-staff'] });
      qc.invalidateQueries({ queryKey: ['unassigned-staff'] });
      qc.invalidateQueries({ queryKey: ['geofence-sites'] });
    } catch (e) {
      message.error(e?.message || 'Import failed');
    }
    return false; // handled manually
  };

  const staff = staffData?.staff ?? [];

  return (
    <Row gutter={16}>
      <Col xs={24} lg={15}>
        <Card
          size="small"
          title={<Space><TeamOutlined />Staff at this warehouse</Space>}
          extra={
            <Space>
              <Select
                showSearch optionFilterProp="label" placeholder="Choose a warehouse"
                style={{ width: 240 }} value={siteId} onChange={setSiteId}
                options={sites.map((s) => ({
                  value: s.id,
                  label: `${s.name} (${s.assigned_staff})`,
                }))}
              />
              <Button type="primary" icon={<UserAddOutlined />} disabled={!siteId}
                      onClick={() => setAdding(true)}>
                Assign
              </Button>
            </Space>
          }
        >
          {!siteId ? (
            <Empty description="Choose a warehouse to see who is assigned to it" />
          ) : (
            <>
            {selected.length > 0 && (
              <Alert type="info" showIcon style={{ marginBottom: 10 }}
                message={`${selected.length} selected`}
                action={
                  <Space>
                    <Popconfirm title="Remove these staff from this warehouse?"
                      description="They will be turned away at the gate here until reassigned."
                      okText="Remove" okButtonProps={{ danger: true }}
                      onConfirm={() => bulkUnassign.mutate(selected)}>
                      <Button size="small" danger icon={<DeleteOutlined />}
                              loading={bulkUnassign.isPending}>Remove from warehouse</Button>
                    </Popconfirm>
                    <Button size="small" type="link" onClick={() => setSelected([])}>Clear</Button>
                  </Space>
                } />
            )}
            <Table
              rowKey="personnel_id" size="small" loading={isLoading} dataSource={staff}
              rowSelection={{ selectedRowKeys: selected, onChange: setSelected }}
              pagination={{ pageSize: 12, showSizeChanger: false }}
              locale={{
                emptyText: (
                  <Empty description="Nobody is assigned here yet — they will all be turned away at the gate" />
                ),
              }}
              columns={[
                { title: 'Employee', dataIndex: 'name',
                  render: (n, r) => (
                    <Space direction="vertical" size={0}>
                      <Text strong style={{ fontSize: 13 }}>{n}</Text>
                      <Text type="secondary" style={{ fontSize: 11 }}>{r.emp_code}</Text>
                    </Space>
                  ) },
                { title: 'Department', dataIndex: 'department', render: (d) => d || '—' },
                { title: 'Primary', dataIndex: 'is_primary', width: 90,
                  render: (p) => (p ? <Tag color="blue">Primary</Tag> : <Tag>Additional</Tag>) },
                { title: '', key: 'x', width: 60,
                  render: (_, r) => (
                    <Popconfirm
                      title="Remove from this warehouse?"
                      description="They will no longer be able to clock in here."
                      onConfirm={() => unassign.mutate(r.personnel_id)}
                    >
                      <Button size="small" danger type="text" icon={<DeleteOutlined />} />
                    </Popconfirm>
                  ) },
              ]}
            />
            </>
          )}
        </Card>
      </Col>

      <Col xs={24} lg={9}>
        <Card
          size="small"
          title={<Space><WarningOutlined />Not assigned anywhere</Space>}
          extra={
            <Upload beforeUpload={bulkImport} showUploadList={false} accept=".csv">
              <Tooltip title="CSV columns: emp_code, site_code">
                <Button size="small" icon={<UploadOutlined />}>Bulk assign</Button>
              </Tooltip>
            </Upload>
          }
        >
          {/* These are the people who will be refused at the gate on day one.
              Surfacing them is what stops a rollout failing quietly. */}
          {unassigned.length > 0 && (
            <Alert
              type="warning" showIcon style={{ marginBottom: 12 }}
              message={`${unassigned.length} employee${unassigned.length === 1 ? '' : 's'} cannot clock in anywhere`}
              description="Assign each of them to a warehouse before go-live."
            />
          )}
          <Input.Search
            allowClear placeholder="Search name or employee number"
            onSearch={setSearch} onChange={(e) => !e.target.value && setSearch('')}
            style={{ marginBottom: 8 }}
          />
          <Table
            rowKey="personnel_id" size="small" dataSource={unassigned}
            pagination={{ pageSize: 10, showSizeChanger: false }}
            locale={{ emptyText: <Empty description="Everyone is assigned to a warehouse" /> }}
            columns={[
              { title: 'Employee', dataIndex: 'name',
                render: (n, r) => (
                  <Space direction="vertical" size={0}>
                    <Text style={{ fontSize: 13 }}>{n}</Text>
                    <Text type="secondary" style={{ fontSize: 11 }}>{r.emp_code}</Text>
                  </Space>
                ) },
              { title: 'Department', dataIndex: 'department', render: (d) => d || '—' },
            ]}
          />
        </Card>
      </Col>

      <Modal
        open={adding}
        onCancel={() => { setAdding(false); setPicked([]); }}
        onOk={() => assign.mutate({ ids: picked.map(Number) })}
        okText={`Assign ${picked.length || ''}`}
        okButtonProps={{ disabled: !picked.length, loading: assign.isPending }}
        title={`Assign staff to ${sites.find((s) => s.id === siteId)?.name ?? ''}`}
        width={680}
      >
        <Transfer
          dataSource={unassigned.map((s) => ({
            key: String(s.personnel_id),
            title: `${s.name} (${s.emp_code})`,
            description: s.department || '',
          }))}
          showSearch
          targetKeys={picked}
          onChange={setPicked}
          render={(item) => item.title}
          listStyle={{ width: 300, height: 340 }}
          titles={['Unassigned', 'To assign']}
          locale={{ itemUnit: 'person', itemsUnit: 'people' }}
        />
      </Modal>
    </Row>
  );
}
