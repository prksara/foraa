import { useState, useCallback, useRef, useEffect } from "react";
import {
  FileText,
  Upload,
  Plus,
  Sparkles,
  Check,
  X,
  ArrowLeft,
  Trash2,
  Download,
  AlertCircle
} from "lucide-react";
import Card from "../components/Card";
import EmptyState from "../components/EmptyState";
import Badge from "../components/Badge";
import Button from "../components/Button";
import AskForraa from "../components/AskForraa";
import * as api from "../api/client";

function Reports() {
  const fileInputRef = useRef(null);
  const [reports, setReports] = useState([]);
  const [showUpload, setShowUpload] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [selectedReportId, setSelectedReportId] = useState(null);
  const [reportDetails, setReportDetails] = useState(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  
  const loadReports = useCallback(async () => {
    try {
      const data = await api.fetchReports();
      setReports(data);
    } catch (err) {
      console.error("Failed to load reports", err);
    }
  }, []);

  useEffect(() => {
    loadReports();
    // Poll for updates if any are processing
    const interval = setInterval(() => {
      setReports((current) => {
        if (current.some(r => r.status === 'uploaded' || r.status === 'processing')) {
          loadReports();
        }
        return current;
      });
    }, 5000);
    return () => clearInterval(interval);
  }, [loadReports]);

  const handleUpload = async (files) => {
    if (!files.length) return;
    setUploading(true);
    try {
      await api.uploadReport(files);
      setShowUpload(false);
      await loadReports();
    } catch (err) {
      alert("Failed to upload report: " + err.message);
    } finally {
      setUploading(false);
    }
  };

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

  const handleDelete = async (reportId) => {
    if (!confirm("Are you sure you want to delete this report?")) return;
    try {
      await api.deleteReport(reportId);
      if (selectedReportId === reportId) {
         setSelectedReportId(null);
         setReportDetails(null);
      }
      await loadReports();
    } catch (err) {
      alert("Failed to delete report.");
    }
  };

  const loadReportDetails = async (id) => {
    setSelectedReportId(id);
    setLoadingDetails(true);
    try {
      const details = await api.fetchReportDetails(id);
      setReportDetails(details);
    } catch (err) {
      alert("Failed to load report details.");
      setSelectedReportId(null);
    } finally {
      setLoadingDetails(false);
    }
  };

  const handleConfirmExtraction = async (extId) => {
    try {
      await api.confirmExtraction(selectedReportId, extId);
      // Update local state
      setReportDetails(prev => ({
         ...prev,
         extractions: prev.extractions.map(e => e.id === extId ? {...e, status: 'confirmed'} : e)
      }));
      loadReports(); // update main list status
    } catch (err) {
      alert("Failed to confirm: " + err.message);
    }
  };

  const handleRejectExtraction = async (extId) => {
    try {
      await api.rejectExtraction(selectedReportId, extId);
      setReportDetails(prev => ({
         ...prev,
         extractions: prev.extractions.map(e => e.id === extId ? {...e, status: 'rejected'} : e)
      }));
      loadReports(); // update main list status
    } catch (err) {
      alert("Failed to reject: " + err.message);
    }
  };

  // Detailed View
  if (selectedReportId) {
    return (
       <div className="page">
          <div className="page-header" style={{flexDirection: 'row', alignItems: 'center', gap: '1rem', justifyContent: 'flex-start'}}>
            <Button variant="ghost" onClick={() => setSelectedReportId(null)} icon={<ArrowLeft size={16}/>}>Back</Button>
            <div>
              <h1 className="page-header__title">{reportDetails?.filename || "Loading..."}</h1>
              <p className="page-header__desc">Review extracted health insights.</p>
            </div>
          </div>
          
          {loadingDetails ? (
            <p>Loading details...</p>
          ) : reportDetails ? (
            <div style={{display: 'flex', flexDirection: 'column', gap: '1.5rem'}}>
               <Card padding="lg">
                 <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start'}}>
                    <div>
                      <h3 style={{marginTop: 0}}>Report Summary</h3>
                      <p style={{whiteSpace: 'pre-wrap', lineHeight: '1.5', color: 'var(--text-secondary)'}}>{reportDetails.summary}</p>
                    </div>
                    <div style={{display: 'flex', gap: '0.5rem'}}>
                      {reportDetails.download_url && (
                        <a href={reportDetails.download_url} target="_blank" rel="noreferrer" style={{textDecoration: 'none'}}>
                           <Button variant="outline" icon={<Download size={14}/>}>Download</Button>
                        </a>
                      )}
                      <Button variant="ghost" onClick={() => handleDelete(reportDetails.id)} icon={<Trash2 size={14}/>}>Delete</Button>
                    </div>
                 </div>
               </Card>
               
               <div>
                  <h3>Extracted Findings</h3>
                  {reportDetails.extractions.length === 0 ? (
                     <p>No specific structured data was extracted from this report.</p>
                  ) : (
                     <div style={{display: 'flex', flexDirection: 'column', gap: '1rem'}}>
                        {reportDetails.extractions.map(ext => (
                           <Card key={ext.id} padding="md">
                              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                                 <div>
                                    <div style={{display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem'}}>
                                       <Badge variant="primary" style={{textTransform: 'capitalize'}}>{ext.entity_type}</Badge>
                                       {ext.status === 'pending_review' && <Badge variant="warning">Needs Review</Badge>}
                                       {ext.status === 'confirmed' && <Badge variant="success">Confirmed</Badge>}
                                       {ext.status === 'rejected' && <Badge variant="danger">Rejected</Badge>}
                                    </div>
                                    <div style={{fontFamily: 'monospace', fontSize: '0.9rem', backgroundColor: 'var(--bg-secondary)', padding: '0.5rem', borderRadius: '4px'}}>
                                       {JSON.stringify(ext.data, null, 2)}
                                    </div>
                                    {ext.source_text && (
                                       <p style={{fontSize: '0.85rem', color: 'var(--text-secondary)', marginTop: '0.5rem'}}>
                                          <AlertCircle size={12} style={{display: 'inline', marginRight: '4px'}}/>
                                          Source: "{ext.source_text}"
                                       </p>
                                    )}
                                 </div>
                                 {ext.status === 'pending_review' && (
                                    <div style={{display: 'flex', flexDirection: 'column', gap: '0.5rem'}}>
                                       <Button variant="primary" icon={<Check size={14}/>} onClick={() => handleConfirmExtraction(ext.id)}>Confirm</Button>
                                       <Button variant="outline" icon={<X size={14}/>} onClick={() => handleRejectExtraction(ext.id)}>Reject</Button>
                                    </div>
                                 )}
                              </div>
                           </Card>
                        ))}
                     </div>
                  )}
               </div>

               <div className="page-section">
                 <AskForraa 
                    placeholder={`Ask Forraa about ${reportDetails.filename}...`} 
                    activeReportId={reportDetails.id}
                 />
               </div>
            </div>
          ) : (
             <p>Report not found.</p>
          )}
       </div>
    );
  }

  // List View
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
          <strong>{uploading ? "Uploading..." : "Drop files here or click to upload"}</strong>
          <p>PDF, lab reports, prescriptions, medical documents</p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.jpg,.jpeg,.png"
            onChange={handleFileSelect}
            style={{ display: "none" }}
            disabled={uploading}
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
                <strong>{report.filename}</strong>
                <span>
                  {new Date(report.created_at).toLocaleDateString()}
                </span>
              </div>
              <Badge
                variant={
                  report.status === "processed" ? "success" 
                  : report.status === "needs_review" ? "warning"
                  : report.status === "failed" ? "danger"
                  : "pending"
                }
              >
                {report.status.replace("_", " ")}
              </Badge>
              <div className="report-card__actions">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => loadReportDetails(report.id)}
                >
                  View
                </Button>
                <Button variant="ghost" size="sm" onClick={() => handleDelete(report.id)} icon={<Trash2 size={14}/>}>Delete</Button>
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