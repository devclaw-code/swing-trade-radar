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
    return <div className={`h-14 w-full rounded bg-white/5 ${className ?? ""}`} />;
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
  const stroke = up ? "#10b981" : "#f43f5e";
  const fill = up ? "rgba(16,185,129,0.12)" : "rgba(244,63,94,0.12)";
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
        strokeWidth={1.5}
        strokeLinejoin="round"
        strokeLinecap="round"
      />
    </svg>
  );
}
