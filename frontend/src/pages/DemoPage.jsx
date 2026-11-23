import { useEffect, useRef, useState } from 'react';
import toast from 'react-hot-toast';
import { FiCamera, FiLock, FiTrash2, FiUpload, FiSearch, FiDatabase, FiCloud } from 'react-icons/fi';
import { closeDemo, getDemoPhotoUrl, prepareDemo, searchDemoFace } from '../services/api';

export default function DemoPage() {
  const [demoPhotos, setDemoPhotos] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [preparing, setPreparing] = useState(false);
  const [faceFile, setFaceFile] = useState(null);
  const [facePreview, setFacePreview] = useState(null);
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState(null);
  const faceInput = useRef(null);

  useEffect(() => {
    return () => {
      if (sessionId) closeDemo(sessionId).catch(() => {});
    };
  }, [sessionId]);

  const handlePhotos = async (event) => {
    const files = Array.from(event.target.files || []).slice(0, 5);
    if (!files.length) return;
    setPreparing(true);
    setResults(null);
    if (sessionId) {
      await closeDemo(sessionId).catch(() => {});
      setSessionId(null);
    }
    try {
      const response = await prepareDemo(files);
      setDemoPhotos(files);
      setSessionId(response.data.session_id);
      toast.success(`${response.data.uploaded_photos} photos processed in temporary local cache`);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Could not prepare the demo');
    } finally {
      setPreparing(false);
      event.target.value = '';
    }
  };

  const handleFace = (event) => {
    const file = event.target.files?.[0];
    if (!file) return;
    setFaceFile(file);
    setFacePreview(URL.createObjectURL(file));
    setResults(null);
  };

  const handleSearch = async () => {
    if (!sessionId) {
      toast.error('Upload up to 5 demo photos first');
      return;
    }
    if (!faceFile) {
      toast.error('Upload or capture a face photo');
      return;
    }
    setSearching(true);
    try {
      const response = await searchDemoFace(sessionId, faceFile);
      setResults(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Demo search failed');
    } finally {
      setSearching(false);
    }
  };

  const handleClose = async () => {
    if (sessionId) await closeDemo(sessionId).catch(() => {});
    setSessionId(null);
    setDemoPhotos([]);
    setFaceFile(null);
    setFacePreview(null);
    setResults(null);
    toast.success('Demo cache cleared');
  };

  return (
    <div className="max-w-5xl mx-auto px-4 py-10 pb-16">
      <section className="text-center mb-8">
        <span className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary-500/10 text-primary-300 text-sm mb-4">
          <FiLock size={14} /> Public demo - no admin login
        </span>
        <h1 className="text-3xl sm:text-5xl font-extrabold gradient-text mb-4">See How Face Search Works</h1>
        <p className="text-slate-400 max-w-2xl mx-auto">
          Upload up to 5 photos, then scan one face. Images stay in temporary local cache and are removed when you close the demo or after 30 minutes.
        </p>
      </section>

      <div className="grid md:grid-cols-3 gap-4 mb-8">
        {[
          [<FiUpload />, '1. Upload', 'Add up to 5 sample photos.'],
          [<FiDatabase />, '2. Process locally', 'The AI detects faces and creates temporary encodings only in this server session.'],
          [<FiSearch />, '3. Match', 'Upload a face photo to find the matching demo photos.'],
        ].map(([icon, title, text]) => (
          <div key={title} className="card text-center">
            <div className="text-primary-400 text-2xl flex justify-center mb-3">{icon}</div>
            <h2 className="font-semibold mb-1">{title}</h2>
            <p className="text-sm text-slate-400">{text}</p>
          </div>
        ))}
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Demo photo set ({demoPhotos.length}/5)</h2>
          <label className="border-2 border-dashed border-slate-700 rounded-xl p-8 flex flex-col items-center cursor-pointer hover:border-primary-500 transition-colors">
            <FiUpload className="text-primary-400 text-3xl mb-3" />
            <span className="font-medium">Choose up to 5 photos</span>
            <span className="text-xs text-slate-500 mt-1">JPG, PNG or WebP</span>
            <input type="file" accept="image/jpeg,image/png,image/webp" multiple onChange={handlePhotos} className="hidden" />
          </label>
          {demoPhotos.length > 0 && (
            <div className="grid grid-cols-5 gap-2 mt-4">
              {demoPhotos.map((file, index) => (
                <img key={`${file.name}-${index}`} src={URL.createObjectURL(file)} alt={file.name} className="w-full aspect-square object-cover rounded-lg" />
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h2 className="text-lg font-semibold mb-4">Face to find</h2>
          {facePreview ? (
            <img src={facePreview} alt="Face search input" className="w-40 h-40 object-cover rounded-xl mx-auto border-2 border-primary-500" />
          ) : (
            <button onClick={() => faceInput.current?.click()} className="w-full border-2 border-dashed border-slate-700 rounded-xl p-10 text-slate-400 hover:border-primary-500">
              <FiCamera className="mx-auto text-3xl mb-3" />
              Choose your face photo
            </button>
          )}
          <input ref={faceInput} type="file" accept="image/jpeg,image/png,image/webp" onChange={handleFace} className="hidden" />
          {facePreview && (
            <button onClick={() => faceInput.current?.click()} className="block mx-auto text-sm text-primary-400 mt-3">Change photo</button>
          )}
        </div>
      </div>

      <div className="flex flex-wrap justify-center gap-3 mt-6">
        <button onClick={handleSearch} disabled={preparing || searching || !sessionId || !faceFile} className="btn-primary flex items-center gap-2">
          {searching ? 'Searching...' : <><FiSearch /> Find Matching Photos</>}
        </button>
        {sessionId && (
          <button onClick={handleClose} className="btn-secondary flex items-center gap-2">
            <FiTrash2 /> Clear Demo
          </button>
        )}
      </div>

      {results && (
        <div className="card mt-8">
          <div className="flex items-center gap-2 mb-4">
            <FiLock className="text-green-400" />
            <h2 className="text-xl font-bold">{results.total_matches} matching photo(s)</h2>
          </div>
          {results.results.length ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
              {results.results.map((photo) => (
                <a key={photo.photo_id} href={getDemoPhotoUrl(sessionId, photo.photo_id)} target="_blank" rel="noreferrer" className="relative rounded-xl overflow-hidden border border-slate-700">
                  <img src={getDemoPhotoUrl(sessionId, photo.photo_id)} alt={photo.original_filename} className="w-full aspect-square object-cover" />
                  <span className="absolute top-2 left-2 text-xs bg-green-500 text-white rounded-full px-2 py-1">{Math.round(photo.similarity_score * 100)}%</span>
                </a>
              ))}
            </div>
          ) : (
            <p className="text-slate-400">No matching face found. Try a clearer, front-facing photo.</p>
          )}
          <p className="text-xs text-slate-500 mt-4">{results.privacy}</p>
        </div>
      )}

      <div className="mt-8 p-4 rounded-xl bg-slate-800/50 border border-slate-700 text-sm text-slate-400 flex items-start gap-3">
        <FiCloud className="text-primary-400 flex-shrink-0 mt-0.5" />
        <p><strong className="text-slate-300">Privacy:</strong> Demo photos are saved only as temporary files on the server, never in MongoDB or Cloudinary. They are deleted when cleared or after the 30-minute session expires.</p>
      </div>
    </div>
  );
}
