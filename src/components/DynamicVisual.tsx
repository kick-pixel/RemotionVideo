import React from 'react';
import { useCurrentFrame, useVideoConfig, spring, interpolate } from 'remotion';

// Utility for continuous floating animation
const useFloat = (offsetY: number, speed: number = 20) => {
  const frame = useCurrentFrame();
  return Math.sin(frame / speed) * offsetY;
};

// ── 1. Flow Visual (Connected nodes) ──
const FlowVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const safeLabels = [...labels, '客户端', '服务端', 'DB'];

  return (
    <div className="flex items-center gap-6 relative">
      <div className="absolute w-full h-1 bg-[#dcd4c3] top-1/2 -translate-y-1/2 -z-10" />
      <div
        className="absolute w-1/3 h-1 bg-[#c8b89a] top-1/2 -translate-y-1/2 -z-10 shadow-[0_0_15px_#c8b89a]"
        style={{ left: `${(frame * 2) % 150 - 50}%` }}
      />
      {[0, 1, 2].map((i) => {
        const floatY = Math.sin((frame + i * 20) / (20 + i * 5)) * 10;
        const nodeIn = spring({ fps, frame: frame - i * 8, config: { damping: 11, stiffness: 180 } });
        return (
          <div
            key={i}
            className="flex flex-col items-center justify-center p-5 border-4 border-[#262322] bg-[#f5efe0] rounded-xl relative shadow-xl min-w-[110px]"
            style={{ transform: `translateY(${floatY}px) scale(${interpolate(nodeIn, [0, 1], [0.5, 1])})`, opacity: nodeIn }}
          >
            <div
              className="absolute inset-0 border-2 border-[#c8b89a] rounded-lg"
              style={{
                transform: `scale(${1 + Math.max(0, Math.sin(frame / 10 - i) * 0.15)})`,
                opacity: 0.2 + Math.max(0, Math.sin(frame / 15 - i) * 0.4),
              }}
            />
            <span className="text-xl font-bold text-[#262322] uppercase tracking-wider relative z-10 w-full text-center">
              {safeLabels[i].substring(0, 6)}
            </span>
          </div>
        );
      })}
    </div>
  );
};

// ── 2. Database Visual (Stacked Disks) ──
const DatabaseVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const mainLabel = labels[0] || 'DATA';
  const subLabel = labels[1] || 'STORE';
  const floatY = useFloat(15, 25);
  const scanY = (Math.sin(frame / 15) + 1) * 60;

  return (
    <div className="relative flex flex-col items-center justify-center h-64 mt-12" style={{ transform: `translateY(${floatY}px) scale(1.3)` }}>
      <div className="absolute w-[300px] h-[6px] bg-[#c8b89a] z-20 shadow-[0_0_25px_#c8b89a] rounded-full opacity-80" style={{ top: `${scanY}px` }} />
      {[0, 1, 2].map((i) => (
        <div key={i} className="w-[280px] h-24 border-[6px] border-[#262322] bg-[#f5efe0] rounded-[50%] flex items-center justify-center absolute shadow-[0_12px_0_#dcd4c3]" style={{ top: i * 55, zIndex: 10 - i }} />
      ))}
      <div className="absolute -left-32 -top-10 bg-[#262322] text-[#f5efe0] px-6 py-3 rounded-lg shadow-xl z-30 transform -rotate-6 shadow-[0_10px_0_#1a1817]">
        <span className="font-black text-3xl tracking-wide">{mainLabel}</span>
      </div>
      <div className="absolute -right-32 bottom-20 bg-[#c8b89a] text-[#262322] px-6 py-3 rounded-lg shadow-xl z-30 transform rotate-6 border-2 border-[#262322]">
        <span className="font-black text-3xl tracking-wide">{subLabel}</span>
      </div>
    </div>
  );
};

