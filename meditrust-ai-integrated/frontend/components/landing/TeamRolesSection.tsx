"use client";

import React from "react";
import { SurfaceCard } from "../shared/SurfaceCard";
import { ImageWithFallback } from "../shared/ImageWithFallback";
import { UserCheck, Stethoscope, HeartPulse, Pill, ShieldCheck, Settings } from "lucide-react";

export const TeamRolesSection: React.FC = () => {
  const roles = [
    { title: "Doctor",             icon: <Stethoscope className="w-4 h-4 text-[#6a5fc1]" />,  desc: "Fast evidence cross-checking during clinical reviews." },
    { title: "Nurse",              icon: <HeartPulse  className="w-4 h-4 text-[#b5414c]" />,  desc: "Instant isolation, hygiene & PPE protocol guidance." },
    { title: "Pharmacist",         icon: <Pill        className="w-4 h-4 text-[#23865f]" />,  desc: "Formulary standards and drug stewardship reference." },
    { title: "Compliance Officer", icon: <ShieldCheck className="w-4 h-4 text-[#c2ef4e]" />,  desc: "Audit trail, risk logs and citation verification." },
    { title: "Administrator",      icon: <Settings    className="w-4 h-4 text-[#a66a00]" />,  desc: "System readiness, uptime and service topology." }
  ];

  return (
    <section className="py-16 bg-[#ffffff] text-[#1f1633] border-b border-[#e5e7eb]">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Image Column */}
          <div className="lg:col-span-5 order-2 lg:order-1">
            <SurfaceCard variant="transactional" className="p-2 border-[#e5e7eb] relative overflow-hidden shadow-sm">
              <div className="relative aspect-square rounded-lg overflow-hidden min-h-[300px] bg-[#f7f6fa]">
                <ImageWithFallback
                  src="/images/trust_story_team.png"
                  alt="Multidisciplinary healthcare team"
                  fill
                />
                <div className="absolute inset-0 bg-gradient-to-t from-[#1f1633]/50 via-transparent to-transparent pointer-events-none" />
                <div className="absolute bottom-4 left-4 right-4 p-3 rounded-xl bg-white/90 backdrop-blur-sm border border-white shadow-md text-xs text-[#1f1633]">
                  <div className="flex items-center space-x-2 font-bold">
                    <UserCheck className="w-4 h-4 text-[#6a5fc1]" />
                    <span>Multidisciplinary Access Roles</span>
                  </div>
                </div>
              </div>
            </SurfaceCard>
          </div>

          {/* Role Chips Column */}
          <div className="lg:col-span-7 space-y-6 order-1 lg:order-2">
            <div>
              <span className="text-xs font-semibold uppercase tracking-wider text-[#6a5fc1]">Tailored Access Roles</span>
              <h2 className="font-display-section text-[#1f1633] mt-1">
                Designed For Healthcare Teams
              </h2>
              <p className="text-sm text-[#494256] mt-2">
                Contextualized guidance interface adapted for different roles across clinical and health system staff.
              </p>
            </div>

            <div className="space-y-3">
              {roles.map((role, idx) => (
                <div
                  key={idx}
                  className="flex items-start space-x-3 p-3.5 rounded-xl border border-[#e5e7eb] bg-[#f7f6fa] hover:border-[#6a5fc1]/40 transition-colors"
                >
                  <div className="p-2 rounded-lg bg-white border border-[#e5e7eb] mt-0.5 flex-shrink-0">
                    {role.icon}
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[#1f1633]">{role.title}</h3>
                    <p className="text-xs text-[#716a7d]">{role.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};
