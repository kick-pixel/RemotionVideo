import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Audio, staticFile } from 'remotion';

// 片头限制在 5 秒（150 帧）内，动画节奏加快
export const IntroScene: React.FC<{
  themeTitle: string;
  themeSubject: string;
  audioPath: string;
}> = ({ themeSubject, audioPath }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Strip brackets and compute a smaller font size if string is very long
  const finalSubject = themeSubject.replace(/[《》]/g, '');
  const subjectFontSize = finalSubject.length > 14 ? 75 : finalSubject.length > 8 ? 90 : 120;

  // 1. 背景大字「今日对话」快速淡入
  const titleEntrance = spring({
    fps,
    frame,
    config: { damping: 20, stiffness: 100 },
  });

  // 2. 持续缓慢放大和拉开字间距作为动态水印
  const bgProgress = spring({
    fps,
    frame,
    config: { damping: 200, stiffness: 10 }, 
  });

  const titleScale   = interpolate(bgProgress, [0, 1], [1, 1.1]);
  const titleOpacity = interpolate(titleEntrance, [0, 1], [0, 0.08]); // 根据入场动画淡入
  const titleSpacing = interpolate(bgProgress, [0, 1], [0.05, 0.2]); // em

  // 3. 第二层副标题 — 在背景完全呈现后（0.8秒后）再优雅平滑升起
  const popInSubject = spring({
    fps,
    frame: frame - fps * 0.8,
    config: { damping: 14, stiffness: 150 },
  });

  const subjectScale   = interpolate(popInSubject, [0, 1], [0.8, 1]);
  const subjectOpacity = interpolate(popInSubject, [0, 1], [0, 1]);
  const subjectY       = interpolate(popInSubject, [0, 1], [60, 0]);

  // 轻微呼吸抖动
  const wobbleX = Math.sin(frame / 30) * 4;
  const wobbleY = Math.cos(frame / 20) * 4;

  return (
    <AbsoluteFill style={{ background: '#f5efe0', overflow: 'hidden' }}>
      {/* 斜纹背景 */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          backgroundImage: [
            'repeating-linear-gradient(45deg, transparent, transparent 36px, rgba(0,0,0,0.032) 36px, rgba(0,0,0,0.032) 37px)',
            'repeating-linear-gradient(135deg, transparent, transparent 36px, rgba(0,0,0,0.032) 36px, rgba(0,0,0,0.032) 37px)',
          ].join(', '),
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          pointerEvents: 'none',
          background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.07) 120%)',
        }}
      />

      <div
        style={{
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexDirection: 'column',
          position: 'relative',
        }}
      >
        {/* 背景大字「今日对话」*/}
        <div
          style={{
            position: 'absolute',
            fontSize: 180,
            fontWeight: 900,
            fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
            color: '#1a1817',
            transform: `scale(${titleScale}) translateY(${wobbleY}px) translateX(${wobbleX}px)`,
            opacity: titleOpacity,
            whiteSpace: 'normal',
            lineHeight: 1.1,
            wordBreak: 'keep-all',
            textAlign: 'center',
            width: '100vw',
            padding: '0 40px',
            letterSpacing: `${titleSpacing}em`,
            zIndex: 1,
          }}
        >
          今日对话
        </div>

        {/* 前景冲击副标题 */}
        {frame > fps * 0.4 && (
          <div
            style={{
              position: 'absolute',
              fontSize: subjectFontSize,
              fontWeight: 900,
              fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
              color: '#1a1817', // High contrast dark bold
              transform: `scale(${subjectScale}) translateY(${subjectY}px)`,
              opacity: subjectOpacity,
              whiteSpace: 'nowrap',
              zIndex: 2,
              filter: 'drop-shadow(0px 12px 24px rgba(0,0,0,0.1)) drop-shadow(0px 4px 8px rgba(0,0,0,0.05))',
              WebkitTextStroke: '2px rgba(255,255,255,0.5)',
            }}
          >
            {finalSubject}
          </div>
        )}
      </div>

      <Audio src={staticFile(audioPath)} />
    </AbsoluteFill>
  );
};