// ── 3. Speed Visual (Dashboard/Speedometer) ──
const SpeedVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const leftLabel = labels[0] || 'OLD';
  const rightLabel = labels[1] || 'NEW';
  const rotate = Math.sin(frame / 10) * 70;
  const floatY = useFloat(8, 25);

  return (
    <div className="relative flex flex-col items-center justify-center w-64 h-64 mt-20" style={{ transform: `translateY(${floatY}px)` }}>
      <div className="absolute inset-0 border-[16px] border-[#dcd4c3] rounded-full shadow-inner" style={{ borderBottomColor: 'transparent', transform: 'rotate(45deg)' }} />
      <div className="absolute inset-0 border-[16px] border-[#c8b89a] rounded-full opacity-60" style={{ borderBottomColor: 'transparent', borderRightColor: 'transparent', transform: 'rotate(-45deg)' }} />
      <div className="absolute top-1/2 left-1/2 w-2 h-32 -mt-32 -ml-1 origin-bottom" style={{ transform: `rotate(${rotate}deg)` }}>
        <div className="w-full h-full bg-[#262322] rounded-full shadow-lg" />
      </div>
      <div className="w-12 h-12 bg-[#262322] rounded-full absolute top-1/2 left-1/2 -mt-6 -ml-6 z-10 border-4 border-[#f5efe0] shadow-xl" />
      <div className="absolute -left-[140px] bottom-10 bg-[#262322] text-[#f5efe0] px-5 py-2 rounded-lg shadow-xl font-black text-xl border-b-4 border-black">{leftLabel}</div>
      <div className="absolute -right-[140px] bottom-10 bg-[#c8b89a] text-[#262322] px-5 py-2 rounded-lg shadow-xl font-black text-xl border-b-4 border-[#a5977d]">{rightLabel}</div>
    </div>
  );
};

// ── 4. Code Visual (Brackets typing) ──
const CodeVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const label = labels[0] || 'Code()';
  const floatY = useFloat(10, 30);

  return (
    <div className="relative flex flex-col items-center" style={{ transform: `translateY(${floatY}px)` }}>
      <div className="flex font-mono font-black tracking-tighter" style={{ fontSize: '100px' }}>
        <span className="text-[#c8b89a] mr-4">&lt;</span>
        <span className="text-[#262322]">{label}</span>
        <span className="text-[#c8b89a] ml-4">/&gt;</span>
      </div>
      {labels[1] && (
        <div className="bg-[#262322] text-[#f5efe0] text-2xl font-black px-6 py-2 mt-4 rounded-full tracking-widest uppercase">
          {labels[1]}
        </div>
      )}
    </div>
  );
};

// ── 5. Compare Visual (Side-by-side contrast) ──
const CompareVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const leftLabel = labels[0] || '旧方案';
  const rightLabel = labels[1] || '新方案';
  const leftSubLabel = labels[2] || '';

  const leftIn = spring({ fps, frame: frame - 5, config: { damping: 11, stiffness: 180 } });
  const rightIn = spring({ fps, frame: frame - 15, config: { damping: 11, stiffness: 180 } });
  const dividerIn = spring({ fps, frame: frame - 10, config: { damping: 15, stiffness: 220 } });

  const pulse = 1 + Math.sin(frame / 12) * 0.03;
  const floatY = useFloat(12, 22);

  return (
    <div className="flex items-stretch gap-0 relative h-52 w-[480px]" style={{ transform: `translateY(${floatY}px)` }}>
      {/* Left card — old/slow */}
      <div
        className="flex-1 flex flex-col items-center justify-center bg-[#262322] text-[#f5efe0] rounded-l-2xl p-6 shadow-xl"
        style={{ transform: `translateX(${interpolate(leftIn, [0, 1], [-80, 0])}px) scale(${interpolate(leftIn, [0, 1], [0.8, 1])})`, opacity: leftIn }}
      >
        <span className="text-5xl mb-2">⚠️</span>
        <span className="font-black text-2xl tracking-wide text-center">{leftLabel}</span>
        {leftSubLabel && <span className="text-lg mt-1 opacity-60">{leftSubLabel}</span>}
      </div>

      {/* Divider VS */}
      <div
        className="w-16 flex items-center justify-center z-10 bg-[#f5efe0] shadow-xl border-x-4 border-[#dcd4c3]"
        style={{ transform: `scaleY(${dividerIn})` }}
      >
        <span className="font-black text-2xl text-[#c8b89a] rotate-90">VS</span>
      </div>

      {/* Right card — new/fast */}
      <div
        className="flex-1 flex flex-col items-center justify-center bg-[#c8b89a] text-[#262322] rounded-r-2xl p-6 shadow-xl"
        style={{
          transform: `translateX(${interpolate(rightIn, [0, 1], [80, 0])}px) scale(${interpolate(rightIn, [0, 1], [0.8, pulse])})`,
          opacity: rightIn,
        }}
      >
        <span className="text-5xl mb-2">✅</span>
        <span className="font-black text-2xl tracking-wide text-center">{rightLabel}</span>
      </div>
    </div>
  );
};

