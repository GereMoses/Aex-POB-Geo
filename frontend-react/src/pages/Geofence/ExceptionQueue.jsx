import { useState, useEffect, useMemo } from 'react';
import { MapContainer, TileLayer, Marker, Circle, Polyline } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  Card, Table, Tag, Space, Typography, Select, Modal, Button, Descriptions,
  Input, message, Empty, Spin, Segmented, Row, Col, Alert, Tooltip, Avatar,
  Statistic, InputNumber, Switch, Popconfirm,
} from 'antd';
import {
  CameraOutlined, CheckOutlined, CloseOutlined, DatabaseOutlined, DeleteOutlined, DownloadOutlined, EnvironmentOutlined, MobileOutlined, ReloadOutlined, WarningOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

// Why a punch was refused, in the language a supervisor would use. The raw
// codes are kept visible too so they can be matched against the audit trail.
const REASON_LABEL = {
  OUTSIDE_FENCE:       'Outside the warehouse boundary',
  LOW_GPS_ACCURACY:    'GPS signal too weak to confirm',
  MOCK_LOCATION:       'Fake GPS app detected',
  ROOTED_DEVICE:       'Modified device',
  EMULATOR:            'Running on an emulator',
  ATTESTATION_FAILED:  'Device failed integrity check',
  NO_ASSIGNMENT:       'Not assigned to any warehouse',
  NO_FENCE_CONFIGURED: 'Warehouse fence not set up',
  IMPOSSIBLE_TRAVEL:   'Impossible travel between punches',
  STATIC_GPS:          'Location did not drift — likely spoofed',
  IMPLAUSIBLE_ALTITUDE:'Altitude does not match the site',
  APPROACH_TELEPORT:   'Jumped to site instead of travelling',
  COMPOSITE_RISK:      'Multiple spoofing signals together',
  MISSING_SELFIE:      'Required photo not provided',
};

const FLAG_LABEL = {
  rooted_device: 'Rooted device',
  clock_skew: 'Device clock wrong',
  implausible_accuracy: 'Impossibly precise GPS',
  within_accuracy_buffer: 'Admitted on weak-signal allowance',
  static_gps: 'No GPS drift',
  zero_altitude: 'Altitude reported as zero',
  implausible_altitude: 'Altitude mismatch',
  mock_location: 'Fake GPS app',
  approach_teleport: 'Teleported to site',
};

const riskColour = (r) => (r >= 80 ? 'red' : r >= 40 ? 'orange' : 'default');

const pin = (colour) => L.divIcon({
  className: '',
  html: `<div style="width:14px;height:14px;border-radius:50%;background:${colour};
         border:3px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.3)"></div>`,
  iconSize: [14, 14], iconAnchor: [7, 7],
});

/** Fetches the punch photo through the authenticated client as a blob URL. */
function PunchPhoto({ evidenceId }) {
  const [url, setUrl] = useState(null);
  const [failed, setFailed] = useState(false);

  useEffect(() => {
    let objectUrl;
    let cancelled = false;
    setUrl(null); setFailed(false);
    apiService
      .downloadFile(`/api/v1/geofence/exceptions/${evidenceId}/photo`)
      .then(({ blob }) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setUrl(objectUrl);
      })
      .catch(() => !cancelled && setFailed(true));
    // The object URL is revoked on unmount; without this every photo opened
    // in a review session would be retained for the life of the tab.
    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [evidenceId]);

  if (failed) return <Empty description="Photo unavailable" image={Empty.PRESENTED_IMAGE_SIMPLE} />;
  if (!url) return <div style={{ textAlign: 'center', padding: 40 }}><Spin /></div>;
  return <img src={url} alt="Captured at clock-in" style={{ width: '100%', borderRadius: 8 }} />;
}

/** Where the punch was attempted, against the warehouse fence. */
function PunchLocationMap({ record, site }) {
  if (record.latitude == null) return <Empty description="No location recorded" image={Empty.PRESENTED_IMAGE_SIMPLE} />;

  const punchAt = [record.latitude, record.longitude];
  const siteAt = site?.latitude != null ? [site.latitude, site.longitude] : null;
  const bounds = siteAt ? [punchAt, siteAt] : [punchAt];

  return (
    <MapContainer bounds={bounds} boundsOptions={{ padding: [40, 40] }}
                  center={punchAt} zoom={15} style={{ height: 260, borderRadius: 8 }}>
      <TileLayer
        url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
        attribution="© Esri" />
      {siteAt && (
        <>
          <Circle center={siteAt} radius={site.radius_m}
                  pathOptions={{ color: '#10B981', weight: 2, fillOpacity: 0.1 }} />
          <Marker position={siteAt} icon={pin('#10B981')} />
          {/* The line makes the distance legible at a glance — a supervisor
              should not have to read a number to see someone punched from home. */}
          <Polyline positions={[siteAt, punchAt]}
                    pathOptions={{ color: '#EF4444', weight: 2, dashArray: '6 6' }} />
        </>
      )}
      <Marker position={punchAt} icon={pin('#EF4444')} />
    </MapContainer>
  );
}

export default function ExceptionQueue() {
  const qc = useQueryClient();
  const [filter, setFilter] = useState('all');
  const [days, setDays] = useState(7);
  const [zoneId, setZoneId] = useState(null);
  const [review, setReview] = useState(null);
  const [search, setSearch] = useState('');
  const [selected, setSelected] = useState([]);
  const [storage, setStorage] = useState(false);
  const [purgeDays, setPurgeDays] = useState(90);
  const [purgePending, setPurgePending] = useState(false);
  const [note, setNote] = useState('');

  const { data: sitesData } = useQuery({
    queryKey: ['geofence-sites'],
    queryFn: () => apiService.get('/api/v1/geofence/sites'),
  });
  const sites = useMemo(() => sitesData?.sites ?? [], [sitesData]);
  const siteById = useMemo(
    () => Object.fromEntries(sites.map((s) => [s.id, s])), [sites]);

  const { data, isLoading } = useQuery({
    queryKey: ['geofence-exceptions', filter, days, zoneId],
    queryFn: () => apiService.get('/api/v1/geofence/exceptions', {
      days,
      ...(filter !== 'all' ? { only: filter } : {}),
      ...(zoneId ? { zone_id: zoneId } : {}),
    }),
    refetchInterval: 30000,
  });

  const reviewMutation = useMutation({
    mutationFn: ({ id, verdict, note }) =>
      apiService.post(`/api/v1/geofence/exceptions/${id}/review`, { verdict, note: note || null }),
    onSuccess: (_, { verdict }) => {
      message.success(verdict === 'MATCH' ? 'Photo confirmed' : 'Recorded as a mismatch');
      qc.invalidateQueries({ queryKey: ['geofence-exceptions'] });
      qc.invalidateQueries({ queryKey: ['geofence-summary'] });
      setReview(null); setNote('');
    },
    onError: (err) => message.error(err?.message || 'Could not record the review'),
  });

  const columns = [
    {
      title: 'Employee', dataIndex: 'employee_name', width: 190,
      render: (name, r) => (
        <Space>
          <Avatar size="small" style={{ background: '#0EA5E9' }}>
            {(name || r.emp_code || '?').charAt(0)}
          </Avatar>
          <div>
            <div style={{ fontSize: 13 }}>{name || '—'}</div>
            <Text type="secondary" style={{ fontSize: 11 }}>{r.emp_code}</Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Outcome', dataIndex: 'decision', width: 240,
      render: (d, r) => (
        <Space direction="vertical" size={2}>
          <Space size={4}>
            {d === 'REJECTED'
              ? <Tag color="red">Blocked</Tag>
              : d === 'ACCEPTED_FLAGGED'
                ? <Tag color="orange">Allowed — flagged</Tag>
                : <Tag color="green">Allowed</Tag>}
            <Tag color={riskColour(r.risk_score)}>risk {r.risk_score}</Tag>
          </Space>
          {r.reason && (
            <Tooltip title={r.reason}>
              <Text style={{ fontSize: 12 }}>{REASON_LABEL[r.reason] || r.reason}</Text>
            </Tooltip>
          )}
        </Space>
      ),
    },
    {
      title: 'Signals', dataIndex: 'flags', width: 210,
      render: (flags) => flags?.length
        ? <Space size={2} wrap>{flags.map((f) =>
            <Tag key={f} style={{ fontSize: 11 }}>{FLAG_LABEL[f] || f}</Tag>)}</Space>
        : <Text type="secondary">—</Text>,
    },
    {
      title: 'Warehouse', dataIndex: 'zone_name', width: 160,
      render: (n, r) => (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize: 13 }}>{n || '—'}</Text>
          {r.metres_outside_fence > 0 && (
            <Text type="danger" style={{ fontSize: 11 }}>
              {r.metres_outside_fence >= 1000
                ? `${(r.metres_outside_fence / 1000).toFixed(1)} km outside`
                : `${Math.round(r.metres_outside_fence)} m outside`}
            </Text>
          )}
        </Space>
      ),
    },
    {
      title: 'When', dataIndex: 'occurred_at', width: 150,
      render: (t, r) => (
        <Space direction="vertical" size={0}>
          <Text style={{ fontSize: 12 }}>{t ? new Date(t).toLocaleString() : '—'}</Text>
          <Tag style={{ fontSize: 11 }}>{r.direction}</Tag>
        </Space>
      ),
    },
    {
      title: '', key: 'actions', width: 120, fixed: 'right',
      render: (_, r) => (
        <Button size="small" type={r.face_verdict === 'PENDING_REVIEW' ? 'primary' : 'default'}
                icon={r.has_photo ? <CameraOutlined /> : <EnvironmentOutlined />}
                onClick={() => { setReview(r); setNote(''); }}>
          {r.face_verdict === 'PENDING_REVIEW' ? 'Review' : 'Open'}
        </Button>
      ),
    },
  ];

  const rows = useMemo(() => {
    const all = data?.exceptions ?? [];
    const q = search.trim().toLowerCase();
    if (!q) return all;
    return all.filter((r) =>
      `${r.emp_code || ''} ${r.name || r.full_name || ''}`.toLowerCase().includes(q));
  }, [data, search]);
  const pendingPhotos = rows.filter((r) => r.face_verdict === 'PENDING_REVIEW').length;

  const { data: usage, refetch: refetchUsage } = useQuery({
    queryKey: ['photo-usage'],
    queryFn: () => apiService.get('/api/v1/geofence/photos/usage'),
    enabled: storage,
  });

  const purge = useMutation({
    mutationFn: (body) => apiService.post('/api/v1/geofence/photos/purge', body),
    onSuccess: (res) => {
      const d = res?.data ?? res;
      message[d.dry_run ? 'info' : 'success'](d.message);
      if (!d.dry_run) { refetchUsage(); qc.invalidateQueries({ queryKey: ['geofence-exceptions'] });
      qc.invalidateQueries({ queryKey: ['geofence-summary'] }); }
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'Could not delete the photos.'),
  });

  const afterBulk = (msgFn) => ({
    onSuccess: (res) => {
      const d = res?.data ?? res;
      msgFn(d);
      setSelected([]);
      qc.invalidateQueries({ queryKey: ['geofence-exceptions'] });
      qc.invalidateQueries({ queryKey: ['geofence-summary'] });
      refetchUsage();
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'That action could not be completed.'),
  });

  const bulkReview = useMutation({
    mutationFn: (body) => apiService.post('/api/v1/geofence/exceptions/bulk-review', body),
    ...afterBulk((d) => message.success(d.message)),
  });
  const bulkPhotos = useMutation({
    mutationFn: (ids) => apiService.post('/api/v1/geofence/exceptions/bulk-delete-photos', { ids }),
    ...afterBulk((d) => message.success(d.message)),
  });
  const resolve = useMutation({
    mutationFn: ({ ids, resolution }) =>
      apiService.post('/api/v1/geofence/exceptions/resolve', { ids, resolution }),
    ...afterBulk((d) => message.success(d.message)),
  });
  const reopen = useMutation({
    mutationFn: (ids) => apiService.post('/api/v1/geofence/exceptions/reopen', { ids }),
    ...afterBulk((d) => message.success(d.message)),
  });

  const bulkDelete = useMutation({
    mutationFn: (ids) => apiService.post('/api/v1/geofence/exceptions/bulk-delete', { ids }),
    ...afterBulk((d) => message.success(d.message)),
  });

  const exportSelected = () => {
    const chosen = rows.filter((r) => selected.includes(r.id));
    const cols = ['id','emp_code','decision','reason','risk_score','zone_name',
                  'server_time','face_verdict','distance_m','gps_accuracy_m'];
    const csv = [cols.join(',')].concat(chosen.map((r) =>
      cols.map((c) => `"${String(r[c] ?? '').replace(/"/g,'""')}"`).join(','))).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv' }));
    const a = document.createElement('a');
    a.href = url;
    a.download = `apex-exceptions-${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a); a.click();
    document.body.removeChild(a); URL.revokeObjectURL(url);
  };

  const deletePhoto = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/geofence/exceptions/${id}/photo`),
    onSuccess: () => {
      message.success('Photo deleted. The punch record is unchanged.');
      setReview(null);
      qc.invalidateQueries({ queryKey: ['geofence-exceptions'] });
      qc.invalidateQueries({ queryKey: ['geofence-summary'] });
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'Could not delete the photo.'),
  });

  return (
    <>
      <Card
        size="small"
        title={<Space><WarningOutlined />Mobile punch exceptions</Space>}
        extra={
          <Space wrap>
            <Segmented
              size="small" value={filter} onChange={setFilter}
              options={[
                { label: 'All', value: 'all' },
                { label: 'Blocked', value: 'blocked' },
                { label: 'Flagged', value: 'flagged' },
                { label: `Photos${pendingPhotos ? ` (${pendingPhotos})` : ''}`, value: 'photo_review' },
                { label: 'Resolved', value: 'resolved' },
              ]}
            />
            <Select size="small" value={days} onChange={setDays} style={{ width: 120 }}
                    options={[
                      { value: 1, label: 'Last 24h' },
                      { value: 7, label: 'Last 7 days' },
                      { value: 30, label: 'Last 30 days' },
                      { value: 90, label: 'Last 90 days' },
                    ]} />
            <Select size="small" allowClear placeholder="All warehouses" value={zoneId}
                    onChange={setZoneId} style={{ width: 180 }} showSearch optionFilterProp="label"
                    options={sites.map((s) => ({ value: s.id, label: s.name }))} />
            <Input.Search size="small" allowClear placeholder="Employee code or name"
                          style={{ width: 200 }} value={search}
                          onChange={(e) => setSearch(e.target.value)} />
            <Button size="small" icon={<DatabaseOutlined />} onClick={() => setStorage(true)}>
              Photo storage
            </Button>
          </Space>
        }
      >
        {selected.length > 0 && (
          <Alert
            type="info" showIcon style={{ marginBottom: 10 }}
            message={`${selected.length} punch(es) selected`}
            action={
              <Space wrap>
                <Button size="small" icon={<CheckOutlined />} loading={bulkReview.isPending}
                        onClick={() => bulkReview.mutate({ ids: selected, verdict: 'MATCH' })}>
                  Confirm identity
                </Button>
                <Button size="small" danger icon={<CloseOutlined />} loading={bulkReview.isPending}
                        onClick={() => bulkReview.mutate({ ids: selected, verdict: 'MISMATCH' })}>
                  Not the employee
                </Button>
                {filter === 'resolved' ? (
                  <Button size="small" icon={<ReloadOutlined />} loading={reopen.isPending}
                          onClick={() => reopen.mutate(selected)}>
                    Reopen
                  </Button>
                ) : (
                  <>
                    <Button size="small" type="primary" icon={<CheckOutlined />}
                            loading={resolve.isPending}
                            onClick={() => resolve.mutate({ ids: selected, resolution: 'REVIEWED' })}>
                      Mark resolved
                    </Button>
                    <Tooltip title="Use when the punch was blocked but the employee was genuinely on site — a run of these at one warehouse means its fence is too tight.">
                      <Button size="small" loading={resolve.isPending}
                              onClick={() => resolve.mutate({ ids: selected, resolution: 'FALSE_POSITIVE' })}>
                        False positive
                      </Button>
                    </Tooltip>
                  </>
                )}
                <Button size="small" icon={<DownloadOutlined />} onClick={exportSelected}>
                  Export
                </Button>
                <Popconfirm title="Delete the photos on these punches?"
                  description="The punch records, risk scores and decisions are kept."
                  okText="Delete photos" okButtonProps={{ danger: true }}
                  onConfirm={() => bulkPhotos.mutate(selected)}>
                  <Button size="small" danger icon={<DeleteOutlined />}
                          loading={bulkPhotos.isPending}>Delete photos</Button>
                </Popconfirm>
                <Popconfirm title="Delete these exception records?"
                  description="This removes the geofence evidence and its photo. Attendance punches are NOT changed. Intended for clearing test data."
                  okText="Delete records" okButtonProps={{ danger: true }}
                  onConfirm={() => bulkDelete.mutate(selected)}>
                  <Button size="small" danger type="primary" icon={<DeleteOutlined />}
                          loading={bulkDelete.isPending}>Delete records</Button>
                </Popconfirm>
                <Button size="small" type="link" onClick={() => setSelected([])}>Clear</Button>
              </Space>
            }
          />
        )}

        <Table
          rowKey="id" size="small" loading={isLoading} columns={columns} dataSource={rows}
          rowSelection={{ selectedRowKeys: selected, onChange: setSelected,
                          preserveSelectedRowKeys: true }}
          scroll={{ x: 1200 }} pagination={{ pageSize: 20, showSizeChanger: true }}
          locale={{ emptyText: <Empty description="No exceptions in this period — every punch was clean" /> }}
        />
      </Card>

      <Modal
        open={!!review}
        onCancel={() => setReview(null)}
        width={860}
        title={review ? `${review.employee_name || review.emp_code} — ${review.direction === 'IN' ? 'clock in' : 'clock out'}` : ''}
        footer={review?.has_photo ? [
          <Popconfirm key="del" title="Delete this photo?"
            description="The punch record, its risk score and decision are kept — only the image is removed."
            okText="Delete" okButtonProps={{ danger: true }}
            onConfirm={() => deletePhoto.mutate(review.id)}>
            <Button danger icon={<DeleteOutlined />} loading={deletePhoto.isPending}
                    style={{ float: 'left' }}>Delete photo</Button>
          </Popconfirm>,
          <Input.TextArea key="note" rows={2} value={note} placeholder="Optional note for the record"
                          onChange={(e) => setNote(e.target.value)} style={{ marginBottom: 8 }} />,
          <Button key="cancel" onClick={() => setReview(null)}>Close</Button>,
          <Button key="mismatch" danger icon={<CloseOutlined />}
                  loading={reviewMutation.isPending}
                  onClick={() => reviewMutation.mutate({ id: review.id, verdict: 'MISMATCH', note })}>
            Not this employee
          </Button>,
          <Button key="match" type="primary" icon={<CheckOutlined />}
                  loading={reviewMutation.isPending}
                  onClick={() => reviewMutation.mutate({ id: review.id, verdict: 'MATCH', note })}>
            Confirm identity
          </Button>,
        ] : [<Button key="cancel" onClick={() => setReview(null)}>Close</Button>]}
      >
        {review && (
          <Row gutter={16}>
            <Col span={review.has_photo ? 14 : 24}>
              <PunchLocationMap record={review} site={siteById[review.zone_id]} />
              <Descriptions size="small" column={2} bordered style={{ marginTop: 12 }}>
                <Descriptions.Item label="Outcome">
                  {review.decision === 'REJECTED' ? 'Blocked' : 'Allowed'}
                </Descriptions.Item>
                <Descriptions.Item label="Risk">{review.risk_score}</Descriptions.Item>
                <Descriptions.Item label="Reason" span={2}>
                  {REASON_LABEL[review.reason] || review.reason || '—'}
                </Descriptions.Item>
                <Descriptions.Item label="GPS accuracy">
                  {review.gps_accuracy_m != null ? `${Math.round(review.gps_accuracy_m)} m` : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="GPS drift">
                  {review.gps_drift_m != null ? `${review.gps_drift_m.toFixed(2)} m` : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Altitude difference">
                  {review.altitude_delta_m != null ? `${Math.round(review.altitude_delta_m)} m` : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Clock difference">
                  {review.clock_skew_seconds != null
                    ? `${Math.round(review.clock_skew_seconds)} s` : '—'}
                </Descriptions.Item>
                <Descriptions.Item label="Device" span={2}>
                  <Space size={4}>
                    <MobileOutlined />
                    <Text style={{ fontSize: 12 }}>{review.platform || 'unknown'}</Text>
                    <Text type="secondary" style={{ fontSize: 11 }}>{review.device_id || ''}</Text>
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Col>

            {review.has_photo && (
              <Col span={10}>
                <PunchPhoto evidenceId={review.id} />
                {review.face_verdict && review.face_verdict !== 'PENDING_REVIEW' && (
                  <Alert style={{ marginTop: 12 }} showIcon
                         type={review.face_verdict === 'MATCH' ? 'success' : 'error'}
                         message={review.face_verdict === 'MATCH'
                           ? 'Identity already confirmed'
                           : 'Already recorded as a mismatch'} />
                )}
                <Alert style={{ marginTop: 12 }} type="info" showIcon
                       message="Compare against the employee's enrolled photo"
                       description="Marking a mismatch records the finding. It does not remove the punch — correct that through the manual adjustment workflow." />
              </Col>
            )}
          </Row>
        )}
      </Modal>

      {/* ── Photo storage ────────────────────────────────────────────────── */}
      <Modal open={storage} onCancel={() => setStorage(false)} width={560} footer={null}
             title={<Space><DatabaseOutlined />Punch photo storage</Space>}>
        <Row gutter={12} style={{ marginBottom: 16 }}>
          <Col span={8}><Card size="small">
            <Statistic title="Photos" value={usage?.photos_recorded ?? 0} /></Card></Col>
          <Col span={8}><Card size="small">
            <Statistic title="Disk used" value={usage?.megabytes ?? 0} suffix="MB" /></Card></Col>
          <Col span={8}><Card size="small">
            <Statistic title="Awaiting review" value={usage?.pending_review ?? 0}
              valueStyle={{ color: (usage?.pending_review ?? 0) ? '#d97706' : undefined }} /></Card></Col>
        </Row>

        {usage?.oldest && (
          <Text type="secondary" style={{ fontSize: 12 }}>
            Oldest photo {new Date(usage.oldest).toLocaleDateString()} ·
            newest {new Date(usage.newest).toLocaleDateString()}
          </Text>
        )}

        <Alert type="info" showIcon style={{ margin: '14px 0' }}
          message="Only the image is deleted"
          description="The punch, its location, risk score and decision stay on record, so
                       attendance and the audit trail are unaffected." />

        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Space wrap>
            <Text>Delete photos older than</Text>
            <InputNumber min={1} max={3650} value={purgeDays} onChange={setPurgeDays}
                         style={{ width: 90 }} />
            <Text>days</Text>
          </Space>
          <Space>
            <Switch checked={purgePending} onChange={setPurgePending} size="small" />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Also delete photos still awaiting review — normally kept, since a pending
              verdict rests on them.
            </Text>
          </Space>
          <Space>
            <Button onClick={() => purge.mutate({ older_than_days: purgeDays,
                      keep_pending_review: !purgePending, dry_run: true })}
                    loading={purge.isPending}>
              Preview
            </Button>
            <Popconfirm title="Delete these photos?"
              description={`Photos older than ${purgeDays} days will be permanently removed.`}
              okText="Delete" okButtonProps={{ danger: true }}
              onConfirm={() => purge.mutate({ older_than_days: purgeDays,
                        keep_pending_review: !purgePending, dry_run: false })}>
              <Button danger icon={<DeleteOutlined />} loading={purge.isPending}>
                Delete now
              </Button>
            </Popconfirm>
          </Space>
        </Space>
      </Modal>
    </>
  );
}
