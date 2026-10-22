// ============================================
// FaceFind Frontend - Admin Dashboard Page
// ============================================
import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  FiImage, FiUsers, FiCalendar, FiHardDrive,
  FiPlus, FiSettings, FiChevronRight, FiTrash2, FiCopy, FiCheck
} from 'react-icons/fi';
import toast from 'react-hot-toast';
import { useAuth } from '../context/AuthContext';
import { getDashboardStats, listEvents, deleteEvent, createEvent } from '../services/api';

export default function DashboardPage() {
  const { admin } = useAuth();
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [creating, setCreating] = useState(false);
  const [copiedCode, setCopiedCode] = useState(null);

  // New event form
  const [newEvent, setNewEvent] = useState({ name: '', description: '', is_public: false });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [statsRes, eventsRes] = await Promise.all([
        getDashboardStats(),
        listEvents(),
      ]);
      setStats(statsRes.data);
      setEvents(eventsRes.data);
    } catch (err) {
      toast.error('Failed to load dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateEvent = async (e) => {
    e.preventDefault();
    if (!newEvent.name.trim()) {
      toast.error('Event name is required');
      return;
    }
    setCreating(true);
    try {
      const res = await createEvent(newEvent);
      toast.success(`Event "${res.data.name}" created! Code: ${res.data.event_code}`);
      setShowCreateModal(false);
      setNewEvent({ name: '', description: '', is_public: false });
      fetchData();
    } catch (err) {
      toast.error('Failed to create event');
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteEvent = async (eventId, eventName) => {
    if (!window.confirm(`Delete "${eventName}" and all its photos? This cannot be undone.`)) return;
    try {
      await deleteEvent(eventId);
      toast.success('Event deleted');
      fetchData();
    } catch {
      toast.error('Failed to delete event');
    }
  };

  const copyCode = (code) => {
    navigator.clipboard.writeText(code);
    setCopiedCode(code);
    toast.success('Event code copied!');
    setTimeout(() => setCopiedCode(null), 2000);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="w-8 h-8 border-3 border-primary-500/30 border-t-primary-500 rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold">Welcome, {admin?.name}!</h1>
          <p className="text-slate-400 text-sm">Manage your events and photos</p>
        </div>
        <button onClick={() => setShowCreateModal(true)} className="btn-primary flex items-center gap-2">
          <FiPlus size={18} /> New Event
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          <StatCard icon={<FiCalendar />} label="Total Events" value={stats.total_events} color="primary" />
          <StatCard icon={<FiImage />} label="Total Photos" value={stats.total_photos} color="accent" />
          <StatCard icon={<FiUsers />} label="Faces Detected" value={stats.total_faces} color="green" />
          <StatCard icon={<FiHardDrive />} label="Storage Used" value={`${stats.storage_used_mb} MB`} color="amber" />
        </div>
      )}

      {/* Events List */}
      <div className="space-y-4">
        <h2 className="text-lg font-semibold">Your Events</h2>

        {events.length === 0 ? (
          <div className="card text-center py-12">
            <FiCalendar size={48} className="text-slate-600 mx-auto mb-4" />
            <p className="text-slate-400 mb-4">No events yet. Create your first event!</p>
            <button onClick={() => setShowCreateModal(true)} className="btn-primary">
              <FiPlus className="inline mr-1" /> Create Event
            </button>
          </div>
        ) : (
          <div className="grid gap-4">
            {events.map((event) => (
              <div
                key={event.id}
                className="card flex flex-wrap items-center gap-4 hover:bg-slate-800/70 cursor-pointer"
                onClick={() => navigate(`/admin/event/${event.id}`)}
              >
                <div className="flex-1 min-w-[200px]">
                  <h3 className="font-semibold text-white">{event.name}</h3>
                  <p className="text-sm text-slate-400 line-clamp-1">{event.description || 'No description'}</p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); copyCode(event.event_code); }}
                    className="flex items-center gap-1 bg-slate-700 px-3 py-1.5 rounded-lg text-sm font-mono hover:bg-slate-600 transition-colors"
                  >
                    {copiedCode === event.event_code ? <FiCheck size={14} className="text-green-400" /> : <FiCopy size={14} />}
                    {event.event_code}
                  </button>
                </div>

                <div className="flex items-center gap-4 text-sm text-slate-400">
                  <span>{event.total_photos} photos</span>
                  <span>{event.total_faces} faces</span>
                  <span className={`px-2 py-0.5 rounded-full text-xs font-medium 
                    ${event.processing_status === 'completed' ? 'bg-green-500/20 text-green-400'
                      : event.processing_status === 'processing' ? 'bg-amber-500/20 text-amber-400'
                      : 'bg-slate-600/50 text-slate-400'}`}>
                    {event.processing_status}
                  </span>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={(e) => { e.stopPropagation(); handleDeleteEvent(event.id, event.name); }}
                    className="p-2 text-red-400 hover:bg-red-500/10 rounded-lg transition-colors"
                  >
                    <FiTrash2 size={16} />
                  </button>
                  <FiChevronRight className="text-slate-500" />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Create Event Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 z-50 bg-black/70 flex items-center justify-center p-4">
          <div className="card max-w-md w-full">
            <h2 className="text-xl font-bold mb-4">Create New Event</h2>
            <form onSubmit={handleCreateEvent} className="space-y-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">Event Name *</label>
                <input
                  type="text"
                  value={newEvent.name}
                  onChange={(e) => setNewEvent({ ...newEvent, name: e.target.value })}
                  placeholder="e.g., Wedding Reception 2026"
                  className="input-field"
                  autoFocus
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">Description</label>
                <textarea
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  placeholder="Brief description of the event..."
                  className="input-field h-24 resize-none"
                />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={newEvent.is_public}
                  onChange={(e) => setNewEvent({ ...newEvent, is_public: e.target.checked })}
                  className="w-4 h-4 rounded accent-primary-500"
                />
                <span className="text-sm text-slate-300">Make event public (no code required)</span>
              </label>
              <div className="flex gap-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCreateModal(false)}
                  className="btn-secondary flex-1"
                >
                  Cancel
                </button>
                <button type="submit" disabled={creating} className="btn-primary flex-1">
                  {creating ? 'Creating...' : 'Create Event'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

function StatCard({ icon, label, value, color }) {
  const colorClasses = {
    primary: 'from-primary-500/20 to-primary-500/5 border-primary-500/30 text-primary-400',
    accent: 'from-accent-500/20 to-accent-500/5 border-accent-500/30 text-accent-400',
    green: 'from-green-500/20 to-green-500/5 border-green-500/30 text-green-400',
    amber: 'from-amber-500/20 to-amber-500/5 border-amber-500/30 text-amber-400',
  };

  return (
    <div className={`bg-gradient-to-br ${colorClasses[color]} border rounded-2xl p-5`}>
      <div className="text-2xl mb-2">{icon}</div>
      <p className="text-2xl font-bold text-white">{value}</p>
      <p className="text-sm text-slate-400">{label}</p>
    </div>
  );
}
