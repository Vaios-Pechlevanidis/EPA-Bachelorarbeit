/**
 * WorkPulse · Analytics Report PDF Export — v3 (vollständige Dashboard-Elemente)
 *
 * Seiten im Dashboard-Stil (A4 Portrait, helles Theme), in der Reihenfolge der Seite:
 *   01 Cover                       — Brand-Bar, Hero (Firmenname + Datum), Meta-Band, Inhalt
 *   02 Datenstand + Kennzahlen     — Datenstand-Karte (FA-37) und die fünf Kacheln mit n,
 *                                    Warnung bei kleiner Basis und Datenbasis (FA-25, FA-26)
 *   03 Timeline + Topics im Detail — zwei Diagramm-Karten mit Legende und Kennzahlen
 *   04 Anomalien im Verlauf        — Diagramm-Karte, Eignung, markierte Veränderungen und Einzelmonate
 *   05 Topic-Übersicht             — Stats-Strip, Sentiment-Tabs, Tabelle aller Topics (mehrseitig)
 *
 * Chart-Extraktion: SVG → PNG (html2canvas als Rückfall), Diagramme aus dem DOM des Dashboards.
 * Texte und Schwellen kommen aus denselben Bibliotheken wie das Dashboard
 * (lib/dataStatusText.js, lib/rollingAverage.js, lib/dataBasis.js, lib/scoreText.js).
 *
 * Hauptexport: exportKPIsAsPDF(kpiData); Firmenvergleich: exportCompareAsPDF(compareData)
 */

import jsPDF from 'jspdf';
import html2canvas from 'html2canvas';
import { BASIS, MIN_REVIEWS_PER_WINDOW } from '../lib/dataBasis';
import { fmtRollingMonth, rollingPhrase, rollingReady, rollingWarnings } from '../lib/rollingAverage';
import { evidenceText, fmtN, lastImportText, marketText, platformText, sourceLine, thresholdsNote, timestampCell } from '../lib/dataStatusText';
import { fmtPeriod } from '../lib/anomalySeries';
import { CATEGORY_MEAN_NOTE, CATEGORY_MEAN_TITLE, CRITICAL_LABEL, CRITICAL_NOTE, SCORE_HINT, scoreCountText, scoreTrendWindowsText } from '../lib/scoreText';
// ═══════════════════════════════════════════════════════════════════════════
// COLORS — gleiche Tokens wie das Frontend (colors_and_type.css)
// ═══════════════════════════════════════════════════════════════════════════
const C = {
    // Slate (Neutralskala)
    s0:   [255, 255, 255],
    s50:  [248, 250, 252],
    s100: [241, 245, 249],
    s150: [233, 238, 244],
    s200: [226, 232, 240],
    s300: [203, 213, 225],
    s400: [148, 163, 184],
    s500: [100, 116, 139],
    s600: [71, 85, 105],
    s700: [51, 65, 85],
    s800: [30, 41, 59],
    s900: [15, 23, 42],

    // Navy (Brand)
    navy: [11, 31, 54],

    // Sentiment / Tone
    emerald50:  [236, 253, 245],
    emerald300: [110, 231, 183],
    emerald500: [16, 185, 129],
    emerald600: [5, 150, 105],
    emerald700: [4, 120, 87],
    rose50:     [255, 241, 242],
    rose300:    [253, 164, 175],
    rose500:    [244, 63, 94],
    rose600:    [225, 29, 72],
    rose700:    [190, 18, 60],
    amber50:    [255, 251, 235],
    amber300:   [253, 230, 138],
    amber500:   [245, 158, 11],
    amber600:   [217, 119, 6],
    amber700:   [180, 83, 9],
    blue50:     [239, 246, 255],
    blue200:    [191, 219, 254],
    blue500:    [59, 130, 246],
    blue600:    [37, 99, 235],
    blue700:    [29, 78, 216],
    orange500:  [249, 115, 22],
    orange600:  [234, 88, 12],
};

// Tonale Paletten — KPI-Karten & Stats-Zellen
const TONE = {
    good:    { bg: C.emerald50, border: C.emerald300, accent: C.emerald500, text: C.emerald700, value: C.emerald600 },
    bad:     { bg: C.rose50,    border: C.rose300,    accent: C.rose500,    text: C.rose700,    value: C.rose600    },
    warn:    { bg: C.amber50,   border: C.amber300,   accent: C.amber500,   text: C.amber700,   value: C.amber600   },
    info:    { bg: C.blue50,    border: C.blue200,    accent: C.blue500,    text: C.blue700,    value: C.blue600    },
    neutral: { bg: C.s0,        border: C.s200,       accent: C.s300,       text: C.s600,       value: C.s900       },
};

const scoreTone = (s) => {
    const n = Number(s);
    if (!Number.isFinite(n)) return 'neutral';
    if (n >= 3.5) return 'good';
    if (n >= 2.5) return 'warn';
    return 'bad';
};

// ═══════════════════════════════════════════════════════════════════════════
// LAYOUT — A4 (mm)
// ═══════════════════════════════════════════════════════════════════════════
const PAGE = {
    w: 210,
    h: 297,
    mx: 16,    // horizontaler Rand
    my: 18,    // vertikaler Rand
    get cw() { return this.w - 2 * this.mx; },
    get cl() { return this.mx; },
    get cr() { return this.w - this.mx; },
};

// ═══════════════════════════════════════════════════════════════════════════
// CHART-EXTRAKTION
// ═══════════════════════════════════════════════════════════════════════════

const sanitizeOklch = (el) => {
    if (!el) return;
    try {
        const cs = getComputedStyle(el);
        ['color', 'backgroundColor', 'borderColor', 'fill', 'stroke'].forEach((p) => {
            const v = cs.getPropertyValue(p);
            if (v && v.includes('oklch')) el.style.setProperty(p, 'transparent', 'important');
        });
        if (el.style?.cssText?.includes('oklch')) {
            el.style.cssText = el.style.cssText.replace(/oklch\([^)]*\)/gi, 'transparent');
        }
    } catch { /* skip */ }
    [...(el.children || [])].forEach(sanitizeOklch);
};

const extractChartViaHtml2Canvas = async (el, targetW = 2400) => {
    if (!el) return null;
    const w = el.offsetWidth || el.scrollWidth || 600;
    const h = el.offsetHeight || el.scrollHeight || 300;
    const canvas = await html2canvas(el, {
        scale: Math.max(3, targetW / w),
        backgroundColor: '#ffffff',
        logging: false,
        useCORS: true,
        allowTaint: true,
        foreignObjectRendering: false,
        imageTimeout: 20000,
        width: w, height: h,
        windowWidth: el.scrollWidth, windowHeight: el.scrollHeight,
        scrollX: 0, scrollY: 0,
        onclone: (clonedDoc) => {
            const cl = el.id ? clonedDoc.getElementById(el.id) : clonedDoc.body;
            if (cl) {
                cl.style.visibility = 'visible';
                cl.style.opacity = '1';
                cl.style.overflow = 'visible';
                sanitizeOklch(cl);
            }
            [...clonedDoc.getElementsByTagName('style')].forEach((s) => {
                if (s.textContent?.includes('oklch')) {
                    s.textContent = s.textContent.replace(/oklch\([^)]*\)/gi, 'transparent');
                }
            });
        },
    });
    return { dataUrl: canvas.toDataURL('image/png', 1.0), w, h };
};

const svgToPng = (svg, targetW = 1200) =>
    new Promise((resolve, reject) => {
        try {
            if (!svg) return reject(new Error('no svg'));
            const clone = svg.cloneNode(true);
            const bbox = svg.getBoundingClientRect();
            const sw = bbox.width || 600, sh = bbox.height || 300;
            clone.setAttribute('width', sw);
            clone.setAttribute('height', sh);
            clone.setAttribute('viewBox', `0 0 ${sw} ${sh}`);
            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
            const STYLE_PROPS = [
                'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-linecap',
                'stroke-linejoin', 'opacity', 'fill-opacity', 'stroke-opacity',
                'font-size', 'font-family', 'font-weight', 'text-anchor',
                'dominant-baseline', 'letter-spacing', 'visibility', 'display',
            ];
            const apply = (a, b) => {
                try {
                    const cs = getComputedStyle(a);
                    STYLE_PROPS.forEach((p) => {
                        const v = cs.getPropertyValue(p);
                        if (v && v !== 'none' && !v.includes('oklch')) b.style.setProperty(p, v);
                    });
                } catch { /* skip */ }
                [...(a.children || [])].forEach((c, i) => b.children[i] && apply(c, b.children[i]));
            };
            apply(svg, clone);
            clone.querySelectorAll('.recharts-tooltip-wrapper, .recharts-active-dot').forEach(el => el.remove());
            let str = new XMLSerializer().serializeToString(clone);
            str = str.replace(/oklch\([^)]*\)/gi, '#64748b');
            const url = URL.createObjectURL(new Blob([str], { type: 'image/svg+xml;charset=utf-8' }));
            const img = new Image();
            img.onload = () => {
                const cv = document.createElement('canvas');
                const s = targetW / sw;
                cv.width = Math.round(sw * s); cv.height = Math.round(sh * s);
                const ctx = cv.getContext('2d');
                ctx.imageSmoothingEnabled = true;
                ctx.imageSmoothingQuality = 'high';
                ctx.fillStyle = '#ffffff'; ctx.fillRect(0, 0, cv.width, cv.height);
                ctx.drawImage(img, 0, 0, cv.width, cv.height);
                URL.revokeObjectURL(url);
                resolve({ dataUrl: cv.toDataURL('image/png', 1.0), w: sw, h: sh });
            };
            img.onerror = () => { URL.revokeObjectURL(url); reject(new Error('img err')); };
            img.src = url;
        } catch (e) { reject(e); }
    });

const extractChart = async (container, targetW = 2400) => {
    if (!container) return null;
    try {
        const r = await extractChartViaHtml2Canvas(container, targetW);
        if (r?.dataUrl?.length > 1000) return r;
    } catch (e) { console.warn('html2canvas fail:', e.message); }
    try {
        const svg = container.querySelector('svg.recharts-surface') || container.querySelector('svg');
        return svg ? await svgToPng(svg, targetW) : null;
    } catch (e) { console.warn('svg fallback fail:', e.message); }
    return null;
};

// Topic-Schlüssel (snake_case) als Anzeigename; Großschreibung nur am Wortanfang,
// Umlaute bleiben unverändert (kein \b, das vor "ä" greifen würde).
const prettifyTopic = (key) => {
    if (!key) return '';
    return String(key).replace(/_/g, ' ').replace(/(^|\s)(\p{L})/gu, (m, s, c) => s + c.toUpperCase());
};

const extractChartSvgFirst = async (container, targetW = 3000) => {
    if (!container) return null;
    try {
        const svg = container.querySelector('svg.recharts-surface') || container.querySelector('svg');
        if (svg) {
            const r = await svgToPng(svg, targetW);
            if (r?.dataUrl?.length > 1000) return r;
        }
    } catch (e) { console.warn('svg extract fail:', e.message); }
    try {
        const r = await extractChartViaHtml2Canvas(container, targetW);
        if (r?.dataUrl?.length > 1000) return r;
    } catch (e) { console.warn('html2canvas fallback fail:', e.message); }
    return null;
};

// ═══════════════════════════════════════════════════════════════════════════
// PDF-PRIMITIVES
// ═══════════════════════════════════════════════════════════════════════════

// Truncate text to fit width with ellipsis
const fitText = (doc, text, maxW) => {
    if (doc.getTextWidth(text) <= maxW) return text;
    let t = text;
    while (t.length > 1 && doc.getTextWidth(t + '…') > maxW) t = t.slice(0, -1);
    return t + '…';
};

// WorkPulse logo (speech bubble + pulse line). Width in mm. Height ≈ 0.78×w.
const drawLogo = (doc, x, y, w, bubble = C.navy, pulse = C.s0) => {
    const s = w / 44;
    doc.setFillColor(...bubble);
    doc.roundedRect(x, y, 44 * s, 32 * s, 8 * s, 8 * s, 'F');
    doc.triangle(x + 10 * s, y + 30 * s, x + 5 * s, y + 43 * s, x + 17 * s, y + 30 * s, 'F');
    doc.setDrawColor(...pulse);
    doc.setLineWidth(2.5 * s);
    doc.setLineCap('round'); doc.setLineJoin('round');
    const pts = [[5, 16], [11, 16], [15, 7], [19, 24], [23, 12], [27, 16], [39, 16]];
    for (let i = 0; i < pts.length - 1; i++) {
        doc.line(x + pts[i][0] * s, y + pts[i][1] * s, x + pts[i + 1][0] * s, y + pts[i + 1][1] * s);
    }
    doc.setFillColor(...pulse);
    doc.circle(x + 39 * s, y + 16 * s, 2.5 * s, 'F');
    doc.setLineCap('butt'); doc.setLineJoin('miter');
};

// Brand-Bar (Top der Cover-Seite)
const drawCoverBrandBar = (doc, y, reportLabel = 'Analytics Report') => {
    drawLogo(doc, PAGE.mx, y - 0.5, 7);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(11);
    doc.setTextColor(...C.s900);
    doc.text('WorkPulse', PAGE.mx + 9, y + 4.2);

    doc.setFont('courier', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s500);
    doc.text(String(reportLabel).toUpperCase(), PAGE.cr, y + 4.2, { align: 'right' });

    doc.setDrawColor(...C.s900);
    doc.setLineWidth(0.4);
    doc.line(PAGE.mx, y + 8, PAGE.cr, y + 8);
};

// Page-Header für Inhaltsseiten (Seite 2+)
const drawPageHeader = (doc, title, dateStr) => {
    drawLogo(doc, PAGE.mx, 14, 5.5);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8.5);
    doc.setTextColor(...C.s700);
    doc.text(fitText(doc, String(title), PAGE.cw - 50), PAGE.mx + 7, 17.2);

    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s400);
    doc.text(String(dateStr), PAGE.cr, 17.2, { align: 'right' });

    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, 21, PAGE.cr, 21);
};

