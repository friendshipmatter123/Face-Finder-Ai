// ============================================
// FaceFind Frontend - Event Detail Page
// ============================================
import { useState, useEffect, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  FiUpload, FiArrowLeft, FiImage, FiUsers,
  FiCopy, FiCheck, FiTrash2, FiRefreshCw
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import {
  getEvent, uploadPhotos, listEventPhotos,
  getProcessingStatus, deletePhoto, retryProcessing
} from '../services/api';
import PhotoGrid from '../components/PhotoGrid';

export default function EventDetailPage() {
  const { eventId } = useParams();
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  const [event, setEvent] = useState(null);
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processingStatus, setProcessingStatus] = useState(null);
  const [copied, setCopied] = useState(false);
  const [retrying, setRetrying] = useState(false);

  useEffect(() => {
    fetchData();
  }, [eventId]);

  // Poll processing status
  useEffect(() => {
    if (processingStatus?.status === 'processing') {
      const interval = setInterval(fetchProcessingStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [processingStatus?.status]);

  const fetchData = async () => {
    try {
      const [eventRes, photosRes] = await Promise.all([
        getEvent(eventId),
        listEventPhotos(eventId, 0, 200),
      ]);
      setEvent(eventRes.data);
      setPhotos(photosRes.data);
      fetchProcessingStatus();
    } catch {
      toast.error('Failed to load event');
      navigate('/admin/dashboard');
    } finally {
      setLoading(false);
    }
  };

  const fetchProcessingStatus = async () => {
    try {
      const res = await getProcessingStatus(eventId);
      setProcessingStatus(res.data);
    } catch {}
  };

  const handleUpload = async (e) => {
    const files = Array.from(e.target.files);
    if (files.length === 0) return;

    if (files.length > 500) {
      toast.error('Max 500 files per upload. Please upload in batches.');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      await uploadPhotos(eventId, files, (progressEvent) => {
        const pct = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        setUploadProgress(pct);
      });

      toast.success(`${files.length} photos uploaded! Processing faces...`);
      fetchData();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Upload failed');
    } finally {
      setUploading(false);
      setUploadProgress(0);
      if (fileInputRef.current) fileInputRef.current.value = '';
    }
  };

  const copyCode = () => {
    if (event) {
      navigator.clipboard.writeText(event.event_code);
      setCopied(true);
      toast.success('Event code copied!');
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleRetryProcessing = async () => {
    setRetrying(true);
    try {
      await retryProcessing(eventId);
      toast.success('Photo processing restarted');
      fetchProcessingStatus();
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Could not restart processing');
    } finally {
      setRetrying(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  if (!event) return null;

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Back button */}
      <button
        onClick={() => navigate('/admin/dashboard')}
        className="flex items-center gap-2 text-slate-400 hover:text-white mb-6 transition-colors"
      >
        <FiArrowLeft /> Back to Dashboard
      </button>

      {/* Event Header */}
      <div className="card mb-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-2xl font-bold mb-1">{event.name}</h1>
            <p className="text-slate-400 text-sm">{event.description || 'No description'}</p>
          </div>

          <div className="flex items-center gap-3">
            {/* Event Code */}
            <button
              onClick={copyCode}
              className="flex items-center gap-2 bg-slate-700 px-4 py-2 rounded-xl
                        font-mono text-lg tracking-wider hover:bg-slate-600 transition-colors"
            >
              {copied ? <FiCheck className="text-green-400" /> : <FiCopy />}
              {event.event_code}
            </button>
          </div>
        </div>

        {/* Stats */}
        <div className="flex flex-wrap gap-6 mt-4 pt-4 border-t border-slate-700">
          <div className="flex items-center gap-2">
            <FiImage className="text-primary-400" />
            <span className="text-sm">{event.total_photos} photos</span>
          </div>
          <div className="flex items-center gap-2">
            <FiUsers className="text-accent-400" />
            <span className="text-sm">{event.total_faces} faces detected</span>
          </div>
          <span className={`px-3 py-1 rounded-full text-xs font-medium
            ${processingStatus?.status === 'completed' ? 'bg-green-500/20 text-green-400'
              : processingStatus?.status === 'processing' ? 'bg-amber-500/20 text-amber-400'
              : 'bg-slate-600/50 text-slate-400'}`}>
            {processingStatus?.status || event.processing_status}
            {processingStatus?.status === 'processing' && ` (${processingStatus.progress_percent}%)`}
          </span>
          {processingStatus?.status === 'processing' && (
            <button
              onClick={handleRetryProcessing}
              disabled={retrying}
              className="flex items-center gap-1 text-xs text-primary-300 hover:text-white disabled:opacity-50"
            >
              <FiRefreshCw size={13} className={retrying ? 'animate-spin' : ''} />
              Restart processing
            </button>
          )}
        </div>

        {/* Processing progress bar */}
        {processingStatus?.status === 'processing' && (
          <div className="mt-4">
            <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-primary-500 to-accent-500 rounded-full transition-all duration-500"
                style={{ width: `${processingStatus.progress_percent}%` }}
              />
            </div>
            <p className="text-xs text-slate-400 mt-1">
              Processing: {processingStatus.processed_photos} / {processingStatus.total_photos} photos
            </p>
          </div>
        )}
      </div>

      {/* Upload Section */}
      <div className="card mb-8">
        <h2 className="text-lg font-semibold mb-4">Upload Photos</h2>

        <div
          className="border-2 border-dashed border-slate-600 rounded-xl p-8 text-center
                     hover:border-primary-500 transition-colors cursor-pointer"
          onClick={() => !uploading && fileInputRef.current?.click()}
        >
          {uploading ? (
            <div>
              <div className="w-12 h-12 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin mx-auto mb-3" />
              <p className="text-slate-300">Uploading... {uploadProgress}%</p>
              <div className="w-48 h-2 bg-slate-700 rounded-full mx-auto mt-2">
                <div
                  className="h-full bg-primary-500 rounded-full transition-all"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          ) : (
            <>
              <FiUpload size={32} className="text-slate-500 mx-auto mb-3" />
              <p className="text-slate-300 mb-1">Click to upload photos or drag & drop</p>
              <p className="text-xs text-slate-500">JPG, PNG, WebP • Max 20MB each • Up to 500 per batch</p>
            </>
          )}
        </div>

        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept="image/*"
          onChange={handleUpload}
          className="hidden"
        />
      </div>

      {/* Photos Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold">Event Photos ({photos.length})</h2>
          <button
            onClick={fetchData}
            className="flex items-center gap-1 text-sm text-slate-400 hover:text-white transition-colors"
          >
            <FiRefreshCw size={14} /> Refresh
          </button>
        </div>

        {photos.length === 0 ? (
          <div className="card text-center py-12">
            <FiImage size={48} className="text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400">No photos uploaded yet. Start by uploading photos above!</p>
          </div>
        ) : (
          <PhotoGrid photos={photos} selectable={false} />
        )}
      </div>
    </div>
  );
}
