import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Audio, staticFile } from 'remotion';

// 片头限制在 5 秒（150 帧）内，动画节奏加快
export const IntroScene: React.FC<{
  themeTitle: string;
  themeSubject: string;
  audioPath: string;
}> = ({ themeTitle, themeSubject, audioPath }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 第一层大字「今日对话」— 弹入速度极快（0~15 帧完成）
  const popInTitle = spring({
    fps,
    frame,
    config: { damping: 14, stiffness: 300 }, // 更高 stiffness，更快弹入
  });

  // 0.4 秒（12 帧）后开始褪色放大成水印
  const fadeBackProgress = spring({
    fps,
    frame: frame - fps * 0.4,
    config: { damping: 18, stiffness: 200 },
  });

  const titleScale   = interpolate(popInTitle, [0, 1], [0, 1]) + interpolate(fadeBackProgress, [0, 1], [0, 0.4]);
  const titleOpacity = interpolate(fadeBackProgress, [0, 1], [1, 0.1]);
  const titleY       = interpolate(fadeBackProgress, [0, 1], [0, -50]);

  // 第二层副标题「《xxx》」— 0.5 秒后冲击弹出
  const popInSubject = spring({
    fps,
    frame: frame - fps * 0.5,
    config: { damping: 10, stiffness: 250 },
  });

  const subjectScale   = interpolate(popInSubject, [0, 1], [2.2, 1]);
  const subjectOpacity = interpolate(popInSubject, [0, 1], [0, 1]);

  // 轻微呼吸抖动
  const wobbleX = Math.sin(frame / 20) * 8;
  const wobbleY = Math.cos(frame / 14) * 8;

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
            fontSize: 220,
            fontWeight: 900,
            fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
            color: '#2a2118',
            transform: `scale(${titleScale}) translateY(${titleY + wobbleY}px) translateX(${wobbleX}px)`,
            opacity: titleOpacity,
            whiteSpace: 'nowrap',
            letterSpacing: '0.05em',
            zIndex: 1,
          }}
        >
          {themeTitle}
        </div>

        {/* 前景冲击副标题 */}
        {frame > fps * 0.4 && (
          <div
            style={{
              position: 'absolute',
              fontSize: 140,
              fontWeight: 900,
              fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
              color: '#f59d0b',
              transform: `scale(${subjectScale})`,
              opacity: subjectOpacity,
              whiteSpace: 'nowrap',
              zIndex: 2,
              filter: 'drop-shadow(0px 16px 24px rgba(245,157,11,0.45))',
              WebkitTextStroke: '5px #ffffff',
            }}
          >
            {themeSubject}
          </div>
        )}
      </div>

      <Audio src={staticFile(audioPath)} />
    </AbsoluteFill>
  );
};
