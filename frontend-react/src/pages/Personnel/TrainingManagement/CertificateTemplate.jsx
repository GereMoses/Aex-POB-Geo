import React, { useRef } from 'react';
import { Button, Space, App } from 'antd';
import { PrinterOutlined, DownloadOutlined } from '@ant-design/icons';
import dayjs from 'dayjs';

/* ────────────────────────────────────────────────────────────
   ApexLogo — uses the product logo from /logo/apex-mark.png
──────────────────────────────────────────────────────────── */
const ApexLogo = ({ size = 80 }) => (
  <img
    src={`${process.env.PUBLIC_URL || ''}/logo/apex-mark.png`}
    alt="Apex POB"
    style={{ width: size, height: size, objectFit: 'contain' }}
    crossOrigin="anonymous"
  />
);

/* ────────────────────────────────────────────────────────────
   Certificate print styles injected once
──────────────────────────────────────────────────────────── */
const PRINT_STYLE_ID = 'cert-print-style';
function ensurePrintStyle() {
  if (document.getElementById(PRINT_STYLE_ID)) return;
  const s = document.createElement('style');
  s.id = PRINT_STYLE_ID;
  s.textContent = `
    @media print {
      body > * { display: none !important; }
      #cert-print-root { display: block !important; position: fixed; top:0;left:0;width:100%;height:100%;z-index:9999; }
    }
  `;
  document.head.appendChild(s);
}

