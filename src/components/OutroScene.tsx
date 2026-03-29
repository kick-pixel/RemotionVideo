import React from 'react';
import { AbsoluteFill, spring, useCurrentFrame, useVideoConfig, interpolate, Audio, staticFile } from 'remotion';
import { Character } from './Character';

// 片尾限制在 5 秒（150 帧）内
export const OutroScene: React.FC<{
  summaryDisplay: string;
  audioPath: string;
}> = ({ summaryDisplay, audioPath }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 整体淡入（更快）
  const opacity = spring({
    fps,
    frame,
    config: { damping: 20, stiffness: 200 },
  });

  // 人物从上方滑入，定位在左上角
  const charSlide = spring({
    fps,
    frame: frame - 3,
    config: { damping: 18, stiffness: 200 },
  });
  const charY = interpolate(charSlide, [0, 1], [-200, 0]);

  // 文字条目（仅取前 3 条，防止溢出）
  const bullets = summaryDisplay.split('\n').filter((v) => v.trim()).slice(0, 3);

  // 底部横幅飞入（缩短延迟）
  const bannerSlide = spring({
    fps,
    frame: frame - fps * 0.8, // 0.8 秒后弹出（原 1.5 秒）
    config: { damping: 18, stiffness: 180 },
  });
  const bannerY = interpolate(bannerSlide, [0, 1], [150, 0]);

  return (
    <AbsoluteFill style={{ background: '#f5efe0', overflow: 'hidden', opacity }}>
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

      {/* ── 人物 (答题角色)：右上角 ── */}
      <div
        style={{
          position: 'absolute',
          top: 20,
          right: 20,
          transform: `translateY(${charY}px)`,
          zIndex: 3,
        }}
      >
        <Character type="answer" />
      </div>

      {/* ── 核心总结列表：左侧居中 ── */}
      <div
        style={{
          position: 'absolute',
          left: 80,
          top: '50%',
          transform: 'translateY(-50%)',
          width: '58%',
          paddingBottom: 140,
        }}
      >

        {bullets.map((bullet, i) => {
          // 每条间隔 12 帧（0.4 秒）弹出
          const delay = 8 + i * 12;
          const bulletSpr = spring({ fps, frame: frame - delay, config: { damping: 16, stiffness: 180 } });
          const bX = interpolate(bulletSpr, [0, 1], [40, 0]);
          return (
            <div
              key={i}
              style={{
                fontSize: 58,
                color: '#2a2118',
                fontWeight: 800,
                fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
                marginBottom: 28,
                lineHeight: 1.4,
                opacity: bulletSpr,
                transform: `translateX(${bX}px)`,
                display: 'flex',
                alignItems: 'baseline',
              }}
            >
              <span style={{ color: '#f59d0b', marginRight: 18, flexShrink: 0 }}>•</span>
              <span>{bullet.replace(/^-\s*/, '')}</span>
            </div>
          );
        })}
      </div>

      {/* ── 底部求关注横幅 ── */}
      <div
        style={{
          position: 'absolute',
          bottom: 0,
          left: 0,
          right: 0,
          height: 120,
          background: '#f59d0b',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transform: `translateY(${bannerY}px)`,
          boxShadow: '0 -10px 40px rgba(245,157,11,0.3)',
          zIndex: 4,
        }}
      >
        <div
          style={{
            fontSize: 62,
            fontWeight: 900,
            color: '#ffffff',
            fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
            letterSpacing: '0.05em',
          }}
        >
          关注我，获取更多面试资料和面试指导
        </div>
      </div>

      <Audio src={staticFile(audioPath)} />
    </AbsoluteFill>
  );
};
