"use client";

/**
 * recharts radar themed to the "Tierra Pixelada" palette — one <Radar> series per
 * selected candidate, drawn in the brand colors over coffee-colored grid/axes.
 */

import {
  Legend,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart as RechartsRadar,
  ResponsiveContainer,
} from "recharts";

import { CANDIDATO_LABEL } from "@/lib/constants";
import type { RadarRow } from "@/lib/radar";

export interface RadarChartProps {
  rows: RadarRow[];
  /** candidato ids to draw a series for. */
  candidatos: string[];
}

const COFFEE = "#2d1b10";
const MONO = "var(--font-jetbrains-mono), monospace";

/** Stable per-candidate colors drawn from the Colombian palette. */
const SERIES_COLOR: Record<string, string> = {
  cepeda: "#bf0229", // scarlet
  valencia: "#3959b0", // navy
  fajardo: "#f0c100", // gold
  lopez: "#00a86b", // emerald
  espriella: "#735c00", // primary
};

export function RadarChart({ rows, candidatos }: RadarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={420}>
      <RechartsRadar data={rows} outerRadius="72%">
        <PolarGrid stroke={COFFEE} strokeOpacity={0.35} />
        <PolarAngleAxis
          dataKey="eje"
          tick={{ fill: COFFEE, fontFamily: MONO, fontSize: 12 }}
        />
        <PolarRadiusAxis
          domain={[0, 5]}
          tickCount={6}
          tick={{ fill: COFFEE, fontFamily: MONO, fontSize: 10 }}
          axisLine={false}
        />
        <Legend
          wrapperStyle={{ fontFamily: MONO, fontSize: 12, textTransform: "uppercase" }}
        />
        {candidatos.map((id) => {
          const color = SERIES_COLOR[id] ?? COFFEE;
          return (
            <Radar
              key={id}
              name={CANDIDATO_LABEL[id] ?? id}
              dataKey={id}
              stroke={color}
              strokeWidth={2}
              fill={color}
              fillOpacity={0.25}
            />
          );
        })}
      </RechartsRadar>
    </ResponsiveContainer>
  );
}
