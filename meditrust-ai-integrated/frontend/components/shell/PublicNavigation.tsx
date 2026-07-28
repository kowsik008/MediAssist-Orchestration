"use client";

import React, { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { ChevronDown, Activity, BarChart3, GitCompare } from "lucide-react";

interface PublicNavigationProps {
  isMarketing?: boolean;
}

export const PublicNavigation: React.FC<PublicNavigationProps> = ({ isMarketing = false }) => {
  const pathname = usePathname();
  const [openDropdown, setOpenDropdown] = useState(false);

  const publicLinks = [
    { href: "/", label: "Overview" },
    { href: "/assistant", label: "Assistant" },
    { href: "/evidence", label: "Evidence" },
  ];

  const adminLinks = [
    { href: "/comparison",    label: "Comparison",    icon: <GitCompare className="w-4 h-4 text-[#6a5fc1]" />, desc: "Evaluator benchmark" },
    { href: "/governance",    label: "Governance",    icon: <BarChart3   className="w-4 h-4 text-[#23865f]" />, desc: "Safety & KPI metrics" },
    { href: "/system-health", label: "System Health", icon: <Activity    className="w-4 h-4 text-[#a66a00]" />, desc: "Operational readiness" },
  ];

  const isAdminActive = adminLinks.some((l) => pathname === l.href);

  return (
    <nav className="hidden md:flex items-center space-x-1">
      {publicLinks.map((link) => {
        const isActive = pathname === link.href;
        return (
          <Link
            key={link.href}
            href={link.href}
            className={cn(
              "px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-150",
              isMarketing
                ? isActive
                  ? "bg-white/15 text-white"
                  : "text-[#bbb3c9] hover:text-white hover:bg-white/10"
                : isActive
                  ? "bg-[#f7f6fa] text-[#1f1633] border border-[#e5e7eb]"
                  : "text-[#716a7d] hover:text-[#1f1633] hover:bg-[#f7f6fa]"
            )}
          >
            {link.label}
          </Link>
        );
      })}

      {/* Admin Dropdown */}
      <div
        className="relative"
        onMouseEnter={() => setOpenDropdown(true)}
        onMouseLeave={() => setOpenDropdown(false)}
      >
        <button
          onClick={() => setOpenDropdown((prev) => !prev)}
          type="button"
          aria-expanded={openDropdown}
          aria-label="Admin and Evaluation Menu"
          className={cn(
            "flex items-center space-x-1.5 px-3.5 py-1.5 rounded-lg text-xs font-bold transition-all duration-150 cursor-pointer",
            isMarketing
              ? isAdminActive
                ? "bg-white/15 text-white"
                : "text-[#bbb3c9] hover:text-white hover:bg-white/10"
              : isAdminActive
                ? "bg-[#f7f6fa] text-[#1f1633] border border-[#e5e7eb]"
                : "text-[#716a7d] hover:text-[#1f1633] hover:bg-[#f7f6fa]"
          )}
        >
          <span>Admin & Ops</span>
          <ChevronDown className="w-3.5 h-3.5 opacity-70" />
        </button>

        {openDropdown && (
          <div className="absolute right-0 top-full mt-1 w-64 rounded-xl bg-white border border-[#e5e7eb] shadow-xl p-2 z-50 animate-in fade-in slide-in-from-top-2 duration-150">
            <div className="px-3 py-1 text-[10px] font-code font-bold tracking-wider text-[#716a7d] uppercase">
              Evaluation & Governance
            </div>
            <div className="h-px bg-[#e5e7eb] my-1" />
            {adminLinks.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={() => setOpenDropdown(false)}
                  className={cn(
                    "flex items-start space-x-3 p-2.5 rounded-lg transition-colors",
                    isActive ? "bg-[#f7f6fa] border border-[#e5e7eb] text-[#1f1633]" : "hover:bg-[#f7f6fa] text-[#1f1633]"
                  )}
                >
                  <div className="mt-0.5">{item.icon}</div>
                  <div>
                    <div className="text-xs font-bold">{item.label}</div>
                    <div className="text-[11px] text-[#716a7d]">{item.desc}</div>
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </nav>
  );
};
