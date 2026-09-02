import React, { useState, useEffect } from 'react';
import {
  Form,
  Input,
  Button,
  Card,
  Checkbox,
  message,
  Alert,
  Row,
  Col,
  Typography,
  Space,
  Divider,
  Spin
} from 'antd';
import {
  UserOutlined,
  LockOutlined,
  EyeInvisibleOutlined,
  EyeTwoTone,
  LoginOutlined,
  WarningOutlined,
  CheckCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';
import { useNavigate, useLocation } from 'react-router-dom';

const { Title, Text, Link } = Typography;

const EnhancedLogin = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const [rememberMe, setRememberMe] = useState(false);
  const [loginAttempts, setLoginAttempts] = useState(0);
  const [showError, setShowError] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // Check for existing token on mount
  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (token) {
      // Validate token
      validateToken(token);
    }
  }, []);

  const validateToken = async (token) => {
    try {
      const response = await axios.get('/api/v1/auth/me', {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      if (response.data) {
        // Token is valid, redirect to dashboard
        navigate('/dashboard');
      }
    } catch (error) {
      // Token is invalid, remove it
      localStorage.removeItem('access_token');
      localStorage.removeItem('user_info');
    }
  };

  const handleLogin = async (values) => {
    setLoading(true);
    setShowError(false);
    
    try {
      // Determine which login endpoint to use
      const isProduction = process.env.NODE_ENV === 'production';
      const endpoint = isProduction ? '/api/v1/auth/production-login' : '/api/v1/auth/simple-login';
      
      const response = await axios.post(endpoint, {
        username: values.username,
        password: values.password
      });
      
      if (response.data.access_token) {
        // Store token and user info
        localStorage.setItem('access_token', response.data.access_token);
        localStorage.setItem('user_info', JSON.stringify(response.data.user));
        
        if (rememberMe) {
          localStorage.setItem('remember_username', values.username);
        } else {
          localStorage.removeItem('remember_username');
        }
        
        message.success({
          content: 'Login successful!',
          icon: <CheckCircleOutlined />,
          duration: 3
        });
        
        // Redirect to intended page or dashboard
        const from = location.state?.from?.pathname || '/dashboard';
        navigate(from, { replace: true });
        
      } else {
        throw new Error('No access token received');
      }
      
    } catch (error) {
      console.error('Login error:', error);
      
      // Increment login attempts
      const newAttempts = loginAttempts + 1;
      setLoginAttempts(newAttempts);
      
      // Show appropriate error message
      let errorMsg = 'Login failed. Please check your credentials.';
      
      if (error.response) {
        const status = error.response.status;
        const detail = error.response.data?.detail;
        
        if (status === 401) {
          if (detail?.includes('inactive')) {
            errorMsg = 'Your account is inactive. Please contact administrator.';
          } else if (detail?.includes('credentials')) {
            errorMsg = 'Invalid username or password.';
          } else {
            errorMsg = 'Authentication failed. Please try again.';
          }
        } else if (status === 429) {
          errorMsg = 'Too many login attempts. Please try again later.';
        } else if (status >= 500) {
          errorMsg = 'Server error. Please try again later.';
        }
      }
      
      setErrorMessage(errorMsg);
      setShowError(true);
      
      message.error({
        content: errorMsg,
        icon: <WarningOutlined />,
        duration: 5
      });
      
    } finally {
      setLoading(false);
    }
  };

  const handleDemoLogin = () => {
    form.setFieldsValue({
      username: 'admin',
      password: 'admin123'
    });
    message.info({
      content: 'Demo credentials loaded',
      duration: 2
    });
  };

  const handleForgotPassword = () => {
    message.info('Password reset feature coming soon!');
  };

  // Load remembered username
  useEffect(() => {
    const rememberedUsername = localStorage.getItem('remember_username');
    if (rememberedUsername) {
      form.setFieldsValue({ username: rememberedUsername });
      setRememberMe(true);
    }
  }, []);

  return (
    <div style={{
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      padding: '20px'
    }}>
      <Row justify="center" align="middle">
        <Col xs={24} sm={20} md={16} lg={12} xl={8}>
          <Card
            style={{
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.12)',
              borderRadius: '12px',
              border: 'none',
              overflow: 'hidden'
            }}
            bodyStyle={{
              padding: '40px'
            }}
          >
            {/* Header */}
            <div style={{ textAlign: 'center', marginBottom: '32px' }}>
              <img
                src={`${process.env.PUBLIC_URL || ''}/logo/apex-mark.png`}
                alt="Apex POB"
                style={{
                  width: 90,
                  height: 90,
                  objectFit: 'contain',
                  margin: '0 auto 12px',
                  display: 'block',
                  borderRadius: 12,
                }}
              />
              <Title level={3} style={{ margin: '8px 0 4px 0', color: '#262626' }}>
                Apex POB
              </Title>
              <Text type="secondary" style={{ fontSize: '13px' }}>
                Personnel on Board Management System
              </Text>
            </div>

            {/* Error Alert */}
            {showError && (
              <Alert
                message={errorMessage}
                type="error"
                showIcon
                closable
                onClose={() => setShowError(false)}
                style={{ marginBottom: '24px' }}
              />
            )}

            {/* Login Form */}
            <Form
              form={form}
              name="login"
              onFinish={handleLogin}
              size="large"
              layout="vertical"
              requiredMark={false}
            >
              <Form.Item
                name="username"
                rules={[
                  { required: true, message: 'Please input your username!' },
                  { min: 3, message: 'Username must be at least 3 characters!' },
                  { max: 50, message: 'Username cannot exceed 50 characters!' }
                ]}
              >
                <Input
                  prefix={<UserOutlined style={{ color: '#1890ff' }} />}
                  placeholder="Username or Email"
                  autoComplete="username"
                  style={{ borderRadius: '8px' }}
                />
              </Form.Item>

              <Form.Item
                name="password"
                rules={[
                  { required: true, message: 'Please input your password!' },
                  { min: 6, message: 'Password must be at least 6 characters!' }
                ]}
              >
                <Input.Password
                  prefix={<LockOutlined style={{ color: '#1890ff' }} />}
                  placeholder="Password"
                  autoComplete="current-password"
                  style={{ borderRadius: '8px' }}
                  iconRender={(visible) => (
                    <span
                      onClick={() => setShowPassword(!visible)}
                      style={{ cursor: 'pointer' }}
                    >
                      {visible ? <EyeTwoTone /> : <EyeInvisibleOutlined />}
                    </span>
                  )}
                />
              </Form.Item>

              <Form.Item>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Checkbox
                    checked={rememberMe}
                    onChange={(e) => setRememberMe(e.target.checked)}
                  >
                    Remember me
                  </Checkbox>
                  <Link 
                    to="/forgot-password" 
                    style={{ color: '#1890ff' }}
                    onClick={handleForgotPassword}
                  >
                    Forgot password?
                  </Link>
                </div>
              </Form.Item>

              <Form.Item style={{ marginBottom: '8px' }}>
                <Button
                  type="primary"
                  htmlType="submit"
                  block
                  size="large"
                  loading={loading}
                  icon={<LoginOutlined />}
                  style={{
                    height: '48px',
                    borderRadius: '8px',
                    background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    border: 'none',
                    fontSize: '16px',
                    fontWeight: '500'
                  }}
                >
                  {loading ? 'Signing in...' : 'Sign In'}
                </Button>
              </Form.Item>
            </Form>

            <Divider style={{ margin: '24px 0' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                Demo Access
              </Text>
            </Divider>

            {/* Demo Account */}
            <div style={{ textAlign: 'center' }}>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Button
                  block
                  size="large"
                  onClick={handleDemoLogin}
                  style={{
                    borderRadius: '8px',
                    border: '1px solid #d9d9d9',
                    background: '#fafafa'
                  }}
                >
                  Use Demo Account
                </Button>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  Default: admin / admin123
                </Text>
              </Space>
            </div>

            {/* Footer */}
            <div style={{ textAlign: 'center', marginTop: '24px' }}>
              <Space split={<Divider type="vertical" />}>
                <Link to="/help" style={{ fontSize: '12px', color: '#666' }}>
                  Help
                </Link>
                <Link to="/privacy" style={{ fontSize: '12px', color: '#666' }}>
                  Privacy
                </Link>
                <Link to="/terms" style={{ fontSize: '12px', color: '#666' }}>
                  Terms
                </Link>
              </Space>
            </div>
          </Card>

          {/* Security Notice */}
          <Card
            style={{
              marginTop: '16px',
              background: '#fff7e6',
              border: '1px solid #ffd591',
              borderRadius: '8px'
            }}
            size="small"
          >
            <div style={{ display: 'flex', alignItems: 'center' }}>
              <WarningOutlined style={{ color: '#faad14', marginRight: '8px' }} />
              <Text style={{ fontSize: '12px', color: '#faad14' }}>
                <strong>Security Notice:</strong> This is a secure system. 
                Unauthorized access attempts are logged and monitored.
              </Text>
            </div>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default EnhancedLogin;
