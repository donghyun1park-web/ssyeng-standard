/**
 * PdfViewerPage — 인앱 PDF 뷰어 (pdfjs-dist).
 * ?url= 로 문서를, ?page= 로 시작 페이지를 받는다. 컨테이너 폭에 맞춰
 * 자동 스케일하며 확대/축소·페이지 이동을 지원한다.
 */
import { useEffect, useRef, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import * as pdfjsLib from 'pdfjs-dist/build/pdf.mjs';
import pdfjsWorker from 'pdfjs-dist/build/pdf.worker.min.mjs?url';
import { readAdminToken } from '../lib/storage';

pdfjsLib.GlobalWorkerOptions.workerSrc = pdfjsWorker;

export default function PdfViewerPage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const url = searchParams.get('url') || '';
  const initialPage = Math.max(1, parseInt(searchParams.get('page') || '1', 10) || 1);
  const title = searchParams.get('title') || 'PDF 보기';

  const canvasRef = useRef(null);
  const pdfRef = useRef(null);
  const renderTaskRef = useRef(null);
  const [numPages, setNumPages] = useState(0);
  const [pageNum, setPageNum] = useState(initialPage);
  const [zoom, setZoom] = useState(1.0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // 문서 로드
  useEffect(() => {
    let cancelled = false;
    setLoading(true); setError('');
    const adminToken = readAdminToken();
    const headers = {};
    if (adminToken && url.includes('/api/rag/')) headers['X-Admin-Token'] = adminToken;

    const task = pdfjsLib.getDocument({ url, httpHeaders: headers, withCredentials: false });
    task.promise.then((pdf) => {
      if (cancelled) return;
      pdfRef.current = pdf;
      setNumPages(pdf.numPages);
      setPageNum((p) => Math.min(Math.max(1, p), pdf.numPages));
      setLoading(false);
    }).catch((err) => {
      if (cancelled) return;
      setError(`PDF를 불러올 수 없습니다: ${err.message || err}`);
      setLoading(false);
    });

    return () => {
      cancelled = true;
      try { task.destroy(); } catch { /* ignore */ }
      if (pdfRef.current) { try { pdfRef.current.destroy(); } catch { /* ignore */ } pdfRef.current = null; }
    };
  }, [url]);

  // 페이지/줌 변경 시 렌더
  useEffect(() => {
    const pdf = pdfRef.current;
    const canvas = canvasRef.current;
    if (!pdf || !canvas || pageNum < 1 || pageNum > pdf.numPages) return;
    let cancelled = false;

    if (renderTaskRef.current) {
      try { renderTaskRef.current.cancel(); } catch { /* ignore */ }
    }

    pdf.getPage(pageNum).then((page) => {
      if (cancelled) return;
      const containerWidth = canvas.parentElement?.clientWidth || window.innerWidth;
      const baseViewport = page.getViewport({ scale: 1 });
      const fitScale = (containerWidth - 16) / baseViewport.width;
      const scale = Math.max(0.5, fitScale * zoom);
      const viewport = page.getViewport({ scale });
      const ctx = canvas.getContext('2d');
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.floor(viewport.width * ratio);
      canvas.height = Math.floor(viewport.height * ratio);
      canvas.style.width = `${Math.floor(viewport.width)}px`;
      canvas.style.height = `${Math.floor(viewport.height)}px`;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      const task = page.render({ canvasContext: ctx, viewport });
      renderTaskRef.current = task;
      task.promise.catch((err) => {
        if (err?.name !== 'RenderingCancelledException') console.error('PDF render error', err);
      });
    });

    return () => { cancelled = true; };
  }, [pageNum, zoom, numPages]);

  const goPrev = () => setPageNum((p) => Math.max(1, p - 1));
  const goNext = () => setPageNum((p) => Math.min(numPages || p, p + 1));
  const zoomIn = () => setZoom((z) => Math.min(4, +(z + 0.25).toFixed(2)));
  const zoomOut = () => setZoom((z) => Math.max(0.5, +(z - 0.25).toFixed(2)));
  const zoomReset = () => setZoom(1.0);

  return (
    <section className="pdf-viewer-page">
      <div className="pdf-viewer-toolbar">
        <button className="btn-ghost" onClick={() => navigate(-1)}>← 닫기</button>
        <strong className="pdf-viewer-title">{title}</strong>
        <a className="btn-outline" href={url} target="_blank" rel="noreferrer" title="외부 브라우저로 열기">↗</a>
      </div>

      {loading ? (
        <div className="loading-row" style={{ padding: 24 }}><span className="spinner" />PDF 불러오는 중...</div>
      ) : error ? (
        <div className="error-box" style={{ margin: 16 }}>{error}</div>
      ) : (
        <>
          <div className="pdf-viewer-canvas-wrap">
            <canvas ref={canvasRef} className="pdf-viewer-canvas" />
          </div>
          <div className="pdf-viewer-controls">
            <button className="btn-outline" onClick={goPrev} disabled={pageNum <= 1}>◀</button>
            <input
              className="pdf-page-input"
              type="number"
              min={1}
              max={numPages}
              value={pageNum}
              onChange={(e) => {
                const v = parseInt(e.target.value, 10);
                if (!Number.isNaN(v)) setPageNum(Math.min(Math.max(1, v), numPages));
              }}
            />
            <span className="pdf-page-total">/ {numPages}</span>
            <button className="btn-outline" onClick={goNext} disabled={pageNum >= numPages}>▶</button>
            <span className="pdf-zoom-controls">
              <button className="btn-outline" onClick={zoomOut} title="축소">−</button>
              <button className="btn-outline" onClick={zoomReset} title="원래 크기">{Math.round(zoom * 100)}%</button>
              <button className="btn-outline" onClick={zoomIn} title="확대">+</button>
            </span>
          </div>
        </>
      )}
    </section>
  );
}