/* ────────────────────────────────────────────────────────────
   CertificateTemplate
──────────────────────────────────────────────────────────── */
const CertificateTemplate = ({ enrollment }) => {
  const { message } = App.useApp();
  const certRef = useRef(null);

  if (!enrollment) return null;

  const {
    personnel_name,
    personnel_emp_code,
    personnel_type,
    personnel_company,
    course_name,
    course_code,
    course_category,
    completion_date,
    expiry_date,
    score,
    certificate_url,
    valid_period_months,
    id,
  } = enrollment;

  const certNo = certificate_url && !certificate_url.startsWith('http')
    ? certificate_url
    : `CERT-${(course_code || 'TRN').replace(/[^A-Z0-9]/g, '')}-${String(id).padStart(5, '0')}`;

  const completedFormatted = completion_date ? dayjs(completion_date).format('DD MMMM YYYY') : '—';
  const expiryFormatted    = expiry_date     ? dayjs(expiry_date).format('DD MMMM YYYY')     : 'Does Not Expire';
  const issuedFormatted    = dayjs().format('DD MMMM YYYY');

  /* ── print handler ── */
  const handlePrint = () => {
    ensurePrintStyle();
    const el = certRef.current;
    if (!el) return;
    // Wrap in a printable root
    const wrapper = document.createElement('div');
    wrapper.id = 'cert-print-root';
    wrapper.style.cssText = 'display:none;background:white;';
    wrapper.innerHTML = el.outerHTML;
    document.body.appendChild(wrapper);
    window.print();
    document.body.removeChild(wrapper);
  };

  /* ── PDF download via jsPDF + html2canvas ── */
  const handleDownload = async () => {
    try {
      const { default: jsPDF } = await import('jspdf');
      const { default: html2canvas } = await import('html2canvas');
      const canvas = await html2canvas(certRef.current, { scale: 2, useCORS: true, backgroundColor: '#ffffff' });
      const imgData = canvas.toDataURL('image/png');
      const pdf = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' });
      const pdfWidth  = pdf.internal.pageSize.getWidth();
      const pdfHeight = pdf.internal.pageSize.getHeight();
      pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
      pdf.save(`Certificate_${certNo}.pdf`);
    } catch {
      // Fallback to print-to-PDF
      message.info('Use Print → Save as PDF for best results');
      handlePrint();
    }
  };

  return (
    <div>
      {/* Action buttons */}
      <Space style={{ marginBottom: 16 }}>
        <Button type="primary" icon={<PrinterOutlined />} onClick={handlePrint}>Print Certificate</Button>
        <Button icon={<DownloadOutlined />} onClick={handleDownload}>Download PDF</Button>
      </Space>

      {/* ── Certificate body ── */}
      <div ref={certRef} style={styles.page}>
        {/* Outer decorative border */}
        <div style={styles.outerBorder}>
          <div style={styles.innerBorder}>

            {/* Corner ornaments */}
            <CornerOrnament pos="topLeft" />
            <CornerOrnament pos="topRight" />
            <CornerOrnament pos="bottomLeft" />
            <CornerOrnament pos="bottomRight" />

            {/* Header */}
            <div style={styles.header}>
              <div style={styles.logoArea}>
                <ApexLogo size={72} />
              </div>
              <div style={styles.headerText}>
                <div style={styles.companyName}>APEX POB</div>
                <div style={styles.companyTagline}>Offshore Personnel On Board Management System</div>
                <div style={styles.dividerLine} />
                <div style={styles.certTitle}>Certificate of Training Completion</div>
              </div>
              <div style={styles.logoArea}>
                {/* Right side: category badge */}
                <div style={{ ...styles.categoryBadge, background: CATEGORY_BADGE_BG[course_category] || '#1a3a5c' }}>
                  <div style={styles.categoryLabel}>{(course_category || 'training').replace(/_/g,' ').toUpperCase()}</div>
                </div>
              </div>
            </div>

            {/* Body */}
            <div style={styles.body}>
              <div style={styles.presentedTo}>THIS IS TO CERTIFY THAT</div>

              <div style={styles.recipientName}>{personnel_name || '—'}</div>

              <div style={styles.recipientMeta}>
                <span style={styles.pill}>{personnel_type || 'STAFF'}</span>
                {personnel_emp_code && <span style={styles.pill}>ID: {personnel_emp_code}</span>}
                {personnel_company && <span style={styles.pill}>{personnel_company}</span>}
              </div>

              <div style={styles.hasCompleted}>
                has successfully completed the required training in
              </div>

              <div style={styles.courseName}>{course_name}</div>
              <div style={styles.courseCode}>[{course_code}]</div>

              {score != null && (
                <div style={styles.scoreRow}>
                  <div style={styles.scoreBox}>
                    <div style={styles.scoreLabel}>Achievement Score</div>
                    <div style={styles.scoreValue}>{Number(score).toFixed(0)}%</div>
                    <div style={styles.scoreGrade}>{Number(score) >= 70 ? 'PASS' : 'MARGINAL PASS'}</div>
                  </div>
                </div>
              )}
            </div>

            {/* Date strip */}
            <div style={styles.dateStrip}>
              <DateBlock label="Completion Date" value={completedFormatted} />
              <div style={styles.dateDivider} />
              <DateBlock label="Issue Date" value={issuedFormatted} />
              <div style={styles.dateDivider} />
              <DateBlock
                label={valid_period_months ? `Expiry Date (${valid_period_months} months)` : 'Validity'}
                value={expiryFormatted}
                highlight={!!valid_period_months}
              />
            </div>

            {/* Footer */}
            <div style={styles.footer}>
              <SignatureBlock label="Training Manager" line="Authorised Signatory" />
              <div style={styles.certNoBlock}>
                <div style={styles.certNoLabel}>Certificate Number</div>
                <div style={styles.certNoValue}>{certNo}</div>
                <div style={styles.certNoLabel} />
                {certificate_url && certificate_url.startsWith('http') && (
                  <div style={styles.verifyUrl}>Verify: {certificate_url}</div>
                )}
              </div>
              <SignatureBlock label="HSE Manager" line="Authorised Signatory" />
            </div>

            {/* Bottom strip */}
            <div style={styles.bottomStrip}>
              <span>Apex POB</span>
              <span style={{ margin: '0 12px' }}>•</span>
              <span>Oil &amp; Gas Personnel Training Record</span>
              <span style={{ margin: '0 12px' }}>•</span>
              <span>Issued: {issuedFormatted}</span>
            </div>

          </div>
        </div>
      </div>
    </div>
  );
};

