// ============================================
// FaceFind Frontend - Webcam Capture Component
// ============================================
import { useRef, useState, useCallback } from 'react';
import Webcam from 'react-webcam';
import { FiCamera, FiRefreshCw, FiCheck, FiX } from 'react-icons/fi';

export default function WebcamCapture({ onCapture, onClose }) {
  const webcamRef = useRef(null);
  const [captured, setCaptured] = useState(null);
  const [facingMode, setFacingMode] = useState('user');

  const videoConstraints = {
    width: 480,
    height: 480,
    facingMode,
  };

  const capture = useCallback(() => {
    if (webcamRef.current) {
      const imageSrc = webcamRef.current.getScreenshot();
      setCaptured(imageSrc);
    }
  }, []);

  const retake = () => setCaptured(null);

  const confirmCapture = () => {
    if (captured) {
      // Convert base64 to blob
      fetch(captured)
        .then((res) => res.blob())
        .then((blob) => {
          const file = new File([blob], 'selfie.jpg', { type: 'image/jpeg' });
          onCapture(file);
        });
    }
  };

  const toggleCamera = () => {
    setFacingMode((prev) => (prev === 'user' ? 'environment' : 'user'));
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
      <div className="glass rounded-2xl p-6 max-w-lg w-full">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold">Scan Your Face</h3>
          <button onClick={onClose} className="text-slate-400 hover:text-white">
            <FiX size={20} />
          </button>
        </div>

        <div className="relative rounded-xl overflow-hidden bg-slate-900 aspect-square">
          {!captured ? (
            <>
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={videoConstraints}
                className="w-full h-full object-cover"
                mirrored={facingMode === 'user'}
              />
              {/* Face guide overlay */}
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className="w-48 h-48 border-2 border-primary-400/50 rounded-full scan-animation" />
              </div>
            </>
          ) : (
            <img src={captured} alt="Captured" className="w-full h-full object-cover" />
          )}
        </div>

        <div className="flex justify-center gap-3 mt-4">
          {!captured ? (
            <>
              <button onClick={toggleCamera} className="btn-secondary !py-2 !px-4">
                <FiRefreshCw size={18} />
              </button>
              <button onClick={capture} className="btn-primary !py-2 !px-8 flex items-center gap-2">
                <FiCamera size={18} />
                Capture
              </button>
            </>
          ) : (
            <>
              <button onClick={retake} className="btn-secondary !py-2 !px-6 flex items-center gap-2">
                <FiRefreshCw size={16} />
                Retake
              </button>
              <button onClick={confirmCapture} className="btn-primary !py-2 !px-6 flex items-center gap-2">
                <FiCheck size={16} />
                Use This Photo
              </button>
            </>
          )}
        </div>

        <p className="text-xs text-slate-400 text-center mt-3">
          Position your face in the circle and ensure good lighting
        </p>
      </div>
    </div>
  );
}