// ── 6. Layers Visual (Tech stack layers) ──
const LayersVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const safeLabels = [...labels, '前端', '后端', '数据库'];
  const colors = ['#c8b89a', '#a5977d', '#262322'];
  const textColors = ['#262322', '#262322', '#f5efe0'];

  return (
    <div className="flex flex-col-reverse items-center gap-2 mt-8" style={{ perspective: '600px' }}>
      {[0, 1, 2].map((i) => {
        const layerIn = spring({ fps, frame: frame - i * 10, config: { damping: 11, stiffness: 160 } });
        const floatY = Math.sin((frame + i * 30) / 25) * 5;
        const width = 360 - i * 40;
        return (
          <div
            key={i}
            className="flex items-center justify-center rounded-xl shadow-xl font-black text-2xl tracking-wide border-4 border-[#262322]"
            style={{
              width,
              height: 70,
              background: colors[i],
              color: textColors[i],
              transform: `translateY(${floatY + interpolate(layerIn, [0, 1], [60, 0])}px) rotateX(${interpolate(layerIn, [0, 1], [30, 0])}deg)`,
              opacity: layerIn,
              zIndex: i,
            }}
          >
            {safeLabels[i]}
          </div>
        );
      })}
    </div>
  );
};

// ── 7. Tree Visual (Parent-child branching) ──
const TreeVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const rootLabel = labels[0] || 'Root';
  const leftLabel = labels[1] || 'Child A';
  const rightLabel = labels[2] || 'Child B';

  const rootIn = spring({ fps, frame, config: { damping: 11, stiffness: 180 } });
  const treeIn = spring({ fps, frame: frame - 15, config: { damping: 11, stiffness: 160 } });
  const linesIn = spring({ fps, frame: frame - 8, config: { damping: 15, stiffness: 140 } });

  const floatY = useFloat(10, 28);

  return (
    <div className="relative flex flex-col items-center" style={{ width: 400, height: 260, transform: `translateY(${floatY}px)` }}>
      {/* Root node */}
      <div
        className="bg-[#262322] text-[#f5efe0] font-black text-2xl px-8 py-4 rounded-2xl shadow-xl border-4 border-[#262322] z-10"
        style={{ transform: `scale(${rootIn})`, opacity: rootIn }}
      >
        {rootLabel}
      </div>

      {/* SVG connecting lines */}
      <svg className="absolute top-[68px] left-0 w-full" height="80" style={{ opacity: linesIn }}>
        <line x1="200" y1="0" x2="80" y2="70" stroke="#c8b89a" strokeWidth="4" strokeDasharray="8 4" />
        <line x1="200" y1="0" x2="320" y2="70" stroke="#c8b89a" strokeWidth="4" strokeDasharray="8 4" />
      </svg>

      {/* Child nodes */}
      <div className="flex gap-12 mt-20">
        {[leftLabel, rightLabel].map((label, i) => (
          <div
            key={i}
            className="bg-[#c8b89a] text-[#262322] font-black text-xl px-6 py-4 rounded-2xl shadow-lg border-4 border-[#262322]"
            style={{
              transform: `translateX(${interpolate(treeIn, [0, 1], [i === 0 ? -40 : 40, 0])}px) scale(${treeIn})`,
              opacity: treeIn,
            }}
          >
            {label}
          </div>
        ))}
      </div>
    </div>
  );
};

