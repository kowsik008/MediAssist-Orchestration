import React from "react";
import { VideoHero } from "@/components/landing/VideoHero";
import { TrustStory } from "@/components/landing/TrustStory";
import { SupportedTaskCards } from "@/components/landing/SupportedTaskCards";
import { EvidencePreviewCollage } from "@/components/landing/EvidencePreviewCollage";
import { SafetySection } from "@/components/landing/SafetySection";
import { TeamRolesSection } from "@/components/landing/TeamRolesSection";
import { FinalCTA } from "@/components/landing/FinalCTA";

export default function LandingPage() {
  return (
    <div className="w-full flex flex-col">
      <VideoHero />
      <TrustStory />
      <SupportedTaskCards />
      <EvidencePreviewCollage />
      <SafetySection />
      <TeamRolesSection />
      <FinalCTA />
    </div>
  );
}
