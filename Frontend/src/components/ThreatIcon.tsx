import { CloudRain, FlaskConical, Pill, ShieldCheck, SunMedium } from "lucide-react";
import type { LucideIcon } from "lucide-react";

type ThreatState = "SAFE" | "WEATHER" | "CAUTION" | "NARCOTIC" | "NARCOTIC PROXY" | "ALCOHOL";

const ICONS: Record<ThreatState, { icon: LucideIcon; label: string }> = {
  SAFE: { icon: ShieldCheck, label: "Safe: item cleared" },
  WEATHER: { icon: CloudRain, label: "Weather variation" },
  CAUTION: { icon: CloudRain, label: "Weather variation" },
  NARCOTIC: { icon: Pill, label: "Possible narcotic threat" },
  "NARCOTIC PROXY": { icon: Pill, label: "Possible narcotic threat" },
  ALCOHOL: { icon: FlaskConical, label: "Alcohol or sanitizer response" },
};

export default function ThreatIcon({ state, size = 24, className = "" }: { state: string; size?: number; className?: string }) {
  const config = ICONS[state as ThreatState] || ICONS.SAFE;
  const Icon = config.icon;

  if (state === "WEATHER" || state === "CAUTION") {
    return (
      <span className={`relative inline-block ${className}`} style={{ width: size, height: size }} role="img" aria-label={config.label} title={config.label}>
        <SunMedium className="absolute left-0 top-0" size={size * .62} strokeWidth={1.8} aria-hidden="true" />
        <CloudRain className="absolute bottom-0 right-0" size={size * .78} strokeWidth={1.8} aria-hidden="true" />
      </span>
    );
  }

  if (state === "NARCOTIC" || state === "NARCOTIC PROXY") {
    return (
      <span className={`relative inline-block ${className}`} style={{ width: size, height: size }} role="img" aria-label={config.label} title={config.label}>
        <Pill className="absolute right-0 top-0" size={size * .78} strokeWidth={1.8} aria-hidden="true" />
        <span className="absolute bottom-[12%] left-[5%] h-[23%] w-[23%] rounded-full bg-current" />
        <span className="absolute bottom-[2%] left-[35%] h-[15%] w-[15%] rounded-full bg-current" />
        <span className="absolute bottom-[15%] left-[60%] h-[12%] w-[12%] rounded-full bg-current" />
        <span className="absolute bottom-[34%] left-[17%] h-[9%] w-[9%] rounded-full bg-current opacity-75" />
      </span>
    );
  }

  if (state === "ALCOHOL") {
    return (
      <svg className={className} width={size} height={size} viewBox="0 0 48 48" fill="none" role="img" aria-label={config.label}>
        <title>{config.label}</title>
        <path d="M19 8h10M20 8v6l-4 5v20h16V19l-4-5V8" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" />
        <path d="M17 27h14M20 21h8" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" />
        <path d="M38 34c0 2.5-2 4-4 4s-4-1.5-4-4c0-2 4-7 4-7s4 5 4 7Z" stroke="currentColor" strokeWidth="1.7" />
      </svg>
    );
  }

  return <Icon className={className} size={size} strokeWidth={1.8} aria-label={config.label} title={config.label} />;
}