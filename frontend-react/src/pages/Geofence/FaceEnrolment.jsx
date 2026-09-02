import { useState, useMemo, useRef, useEffect, useCallback } from 'react';
import {
  Card, Row, Col, Table, Button, Space, Tag, Typography, Modal, Input,
  Upload, message, Alert, Popconfirm, Tooltip, Statistic, Segmented,
} from 'antd';
import {
  CameraOutlined, UploadOutlined, DeleteOutlined, ReloadOutlined,
  CheckCircleOutlined, ExclamationCircleOutlined, UserOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

/* Long side the capture is scaled to before upload. Big enough for the detector
   to work with, small enough that a warehouse on mobile data is not punished. */
const CAPTURE_LONG_SIDE = 720;

export default function FaceEnrolment() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState([]);
  const [target, setTarget] = useState(null);   // employee being enrolled
  const [preview, setPreview] = useState(null); // data-URI awaiting submit
  const [camError, setCamError] = useState(null);
  const videoRef = useRef(null);
  const streamRef = useRef(null);

  const { data: status } = useQuery({
    queryKey: ['face-status'],
    queryFn: () => apiService.get('/api/v1/geofence/face/status'),
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['face-enrolment'],
    queryFn: () => apiService.get('/api/v1/geofence/face/enrolment'),
  });

  const staff = useMemo(() => data?.staff ?? [], [data]);
  const rows = useMemo(() => {
    const q = search.trim().toLowerCase();
    return staff.filter((s) => {
      if (filter === 'enrolled' && !s.enrolled) return false;
      if (filter === 'missing' && s.enrolled) return false;
      if (!q) return true;
      return `${s.name} ${s.emp_code}`.toLowerCase().includes(q);
    });
  }, [staff, search, filter, ]);

  /* ── camera ─────────────────────────────────────────────────────────────── */
  const stopCamera = useCallback(() => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
  }, []);

  const startCamera = useCallback(async () => {
    setCamError(null);
    // getUserMedia is stripped on insecure origins, so say so plainly rather
    // than letting the operator wonder why nothing happens.
    if (!window.isSecureContext || !navigator.mediaDevices?.getUserMedia) {
      setCamError('The camera needs an HTTPS connection. Upload a photo instead.');
      return;
    }
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user', width: { ideal: 1280 }, height: { ideal: 960 } },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play().catch(() => {});
      }
    } catch (e) {
      setCamError(e?.name === 'NotAllowedError'
        ? 'Camera permission was refused. Allow it, or upload a photo instead.'
        : 'No camera is available on this machine. Upload a photo instead.');
    }
  }, []);

  useEffect(() => () => stopCamera(), [stopCamera]);

  const capture = async () => {
    const v = videoRef.current;
    // play() resolves before the first frame decodes; drawing too early yields
    // a blank image, so wait until the video actually has dimensions.
    if (!v || !v.videoWidth) { message.warning('The camera is still warming up.'); return; }
    const scale = CAPTURE_LONG_SIDE / Math.max(v.videoWidth, v.videoHeight);
    const w = Math.round(v.videoWidth * scale);
    const h = Math.round(v.videoHeight * scale);
    const c = document.createElement('canvas');
    c.width = w; c.height = h;
    c.getContext('2d').drawImage(v, 0, 0, w, h);
    const uri = c.toDataURL('image/jpeg', 0.92);
    if (uri.length < 2000) { message.error('That capture came out blank. Try again.'); return; }
    setPreview(uri);
    stopCamera();
  };

  const openFor = (row) => {
    setTarget(row); setPreview(null); setCamError(null);
    setTimeout(startCamera, 150);
  };
  const close = () => { stopCamera(); setTarget(null); setPreview(null); };

  /* ── mutations ──────────────────────────────────────────────────────────── */
  const enrol = useMutation({
    mutationFn: ({ id, photo }) =>
      apiService.post(`/api/v1/geofence/face/enrolment/${id}`, { photo_base64: photo }),
    onSuccess: () => {
      message.success('Reference photo saved.');
      qc.invalidateQueries({ queryKey: ['face-enrolment'] });
      close();
    },
    onError: (e) => message.error(
      e?.response?.data?.detail || 'That photo could not be used.'),
  });

  const bulkRemove = useMutation({
    // No bulk endpoint exists for enrolments, so this fans out. The count is
    // bounded by what an operator can select on screen, and reporting the
    // failures matters more than the extra round trips.
    mutationFn: async (ids) => {
      const results = await Promise.allSettled(ids.map((id) =>
        apiService.delete(`/api/v1/geofence/face/enrolment/${id}`)));
      return { ok: results.filter((r) => r.status === 'fulfilled').length,
               failed: results.filter((r) => r.status === 'rejected').length };
    },
    onSuccess: ({ ok, failed }) => {
      if (failed) message.warning(`${ok} removed, ${failed} failed.`);
      else message.success(`${ok} reference photo(s) removed.`);
      setSelected([]);
      qc.invalidateQueries({ queryKey: ['face-enrolment'] });
    },
    onError: () => message.error('Could not remove the reference photos.'),
  });

  const remove = useMutation({
    mutationFn: (id) => apiService.delete(`/api/v1/geofence/face/enrolment/${id}`),
    onSuccess: () => {
      message.success('Reference photo removed.');
      qc.invalidateQueries({ queryKey: ['face-enrolment'] });
    },
    onError: (e) => message.error(e?.response?.data?.detail || 'Could not remove it.'),
  });

  const onUpload = (file) => {
    const reader = new FileReader();
    reader.onload = () => { setPreview(reader.result); stopCamera(); };
    reader.readAsDataURL(file);
    return false; // keep antd from uploading it itself
  };

  const enrolled = staff.filter((s) => s.enrolled).length;
  const available = status?.available;

  const columns = [
    { title: 'Employee', dataIndex: 'name', key: 'name',
      render: (v, r) => (
        <Space direction="vertical" size={0}>
          <Text strong>{v}</Text>
          <Text type="secondary" style={{ fontSize: 12 }}>{r.emp_code}</Text>
        </Space>
      ) },
    { title: 'Reference photo', dataIndex: 'enrolled', key: 'enrolled', width: 200,
      render: (v, r) => (v
        ? <Space direction="vertical" size={0}>
            <Tag color="green" icon={<CheckCircleOutlined />}>Registered</Tag>
            {r.source === 'SELF' && (
              <Tooltip title="Registered by the employee on their own device. Confirm it before relying on it.">
                <Tag color="gold" style={{ marginTop: 4 }}>Self-registered</Tag>
              </Tooltip>
            )}
          </Space>
        : <Tag color="orange" icon={<ExclamationCircleOutlined />}>Not registered</Tag>) },
    { title: 'Registered', dataIndex: 'enrolled_at', key: 'enrolled_at', width: 180,
      render: (v) => v ? new Date(v).toLocaleString() : <Text type="secondary">—</Text> },
    { title: '', key: 'actions', width: 210, align: 'right',
      render: (_, r) => (
        <Space>
          <Button size="small" icon={<CameraOutlined />} onClick={() => openFor(r)}
                  disabled={!available}>
            {r.enrolled ? 'Replace' : 'Register'}
          </Button>
          {r.enrolled && (
            <Popconfirm title="Remove this reference photo?"
                        description="Their punches will go to the review queue until a new one is registered."
                        onConfirm={() => remove.mutate(r.personnel_id)}>
              <Button size="small" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ) },
  ];

  return (
    <div>
      {available === false && (
        <Alert type="warning" showIcon style={{ marginBottom: 16 }}
          message="Face matching is not installed on this server"
          description={<>
            {status?.reason || 'The face model is unavailable.'} Staff can still clock in —
            their photo is captured and queued for a supervisor to check by eye — but nothing
            is compared automatically.
          </>} />
      )}

      <Row gutter={16} style={{ marginBottom: 16 }}>
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Registered" value={enrolled}
            suffix={`/ ${staff.length}`} valueStyle={{ color: '#16a34a' }} /></Card>
        </Col>
        <Col xs={12} md={6}>
          <Card size="small"><Statistic title="Awaiting a photo"
            value={Math.max(0, staff.length - enrolled)}
            valueStyle={{ color: staff.length - enrolled ? '#d97706' : undefined }} /></Card>
        </Col>
        <Col xs={24} md={12}>
          <Card size="small">
            <Text type="secondary" style={{ fontSize: 12 }}>
              Staff without a reference photo can still clock in. Their selfie is captured and
              stored, but nothing is compared against it, so the punch proves location — not
              identity.
            </Text>
          </Card>
        </Col>
      </Row>

      <Card size="small" bodyStyle={{ paddingBottom: 8 }}>
        <Space wrap style={{ marginBottom: 12 }}>
          <Input.Search placeholder="Search name or employee code" allowClear
            style={{ width: 260 }} value={search}
            onChange={(e) => setSearch(e.target.value)} />
          <Segmented value={filter} onChange={setFilter} options={[
            { label: 'All', value: 'all' },
            { label: 'Registered', value: 'enrolled' },
            { label: 'Missing', value: 'missing' },
          ]} />
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>Refresh</Button>
        </Space>

        {selected.length > 0 && (
          <Alert type="info" showIcon style={{ marginBottom: 10 }}
            message={`${selected.length} employee(s) selected`}
            action={
              <Space>
                <Popconfirm title="Remove these reference photos?"
                  description="Their punches go to the review queue until a new photo is registered."
                  okText="Remove" okButtonProps={{ danger: true }}
                  onConfirm={() => bulkRemove.mutate(selected)}>
                  <Button size="small" danger icon={<DeleteOutlined />}
                          loading={bulkRemove.isPending}>Remove photos</Button>
                </Popconfirm>
                <Button size="small" type="link" onClick={() => setSelected([])}>Clear</Button>
              </Space>
            } />
        )}

        <Table rowKey="personnel_id" size="small" loading={isLoading}
          dataSource={rows} columns={columns}
          rowSelection={{ selectedRowKeys: selected, onChange: setSelected,
                          getCheckboxProps: (r) => ({ disabled: !r.enrolled }) }}
          pagination={{ pageSize: 20, showSizeChanger: true, showTotal: (t) => `${t} staff` }} />
      </Card>

      <Modal open={!!target} onCancel={close} width={560}
        title={target ? <Space><UserOutlined />{target.name} · {target.emp_code}</Space> : ''}
        okText="Save reference photo"
        okButtonProps={{ disabled: !preview, loading: enrol.isPending }}
        onOk={() => enrol.mutate({ id: target.personnel_id, photo: preview })}>
        <Space direction="vertical" style={{ width: '100%' }} size={12}>
          <Text type="secondary">
            A clear, front-facing photo in good light, with the face filling most of the frame.
            Only a numeric signature is kept for matching — the photo itself is stored separately
            and is never shown outside this console.
          </Text>

          {camError && <Alert type="info" showIcon message={camError} />}

          <div style={{ background: '#0f172a', borderRadius: 8, overflow: 'hidden',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        minHeight: 260 }}>
            {preview
              ? <img src={preview} alt="Reference preview"
                     style={{ maxWidth: '100%', maxHeight: 320, display: 'block' }} />
              : <video ref={videoRef} playsInline muted
                       style={{ width: '100%', maxHeight: 320, display: 'block' }} />}
          </div>

          <Space wrap>
            {!preview && <Button type="primary" icon={<CameraOutlined />} onClick={capture}>
              Capture
            </Button>}
            {preview && <Button onClick={() => { setPreview(null); startCamera(); }}>
              Retake
            </Button>}
            <Upload accept="image/*" showUploadList={false} beforeUpload={onUpload}>
              <Button icon={<UploadOutlined />}>Upload a photo</Button>
            </Upload>
          </Space>
        </Space>
      </Modal>
    </div>
  );
}
