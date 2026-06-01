interface SparklineProps {
  values: number[];
  width?: number;
  height?: number;
  className?: string;
  positive?: boolean;
}

export function Sparkline({
  values,
  width = 320,
  height = 56,
  className,
  positive,
}: SparklineProps) {
  if (!values || values.length < 2) {
    return <div className={`h-14 w-full rounded bg-slate-800 ${className ?? ""}`} />;
  }
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;
  const stepX = width / (values.length - 1);
  const points = values
    .map((v, i) => {
      const x = i * stepX;
      const y = height - ((v - min) / span) * (height - 4) - 2;
      return `${x.toFixed(1)},${y.toFixed(1)}`;
    })
    .join(" ");
  const last = values[values.length - 1];
  const first = values[0];
  const up = positive ?? last >= first;
  // Saturated emerald-400 / rose-400, NOT washed out
  const stroke = up ? "#34d399" : "#fb7185";
  const fill = up ? "rgba(52,211,153,0.18)" : "rgba(251,113,133,0.18)";
  const areaPath = `M 0,${height} L ${points.replace(/ /g, " L ")} L ${width},${height} Z`;

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      preserveAspectRatio="none"
      className={`h-14 w-full ${className ?? ""}`}
      role="img"
      aria-label="60-day price sparkline"
    >
      <path d={areaPath} fill={fill} />
      <polyline
        points={points}
        fill="none"
        stroke={stroke}
        strokeWidth={1.75}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
