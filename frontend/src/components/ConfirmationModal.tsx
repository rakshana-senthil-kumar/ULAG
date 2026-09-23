import React, { useState } from 'react';
import { AlertCircle, CheckCircle2, X } from 'lucide-react';

interface ConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (comment: string) => void;
  title: string;
  actionName: string;
  targetId: string;
  recommendedVersion?: string;
  isSubmitting?: boolean;
}

export const ConfirmationModal: React.FC<ConfirmationModalProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  actionName,
  targetId,
  recommendedVersion = 'v4.1',
  isSubmitting = false
}) => {
  const [comment, setComment] = useState('');

  if (!isOpen) return null;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onConfirm(comment);
    setComment('');
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4 font-sans animate-fade-in">
      <div className="bg-white rounded-lg shadow-2xl border border-slate-200 w-full max-w-md overflow-hidden">
        {/* Header */}
        <div className="bg-[#0b1e36] text-white px-5 py-4 flex items-center justify-between border-b border-slate-800">
          <div className="flex items-center gap-2.5">
            <CheckCircle2 className="w-5 h-5 text-emerald-400" />
            <h3 className="font-semibold text-sm tracking-wide">{title}</h3>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content */}
        <form onSubmit={handleSubmit} className="p-5 space-y-4">
          <div className="bg-slate-50 border border-slate-200 rounded p-3 text-xs space-y-1.5">
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Target Parcel / Feature:</span>
              <strong className="text-slate-800 font-mono">{targetId}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Action:</span>
              <span className="text-blue-700 font-semibold uppercase">{actionName}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500 font-medium">Resulting Dataset:</span>
              <span className="text-emerald-700 font-semibold font-mono">Harmonized Dataset {recommendedVersion}</span>
            </div>
          </div>

          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-slate-700">
              Officer Audit Comment / Reason <span className="text-red-500">*</span>
            </label>
            <textarea
              required
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder="e.g. Approved GNSS survey boundaries over historical cadastral due to high accuracy alignment with drone ORI."
              className="w-full text-xs p-2.5 border border-slate-300 rounded focus:ring-2 focus:ring-blue-600 focus:border-blue-600 outline-none text-slate-800"
            />
            <p className="text-[10px] text-slate-500 flex items-center gap-1">
              <AlertCircle className="w-3 h-3 text-amber-500" />
              This decision will be permanently signed with your Review Officer credentials in the provenance log.
            </p>
          </div>

          {/* Footer actions */}
          <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-700 hover:bg-slate-100 rounded border border-slate-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !comment.trim()}
              className="px-4 py-2 text-xs font-semibold text-white bg-blue-700 hover:bg-blue-800 rounded transition-colors disabled:opacity-50 disabled:cursor-not-allowed shadow-xs"
            >
              {isSubmitting ? 'Recording...' : 'Confirm Decision'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
