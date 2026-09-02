import { useEffect } from 'react';
import {
  Card, Form, InputNumber, Switch, Button, Space, Typography, Row, Col,
  message, Alert, Divider, Spin,
} from 'antd';
import { SafetyOutlined, UndoOutlined } from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import apiService from '../../services/api';

const { Text } = Typography;

// Shipping defaults, so an administrator who has tuned themselves into a corner
// can get back to a known-good starting point.
const DEFAULTS = {
  face_matching_enabled: true,
  face_match_threshold: 0.40,
  block_on_face_mismatch: false,
  allow_pwa_punches: true,
  risk_pwa_client: 0,
  impossible_travel_kmh: 900,
  approach_max_ground_speed_kmh: 200,
  reject_risk_threshold: 80,
  min_expected_drift_m: 0.5,
  min_drift_samples: 3,
  altitude_tolerance_m: 150,
  clock_skew_flag_seconds: 300,
  risk_rooted_device: 40,
  risk_static_gps: 50,
  risk_implausible_altitude: 40,
  risk_zero_altitude: 30,
  risk_implausible_accuracy: 30,
  risk_clock_skew: 20,
  risk_accuracy_buffer: 10,
  block_rooted_devices: false,
};

const RISK_FIELDS = [
  ['risk_static_gps', 'Location did not drift', 'The strongest single spoofing signal — a real handset always jitters a few metres.'],
  ['risk_rooted_device', 'Rooted or jailbroken phone', 'Suspicious, but plenty of people modify their own handset for unrelated reasons.'],
  ['risk_implausible_altitude', 'Altitude does not match the site', 'Only applies where the warehouse has an elevation recorded.'],
  ['risk_zero_altitude', 'Altitude reported as exactly zero', 'A common fake-GPS default. Real satellite fixes never land on 0.000.'],
  ['risk_implausible_accuracy', 'Impossibly precise fix', 'Sub-metre accuracy is not achievable on a phone, least of all indoors.'],
  ['risk_clock_skew', 'Device clock is wrong', 'Evidence only — the punch is always stamped with server time.'],
  ['risk_accuracy_buffer', 'Admitted on the weak-signal allowance', 'Not misconduct. A cluster of these means a fence needs recalibrating.'],
];

