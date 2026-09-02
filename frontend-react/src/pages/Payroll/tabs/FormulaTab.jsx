import React, { useState } from 'react';
import {
  Row, Col, Form, Input, Button, Select, InputNumber, Alert,
  Space, Divider, Typography, List, Spin, Tooltip, App,
} from 'antd';
import {
  FunctionOutlined, PlayCircleOutlined, ClearOutlined,
  CheckCircleOutlined, WarningOutlined, CloseCircleOutlined,
  HistoryOutlined, CopyOutlined,
} from '@ant-design/icons';
import { apiCall } from '../payrollApi';

const { Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;

const VARIABLES = [
  { name: 'Basic',          desc: 'Basic salary amount',               example: 'Basic * 0.4'                          },
  { name: 'BasicSalary',    desc: 'Alias for Basic',                   example: 'BasicSalary'                          },
  { name: 'WorkDays',       desc: 'Total scheduled work days',         example: 'WorkDays'                             },
  { name: 'PresentDays',    desc: 'Days employee was present',         example: 'Basic / WorkDays * PresentDays'       },
  { name: 'AbsentDays',     desc: 'Absent days count',                 example: 'Basic / WorkDays * AbsentDays'        },
  { name: 'LeaveDays',      desc: 'Approved leave days',               example: 'LeaveDays'                            },
  { name: 'OTHours',        desc: 'Overtime hours',                    example: 'OTHours * 500'                        },
  { name: 'LateMinutes',    desc: 'Late minutes total',                example: 'LateMinutes * 50'                     },
  { name: 'WorkHours',      desc: 'Total hours worked',                example: 'WorkHours'                            },
  { name: 'ZoneHours',      desc: 'Hours on site at a warehouse',                example: 'ZoneHours * 300'                      },
  { name: 'NightHours',     desc: 'Night-shift hours',                 example: 'NightHours * 200'                     },
  { name: 'HazardDays',     desc: 'Days at a hazard-rated warehouse',              example: 'HazardDays * 1500'                    },
  { name: 'ContractorFlag', desc: '1 if contractor, 0 if staff',       example: 'IF(ContractorFlag, Basic * 1.2, Basic)'},
];

const FUNCTIONS = [
  { name: 'ABS(x)',        desc: 'Absolute value'                    },
  { name: 'ROUND(x, n)',   desc: 'Round to n decimal places'         },
  { name: 'MIN(a, b)',     desc: 'Minimum of two values'             },
  { name: 'MAX(a, b)',     desc: 'Maximum of two values'             },
  { name: 'IF(cond, t, f)', desc: 'Return t if cond is true, else f' },
  { name: 'CEIL(x)',       desc: 'Round up to nearest integer'       },
  { name: 'FLOOR(x)',      desc: 'Round down to nearest integer'     },
  { name: 'SUM(a, b, …)',  desc: 'Sum of values'                     },
];

const SNIPPETS = [
  { label: 'Housing Allowance (40%)',    formula: 'ROUND(Basic * 0.4, 2)'                                       },
  { label: 'Transport Allowance (10%)',  formula: 'ROUND(Basic * 0.1, 2)'                                       },
  { label: 'OT Pay (1.5x)',             formula: 'ROUND(OTHours * (Basic / 160) * 1.5, 2)'                     },
  { label: 'Late Deduction',            formula: 'ROUND(LateMinutes * (Basic / (WorkDays * 480)), 2)'          },
  { label: 'Absence Deduction',         formula: 'ROUND(Basic / WorkDays * AbsentDays, 2)'                     },
  { label: 'Warehouse Allowance',            formula: 'ROUND(ZoneHours * 300 + NightHours * 200 + HazardDays * 1500, 2)' },
  { label: 'Pension (8% of Gross)',      formula: 'ROUND(Basic * 0.08, 2)'                                      },
  { label: 'Contractor Rate Premium',   formula: 'IF(ContractorFlag, Basic * 0.15, 0)'                         },
];

const DEFAULT_VARS = VARIABLES.reduce((acc, v) => {
  acc[v.name] = v.name === 'Basic' || v.name === 'BasicSalary' ? 50000
    : v.name === 'WorkDays' ? 22 : v.name === 'PresentDays' ? 20
    : v.name === 'OTHours' ? 8 : v.name === 'ZoneHours' ? 30
    : v.name === 'NightHours' ? 15 : v.name === 'HazardDays' ? 5 : 0;
  return acc;
}, {});

const VarPill = ({ name }) => (
  <code style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600, fontFamily: 'monospace', color: '#2563eb', background: '#eff6ff', border: '1px solid #bfdbfe' }}>
    {name}
  </code>
);

