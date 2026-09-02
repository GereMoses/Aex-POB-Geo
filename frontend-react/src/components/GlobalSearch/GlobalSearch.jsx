import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Modal, Input, List, Tag, Space, Typography, Spin, Empty } from 'antd';
import {
  SearchOutlined, UserOutlined, DesktopOutlined, EnvironmentOutlined,
  IdcardOutlined, TeamOutlined, BankOutlined, ArrowRightOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import apiService from '../../services/api';

const { Text } = Typography;

const TYPE_META = {
  personnel:   { color: '#3B82F6', icon: <UserOutlined />,        label: 'Personnel' },
  device:      { color: '#8B5CF6', icon: <DesktopOutlined />,     label: 'Device' },
  zone:        { color: '#10B981', icon: <EnvironmentOutlined />,  label: 'Warehouse' },
  visitor:     { color: '#F59E0B', icon: <IdcardOutlined />,       label: 'Visitor' },
  contractor:  { color: '#EF4444', icon: <TeamOutlined />,         label: 'Contractor' },
  department:  { color: '#6366F1', icon: <BankOutlined />,         label: 'Department' },
};

let _debounce = null;

const GlobalSearch = ({ open, onClose }) => {
  const [query, setQuery]     = useState('');
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(0);
  const navigate = useNavigate();
  const inputRef = useRef(null);

  const search = useCallback((q) => {
    if (_debounce) clearTimeout(_debounce);
    if (!q || q.length < 2) { setResults([]); setLoading(false); return; }
    setLoading(true);
    _debounce = setTimeout(async () => {
      try {
        const res = await apiService.get(`/api/v1/search/?q=${encodeURIComponent(q)}`);
        setResults(res?.results ?? []);
        setSelected(0);
      } catch {
        setResults([]);
      } finally {
        setLoading(false);
      }
    }, 250);
  }, []);

  useEffect(() => {
    if (open) {
      setQuery(''); setResults([]); setSelected(0);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  useEffect(() => { search(query); }, [query, search]);

  const navigate_to = (result) => {
    onClose();
    navigate(result.url);
  };

  const handleKey = (e) => {
    if (e.key === 'ArrowDown') { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
    if (e.key === 'ArrowUp')   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
    if (e.key === 'Enter' && results[selected]) navigate_to(results[selected]);
    if (e.key === 'Escape') onClose();
  };

  return (
    <Modal
      open={open}
      onCancel={onClose}
      footer={null}
      closable={false}
      width={600}
      styles={{ body: { padding: 0 } }}
      style={{ top: 120 }}
    >
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #f0f0f0' }}>
        <Input
          ref={inputRef}
          prefix={loading ? <Spin size="small" /> : <SearchOutlined style={{ color: '#9CA3AF' }} />}
          placeholder="Search personnel, warehouses…"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onKeyDown={handleKey}
          size="large"
          variant="borderless"
          autoComplete="off"
          style={{ fontSize: 16 }}
        />
      </div>

      <div style={{ maxHeight: 440, overflowY: 'auto' }}>
        {query.length >= 2 && !loading && results.length === 0 ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={`No results for "${query}"`}
            style={{ padding: '32px 0' }}
          />
        ) : (
          <List
            dataSource={results}
            renderItem={(item, idx) => {
              const meta = TYPE_META[item.type] || { color: '#9CA3AF', icon: <SearchOutlined />, label: item.type };
              const isSelected = idx === selected;
              return (
                <List.Item
                  key={`${item.type}-${item.id}`}
                  onClick={() => navigate_to(item)}
                  onMouseEnter={() => setSelected(idx)}
                  style={{
                    padding: '10px 16px',
                    cursor: 'pointer',
                    background: isSelected ? '#EFF6FF' : 'transparent',
                    borderLeft: isSelected ? `3px solid ${meta.color}` : '3px solid transparent',
                    transition: 'all 0.1s',
                  }}
                >
                  <Space style={{ width: '100%' }}>
                    <div style={{
                      width: 32, height: 32, borderRadius: 8,
                      background: `${meta.color}18`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      color: meta.color, flexShrink: 0,
                    }}>
                      {meta.icon}
                    </div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 500, fontSize: 13, color: '#1F2937' }}>{item.label}</div>
                      <div style={{ fontSize: 11, color: '#9CA3AF', marginTop: 1 }}>{item.sub}</div>
                    </div>
                    <Tag
                      style={{
                        fontSize: 10, background: `${meta.color}18`,
                        color: meta.color, border: 'none', flexShrink: 0,
                      }}
                    >
                      {meta.label}
                    </Tag>
                    {isSelected && <ArrowRightOutlined style={{ color: meta.color, flexShrink: 0 }} />}
                  </Space>
                </List.Item>
              );
            }}
          />
        )}
      </div>

      {results.length > 0 && (
        <div style={{
          padding: '8px 16px', borderTop: '1px solid #f0f0f0',
          display: 'flex', gap: 12, fontSize: 11, color: '#9CA3AF',
        }}>
          <span>↑↓ navigate</span>
          <span>↵ open</span>
          <span>Esc close</span>
        </div>
      )}
    </Modal>
  );
};

export default GlobalSearch;
