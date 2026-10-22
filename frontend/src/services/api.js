// ============================================
// FaceFind Frontend - API Service
// ============================================
import axios from 'axios';

// In production: use full backend URL; In dev: proxy handles it
const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 120000, // 2 min for large uploads
});

// Attach auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('facefind_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('facefind_token');
      window.location.href = '/admin/login';
    }
    return Promise.reject(error);
  }
);

// ──── Auth ────
export const adminLogin = (email, password) =>
  api.post('/admin/login', { email, password });

export const adminRegister = (email, password, name) =>
  api.post('/admin/register', { email, password, name });

export const getAdminProfile = () =>
  api.get('/admin/me');

export const getDashboardStats = () =>
  api.get('/admin/dashboard');

// ──── Events ────
export const createEvent = (data) =>
  api.post('/events/', data);

export const listEvents = () =>
  api.get('/events/');

export const getEvent = (eventId) =>
  api.get(`/events/${eventId}`);

export const updateEvent = (eventId, data) =>
  api.put(`/events/${eventId}`, data);

export const deleteEvent = (eventId) =>
  api.delete(`/events/${eventId}`);

export const getEventByCode = (eventCode) =>
  api.get(`/events/code/${eventCode}`);

// ──── Photos ────
export const uploadPhotos = (eventId, files, onProgress) => {
  const formData = new FormData();
  files.forEach((file) => formData.append('files', file));

  return api.post(`/photos/upload/${eventId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000, // 10 min for bulk uploads
    onUploadProgress: onProgress,
  });
};

export const listEventPhotos = (eventId, skip = 0, limit = 50) =>
  api.get(`/photos/event/${eventId}?skip=${skip}&limit=${limit}`);

export const getProcessingStatus = (eventId) =>
  api.get(`/photos/processing-status/${eventId}`);

export const deletePhoto = (photoId) =>
  api.delete(`/photos/${photoId}`);

// ──── Search ────
export const searchFace = (eventCode, faceImage, tolerance) => {
  const formData = new FormData();
  formData.append('face_image', faceImage);
  if (tolerance) {
    formData.append('tolerance', tolerance);
  }

  return api.post(`/search/${eventCode}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 60000,
  });
};

// ──── Files ────
export const getPhotoUrl = (photoId) => `${API_BASE}/files/photo/${photoId}`;
export const getThumbnailUrl = (photoId) => `${API_BASE}/files/thumbnail/${photoId}`;

export const downloadPhoto = (photoId) =>
  api.get(`/files/download/${photoId}`, { responseType: 'blob' });

export const downloadZip = (photoIds) =>
  api.post('/files/download-zip', photoIds, { responseType: 'blob' });

export default api;