// Footer auf allen Seiten
const drawPageFooter = (doc, leftLabel, centerLabel, rightLabel) => {
    const y = PAGE.h - 11;
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, y - 4, PAGE.cr, y - 4);

    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s500);
    doc.text(String(leftLabel), PAGE.mx, y);
    doc.text(String(rightLabel), PAGE.cr, y, { align: 'right' });

    doc.setFont('courier', 'bold');
    doc.text(String(centerLabel), PAGE.w / 2, y, { align: 'center' });
};

// Section-Titel (Eyebrow-Num + h1 + Tag rechts)
const drawSectionTitle = (doc, y, num, title, tag) => {
    doc.setFont('courier', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...C.s400);
    doc.text(String(num).padStart(2, '0'), PAGE.mx, y);

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(13);
    doc.setTextColor(...C.s900);
    doc.text(title, PAGE.mx + 7, y);

    if (tag) {
        doc.setFont('courier', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s500);
        doc.text(String(tag).toUpperCase(), PAGE.cr, y, { align: 'right' });
    }

    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.2);
    doc.line(PAGE.mx, y + 2.5, PAGE.cr, y + 2.5);

    return y + 8;
};

// ═══════════════════════════════════════════════════════════════════════════
// TEXT-HILFEN (nur Zeichen der Standardschriften: kein Pfeil, kein U+2212)
// ═══════════════════════════════════════════════════════════════════════════

// Zahl mit Komma: 3.77 → "3,77"
const fmtNum = (v, digits = 2) =>
    (v == null || !Number.isFinite(Number(v))) ? '–' : Number(v).toFixed(digits).replace('.', ',');

// Mit Vorzeichen: "+0,10", "-0,10", "±0,00"
const fmtSigned = (v, digits = 2) =>
    (v == null || !Number.isFinite(Number(v))) ? '–' : `${v > 0 ? '+' : v < 0 ? '-' : '±'}${fmtNum(Math.abs(v), digits)}`;

const fmtInt = (n) => (n == null ? '–' : fmtN(n));

// Zeitraum zweier Monate "YYYY-MM"
const fmtSpan = (from, to) => (from && to && from !== to ? `${fmtPeriod(from)} – ${fmtPeriod(to)}` : fmtPeriod(from ?? to));

const SOURCE_NAME = { employee: 'Mitarbeiter', candidates: 'Bewerber' };
const sourceName = (key) => SOURCE_NAME[key] || 'Alle Quellen';

// Globaler Zeitfilter des Dashboards (Topbar)
const TIME_RANGE_LABEL = {
    all:  { value: 'Standard', sub: 'gesamter Zeitraum' },
    '1y': { value: '1 Jahr',   sub: 'Kennzahlen, Timeline, Topics' },
    '3y': { value: '3 Jahre',  sub: 'Kennzahlen, Timeline, Topics' },
};

// Mehrzeiliger Text in der aktuellen Schrift; gibt die nächste freie Grundlinie zurück.
const drawWrapped = (doc, text, x, y, maxW, { lineH = 3.3, maxLines = Infinity } = {}) => {
    const lines = doc.splitTextToSize(String(text ?? ''), maxW).slice(0, maxLines);
    lines.forEach((line, i) => doc.text(line, x, y + i * lineH));
    return y + lines.length * lineH;
};

// Datenbasis-Kennzeichen (FA-25, lib/dataBasis.js) als Pille; gibt die Breite zurück.
const drawBasisPill = (doc, x, y, basisKey, { align = 'left', small = false } = {}) => {
    const label = BASIS[basisKey]?.label;
    if (!label) return 0;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(small ? 6 : 6.5);
    const w = doc.getTextWidth(label) + 4;
    const h = small ? 3.6 : 4;
    const px = align === 'right' ? x - w : x;
    doc.setFillColor(...C.s50);
    doc.setDrawColor(...C.s300);
    doc.setLineWidth(0.2);
    doc.roundedRect(px, y, w, h, h / 2, h / 2, 'FD');
    doc.setTextColor(...C.s600);
    doc.text(label, px + w / 2, y + h - 1.1, { align: 'center' });
    return w;
};

// Warnung bei kleiner Basis (FA-26) in Amber, eine Zeile; gibt die nächste Grundlinie zurück.
const drawWarningLine = (doc, text, x, y, maxW, lineH = 3.1) => {
    doc.setFillColor(...C.amber500);
    doc.triangle(x, y, x + 2.2, y, x + 1.1, y - 2, 'F');
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(6.5);
    doc.setTextColor(...C.amber700);
    doc.text(fitText(doc, String(text), maxW - 3.2), x + 3.2, y);
    return y + lineH;
};

// Text der Warnung wie SmallBasisWarning im Dashboard; null, wenn keine Warnung nötig ist.
const smallBasisText = (n, min, unit = 'Bewertungen', context = '') =>
    (n == null || min == null || n >= min) ? null : `kleine Basis (${fmtInt(n)} ${unit}${context ? ` ${context}` : ''}, unter ${min})`;

// ═══════════════════════════════════════════════════════════════════════════
// COVER-SEITE
// ═══════════════════════════════════════════════════════════════════════════

// Brand-Bar, Hero und Meta-Band. Inhaltsverzeichnis und Fußzeile folgen am Ende
// des Exports (drawCoverToc), wenn die Seitenzahlen der Abschnitte feststehen.
// Gibt die Unterkante des Meta-Bands zurück.
const drawCoverPage = (doc, opts) => {
    const {
        companyName = 'Unbekannte Firma',
        subtitle = 'Übersicht aller Bewertungen, Topics und Trends.',
        dateStr,
        timeStr,
        meta = [],          // bis zu 5 Zellen [{label, value, sub}]
    } = opts;

    // Brand-Bar (oben)
    drawCoverBrandBar(doc, PAGE.my);

    const heroCenterY = 128;

    // === Hero ===
    doc.setFont('courier', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...C.s500);
    doc.text('FIRMENANALYSE · BEWERTUNGEN, TOPICS & TRENDS', PAGE.w / 2, heroCenterY - 30, { align: 'center' });

    // Firmenname (groß, fett, verkleinert falls zu lang)
    doc.setFont('helvetica', 'bold');
    let fs = 44;
    doc.setFontSize(fs);
    while (fs > 14 && doc.getTextWidth(companyName) > PAGE.cw - 20) {
        fs -= 2;
        doc.setFontSize(fs);
    }
    doc.setTextColor(...C.s900);
    doc.text(companyName, PAGE.w / 2, heroCenterY - 14, { align: 'center' });

    // Subtitle
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(10);
    doc.setTextColor(...C.s600);
    const subLines = doc.splitTextToSize(subtitle, 130);
    subLines.slice(0, 3).forEach((line, i) => {
        doc.text(line, PAGE.w / 2, heroCenterY - 4 + i * 5, { align: 'center' });
    });

    // Divider (kurzer Strich)
    doc.setDrawColor(...C.s300);
    doc.setLineWidth(0.4);
    doc.line(PAGE.w / 2 - 8, heroCenterY + 8, PAGE.w / 2 + 8, heroCenterY + 8);

    // Datum
    doc.setFont('courier', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(...C.s500);
    doc.text('ERSTELLT AM', PAGE.w / 2, heroCenterY + 14, { align: 'center' });

    doc.setFont('courier', 'normal');
    doc.setFontSize(9);
    doc.setTextColor(...C.s900);
    const datetime = timeStr ? `${dateStr} · ${timeStr}` : dateStr;
    doc.text(datetime, PAGE.w / 2, heroCenterY + 19, { align: 'center' });

    // === Meta-Band (bis zu 5 Zellen, horizontal getrennt) ===
    const cells = meta.slice(0, 5);
    const metaY = heroCenterY + 28;
    const metaH = 25;
    const cellW = PAGE.cw / Math.max(1, cells.length);

    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, metaY, PAGE.cr, metaY);
    doc.line(PAGE.mx, metaY + metaH, PAGE.cr, metaY + metaH);
    for (let i = 1; i < cells.length; i++) {
        doc.line(PAGE.mx + i * cellW, metaY + 3, PAGE.mx + i * cellW, metaY + metaH - 3);
    }

    cells.forEach((m, i) => {
        const cx = PAGE.mx + i * cellW + cellW / 2;

        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(String(m.label).toUpperCase(), cx, metaY + 6.5, { align: 'center' });

        doc.setFont('helvetica', 'bold');
        const valStr = String(m.value);
        let vfs = 16;
        doc.setFontSize(vfs);
        while (vfs > 9 && doc.getTextWidth(valStr) > cellW - 5) { vfs -= 1; doc.setFontSize(vfs); }
        doc.setTextColor(...C.s900);
        doc.text(fitText(doc, valStr, cellW - 4), cx, metaY + 13.5, { align: 'center' });

        if (m.sub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.8);
            doc.setTextColor(...C.s500);
            doc.splitTextToSize(String(m.sub), cellW - 4).slice(0, 2).forEach((line, j) => {
                doc.text(line, cx, metaY + 18.3 + j * 3, { align: 'center' });
            });
        }
    });

    return metaY + metaH;
};

// Inhaltsverzeichnis auf dem Cover (nachträglich auf Seite 1 gezeichnet)
const drawCoverToc = (doc, tocY, toc) => {
    doc.setFont('courier', 'bold');
    doc.setFontSize(7.5);
    doc.setTextColor(...C.s500);
    doc.text('INHALT', PAGE.mx, tocY);

    let curY = tocY + 8;
    toc.forEach((item, i) => {
        doc.setFont('courier', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...C.s400);
        doc.text(String(i + 1).padStart(2, '0'), PAGE.mx, curY);

        doc.setFont('helvetica', 'normal');
        doc.setFontSize(10);
        doc.setTextColor(...C.s800);
        const titleW = doc.getTextWidth(item.title);
        doc.text(item.title, PAGE.mx + 8, curY);

        let metaW = 0;
        if (item.meta) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(8);
            doc.setTextColor(...C.s400);
            const metaText = fitText(doc, '· ' + item.meta, PAGE.cw - 8 - titleW - 24);
            doc.text(metaText, PAGE.mx + 8 + titleW + 2, curY);
            metaW = doc.getTextWidth(metaText) + 2;
        }

        doc.setDrawColor(...C.s300);
        doc.setLineWidth(0.2);
        doc.setLineDashPattern([0.6, 1.6], 0);
        doc.line(PAGE.mx + 8 + titleW + metaW + 3, curY - 1, PAGE.cr - 10, curY - 1);
        doc.setLineDashPattern([], 0);

        doc.setFont('courier', 'bold');
        doc.setFontSize(9);
        doc.setTextColor(...C.s600);
        doc.text(String(item.page).padStart(2, '0'), PAGE.cr, curY, { align: 'right' });

        curY += 7;
    });
};

// ═══════════════════════════════════════════════════════════════════════════
// KPI-KACHEL (tonaler Akzentbalken + tonaler Hintergrund), wie KPIGrid.jsx:
// Bezeichnung, Wert, Badge, Fußnoten mit n, Warnung bei kleiner Basis (FA-26),
// Datenbasis-Kennzeichen (FA-25)
// ═══════════════════════════════════════════════════════════════════════════

const KPI_FOOTER_FS = 6.5;
const KPI_FOOTER_LH = 3.1;

// Fußnotenzeilen einer Kachel bei gegebener Breite (für die Kartenhöhe)
const kpiFooterLines = (doc, card, innerW) => {
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(KPI_FOOTER_FS);
    const src = Array.isArray(card.footer) ? card.footer : card.footer ? [card.footer] : [];
    return src.flatMap((t) => doc.splitTextToSize(String(t), innerW));
};

const kpiCardHeight = (doc, card, w) => {
    const n = kpiFooterLines(doc, card, w - 8).length;
    return 26 + n * KPI_FOOTER_LH + (card.warning ? KPI_FOOTER_LH : 0) + 2.5;
};

const drawKPICard = (doc, x, y, w, h, opts) => {
    const { label, value, badge, tone = 'neutral', basis = null, warning = null } = opts;
    const t = TONE[tone] || TONE.neutral;
    const ix = x + 5;        // innen links (nach dem Akzentbalken + Innenabstand)
    const innerW = w - 8;    // innere Breite

    // Karten-Hintergrund (tonal)
    doc.setFillColor(...t.bg);
    doc.setDrawColor(...t.border);
    doc.setLineWidth(0.3);
    doc.roundedRect(x, y, w, h, 2.5, 2.5, 'FD');

    // Akzentbalken links
    doc.setFillColor(...t.accent);
    doc.rect(x, y, 1.5, h, 'F');

    // Bezeichnung (oben links, fett, tonal); bei langer Bezeichnung kleiner statt gekürzt
    doc.setFont('helvetica', 'bold');
    let lfs = 8;
    doc.setFontSize(lfs);
    while (lfs > 6.5 && doc.getTextWidth(String(label)) > innerW) { lfs -= 0.5; doc.setFontSize(lfs); }
    doc.setTextColor(...t.text);
    doc.text(fitText(doc, String(label), innerW), ix, y + 6);

    // Datenbasis-Kennzeichen rechts in der Badge-Zeile (unter dem Wert)
    if (basis) drawBasisPill(doc, x + w - 3, y + 18.4, basis, { align: 'right', small: true });

    // Wert: Text (Topic-Name) kleiner, Zahl groß
    const valStr = String(value);
    const isLongText = valStr.length > 8 || /[a-zäöüß]/i.test(valStr.replace(/\s/g, ''));
    doc.setFont('helvetica', 'bold');
    if (isLongText) {
        let vfs = 12;
        doc.setFontSize(vfs);
        while (vfs > 7.5 && doc.getTextWidth(valStr) > innerW) { vfs -= 0.5; doc.setFontSize(vfs); }
        doc.setTextColor(...t.value);
        doc.text(fitText(doc, valStr, innerW), ix, y + 15);
    } else {
        let vfs = 20;
        doc.setFontSize(vfs);
        while (vfs > 11 && doc.getTextWidth(valStr) > innerW) { vfs -= 1; doc.setFontSize(vfs); }
        doc.setTextColor(...t.value);
        doc.text(valStr, ix, y + 16);
    }

    // Badge (Pille unter dem Wert); die Zeile bleibt auch ohne Badge frei (Kennzeichen rechts)
    const fy = y + 26;
    if (badge) {
        const badgeY = y + 18.2;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7);
        const bText = fitText(doc, String(badge), innerW - 4);
        const bW = doc.getTextWidth(bText) + 5;
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(...t.accent);
        doc.setLineWidth(0.3);
        doc.roundedRect(ix, badgeY, bW, 4.4, 2.2, 2.2, 'FD');
        doc.setTextColor(...t.text);
        doc.text(bText, ix + bW / 2, badgeY + 3.1, { align: 'center' });
    }

    // Fußnoten (klein, slate-500)
    const lines = kpiFooterLines(doc, opts, innerW);
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(KPI_FOOTER_FS);
    doc.setTextColor(...C.s500);
    lines.forEach((line, i) => doc.text(line, ix, fy + i * KPI_FOOTER_LH));

    // Warnung bei kleiner Basis
    if (warning) drawWarningLine(doc, warning, ix, fy + lines.length * KPI_FOOTER_LH, innerW, KPI_FOOTER_LH);
};

