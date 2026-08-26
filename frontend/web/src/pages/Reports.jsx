import { useState, useCallback, useRef } from "react";
import {
  FileText,
  Upload,
  Plus,
  Sparkles,
} from "lucide-react";
import Card from "../components/Card";
import EmptyState from "../components/EmptyState";
import Badge from "../components/Badge";
import Button from "../components/Button";
import AskForraa from "../components/AskForraa";

function Reports() {
  const fileInputRef = useRef(null);
  const [reports, setReports] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [dragActive, setDragActive] = useState(false);

  /*
   * Clean callbacks for future backend integration.
   *
   * Upload flow:
   *   1. handleUpload(files)  → POST /api/reports/upload
   *   2. Backend extracts text, parses structure
   *   3. handleAnalyze(id)    → POST /api/reports/:id/analyze
   *   4. Backend runs AI analysis, returns insights
   *   5. handleView(id)       → Navigate to report detail
   *   6. handleDelete(id)     → DELETE /api/reports/:id
   */

  const handleUpload = useCallback(async (files) => {
    // Future: const formData = new FormData();
    //         files.forEach(f => formData.append('files', f));
    //         const response = await fetch('/api/reports/upload', {
    //           method: 'POST', body: formData
    //         });
    //         const data = await response.json();
    //         setReports(prev => [...prev, ...data.reports]);
    console.log("[Forraa] Upload files:", files.map((f) => f.name));
  }, []);

  const handleAnalyze = useCallback(async (reportId) => {
    // Future: const result = await fetch(`/api/reports/${reportId}/analyze`, {
    //           method: 'POST'
    //         });
    //         setReports(prev =>
    //           prev.map(r => r.id === reportId
    //             ? { ...r, status: 'analyzed' }
    //             : r
    //           )
    //         );
    console.log("[Forraa] Analyze report:", reportId);
  }, []);

  const handleView = useCallback((reportId) => {
    // Future: navigate to /reports/:id detail view
    console.log("[Forraa] View report:", reportId);
  }, []);

  const handleDelete = useCallback(async (reportId) => {
    // Future: await fetch(`/api/reports/${reportId}`, { method: 'DELETE' });
    //         setReports(prev => prev.filter(r => r.id !== reportId));
    console.log("[Forraa] Delete report:", reportId);
  }, []);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files?.length) {
      handleUpload(Array.from(e.dataTransfer.files));
    }
  };

  const handleFileSelect = (e) => {
    if (e.target.files?.length) {
      handleUpload(Array.from(e.target.files));
      e.target.value = "";
    }
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-header__title">Reports</h1>
          <p className="page-header__desc">
            Understand your health documents with Forraa.
          </p>
        </div>
        <Button
          variant="primary"
          icon={<Plus size={16} />}
          onClick={() => setShowUpload(!showUpload)}
        >
          Upload report
        </Button>
      </div>

      {showUpload && (
        <div
          className={`upload-zone${dragActive ? " upload-zone--active" : ""}`}
          onDragEnter={handleDrag}
          onDragLeave={handleDrag}
          onDragOver={handleDrag}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
        >
          <Upload size={24} />
          <strong>Drop files here or click to upload</strong>
          <p>PDF, lab reports, prescriptions, medical documents</p>
          <input
            ref={fileInputRef}
            type="file"
            multiple
            accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
            onChange={handleFileSelect}
            style={{ display: "none" }}
          />
        </div>
      )}

      {reports.length === 0 ? (
        <Card padding="lg">
          <EmptyState
            icon={<FileText size={24} />}
            title="Your health documents will appear here"
            description="Upload your first report to begin. Forraa can help you understand lab results, prescriptions, and medical documents."
            action={{
              label: "Upload a report",
              onClick: () => setShowUpload(true),
            }}
          />
        </Card>
      ) : (
        <div className="reports-list">
          {reports.map((report) => (
            <div key={report.id} className="report-card">
              <div className="report-card__icon">
                <FileText size={18} />
              </div>
              <div className="report-card__info">
                <strong>{report.name}</strong>
                <span>
                  {report.date} · {report.type}
                </span>
              </div>
              <Badge
                variant={
                  report.status === "analyzed" ? "success" : "pending"
                }
              >
                {report.status === "analyzed" ? "Analyzed" : "Pending"}
              </Badge>
              <div className="report-card__actions">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleView(report.id)}
                >
                  View
                </Button>
                {report.status !== "analyzed" && (
                  <Button
                    variant="ghost"
                    size="sm"
                    icon={<Sparkles size={14} />}
                    onClick={() => handleAnalyze(report.id)}
                  >
                    Analyze
                  </Button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      <div className="page-section">
        <AskForraa placeholder="Ask Forraa to explain a health report..." />
      </div>
    </div>
  );
}

export default Reports;