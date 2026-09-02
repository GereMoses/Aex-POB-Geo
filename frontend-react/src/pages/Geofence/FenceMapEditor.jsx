import { useState, useMemo, useEffect, Fragment } from 'react';
import { MapContainer, TileLayer, Marker, Circle, Polygon, useMapEvents, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  Card, List, Input, Button, Drawer, Form, InputNumber, Switch, Space, Tag,
  Typography, Empty, Alert, Upload, message, Segmented, Tooltip, Statistic, Row, Col,
} from 'antd';
import {
  EnvironmentOutlined, AimOutlined, UploadOutlined, SearchOutlined,
  CameraOutlined, TeamOutlined, WarningOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

const TILE_LAYERS = {
  Street: {
    url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  },
  Satellite: {
    url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
    attribution: '© <a href="https://www.esri.com/">Esri</a>',
  },
};

// Satellite is the default: an administrator placing a fence needs to see the
// roof and yard they are drawing around, not a street abstraction of them.
const DEFAULT_TILE = 'Satellite';

const siteIcon = (configured) => L.divIcon({
  className: '',
  html: `<div style="
    width:16px;height:16px;border-radius:50%;
    background:${configured ? '#10B981' : '#9CA3AF'};
    border:3px solid #fff;box-shadow:0 0 0 1px rgba(0,0,0,.25)"></div>`,
  iconSize: [16, 16],
  iconAnchor: [8, 8],
});

/** Click-to-place, active only while the drawer is open. */
function FencePlacer({ active, onPlace }) {
  useMapEvents({ click: (e) => active && onPlace(e.latlng.lat, e.latlng.lng) });
  return null;
}

/** Recentres the map when a different site is selected. */
function MapFocus({ lat, lng, zoom }) {
  const map = useMap();
  useEffect(() => {
    if (lat != null && lng != null) {
      map.flyTo([lat, lng], zoom ?? map.getZoom(), { duration: 0.6 });
    }
  }, [lat, lng, zoom, map]);
  return null;
}

export default function FenceMapEditor() {
  const qc = useQueryClient();
  const [search, setSearch] = useState('');
  const [fenceFilter, setFenceFilter] = useState('all');
  const [selected, setSelected] = useState(null);
  const [tile, setTile] = useState(DEFAULT_TILE);
  const [draft, setDraft] = useState(null);
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['geofence-sites'],
    queryFn: () => apiService.get('/api/v1/geofence/sites'),
  });

  const sites = useMemo(() => data?.sites ?? [], [data]);
  const configured = sites.filter((s) => s.geofence_enabled && s.latitude != null);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    const hasFence = (s) => !!(s.geofence_enabled && s.latitude != null);
    return sites.filter((s) => {
      if (fenceFilter === 'set' && !hasFence(s)) return false;
      if (fenceFilter === 'unset' && hasFence(s)) return false;
      if (!q) return true;
      return [s.name, s.code, s.address, s.state].some((v) => v?.toLowerCase().includes(q));
    });
  }, [sites, search, fenceFilter]);

  const saveMutation = useMutation({
    mutationFn: ({ id, values }) => apiService.put(`/api/v1/geofence/sites/${id}`, values),
    onSuccess: (_, { name }) => {
      message.success(`Fence saved for ${name}`);
      qc.invalidateQueries({ queryKey: ['geofence-sites'] });
      setSelected(null);
      setDraft(null);
    },
    onError: (err) => message.error(err?.message || 'Could not save the fence'),
  });

  const openSite = (site) => {
    setSelected(site);
    setDraft(site.latitude != null ? [site.latitude, site.longitude] : null);
    form.setFieldsValue({
      geofence_enabled: site.geofence_enabled ?? true,
      radius_m: site.radius_m ?? 200,
      gps_accuracy_max_m: site.gps_accuracy_max_m ?? 100,
      accuracy_buffer_cap_m: site.accuracy_buffer_cap_m ?? 50,
      elevation_m: site.elevation_m ?? null,
      require_selfie: site.require_selfie ?? false,
    });
  };

  const handleSave = async () => {
    const values = await form.validateFields();
    if (values.geofence_enabled && !draft) {
      message.warning('Click the map to place the warehouse centre first');
      return;
    }
    saveMutation.mutate({
      id: selected.id,
      name: selected.name,
      values: {
        ...values,
        latitude: draft?.[0] ?? null,
        longitude: draft?.[1] ?? null,
      },
    });
  };

  const importCsv = async (file) => {
    try {
      const res = await apiService.upload('/api/v1/geofence/sites/bulk-import', file);
      if (res.failed) {
        message.warning(`${res.configured} configured, ${res.failed} rejected — see the list below`);
      } else {
        message.success(`${res.configured} warehouse fences configured`);
      }
      qc.invalidateQueries({ queryKey: ['geofence-sites'] });
    } catch (err) {
      message.error(err?.message || 'Import failed');
    }
    return false; // handled manually; keep antd from uploading again
  };

  const mapCentre = draft
    ?? (configured.length ? [configured[0].latitude, configured[0].longitude] : [6.4531, 3.3958]);

  const focusLat = draft?.[0] ?? selected?.latitude ?? null;
  const focusLng = draft?.[1] ?? selected?.longitude ?? null;

  const radius = Form.useWatch('radius_m', form) ?? selected?.radius_m ?? 200;
  const bufferCap = Form.useWatch('accuracy_buffer_cap_m', form) ?? 50;

  return (
    <Row gutter={16}>
      <Col xs={24} lg={7}>
        <Card
          size="small"
          title={<Space><EnvironmentOutlined />Warehouses</Space>}
          extra={
            <Upload beforeUpload={importCsv} showUploadList={false} accept=".csv">
              <Tooltip title="CSV columns: code, latitude, longitude, radius_m, elevation_m, require_selfie">
                <Button size="small" icon={<UploadOutlined />}>Bulk import</Button>
              </Tooltip>
            </Upload>
          }
          styles={{ body: { padding: 12 } }}
        >
          <Row gutter={8} style={{ marginBottom: 12 }}>
            <Col span={12}>
              <Statistic title="Fenced" value={configured.length} suffix={`/ ${sites.length}`}
                         valueStyle={{ fontSize: 20, color: '#10B981' }} />
            </Col>
            <Col span={12}>
              <Statistic title="Not set up" value={sites.length - configured.length}
                         valueStyle={{ fontSize: 20, color: sites.length - configured.length ? '#F59E0B' : '#9CA3AF' }} />
            </Col>
          </Row>

          <Input
            allowClear
            prefix={<SearchOutlined />}
            placeholder="Search name, code, state"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ marginBottom: 8 }}
          />

          {/* Across hundreds of sites the useful question is which ones still
              have no boundary — nobody can clock in at those. */}
          <Segmented
            size="small" block value={fenceFilter} onChange={setFenceFilter}
            style={{ marginBottom: 8 }}
            options={[
              { label: 'All', value: 'all' },
              { label: 'Fence set', value: 'set' },
              { label: 'No fence', value: 'unset' },
            ]}
          />

          <List
            size="small"
            loading={isLoading}
            dataSource={filtered}
            locale={{ emptyText: <Empty description="No warehouses" /> }}
            style={{ maxHeight: 460, overflowY: 'auto' }}
            renderItem={(site) => (
              <List.Item
                onClick={() => openSite(site)}
                style={{
                  cursor: 'pointer', padding: '8px 6px', borderRadius: 6,
                  background: selected?.id === site.id ? 'rgba(16,185,129,.08)' : undefined,
                }}
              >
                <List.Item.Meta
                  title={
                    <Space size={4}>
                      <Text strong style={{ fontSize: 13 }}>{site.name}</Text>
                      {site.require_selfie && (
                        <Tooltip title="Photo required at clock-in">
                          <CameraOutlined style={{ color: '#0EA5E9' }} />
                        </Tooltip>
                      )}
                    </Space>
                  }
                  description={
                    <Space size={4} wrap>
                      <Tag>{site.code}</Tag>
                      {site.geofence_enabled && site.latitude != null
                        ? <Tag color="green">{site.radius_m}m</Tag>
                        : <Tag color="orange">No fence</Tag>}
                      <Tag icon={<TeamOutlined />}>{site.assigned_staff}</Tag>
                    </Space>
                  }
                />
              </List.Item>
            )}
          />
        </Card>
      </Col>

      <Col xs={24} lg={17}>
        <Card
          size="small"
          styles={{ body: { padding: 0, position: 'relative' } }}
          title={<Space><AimOutlined />Fence map</Space>}
          extra={
            <Segmented size="small" value={tile} onChange={setTile}
                       options={Object.keys(TILE_LAYERS)} />
          }
        >
          <MapContainer center={mapCentre} zoom={16} style={{ height: 620, borderRadius: 8 }}>
            <TileLayer url={TILE_LAYERS[tile].url} attribution={TILE_LAYERS[tile].attribution} />
            <MapFocus lat={focusLat} lng={focusLng} zoom={17} />
            <FencePlacer active={!!selected} onPlace={(lat, lng) => setDraft([lat, lng])} />

            {configured.filter((s) => s.id !== selected?.id).map((s) => (
              // Fragment, not a div: react-leaflet attaches layers through
              // context, so a real DOM element here would be injected into the
              // map container and sit over the tiles.
              <Fragment key={s.id}>
                <Marker position={[s.latitude, s.longitude]} icon={siteIcon(true)} />
                {s.polygon?.points
                  ? <Polygon positions={s.polygon.points} pathOptions={{ color: '#10B981', weight: 2, fillOpacity: 0.08 }} />
                  : <Circle center={[s.latitude, s.longitude]} radius={s.radius_m}
                            pathOptions={{ color: '#10B981', weight: 2, fillOpacity: 0.08 }} />}
              </Fragment>
            ))}

            {draft && (
              <>
                <Marker position={draft} icon={siteIcon(true)} />
                {/* Inner ring is the fence proper; the outer ring shows how far
                    the accuracy buffer can stretch it on a poor GPS fix, so the
                    administrator sees the real worst-case boundary. */}
                <Circle center={draft} radius={radius}
                        pathOptions={{ color: '#0EA5E9', weight: 3, fillOpacity: 0.12 }} />
                <Circle center={draft} radius={radius + bufferCap}
                        pathOptions={{ color: '#0EA5E9', weight: 1, dashArray: '6 6', fill: false }} />
              </>
            )}
          </MapContainer>

          {selected && (
            <div style={{
              position: 'absolute', top: 56, left: 12, zIndex: 500,
              background: 'rgba(255,255,255,.94)', padding: '6px 12px',
              borderRadius: 6, boxShadow: '0 2px 8px rgba(0,0,0,.15)',
            }}>
              <Text style={{ fontSize: 12 }}>
                Click the map to place <Text strong>{selected.name}</Text>
              </Text>
            </div>
          )}
        </Card>
      </Col>

      <Drawer
        open={!!selected}
        onClose={() => { setSelected(null); setDraft(null); }}
        title={selected ? `Fence — ${selected.name}` : ''}
        width={420}
        extra={
          <Button type="primary" onClick={handleSave} loading={saveMutation.isPending}>
            Save fence
          </Button>
        }
      >
        <Form form={form} layout="vertical">
          <Alert
            type="info" showIcon style={{ marginBottom: 16 }}
            message={draft
              ? `Centre: ${draft[0].toFixed(6)}, ${draft[1].toFixed(6)}`
              : 'Click the map to place this warehouse'}
          />

          <Form.Item name="geofence_enabled" label="Fence active" valuePropName="checked"
                     extra="While off, staff at this warehouse cannot clock in from the mobile app at all.">
            <Switch />
          </Form.Item>

          <Form.Item name="radius_m" label="Radius (metres)" rules={[{ required: true }]}
                     extra="Cover the yard and gate, not just the building. Large distribution centres commonly need 200–400m.">
            <InputNumber min={25} max={5000} step={25} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="gps_accuracy_max_m" label="Reject fixes weaker than (metres)"
                     extra="A reading less accurate than this cannot be trusted either way, so the punch is refused and the employee is asked to step outside.">
            <InputNumber min={10} max={1000} step={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="accuracy_buffer_cap_m" label="Maximum accuracy allowance (metres)"
                     extra="How far a weak fix may stretch the fence. Capped deliberately — without a limit, a spoofed device could claim huge inaccuracy to widen the boundary.">
            <InputNumber min={0} max={500} step={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item name="elevation_m" label="Site elevation (metres above sea level)"
                     extra="Optional. Enables the altitude check — fake-GPS apps rarely report plausible elevation.">
            <InputNumber step={1} style={{ width: '100%' }} placeholder="Leave blank to skip this check" />
          </Form.Item>

          <Form.Item name="require_selfie" label="Require a photo at clock-in" valuePropName="checked"
                     extra="Location proves a phone was on site, not who was holding it. The photo is what closes buddy punching.">
            <Switch />
          </Form.Item>

          {selected && !selected.assigned_staff && (
            <Alert type="warning" showIcon icon={<WarningOutlined />}
                   message="No staff assigned to this warehouse yet"
                   description="A fence has no effect until employees are assigned to the site." />
          )}
        </Form>
      </Drawer>
    </Row>
  );
}