// Kacheln im Raster (3 je Zeile wie die mittlere Breite des Dashboards);
// Zeilenhöhe = höchste Kachel der Zeile. Gibt die Unterkante zurück.
const kpiGridRows = (doc, cards, perRow, cardW) => {
    const rows = [];
    for (let i = 0; i < cards.length; i += perRow) {
        const row = cards.slice(i, i + perRow);
        rows.push({ cards: row, h: Math.max(...row.map((c) => kpiCardHeight(doc, c, cardW))) });
    }
    return rows;
};

const kpiGridHeight = (doc, cards, { perRow = 3, gap = 3 } = {}) => {
    const cardW = (PAGE.cw - (perRow - 1) * gap) / perRow;
    const rows = kpiGridRows(doc, cards, perRow, cardW);
    return rows.reduce((s, r) => s + r.h, 0) + Math.max(0, rows.length - 1) * gap;
};

const drawKPIGrid = (doc, y, cards, { perRow = 3, gap = 3 } = {}) => {
    const cardW = (PAGE.cw - (perRow - 1) * gap) / perRow;
    let curY = y;
    kpiGridRows(doc, cards, perRow, cardW).forEach((row) => {
        row.cards.forEach((c, j) => drawKPICard(doc, PAGE.mx + j * (cardW + gap), curY, cardW, row.h, c));
        curY += row.h + gap;
    });
    return curY - gap;
};

// ═══════════════════════════════════════════════════════════════════════════
// DASHBOARD-CARD (Chart-Container im Dashboard-Stil)
// ═══════════════════════════════════════════════════════════════════════════

const drawCardHeader = (doc, y, opts) => {
    const { eyebrow, title, subtitle, iconTone = 'info', controlsText, basis = null } = opts;
    const t = TONE[iconTone] || TONE.info;
    const x = PAGE.mx;

    // Icon-Quadrat (9×9 mm, tonaler Hintergrund + drei aufsteigende Balken)
    const ix = x + 4, iy = y + 4, is = 9;
    doc.setFillColor(...t.bg);
    doc.roundedRect(ix, iy, is, is, 2, 2, 'F');
    doc.setFillColor(...t.accent);
    const bw = 1.9, bx0 = ix + 1.6, bBase = iy + is - 1.6;
    doc.roundedRect(bx0,                bBase - 2.2, bw, 2.2, 0.5, 0.5, 'F');
    doc.roundedRect(bx0 + bw + 0.8,     bBase - 4.0, bw, 4.0, 0.5, 0.5, 'F');
    doc.roundedRect(bx0 + 2*(bw + 0.8), bBase - 6.0, bw, 6.0, 0.5, 0.5, 'F');

    // Text-Block
    const tx = x + 16;
    let ex = tx;
    if (eyebrow) {
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        const eb = String(eyebrow).toUpperCase();
        doc.text(eb, tx, y + 5);
        ex = tx + doc.getTextWidth(eb) + 2.5;
    }
    // Datenbasis-Kennzeichen hinter dem Eyebrow (wie ChartCardHeader)
    if (basis) drawBasisPill(doc, ex, y + 2.1, basis, { small: true });

    doc.setFont('helvetica', 'bold');
    doc.setFontSize(12);
    doc.setTextColor(...C.s900);
    doc.text(title, tx, y + 10);

    // Filter-Pille rechts (z. B. "Mitarbeiter")
    if (controlsText) {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        const tw = doc.getTextWidth(controlsText) + 7;
        const px = PAGE.cr - tw - 2;
        doc.setFillColor(...C.s50);
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.roundedRect(px, y + 6, tw, 5.5, 2.75, 2.75, 'FD');
        doc.setTextColor(...C.s700);
        doc.text(controlsText, px + tw / 2, y + 9.6, { align: 'center' });
    }

    if (subtitle) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8.5);
        doc.setTextColor(...C.s500);
        doc.text(fitText(doc, String(subtitle), PAGE.cr - tx - 4), tx, y + 14.5);
    }
};

const drawCardChart = (doc, x, y, w, h, imgResult, emptyText = 'Chart nicht verfügbar') => {
    if (!imgResult?.dataUrl) {
        doc.setFillColor(...C.s50);
        doc.roundedRect(x, y, w, h, 1, 1, 'F');
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(8);
        doc.setTextColor(...C.s500);
        doc.text(doc.splitTextToSize(String(emptyText), w - 20), x + w / 2, y + h / 2, { align: 'center' });
        return;
    }
    const aspect = imgResult.w / imgResult.h;
    let iw = w, ih = w / aspect;
    if (ih > h) { ih = h; iw = h * aspect; }
    const ix = x + (w - iw) / 2;
    const iy = y + (h - ih) / 2;
    doc.addImage(imgResult.dataUrl, 'PNG', ix, iy, iw, ih, undefined, 'FAST');
};

// Stats-Footer-Grid (4 Zellen, jede mit optionalem Tone)
const drawStatsFooter = (doc, x, y, w, cells) => {
    const h = 16;
    const cellW = w / cells.length;

    cells.forEach((cell, i) => {
        const cx = x + i * cellW;
        const t = cell.tone ? (TONE[cell.tone] || TONE.neutral) : TONE.neutral;

        // Hintergrund (tonal oder weiß)
        if (cell.tone && cell.tone !== 'neutral') {
            doc.setFillColor(...t.bg);
            doc.rect(cx, y, cellW, h, 'F');
        }

        // Rechte Trennlinie (zwischen Zellen)
        if (i < cells.length - 1) {
            doc.setDrawColor(...C.s100);
            doc.setLineWidth(0.2);
            doc.line(cx + cellW, y + 2, cx + cellW, y + h - 2);
        }

        // Label
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(String(cell.label).toUpperCase(), cx + 4, y + 5);

        // Value
        const valStr = String(cell.value);
        const isText = valStr.length > 6 || /[a-zäöü]/i.test(valStr.replace(/\s/g, ''));
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(isText ? 10 : 14);
        doc.setTextColor(...(cell.tone ? t.value : C.s900));
        doc.text(fitText(doc, valStr, cellW - 6), cx + 4, y + 11);

        // Sub
        if (cell.sub) {
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(7);
            doc.setTextColor(...C.s500);
            doc.text(fitText(doc, String(cell.sub), cellW - 6), cx + 4, y + h - 3);
        }
    });

    // Top-Trennlinie zur Card
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.3);
    doc.line(x, y, x + w, y);

    return y + h;
};

// Legende in Zeilen umbrechen (wie die umbrechenden Zeilen unter den Dashboard-Diagrammen).
// Die Quellenangabe (sourceNote) steht rechtsbündig in der letzten Zeile, wenn Platz ist,
// sonst in einer eigenen Zeile. Gibt {rows, note, noteInLastRow, noteOwnRow, height} zurück.
const LEGEND_FS = 7.5, LEGEND_LH = 4.2, LEGEND_SWATCH = 4, LEGEND_GAP = 6;

const layoutLegend = (doc, legend, width) => {
    const items = legend.filter((i) => !i.sourceNote);
    const note = legend.find((i) => i.sourceNote) || null;
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(LEGEND_FS);
    const rows = [];
    let row = [], used = 0;
    items.forEach((item) => {
        const swatchW = item.shape === 'none' ? 0 : LEGEND_SWATCH + 1.5;
        const w = swatchW + doc.getTextWidth(String(item.label));
        if (row.length && used + w > width) { rows.push(row); row = []; used = 0; }
        row.push({ ...item, w, swatchW });
        used += w + LEGEND_GAP;
    });
    if (row.length) rows.push(row);
    let noteW = 0;
    if (note) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(7);
        noteW = doc.getTextWidth(String(note.label));
    }
    const lastUsed = rows.length ? rows[rows.length - 1].reduce((s, i) => s + i.w + LEGEND_GAP, 0) : 0;
    const noteInLastRow = Boolean(note) && rows.length > 0 && lastUsed + noteW + 4 <= width;
    const noteOwnRow = Boolean(note) && !noteInLastRow;
    const lines = rows.length + (noteOwnRow ? 1 : 0);
    return { rows, note, noteInLastRow, noteOwnRow, height: lines ? 3 + lines * LEGEND_LH : 0 };
};

// Legendensymbol: Balken (Standard), gestrichelte Linie, Ring (Markierung der Karte),
// Raute (auffälliger Einzelmonat); y = Grundlinie des Texts.
const drawLegendSwatch = (doc, item, x, y) => {
    const cy = y - 1;
    if (item.shape === 'ring') {
        doc.setFillColor(...(item.fill || C.s100));
        doc.setDrawColor(...item.color);
        doc.setLineWidth(0.35);
        doc.circle(x + 2, cy, 1.3, 'FD');
    } else if (item.shape === 'diamond') {
        doc.setFillColor(255, 255, 255);
        doc.setDrawColor(...item.color);
        doc.setLineWidth(0.35);
        doc.lines([[1.4, 1.4], [-1.4, 1.4], [-1.4, -1.4], [1.4, -1.4]], x + 2, cy - 1.4, [1, 1], 'FD', true);
    } else if (item.dashed) {
        doc.setDrawColor(...item.color);
        doc.setLineWidth(0.8);
        doc.setLineDashPattern([1, 0.8], 0);
        doc.line(x, cy, x + LEGEND_SWATCH, cy);
        doc.setLineDashPattern([], 0);
    } else {
        doc.setFillColor(...item.color);
        doc.roundedRect(x, cy - 0.6, LEGEND_SWATCH, 1.2, 0.6, 0.6, 'F');
    }
};

// Eine komplette Dashboard-Card rendern. Gibt das untere Y zurück (mit Bildunterschrift).
// opts: { header: {eyebrow, title, subtitle, iconTone, controlsText, basis},
//         chart: imgResult, chartH: mm, emptyText: Text statt fehlendem Diagramm,
//         legend: [{label, color, dashed, shape, fill, sourceNote}], stats: [{label, value, sub, tone}],
//         caption: string }
const drawDashboardCard = (doc, y, opts) => {
    const { header, chart, chartH = 70, legend = [], stats = [], caption, emptyText } = opts;
    const cardX = PAGE.mx;
    const cardW = PAGE.cw;

    const headerH = 18;
    const lg = layoutLegend(doc, legend, cardW - 12);
    const statsH = stats.length ? 16 : 0;
    const cardH = headerH + chartH + lg.height + statsH;

    // Karten-Rahmen
    doc.setFillColor(...C.s0);
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.roundedRect(cardX, y, cardW, cardH, 2.5, 2.5, 'FD');

    // Header
    drawCardHeader(doc, y, header);

    // Header → Chart Trennlinie
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.2);
    doc.line(cardX + 2, y + headerH, cardX + cardW - 2, y + headerH);

    // Chart
    drawCardChart(doc, cardX + 4, y + headerH + 2, cardW - 8, chartH - 4, chart, emptyText);

    let curY = y + headerH + chartH;

    // Legende (umbrechend)
    if (lg.height) {
        const x0 = cardX + 6;
        lg.rows.forEach((row, r) => {
            const ly = curY + 5 + r * LEGEND_LH;
            let lx = x0;
            row.forEach((item) => {
                if (item.swatchW) drawLegendSwatch(doc, item, lx, ly);
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(LEGEND_FS);
                doc.setTextColor(...C.s600);
                doc.text(String(item.label), lx + item.swatchW, ly);
                lx += item.w + LEGEND_GAP;
            });
        });
        if (lg.note) {
            const noteRow = lg.noteInLastRow ? lg.rows.length - 1 : lg.rows.length;
            const ny = curY + 5 + noteRow * LEGEND_LH;
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(7);
            doc.setTextColor(...C.s400);
            doc.text(fitText(doc, String(lg.note.label), cardW - 12), cardX + cardW - 5, ny, { align: 'right' });
        }
        curY += lg.height;
    }

    // Stats
    if (stats.length) {
        drawStatsFooter(doc, cardX, curY, cardW, stats);
    }

    // Bildunterschrift (kursiv, unter der Karte)
    if (caption) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s400);
        doc.text(fitText(doc, String(caption), cardW), PAGE.w / 2, y + cardH + 5, { align: 'center' });
        return y + cardH + 8;
    }

    return y + cardH;
};

// ═══════════════════════════════════════════════════════════════════════════
// TOPIC-TABELLE
// ═══════════════════════════════════════════════════════════════════════════

const drawSortChevrons = (doc, x, y, active = 'none') => {
    // active: 'up' | 'down' | 'none'
    doc.setLineWidth(0.4);
    doc.setLineCap('round'); doc.setLineJoin('round');

    // Up chevron
    doc.setDrawColor(...(active === 'up' ? C.s700 : C.s400));
    doc.lines([[0.8, -0.7], [0.8, 0.7]], x, y - 0.4);

    // Down chevron
    doc.setDrawColor(...(active === 'down' ? C.s700 : C.s400));
    doc.lines([[0.8, 0.7], [0.8, -0.7]], x, y + 1.4);

    doc.setLineCap('butt'); doc.setLineJoin('miter');
};