// ── 8. Timeline Visual (Horizontal time sequence) ──
const TimelineVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const safeLabels = [...labels, 'Step 1', 'Step 2', 'Step 3'];

  return (
    <div className="relative flex items-center" style={{ width: 460, height: 160 }}>
      {/* Baseline */}
      <div className="absolute top-1/2 left-4 right-4 h-1 bg-[#dcd4c3]" style={{ transform: 'translateY(-50%)' }} />

      {[0, 1, 2].map((i) => {
        const nodeIn = spring({ fps, frame: frame - i * 12, config: { damping: 12, stiffness: 200 } });
        const pulse = 1 + Math.max(0, Math.sin((frame - i * 12) / 8) * 0.2) * (nodeIn > 0.9 ? 1 : 0);
        const x = 80 + i * 150;
        const labelTop = i % 2 === 0; // Alternate label position

        return (
          <div key={i} className="absolute flex flex-col items-center" style={{ left: x - 28, top: '50%', transform: 'translateY(-50%)' }}>
            {labelTop && (
              <div
                className="mb-3 bg-[#262322] text-[#f5efe0] font-black text-lg px-4 py-2 rounded-lg shadow-md"
                style={{ transform: `translateY(${interpolate(nodeIn, [0, 1], [-20, -50])}px)`, opacity: nodeIn }}
              >
                {safeLabels[i]}
              </div>
            )}
            {/* Pulse ring */}
            <div
              className="absolute w-14 h-14 bg-[#c8b89a] rounded-full opacity-20"
              style={{ transform: `scale(${pulse})` }}
            />
            <div
              className="w-10 h-10 bg-[#262322] rounded-full border-4 border-[#c8b89a] z-10"
              style={{ transform: `scale(${nodeIn})`, opacity: nodeIn }}
            />
            {!labelTop && (
              <div
                className="mt-3 bg-[#c8b89a] text-[#262322] font-black text-lg px-4 py-2 rounded-lg shadow-md"
                style={{ transform: `translateY(${interpolate(nodeIn, [0, 1], [20, 50])}px)`, opacity: nodeIn }}
              >
                {safeLabels[i]}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
};

// ── 9. Lock Visual (Security/Auth concept) ──
const LockVisual: React.FC<{ labels: string[] }> = ({ labels }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const mainLabel = labels[0] || 'TOKEN';
  const subLabel = labels[1] || 'SECURE';

  const lockIn = spring({ fps, frame, config: { damping: 14, stiffness: 120 } });
  const orbit1Angle = (frame / 30) * Math.PI * 2;
  const orbit2Angle = -(frame / 20) * Math.PI * 2;

  const orb1x = Math.cos(orbit1Angle) * 100;
  const orb1y = Math.sin(orbit1Angle) * 45;
  const orb2x = Math.cos(orbit2Angle) * 130;
  const orb2y = Math.sin(orbit2Angle) * 55;

  return (
    <div
      className="relative flex items-center justify-center"
      style={{ width: 320, height: 280, transform: `scale(${lockIn})`, opacity: lockIn }}
    >
      {/* Orbit rings */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="absolute w-[240px] h-[110px] border-4 border-dashed border-[#dcd4c3] rounded-full opacity-60" style={{ transform: 'rotateX(60deg)' }} />
        <div className="absolute w-[300px] h-[135px] border-4 border-dashed border-[#c8b89a] rounded-full opacity-40" style={{ transform: 'rotateX(60deg)' }} />
      </div>

      {/* Orbiting dots */}
      <div className="absolute w-5 h-5 bg-[#c8b89a] rounded-full shadow-lg" style={{ transform: `translate(${orb1x}px, ${orb1y}px)` }} />
      <div className="absolute w-4 h-4 bg-[#262322] rounded-full shadow-lg" style={{ transform: `translate(${orb2x}px, ${orb2y}px)` }} />

      {/* Lock body */}
      <div className="relative z-10 flex flex-col items-center">
        {/* Lock shackle */}
        <div className="w-24 h-14 border-[8px] border-[#262322] rounded-t-full border-b-0 mb-0" style={{ marginBottom: '-4px' }} />
        {/* Lock body */}
        <div className="w-32 h-28 bg-[#262322] rounded-2xl flex items-center justify-center shadow-2xl border-b-8 border-[#1a1817]">
          <div className="flex flex-col items-center">
            <div className="w-8 h-8 bg-[#c8b89a] rounded-full mb-1 shadow-inner" />
            <span className="text-[#f5efe0] font-black text-lg tracking-widest">{mainLabel}</span>
          </div>
        </div>
      </div>

      {/* Sub label */}
      <div
        className="absolute -bottom-4 bg-[#c8b89a] text-[#262322] font-black text-xl px-6 py-2 rounded-full shadow-xl border-4 border-[#262322]"
        style={{ transform: `translateY(${interpolate(lockIn, [0, 1], [20, 0])}px)` }}
      >
        {subLabel}
      </div>
    </div>
  );
};

// ── Root Wrapper ──
export const DynamicVisual: React.FC<{
  type?: string;
  labels?: string[];
}> = ({ type = 'flow', labels = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const entrance = spring({
    fps,
    frame: frame - 10,
    config: { damping: 14, stiffness: 120 },
  });

  const floatY = Math.sin(frame / 25) * 8;
  const scale = interpolate(entrance, [0, 1], [0.8, 1.3]);
  const opacity = interpolate(entrance, [0, 1], [0, 1]);

  const style: React.CSSProperties = {
    position: 'absolute',
    bottom: 120,
    right: 140,
    width: 600,
    height: 400,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    transform: `translate(${floatY}px, ${floatY * 0.5}px) scale(${scale})`,
    opacity,
  };

  let Content: React.FC<{ labels: string[] }> = FlowVisual;
  if (type === 'database') Content = DatabaseVisual;
  else if (type === 'speed') Content = SpeedVisual;
  else if (type === 'code') Content = CodeVisual;
  else if (type === 'compare') Content = CompareVisual;
  else if (type === 'layers') Content = LayersVisual;
  else if (type === 'tree') Content = TreeVisual;
  else if (type === 'timeline') Content = TimelineVisual;
  else if (type === 'lock') Content = LockVisual;

  return (
    <div style={style}>
      <Content labels={labels} />
    </div>
  );
};
