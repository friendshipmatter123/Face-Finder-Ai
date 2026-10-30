// ============================================
// FaceFind Frontend - Home / Search Page
// ============================================
import { useState, useRef } from 'react';
import { FiSearch, FiCamera, FiUpload, FiDownload, FiPackage, FiShield } from 'react-icons/fi';
import toast from 'react-hot-toast';
import WebcamCapture from '../components/WebcamCapture';
import MultiAngleRegistration from '../components/MultiAngleRegistration';
import PhotoGrid from '../components/PhotoGrid';
import {
  searchFace, searchFaceWithRegistration, getEventByCode, downloadZip, downloadPhoto,
  deleteFaceRegistration,
} from '../services/api';

export default function HomePage() {
  const [eventCode, setEventCode] = useState('');
  const [eventInfo, setEventInfo] = useState(null);
  const [showWebcam, setShowWebcam] = useState(false);
  const [faceFile, setFaceFile] = useState(null);
  const [facePreview, setFacePreview] = useState(null);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const [selectedPhotos, setSelectedPhotos] = useState([]);
  const [downloading, setDownloading] = useState(false);
  const [showRegistration, setShowRegistration] = useState(false);
  const [registration, setRegistration] = useState(null);
  const fileInputRef = useRef(null);

  // Step 1: Verify event code
  const handleEventCode = async () => {
    if (!eventCode.trim()) {
      toast.error('Please enter an event code');
      return;
    }
    try {
      const res = await getEventByCode(eventCode.trim().toUpperCase());
      setEventInfo(res.data);
      toast.success(`Event found: ${res.data.name}`);
    } catch (err) {
      toast.error('Event not found. Check the code and try again.');
      setEventInfo(null);
    }
  };

  // Step 2: Handle face image selection
  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFaceFile(file);
      setFacePreview(URL.createObjectURL(file));
      setResults(null);
    }
  };

  const handleWebcamCapture = (file) => {
    setFaceFile(file);
    setFacePreview(URL.createObjectURL(file));
    setShowWebcam(false);
    setResults(null);
  };

  // Step 3: Search
  const handleSearch = async () => {
    if (!faceFile && !registration) {
      toast.error('Please upload or capture your face photo first');
      return;
    }
    if (!eventInfo) {
      toast.error('Please enter a valid event code first');
      return;
    }

    setSearching(true);
    setResults(null);

    try {
      const res = registration
        ? await searchFaceWithRegistration(eventInfo.event_code, registration.registration_id)
        : await searchFace(eventInfo.event_code, faceFile);
      setResults(res.data);

      if (res.data.total_matches === 0) {
        toast('No matching photos found. Try a different photo or adjust tolerance.', {
          icon: '😔',
        });
      } else {
        toast.success(`Found ${res.data.total_matches} photos in ${res.data.search_time_seconds}s!`);
      }
    } catch (err) {
      const msg = err.response?.data?.detail || 'Search failed. Please try again.';
      toast.error(msg);
    } finally {
      setSearching(false);
    }
  };

  const handleRegistration = (data) => {
    setRegistration(data);
    setFaceFile(null);
    setFacePreview(null);
    setResults(null);
  };

  const handleDeleteRegistration = async () => {
    if (!registration) return;
    try {
      await deleteFaceRegistration(registration.registration_id, registration.deletion_token);
      setRegistration(null);
      setResults(null);
      toast.success('Your stored facial data was deleted.');
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not delete facial data.');
    }
  };

  // Step 4: Download
  const handleDownloadSelected = async () => {
    if (selectedPhotos.length === 0) {
      toast.error('Please select photos to download');
      return;
    }
    setDownloading(true);
    try {
      if (selectedPhotos.length === 1) {
        const res = await downloadPhoto(selectedPhotos[0]);
        const url = URL.createObjectURL(new Blob([res.data]));
        const a = document.createElement('a');
        a.href = url;
        a.download = 'FaceFind_Photo.jpg';
        a.click();
        URL.revokeObjectURL(url);
      } else {
        const res = await downloadZip(selectedPhotos);
        const url = URL.createObjectURL(new Blob([res.data]));
        const a = document.createElement('a');
        a.href = url;
        a.download = 'FaceFind_Photos.zip';
        a.click();
        URL.revokeObjectURL(url);
      }
      toast.success('Download started!');
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  const handleDownloadAll = async () => {
    if (!results || results.results.length === 0) return;
    setDownloading(true);
    try {
      const allIds = results.results.map((r) => r.photo_id);
      const res = await downloadZip(allIds);
      const url = URL.createObjectURL(new Blob([res.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = 'FaceFind_All_Photos.zip';
      a.click();
      URL.revokeObjectURL(url);
      toast.success('Downloading all photos!');
    } catch {
      toast.error('Download failed');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <section className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-primary-900/20 via-transparent to-accent-900/20" />
        <div className="max-w-4xl mx-auto px-4 py-12 sm:py-16 text-center relative">
          <h1 className="text-3xl sm:text-4xl lg:text-6xl font-extrabold mb-4">
            <span className="gradient-text">Find Your Photos</span>
            <br />
            <span className="text-slate-300 text-2xl sm:text-3xl lg:text-4xl">with AI Face Search</span>
          </h1>
          <p className="text-base sm:text-lg text-slate-400 max-w-2xl mx-auto mb-8 px-4">
            Upload your selfie or scan your face — our AI will instantly find all photos
            where you appear from thousands of event photos.
          </p>
        </div>
      </section>

      {/* Main Search Flow */}
      <section className="max-w-4xl mx-auto px-4 pb-16 space-y-8">
        {/* Step 1: Event Code */}
        <div className="card animate-fade-in">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-400 font-bold text-sm">
              1
            </div>
            <h2 className="text-lg font-semibold">Enter Event Code</h2>
          </div>
          <div className="flex gap-3">
            <input
              type="text"
              value={eventCode}
              onChange={(e) => setEventCode(e.target.value.toUpperCase())}
              placeholder="e.g., ABC12345"
              className="input-field uppercase tracking-widest text-center text-lg font-mono"
              onKeyDown={(e) => e.key === 'Enter' && handleEventCode()}
              maxLength={10}
            />
            <button onClick={handleEventCode} className="btn-primary whitespace-nowrap">
              <FiSearch className="inline mr-1" /> Verify
            </button>
          </div>
          {eventInfo && (
            <div className="mt-3 p-3 bg-green-500/10 border border-green-500/30 rounded-xl text-green-400 text-sm">
              ✅ <strong>{eventInfo.name}</strong> — {eventInfo.total_photos} photos, {eventInfo.total_faces} faces detected
            </div>
          )}
        </div>

        {/* Step 2: Face Upload */}
        {eventInfo && (
          <div className="card animate-fade-in">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-8 h-8 rounded-full bg-primary-500/20 flex items-center justify-center text-primary-400 font-bold text-sm">
                2
              </div>
              <h2 className="text-lg font-semibold">Scan Your Face</h2>
            </div>

            <div className="flex flex-col sm:flex-row gap-4 items-center">
              {/* Face preview */}
              {facePreview && (
                <div className="w-32 h-32 rounded-xl overflow-hidden border-2 border-primary-500 flex-shrink-0">
                  <img src={facePreview} alt="Your face" className="w-full h-full object-cover" />
                </div>
              )}

              <div className="flex gap-3 flex-wrap">
                <button onClick={() => setShowRegistration(true)} className="btn-primary flex items-center gap-2">
                  <FiShield size={18} /> Register face angles
                </button>
                <button
                  onClick={() => setShowWebcam(true)}
                  className="btn-accent flex items-center gap-2"
                >
                  <FiCamera size={18} /> Use Camera
                </button>
                <button
                  onClick={() => fileInputRef.current.click()}
                  className="btn-secondary flex items-center gap-2"
                >
                  <FiUpload size={18} /> Upload Photo
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>
            </div>
            {registration && (
              <div className="mt-4 p-3 bg-green-500/10 border border-green-500/30 rounded-xl flex flex-wrap items-center justify-between gap-3 text-sm">
                <span className="text-green-300">Registered angles: {registration.angles.join(', ')}</span>
                <button onClick={handleDeleteRegistration} className="text-red-300 underline">Delete registration data</button>
              </div>
            )}
          </div>
        )}

        {/* Step 3: Search Button */}
        {eventInfo && (faceFile || registration) && (
          <div className="text-center animate-fade-in">
            <button
              onClick={handleSearch}
              disabled={searching}
              className="btn-primary !py-4 !px-12 text-lg flex items-center gap-3 mx-auto"
            >
              {searching ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching faces...
                </>
              ) : (
                <>
                  <FiSearch size={22} /> Find My Photos
                </>
              )}
            </button>
          </div>
        )}

        {/* Results */}
        {results && (
          <div className="animate-fade-in">
            <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
              <div>
                <h2 className="text-2xl font-bold">
                  {results.total_matches > 0 ? (
                    <span className="gradient-text">
                      {results.total_matches} Photos Found!
                    </span>
                  ) : (
                    'No Matches Found'
                  )}
                </h2>
                <p className="text-sm text-slate-400">
                  Searched in {results.search_time_seconds}s
                </p>
              </div>

              {results.total_matches > 0 && (
                <div className="flex gap-3">
                  <button
                    onClick={handleDownloadSelected}
                    disabled={downloading || selectedPhotos.length === 0}
                    className="btn-secondary !py-2 !px-4 text-sm flex items-center gap-2"
                  >
                    <FiDownload size={14} />
                    Download Selected ({selectedPhotos.length})
                  </button>
                  <button
                    onClick={handleDownloadAll}
                    disabled={downloading}
                    className="btn-primary !py-2 !px-4 text-sm flex items-center gap-2"
                  >
                    <FiPackage size={14} />
                    Download All (ZIP)
                  </button>
                </div>
              )}
            </div>

            {results.total_matches > 0 && (
              <PhotoGrid
                photos={results.results}
                selectable={true}
                onSelectionChange={setSelectedPhotos}
              />
            )}
          </div>
        )}
      </section>

      {/* Webcam modal */}
      {showRegistration && (
        <MultiAngleRegistration onRegistered={handleRegistration} onClose={() => setShowRegistration(false)} />
      )}
      {showWebcam && (
        <WebcamCapture
          onCapture={handleWebcamCapture}
          onClose={() => setShowWebcam(false)}
        />
      )}
    </div>
  );
}
