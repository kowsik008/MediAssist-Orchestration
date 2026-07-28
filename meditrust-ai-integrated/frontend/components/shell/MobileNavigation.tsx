"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { Menu, X, Shield, Activity, BarChart3, GitCompare } from "lucide-react";

export const MobileNavigation: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const pathname = usePathname();

  const publicLinks = [
    { href: "/", label: "Overview" },
    { href: "/assistant", label: "Assistant" },
    { href: "/evidence", label: "Evidence" },
  ];

  const operationalLinks = [
    { href: "/comparison",    label: "Comparison",    icon: <GitCompare className="w-4 h-4 text-[#1B5FA8]" /> },
    { href: "/governance",    label: "Governance",    icon: <BarChart3   className="w-4 h-4 text-violet-600" /> },
    { href: "/system-health", label: "System Health", icon: <Activity    className="w-4 h-4 text-[#0E9F6E]" /> },
  ];

  return (
    <div className="md:hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        aria-label="Toggle Navigation Menu"
        className="p-2.5 rounded-xl text-slate-600 hover:text-slate-900 bg-slate-100 border border-slate-200 hover:bg-slate-200 transition-colors"
      >
        {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
      </button>

      {isOpen && (
        <div className="fixed inset-x-0 top-16 bottom-0 z-50 bg-white/95 backdrop-blur-xl p-6 flex flex-col justify-between border-t border-slate-200 shadow-2xl animate-in fade-in slide-in-from-top-4">
          <div className="space-y-6">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-slate-400">Public Navigation</span>
              <div className="mt-2 space-y-1">
                {publicLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "block px-4 py-3 rounded-xl text-base font-medium transition-colors",
                      pathname === link.href
                        ? "bg-blue-50 border border-blue-200 text-[#1B5FA8]"
                        : "text-slate-700 hover:bg-slate-100"
                    )}
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <span className="text-xs font-semibold uppercase tracking-wider text-[#1B5FA8]">Operational & Evaluation</span>
              <div className="mt-2 space-y-1">
                {operationalLinks.map((link) => (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setIsOpen(false)}
                    className={cn(
                      "flex items-center space-x-3 px-4 py-3 rounded-xl text-base font-medium transition-colors",
                      pathname === link.href
                        ? "bg-blue-50 border border-blue-200 text-[#1B5FA8]"
                        : "text-slate-600 hover:bg-slate-100"
                    )}
                  >
                    {link.icon}
                    <span>{link.label}</span>
                  </Link>
                ))}
              </div>
            </div>
          </div>

          <div className="p-4 rounded-xl bg-blue-50 border border-blue-200 text-xs text-blue-700 flex items-center space-x-2">
            <Shield className="w-4 h-4 text-[#1B5FA8] flex-shrink-0" />
            <span>Governed Healthcare Knowledge System • Read-only Guidance</span>
          </div>
        </div>
      )}
    </div>
  );
};
