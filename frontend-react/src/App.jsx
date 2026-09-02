import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ConfigProvider, App as AntdApp, Result, Button } from 'antd';
// import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { ThemeProvider, useTheme } from './contexts/ThemeContext';
import 'antd/dist/reset.css';
import './App.css';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard/Dashboard';
import Personnel from './pages/Personnel';
import AttendanceManagement from './pages/Attendance/AttendanceManagement';
import Reports from './pages/Reports/Reports';
import Settings from './pages/Settings/Settings';
import Login from './pages/Auth/Login';
import ZoneManagement from './pages/Zones/ZoneManagement';
import GeofenceManagement from './pages/Geofence/GeofenceManagement';
import Payroll from './pages/Payroll/Payroll';
import SubscriptionDashboard from './pages/Subscription/SubscriptionDashboard';
import LicenseExpiredScreen from './components/LicenseExpiredScreen';
import NotificationsPage from './pages/Notifications/NotificationsPage';

const ThemedShell = ({ children }) => {
  const { antdConfig } = useTheme();
  return <ConfigProvider theme={antdConfig} warning={{ strict: false }}>{children}</ConfigProvider>;
};

// Create React Query client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  const [isAuthenticated, setIsAuthenticated] = React.useState(false);
  const [user, setUser] = React.useState(null);
  const [licenseStatus, setLicenseStatus] = React.useState('active'); // optimistic default

  React.useEffect(() => {
    const token = localStorage.getItem('token') || localStorage.getItem('authToken') || localStorage.getItem('access_token');
    if (!token) {
      setIsAuthenticated(false);
      setUser(null);
      return;
    }

    // Always validate the token with the server — never trust user_info alone
    // because the token may have expired between sessions.
    // Use cached user_info to render optimistically while the check runs.
    const stored = localStorage.getItem('user_info');
    if (stored) {
      try {
        setUser(JSON.parse(stored));
        setIsAuthenticated(true);
      } catch (_) { /* continue to server check */ }
    }

    fetch('/api/v1/auth/me', { headers: { Authorization: `Bearer ${token}` } })
      .then(r => r.ok ? r.json() : Promise.reject(r.status))
      .then(u => {
        localStorage.setItem('user_info', JSON.stringify(u));
        setUser(u);
        setIsAuthenticated(true);
      })
      .catch(() => {
        // Token is expired or invalid — force re-login
        ['token', 'authToken', 'access_token', 'user_info'].forEach(k => localStorage.removeItem(k));
        setIsAuthenticated(false);
        setUser(null);
      });
  }, []);

  const ProtectedRoute = ({ permission, children }) => {
    if (permission && !user?.is_superuser && !(user?.permissions || []).includes(permission)) {
      return (
        <Result
          status="403"
          title="Access Denied"
          subTitle="You do not have permission to view this page."
          extra={<Button type="primary" onClick={() => window.history.back()}>Go Back</Button>}
        />
      );
    }
    return children;
  };

  const handleLogin = (userData, token) => {
    setIsAuthenticated(true);
    setUser(userData);
    // Write the canonical key; remove legacy aliases to keep storage clean
    localStorage.setItem('token', token);
    localStorage.removeItem('authToken');
    localStorage.removeItem('access_token');
  };

  const handleLogout = React.useCallback(async () => {
    // Revoke the token server-side before clearing local state
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('/api/v1/auth/logout', {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        });
      }
    } catch (_) {
      // best-effort — always clear local state even if API call fails
    }
    setIsAuthenticated(false);
    setUser(null);
    ['token', 'authToken', 'access_token', 'user_info'].forEach(k => localStorage.removeItem(k));
  }, []);

  // Listen for 401 events from the API service
  React.useEffect(() => {
    window.addEventListener('auth:unauthorized', handleLogout);
    return () => window.removeEventListener('auth:unauthorized', handleLogout);
  }, [handleLogout]);

  // Poll subscription status every 5 minutes; also react to 402 events from api service
  React.useEffect(() => {
    const checkLicense = () => {
      fetch('/api/v1/subscription/status')
        .then(r => r.ok ? r.json() : null)
        .then(data => { if (data?.data?.status) setLicenseStatus(data.data.status); })
        .catch(() => {});
    };
    checkLicense();
    const interval = setInterval(checkLicense, 5 * 60 * 1000);

    const onExpired = () => setLicenseStatus('expired');
    window.addEventListener('license:expired', onExpired);

    return () => {
      clearInterval(interval);
      window.removeEventListener('license:expired', onExpired);
    };
  }, []);

  // Show lock screen when license is expired/missing, UNLESS the logged-in user is Global Admin
  const licenseBlocked = isAuthenticated
    && ['expired', 'no_license'].includes(licenseStatus)
    && !user?.is_global_admin;

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <ThemedShell>
        <AntdApp>
        {!isAuthenticated ? (
          <Router basename={process.env.PUBLIC_URL || "/"} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
            <Routes>
              {/* Public kiosk — accessible without login */}
              {/* Anything else → login */}
              <Route path="/*" element={<Login onLogin={handleLogin} />} />
            </Routes>
          </Router>
        ) : licenseBlocked ? (
          <LicenseExpiredScreen
            status={licenseStatus}
            onUnlocked={() => setLicenseStatus('active')}
            onLoginAsAdmin={handleLogout}
          />
        ) : (
        <Router basename={process.env.PUBLIC_URL || "/"} future={{ v7_startTransition: true, v7_relativeSplatPath: true }}>
          <Layout user={user} onLogout={handleLogout}>
            <Routes>
              {/* Public kiosk — also accessible when logged in */}

              {/* Dashboard — no permission required */}
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />

              {/* Personnel Management */}
              <Route path="/personnel/*" element={<ProtectedRoute permission="personnel.view"><Personnel /></ProtectedRoute>} />

              {/* Payroll */}
              <Route path="/payroll" element={<ProtectedRoute permission="payroll.view"><Payroll /></ProtectedRoute>} />
              <Route path="/payroll/*" element={<ProtectedRoute permission="payroll.view"><Payroll /></ProtectedRoute>} />

              {/* Attendance Management */}
              <Route path="/attendance" element={<ProtectedRoute permission="attendance.view"><AttendanceManagement /></ProtectedRoute>} />
              <Route path="/attendance/transactions" element={<ProtectedRoute permission="attendance.view"><AttendanceManagement /></ProtectedRoute>} />
              <Route path="/attendance/leave" element={<ProtectedRoute permission="attendance.view"><AttendanceManagement /></ProtectedRoute>} />
              <Route path="/attendance/manual-log" element={<ProtectedRoute permission="attendance.view"><AttendanceManagement /></ProtectedRoute>} />
              <Route path="/attendance/summary" element={<ProtectedRoute permission="attendance.view"><AttendanceManagement /></ProtectedRoute>} />

              {/* Device Management */}

              {/* Warehouse Management */}
              <Route path="/zones" element={<ZoneManagement />} />
              <Route path="/geofence" element={<ProtectedRoute permission="attendance.view"><GeofenceManagement /></ProtectedRoute>} />

              {/* Reports */}
              <Route path="/reports" element={<ProtectedRoute permission="reports.view"><Reports /></ProtectedRoute>} />
              <Route path="/reports/attendance" element={<ProtectedRoute permission="reports.view"><Reports /></ProtectedRoute>} />
              <Route path="/reports/personnel" element={<ProtectedRoute permission="reports.view"><Reports /></ProtectedRoute>} />

              {/* Settings */}
              <Route path="/settings" element={<ProtectedRoute permission="settings.view"><Settings /></ProtectedRoute>} />
              <Route path="/settings/users" element={<ProtectedRoute permission="settings.view"><Settings /></ProtectedRoute>} />
              <Route path="/settings/roles" element={<ProtectedRoute permission="settings.view"><Settings /></ProtectedRoute>} />
              <Route path="/settings/system" element={<ProtectedRoute permission="settings.view"><Settings /></ProtectedRoute>} />

              {/* Notifications */}
              <Route path="/notifications" element={<NotificationsPage />} />

              {/* Subscription — Global Admin only */}
              <Route path="/subscription" element={
                user?.is_global_admin
                  ? <SubscriptionDashboard />
                  : <Result status="403" title="Access Denied" subTitle="Global Admin access required." />
              } />

              {/* Any unmatched route (e.g. the 'personnel-group' menu group, which
                  has no page of its own) redirects to the dashboard instead of
                  rendering a blank content area. */}
              <Route path="*" element={<Navigate to="/dashboard" replace />} />
            </Routes>
          </Layout>
        </Router>
        )}
        </AntdApp>
        </ThemedShell>
      </ThemeProvider>

      {/* {process.env.NODE_ENV === 'development' && <ReactQueryDevtools initialIsOpen={false} />} */}
    </QueryClientProvider>
  );
}

export default App;