// Sentiment-Tone Lookup
const sentimentStyle = (sentiment) => {
    const s = String(sentiment || 'Neutral').trim();
    if (s === 'Positiv') return { bg: C.emerald50, text: C.emerald700, dot: C.emerald500 };
    if (s === 'Negativ') return { bg: C.rose50,    text: C.rose700,    dot: C.rose500    };
    if (s === 'Gemischt') return { bg: C.amber50,  text: C.amber700,   dot: C.amber500   };
    return { bg: C.s100, text: C.s600, dot: C.s400 };
};

// Datenqualität-Tone Lookup
const qualityStyle = (risk) => {
    switch (risk) {
        case 'solid':       return { label: 'Solide',       bg: C.emerald50, text: C.emerald700 };
        case 'acceptable':  return { label: 'Akzeptabel',   bg: C.amber50,   text: C.amber700   };
        case 'constrained': return { label: 'Eingeschränkt', bg: C.amber50,  text: C.amber700   };
        case 'limited':     return { label: 'Begrenzt',     bg: C.rose50,    text: C.rose700    };
        default:            return { label: '–',            bg: null,        text: C.s500       };
    }
};

const ratingTone = (r) => {
    const n = Number(r);
    if (!Number.isFinite(n)) return C.s400;
    if (n >= 3.5) return C.emerald500;
    if (n >= 2.5) return C.amber500;
    return C.rose500;
};

// Tabelle: Topic (+ Beispiel) | Erwähnungen | Ø Rating | Sentiment | Datenqualität,
// Spalten wie TopicTableModal. Kopf und Zeilen getrennt, damit die Tabelle über
// mehrere Seiten laufen kann (alle Topics, keine Kürzung).
const TOPIC_ROW_H = 7;        // ohne Beispielzeile
const TOPIC_ROW_H_EX = 10.5;  // mit Beispielzeile
const TOPIC_HEAD_H = 9;
const TOPIC_PAD_L = 4;
const TOPIC_RATIOS = [0.36, 0.12, 0.22, 0.15, 0.15];   // Summe 1,0

const topicColumns = (x, w) => {
    const inner = w - TOPIC_PAD_L * 2;
    const colX = [];
    let acc = TOPIC_PAD_L;
    TOPIC_RATIOS.forEach((r) => { colX.push(x + acc); acc += r * inner; });
    return {
        inner,
        topic:     colX[0],
        topicW:    TOPIC_RATIOS[0] * inner - 4,
        ment:      colX[1] + TOPIC_RATIOS[1] * inner - 8,   // rechtsbündig
        rating:    colX[2],
        sentiment: colX[3],
        quality:   colX[4],
    };
};

// Kopfzeile mit Grundlinie y; gibt die Grundlinie der ersten Zeile zurück.
const drawTopicTableHead = (doc, x, y, w) => {
    const cols = topicColumns(x, w);
    doc.setFillColor(...C.s50);
    doc.rect(x + 0.3, y - 4.5, w - 0.6, TOPIC_ROW_H + 1, 'F');
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(x, y + TOPIC_ROW_H - 3.5, x + w, y + TOPIC_ROW_H - 3.5);

    doc.setFont('courier', 'bold');
    doc.setFontSize(7);
    doc.setTextColor(...C.s600);
    doc.text('TOPIC', cols.topic, y);
    drawSortChevrons(doc, cols.topic + doc.getTextWidth('TOPIC') + 1, y, 'none');
    doc.text('ERWÄHNUNGEN', cols.ment, y, { align: 'right' });
    drawSortChevrons(doc, cols.ment + 1.5, y, 'down');
    doc.text('Ø RATING', cols.rating, y);
    drawSortChevrons(doc, cols.rating + doc.getTextWidth('Ø RATING') + 1, y, 'none');
    doc.text('SENTIMENT', cols.sentiment, y);
    doc.text('DATENQUALITÄT', cols.quality, y);
    return y + TOPIC_HEAD_H;
};

// Eine Zeile mit Grundlinie curY; der Zeilenkasten reicht von curY − 4,5 bis curY − 4,5 + rowH.
const drawTopicRow = (doc, x, curY, w, topic, idx, rowH) => {
    const cols = topicColumns(x, w);
    const top = curY - 4.5;
    const limited = topic.statistical_meta?.risk_level === 'limited';

    if (idx % 2 === 1) {
        doc.setFillColor(...C.s50);
        doc.rect(x + 0.3, top, w - 0.6, rowH, 'F');
    }
    // Linker Balken bei begrenzter Datenbasis (wie TopicTableModal)
    if (limited) {
        doc.setFillColor(...C.rose300);
        doc.rect(x + 0.3, top, 1.2, rowH, 'F');
    }
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.15);
    doc.line(x, top + rowH, x + w, top + rowH);

    // Topic-Name wie in der Tabelle der Web-App (+ n bei begrenzter Basis)
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(8);
    doc.setTextColor(...C.s900);
    let name = String(topic.topic ?? '');
    let tagW = 0;
    const n = topic.statistical_meta?.review_count;
    if (limited && n != null) {
        doc.setFont('courier', 'normal');
        doc.setFontSize(6);
        tagW = doc.getTextWidth(`n=${n}`) + 4;
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
    }
    name = fitText(doc, name, cols.topicW - tagW);
    doc.text(name, cols.topic, curY);
    if (tagW) {
        const tx = cols.topic + doc.getTextWidth(name) + 2;
        doc.setFillColor(...C.rose50);
        doc.setDrawColor(...C.rose300);
        doc.setLineWidth(0.2);
        doc.roundedRect(tx, curY - 2.9, tagW - 1, 3.6, 1, 1, 'FD');
        doc.setFont('courier', 'normal');
        doc.setFontSize(6);
        doc.setTextColor(...C.rose700);
        doc.text(`n=${n}`, tx + (tagW - 1) / 2, curY - 0.3, { align: 'center' });
    }

    // Beispiel (zweite Zeile, kursiv, über die ganze Breite)
    if (rowH >= TOPIC_ROW_H_EX && topic.example) {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(6.5);
        doc.setTextColor(...C.s500);
        doc.text(fitText(doc, String(topic.example).replace(/\s+/g, ' ').trim(), cols.inner - 2), cols.topic, curY + 3.6);
    }

    // Erwähnungen (rechtsbündig)
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(8);
    doc.setTextColor(...C.s700);
    doc.text(fmtInt(topic.frequency || 0), cols.ment, curY, { align: 'right' });

    // Ø Rating: Mini-Balken + Wert
    const rating = Number(topic.avgRating);
    if (Number.isFinite(rating)) {
        const barX = cols.rating, barY = curY - 1.5, barW = 16, barH = 1.4;
        doc.setFillColor(...C.s100);
        doc.roundedRect(barX, barY, barW, barH, 0.7, 0.7, 'F');
        const pct = Math.min(1, Math.max(0, rating / 5));
        doc.setFillColor(...ratingTone(rating));
        doc.roundedRect(barX, barY, barW * pct, barH, 0.7, 0.7, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(...C.s900);
        doc.text(rating.toFixed(1).replace('.', ','), barX + barW + 2.5, curY);
    } else {
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s400);
        doc.text('–', cols.rating, curY);
    }

    // Sentiment-Pille
    const ss = sentimentStyle(topic.sentiment);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    const sLabel = String(topic.sentiment || 'Neutral');
    const sW = doc.getTextWidth(sLabel) + 7;
    doc.setFillColor(...ss.bg);
    doc.roundedRect(cols.sentiment, curY - 3.2, sW, 4.4, 2.2, 2.2, 'F');
    doc.setFillColor(...ss.dot);
    doc.circle(cols.sentiment + 2.4, curY - 0.9, 0.7, 'F');
    doc.setTextColor(...ss.text);
    doc.text(sLabel, cols.sentiment + 4.2, curY - 0.1);

    // Datenqualität-Pille
    const q = qualityStyle(topic.statistical_meta?.risk_level);
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7);
    const qW = doc.getTextWidth(q.label) + 5;
    if (q.bg) {
        doc.setFillColor(...q.bg);
        doc.roundedRect(cols.quality, curY - 3.2, qW, 4.4, 2.2, 2.2, 'F');
    }
    doc.setTextColor(...q.text);
    doc.text(q.label, cols.quality + 2.5, curY - 0.1);
};

// Sentiment-Filter-Tabs (Alle / Positiv / Neutral / Negativ)
const drawSentimentTabs = (doc, x, y, w, counts) => {
    // counts: { total, pos, neu, neg }
    const items = [
        { label: 'Alle',    count: counts.total, dotColor: null,           active: true },
        { label: 'Positiv', count: counts.pos,   dotColor: C.emerald500, active: false },
        { label: 'Neutral', count: counts.neu,   dotColor: C.s400,         active: false },
        { label: 'Negativ', count: counts.neg,   dotColor: C.rose500,    active: false },
    ];

    const h = 10;
    // Background-Strip
    doc.setFillColor(...C.s50);
    doc.rect(x, y, w, h, 'F');
    doc.setDrawColor(...C.s100);
    doc.setLineWidth(0.2);
    doc.line(x, y, x + w, y);
    doc.line(x, y + h, x + w, y + h);

    let cx = x + 6;
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(7.5);

    items.forEach((it) => {
        const labelW = doc.getTextWidth(it.label);
        const cntStr = String(it.count);
        doc.setFont('courier', 'bold');
        const cntW = doc.getTextWidth(cntStr);
        const pillW = (it.dotColor ? 4 : 0) + labelW + 3 + cntW + 8;
        const pillY = y + 1.8;

        if (it.active) {
            doc.setFillColor(...C.s0);
            doc.setDrawColor(...C.s200);
            doc.setLineWidth(0.3);
            doc.roundedRect(cx, pillY, pillW, 6, 3, 3, 'FD');
        }
        let tx = cx + 4;
        if (it.dotColor) {
            doc.setFillColor(...it.dotColor);
            doc.circle(tx, pillY + 3.1, 0.9, 'F');
            tx += 2.5;
        }
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(...(it.active ? C.s900 : C.s600));
        doc.text(it.label, tx, pillY + 4);
        doc.setFont('courier', 'bold');
        doc.setFontSize(7);
        doc.setTextColor(...C.s500);
        doc.text(cntStr, tx + labelW + 2.5, pillY + 4);

        cx += pillW + 2;
    });

    // "sortiert nach Erwähnungen" rechts
    doc.setFont('courier', 'bold');
    doc.setFontSize(6.5);
    doc.setTextColor(...C.s400);
    doc.text('SORTIERT NACH ERWÄHNUNGEN', x + w - 4, y + 6.5, { align: 'right' });

    return y + h;
};

// ═══════════════════════════════════════════════════════════════════════════
// DATENSTAND-KARTE (Inkrement 6, FA-37) — Texte wie DataStatusBar (lib/dataStatusText.js)
// ═══════════════════════════════════════════════════════════════════════════

const drawDataStatusCard = (doc, y, status, { lastImportLocal = null } = {}) => {
    const cardX = PAGE.mx, cardW = PAGE.cw, pad = 4;
    const labelW = 30;
    const textX = cardX + pad + labelW;
    const textW = cardW - pad * 2 - labelW;
    let curY = y + 6;

    const row = (label, text) => {
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s700);
        doc.text(label, cardX + pad, curY);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s600);
        curY = drawWrapped(doc, text, textX, curY, textW, { lineH: 3.3 }) + 1.2;
    };

    if (!status) {
        row('Datenstand', 'konnte nicht geladen werden (GET /companies/{id}/data-status); die Leiste im Dashboard zeigt den Stand nach dem nächsten Abruf.');
    } else {
        row('Mitarbeitende', sourceLine(status.sources?.employee));
        row('Bewerbende', sourceLine(status.sources?.candidates));
        row('Letzter Import', lastImportText(status));
        if (lastImportLocal) {
            const stamp = new Date(lastImportLocal).toLocaleString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
            row('Import über die App', `${stamp} (Verlauf dieses Geräts, wie die Anzeige „Letzter Import“ im Dashboard)`);
        }
        row('Plattform', platformText(status.platform));
        if (status.market_cache !== undefined) row('Kurs', marketText(status.market_cache));
        if (status.evidence_store !== undefined) row('Belege', evidenceText(status.evidence_store));

        doc.setFont('helvetica', 'italic');
        doc.setFontSize(6.8);
        doc.setTextColor(...C.s500);
        curY = drawWrapped(doc, thresholdsNote(status.thresholds), cardX + pad, curY + 0.3, cardW - pad * 2, { lineH: 3.1 }) + 1.5;

        // Zeitstempel je Feld (aufklappbarer Teil der Leiste)
        const fields = Object.entries(status.timestamp_fields ?? {});
        const sources = Object.entries(status.sources ?? {});
        if (fields.length) {
            doc.setDrawColor(...C.s100);
            doc.setLineWidth(0.2);
            doc.line(cardX + pad, curY, cardX + cardW - pad, curY);
            curY += 4.5;
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(7);
            doc.setTextColor(...C.s700);
            doc.text('Zeitstempel je Feld', (cardX + pad), curY);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(...C.s500);
            doc.text('(aufklappbarer Teil der Leiste: ältester und jüngster Wert je Quelle, Anzahl in Klammern)', (cardX + pad) + 26, curY);
            curY += 4;
            const colFieldW = 20, colSrcW = 54;
            const colMeaningW = cardW - pad * 2 - colFieldW - colSrcW * sources.length;
            const xField = cardX + pad, xMeaning = xField + colFieldW, xSrc = (i) => xMeaning + colMeaningW + i * colSrcW;

            doc.setFont('courier', 'bold');
            doc.setFontSize(6);
            doc.setTextColor(...C.s500);
            doc.text('FELD', xField, curY);
            doc.text('BEDEUTUNG', xMeaning, curY);
            sources.forEach(([, s], i) => doc.text(fitText(doc, String(s.label).toUpperCase(), colSrcW - 2), xSrc(i), curY));
            curY += 1.3;
            doc.setDrawColor(...C.s200);
            doc.line(cardX + pad, curY, cardX + cardW - pad, curY);
            curY += 3.6;

            fields.forEach(([field, meaning]) => {
                doc.setFont('helvetica', 'normal');
                doc.setFontSize(6.2);
                const meaningLines = doc.splitTextToSize(String(meaning), colMeaningW - 3);
                doc.setFont('courier', 'normal');
                doc.setFontSize(6.2);
                doc.setTextColor(...C.s700);
                doc.text(field, xField, curY);
                doc.setFont('helvetica', 'normal');
                doc.setTextColor(...C.s600);
                meaningLines.forEach((l, i) => doc.text(l, xMeaning, curY + i * 2.9));
                doc.setTextColor(...C.s700);
                sources.forEach(([, s], i) => doc.text(fitText(doc, timestampCell(s.timestamps?.[field]), colSrcW - 2), xSrc(i), curY));
                curY += Math.max(1, meaningLines.length) * 2.9 + 1.5;
            });
        }
        if (status.note) {
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(6.5);
            doc.setTextColor(...C.s500);
            curY = drawWrapped(doc, status.note, cardX + pad, curY + 0.3, cardW - pad * 2, { lineH: 3 });
        }
    }

    const cardH = curY - y + 1;
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.roundedRect(cardX, y, cardW, cardH, 2.5, 2.5, 'S');
    return y + cardH;
};

