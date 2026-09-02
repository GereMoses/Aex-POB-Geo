import React, { useState, useEffect, useRef } from 'react';
import {
  Avatar,
  Badge,
  Dropdown,
  Space,
  Button,
  Input,
  Typography,
  Tooltip,
  Modal,
  List,
  Tag,
  Switch,
  Divider,
  message,
  Popover,
  Calendar,
  Card,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd';
import {
  BellOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  SearchOutlined,
  GlobalOutlined,
  TeamOutlined,
  FileTextOutlined,
  BarChartOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined,
  QuestionCircleOutlined,
  SyncOutlined,
  FilterOutlined,
  ExportOutlined,
  DownloadOutlined,
  PrinterOutlined,
  ShareAltOutlined,
  StarOutlined,
  StarFilled,
  HeartOutlined,
  EyeOutlined,
  EditOutlined,
  DeleteOutlined,
  LockOutlined,
  UnlockOutlined,
  ReloadOutlined
} from '@ant-design/icons';
import { useAuth } from '../../contexts/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const { Text, Title } = Typography;
const { Search } = Input;

const AdvancedHeader = ({ collapsed, onToggleSidebar, onToggleFullscreen, isFullscreen }) => {
  const { user, logout, hasPermission, notifications, updateNotifications } = useAuth();
  const [notificationVisible, setNotificationVisible] = useState(false);
  const [profileVisible, setProfileVisible] = useState(false);
  const [searchVisible, setSearchVisible] = useState(false);
  const [globalSearchValue, setGlobalSearchValue] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [currentTime, setCurrentTime] = useState(new Date());
  const [systemStats, setSystemStats] = useState({});
  const searchInputRef = useRef(null);

  // Update current time
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Load system stats
  useEffect(() => {
    loadSystemStats();
  }, []);

  // Load notifications
  useEffect(() => {
    loadNotifications();
  }, []);

  const loadSystemStats = async () => {
    try {
      const response = await axios.get('/api/v1/system/stats');
      setSystemStats(response.data || {});
    } catch (error) {
      console.error('Failed to load system stats:', error);
    }
  };

  const loadNotifications = async () => {
    try {
      const response = await axios.get('/api/v1/notifications');
      updateNotifications(response.data || []);
    } catch (error) {
      console.error('Failed to load notifications:', error);
    }
  };

  const handleGlobalSearch = async (value) => {
    setGlobalSearchValue(value);
    
    if (value.length < 2) {
      setSearchResults([]);
      return;
    }

    setLoading(true);
    try {
      const response = await axios.get(`/api/v1/search?q=${encodeURIComponent(value)}`);
      setSearchResults(response.data?.results || []);
    } catch (error) {
      console.error('Search failed:', error);
      setSearchResults([]);
    } finally {
      setLoading(false);
    }
  };

  const handleNotificationAction = async (notification, action) => {
    try {
      switch (action) {
        case 'mark_read':
          await axios.put(`/api/v1/notifications/${notification.id}/read`);
          updateNotifications(notifications.map(n => 
            n.id === notification.id ? { ...n, read: true } : n
          ));
          message.success('Notification marked as read');
          break;
        
        case 'delete':
          await axios.delete(`/api/v1/notifications/${notification.id}`);
          updateNotifications(notifications.filter(n => n.id !== notification.id));
          message.success('Notification deleted');
          break;
        
        case 'archive':
          await axios.put(`/api/v1/notifications/${notification.id}/archive`);
          updateNotifications(notifications.map(n => 
            n.id === notification.id ? { ...n, archived: true } : n
          ));
          message.success('Notification archived');
          break;
      }
    } catch (error) {
      console.error('Notification action failed:', error);
      message.error('Failed to process notification');
    }
  };

  const getNotificationIcon = (type) => {
    const icons = {
      info: <InfoCircleOutlined style={{ color: '#1890ff' }} />,
      success: <CheckCircleOutlined style={{ color: '#52c41a' }} />,
      warning: <WarningOutlined style={{ color: '#faad14' }} />,
      error: <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
    };
    return icons[type] || <InfoCircleOutlined />;
  };

  const getNotificationColor = (type) => {
    const colors = {
      info: '#1890ff',
      success: '#52c41a',
      warning: '#faad14',
      error: '#ff4d4f'
    };
    return colors[type] || '#1890ff';
  };

  const unreadCount = notifications?.filter(n => !n.read).length || 0;

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => setProfileVisible(true)
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => window.location.href = '/settings'
    },
    {
      key: 'help',
      icon: <QuestionCircleOutlined />,
      label: 'Help & Support',
      onClick: () => window.open('/help', '_blank')
    },
    {
      type: 'divider'
    },
    {
      key: 'theme',
      icon: <SyncOutlined />,
      label: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Theme</span>
          <Switch size="small" defaultChecked />
        </div>
      ),
      onClick: () => message.info('Theme customization coming soon!')
    },
    {
      key: 'language',
      icon: <GlobalOutlined />,
      label: (
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <span>Language</span>
          <Select defaultValue="en" size="small" style={{ width: 80 }}>
            <Select.Option value="en">English</Select.Option>
            <Select.Option value="fr">Français</Select.Option>
          </Select>
        </div>
      )
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: () => logout(),
      danger: true
    }
  ];

  const notificationMenuItems = (notification) => [
    {
      key: 'mark_read',
      icon: <CheckCircleOutlined />,
      label: 'Mark as Read',
      disabled: notification.read,
      onClick: () => handleNotificationAction(notification, 'mark_read')
    },
    {
      key: 'archive',
      icon: <FileTextOutlined />,
      label: 'Archive',
      disabled: notification.archived,
      onClick: () => handleNotificationAction(notification, 'archive')
    },
    {
      type: 'divider'
    },
    {
      key: 'delete',
      icon: <DeleteOutlined />,
      label: 'Delete',
      danger: true,
      onClick: () => handleNotificationAction(notification, 'delete')
    }
  ];

  const quickActions = [
    {
      key: 'new-report',
      icon: <FileTextOutlined />,
      label: 'New Report',
      color: '#1890ff',
      onClick: () => window.location.href = '/reports/custom'
    },
    {
      key: 'export-data',
      icon: <ExportOutlined />,
      label: 'Export Data',
      color: '#52c41a',
      onClick: () => message.info('Export feature coming soon!')
    },
    {
      key: 'print-report',
      icon: <PrinterOutlined />,
      label: 'Print Report',
      color: '#faad14',
      onClick: () => window.print()
    },
    {
      key: 'share-dashboard',
      icon: <ShareAltOutlined />,
      label: 'Share Dashboard',
      color: '#722ed1',
      onClick: () => message.info('Share feature coming soon!')
    }
  ];

  const systemHealthItems = [
    {
      title: 'System Status',
      value: systemStats.system_status || 'Healthy',
      prefix: <CheckCircleOutlined style={{ color: '#52c41a' }} />
    },
    {
      title: 'Active Users',
      value: systemStats.active_users || 0,
      prefix: <TeamOutlined style={{ color: '#1890ff' }} />
    },
    {
      title: 'Server Load',
      value: systemStats.server_load || '0%',
      prefix: <BarChartOutlined style={{ color: '#faad14' }} />
    },
    {
      title: 'Database',
      value: systemStats.database_status || 'Connected',
      prefix: <SyncOutlined style={{ color: '#52c41a' }} />
    }
  ];

  return (
    <div style={{
      background: '#fff',
      padding: '0 24px',
      boxShadow: '0 2px 8px rgba(0, 0, 0, 0.06)',
      zIndex: 1000,
      position: 'sticky',
      top: 0
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: '64px' }}>
        
        {/* Left Section - Logo and Search */}
        <div style={{ display: 'flex', alignItems: 'center', flex: 1 }}>
          {/* Collapse Toggle */}
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={onToggleSidebar}
            style={{ marginRight: '16px' }}
          />

          {/* Company Logo */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            marginRight: '24px'
          }}>
            <img
              src={`${process.env.PUBLIC_URL || ''}/logo/apex-mark.png`}
              alt="Apex POB"
              style={{ width: 32, height: 32, objectFit: 'contain', borderRadius: 6 }}
            />
            <Title level={4} style={{ margin: '0 0 0 10px', color: '#262626', fontSize: 15 }}>
              Apex POB
            </Title>
          </div>

          {/* Global Search */}
          <Popover
            content={
              <div style={{ width: '400px', maxHeight: '400px', overflow: 'auto' }}>
                <Search
                  placeholder="Search anything..."
                  value={globalSearchValue}
                  onChange={(e) => handleGlobalSearch(e.target.value)}
                  style={{ marginBottom: '12px' }}
                  prefix={<SearchOutlined />}
                  loading={loading}
                  ref={searchInputRef}
                />
                
                {searchResults.length > 0 && (
                  <List
                    size="small"
                    dataSource={searchResults}
                    renderItem={(item) => (
                      <List.Item
                        onClick={() => {
                          if (item.type === 'report') {
                            window.location.href = `/reports/${item.id}`;
                          } else if (item.type === 'personnel') {
                            window.location.href = `/personnel/${item.id}`;
                          }
                        }}
                        style={{ cursor: 'pointer' }}
                      >
                        <List.Item.Meta
                          avatar={<Avatar icon={<FileTextOutlined />} size="small" />}
                          title={item.title}
                          description={item.description}
                        />
                      </List.Item>
                    )}
                  />
                )}
              </div>
            }
            trigger="click"
            placement="bottomLeft"
            title="Global Search (Ctrl+K)"
          >
            <Button
              type="text"
              icon={<SearchOutlined />}
              onClick={() => {
                setSearchVisible(true);
                setTimeout(() => searchInputRef.current?.focus(), 100);
              }}
            >
              Search (Ctrl+K)
            </Button>
          </Popover>
        </div>

        {/* Center Section - System Stats */}
        <div style={{ display: 'flex', alignItems: 'center', margin: '0 24px' }}>
          <Row gutter={16}>
            {systemHealthItems.map((item, index) => (
              <Col key={index}>
                <Statistic
                  title={item.title}
                  value={item.value}
                  prefix={item.prefix}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
            ))}
          </Row>
        </div>

        {/* Right Section - Notifications, User, Quick Actions */}
        <div style={{ display: 'flex', alignItems: 'center' }}>
          
          {/* Quick Actions */}
          <Dropdown
            menu={{
              items: quickActions.map(action => ({
                key: action.key,
                icon: action.icon,
                label: action.label,
                onClick: action.onClick
              }))
            }}
            trigger="click"
            placement="bottomRight"
          >
            <Button
              type="text"
              icon={<FilterOutlined />}
              style={{ marginRight: '8px' }}
            >
              Quick Actions
            </Button>
          </Dropdown>

          {/* Notifications */}
          <Dropdown
            overlay={
              <div style={{ width: '350px', maxHeight: '400px', overflow: 'auto' }}>
                <div style={{ padding: '8px 12px', borderBottom: '1px solid #f0f0f0' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>Notifications</Text>
                    <Button
                      type="text"
                      size="small"
                      onClick={() => loadNotifications()}
                    >
                      <ReloadOutlined />
                    </Button>
                  </div>
                </div>
                
                <List
                  size="small"
                  dataSource={notifications.slice(0, 10)}
                  renderItem={(notification) => (
                    <List.Item
                      style={{ 
                        padding: '8px 0',
                        background: notification.read ? '#f9f9f9' : '#fff'
                      }}
                      actions={[
                        <Dropdown
                          menu={{ items: notificationMenuItems(notification) }}
                          trigger={['click']}
                          placement="bottomRight"
                        >
                          <Button type="text" size="small" icon={<SettingOutlined />} />
                        </Dropdown>
                      ]}
                    >
                      <List.Item.Meta
                        avatar={
                          <Avatar
                            icon={getNotificationIcon(notification.type)}
                            style={{
                              backgroundColor: getNotificationColor(notification.type),
                              color: '#fff'
                            }}
                            size="small"
                          />
                        }
                        title={
                          <div>
                            <Text strong={!notification.read}>
                              {notification.title}
                            </Text>
                            <br />
                            <Text type="secondary" style={{ fontSize: '12px' }}>
                              {new Date(notification.created_at).toLocaleString()}
                            </Text>
                          </div>
                        }
                        description={
                          <Text type="secondary" style={{ fontSize: '12px' }}>
                            {notification.message?.substring(0, 80)}
                            {notification.message?.length > 80 && '...'}
                          </Text>
                        }
                      />
                    </List.Item>
                  )}
                />
                
                {notifications.length > 10 && (
                  <div style={{ textAlign: 'center', padding: '12px' }}>
                    <Button type="link" onClick={() => window.location.href = '/notifications'}>
                      View All Notifications
                    </Button>
                  </div>
                )}
              </div>
            }
            trigger="click"
            placement="bottomRight"
          >
            <Badge count={unreadCount} size="small">
              <Button
                type="text"
                icon={<BellOutlined />}
                style={{ marginRight: '8px' }}
              />
            </Badge>
          </Dropdown>

          {/* User Menu */}
          <Dropdown
            menu={{ items: userMenuItems }}
            trigger="click"
            placement="bottomRight"
          >
            <div style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <Avatar
                size="small"
                style={{
                  backgroundColor: '#1890ff',
                  color: '#fff',
                  marginRight: '8px'
                }}
              >
                {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U'}
              </Avatar>
              <div>
                <Text strong>{user?.full_name || 'User'}</Text>
                <br />
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {user?.email || 'user@example.com'}
                </Text>
              </div>
            </div>
          </Dropdown>

          {/* Fullscreen Toggle */}
          <Tooltip title={isFullscreen ? 'Exit Fullscreen' : 'Enter Fullscreen'}>
            <Button
              type="text"
              icon={isFullscreen ? <FullscreenExitOutlined /> : <FullscreenOutlined />}
              onClick={onToggleFullscreen}
              style={{ marginLeft: '8px' }}
            />
          </Tooltip>
        </div>
      </div>

      {/* Current Time Display */}
      <div style={{
        position: 'absolute',
        right: '24px',
        top: '70px',
        background: 'rgba(0, 0, 0, 0.8)',
        color: '#fff',
        padding: '4px 12px',
        borderRadius: '4px',
        fontSize: '12px',
        zIndex: 1001
      }}>
        {currentTime.toLocaleTimeString()}
      </div>

      {/* Profile Modal */}
      <Modal
        title="User Profile"
        open={profileVisible}
        onCancel={() => setProfileVisible(false)}
        footer={null}
        width={600}
      >
        <Row gutter={24}>
          <Col span={8}>
            <div style={{ textAlign: 'center' }}>
              <Avatar
                size={80}
                style={{
                  backgroundColor: '#1890ff',
                  color: '#fff',
                  fontSize: '32px'
                }}
              >
                {user?.full_name?.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2) || 'U'}
              </Avatar>
              <div style={{ marginTop: '12px' }}>
                <Button type="primary" icon={<EditOutlined />} block>
                  Change Avatar
                </Button>
              </div>
            </div>
          </Col>
          <Col span={16}>
            <Card title="Profile Information" size="small">
              <p><strong>Full Name:</strong> {user?.full_name || 'N/A'}</p>
              <p><strong>Email:</strong> {user?.email || 'N/A'}</p>
              <p><strong>Phone:</strong> {user?.phone || 'N/A'}</p>
              <p><strong>Department:</strong> {user?.department || 'N/A'}</p>
              <p><strong>Role:</strong> {user?.roles?.join(', ') || user?.role || 'N/A'}</p>
              <p><strong>Last Login:</strong> {user?.last_login ? new Date(user.last_login).toLocaleString() : 'N/A'}</p>
            </Card>
          </Col>
        </Row>
      </Modal>
    </div>
  );
};

export default AdvancedHeader;
