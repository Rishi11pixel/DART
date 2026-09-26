export type DeviceStatus = "ONLINE" | "OFFLINE" | "ALERT" | "WARNING";
export type ScanResult  = "SAFE" | "CAUTION" | "ALCOHOL" | "NARCOTIC PROXY";
export type LogLevel    = "ALERT" | "WARNING" | "SUCCESS" | "INFO";

export interface SensorReading {
  device_id: string;
  timestamp: string | number;
  temperature: number;
  humidity: number;
  mq2: number;
  mq3: number;
  mq135: number;
  sen0567: number;
  battery?: number;
  signal?: number;
  source_status?: string;
  test_object?: string;
}

export interface PredictionResult {
  id: string;
  window_id: string;
  timestamp: string;
  device_id: string;
  status: "SAFE" | "ALERT" | "ERROR";
  prediction: string | null;
  displayResult?: ScanResult;
  confidence: number;
  probabilities: Record<string, number>;
  features: Record<string, number>;
}

export interface Device {
  id: string;
  location: string;
  platform: string;
  status: DeviceStatus;
  battery: number | null;
  signal: number | null;
  health: number | null;
  lastSync: string | null;
  operatingTime: string | null;
  lastResult: ScanResult;
  confidence: number;
  mapX: number; // percent positions on SVG viewbox 0-100
  mapY: number;
  latestReading?: SensorReading | null;
  latestPrediction?: PredictionResult | null;
}

export interface LogEntry {
  timestamp: string;
  device: string;
  event: string;
  location: string;
  level: LogLevel;
}

export interface Incident {
  id: string;
  type: ScanResult;
  location: string;
  platform: string;
  confidence: number;
  status: "RESPONSE DISPATCHED" | "TEAM NOTIFIED" | "RESOLVED" | "ACKNOWLEDGED";
  team: string;
  time: string;
  device: string;
  latestReading?: SensorReading | null;
}

const demoReading = (device_id: string, timestamp: string, temperature: number, humidity: number, mq2: number, mq3: number, mq135: number, battery: number, signal: number): SensorReading => ({
  device_id,
  timestamp,
  temperature,
  humidity,
  mq2,
  mq3,
  mq135,
  sen0567: 0,
  battery,
  signal,
  source_status: "DEMO",
});

export const DEMO_DEVICES: Device[] = [
  {
    id: "DART-032",
    location: "Near Kendriya Vidyalaya",
    platform: "Near Kendriya Vidyalaya",
    status: "ONLINE",
    battery: 86,
    signal: 94,
    health: 98,
    lastSync: "2026-09-20 14:32:08",
    operatingTime: "18h 42m",
    lastResult: "SAFE",
    confidence: 0.99,
    mapX: 43,
    mapY: 27,
    latestReading: demoReading("DART-032", "14:32:08", 27.4, 48.2, 112, 38, 146, 86, 94),
  },
  {
    id: "DART-041",
    location: "Sector-10,11 Dividing Road",
    platform: "Sector-10,11 Dividing Road",
    status: "WARNING",
    battery: 71,
    signal: 88,
    health: 93,
    lastSync: "2026-09-20 14:31:52",
    operatingTime: "16h 09m",
    lastResult: "ALCOHOL",
    confidence: 0.91,
    mapX: 58,
    mapY: 51,
    latestReading: demoReading("DART-041", "14:31:52", 28.1, 51.8, 286, 118, 174, 71, 88),
  },
  {
    id: "DART-017",
    location: "Near Medical Colleges",
    platform: "Near Medical Colleges",
    status: "ALERT",
    battery: 64,
    signal: 91,
    health: 89,
    lastSync: "2026-09-20 14:31:36",
    operatingTime: "12h 55m",
    lastResult: "NARCOTIC PROXY",
    confidence: 0.88,
    mapX: 76,
    mapY: 76,
    latestReading: demoReading("DART-017", "14:31:36", 27.8, 49.4, 164, 364, 238, 64, 91),
  },
  {
    id: "DART-006",
    location: "Area Police Station Response",
    platform: "Area Police Station Response",
    status: "ONLINE",
    battery: 93,
    signal: 97,
    health: 100,
    lastSync: "2026-09-20 14:32:02",
    operatingTime: "21h 18m",
    lastResult: "SAFE",
    confidence: 0.98,
    mapX: 45,
    mapY: 78,
    latestReading: demoReading("DART-006", "14:32:02", 26.9, 46.7, 108, 34, 132, 93, 97),
  },
  {
    id: "DART-028",
    location: "Sector-10 Market Approach",
    platform: "Sector-10 Market Approach",
    status: "OFFLINE",
    battery: 18,
    signal: null,
    health: 61,
    lastSync: "2026-09-20 13:58:11",
    operatingTime: "09h 04m",
    lastResult: "CAUTION",
    confidence: 0.68,
    mapX: 22,
    mapY: 61,
    latestReading: null,
  },
];