// ═══════════════════════════════════════════════════════════════════════════
// KENNZAHLEN — fünf Kacheln wie KPIGrid.jsx (Ø Score, Trend, 12- vs. 24-Monats-Schnitt,
// Kritischste Kategorie, Negativstes Topic), mit n, Warnung bei kleiner Basis und Datenbasis
// ═══════════════════════════════════════════════════════════════════════════

const buildKpiCards = ({ avgScore, avgCount, trend, rolling, mostCritical, negativeTopic, negativeTopicItem }) => {
    const cards = [];

    // Ø Score: Mittel der Gesamtnote, Mitarbeitende, ungewichtet (D1, FA-38)
    const scoreNum = avgScore !== '-' && avgScore != null ? Number(avgScore) : NaN;
    cards.push({
        label: 'Ø Score',
        value: Number.isFinite(scoreNum) ? fmtNum(scoreNum, 1) : '–',
        badge: '/ 5',
        tone: Number.isFinite(scoreNum) ? scoreTone(scoreNum) : 'neutral',
        basis: 'stars',
        footer: [scoreCountText(avgCount)],
        warning: smallBasisText(avgCount, MIN_REVIEWS_PER_WINDOW),
    });

    // Trend der Gesamtnote (Modus score_months, 12 oder 36 volle Monate je Zeitfilter)
    const tv = trend?.avgDelta != null ? parseFloat(trend.avgDelta) : NaN;
    const months = trend?.windowMonths;
    const trendT = trend?.sign === 'up' ? 'good' : trend?.sign === 'down' ? 'bad' : 'neutral';
    const nCur = trend?.nReviews?.current, nPrev = trend?.nReviews?.previous;
    cards.push({
        label: months ? `Trend ${months}M` : 'Trend',
        value: Number.isFinite(tv) ? `${tv > 0 ? '+' : ''}${fmtNum(tv, 2)}` : '–',
        badge: trend?.sign ? (trend.sign === 'up' ? 'steigend' : trend.sign === 'down' ? 'sinkend' : 'stabil') : null,
        tone: trend?.sign ? trendT : 'neutral',
        basis: 'stars',
        footer: [
            months ? `Gesamtnote, ${months} volle Monate vs. ${months} davor` : 'Gesamtnote, Mitarbeitende',
            ...(trend?.raw ? [scoreTrendWindowsText(trend.raw)] : []),
        ],
        warning: trend?.nReviews
            ? smallBasisText(Math.min(nCur ?? Infinity, nPrev ?? Infinity), MIN_REVIEWS_PER_WINDOW, 'Bewertungen', 'in einem Fenster')
            : null,
    });

    // 12- vs. 24-Monats-Schnitt (FA-08): beschreibt nur die Lage, keine Prognose
    const rOk = rollingReady(rolling);
    const rFooter = [];
    if (!rolling) rFooter.push('Sternebewertung, Mitarbeitende');
    else if (!rolling.anchor) rFooter.push('keine datierten Bewertungen mit Gesamtnote');
    else {
        rFooter.push(`12 M: ${fmtRollingMonth(rolling.short.from)} – ${fmtRollingMonth(rolling.short.to)}, n = ${fmtInt(rolling.short.n)} · 24 M: ab ${fmtRollingMonth(rolling.long.from)}, n = ${fmtInt(rolling.long.n)}`);
        rFooter.push(`12-Monats-Schnitt ${rollingPhrase(rolling)}.`);
    }
    const rWarn = rolling?.anchor ? rollingWarnings(rolling) : [];
    cards.push({
        label: '12- vs. 24-Monats-Schnitt',
        value: rOk ? fmtNum(rolling.short.mean, 2) : '–',
        badge: rOk ? `24 M: ${fmtNum(rolling.long.mean, 2)}` : null,
        tone: 'neutral',
        basis: 'stars',
        footer: rFooter,
        warning: rWarn.length ? rWarn.join(' · ') : null,
    });

    // Kritischste Kategorie: niedrigstes Kategorienmittel (kategorienbasiert)
    const mc = mostCritical?.topicName && mostCritical.topicName !== '-' ? mostCritical : null;
    const mcScore = mc ? Number(mc.score) : NaN;
    cards.push({
        label: CRITICAL_LABEL,
        value: mc ? mc.topicName : '–',
        badge: mc ? `${fmtNum(mcScore, 1)} / 5` : null,
        tone: mc ? scoreTone(mcScore) : 'neutral',
        basis: 'stars',
        footer: [
            CRITICAL_NOTE,
            ...(mc?.n != null ? [`n = ${fmtInt(mc.n)} Bewertungen in dieser Kategorie`] : []),
        ],
        warning: mc?.n != null ? smallBasisText(mc.n, MIN_REVIEWS_PER_WINDOW) : null,
    });

    // Negative Topic: höchste Negativrate in den Freitexten
    const hasNeg = Boolean(negativeTopic) && negativeTopic !== '-';
    const mentions = negativeTopicItem?.mention_count;
    cards.push({
        label: 'Negative Topic',
        value: hasNeg ? negativeTopic : '–',
        badge: hasNeg && mentions ? `n = ${fmtInt(mentions)}` : null,
        tone: hasNeg ? 'bad' : 'neutral',
        basis: 'text',
        footer: [
            'höchste Negativrate (Freitexte)',
            ...(mentions != null ? [`n = ${fmtInt(mentions)} Nennungen`] : []),
        ],
        warning: null,
    });

    return cards;
};

// Kennzahlen unter der Timeline je Metrik, wie SummaryStats der Karte
const timelineStats = (tf) => {
    const st = tf?.stats || {};
    const metric = tf?.metric || 'Ø Score';
    const out = [];
    if (st.dataPoints != null) {
        out.push({ label: 'Datenpunkte', value: String(st.dataPoints), sub: tf?.granularity === 'year' ? 'jährlich' : 'aggregiert' });
    }
    if (metric === 'Anzahl') {
        if (st.avgCount != null) out.push({ label: 'Ø Anzahl', value: fmtNum(st.avgCount, 1), sub: 'je Datenpunkt', tone: 'info' });
        if (st.maxCount != null) out.push({ label: 'Max Anzahl', value: String(st.maxCount), sub: 'höchster Datenpunkt', tone: 'info' });
    } else if (metric === 'Trend') {
        if (st.avgTrend != null) {
            const at = parseFloat(st.avgTrend);
            out.push({ label: 'Ø Trend', value: fmtSigned(at, 2), sub: 'Mittel der Änderungen', tone: at >= 0 ? 'good' : 'bad' });
        }
        if (st.maxTrend != null && st.minTrend != null) {
            out.push({ label: 'Max / Min', value: `${fmtSigned(parseFloat(st.maxTrend), 2)} / ${fmtNum(parseFloat(st.minTrend), 2)}`, sub: 'Spanne' });
        }
    } else {
        if (st.avgHistorical != null) out.push({ label: 'Ø Historisch', value: fmtNum(st.avgHistorical, 2), sub: st.dateRange || 'gesamte Historie', tone: 'info' });
        if (st.avgForecast != null) out.push({ label: 'Ø Prognose', value: fmtNum(st.avgForecast, 2), sub: st.forecastRange || 'kommende Monate', tone: 'warn' });
    }
    return out;
};

// Farben der Topic-Linien wie TopicRatingCard (Index in der Liste aller Topics)
const TOPIC_PALETTE = [
    [59, 130, 246], [249, 115, 22], [16, 185, 129], [168, 85, 247], [239, 68, 68], [20, 184, 166],
    [234, 179, 8], [99, 102, 241], [244, 63, 94], [14, 165, 233], [132, 204, 22], [217, 70, 239],
];
const topicLineColor = (idx) => TOPIC_PALETTE[Math.max(0, idx) % TOPIC_PALETTE.length];

// ═══════════════════════════════════════════════════════════════════════════
// KLEINE TABELLE (Listen der Anomalien-Seite), mit Seitenumbruch
// cols: [{label, w, align}], rows: [{cells: [string | {text, color, bold}], note}]
// ═══════════════════════════════════════════════════════════════════════════

const drawMiniTable = (doc, y, { cols, rows, rowH = 6, newPage, limit }) => {
    const x = PAGE.mx;
    const colX = [];
    let acc = x + 2;
    cols.forEach((c) => { colX.push(acc); acc += c.w; });

    const head = (yy) => {
        doc.setFillColor(...C.s50);
        doc.rect(x, yy - 4, PAGE.cw, 6, 'F');
        doc.setFont('courier', 'bold');
        doc.setFontSize(6.5);
        doc.setTextColor(...C.s600);
        cols.forEach((c, i) => {
            if (c.align === 'right') doc.text(c.label.toUpperCase(), colX[i] + c.w - 2, yy, { align: 'right' });
            else doc.text(c.label.toUpperCase(), colX[i], yy);
        });
        return yy + 6;
    };

    let curY = head(y);
    rows.forEach((row, idx) => {
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(6.5);
        const noteLines = row.note ? doc.splitTextToSize(String(row.note), PAGE.cw - 6) : [];
        const h = rowH + noteLines.length * 3;
        if (curY - 4 + h > limit) curY = head(newPage());
        if (idx % 2 === 1) {
            doc.setFillColor(...C.s50);
            doc.rect(x, curY - 4, PAGE.cw, h, 'F');
        }
        row.cells.forEach((cell, i) => {
            const c = cell && typeof cell === 'object' ? cell : { text: cell };
            doc.setFont('helvetica', c.bold ? 'bold' : 'normal');
            doc.setFontSize(7);
            doc.setTextColor(...(c.color || C.s700));
            const text = fitText(doc, String(c.text ?? '–'), cols[i].w - 3);
            if (cols[i].align === 'right') doc.text(text, colX[i] + cols[i].w - 2, curY, { align: 'right' });
            else doc.text(text, colX[i], curY);
        });
        if (noteLines.length) {
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(6.5);
            doc.setTextColor(...C.s500);
            noteLines.forEach((l, i) => doc.text(l, colX[0], curY + 3.4 + i * 3));
        }
        doc.setDrawColor(...C.s100);
        doc.setLineWidth(0.15);
        doc.line(x, curY - 4 + h, x + PAGE.cw, curY - 4 + h);
        curY += h;
    });
    return curY;
};

// Zwischenüberschrift einer Liste
const drawListTitle = (doc, y, title, sub = null) => {
    doc.setFont('helvetica', 'bold');
    doc.setFontSize(9);
    doc.setTextColor(...C.s800);
    doc.text(title, PAGE.mx, y);
    const titleW = doc.getTextWidth(title);
    if (sub) {
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s500);
        doc.text(fitText(doc, sub, PAGE.cw - titleW - 6), PAGE.mx + titleW + 3, y);
    }
    return y + 6;
};

const ANOMALY_COLOR = { fall: C.rose500, rise: C.emerald500 };
const ANOMALY_FILL  = { fall: [251, 188, 199], rise: [171, 230, 211] };   // Ring: 35 % Deckung auf Weiß
const DIRECTION_LABEL = { fall: 'Abfall', rise: 'Anstieg' };
const SEVERITY_LABEL  = { high: 'deutlich', medium: 'mäßig' };

// ═══════════════════════════════════════════════════════════════════════════
// HAUPT-EXPORT — alle Elemente des Dashboards in der Reihenfolge der Seite
// ═══════════════════════════════════════════════════════════════════════════

