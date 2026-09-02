import { useState } from 'react';
import { Tabs, Typography, Space } from 'antd';
import { AimOutlined, WarningOutlined, BarChartOutlined, TeamOutlined, SafetyOutlined,
         CameraOutlined, KeyOutlined } from '@ant-design/icons';
import FenceMapEditor from './FenceMapEditor';
import StaffAssignment from './StaffAssignment';
import ClockInRules from './ClockInRules';
import ExceptionQueue from './ExceptionQueue';
import GeofenceSummary from './GeofenceSummary';
import FaceEnrolment from './FaceEnrolment';
import StaffLogins from './StaffLogins';

const { Title, Text } = Typography;

export default function GeofenceManagement() {
  const [tab, setTab] = useState('fences');

  return (
    <div style={{ padding: 16 }}>
      <Space direction="vertical" size={2} style={{ marginBottom: 16 }}>
        <Title level={4} style={{ margin: 0 }}>Geofenced attendance</Title>
        <Text type="secondary">
          Warehouse boundaries, and the punches that fell outside them.
        </Text>
      </Space>

      <Tabs
        activeKey={tab}
        onChange={setTab}
        destroyInactiveTabPane
        items={[
          { key: 'fences', label: <Space><AimOutlined />Warehouse fences</Space>,
            children: <FenceMapEditor /> },
          { key: 'staff', label: <Space><TeamOutlined />Staff</Space>,
            children: <StaffAssignment /> },
          { key: 'logins', label: <Space><KeyOutlined />Staff logins</Space>,
            children: <StaffLogins /> },
          { key: 'faces', label: <Space><CameraOutlined />Face registration</Space>,
            children: <FaceEnrolment /> },
          { key: 'exceptions', label: <Space><WarningOutlined />Exceptions</Space>,
            children: <ExceptionQueue /> },
          { key: 'summary', label: <Space><BarChartOutlined />Summary</Space>,
            children: <GeofenceSummary /> },
          { key: 'rules', label: <Space><SafetyOutlined />Clock-in rules</Space>,
            children: <ClockInRules /> },
        ]}
      />
    </div>
  );
}
