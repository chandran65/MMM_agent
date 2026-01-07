import React, { useState } from 'react';
import axios from 'axios';
import { Upload, FileText, CheckCircle, Play, Loader, AlertCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

const DataStudio = () => {
    const navigate = useNavigate();
    const [file, setFile] = useState(null);
    const [uploading, setUploading] = useState(false);
    const [uploadStatus, setUploadStatus] = useState(null); // 'success', 'error'
    const [fileId, setFileId] = useState(null);
    const [running, setRunning] = useState(false);
    const [pipelineId, setPipelineId] = useState(null);
    const [error, setError] = useState(null);

    const handleFileChange = (e) => {
        if (e.target.files[0]) {
            setFile(e.target.files[0]);
            setUploadStatus(null);
            setError(null);
        }
    };

    const handleUpload = async () => {
        if (!file) return;

        setUploading(true);
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await axios.post('http://localhost:8080/api/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });

            setFileId(response.data.file_id);
            setUploadStatus('success');
            setUploading(false);
        } catch (err) {
            setError('Upload failed: ' + (err.response?.data?.error || err.message));
            setUploading(false);
            setUploadStatus('error');
        }
    };

    const runModel = async () => {
        if (!fileId) return;
        setRunning(true);

        try {
            const response = await axios.post('http://localhost:8080/api/pipeline/run', {
                file_id: fileId,
                config: { auto_approve: true } // Auto approve for demo smoothness
            });

            const pid = response.data.pipeline_id;
            setPipelineId(pid);

            // Poll for status
            pollStatus(pid);

        } catch (err) {
            setError('Pipeline start failed: ' + (err.response?.data?.error || err.message));
            setRunning(false);
        }
    };

    const pollStatus = (pid) => {
        const interval = setInterval(async () => {
            try {
                const res = await axios.get(`http://localhost:8080/api/pipeline/${pid}/status`);
                const status = res.data.status;

                if (status === 'completed') {
                    clearInterval(interval);
                    setRunning(false);
                    // Navigate to dashboard or show success
                    alert("Model run completed successfully! Check the Dashboard.");
                    navigate('/');
                } else if (status === 'failed') {
                    clearInterval(interval);
                    setRunning(false);
                    setError('Pipeline execution failed: ' + res.data.error);
                }
                // else: still running
            } catch (err) {
                clearInterval(interval);
                setRunning(false);
                setError('Status check failed');
            }
        }, 2000);
    };

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '2rem', maxWidth: '800px', margin: '0 auto' }}>

            {/* Upload Section */}
            <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)', textAlign: 'center', border: '2px dashed var(--border)' }}>
                <div style={{ width: 64, height: 64, background: 'var(--bg-hover)', borderRadius: '50%', margin: '0 auto 1.5rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                    {uploadStatus === 'success' ? <CheckCircle size={32} color="var(--success)" /> : <Upload size={32} color="var(--accent)" />}
                </div>

                <h2 style={{ marginBottom: '0.5rem' }}>
                    {uploadStatus === 'success' ? 'File Uploaded Successfully' : 'Upload Sales Data'}
                </h2>

                {!uploadStatus && (
                    <>
                        <input
                            type="file"
                            accept=".csv"
                            onChange={handleFileChange}
                            style={{ display: 'none' }}
                            id="file-upload"
                        />
                        <label htmlFor="file-upload">
                            <p style={{ color: 'var(--text-secondary)', marginBottom: '1.5rem', cursor: 'pointer' }}>
                                {file ? file.name : "Click to select CSV file"}
                            </p>
                        </label>

                        <button
                            onClick={handleUpload}
                            disabled={!file || uploading}
                            style={{
                                background: file ? 'var(--accent)' : 'var(--bg-hover)',
                                color: 'white',
                                border: 'none',
                                padding: '0.75rem 2rem',
                                borderRadius: 'var(--radius-md)',
                                fontWeight: 500,
                                cursor: file ? 'pointer' : 'not-allowed',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem',
                                margin: '0 auto'
                            }}
                        >
                            {uploading ? <Loader className="animate-spin" size={20} /> : <Upload size={20} />}
                            {uploading ? 'Uploading...' : 'Upload File'}
                        </button>
                    </>
                )}

                {uploadStatus === 'success' && (
                    <div style={{ marginTop: '1rem', color: 'var(--success)' }}>
                        Ready for modeling. ID: {fileId.substring(0, 8)}...
                    </div>
                )}

                {error && (
                    <div style={{ marginTop: '1rem', color: 'var(--danger)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem' }}>
                        <AlertCircle size={18} />
                        {error}
                    </div>
                )}
            </div>

            {/* Model Configuration / Run Section */}
            {uploadStatus === 'success' && (
                <div className="glass-panel" style={{ padding: '2rem', borderRadius: 'var(--radius-lg)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
                        <div>
                            <h3 style={{ marginBottom: '0.5rem' }}>Run MMX Model</h3>
                            <p style={{ color: 'var(--text-secondary)' }}>
                                Configure parameters and start the optimization pipeline.
                            </p>
                        </div>
                        <button
                            onClick={runModel}
                            disabled={running}
                            style={{
                                background: running ? 'var(--bg-hover)' : 'var(--success)',
                                color: 'white',
                                border: 'none',
                                padding: '0.75rem 2rem',
                                borderRadius: 'var(--radius-md)',
                                fontWeight: 600,
                                cursor: running ? 'wait' : 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '0.5rem'
                            }}
                        >
                            {running ? <Loader className="animate-spin" size={20} /> : <Play size={20} />}
                            {running ? 'Processing...' : 'Run Pipeline'}
                        </button>
                    </div>

                    {running && (
                        <div style={{ background: 'var(--bg-primary)', padding: '1rem', borderRadius: 'var(--radius-md)', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                                <span>Pipeline Status</span>
                                <span style={{ color: 'var(--accent)' }}>Running</span>
                            </div>
                            <div style={{ width: '100%', height: '6px', background: 'var(--bg-hover)', borderRadius: '3px', overflow: 'hidden' }}>
                                <div className="progress-bar" style={{ width: '60%', height: '100%', background: 'var(--accent)', transition: 'width 0.5s ease' }}></div>
                            </div>
                            <p style={{ marginTop: '0.5rem', fontSize: '0.8rem' }}>
                                Initializing agents, checking data quality, running Bayesian optimization...
                            </p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};

export default DataStudio;