/* ── Small sub-components ─────────────────────────────────── */

const CATEGORY_BADGE_BG = {
  safety: '#b91c1c', technical: '#1d4ed8', compliance: '#b45309',
  leadership: '#6d28d9', induction: '#047857', refresher: '#b45309',
  certification: '#9d174d', soft_skills: '#0e7490',
};

const CornerOrnament = ({ pos }) => {
  const posMap = {
    topLeft:     { top: 10,    left: 10,    borderTop: '3px solid #c9a84c',  borderLeft:  '3px solid #c9a84c' },
    topRight:    { top: 10,    right: 10,   borderTop: '3px solid #c9a84c',  borderRight: '3px solid #c9a84c' },
    bottomLeft:  { bottom: 10, left: 10,    borderBottom: '3px solid #c9a84c', borderLeft:  '3px solid #c9a84c' },
    bottomRight: { bottom: 10, right: 10,   borderBottom: '3px solid #c9a84c', borderRight: '3px solid #c9a84c' },
  };
  return <div style={{ position: 'absolute', width: 28, height: 28, ...posMap[pos] }} />;
};

const DateBlock = ({ label, value, highlight }) => (
  <div style={styles.dateBlock}>
    <div style={styles.dateLabel}>{label}</div>
    <div style={{ ...styles.dateValue, color: highlight ? '#b91c1c' : '#1a3a5c' }}>{value}</div>
  </div>
);

const SignatureBlock = ({ label, line }) => (
  <div style={styles.sigBlock}>
    <div style={styles.sigLine} />
    <div style={styles.sigLabel}>{label}</div>
    <div style={styles.sigSub}>{line}</div>
  </div>
);

