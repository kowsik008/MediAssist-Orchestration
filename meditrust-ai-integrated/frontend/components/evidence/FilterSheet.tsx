"use client";

import React from "react";

interface FilterSheetProps {
  isOpen: boolean;
  selectedStatus: string;
  onSelectStatus: (s: string) => void;
  selectedRole: string;
  onSelectRole: (r: string) => void;
  selectedType: string;
  onSelectType: (t: string) => void;
  onReset: () => void;
}

export const FilterSheet: React.FC<FilterSheetProps> = ({
  isOpen, selectedStatus, onSelectStatus, selectedRole, onSelectRole, selectedType, onSelectType, onReset
}) => {
  if (!isOpen) return null;

  const selectClass = "w-full bg-white text-slate-700 border border-slate-200 rounded-xl p-2.5 text-xs focus:outline-none focus:border-[#1B5FA8] focus:ring-2 focus:ring-blue-100 transition-all shadow-sm";

  return (
    <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 my-3 grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs animate-in fade-in shadow-sm">
      <div>
        <label className="block text-slate-600 font-semibold mb-1">Source Status</label>
        <select value={selectedStatus} onChange={(e) => onSelectStatus(e.target.value)} className={selectClass}>
          <option value="All">All Statuses</option>
          <option value="Current">Current</option>
          <option value="Superseded">Superseded</option>
          <option value="Expired">Expired</option>
          <option value="Demonstration only">Demonstration only</option>
        </select>
      </div>

      <div>
        <label className="block text-slate-600 font-semibold mb-1">Access Role</label>
        <select value={selectedRole} onChange={(e) => onSelectRole(e.target.value)} className={selectClass}>
          <option value="All">All Roles</option>
          <option value="Doctor">Doctor</option>
          <option value="Nurse">Nurse</option>
          <option value="Pharmacist">Pharmacist</option>
          <option value="Compliance Officer">Compliance Officer</option>
        </select>
      </div>

      <div>
        <label className="block text-slate-600 font-semibold mb-1">Document Type</label>
        <select value={selectedType} onChange={(e) => onSelectType(e.target.value)} className={selectClass}>
          <option value="All">All Types</option>
          <option value="Clinical Guidance">Clinical Guidance</option>
          <option value="Formulary Standard">Formulary Standard</option>
          <option value="Policy Document">Policy Document</option>
          <option value="Synthetic Demonstration">Synthetic Demonstration</option>
        </select>
      </div>

      <div className="sm:col-span-3 flex justify-end">
        <button onClick={onReset} className="text-xs text-[#1B5FA8] hover:underline font-semibold">Reset Filters</button>
      </div>
    </div>
  );
};