const FuncPill = ({ name }) => (
  <code style={{ display: 'inline-block', padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600, fontFamily: 'monospace', color: '#7c3aed', background: '#ede9fe', border: '1px solid #ddd6fe' }}>
    {name}
  </code>
);

const HistoryStatusDot = ({ success }) => (
  <span style={{ display: 'inline-block', padding: '1px 6px', borderRadius: 999, fontSize: 10, fontWeight: 700, color: success ? '#16a34a' : '#dc2626', background: success ? '#f0fdf4' : '#fef2f2', border: `1px solid ${success ? '#bbf7d0' : '#fecaca'}` }}>
    {success ? '✓ OK' : '✗ ERR'}
  </span>
);

const FormulaTab = ({ structures }) => {
  const { message } = App.useApp();
  const [formula, setFormula] = useState('');
  const [selectedStructureId, setSelectedStructureId] = useState(null);
  const [variables, setVariables] = useState({ ...DEFAULT_VARS });
  const [testResult, setTestResult] = useState(null);
  const [testing, setTesting] = useState(false);
  const [history, setHistory] = useState([]);

  const handleTest = async () => {
    if (!formula.trim()) { message.warning('Enter a formula first'); return; }
    const sid = selectedStructureId || (structures[0]?.id);
    if (!sid) { message.warning('Select a salary structure to test against'); return; }
    setTesting(true);
    try {
      const result = await apiCall(`/api/v1/payroll/structures/${sid}/formula/test/`, {
        method: 'POST',
        body: JSON.stringify({ formula, sample_data: variables }),
      });
      setTestResult(result);
      setHistory(prev => [
        { formula, result: result.value, success: result.success, ts: new Date().toLocaleTimeString() },
        ...prev.slice(0, 9),
      ]);
    } catch (e) {
      setTestResult({ success: false, error: e.message, value: null });
    } finally {
      setTesting(false);
    }
  };

  const applySnippet = (snip) => { setFormula(snip.formula); setTestResult(null); };
  const copyFormula = () => navigator.clipboard.writeText(formula).then(() => message.success('Copied!'));

  return (
    <Row gutter={16}>
      {/* Left: editor + variables */}
      <Col xs={24} lg={14}>
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <Text strong style={{ fontSize: 14 }}><FunctionOutlined style={{ marginRight: 6 }} />Formula Editor</Text>
            <Select placeholder="Test against structure" style={{ width: 200 }} allowClear onChange={setSelectedStructureId} value={selectedStructureId}>
              {structures.map(s => <Option key={s.id} value={s.id}>{s.structure_name}</Option>)}
            </Select>
          </div>
          <Form layout="vertical">
            <Form.Item label="Formula" style={{ marginBottom: 8 }}>
              <TextArea
                rows={5}
                value={formula}
                onChange={e => { setFormula(e.target.value); setTestResult(null); }}
                placeholder="e.g.  ROUND(Basic * 0.4, 2)   or   IF(OTHours > 0, OTHours * 500, 0)"
                style={{ fontFamily: 'monospace', fontSize: 14 }}
              />
            </Form.Item>
            <Space>
              <Button type="primary" icon={<PlayCircleOutlined />} onClick={handleTest} loading={testing}>Test Formula</Button>
              <Button icon={<CopyOutlined />} onClick={copyFormula} disabled={!formula}>Copy</Button>
              <Button icon={<ClearOutlined />} onClick={() => { setFormula(''); setTestResult(null); }}>Clear</Button>
            </Space>
          </Form>

          {testing && <div style={{ textAlign: 'center', padding: 16 }}><Spin tip="Evaluating…" /></div>}
          {testResult && !testing && (
            <div style={{ marginTop: 16 }}>
              <Divider style={{ margin: '12px 0' }} />
              {testResult.success ? (
                <Alert
                  type="success"
                  showIcon
                  icon={<CheckCircleOutlined />}
                  message={
                    <span>
                      Result: <Text strong style={{ fontSize: 18 }}>₦{Number(testResult.value || 0).toLocaleString('en-NG', { minimumFractionDigits: 2 })}</Text>
                    </span>
                  }
                  description={
                    testResult.warnings?.length > 0 ? (
                      <div style={{ marginTop: 4 }}>
                        {testResult.warnings.map((w, i) => (
                          <span key={i} style={{ display: 'inline-flex', alignItems: 'center', gap: 4, padding: '2px 8px', borderRadius: 999, fontSize: 11, fontWeight: 600, color: '#d97706', background: '#fffbeb', border: '1px solid #fde68a', marginRight: 4 }}>
                            <WarningOutlined /> {w}
                          </span>
                        ))}
                      </div>
                    ) : testResult.trace ? (
                      <pre style={{ fontSize: 11, background: '#f6ffed', padding: 8, borderRadius: 4, marginTop: 8 }}>
                        {JSON.stringify(testResult.trace, null, 2)}
                      </pre>
                    ) : null
                  }
                />
              ) : (
                <Alert type="error" showIcon icon={<CloseCircleOutlined />} message="Formula Error" description={testResult.error} />
              )}
            </div>
          )}
        </div>

        {/* Variable Inputs */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
          <Text strong style={{ fontSize: 14 }}>Sample Variable Values</Text>
          <Alert type="info" message="Adjust these sample values to test your formula with different scenarios." showIcon style={{ margin: '10px 0' }} />
          <Row gutter={[8, 8]}>
            {VARIABLES.filter(v => v.name !== 'BasicSalary').map(v => (
              <Col key={v.name} xs={12} sm={8} md={6}>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 2 }}>
                  <Tooltip title={v.desc}><code style={{ fontFamily: 'monospace', color: '#2563eb' }}>{v.name}</code></Tooltip>
                </div>
                <InputNumber
                  size="small"
                  style={{ width: '100%' }}
                  value={variables[v.name]}
                  onChange={val => setVariables(prev => ({ ...prev, [v.name]: val || 0, ...(v.name === 'Basic' && { BasicSalary: val || 0 }) }))}
                  min={0}
                />
              </Col>
            ))}
          </Row>
        </div>
      </Col>

      {/* Right: reference + snippets + history */}
      <Col xs={24} lg={10}>
        {/* Snippets */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 14 }}>Formula Templates</Text>
          <List
            size="small"
            style={{ marginTop: 8 }}
            dataSource={SNIPPETS}
            renderItem={item => (
              <List.Item actions={[<Button size="small" onClick={() => applySnippet(item)}>Use</Button>]}>
                <div>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{item.label}</div>
                  <code style={{ fontSize: 11, color: '#7c3aed', fontFamily: 'monospace' }}>{item.formula}</code>
                </div>
              </List.Item>
            )}
          />
        </div>

        {/* Variable Reference */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 14 }}>Variable Reference</Text>
          <List
            size="small"
            style={{ marginTop: 8 }}
            dataSource={VARIABLES}
            renderItem={v => (
              <List.Item style={{ padding: '4px 0' }}>
                <Space>
                  <VarPill name={v.name} />
                  <Text type="secondary" style={{ fontSize: 12 }}>{v.desc}</Text>
                </Space>
              </List.Item>
            )}
          />
        </div>

        {/* Function Reference */}
        <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)', marginBottom: 12 }}>
          <Text strong style={{ fontSize: 14 }}>Available Functions</Text>
          <List
            size="small"
            style={{ marginTop: 8 }}
            dataSource={FUNCTIONS}
            renderItem={f => (
              <List.Item style={{ padding: '4px 0' }}>
                <Space>
                  <FuncPill name={f.name} />
                  <Text type="secondary" style={{ fontSize: 12 }}>{f.desc}</Text>
                </Space>
              </List.Item>
            )}
          />
        </div>

        {/* History */}
        {history.length > 0 && (
          <div style={{ background: '#fff', borderRadius: 8, padding: 16, boxShadow: '0 1px 4px rgba(0,0,0,0.06)' }}>
            <Text strong style={{ fontSize: 14 }}><HistoryOutlined style={{ marginRight: 6 }} />Recent Tests</Text>
            <List
              size="small"
              style={{ marginTop: 8 }}
              dataSource={history}
              renderItem={h => (
                <List.Item actions={[<Button size="small" onClick={() => setFormula(h.formula)}>Load</Button>]}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <HistoryStatusDot success={h.success} />
                      {h.success && <Text strong style={{ fontSize: 13 }}>₦{Number(h.result || 0).toLocaleString()}</Text>}
                      <Text type="secondary" style={{ fontSize: 11 }}>{h.ts}</Text>
                    </div>
                    <code style={{ fontSize: 11, color: '#94a3b8', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontFamily: 'monospace' }}>
                      {h.formula}
                    </code>
                  </div>
                </List.Item>
              )}
            />
          </div>
        )}
      </Col>
    </Row>
  );
};

export default FormulaTab;
