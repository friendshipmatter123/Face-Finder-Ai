// ============================================
// FaceFind Frontend - Footer Component
// ============================================
import { FiHeart, FiShield, FiMail } from 'react-icons/fi';

export default function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="border-t border-slate-700/50 bg-slate-900/80 backdrop-blur-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Top Section */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-8 mb-8">
          {/* Brand */}
          <div className="flex flex-col gap-3">
            <div className="flex items-center gap-3">
              <img src="/jain-logo.png" alt="Jain Group" className="w-8 h-8 rounded" />
              <div className="flex flex-col leading-tight">
                <span className="text-lg font-bold text-white">Jain Group</span>
                <span className="text-[10px] text-slate-400 tracking-widest uppercase">FaceFind AI</span>
              </div>
            </div>
            <p className="text-slate-400 text-sm leading-relaxed">
              AI-powered face recognition photo search. Find your photos from event galleries instantly using advanced face detection technology.
            </p>
          </div>

          {/* Quick Info */}
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-white mb-1">About</h3>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <FiShield size={14} className="text-primary-400 flex-shrink-0" />
              Your photos are securely processed
            </p>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <FiShield size={14} className="text-primary-400 flex-shrink-0" />
              Face data is not shared with third parties
            </p>
            <p className="text-slate-400 text-sm flex items-center gap-2">
              <FiShield size={14} className="text-primary-400 flex-shrink-0" />
              Images are processed on secure servers
            </p>
          </div>

          {/* Contact */}
          <div className="flex flex-col gap-2">
            <h3 className="text-sm font-semibold text-white mb-1">Contact</h3>
            <a href="mailto:jaingroup008@gmail.com" className="text-slate-400 hover:text-primary-400 text-sm flex items-center gap-2 transition-colors">
              <FiMail size={14} className="flex-shrink-0" />
              jaingroup008@gmail.com
            </a>
          </div>
        </div>

        {/* Divider */}
        <div className="border-t border-slate-700/50 pt-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-3">
            <p className="text-slate-500 text-xs text-center sm:text-left">
              &copy; {currentYear} Jain Group. All rights reserved. Powered by FaceFind AI.
            </p>
            <p className="text-slate-500 text-xs flex items-center gap-1">
              Made with <FiHeart size={12} className="text-red-400" /> in India
            </p>
          </div>
        </div>
      </div>
    </footer>
  );
}