export const exportKPIsAsPDF = async (kpiData) => {
    const {
        companyName = 'Unbekannte Firma',
        reviewCount = null,            // Bewertungen laut Firmenliste (Seitenkopf)
        timeRange = 'all',             // globaler Zeitfilter (all | 1y | 3y)
        lastImportLocal = null,        // letzter Import über die App (localStorage), ISO-Zeit
        dataStatus = null,             // GET /companies/{id}/data-status
        avgScore = '-',                // Ø Score: Mittel der Gesamtnote (score, D1)
        avgCount = null,               // score_n
        categoryMean = null,           // avg_overall: Mittel der Kategorienmittel
        trend = null,
        rolling = null,                // GET /companies/{id}/ratings/trend?mode=rolling
        mostCritical = null,
        negativeTopic = '-',
        negativeTopicItem = null,
        timelineChartElement = null,
        timelineFilters = null,
        topicRatingChartElement = null,
        topicRatingFilters = null,
        anomalyChartElement = null,
        anomalyData = null,            // Zustand der AnomalyCard (onDataChange)
        topicOverviewData = null,
    } = kpiData;

    // Charts extrahieren (SVG → PNG, html2canvas als Rückfall)
    console.log('📸 Extrahiere Charts…');
    let timelineImg = null, topicRatingImg = null, anomalyImg = null;
    try { timelineImg = await extractChartSvgFirst(timelineChartElement); }
    catch (e) { console.warn('Timeline-Chart:', e); }
    try { topicRatingImg = await extractChartSvgFirst(topicRatingChartElement); }
    catch (e) { console.warn('Topic-Rating-Chart:', e); }
    try { anomalyImg = await extractChartSvgFirst(anomalyChartElement); }
    catch (e) { console.warn('Anomalien-Chart:', e); }

    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    const now = new Date();
    const dateStr = now.toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' });
    const timeStr = now.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }) + ' Uhr';
    const dateShort = now.toLocaleDateString('de-DE', { day: '2-digit', month: '2-digit', year: 'numeric' });

    const headerLabel = `WorkPulse · ${companyName} — Analytics Report`;
    const footerLeft  = `WorkPulse · ${companyName}`;
    const limit = PAGE.h - 19;   // unterste Grundlinie des Inhalts, über der Fußzeile

    // Seitenverwaltung: Inhaltsseiten mit Kopfzeile; das Inhaltsverzeichnis entsteht
    // am Ende aus den Startseiten der Abschnitte.
    const ctx = { page: 1 };
    const toc = [];
    const newPage = () => {
        doc.addPage();
        ctx.page += 1;
        drawPageHeader(doc, headerLabel, dateShort);
        return 30;
    };
    const startSection = (title, meta) => {
        const y = newPage();
        toc.push({ title, page: ctx.page, meta });
        return y;
    };
    const ensureSpace = (y, needed) => (y + needed > limit ? newPage() : y);

    const range = TIME_RANGE_LABEL[timeRange] || TIME_RANGE_LABEL.all;
    const emp = dataStatus?.sources?.employee ?? null;
    const cand = dataStatus?.sources?.candidates ?? null;
    const topics = topicOverviewData?.topics || [];
    const ovStats = topicOverviewData?.stats || {};

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 1 — COVER (Inhaltsverzeichnis und Fußzeile folgen am Ende)
    // ───────────────────────────────────────────────────────────────────────
    const metaBottom = drawCoverPage(doc, {
        companyName,
        subtitle: 'Übersicht aller Bewertungen, Topics und Trends. Mitarbeiter- und Bewerberperspektive, aggregiert und über Zeit verglichen.',
        dateStr,
        timeStr,
        meta: [
            { label: 'Zeitfilter', value: range.value, sub: range.sub },
            {
                label: 'Zeitraum',
                value: timelineFilters?.stats?.dateRange || 'gesamter Zeitraum',
                sub:   timelineFilters?.stats?.dateRangeSub || 'Timeline: Historie + Prognose',
            },
            {
                label: 'Bewertungen',
                value: fmtInt(reviewCount ?? dataStatus?.n_reviews_total ?? null),
                sub:   emp || cand ? `${fmtInt(emp?.n_reviews)} Mitarbeitende · ${fmtInt(cand?.n_reviews)} Bewerbende` : 'im Datensatz',
            },
            { label: 'Topics', value: String(topics.length || ovStats.totalTopics || '–'), sub: 'Themen aus Freitexten' },
            { label: 'Erwähnungen', value: fmtInt(ovStats.totalMentions ?? null), sub: 'über alle Topics' },
        ],
    });

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 2 — DATENSTAND + KENNZAHLEN
    // ───────────────────────────────────────────────────────────────────────
    let y = startSection('Datenstand & Kennzahlen', 'Abdeckung des Datensatzes, fünf Kacheln mit n und Datenbasis');
    y = drawSectionTitle(doc, y, 1, 'Datenstand', 'Datensatz · Abdeckung · Zeitstempel');
    y = drawDataStatusCard(doc, y, dataStatus, { lastImportLocal });

    const kpis = buildKpiCards({ avgScore, avgCount, trend, rolling, mostCritical, negativeTopic, negativeTopicItem });
    y = ensureSpace(y + 8, 8 + kpiGridHeight(doc, kpis) + 12);
    y = drawSectionTitle(doc, y, 2, 'Kennzahlen', `Skala 1 – 5 · Zeitfilter ${range.value}`);
    y = drawKPIGrid(doc, y, kpis, { perRow: 3 });

    // Berechnungshinweis (FA-38), wortgleich mit Kachel und Detailfenster (lib/scoreText.js)
    doc.setFont('helvetica', 'normal');
    doc.setFontSize(7);
    doc.setTextColor(...C.s600);
    y = drawWrapped(doc, SCORE_HINT, PAGE.mx, y + 5, PAGE.cw, { lineH: 3.1 });
    if (categoryMean != null) {
        y = drawWrapped(
            doc,
            `${CATEGORY_MEAN_TITLE}: ${fmtNum(categoryMean, 2)} / 5. ${CATEGORY_MEAN_NOTE}`,
            PAGE.mx, y + 1.5, PAGE.cw, { lineH: 3.1 },
        );
    }

    doc.setFont('helvetica', 'italic');
    doc.setFontSize(7);
    doc.setTextColor(...C.s500);
    y = drawWrapped(
        doc,
        `Zeitfilter „${range.value}“ gilt für Ø Score, Trend, Most Critical, Negative Topic, Timeline, Topics im Detail und Topic-Übersicht. Der 12- vs. 24-Monats-Schnitt und die Anomalien beziehen sich immer auf die ganze Reihe. Kennzeichen: Sternebewertung = Sterne der Kununu-Bewertungen, Freitextanalyse = Freitexte der Bewertungen.`,
        PAGE.mx, y + 5, PAGE.cw, { lineH: 3.1 },
    );

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 3 — TIMELINE + TOPICS IM DETAIL (Diagrammzeile des Dashboards)
    // ───────────────────────────────────────────────────────────────────────
    y = startSection('Timeline & Topics im Detail', 'Bewertungsverlauf und Bewertungen je Topic über Zeit');
    y = drawSectionTitle(doc, y, 3, 'Timeline', 'Zeitreihe · Historie & Prognose');

    const tlSource = sourceName(timelineFilters?.source);
    const tlMetric = timelineFilters?.metric || 'Ø Score';
    const tlLegend = [{ label: 'Historisch', color: C.blue600 }];
    if (timelineFilters?.hasInterpolation) tlLegend.push({ label: 'Interpoliert (gestrichelt)', color: C.s400, dashed: true });
    if (timelineFilters?.hasForecast)      tlLegend.push({ label: 'Prognose', color: C.orange500, dashed: true });
    tlLegend.push({
        label: `Quelle: ${tlSource} · ${tlMetric}${timelineFilters?.stats?.dataPoints != null ? ` · n = ${timelineFilters.stats.dataPoints} Datenpunkte` : ''}`,
        sourceNote: true,
    });
    y = drawDashboardCard(doc, y, {
        header: {
            eyebrow: 'Zeitreihe · Historie & Prognose',
            title: 'Timeline',
            subtitle: `${tlSource} · ${tlMetric}${timelineFilters?.granularity === 'year' && timelineFilters?.selectedYear ? ` · ${timelineFilters.selectedYear}` : ''}`,
            iconTone: 'info',
            controlsText: tlSource,
            basis: 'stars',
        },
        chart: timelineImg,
        chartH: 58,
        emptyText: 'Keine Daten für diesen Zeitraum verfügbar',
        legend: tlLegend,
        stats: timelineStats(timelineFilters),
        caption: 'Abb. 1 · Bewertungsverlauf mit Prognose · gestrichelte Linien = interpolierte bzw. prognostizierte Werte',
    });

    y += 5;
    y = drawSectionTitle(doc, y, 4, 'Topics im Detail', 'Topic-Bewertungen · Detailansicht');

    const trSource = sourceName(topicRatingFilters?.source);
    const visibleTopics = topicRatingFilters?.visibleTopics || [];
    const allTopics = topicRatingFilters?.allTopics || [];
    const trGran = topicRatingFilters?.granularity === 'year' ? 'jährlich aggregiert' : 'aggregiert';
    const trStats = [];
    if (topicRatingFilters?.stats?.dataPoints != null) {
        trStats.push({ label: 'Datenpunkte', value: String(topicRatingFilters.stats.dataPoints), sub: trGran });
    }
    if (topicRatingFilters?.stats?.avgScore) {
        trStats.push({ label: 'Ø Score', value: fmtNum(topicRatingFilters.stats.avgScore, 2), sub: `über alle ${visibleTopics.length} Topics`, tone: 'good' });
    }
    if (topicRatingFilters?.stats?.bestTopic) {
        trStats.push({ label: 'Bestes Topic', value: topicRatingFilters.stats.bestTopic.name, sub: `Ø ${fmtNum(topicRatingFilters.stats.bestTopic.score, 2)}`, tone: 'good' });
    }
    if (topicRatingFilters?.stats?.worstTopic) {
        trStats.push({ label: 'Schlechtestes', value: topicRatingFilters.stats.worstTopic.name, sub: `Ø ${fmtNum(topicRatingFilters.stats.worstTopic.score, 2)}`, tone: 'bad' });
    }
    const trLegend = visibleTopics.slice(0, 6).map((topic) => ({
        label: prettifyTopic(topic),
        color: topicLineColor(allTopics.indexOf(topic)),
    }));
    if (visibleTopics.length > 6) trLegend.push({ label: `+ ${visibleTopics.length - 6} weitere`, color: C.s400, shape: 'none' });
    trLegend.push({ label: `Quelle: ${trSource} · Themen aus Freitexten, Bewertung aus Sternen`, sourceNote: true });

    y = drawDashboardCard(doc, y, {
        header: {
            eyebrow: 'Topic-Bewertungen',
            title: 'Topics im Detail',
            subtitle: `${trSource} · ${visibleTopics.length}/${allTopics.length || '?'} Topics · ${topicRatingFilters?.granularity === 'year' && topicRatingFilters?.selectedYear ? topicRatingFilters.selectedYear : 'gesamter Zeitraum'}`,
            iconTone: 'warn',
            controlsText: trSource,
            basis: 'stars',
        },
        chart: topicRatingImg,
        chartH: 58,
        emptyText: 'Keine Daten für diesen Zeitraum verfügbar',
        legend: trLegend,
        stats: trStats,
        caption: `Abb. 2 · Durchschnittliche Bewertung pro Topic über Zeit · Quelle: ${trSource}`,
    });

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 4 — ANOMALIEN IM VERLAUF (Inkrement 1, Karte unter der Diagrammzeile)
    // ───────────────────────────────────────────────────────────────────────
    y = startSection('Anomalien im Verlauf', 'auffällige Veränderungen, Einzelmonate, Eignung der Reihe');
    y = drawSectionTitle(doc, y, 5, 'Anomalien im Verlauf', 'Verlauf · auffällige Veränderungen');

    const an = anomalyData;
    const anomalies = an?.anomalies || [];
    const outliers = an?.outliers || [];
    const elig = an?.eligibility || null;
    const minReviews = an?.minReviews ?? dataStatus?.thresholds?.min_reviews_per_month ?? 5;

    const anLegend = [{ label: 'Monatsmittel (bewertete Monate)', color: C.blue500 }];
    if (an?.hasInterpolation) {
        anLegend.push({ label: `interpoliert (Monat mit weniger als ${minReviews} Bewertungen mit Wert, nicht in der Erkennung)`, color: C.s400, dashed: true });
    }
    if (anomalies.length) {
        anLegend.push({ label: 'Ring = auffällige Veränderung ab diesem Monat: Abfall', color: ANOMALY_COLOR.fall, fill: ANOMALY_FILL.fall, shape: 'ring' });
        anLegend.push({ label: 'Anstieg', color: ANOMALY_COLOR.rise, fill: ANOMALY_FILL.rise, shape: 'ring' });
    }
    if (outliers.length) {
        anLegend.push({ label: 'Raute = auffälliger Einzelmonat (unter bzw. über den Nachbarmonaten, kein neues Niveau)', color: C.s500, shape: 'diamond' });
    }
    anLegend.push({ label: `Sternebewertung, Monatsmittel, Monate mit mindestens ${minReviews} Bewertungen mit Wert`, sourceNote: true });

    const anStats = [
        {
            label: 'Bewertete Monate',
            value: String(an?.evaluatedMonths ?? elig?.evaluated_months ?? '–'),
            sub: an?.monthsInSpan ? `von ${an.monthsInSpan} Monaten im Zeitraum` : 'Monate mit genug Bewertungen',
        },
        { label: 'Veränderungen', value: String(anomalies.length), sub: 'auffällige Niveauwechsel', tone: anomalies.length ? 'warn' : 'neutral' },
        { label: 'Einzelmonate', value: String(outliers.length), sub: 'auffällig, kein neues Niveau', tone: outliers.length ? 'warn' : 'neutral' },
        {
            label: 'Erkennung',
            value: elig ? (elig.eligible ? 'geeignet' : 'nicht geeignet') : '–',
            sub: elig ? `ab ${elig.min_evaluated_months} bewerteten Monaten` : '',
            tone: elig ? (elig.eligible ? 'good' : 'bad') : 'neutral',
        },
    ];

    y = drawDashboardCard(doc, y, {
        header: {
            eyebrow: 'Verlauf · auffällige Veränderungen',
            title: 'Anomalien im Verlauf',
            subtitle: an ? `${an.group} · ${an.dimensionName} · ${an.countText}` : 'keine Daten',
            iconTone: 'warn',
            controlsText: an?.group || null,
            basis: 'stars',
        },
        chart: anomalyImg,
        chartH: 78,
        legend: anLegend,
        stats: anStats,
        emptyText: an?.error
            ? `Anomalien konnten nicht geladen werden: ${an.error}`
            : an && !an.monthsInSpan ? 'Keine datierten Bewertungen vorhanden.' : 'Diagramm nicht verfügbar',
        caption: `Abb. 3 · Monatsverlauf${an ? ` · ${an.group}, ${an.dimensionName}` : ''}${an?.evaluatedRange ? ` · angezeigt ${fmtSpan(an.evaluatedRange.from, an.evaluatedRange.to)}` : ''} · keine Aussage über Ursachen`,
    });

    // Hinweise unter der Karte (wie im Dashboard)
    if (elig && !elig.eligible) {
        y = ensureSpace(y, 12);
        doc.setFont('helvetica', 'bold');
        doc.setFontSize(8);
        doc.setTextColor(...C.s700);
        doc.text('Keine automatische Erkennung.', PAGE.mx, y + 2);
        const lw = doc.getTextWidth('Keine automatische Erkennung.') + 2;
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s600);
        y = drawWrapped(doc, elig.reason || '', PAGE.mx + lw, y + 2, PAGE.cw - lw, { lineH: 3.4 }) + 1;
    }
    if (an?.statusHint) {
        y = ensureSpace(y, 12);
        doc.setFont('helvetica', 'normal');
        doc.setFontSize(7.5);
        doc.setTextColor(...C.s500);
        y = drawWrapped(doc, `Hinweis zum Status: ${an.statusHint}`, PAGE.mx, y + 2, PAGE.cw, { lineH: 3.2 }) + 1;
    }

    // Markierungen als Liste: im Dashboard als Tooltip, im PDF ausgeschrieben
    if (anomalies.length) {
        y = ensureSpace(y + 4, 24);
        y = drawListTitle(doc, y, 'Auffällige Veränderungen', `${anomalies.length} Niveauwechsel · Stufe von Ø davor zu Ø danach, Bewertungen mit Wert je Abschnitt`);
        y = drawMiniTable(doc, y, {
            cols: [
                { label: 'ab Monat', w: 20 },
                { label: 'Richtung', w: 16 },
                { label: 'Delta', w: 20 },
                { label: 'Ø davor (Zeitraum)', w: 40 },
                { label: 'Ø danach (Zeitraum)', w: 40 },
                { label: 'n davor / danach', w: 26 },
                { label: 'Ausmaß', w: 14 },
            ],
            rows: anomalies.map((a) => {
                const color = ANOMALY_COLOR[a.direction] || C.s700;
                const notes = [];
                if (a.gap_months > 0) {
                    notes.push(`Davor ${a.gap_months} ${a.gap_months === 1 ? 'Monat' : 'Monate'} nicht bewertet (seit ${fmtPeriod(a.previous_period)}); der Übergang kann in dieser Lücke liegen.`);
                }
                if (a.month_near_previous_level) {
                    notes.push('Das Monatsmittel liegt noch nahe am alten Niveau. Ein Abschnitt umfasst mindestens 3 Monate, der sichtbare Übergang folgt daher später.');
                }
                return {
                    cells: [
                        `ab ${fmtPeriod(a.date)}`,
                        { text: DIRECTION_LABEL[a.direction] || a.direction, color, bold: true },
                        { text: `${fmtSigned(a.delta)} Sterne`, color, bold: true },
                        `${fmtNum(a.before_mean)} (${fmtSpan(a.before_from, a.previous_period)})`,
                        `${fmtNum(a.after_mean)} (${fmtSpan(a.date, a.after_to)})`,
                        `${fmtInt(a.n_reviews_before)} / ${fmtInt(a.n_reviews_after)}`,
                        SEVERITY_LABEL[a.severity] || a.severity || '–',
                    ],
                    note: notes.length ? notes.join(' ') : null,
                };
            }),
            newPage,
            limit,
        });
    }
    if (outliers.length) {
        y = ensureSpace(y + 5, 24);
        y = drawListTitle(doc, y, 'Auffällige Einzelmonate', `${outliers.length} ${outliers.length === 1 ? 'Monat' : 'Monate'} · Abweichung vom Niveau der Nachbarmonate, kein neues Niveau`);
        y = drawMiniTable(doc, y, {
            cols: [
                { label: 'Monat', w: 22 },
                { label: 'Abweichung', w: 26 },
                { label: 'Ø Monat', w: 20 },
                { label: 'Niveau der Nachbarmonate', w: 70 },
                { label: 'Bewertungen mit Wert', w: 38 },
            ],
            rows: outliers.map((o) => {
                const color = ANOMALY_COLOR[o.direction] || C.s700;
                return {
                    cells: [
                        fmtPeriod(o.date),
                        { text: `${fmtSigned(o.deviation)} Sterne`, color, bold: true },
                        fmtNum(o.month_mean),
                        `${fmtNum(o.level)} (${fmtSpan(o.neighbours_from, o.neighbours_to)})`,
                        fmtInt(o.n_values),
                    ],
                };
            }),
            newPage,
            limit,
        });
    }
    if (an && !an.error && an.monthsInSpan > 0) {
        y = ensureSpace(y + 4, 8);
        doc.setFont('helvetica', 'italic');
        doc.setFontSize(7);
        doc.setTextColor(...C.s400);
        doc.text('Die Detailseite „Anomalien“ zeigt zu jeder Markierung die Bewertungen des Zeitraums, den Vorher-Nachher-Vergleich und die Belege.', PAGE.mx, y + 2);
    }

    // ───────────────────────────────────────────────────────────────────────
    // SEITE 5+ — TOPIC-ÜBERSICHT (alle Topics, Tabelle mehrseitig)
    // ───────────────────────────────────────────────────────────────────────
    if (topics.length > 0) {
        y = startSection('Topic-Übersicht', `Tabelle aller ${topics.length} Topics mit Beispiel`);
        y = drawSectionTitle(doc, y, 6, 'Topic-Übersicht', 'Themenbereiche · Tabellenansicht');

        const ovSource = sourceName(topicOverviewData.sourceFilter);
        const totalReviews = topicOverviewData.totalReviews ?? null;
        const avgRating = topics.reduce((s, t) => s + (Number(t.avgRating) || 0), 0) / topics.length;
        const limited = ovStats.limited ?? topics.filter((t) => t.statistical_meta?.risk_level === 'limited').length;
        const sentCounts = {
            total: topics.length,
            pos: topics.filter((t) => t.sentiment === 'Positiv').length,
            neu: topics.filter((t) => t.sentiment === 'Neutral' || !t.sentiment).length,
            neg: topics.filter((t) => t.sentiment === 'Negativ').length,
        };

        const cardX = PAGE.mx;
        const cardW = PAGE.cw;
        const headerH = 18;
        let segTop = y;

        drawCardHeader(doc, y, {
            eyebrow: 'Topic-Übersicht',
            title: 'Themenbereiche',
            subtitle: `${ovSource} · ${topics.length} Topics${totalReviews != null ? ` · n = ${fmtInt(totalReviews)} Bewertungen` : ''} · ${fmtInt(ovStats.totalMentions ?? null)} Erwähnungen`,
            iconTone: 'info',
            controlsText: ovSource,
            basis: 'text',
        });
        let cy = y + headerH;
        doc.setDrawColor(...C.s100);
        doc.setLineWidth(0.2);
        doc.line(cardX + 2, cy, cardX + cardW - 2, cy);

        // Warnbanner (wie die Karte): Topics mit begrenzter Datenbasis
        if (limited > 0) {
            doc.setFillColor(...C.rose50);
            doc.setDrawColor(...C.rose300);
            doc.setLineWidth(0.2);
            doc.roundedRect(cardX + 3, cy + 2.5, cardW - 6, 9.5, 1.5, 1.5, 'FD');
            doc.setFont('helvetica', 'bold');
            doc.setFontSize(7.5);
            doc.setTextColor(...C.rose700);
            doc.text(`Begrenzte Datenbasis bei ${limited} Topic${limited !== 1 ? 's' : ''}`, cardX + 7, cy + 6.3);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(6.8);
            doc.text('Weniger als 30 Reviews — Ergebnisse mit Vorsicht interpretieren', cardX + 7, cy + 9.8);
            cy += 14;
        }

        // Stats-Strip (Topics, Ø Rating mit n, Erwähnungen) und Sentiment-Verteilung
        cy = drawStatsFooter(doc, cardX, cy, cardW, [
            { label: 'Topics',      value: String(topics.length), sub: 'identifiziert' },
            { label: 'Ø Rating',    value: fmtNum(avgRating, 2), sub: totalReviews != null ? `${fmtInt(totalReviews)} Bewertungen` : 'ungewichtet', tone: scoreTone(avgRating) },
            { label: 'Erwähnungen', value: fmtInt(ovStats.totalMentions ?? null), sub: 'über alle Topics' },
            { label: 'Sentiment',   value: `${sentCounts.pos} · ${sentCounts.neu} · ${sentCounts.neg}`, sub: 'Positiv · Neutral · Negativ' },
        ]);

        // Sentiment-Tabs
        cy = drawSentimentTabs(doc, cardX, cy, cardW, sentCounts);

        // Tabelle, bei Bedarf über mehrere Seiten
        const rowH = topics.some((t) => t.example) ? TOPIC_ROW_H_EX : TOPIC_ROW_H;
        let curY = drawTopicTableHead(doc, cardX, cy + 6, cardW);
        const closeSegment = (bottom) => {
            doc.setDrawColor(...C.s200);
            doc.setLineWidth(0.3);
            doc.roundedRect(cardX, segTop, cardW, bottom - segTop, 2.5, 2.5, 'S');
        };
        topics.forEach((topic, idx) => {
            if (curY - 4.5 + rowH > limit) {
                closeSegment(curY - 4.5);
                const ny = newPage();
                doc.setFont('helvetica', 'bold');
                doc.setFontSize(10);
                doc.setTextColor(...C.s700);
                doc.text(`Topic-Übersicht (Fortsetzung) · ${ovSource}`, PAGE.mx, ny);
                segTop = ny + 4;
                curY = drawTopicTableHead(doc, cardX, segTop + 6, cardW);
            }
            drawTopicRow(doc, cardX, curY, cardW, topic, idx, rowH);
            curY += rowH;
        });
        closeSegment(curY - 4.5 + 1.5);
        y = curY + 2;

        // Hinweis, falls die API mehr Topics zählt als sie liefert
        const totalTopicCount = ovStats.totalTopics || topics.length;
        const hiddenCount = Math.max(0, totalTopicCount - topics.length);
        if (hiddenCount > 0) {
            y = ensureSpace(y, 10);
            doc.setFont('helvetica', 'italic');
            doc.setFontSize(7);
            doc.setTextColor(...C.s500);
            doc.text(`${topics.length} von ${totalTopicCount} Topics · weitere ${hiddenCount} Topics in der Web-App einsehbar`, PAGE.mx, y + 4);
        }
    }

    // ───────────────────────────────────────────────────────────────────────
    // Inhaltsverzeichnis auf dem Cover, Fußzeilen auf allen Seiten
    // ───────────────────────────────────────────────────────────────────────
    const total = doc.getNumberOfPages();
    const pageNo = (p) => `${String(p).padStart(2, '0')} / ${String(total).padStart(2, '0')}`;
    doc.setPage(1);
    drawCoverToc(doc, metaBottom + 18, toc);
    drawPageFooter(doc, 'WorkPulse · Analytics Report', companyName, pageNo(1));
    for (let p = 2; p <= total; p++) {
        doc.setPage(p);
        drawPageFooter(doc, footerLeft, pageNo(p), dateShort);
    }

    // ───────────────────────────────────────────────────────────────────────
    // Speichern
    // ───────────────────────────────────────────────────────────────────────
    const safeName = String(companyName).replace(/\s+/g, '_');
    const fileName = `Analytics_Report_${safeName}_${now.toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    console.log(`✅ PDF gespeichert: ${fileName} (${total} Seiten)`);
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPARE PDF EXPORT — private helpers
// ═══════════════════════════════════════════════════════════════════════════

/** Draw a chart image scaled to fill available width, returns new y. */
const _cmpAddChart = (doc, imgResult, yPos, maxAvailableHeight = null) => {
    if (!imgResult?.dataUrl) return yPos;
    const availW = PAGE.cw;
    const availH = maxAvailableHeight || (PAGE.h - PAGE.my - 10 - yPos);
    const aspect = imgResult.w / imgResult.h;
    let imgW = availW;
    let imgH = imgW / aspect;
    if (imgH > availH) { imgH = availH; imgW = imgH * aspect; }
    const xPos = PAGE.mx + (availW - imgW) / 2;
    doc.addImage(imgResult.dataUrl, 'PNG', xPos, yPos, imgW, imgH, undefined, 'FAST');
    return yPos + imgH + 4;
};

/** Draw a bold section title + optional subtitle + rule, returns new y. */
const _cmpAddTitle = (doc, title, yPos, subtitle = null) => {
    doc.setFontSize(14);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s900);
    doc.text(title, PAGE.mx, yPos);
    let y = yPos + 7;
    if (subtitle) {
        doc.setFontSize(9);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s500);
        doc.text(subtitle, PAGE.mx, y);
        y += 5;
    }
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, y, PAGE.cr, y);
    return y + 6;
};

/** Draw page footer with label + page number. */
const _cmpAddFooter = (doc, pageNum, totalPages, label) => {
    const y = PAGE.h - PAGE.my + 6;
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.3);
    doc.line(PAGE.mx, y - 4, PAGE.cr, y - 4);
    doc.setFontSize(7.5);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s400);
    doc.text(label, PAGE.mx, y);
    doc.text(`Seite ${pageNum} / ${totalPages}`, PAGE.cr, y, { align: 'right' });
};

// ═══════════════════════════════════════════════════════════════════════════
// COMPARE PDF EXPORT — main
// ═══════════════════════════════════════════════════════════════════════════

export const exportCompareAsPDF = async (compareData) => {
    const {
        companies = [],         // [{ name, id, score, trend, mostCritical, negativeTopic, categoryRatings }]
        radarChartElement = null,
        barChartElement = null,
        timelineChartElement = null,
        categoryData = [],      // [{ category, ...companyValues }]
        companyColors = null,   // optional hex strings per company
    } = compareData;

    // Convert hex colour strings supplied by Compare.jsx to RGB triples
    const hexToRgb = (hex) => [
        parseInt(hex.slice(1, 3), 16),
        parseInt(hex.slice(3, 5), 16),
        parseInt(hex.slice(5, 7), 16),
    ];
    const CMP_COLORS_DEFAULT = [C.blue500, C.emerald500, C.orange500, C.rose500, [139, 92, 246]];
    const CMP_COLORS = companyColors
        ? companyColors.map(hexToRgb)
        : CMP_COLORS_DEFAULT;

    const companyNames = companies.map(c => c.name || 'Unbekannt');
    const titleLabel = companyNames.join(' vs. ');

    const doc = new jsPDF({ orientation: 'portrait', unit: 'mm', format: 'a4' });

    // ── chart images ──────────────────────────────────────────────────────
    let radarImg = null, barImg = null, timelineImg = null;
    try { radarImg    = await extractChart(radarChartElement); }    catch (e) { console.warn('Radar-Chart Extraktion fehlgeschlagen:', e); }
    try { barImg      = await extractChart(barChartElement); }      catch (e) { console.warn('Bar-Chart Extraktion fehlgeschlagen:', e); }
    try { timelineImg = await extractChart(timelineChartElement); } catch (e) { console.warn('Timeline-Chart Extraktion fehlgeschlagen:', e); }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 1 — cover
    // ═════════════════════════════════════════════════════════════════════
    const headerH = 125;
    doc.setFillColor(...C.navy);
    doc.rect(0, 0, PAGE.w, headerH, 'F');
    doc.setFillColor(...C.s800);
    doc.rect(0, headerH - 25, PAGE.w, 25, 'F');

    // accent strip
    doc.setFillColor(...C.blue600);
    doc.rect(0, 0, PAGE.w, 2.5, 'F');

    // bar-chart icon
    const logoX = PAGE.w / 2;
    const logoY = 38;
    [[logoX - 16, 18], [logoX - 8, 14], [logoX, 10], [logoX + 8, 16]].forEach(([x, h], i) => {
        doc.setFillColor(...(i % 2 === 0 ? C.blue600 : C.blue200));
        doc.roundedRect(x, logoY + (18 - h), 5, h, 1, 1, 'F');
    });

    // title
    doc.setFontSize(26);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s0);
    doc.text('Firmenvergleich', PAGE.w / 2, 78, { align: 'center' });

    doc.setFontSize(12);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.blue200);
    const coverSubtitle = companyNames.length <= 3
        ? companyNames.join('  ·  ')
        : companyNames.slice(0, 3).join('  ·  ');
    doc.text(coverSubtitle, PAGE.w / 2, 90, { align: 'center' });

    doc.setDrawColor(...C.s300);
    doc.setLineWidth(0.3);
    doc.line(PAGE.w / 2 - 40, 96, PAGE.w / 2 + 40, 96);

    doc.setFontSize(10);
    doc.setTextColor(...C.s400);
    doc.text(
        new Date().toLocaleDateString('de-DE', { day: '2-digit', month: 'long', year: 'numeric' }),
        PAGE.w / 2, 103, { align: 'center' }
    );

    // summary box
    const execY = headerH + 15;
    doc.setFillColor(...C.s0);
    doc.setDrawColor(...C.s200);
    doc.setLineWidth(0.4);
    doc.roundedRect(PAGE.mx, execY, PAGE.cw, 40 + companies.length * 8, 3, 3, 'FD');
    doc.setFillColor(...C.blue600);
    doc.roundedRect(PAGE.mx, execY, PAGE.cw, 3, 3, 3, 'F');
    doc.setFillColor(...C.s0);
    doc.rect(PAGE.mx, execY + 2, PAGE.cw, 2, 'F');

    doc.setFontSize(11);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s800);
    doc.text('Zusammenfassung', PAGE.mx + 8, execY + 12);

    doc.setFontSize(9);
    doc.setFont('helvetica', 'normal');
    doc.setTextColor(...C.s500);
    doc.text(`Vergleich von ${companies.length} Unternehmen anhand von Bewertungen,`, PAGE.mx + 8, execY + 20);
    doc.text('Kategorien, Trends und Themenbereichen.', PAGE.mx + 8, execY + 26);

    let summaryY = execY + 34;
    companies.forEach((comp, i) => {
        const col = CMP_COLORS[i] || C.s400;
        doc.setFillColor(...col);
        doc.circle(PAGE.mx + 12, summaryY + 3, 2, 'F');
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.s800);
        doc.text(comp.name || 'Unbekannt', PAGE.mx + 18, summaryY + 4);
        summaryY += 8;
    });

    // table of contents
    let tocY = summaryY + 14;
    doc.setFontSize(12);
    doc.setFont('helvetica', 'bold');
    doc.setTextColor(...C.s800);
    doc.text('Inhalt', PAGE.mx, tocY);
    tocY += 8;

    const tocItems = [];
    let pgCounter = 1;
    pgCounter++; tocItems.push(['KPI-Vergleich', pgCounter]);
    if (radarImg || barImg) { pgCounter++; tocItems.push(['Kategorievergleich', pgCounter]); }
    if (timelineImg)        { pgCounter++; tocItems.push(['Bewertungsverlauf', pgCounter]); }
    if (categoryData.length > 0) { pgCounter++; tocItems.push(['Detailvergleich', pgCounter]); }

    tocItems.forEach(([label, pg]) => {
        doc.setFontSize(9.5);
        doc.setFont('helvetica', 'normal');
        doc.setTextColor(...C.s800);
        doc.text(label, PAGE.mx + 4, tocY);
        const dotX = PAGE.mx + 4 + doc.getTextWidth(label) + 2;
        const pageX = PAGE.cr - 4;
        doc.setTextColor(...C.s300);
        doc.text('.'.repeat(Math.max(1, Math.floor((pageX - dotX - 10) / 1.5))), dotX, tocY);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.blue600);
        doc.text(String(pg), pageX, tocY, { align: 'right' });
        tocY += 6;
    });

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 2 — KPI comparison
    // ═════════════════════════════════════════════════════════════════════
    doc.addPage();
    doc.setFillColor(...C.s100);
    doc.rect(0, 0, PAGE.w, PAGE.h, 'F');

    let y = _cmpAddTitle(doc, 'KPI-Vergleich', PAGE.my + 5, 'Gegenüberstellung der wichtigsten Kennzahlen');

    // legend
    companies.forEach((comp, i) => {
        const col = CMP_COLORS[i] || C.s400;
        doc.setFillColor(...col);
        doc.circle(PAGE.mx + 4 + i * 60, y, 2, 'F');
        doc.setFontSize(8);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...col);
        doc.text(comp.name.length > 18 ? comp.name.substring(0, 18) + '…' : comp.name, PAGE.mx + 9 + i * 60, y + 0.5);
    });
    y += 10;

    const drawKPIBlock = (title, yPos, getValue) => {
        const rowH = 8;
        const boxH = 10 + companies.length * rowH + 4;
        doc.setFillColor(...C.s0);
        doc.setDrawColor(...C.s200);
        doc.setLineWidth(0.3);
        doc.roundedRect(PAGE.mx, yPos, PAGE.cw, boxH, 2, 2, 'FD');
        doc.setFontSize(9);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(...C.s800);
        doc.text(title, PAGE.mx + 6, yPos + 7);
        let rowY = yPos + 14;
        companies.forEach((comp, i) => {
            const col = CMP_COLORS[i] || C.s400;
            const { value, valueColor } = getValue(comp);
            doc.setFillColor(...col);
            doc.circle(PAGE.mx + 10, rowY - 1, 1.5, 'F');
            doc.setFontSize(8.5);
            doc.setFont('helvetica', 'normal');
            doc.setTextColor(...C.s800);
            doc.text(comp.name.length > 30 ? comp.name.substring(0, 30) + '…' : comp.name, PAGE.mx + 15, rowY);
            doc.setFont('helvetica', 'bold');
            doc.setTextColor(...(valueColor || C.s800));
            doc.text(String(value), PAGE.cr - 6, rowY, { align: 'right' });
            rowY += rowH;
        });
        return yPos + boxH + 6;
    };

    y = drawKPIBlock('Ø Score (Gesamtnote)', y, (comp) => {
        const s = comp.score;
        return {
            value: s != null ? `${fmtNum(s, 2)}${comp.scoreN != null ? ` (n = ${fmtInt(comp.scoreN)})` : ''}` : '–',
            valueColor: s > 3 ? C.emerald500 : s >= 2 ? C.s800 : s != null ? C.rose500 : C.s300,
        };
    });

    y = drawKPIBlock('Trend', y, (comp) => {
        if (!comp.trend) return { value: '–', valueColor: C.s300 };
        const tv = parseFloat(comp.trend.avgDelta);
        return {
            value: `${tv > 0 ? '+' : ''}${comp.trend.avgDelta}`,
            valueColor: tv > 0.05 ? C.emerald500 : tv < -0.05 ? C.rose500 : C.s500,
        };
    });

    y = drawKPIBlock('Most Critical', y, (comp) => {
        if (!comp.mostCritical) return { value: '–', valueColor: C.s300 };
        return { value: `${comp.mostCritical.topicName} (${comp.mostCritical.score})`, valueColor: C.rose500 };
    });

    drawKPIBlock('Negative Topic', y, (comp) => {
        const nt = comp.negativeTopic;
        if (!nt) return { value: '–', valueColor: C.s300 };
        const lbl = (nt.topic_label || nt.topic_text || nt.topic || '–');
        return { value: lbl.length > 30 ? lbl.substring(0, 30) + '…' : lbl, valueColor: C.orange500 };
    });

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 3 — category comparison (radar + bar)
    // ═════════════════════════════════════════════════════════════════════
    if (radarImg || barImg) {
        doc.addPage();
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        let y3 = _cmpAddTitle(doc, 'Kategorievergleich', PAGE.my + 5, 'Bewertung der Firmen in den einzelnen Kategorien');

        if (radarImg) {
            doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text('Radar-Ansicht', PAGE.mx + 8, y3);
            y3 += 4;
            y3 = _cmpAddChart(doc, radarImg, y3, barImg ? 110 : PAGE.h - PAGE.my - 10 - y3);
            y3 += 4;
        }
        if (barImg) {
            doc.setFontSize(10); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text('Balken-Ansicht', PAGE.mx + 8, y3);
            y3 += 4;
            _cmpAddChart(doc, barImg, y3, PAGE.h - PAGE.my - 10 - y3);
        }
    }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 4 — timeline
    // ═════════════════════════════════════════════════════════════════════
    if (timelineImg) {
        doc.addPage();
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        const y4 = _cmpAddTitle(doc, 'Bewertungsverlauf', PAGE.my + 5, 'Historische Entwicklung der Bewertungen im Vergleich');
        _cmpAddChart(doc, timelineImg, y4, PAGE.h - PAGE.my - 10 - y4);
    }

    // ═════════════════════════════════════════════════════════════════════
    // PAGE 5+ — detail table
    // ═════════════════════════════════════════════════════════════════════
    if (categoryData.length > 0) {
        doc.addPage();
        doc.setFillColor(...C.s100);
        doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
        let yT = _cmpAddTitle(doc, 'Detailvergleich', PAGE.my + 5, 'Bewertungen nach Kategorien mit Differenzanalyse');

        const catColW = 55;
        const compColW = companies.length >= 3 ? 30 : 38;
        const rowH = 7;

        const drawTableHeader = (atY) => {
            doc.setFillColor(...C.s800);
            doc.roundedRect(PAGE.mx, atY - 5, PAGE.cw, rowH + 3, 1, 1, 'F');
            doc.setFontSize(7.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s0);
            doc.text('Kategorie', PAGE.mx + 4, atY);
            companies.forEach((comp, i) => {
                doc.text(
                    comp.name.length > 12 ? comp.name.substring(0, 12) + '…' : comp.name,
                    PAGE.mx + catColW + i * compColW, atY
                );
            });
            doc.text('Diff.', PAGE.cr - 4, atY, { align: 'right' });
            return atY + rowH + 2;
        };

        yT = drawTableHeader(yT);

        categoryData.forEach((row, idx) => {
            if (yT > PAGE.h - PAGE.my - 10) {
                doc.addPage();
                doc.setFillColor(...C.s100);
                doc.rect(0, 0, PAGE.w, PAGE.h, 'F');
                yT = PAGE.my;
                yT = drawTableHeader(yT);
            }
            doc.setFillColor(...(idx % 2 === 0 ? C.s0 : C.s50));
            doc.rect(PAGE.mx, yT - 4.5, PAGE.cw, rowH, 'F');

            doc.setFontSize(7.5); doc.setFont('helvetica', 'bold'); doc.setTextColor(...C.s800);
            doc.text(row.category.length > 28 ? row.category.substring(0, 28) + '…' : row.category, PAGE.mx + 4, yT);

            const values = companies.map(comp => {
                const v = row[comp.name];
                return v != null ? Number(v) : null;
            });
            const valid = values.filter(v => v != null);
            const maxVal = valid.length ? Math.max(...valid) : null;
            const minVal = valid.length ? Math.min(...valid) : null;

            companies.forEach((comp, i) => {
                const x = PAGE.mx + catColW + i * compColW;
                const val = values[i];
                if (val == null) {
                    doc.setFont('helvetica', 'normal'); doc.setTextColor(...C.s300);
                    doc.text('–', x, yT);
                } else {
                    const isBest  = valid.length >= 2 && val === maxVal;
                    const isWorst = valid.length >= 2 && val === minVal && maxVal !== minVal;
                    doc.setFont('helvetica', 'bold');
                    doc.setTextColor(...(isBest ? C.emerald500 : isWorst ? C.rose500 : C.s800));
                    doc.text(val.toFixed(2), x, yT);
                }
            });

            if (valid.length >= 2) {
                doc.setFont('helvetica', 'normal'); doc.setTextColor(...C.s500);
                doc.text(`±${(maxVal - minVal).toFixed(2)}`, PAGE.cr - 4, yT, { align: 'right' });
            }
            yT += rowH;
        });

        doc.setDrawColor(...C.s200); doc.setLineWidth(0.3);
        doc.line(PAGE.mx, yT - 3, PAGE.cr, yT - 3);
    }

    // ═════════════════════════════════════════════════════════════════════
    // Footers on every page except cover
    // ═════════════════════════════════════════════════════════════════════
    const totalPages = doc.internal.pages.length - 1;
    for (let i = 2; i <= totalPages; i++) {
        doc.setPage(i);
        _cmpAddFooter(doc, i, totalPages, titleLabel);
    }

    const fileName = `Firmenvergleich_${companyNames.map(n => n.replace(/\s+/g, '_')).join('_vs_')}_${new Date().toISOString().split('T')[0]}.pdf`;
    doc.save(fileName);
    console.log(`✅ Firmenvergleich PDF gespeichert: ${fileName} (${totalPages} Seiten)`);
};
