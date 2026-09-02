import React, { useState } from 'react';
import { Form, Input, Button, App, Checkbox } from 'antd';
import {
  UserOutlined, LockOutlined, SafetyOutlined, TeamOutlined,
  ApartmentOutlined, AlertOutlined, DashboardOutlined, CheckCircleFilled,
  EyeInvisibleOutlined, EyeTwoTone, RightOutlined, MobileOutlined,
} from '@ant-design/icons';

/* ─── Feature list shown in the left panel ─────────────── */
const FEATURES = [
  { icon: <TeamOutlined />,      label: 'Personnel On Board Management' },
  { icon: <SafetyOutlined />,    label: 'Location-Verified Attendance'   },
  { icon: <AlertOutlined />,     label: 'Emergency Response System'      },
  { icon: <ApartmentOutlined />, label: 'Department & Role Management'   },
  { icon: <DashboardOutlined />, label: 'Real-time Analytics Dashboard'  },
];

/* ─── Animated floating orbs (pure CSS, no library) ────── */
const ORB_DEFS = [
  { size: 420, top: '-12%', left: '-8%',   delay: '0s',    dur: '18s', opacity: 0.07 },
  { size: 280, top: '55%',  left: '-5%',   delay: '-6s',   dur: '22s', opacity: 0.06 },
  { size: 360, top: '20%',  left: '65%',   delay: '-3s',   dur: '20s', opacity: 0.05 },
  { size: 200, top: '75%',  left: '72%',   delay: '-9s',   dur: '16s', opacity: 0.08 },
  { size: 140, top: '40%',  left: '30%',   delay: '-12s',  dur: '14s', opacity: 0.04 },
];