export const DEMO_INCIDENTS: Incident[] = [
  {
    id: "INC-2409-017",
    type: "NARCOTIC PROXY",
    location: "Near Medical Colleges",
    platform: "Near Medical Colleges",
    confidence: 0.88,
    status: "RESPONSE DISPATCHED",
    team: "Area Police Response Team",
    time: "14:31:36",
    device: "DART-017",
    latestReading: DEMO_DEVICES[2].latestReading,
  },
  {
    id: "INC-2409-041",
    type: "ALCOHOL",
    location: "Sector-10,11 Dividing Road",
    platform: "Sector-10,11 Dividing Road",
    confidence: 0.91,
    status: "TEAM NOTIFIED",
    team: "Area Police Response Team",
    time: "14:31:52",
    device: "DART-041",
    latestReading: DEMO_DEVICES[1].latestReading,
  },
];

export const DEMO_LOGS: LogEntry[] = [
  { timestamp: "14:32:08", device: "DART-032", event: "Breath sample cleared - no alcohol or drug influence detected", location: "Near Kendriya Vidyalaya", level: "SUCCESS" },
  { timestamp: "14:32:02", device: "DART-006", event: "Heartbeat and sensor calibration confirmed", location: "Area Police Station Response", level: "INFO" },
  { timestamp: "14:31:52", device: "DART-041", event: "Alcohol influence signal above screening threshold", location: "Sector-10,11 Dividing Road", level: "WARNING" },
  { timestamp: "14:31:36", device: "DART-017", event: "Drug influence pattern requires field response", location: "Near Medical Colleges", level: "ALERT" },
  { timestamp: "13:58:11", device: "DART-028", event: "Device heartbeat lost - last reading retained", location: "Sector-10 Market Approach", level: "WARNING" },
  { timestamp: "13:44:27", device: "DART-032", event: "MQ-2, MQ-3 and MQ-135 sensors warmed and ready", location: "Near Kendriya Vidyalaya", level: "INFO" },
];

export const DEMO_PREDICTIONS: Record<string, PredictionResult[]> = {
  "DART-032": [
    { id: "P-032-01", window_id: "W-032-01", timestamp: "14:32:08", device_id: "DART-032", status: "SAFE", prediction: "SAFE", displayResult: "SAFE", confidence: 0.99, probabilities: { SAFE: 0.99 }, features: {} },
    { id: "P-032-02", window_id: "W-032-02", timestamp: "14:28:08", device_id: "DART-032", status: "SAFE", prediction: "SAFE", displayResult: "SAFE", confidence: 0.98, probabilities: { SAFE: 0.98 }, features: {} },
  ],
  "DART-041": [
    { id: "P-041-01", window_id: "W-041-01", timestamp: "14:31:52", device_id: "DART-041", status: "ALERT", prediction: "ALCOHOL", displayResult: "ALCOHOL", confidence: 0.91, probabilities: { ALCOHOL: 0.91 }, features: {} },
    { id: "P-041-02", window_id: "W-041-02", timestamp: "14:27:52", device_id: "DART-041", status: "ALERT", prediction: "ALCOHOL", displayResult: "ALCOHOL", confidence: 0.86, probabilities: { ALCOHOL: 0.86 }, features: {} },
  ],
  "DART-017": [
    { id: "P-017-01", window_id: "W-017-01", timestamp: "14:31:36", device_id: "DART-017", status: "ALERT", prediction: "NARCOTIC PROXY", displayResult: "NARCOTIC PROXY", confidence: 0.88, probabilities: { "NARCOTIC PROXY": 0.88 }, features: {} },
  ],
  "DART-006": [
    { id: "P-006-01", window_id: "W-006-01", timestamp: "14:32:02", device_id: "DART-006", status: "SAFE", prediction: "SAFE", displayResult: "SAFE", confidence: 0.98, probabilities: { SAFE: 0.98 }, features: {} },
  ],
};

export function truncateConfidencePercent(value: number): string {
  return (Math.trunc(value * 100) / 100).toFixed(2);
}

export const DETECTION_DIST = [
  { name:"SAFE",           value:847, color:"#20C878" },
  { name:"CAUTION",        value:43,  color:"#D99A27" },
  { name:"NARCOTIC PROXY", value:12,  color:"#B3262E" },
];