export default function ClockInRules() {
  const qc = useQueryClient();
  const [form] = Form.useForm();

  const { data, isLoading } = useQuery({
    queryKey: ['geofence-policy'],
    queryFn: () => apiService.get('/api/v1/geofence/policy'),
  });

  useEffect(() => {
    if (data?.rules) form.setFieldsValue(data.rules);
  }, [data, form]);

  const save = useMutation({
    mutationFn: (values) => apiService.put('/api/v1/geofence/policy', values),
    onSuccess: () => {
      message.success('Clock-in rules updated — they apply to the next punch');
      qc.invalidateQueries({ queryKey: ['geofence-policy'] });
    },
    onError: (e) => message.error(e?.message || 'Could not save the rules'),
  });

  const threshold = Form.useWatch('reject_risk_threshold', form) ?? 80;

  if (isLoading) return <Spin style={{ display: 'block', padding: 48 }} />;

  return (
    <Form form={form} layout="vertical" onFinish={(v) => save.mutate(v)}>
      <Row gutter={16}>
        <Col xs={24} lg={12}>
          <Card size="small" title={<Space><SafetyOutlined />How a punch is judged</Space>}>
            <Alert
              type="info" showIcon style={{ marginBottom: 16 }}
              message="No single signal blocks a punch"
              description={
                <>
                  Each signal below adds to a risk score. A punch is refused only when the
                  total reaches <Text strong>{threshold}</Text>. A rooted phone alone scores{' '}
                  {form.getFieldValue('risk_rooted_device') ?? 40} and passes, flagged — a rooted
                  phone <em>and</em> a frozen GPS reading together do not. Judging on the total
                  is what keeps honest staff from being stranded at the gate at 6am.
                </>
              }
            />

            <Form.Item
              name="reject_risk_threshold" label="Refuse a punch at this total risk"
              extra="Lower is stricter. Below about 50 you will start refusing legitimate staff."
              rules={[{ required: true }]}
            >
              <InputNumber min={10} max={200} style={{ width: '100%' }} />
            </Form.Item>

            <Divider orientation="left" plain>Signal weights</Divider>
            {RISK_FIELDS.map(([name, label, help]) => (
              <Form.Item key={name} name={name} label={label} extra={help}>
                <InputNumber min={0} max={100} style={{ width: '100%' }} />
              </Form.Item>
            ))}
          </Card>
        </Col>

        <Col xs={24} lg={12}>
          <Card size="small" title="Hard limits" style={{ marginBottom: 16 }}>
            <Text type="secondary" style={{ fontSize: 12 }}>
              These refuse a punch outright, whatever the risk score says.
            </Text>
            <Divider style={{ margin: '12px 0' }} />

            <Form.Item
              name="block_rooted_devices" label="Refuse rooted and jailbroken phones outright"
              valuePropName="checked"
              extra="Off by default. Turning this on is the strictest setting available, and will generate support calls from staff who modified their own phone."
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name="approach_max_ground_speed_kmh" label="Impossible approach speed (km/h)"
              extra="Checked across the minutes before a punch. Someone travelling to a warehouse on the ground cannot exceed this — jumping 9 km in two minutes is 270 km/h."
            >
              <InputNumber min={30} max={1000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="impossible_travel_kmh" label="Impossible travel between punches (km/h)"
              extra="Separate, and far looser: two punches can legitimately be a flight apart."
            >
              <InputNumber min={100} max={5000} style={{ width: '100%' }} />
            </Form.Item>
          </Card>

          <Card size="small" title="Identity and client" style={{ marginBottom: 16 }}>
            <Form.Item
              name="face_matching_enabled" label="Match punch photos against the enrolled face"
              valuePropName="checked"
              extra="Requires the optional face module on the server. Without it, photos are queued for a supervisor instead."
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="face_match_threshold" label="Face match threshold"
              extra="Cosine similarity above which two photos are treated as the same person. On the reference model, different people scored at most 0.23 and the same person at least 0.93 — so 0.40 sits well clear of both. Raise it to be stricter."
            >
              <InputNumber min={0.05} max={0.95} step={0.05} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="block_on_face_mismatch" label="Refuse the punch on a face mismatch"
              valuePropName="checked"
              extra="Off by default. Until every employee has a good enrolment photo, a mismatch is more often a poor reference than an impostor — and turning somebody away at the gate is the worse error."
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="allow_pwa_punches" label="Allow clock-in from the browser"
              valuePropName="checked"
              extra="The browser version cannot run device integrity checks. Useful for a pilot; switch off once the app is distributed."
            >
              <Switch />
            </Form.Item>
            <Form.Item
              name="risk_pwa_client" label="Risk added to a browser punch"
              extra="A standing score for punches with no device attestation behind them. Leave at 0 during a pilot."
            >
              <InputNumber min={0} max={100} style={{ width: '100%' }} />
            </Form.Item>
          </Card>

          <Card size="small" title="Detector sensitivity">
            <Form.Item
              name="min_expected_drift_m" label="Minimum expected GPS drift (metres)"
              extra="Below this spread across the sample burst, the fix looks synthetic. Raising it makes the check stricter."
            >
              <InputNumber min={0} max={20} step={0.1} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="min_drift_samples" label="Samples needed before drift counts"
              extra="Fewer than this and the check is skipped — two identical readings happen legitimately when the phone returns a cached fix."
            >
              <InputNumber min={2} max={20} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="altitude_tolerance_m" label="Altitude tolerance (metres)"
              extra="Deliberately loose. Satellite altitude is far less accurate than horizontal position — routinely 30m out, worse under a roof."
            >
              <InputNumber min={20} max={2000} style={{ width: '100%' }} />
            </Form.Item>
            <Form.Item
              name="clock_skew_flag_seconds" label="Flag device clock drift beyond (seconds)"
              extra="Recorded as evidence only. The punch time always comes from the server."
            >
              <InputNumber min={30} max={86400} style={{ width: '100%' }} />
            </Form.Item>
          </Card>
        </Col>
      </Row>

      <Space style={{ marginTop: 16 }}>
        <Button type="primary" htmlType="submit" loading={save.isPending}>
          Save rules
        </Button>
        <Button icon={<UndoOutlined />} onClick={() => form.setFieldsValue(DEFAULTS)}>
          Restore defaults
        </Button>
        {data?.rules?.updated_by ? (
          <Text type="secondary" style={{ fontSize: 12 }}>
            Last changed by {data.rules.updated_by}
            {data.rules.updated_at ? ` on ${new Date(data.rules.updated_at).toLocaleString()}` : ''}
          </Text>
        ) : null}
      </Space>
    </Form>
  );
}