/* ── Styles ───────────────────────────────────────────────── */
const styles = {
  page: {
    width: 940,
    minHeight: 620,
    background: '#ffffff',
    fontFamily: "'Georgia', 'Times New Roman', serif",
    userSelect: 'none',
  },
  outerBorder: {
    border: '10px solid #1a3a5c',
    padding: 6,
    background: 'linear-gradient(135deg, #f8f4e8 0%, #ffffff 50%, #f8f4e8 100%)',
    minHeight: 620,
    position: 'relative',
  },
  innerBorder: {
    border: '2px solid #c9a84c',
    minHeight: 600,
    position: 'relative',
    display: 'flex',
    flexDirection: 'column',
    padding: '20px 30px 14px',
    backgroundImage: `
      radial-gradient(ellipse at 50% 50%, rgba(201,168,76,0.04) 0%, transparent 70%),
      repeating-linear-gradient(45deg, transparent, transparent 40px, rgba(201,168,76,0.015) 40px, rgba(201,168,76,0.015) 41px)
    `,
  },

  /* Header */
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 },
  logoArea: { width: 100, display: 'flex', justifyContent: 'center', alignItems: 'center' },
  headerText: { flex: 1, textAlign: 'center' },
  companyName: { fontSize: 32, fontWeight: 'bold', color: '#1a3a5c', letterSpacing: 8, textTransform: 'uppercase' },
  companyTagline: { fontSize: 11, color: '#666', letterSpacing: 2, marginTop: 2 },
  dividerLine: { borderTop: '2px solid #c9a84c', margin: '8px 40px 8px', position: 'relative' },
  certTitle: { fontSize: 18, color: '#8b6914', letterSpacing: 3, textTransform: 'uppercase', fontStyle: 'italic' },
  categoryBadge: { borderRadius: 6, padding: '8px 12px', textAlign: 'center', minWidth: 80 },
  categoryLabel: { fontSize: 9, color: 'white', letterSpacing: 1, fontWeight: 'bold', fontFamily: 'sans-serif', textTransform: 'uppercase' },

  /* Body */
  body: { flex: 1, textAlign: 'center', paddingTop: 6 },
  presentedTo: { fontSize: 11, letterSpacing: 4, color: '#888', textTransform: 'uppercase', marginBottom: 8 },
  recipientName: { fontSize: 36, color: '#1a3a5c', fontWeight: 'bold', fontStyle: 'italic', letterSpacing: 1, lineHeight: 1.2, marginBottom: 6 },
  recipientMeta: { display: 'flex', justifyContent: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 12 },
  pill: { background: '#f0f4ff', border: '1px solid #c9a84c', borderRadius: 12, padding: '2px 12px', fontSize: 11, color: '#1a3a5c', fontFamily: 'sans-serif' },
  hasCompleted: { fontSize: 13, color: '#555', marginBottom: 10, letterSpacing: 1 },
  courseName: { fontSize: 24, color: '#1a3a5c', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 2, lineHeight: 1.3, marginBottom: 4, padding: '0 40px' },
  courseCode: { fontSize: 12, color: '#c9a84c', letterSpacing: 3, marginBottom: 10 },
  scoreRow: { display: 'flex', justifyContent: 'center', marginTop: 4 },
  scoreBox: { border: '2px solid #c9a84c', borderRadius: 8, padding: '6px 24px', textAlign: 'center', background: 'rgba(201,168,76,0.06)' },
  scoreLabel: { fontSize: 10, color: '#888', letterSpacing: 2, textTransform: 'uppercase', fontFamily: 'sans-serif' },
  scoreValue: { fontSize: 28, fontWeight: 'bold', color: '#1a3a5c' },
  scoreGrade: { fontSize: 11, color: '#047857', letterSpacing: 2, fontFamily: 'sans-serif', fontWeight: 'bold' },

  /* Date strip */
  dateStrip: { display: 'flex', justifyContent: 'center', alignItems: 'stretch', borderTop: '1px solid #c9a84c', borderBottom: '1px solid #c9a84c', margin: '10px 0', padding: '10px 0' },
  dateDivider: { width: 1, background: '#c9a84c', margin: '0 24px' },
  dateBlock: { textAlign: 'center', flex: 1, maxWidth: 220 },
  dateLabel: { fontSize: 10, color: '#888', letterSpacing: 2, textTransform: 'uppercase', fontFamily: 'sans-serif', marginBottom: 4 },
  dateValue: { fontSize: 14, fontWeight: 'bold' },

  /* Footer */
  footer: { display: 'flex', justifyContent: 'space-between', alignItems: 'flex-end', marginTop: 8 },
  sigBlock: { textAlign: 'center', width: 180 },
  sigLine: { borderTop: '1px solid #1a3a5c', marginBottom: 4 },
  sigLabel: { fontSize: 11, color: '#1a3a5c', fontWeight: 'bold', fontFamily: 'sans-serif' },
  sigSub: { fontSize: 10, color: '#888', fontFamily: 'sans-serif' },
  certNoBlock: { textAlign: 'center' },
  certNoLabel: { fontSize: 9, color: '#888', letterSpacing: 2, textTransform: 'uppercase', fontFamily: 'sans-serif' },
  certNoValue: { fontSize: 13, color: '#1a3a5c', fontWeight: 'bold', fontFamily: 'monospace', letterSpacing: 2 },
  verifyUrl: { fontSize: 8, color: '#888', fontFamily: 'sans-serif', marginTop: 2, wordBreak: 'break-all', maxWidth: 200 },

  /* Bottom strip */
  bottomStrip: { background: '#1a3a5c', color: 'white', textAlign: 'center', padding: '5px 0', fontSize: 9, letterSpacing: 2, textTransform: 'uppercase', fontFamily: 'sans-serif', margin: '10px -30px -14px', borderTop: '2px solid #c9a84c' },
};

export default CertificateTemplate;
