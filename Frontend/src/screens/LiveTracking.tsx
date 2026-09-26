import { useState, useEffect } from "react";
import { ChevronDown, AlertTriangle } from "lucide-react";
import { getDevicePredictions } from "../api";
import { DEMO_PREDICTIONS, truncateConfidencePercent, type Device, type PredictionResult } from "../data";
import ThreatIcon from "../components/ThreatIcon";

const RESULT_COLOR: Record<string, string> = {
  "ALCOHOL": "#F4B942",
  "NARCOTIC PROXY": "#E05252",
};

const SCREENING_ANOMALIES = new Set(["ALCOHOL", "NARCOTIC PROXY"]);

function displayResult(result: string) {
  return result === "CAUTION" ? "WEATHER DRIFT" : result;
}

export default function LiveTracking({ theme, devices }: { theme: "dark" | "light"; devices: Device[] }) {
  const dark  = theme === "dark";
  const [selId, setSelId] = useState("DART-041");
  const [drop, setDrop]   = useState(false);
  const [time, setTime]   = useState(() => new Date().toLocaleTimeString("en-IN", { hour12: false }));
  const [livePredictions, setLivePredictions] = useState<PredictionResult[]>(() => DEMO_PREDICTIONS[selId] || []);

  const device = devices.find(d => d.id === selId);

  useEffect(() => {
    if (devices.length > 0 && !devices.some(d => d.id === selId)) {
      setSelId(devices[0].id);
    }
  }, [devices, selId]);

  useEffect(() => {
    if (!device) return;
    setLivePredictions(DEMO_PREDICTIONS[device.id] || []);
    let active = true;
    const refresh = () => getDevicePredictions(device.id).then(next => {
      if (active) setLivePredictions(next.length > 0 ? next : DEMO_PREDICTIONS[device.id] || []);
    }).catch(() => undefined);
    refresh();
    const interval = window.setInterval(refresh, 2000);
    return () => { active = false; window.clearInterval(interval); };
  }, [device?.id]);

  const screeningAnomalies = livePredictions.filter(prediction => SCREENING_ANOMALIES.has(prediction.displayResult || prediction.prediction || ""));
  const liveAnomaly = screeningAnomalies[0];
  const lastAnomaly = liveAnomaly
    ? { timestamp: liveAnomaly.timestamp, result: displayResult(liveAnomaly.displayResult || liveAnomaly.prediction || ""), confidence: liveAnomaly.confidence * 100 }
    : null;
  const anomalyColor = lastAnomaly ? RESULT_COLOR[lastAnomaly.result] || "#F4B942" : "#8C9199";

  useEffect(() => {
    const id = setInterval(() => {
      setTime(new Date().toLocaleTimeString("en-IN", { hour12: false }));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const cBg  = dark ? "bg-gunmetal"   : "bg-white";
  const text = dark ? "text-ivory"    : "text-obsidian";
  const muted= dark ? "text-warm-grey": "text-[#6F6A61]";
  const bdr  = dark ? "border-warm-grey/10" : "border-obsidian/8";
  const bg   = dark ? "bg-obsidian"   : "bg-[#F1EDE3]";

  if (!device) {
    return (
      <div className={`min-h-full ${bg} p-4 md:p-6`}>
        <div className={`panel ${cBg} p-10 text-center`}>
          <div className={`font-mono text-[10px] tracking-widest ${muted}`}>
            {devices.length === 0 ? "NO DEVICES AVAILABLE" : "SELECTED DEVICE NOT AVAILABLE"}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className={`min-h-full ${bg}`}>
      <div className="p-4 md:p-6 space-y-4 pb-20 md:pb-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className={`font-display text-[40px] md:text-[50px] tracking-widest leading-none ${text}`}>LIVE TRACKING</div>
            <div className={`font-mono text-[9.5px] tracking-widest uppercase mt-1 ${muted}`}>
              Real-time DART device monitoring // {time}
            </div>
          </div>

          {/* Device selector */}
          <div className="relative">
            <button onClick={() => setDrop(!drop)}
              className={`flex items-center gap-3 px-4 py-2.5 panel ${cBg} min-w-[200px]`}>
              <span className="w-2 h-2 rounded-full bg-signal-red blink flex-shrink-0" />
              <span className={`font-mono text-[10px] tracking-widest flex-1 text-left ${text}`}>{selId}</span>
              <ChevronDown className={`w-3.5 h-3.5 ${muted}`} />
            </button>
            {drop && (
              <div className={`absolute top-full right-0 mt-0.5 z-30 min-w-full border ${bdr} ${cBg} shadow-xl`}>
                {devices.map(d => {
                  const c = { ONLINE: "#3FB950", OFFLINE: "#8C9199", ALERT: "#E05252", WARNING: "#F4B942" }[d.status];
                  return (
                    <button key={d.id} onClick={() => { setSelId(d.id); setDrop(false); }}
                      className={`w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors
                        ${d.id === selId ? (dark ? "bg-charcoal" : "bg-[#F4F0E8]") : "hover:bg-signal-red/8"}`}>
                      <span className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: c }} />
                      <div>
                        <div className={`font-mono text-[10px] tracking-widest ${text}`}>{d.id}</div>
                        <div className={`font-mono text-[8.5px] ${muted}`}>{d.location}</div>
                      </div>
                    </button>
                  );
                })}
              </div>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          {/* ── Station Map ── */}
          <div className={`panel ${cBg}`}>
            <div className="h-[1px] bg-brass/25" />
            <div className={`px-4 py-2.5 border-b ${bdr} flex items-center justify-between`}>
              <div className="font-mono text-[9px] tracking-[.2em] uppercase text-brass">AREA MAP // POLICE STATION</div>
              <div className="flex items-center gap-1.5">
                <span className="w-1.5 h-1.5 rounded-full bg-brass blink" />
                <span className="font-mono text-[8.5px] text-brass">LIVE</span>
              </div>
            </div>
            <div className={`relative h-72 ${dark ? "bg-[#0A0B0D]" : "bg-[#E0DBD0]"} grid-bg overflow-hidden`}>
              {/* SVG station schematic */}
              <svg className="absolute inset-0 w-full h-full" viewBox="0 0 640 380" preserveAspectRatio="xMidYMid meet">
                <rect x="20" y="15" width="600" height="350" fill="none" stroke="#C49A4A" strokeWidth=".6" strokeOpacity=".15" />
                <rect x="60" y="55" width="500" height="55" fill="none" stroke="#C49A4A" strokeWidth=".7" strokeOpacity=".22" />
                <line x1="60" y1="72" x2="560" y2="72" stroke="#C49A4A" strokeWidth="1.8" strokeOpacity=".3" />
                <line x1="60" y1="94" x2="560" y2="94" stroke="#C49A4A" strokeWidth="1.8" strokeOpacity=".3" />
                {[80,110,140,170,200,230,260,290,320,350,380,410,440,470,500,530].map(x => (
                  <line key={x} x1={x} y1="69" x2={x} y2="97" stroke="#C49A4A" strokeWidth="1" strokeOpacity=".15" />
                ))}
                <text x="310" y="68" textAnchor="middle" fontSize="8" fill="#F4B942" fillOpacity=".5" fontFamily="JetBrains Mono,monospace" letterSpacing="1">NEAR KENDRIYA VIDYALAYA</text>
                <rect x="60" y="155" width="500" height="55" fill="none" stroke="#C49A4A" strokeWidth=".7" strokeOpacity=".22" />
                <line x1="60" y1="172" x2="560" y2="172" stroke="#C49A4A" strokeWidth="1.8" strokeOpacity=".3" />
                <line x1="60" y1="194" x2="560" y2="194" stroke="#C49A4A" strokeWidth="1.8" strokeOpacity=".3" />
                <text x="310" y="168" textAnchor="middle" fontSize="8" fill="#F4B942" fillOpacity=".5" fontFamily="JetBrains Mono,monospace" letterSpacing="1">SECTOR-10,11 DIVIDING ROAD</text>
                <rect x="20" y="140" width="65" height="95" fill="none" stroke="#C49A4A" strokeWidth=".5" strokeOpacity=".18" />
                <text x="52" y="175" textAnchor="middle" fontSize="7" fill="#C49A4A" fillOpacity=".4" fontFamily="JetBrains Mono,monospace">GATE 2</text>
                <rect x="400" y="265" width="160" height="70" fill="none" stroke="#C49A4A" strokeWidth=".5" strokeOpacity=".18" />
                <text x="480" y="285" textAnchor="middle" fontSize="7" fill="#F4B942" fillOpacity=".4" fontFamily="JetBrains Mono,monospace">NEAR MEDICAL COLLEGES</text>
                <rect x="20" y="15" width="600" height="350" fill={dark ? "#0D1013" : "#D9DDE1"} />
                <rect x="20" y="15" width="600" height="350" fill="none" stroke="#F4B942" strokeWidth="1" strokeOpacity=".35" />
                <path d="M35 112H605M35 218H605M178 25V350M382 25V350" stroke={dark ? "#292C30" : "#AEB5BC"} strokeWidth="22" />
                <path d="M35 112H605M35 218H605M178 25V350M382 25V350" stroke="#F4B942" strokeWidth="1" strokeDasharray="8 7" strokeOpacity=".65" />
                <rect x="218" y="242" width="126" height="68" fill={dark ? "#15171A" : "#EEF0F2"} stroke="#F4B942" strokeOpacity=".7" />
                <text x="281" y="270" textAnchor="middle" fontSize="7" fill="#F4B942" fontFamily="JetBrains Mono,monospace">AREA POLICE</text>
                <text x="281" y="281" textAnchor="middle" fontSize="7" fill="#F4B942" fontFamily="JetBrains Mono,monospace">STATION RESPONSE</text>
                <text x="314" y="105" textAnchor="middle" fontSize="7" fill={dark ? "#F5F5F5" : "#15171A"} fontFamily="JetBrains Mono,monospace">SECTOR-10,11 DIVIDING ROAD</text>
                <text x="592" y="43" textAnchor="end" fontSize="8" fill="#F4B942" fontFamily="JetBrains Mono,monospace">N</text>
                <path d="M592 49v18m0-18-4 6m4-6 4 6" stroke="#F4B942" strokeWidth="1.5" />
              </svg>

              {/* Selected device marker */}
              <div className="absolute transform -translate-x-1/2 -translate-y-1/2 z-10"
                style={{ left: `${device.mapX}%`, top: `${device.mapY}%` }}>
                <div className="relative">
                  <div className="w-4 h-4 rounded-full border-2 border-ivory z-10 relative"
                    style={{ background: device.lastResult === "NARCOTIC PROXY" ? "#E05252" : "#F4B942", boxShadow: `0 0 10px ${device.lastResult === "NARCOTIC PROXY" ? "#E05252" : "#F4B942"}80` }} />
                  <div className={`absolute inset-0 rounded-full ${device.lastResult === "NARCOTIC PROXY" ? "pulse-red" : "pulse-amber"}`} style={{ background: device.lastResult === "NARCOTIC PROXY" ? "#E05252" : "#F4B942" }} />
                </div>
                {/* Label */}
                <div className={`absolute left-5 top-0 whitespace-nowrap ${dark ? "bg-gunmetal" : "bg-white"} border border-warm-grey/20 px-2 py-1`}>
                  <div className={`font-mono text-[8.5px] tracking-widest ${text}`}>{device.id}</div>
                  <div className={`font-mono text-[7.5px] ${muted}`}>{device.location}</div>
                </div>
              </div>

              {/* Battery-only overlay */}
              <div className={`absolute bottom-3 left-3 px-3 py-2 ${dark ? "bg-charcoal/90" : "bg-white/90"} border ${bdr}`}>
                <div className={`font-mono text-[7.5px] tracking-widest uppercase ${muted} mb-1`}>BATTERY</div>
                <div className="font-mono text-[18px] leading-none font-medium"
                  style={{ color: device.battery > 50 ? "#20C878" : device.battery > 20 ? "#D99A27" : "#B3262E" }}>
                  {device.battery > 0 ? `${device.battery}%` : "—"}
                </div>
              </div>
            </div>
          </div>

          {/* ── Right column ── */}
          <div className="space-y-4">

            {/* Last anomaly detected */}
            {lastAnomaly && <div className={`panel ${cBg}`} style={{ borderTop: `2px solid ${anomalyColor}` }}>
              <div className="p-4">
                <div className="flex items-center gap-2.5 mb-3">
                  <AlertTriangle className="w-4 h-4 flex-shrink-0" style={{ color: anomalyColor }} />
                  <div className="font-mono text-[9px] tracking-[.2em] uppercase text-brass">LAST ANOMALY DETECTED</div>
                </div>

                <div className="flex items-center gap-3 mb-3" style={{ color: anomalyColor }}>
                  <ThreatIcon state={lastAnomaly.result} size={62} className="flex-shrink-0" />
                  <div className="font-display text-[44px] tracking-widest leading-none">
                    {lastAnomaly.result}
                  </div>
                </div>

                <div className="flex items-center gap-4 mb-3">
                  <div>
                    <div className={`font-mono text-[8px] tracking-widest uppercase ${muted} mb-0.5`}>CONFIDENCE</div>
                    <div className="font-mono text-[22px] leading-none font-medium" style={{ color: anomalyColor }}>
                      {truncateConfidencePercent(lastAnomaly.confidence)}%
                    </div>
                  </div>
                </div>

                {/* Confidence bar */}
                <div className={`h-1.5 w-full ${dark ? "bg-obsidian" : "bg-[#E4E0D7]"} mb-1`}>
                  <div className="h-full transition-all duration-700"
                    style={{ width: `${lastAnomaly.confidence}%`, background: anomalyColor }} />
                </div>
                <div className="flex justify-between">
                  <span className={`font-mono text-[7.5px] ${muted}`}>0%</span>
                  <span className={`font-mono text-[7.5px] ${muted}`}>100%</span>
                </div>

                <div className={`mt-3 pt-3 border-t ${bdr} font-mono text-[9px] tracking-widest ${muted}`}>
                  DEVICE: <span className="text-brass">{device.id}</span>
                  &nbsp;// LOCATION: <span className={text}>{device.location}</span>
                </div>
              </div>
            </div>}

            {/* Last 10 anomalies */}
            <div className={`panel ${cBg}`}>
              <div className="h-[1px] bg-signal-red/30" />
              <div className="p-4">
                <div className="font-mono text-[9px] tracking-[.2em] uppercase text-brass mb-3">
                  LAST 10 ANOMALIES
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className={`border-b ${bdr}`}>
                        {["TIME", "DETECTION TYPE", "CONF."].map(h => (
                          <th key={h} className={`text-left pb-2 font-mono text-[8px] tracking-widest ${muted}`}>{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {screeningAnomalies.map((a, i) => {
                        const result = displayResult(a.displayResult || a.prediction || "");
                        const c = RESULT_COLOR[result] || "#A8A39A";
                        return (
                          <tr key={i} className={`border-b ${bdr} last:border-0`}>
                            <td className="py-2 font-mono text-[9.5px] text-brass whitespace-nowrap">{a.timestamp}</td>
                              <td className="py-2 pr-3">
                                <div className="flex items-center gap-2" style={{ color: c }}>
                                <ThreatIcon state={result} size={18} className="flex-shrink-0" />
                              <span className="font-mono text-[8.5px] px-1.5 py-[2px] whitespace-nowrap"
                                style={{ background: `${c}20`, color: c, border: `1px solid ${c}40` }}>
                                {result}
                              </span>
                                </div>
                            </td>
                            <td className="py-2 font-mono text-[9.5px]" style={{ color: c }}>
                              {truncateConfidencePercent(a.confidence * 100)}%
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                  {screeningAnomalies.length === 0 && (
                    <div className={`py-6 text-center font-mono text-[9.5px] tracking-widest ${muted}`}>NO PREDICTIONS RECORDED</div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