const Login = ({ onLogin }) => {
  const { message } = App.useApp();
  const [loading, setLoading]       = useState(false);
  const [focused, setFocused]       = useState(null);
  const [year]                      = useState(new Date().getFullYear());
  // MFA step state
  const [mfaRequired, setMfaRequired] = useState(false);
  const [mfaPendingToken, setMfaPendingToken] = useState(null);
  const [mfaLoading, setMfaLoading] = useState(false);
  const [mfaForm] = Form.useForm();

  const handleSubmit = async (values) => {
    setLoading(true);
    try {
      const formData = new URLSearchParams();
      formData.append('username', values.username);
      formData.append('password', values.password);

      const response = await fetch('/api/v1/auth/production-login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: formData.toString(),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Authentication failed');
      }

      const data = await response.json();

      // If backend requires MFA, show the TOTP step instead of logging in
      if (data.mfa_required) {
        setMfaPendingToken(data.access_token);
        setMfaRequired(true);
        message.info('Enter the code from your authenticator app to continue.');
        return;
      }

      localStorage.setItem('token', data.access_token);
      localStorage.removeItem('authToken');
      localStorage.removeItem('access_token');
      localStorage.setItem('user_info', JSON.stringify(data.user));
      onLogin(data.user, data.access_token);
      message.success('Welcome back — access granted');
    } catch (error) {
      message.error(error.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleMfaSubmit = async (values) => {
    setMfaLoading(true);
    try {
      const response = await fetch('/api/v1/mfa/verify', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${mfaPendingToken}`,
        },
        body: JSON.stringify({ code: values.totp_code }),
      });

      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'MFA verification failed');
      }

      const data = await response.json();
      // Fetch full user profile with the real token
      const meRes = await fetch('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });
      if (!meRes.ok) {
        throw new Error('Failed to load your profile after MFA. Please try again.');
      }
      const userData = await meRes.json();

      localStorage.setItem('token', data.access_token);
      localStorage.removeItem('authToken');
      localStorage.removeItem('access_token');
      localStorage.setItem('user_info', JSON.stringify(userData));
      onLogin(userData, data.access_token);
      message.success('Welcome back — access granted');
    } catch (error) {
      message.error(error.message || 'Invalid code. Try again.');
    } finally {
      setMfaLoading(false);
    }
  };

  const inputStyle = (field) => ({
    height: 48,
    borderRadius: 10,
    border: `1.5px solid ${focused === field ? '#4f8ef7' : '#e2e8f0'}`,
    background: focused === field ? 'rgba(79,142,247,0.04)' : '#fafbfc',
    boxShadow: focused === field ? '0 0 0 3px rgba(79,142,247,0.12)' : 'none',
    transition: 'all 0.2s ease',
    fontSize: 14,
  });

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      background: '#0a0f1e',
      fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, sans-serif",
    }}>

      {/* ═══ LEFT PANEL — Branding ════════════════════════════ */}
      <div style={{
        flex: '0 0 52%',
        position: 'relative',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '52px 56px',
      }}>

        {/* Access control background photo */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'url(/logo/access-control-bg.png)',
          backgroundSize: 'cover',
          backgroundPosition: 'center center',
          backgroundRepeat: 'no-repeat',
        }} />

        {/* Dark overlay — top heavier so text stays readable, bottom lighter to show scene */}
        <div style={{
          position: 'absolute', inset: 0,
          background: 'linear-gradient(180deg, rgba(5,12,30,0.82) 0%, rgba(5,14,36,0.60) 50%, rgba(5,12,30,0.75) 100%)',
        }} />

        {/* Subtle grid on top of photo */}
        <div style={{
          position: 'absolute', inset: 0, pointerEvents: 'none',
          backgroundImage: `
            linear-gradient(rgba(79,142,247,0.05) 1px, transparent 1px),
            linear-gradient(90deg, rgba(79,142,247,0.05) 1px, transparent 1px)
          `,
          backgroundSize: '48px 48px',
        }} />

        {/* Floating orbs */}
        {ORB_DEFS.map((o, i) => (
          <div key={i} style={{
            position: 'absolute',
            top: o.top, left: o.left,
            width: o.size, height: o.size,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(79,142,247,0.35) 0%, transparent 70%)',
            opacity: o.opacity,
            animation: `orbFloat ${o.dur} ease-in-out ${o.delay} infinite`,
            pointerEvents: 'none',
          }} />
        ))}

        {/* Top: Apex POB (application) logo */}
        <div style={{ position: 'relative', zIndex: 2 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginBottom: 6 }}>
            <div style={{
              background: 'white',
              borderRadius: 14,
              padding: '8px 14px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.35)',
              display: 'inline-flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}>
              <img
                src={`${process.env.PUBLIC_URL || ''}/logo/apex-mark.png`}
                alt="Apex POB"
                style={{ height: 44, width: 'auto', display: 'block' }}
              />
            </div>
            <div>
              <div style={{ color: 'white', fontSize: 18, fontWeight: 800, letterSpacing: '-0.2px', lineHeight: 1.2 }}>
                Apex POB
              </div>
              <div style={{ color: 'rgba(255,255,255,0.4)', fontSize: 10, letterSpacing: '0.14em', textTransform: 'uppercase', marginTop: 3 }}>
                Personnel On Board
              </div>
            </div>
          </div>
        </div>

        {/* Middle: Hero text + features */}
        <div style={{ position: 'relative', zIndex: 2, flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', paddingTop: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: 'rgba(79,142,247,0.12)',
              border: '1px solid rgba(79,142,247,0.25)',
              borderRadius: 20, padding: '4px 12px',
            }}>
              <span style={{
                width: 6, height: 6, borderRadius: '50%',
                background: '#4ade80',
                boxShadow: '0 0 6px #4ade80',
                display: 'inline-block',
                animation: 'pulse 2s infinite',
              }} />
              <span style={{
                color: 'rgba(255,255,255,0.55)', fontSize: 10, fontWeight: 700,
                letterSpacing: '0.18em', textTransform: 'uppercase',
              }}>
                Biometric Access Enabled
              </span>
            </div>
          </div>

          <div style={{
            color: 'rgba(255,255,255,0.18)', fontSize: 11, fontWeight: 700,
            letterSpacing: '0.2em', textTransform: 'uppercase', marginBottom: 16,
          }}>
            Personnel On Board Management
          </div>

          <h1 style={{
            color: 'white', fontSize: 38, fontWeight: 800,
            lineHeight: 1.15, letterSpacing: '-0.8px', margin: 0, marginBottom: 8,
          }}>
            Manage your<br />
            <span style={{ background: 'linear-gradient(90deg, #4f8ef7, #38bdf8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              workforce
            </span>{' '}
            with<br />precision.
          </h1>

          <p style={{
            color: 'rgba(255,255,255,0.45)', fontSize: 14, lineHeight: 1.7,
            maxWidth: 380, margin: '16px 0 36px',
          }}>
            BioTime 9.5-compatible access control, biometric integration, emergency management and real-time personnel tracking — all in one platform.
          </p>

          {/* Feature list */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {FEATURES.map((f, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div style={{
                  width: 32, height: 32, borderRadius: 8, flexShrink: 0,
                  background: 'rgba(79,142,247,0.1)',
                  border: '1px solid rgba(79,142,247,0.2)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  color: '#4f8ef7', fontSize: 14,
                }}>
                  {f.icon}
                </div>
                <span style={{ color: 'rgba(255,255,255,0.65)', fontSize: 13, fontWeight: 500 }}>
                  {f.label}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Bottom: Stats row */}
        <div style={{
          position: 'relative', zIndex: 2,
          display: 'flex', gap: 32,
          paddingTop: 32,
          borderTop: '1px solid rgba(255,255,255,0.06)',
        }}>
          {[
            { value: '99.9%', label: 'Uptime SLA'   },
            { value: 'ISO',   label: 'Certified'     },
            { value: '24/7',  label: 'Monitoring'    },
          ].map((s, i) => (
            <div key={i}>
              <div style={{ color: 'white', fontSize: 18, fontWeight: 800 }}>{s.value}</div>
              <div style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, marginTop: 2 }}>{s.label}</div>
            </div>
          ))}
        </div>
      </div>

      {/* ═══ RIGHT PANEL — Login form ════════════════════════ */}
      <div style={{
        flex: 1,
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'center',
        alignItems: 'center',
        padding: '40px 32px',
        background: '#f7f9fc',
        position: 'relative',
      }}>

        {/* Subtle radial glow top-right */}
        <div style={{
          position: 'absolute', top: -120, right: -120,
          width: 400, height: 400, borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(79,142,247,0.07) 0%, transparent 70%)',
          pointerEvents: 'none',
        }} />

        {/* The card */}
        <div style={{
          width: '100%', maxWidth: 400,
          background: 'white',
          borderRadius: 20,
          padding: '40px 36px',
          boxShadow: '0 4px 6px rgba(0,0,0,0.04), 0 20px 60px rgba(0,0,0,0.08)',
          border: '1px solid rgba(0,0,0,0.05)',
          position: 'relative',
        }}>

          {/* Top accent line */}
          <div style={{
            position: 'absolute', top: 0, left: 24, right: 24, height: 3,
            background: 'linear-gradient(90deg, #4f8ef7, #38bdf8)',
            borderRadius: '0 0 4px 4px',
          }} />

          {/* Apex logo + welcome text */}
          <div style={{ textAlign: 'center', marginBottom: 28, marginTop: 8 }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              marginBottom: 18,
            }}>
              <img
                src={`${process.env.PUBLIC_URL || ''}/logo/apex-mark.png`}
                alt="Apex POB"
                style={{
                  height: 72, width: 'auto',
                  filter: 'drop-shadow(0 4px 12px rgba(15,23,42,0.18))',
                }}
              />
            </div>

            {/* Divider line */}
            <div style={{
              width: 48, height: 3, margin: '0 auto 16px',
              background: 'linear-gradient(90deg, #4f8ef7, #38bdf8)',
              borderRadius: 2,
            }} />

            <div style={{ fontWeight: 800, fontSize: 21, color: '#0f172a', letterSpacing: '-0.3px' }}>
              Welcome back
            </div>
            <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 6 }}>
              Sign in to your Apex POB account
            </div>
          </div>

          {/* ── MFA Step ── */}
          {mfaRequired && (
            <div style={{ marginBottom: 8 }}>
              <div style={{ textAlign: 'center', marginBottom: 20 }}>
                <MobileOutlined style={{ fontSize: 32, color: '#4f8ef7', marginBottom: 8 }} />
                <div style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>Two-Factor Authentication</div>
                <div style={{ color: '#94a3b8', fontSize: 13, marginTop: 4 }}>
                  Enter the 6-digit code from your authenticator app
                </div>
              </div>
              <Form form={mfaForm} onFinish={handleMfaSubmit} layout="vertical" requiredMark={false}>
                <Form.Item
                  name="totp_code"
                  rules={[
                    { required: true, message: 'Code is required' },
                    { len: 6, message: 'Code must be 6 digits' },
                    { pattern: /^\d+$/, message: 'Digits only' },
                  ]}
                  style={{ marginBottom: 16 }}
                >
                  <Input
                    prefix={<SafetyOutlined style={{ color: '#4f8ef7' }} />}
                    placeholder="000000"
                    maxLength={6}
                    size="large"
                    style={{ textAlign: 'center', letterSpacing: 8, fontSize: 20, borderRadius: 10, height: 52 }}
                    autoFocus
                  />
                </Form.Item>
                <Form.Item style={{ marginBottom: 12 }}>
                  <Button
                    type="primary" htmlType="submit" loading={mfaLoading} block
                    style={{ height: 50, borderRadius: 12, background: 'linear-gradient(135deg,#4f8ef7,#1d5ed8)', border: 'none', fontWeight: 700, fontSize: 15 }}
                  >
                    {mfaLoading ? 'Verifying…' : 'Verify Code'}
                  </Button>
                </Form.Item>
                <div style={{ textAlign: 'center' }}>
                  <Button type="link" size="small" onClick={() => { setMfaRequired(false); setMfaPendingToken(null); }}>
                    ← Back to login
                  </Button>
                </div>
              </Form>
            </div>
          )}

          {/* Form */}
          {!mfaRequired && (
          <Form name="login" onFinish={handleSubmit} layout="vertical" requiredMark={false}>

            <Form.Item
              name="username"
              style={{ marginBottom: 16 }}
              rules={[{ required: true, message: 'Username is required' }]}
            >
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6, letterSpacing: '0.02em' }}>
                  USERNAME
                </label>
                <Input
                  prefix={<UserOutlined style={{ color: focused === 'username' ? '#4f8ef7' : '#9ca3af', fontSize: 14, marginRight: 4 }} />}
                  placeholder="Enter your username"
                  size="large"
                  style={inputStyle('username')}
                  onFocus={() => setFocused('username')}
                  onBlur={() => setFocused(null)}
                />
              </div>
            </Form.Item>

            <Form.Item
              name="password"
              style={{ marginBottom: 20 }}
              rules={[{ required: true, message: 'Password is required' }]}
            >
              <div>
                <label style={{ display: 'block', fontSize: 12, fontWeight: 600, color: '#374151', marginBottom: 6, letterSpacing: '0.02em' }}>
                  PASSWORD
                </label>
                <Input.Password
                  prefix={<LockOutlined style={{ color: focused === 'password' ? '#4f8ef7' : '#9ca3af', fontSize: 14, marginRight: 4 }} />}
                  placeholder="Enter your password"
                  size="large"
                  style={inputStyle('password')}
                  onFocus={() => setFocused('password')}
                  onBlur={() => setFocused(null)}
                  iconRender={(visible) => visible ? <EyeTwoTone twoToneColor="#4f8ef7" /> : <EyeInvisibleOutlined style={{ color: '#9ca3af' }} />}
                />
              </div>
            </Form.Item>

            {/* Remember me */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
              <Form.Item name="remember" valuePropName="checked" style={{ margin: 0 }}>
                <Checkbox style={{ fontSize: 13, color: '#64748b' }}>
                  Keep me signed in
                </Checkbox>
              </Form.Item>
              <span style={{ fontSize: 13, color: '#4f8ef7', cursor: 'pointer', fontWeight: 500 }}>
                Forgot password?
              </span>
            </div>

            {/* Submit */}
            <Form.Item style={{ marginBottom: 20 }}>
              <Button
                type="primary"
                htmlType="submit"
                loading={loading}
                block
                style={{
                  height: 50,
                  borderRadius: 12,
                  background: loading ? undefined : 'linear-gradient(135deg, #4f8ef7 0%, #1d5ed8 100%)',
                  border: 'none',
                  fontSize: 15,
                  fontWeight: 700,
                  letterSpacing: '0.02em',
                  boxShadow: '0 6px 20px rgba(79,142,247,0.4)',
                  transition: 'all 0.2s',
                }}
              >
                {loading ? 'Authenticating…' : (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                    Sign In <RightOutlined style={{ fontSize: 12 }} />
                  </span>
                )}
              </Button>
            </Form.Item>
          </Form>
          )}

          {/* Trust indicators */}
          <div style={{
            display: 'flex', justifyContent: 'center', gap: 20,
            paddingTop: 20, borderTop: '1px solid #f1f5f9',
          }}>
            {[
              { icon: <LockOutlined />,         label: 'TLS Encrypted'   },
              { icon: <SafetyOutlined />,        label: 'Secure Session'  },
              { icon: <CheckCircleFilled />,     label: 'Audit Logged'    },
            ].map((t, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 5 }}>
                <span style={{ color: '#22c55e', fontSize: 11 }}>{t.icon}</span>
                <span style={{ color: '#94a3b8', fontSize: 10, fontWeight: 500 }}>{t.label}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div style={{ marginTop: 28, textAlign: 'center' }}>
          <div style={{ color: '#94a3b8', fontSize: 12 }}>
            © {year} Apex POB · All rights reserved
          </div>
          <div style={{ fontSize: 11, marginTop: 4 }}>
            <span style={{ color: '#cbd5e1' }}>Apex POB v2.0</span>
          </div>
        </div>
      </div>

      {/* ─── Global keyframes ─────────────────────────────── */}
      <style>{`
        @keyframes orbFloat {
          0%,100% { transform: translateY(0px) scale(1); }
          33%      { transform: translateY(-28px) scale(1.04); }
          66%      { transform: translateY(14px) scale(0.97); }
        }
        @keyframes pulse {
          0%,100% { opacity: 1; transform: scale(1); }
          50%      { opacity: 0.5; transform: scale(1.3); }
        }

        /* Smooth hover lift on submit button */
        .ant-btn-primary:not(.ant-btn-loading):hover {
          transform: translateY(-1px);
          box-shadow: 0 10px 28px rgba(79,142,247,0.5) !important;
        }
        .ant-btn-primary:not(.ant-btn-loading):active {
          transform: translateY(0);
        }

        /* Input focus animation */
        .ant-input, .ant-input-password .ant-input {
          transition: all 0.2s ease !important;
        }

        /* Remove Ant Design default input border override */
        .ant-input-affix-wrapper {
          border-radius: 10px !important;
          transition: all 0.2s ease !important;
        }
        .ant-input-affix-wrapper-focused {
          box-shadow: 0 0 0 3px rgba(79,142,247,0.12) !important;
          border-color: #4f8ef7 !important;
        }

        /* Checkbox style */
        .ant-checkbox-checked .ant-checkbox-inner {
          background-color: #4f8ef7 !important;
          border-color: #4f8ef7 !important;
        }

        /* Responsive: stack on small screens */
        @media (max-width: 820px) {
          div[style*="flex: 0 0 52%"] {
            display: none !important;
          }
        }
      `}</style>
    </div>
  );
};

export default Login;
