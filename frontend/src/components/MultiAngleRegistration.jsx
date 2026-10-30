import { useCallback, useEffect, useRef, useState } from 'react';
import Webcam from 'react-webcam';
import { FaceMesh } from '@mediapipe/face_mesh';
import { FiCheck, FiChevronRight, FiRefreshCw, FiShield, FiX } from 'react-icons/fi';
import toast from 'react-hot-toast';
import { registerFaces } from '../services/api';

const STEPS = [
  { key: 'front', title: 'Front face', instruction: 'Look directly at the camera', target: 0 },
  { key: 'left', title: 'Left face', instruction: 'Turn your head slightly to the left', target: 1 },
  { key: 'right', title: 'Right face', instruction: 'Turn your head slightly to the right', target: -1 },
];

const POSE = {
  frontMaxYaw: 8,
  sideStartYaw: 12,
  sideTargetYaw: 28,
  stableFrames: 8,
};

function dataUrlToFile(dataUrl, name) {
  const [header, data] = dataUrl.split(',');
  const bytes = Uint8Array.from(atob(data), (character) => character.charCodeAt(0));
  return new File([bytes], name, { type: header.match(/:(.*?);/)[1] });
}

function clamp(value, min = 0, max = 1) {
  return Math.min(max, Math.max(min, value));
}

function assessImageQuality(image) {
  if (!image) return false;
  const canvas = document.createElement('canvas');
  canvas.width = 64;
  canvas.height = 64;
  const context = canvas.getContext('2d', { willReadFrequently: true });
  if (!context) return false;
  context.drawImage(image, 0, 0, 64, 64);
  const pixels = context.getImageData(0, 0, 64, 64).data;
  let brightness = 0;
  let edgeVariance = 0;
  for (let index = 0; index < pixels.length; index += 4) {
    const luminance = (pixels[index] * 0.299) + (pixels[index + 1] * 0.587) + (pixels[index + 2] * 0.114);
    brightness += luminance;
    if (index >= 256) {
      const previous = pixels[index - 256] * 0.299 + pixels[index - 255] * 0.587 + pixels[index - 254] * 0.114;
      edgeVariance += Math.abs(luminance - previous);
    }
  }
  const samples = pixels.length / 4;
  return brightness / samples > 35 && brightness / samples < 235 && edgeVariance / samples > 3;
}

function ProgressArc({ progress, complete, target }) {
  const circumference = 157;
  return (
    <svg viewBox="0 0 120 70" className={`w-full max-w-[180px] h-auto ${target < 0 ? 'scale-x-[-1]' : ''}`}>
      <path d="M 10 60 A 50 50 0 0 1 110 60" fill="none" stroke="#334155" strokeWidth="9" strokeLinecap="round" />
      <path
        d="M 10 60 A 50 50 0 0 1 110 60"
        fill="none"
        stroke={complete ? '#22c55e' : '#38bdf8'}
        strokeWidth="9"
        strokeLinecap="round"
        strokeDasharray={circumference}
        strokeDashoffset={circumference * (1 - progress)}
        className="transition-[stroke-dashoffset] duration-150"
      />
      <text x="60" y="52" textAnchor="middle" fill="white" fontSize="16" fontWeight="bold" transform={target < 0 ? 'scale(-1 1) translate(-120 0)' : undefined}>
        {Math.round(progress * 100)}%
      </text>
    </svg>
  );
}

