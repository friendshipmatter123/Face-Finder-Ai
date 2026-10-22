// ============================================
// FaceFind Frontend - Photo Grid Component
// ============================================
import { useState } from 'react';
import { FiDownload, FiCheck, FiZoomIn, FiX } from 'react-icons/fi';
import { getThumbnailUrl, getPhotoUrl } from '../services/api';

export default function PhotoGrid({ photos, selectable = true, onSelectionChange }) {
  const [selected, setSelected] = useState(new Set());
  const [lightbox, setLightbox] = useState(null);

  const toggleSelect = (photoId) => {
    const newSelected = new Set(selected);
    if (newSelected.has(photoId)) {
      newSelected.delete(photoId);
    } else {
      newSelected.add(photoId);
    }
    setSelected(newSelected);
    onSelectionChange?.(Array.from(newSelected));
  };

  const selectAll = () => {
    const all = new Set(photos.map((p) => p.photo_id || p.id));
    setSelected(all);
    onSelectionChange?.(Array.from(all));
  };

  const deselectAll = () => {
    setSelected(new Set());
    onSelectionChange?.([]);
  };

  return (
    <div>
      {/* Selection toolbar */}
      {selectable && photos.length > 0 && (
        <div className="flex items-center gap-4 mb-4">
          <button onClick={selectAll} className="text-sm text-primary-400 hover:text-primary-300">
            Select All
          </button>
          <button onClick={deselectAll} className="text-sm text-slate-400 hover:text-slate-300">
            Deselect All
          </button>
          <span className="text-sm text-slate-500">
            {selected.size} selected
          </span>
        </div>
      )}

      {/* Photo grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
        {photos.map((photo, idx) => {
          const id = photo.photo_id || photo.id;
          const isSelected = selected.has(id);
          const similarity = photo.similarity_score;

          return (
            <div
              key={id}
              className={`relative group rounded-xl overflow-hidden border-2 transition-all duration-200 cursor-pointer
                ${isSelected ? 'border-primary-500 ring-2 ring-primary-500/30' : 'border-transparent hover:border-slate-600'}`}
              style={{ animationDelay: `${idx * 30}ms` }}
            >
              {/* Image */}
              <div className="aspect-square bg-slate-800">
                <img
                  src={getThumbnailUrl(id)}
                  alt={photo.original_filename || photo.filename}
                  className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-105"
                  loading="lazy"
                />
              </div>

              {/* Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent
                              opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div className="absolute bottom-2 left-2 right-2 flex justify-between items-end">
                  <p className="text-xs text-white truncate max-w-[70%]">
                    {photo.original_filename || photo.filename}
                  </p>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setLightbox(id);
                    }}
                    className="p-1.5 bg-white/20 rounded-lg hover:bg-white/30 transition-colors"
                  >
                    <FiZoomIn size={14} className="text-white" />
                  </button>
                </div>
              </div>

              {/* Similarity badge */}
              {similarity !== undefined && (
                <div className="absolute top-2 left-2 bg-green-500/90 text-white text-xs font-bold px-2 py-0.5 rounded-full">
                  {Math.round(similarity * 100)}%
                </div>
              )}

              {/* Select checkbox */}
              {selectable && (
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSelect(id);
                  }}
                  className={`absolute top-2 right-2 w-6 h-6 rounded-md flex items-center justify-center transition-all
                    ${isSelected
                      ? 'bg-primary-500 text-white'
                      : 'bg-black/30 text-white/60 opacity-0 group-hover:opacity-100'}`}
                >
                  {isSelected && <FiCheck size={14} />}
                </button>
              )}
            </div>
          );
        })}
      </div>

      {/* Lightbox */}
      {lightbox && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center p-4"
          onClick={() => setLightbox(null)}
        >
          <button
            className="absolute top-4 right-4 text-white/70 hover:text-white p-2"
            onClick={() => setLightbox(null)}
          >
            <FiX size={24} />
          </button>
          <img
            src={getPhotoUrl(lightbox)}
            alt="Full size"
            className="max-w-full max-h-[90vh] object-contain rounded-lg"
            onClick={(e) => e.stopPropagation()}
          />
        </div>
      )}
    </div>
  );
}
