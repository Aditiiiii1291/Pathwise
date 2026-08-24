import React, { useState, useRef } from 'react';
import {
  UploadCloud,
  FileText,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  X,
  FileCheck,
  Info,
  RefreshCw,
} from 'lucide-react';
import { uploadDataset } from '../utils/api';

const DATA_TYPES = [
  { id: 'students', label: 'Student Roster', desc: 'Roll numbers, names, departments, and mentor assignments' },
  { id: 'attendance', label: 'Attendance Records', desc: 'Weekly attended and total timetable hours' },
  { id: 'marks', label: 'Academic Marks', desc: 'Internal assessments, quizzes, and term exam scores' },
  { id: 'fees', label: 'Fee Transactions', desc: 'Billing installments, payment dates, and due statuses' },
  { id: 'attempts', label: 'Attempt & Backlog History', desc: 'Course retakes, examination attempts, and backlog status' },
];

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

export default function UploadPage() {
  const [selectedType, setSelectedType] = useState('students');
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [clientError, setClientError] = useState(null);
  const [result, setResult] = useState(null);
  const fileInputRef = useRef(null);

  const handleFileSelect = (e) => {
    setClientError(null);
    setResult(null);
    const selected = e.target.files?.[0];
    if (!selected) return;

    // Check size limit (10MB)
    if (selected.size > MAX_FILE_SIZE_BYTES) {
      setClientError(`Selected file (${(selected.size / (1024 * 1024)).toFixed(1)} MB) exceeds maximum allowed size of 10 MB.`);
      setFile(null);
      return;
    }

    // Check extension
    const ext = selected.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      setClientError('Only CSV (.csv) and Excel (.xlsx) files are supported.');
      setFile(null);
      return;
    }

    setFile(selected);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setClientError(null);
    setResult(null);
    const dropped = e.dataTransfer.files?.[0];
    if (!dropped) return;

    if (dropped.size > MAX_FILE_SIZE_BYTES) {
      setClientError(`Dropped file exceeds maximum allowed size of 10 MB.`);
      return;
    }

    const ext = dropped.name.split('.').pop().toLowerCase();
    if (ext !== 'csv' && ext !== 'xlsx') {
      setClientError('Only CSV (.csv) and Excel (.xlsx) files are supported.');
      return;
    }

    setFile(dropped);
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setUploading(true);
    setClientError(null);
    setResult(null);

    try {
      const res = await uploadDataset(selectedType, file);
      setResult(res);
      setFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
    } catch (err) {
      console.error('Upload failed:', err);
      setClientError(err.message || 'Dataset upload failed.');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      {/* Header */}
      <div>
        <h2 className="text-xl font-bold tracking-tight text-slate-800 flex items-center gap-2">
          <UploadCloud className="w-5 h-5 text-brand-600" />
          Institutional Data Ingestion
        </h2>
        <p className="text-xs text-slate-500 mt-0.5">
          Upload and validate CSV or Excel (XLSX) institutional datasets into Pathwise
        </p>
      </div>

      {/* Dataset Type Selector */}
      <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          1. Select Dataset Category
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
          {DATA_TYPES.map((t) => (
            <div
              key={t.id}
              onClick={() => setSelectedType(t.id)}
              className={`p-3.5 rounded-xl border cursor-pointer transition ${
                selectedType === t.id
                  ? 'bg-brand-50/70 border-brand-300 ring-2 ring-brand-500/20'
                  : 'bg-slate-50/50 border-slate-200/70 hover:bg-slate-100/60'
              }`}
            >
              <span className={`text-xs font-bold block ${selectedType === t.id ? 'text-brand-800' : 'text-slate-800'}`}>
                {t.label}
              </span>
              <span className="text-[11px] text-slate-500 mt-1 block leading-normal">
                {t.desc}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* File Upload Zone */}
      <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4">
        <h3 className="text-xs font-bold text-slate-800 uppercase tracking-wider">
          2. Choose or Drop Dataset File (.csv / .xlsx)
        </h3>

        <div
          onDragOver={(e) => e.preventDefault()}
          onDrop={handleDrop}
          className={`border-2 border-dashed rounded-2xl p-8 text-center transition flex flex-col items-center justify-center gap-3 ${
            file
              ? 'border-emerald-300 bg-emerald-50/30'
              : 'border-slate-200 hover:border-brand-300 hover:bg-slate-50/50'
          }`}
        >
          <div className="w-12 h-12 rounded-2xl bg-brand-50 text-brand-600 flex items-center justify-center shadow-xs">
            <UploadCloud className="w-6 h-6" />
          </div>

          <div>
            <p className="text-xs font-semibold text-slate-700">
              Drag and drop your spreadsheet file here, or{' '}
              <label className="text-brand-600 hover:text-brand-700 cursor-pointer underline">
                browse files
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".csv,.xlsx"
                  onChange={handleFileSelect}
                  className="hidden"
                />
              </label>
            </p>
            <p className="text-[11px] text-slate-400 mt-1">
              Supports .csv and .xlsx up to 10MB
            </p>
          </div>

          {file && (
            <div className="mt-2 inline-flex items-center gap-2 px-3 py-1.5 bg-white border border-emerald-200 rounded-xl text-xs font-medium text-emerald-800 shadow-xs">
              <FileCheck className="w-4 h-4 text-emerald-600" />
              <span>{file.name} ({(file.size / 1024).toFixed(1)} KB)</span>
              <button
                type="button"
                onClick={() => setFile(null)}
                className="text-slate-400 hover:text-slate-600 ml-1"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          )}
        </div>

        {/* Error Alert */}
        {clientError && (
          <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl flex items-center gap-2.5 text-xs text-rose-800">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{clientError}</span>
          </div>
        )}

        {/* Action Button */}
        <div className="flex items-center justify-between pt-2">
          <div className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <Info className="w-3.5 h-3.5" />
            <span>Target category: <strong className="text-slate-600">{selectedType}</strong></span>
          </div>

          <button
            onClick={handleUpload}
            disabled={!file || uploading}
            className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:opacity-40 text-white font-semibold rounded-xl text-xs shadow-md transition flex items-center gap-2"
          >
            {uploading ? (
              <>
                <RefreshCw className="w-4 h-4 animate-spin" />
                <span>Validating & Ingesting...</span>
              </>
            ) : (
              <>
                <UploadCloud className="w-4 h-4" />
                <span>Upload & Ingest Dataset</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Ingestion Results Diagnostic Card */}
      {result && (
        <div className="bg-white border border-slate-100 rounded-2xl p-6 shadow-card space-y-4 animate-in fade-in">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-600" />
              <div>
                <h3 className="text-sm font-bold text-slate-800">
                  Ingestion Summary: {result.filename}
                </h3>
                <span className="text-[11px] text-slate-400 font-mono">
                  Category: {result.data_type}
                </span>
              </div>
            </div>

            <span
              className={`px-3 py-1 rounded-full text-xs font-semibold ${
                result.invalid_rows === 0
                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                  : 'bg-amber-50 text-amber-700 border border-amber-200'
              }`}
            >
              {result.invalid_rows === 0 ? '100% Valid' : 'Partial Import with Exceptions'}
            </span>
          </div>

          {/* Metric Badges */}
          <div className="grid grid-cols-3 gap-3">
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Valid Rows</span>
              <span className="text-xl font-bold text-emerald-600">{result.valid_rows}</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Inserted Rows</span>
              <span className="text-xl font-bold text-brand-600">{result.inserted_rows}</span>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-100 rounded-xl text-center">
              <span className="text-[10px] uppercase font-bold text-slate-400 block">Invalid Rows</span>
              <span className="text-xl font-bold text-rose-600">{result.invalid_rows}</span>
            </div>
          </div>

          {/* Row Errors Table */}
          {result.errors && result.errors.length > 0 && (
            <div className="space-y-2 pt-2">
              <h4 className="text-xs font-semibold text-rose-800 flex items-center gap-1.5">
                <AlertTriangle className="w-3.5 h-3.5 text-rose-600" />
                Validation Diagnostic Issues ({result.errors.length})
              </h4>
              <div className="max-h-48 overflow-y-auto border border-rose-100 rounded-xl">
                <table className="w-full text-left text-xs">
                  <thead className="bg-rose-50/50 text-[10px] text-rose-700 font-bold uppercase sticky top-0">
                    <tr>
                      <th className="py-2 px-3">Row</th>
                      <th className="py-2 px-3">Code</th>
                      <th className="py-2 px-3">Field</th>
                      <th className="py-2 px-3">Message</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-rose-100/60 bg-white">
                    {result.errors.map((err, idx) => (
                      <tr key={idx} className="hover:bg-rose-50/30">
                        <td className="py-2 px-3 font-mono font-bold text-slate-600">{err.row_number || '—'}</td>
                        <td className="py-2 px-3 font-mono text-[10px] text-rose-600">{err.code}</td>
                        <td className="py-2 px-3 font-mono text-slate-500">{err.field || '—'}</td>
                        <td className="py-2 px-3 text-slate-700">{err.message}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