export default function MultiAngleRegistration({ onRegistered, onClose }) {
  const webcamRef = useRef(null);
  const videoRef = useRef(null);
  const meshRef = useRef(null);
  const frameRef = useRef(null);
  const processingRef = useRef(false);
  const stableRef = useRef(0);
  const capturedRef = useRef(false);
  const [step, setStep] = useState(0);
  const [captures, setCaptures] = useState({});
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState('Starting camera...');
  const [cameraError, setCameraError] = useState('');
  const [consent, setConsent] = useState(false);
  const [reviewing, setReviewing] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const current = STEPS[step];
  const currentRef = useRef(current);
  const reviewingRef = useRef(reviewing);
  const captureCurrentRef = useRef(null);
  currentRef.current = current;
  reviewingRef.current = reviewing;

  const stopCamera = useCallback(() => {
    if (frameRef.current) cancelAnimationFrame(frameRef.current);
    const stream = webcamRef.current?.video?.srcObject;
    stream?.getTracks().forEach((track) => track.stop());
  }, []);

  const resetPose = useCallback(() => {
    stableRef.current = 0;
    capturedRef.current = false;
    setProgress(0);
  }, []);

  const captureCurrent = useCallback(() => {
    if (capturedRef.current) return;
    const image = webcamRef.current?.getScreenshot();
    if (!image) return;
    const activeStep = currentRef.current;
    capturedRef.current = true;
    stableRef.current = 0;
    setProgress(1);
    setStatus('Perfect angle! Captured.');
    setCaptures((previous) => ({ ...previous, [activeStep.key]: image }));
    setTimeout(() => {
      if (activeStep.key === 'right') {
        stopCamera();
        setReviewing(true);
      } else {
        setStep((previous) => previous + 1);
        resetPose();
      }
    }, 850);
  }, [resetPose, stopCamera]);
  captureCurrentRef.current = captureCurrent;

  const inspectFrame = useCallback((results) => {
    processingRef.current = false;
    if (capturedRef.current || reviewingRef.current) return;
    const landmarks = results.multiFaceLandmarks || [];
    if (landmarks.length === 0) {
      stableRef.current = 0;
      setProgress(0);
      setStatus('No face detected. Center your face in the outline.');
      return;
    }
    if (landmarks.length > 1) {
      stableRef.current = 0;
      setProgress(0);
      setStatus('Only one face can be visible.');
      return;
    }

    const face = landmarks[0];
    if (!assessImageQuality(results.image)) {
      stableRef.current = 0;
      setProgress(0);
      setStatus('Improve lighting and hold still for a sharper image.');
      return;
    }
    const leftEye = face[33];
    const rightEye = face[263];
    const nose = face[1];
    const eyeMid = (leftEye.x + rightEye.x) / 2;
    const eyeDistance = Math.max(Math.abs(rightEye.x - leftEye.x), 0.001);
    const yaw = Math.atan((nose.x - eyeMid) / eyeDistance) * (180 / Math.PI) * 2;
    const faceWidth = Math.abs(face[234].x - face[454].x);
    const centered = faceWidth > 0.2 && face[10].y > 0.08 && face[152].y < 0.95;
    const activeStep = currentRef.current;
    const targetProgress = activeStep.target === 0
      ? clamp(1 - Math.abs(yaw) / POSE.frontMaxYaw)
      : clamp((Math.abs(yaw) - POSE.sideStartYaw) / (POSE.sideTargetYaw - POSE.sideStartYaw));
    const correctDirection = activeStep.target === 0 || Math.sign(yaw) === activeStep.target;
    const poseProgress = correctDirection ? targetProgress : 0;
    setProgress(poseProgress);

    if (!centered) {
      stableRef.current = 0;
      setStatus('Move closer and keep your face inside the outline.');
    } else if (!correctDirection || poseProgress < 0.45) {
      stableRef.current = 0;
      setStatus(activeStep.target === 0 ? 'Look straight at the camera.' : 'Turn a little more.');
    } else if (poseProgress < 0.92) {
      stableRef.current = 0;
      setStatus('Hold this position...');
    } else {
      stableRef.current += 1;
      setStatus(stableRef.current >= POSE.stableFrames ? 'Perfect angle!' : 'Hold this position...');
    }

    if (centered && correctDirection && poseProgress >= 0.92) {
      if (stableRef.current >= POSE.stableFrames) captureCurrentRef.current?.();
    }
  }, []);

  const processVideo = useCallback(async () => {
    const video = videoRef.current;
    if (video && video.readyState >= 2 && meshRef.current && !processingRef.current && !capturedRef.current && !reviewing) {
      processingRef.current = true;
      try {
        await meshRef.current.send({ image: video });
      } catch {
        processingRef.current = false;
        setStatus('Face detection is temporarily unavailable. Please retry.');
      }
    }
    frameRef.current = requestAnimationFrame(processVideo);
  }, [reviewing]);

  const initializeMesh = useCallback(async () => {
    const mesh = new FaceMesh({
      locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}`,
    });
    mesh.setOptions({
      maxNumFaces: 2,
      refineLandmarks: false,
      minDetectionConfidence: 0.7,
      minTrackingConfidence: 0.7,
    });
    mesh.onResults(inspectFrame);
    meshRef.current = mesh;
    setStatus('Look at the camera to begin.');
  }, [inspectFrame]);

  useEffect(() => {
    initializeMesh();
    return () => {
      stopCamera();
      meshRef.current?.close?.();
    };
  }, [initializeMesh, stopCamera]);

  useEffect(() => {
    resetPose();
    setStatus(current.instruction);
  }, [current, resetPose]);

  const handleUserMedia = (stream) => {
    videoRef.current = webcamRef.current?.video;
    setCameraError('');
    setStatus(current.instruction);
    processVideo();
    return stream;
  };

  const handleRetake = (key) => {
    const index = STEPS.findIndex((item) => item.key === key);
    setCaptures((previous) => {
      const next = { ...previous };
      delete next[key];
      return next;
    });
    setReviewing(false);
    setStep(index);
    resetPose();
  };

  const skipCurrent = () => {
    if (current.key === 'front') return;
    setCaptures((previous) => ({ ...previous, [current.key]: null }));
    if (current.key === 'left') {
      setStep(2);
      resetPose();
    } else {
      stopCamera();
      setReviewing(true);
    }
  };

  const submit = async () => {
    if (!captures.front) {
      toast.error('The front-face image is required.');
      handleRetake('front');
      return;
    }
    if (!consent) {
      toast.error('Please provide consent to store facial data.');
      return;
    }
    setSubmitting(true);
    try {
      const response = await registerFaces(
        dataUrlToFile(captures.front, 'front-face.jpg'),
        captures.left ? dataUrlToFile(captures.left, 'left-face.jpg') : null,
        captures.right ? dataUrlToFile(captures.right, 'right-face.jpg') : null,
        consent,
      );
      onRegistered(response.data);
      toast.success('Face registration saved.');
      onClose();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Registration failed. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-950/95 flex items-center justify-center p-4">
      <div className="glass rounded-2xl p-4 sm:p-5 max-w-lg w-full max-h-[calc(100vh-1rem)] overflow-hidden">
        <div className="flex items-start justify-between mb-2">
          <div>
            <p className="text-sm text-primary-400 font-semibold flex items-center gap-2"><FiShield /> Private face registration</p>
            <h2 className="text-xl font-bold mt-0.5">{reviewing ? 'Review your captures' : current.title}</h2>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-white" aria-label="Close"><FiX size={22} /></button>
        </div>

        <div className="flex items-center gap-2 mb-2">
          {STEPS.map((item, index) => (
            <div key={item.key} className="flex items-center gap-2 flex-1">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold ${captures[item.key] ? 'bg-green-500' : index === step && !reviewing ? 'bg-primary-500' : 'bg-slate-700'}`}>
                {captures[item.key] ? <FiCheck /> : index + 1}
              </div>
              <span className="hidden sm:block text-xs text-slate-300">{item.title}</span>
              {index < 2 && <div className="h-px bg-slate-700 flex-1" />}
            </div>
          ))}
        </div>

        {!reviewing ? (
          <>
            <div className="relative h-[clamp(200px,39vh,380px)] rounded-xl overflow-hidden bg-slate-900">
              <Webcam
                ref={webcamRef}
                audio={false}
                screenshotFormat="image/jpeg"
                videoConstraints={{ width: 640, height: 640, facingMode: 'user' }}
                onUserMedia={handleUserMedia}
                onUserMediaError={() => setCameraError('Camera permission was denied or the camera is unavailable.')}
                className="w-full h-full object-cover"
                mirrored
              />
              <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
                <div className={`w-52 h-64 border-2 ${progress >= 0.92 ? 'border-green-400' : 'border-primary-400/80'} rounded-[45%] transition-colors`} />
              </div>
            </div>
            <div className="flex justify-center mt-1"><ProgressArc progress={progress} complete={progress >= 1} target={current.target} /></div>
            <p className={`text-center font-semibold ${progress >= 0.92 ? 'text-green-300' : 'text-primary-300'}`}>{status}</p>
            <p className="text-center text-xs text-slate-400 mt-1">{current.instruction}. Automatic capture starts after a stable pose.</p>
            <button
              onClick={captureCurrent}
              disabled={capturedRef.current || submitting}
              className="btn-primary mx-auto mt-3 flex items-center justify-center gap-2 py-2 px-4 text-sm"
            >
              Capture now <FiCheck />
            </button>
            {cameraError && <p className="text-red-400 text-sm text-center mt-3">{cameraError}</p>}
            {current.key !== 'front' && (
              <button onClick={skipCurrent} className="block mx-auto mt-4 text-xs text-slate-400 hover:text-white">Skip this optional angle</button>
            )}
          </>
        ) : (
          <>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              {STEPS.map((item) => (
                <div key={item.key} className="relative">
                  {captures[item.key] ? (
                    <img src={captures[item.key]} alt={`${item.title} capture`} className="aspect-square object-cover rounded-xl border border-green-500/60" />
                  ) : (
                    <div className="aspect-square rounded-xl bg-slate-800 flex items-center justify-center text-xs text-slate-500">Skipped</div>
                  )}
                  <button onClick={() => handleRetake(item.key)} className="absolute bottom-2 right-2 bg-slate-950/80 rounded-lg p-2" aria-label={`Retake ${item.title}`}><FiRefreshCw /></button>
                  <p className="text-xs text-center mt-2">{item.title}</p>
                </div>
              ))}
            </div>
            <label className="flex items-start gap-2 mt-5 text-sm text-slate-300 cursor-pointer">
              <input type="checkbox" checked={consent} onChange={(event) => setConsent(event.target.checked)} className="mt-1 accent-primary-500" />
              I consent to storing these facial encodings to find my event photos. I can delete this registration later.
            </label>
            <button onClick={submit} disabled={!consent || submitting} className="btn-primary w-full mt-5 flex items-center justify-center gap-2">
              {submitting ? 'Validating and saving...' : 'Save registration'} <FiChevronRight />
            </button>
          </>
        )}
      </div>
    </div>
  );
}
