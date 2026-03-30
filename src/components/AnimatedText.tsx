import React from 'react';
import { interpolate, spring, useCurrentFrame, useVideoConfig } from 'remotion';

export const AnimatedText: React.FC<{
  text: string;
  delay?: number;
  align?: 'left' | 'center' | 'right';
}> = ({ text, delay = 0, align = 'left' }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // Parse <hl>...</hl> highlight tags
  const parts = text.split(/(<hl>.*?<\/hl>)/g).filter(Boolean);

  let charCount = 0;



  return (
    <div
      style={{
        display: 'block',
        textAlign: align,
        fontSize: 72,
        lineHeight: 1.5,
        fontWeight: 900,
        fontFamily: '"PingFang SC", "Microsoft YaHei", "Noto Sans SC", sans-serif',
        color: '#2a2118',
        wordBreak: 'keep-all',   // 适用于中英混排，避免生硬折断
        overflowWrap: 'break-word',
      }}
    >
      {parts.map((part, i) => {
        const isHighlight =
          part.startsWith('<hl>') && part.endsWith('</hl>');
        const content = isHighlight ? part.slice(4, -5) : part;

        // Highlighted text: orange (#f59d0b) with slight scale-up entrance
        const color = isHighlight ? '#f59d0b' : '#2a2118';

        // 智能分词：将连续英文/数字组合打包，中文字符/标点独立
        const contentTokens = content.match(/[\w]+|[^\w]/g) || [];

        return (
          <span
            key={i}
            style={{
              color,
              display: 'inline',
            }}
          >
            {contentTokens.map((token, k) => {
              const isWord = /^[\w]+$/.test(token);
              
              return (
                <span key={k} style={{ 
                  display: 'inline', 
                  whiteSpace: isWord ? 'nowrap' : 'normal' 
                }}>
                  {token.split('').map((char, j) => {
                    const currentIdx = charCount++;
                    // 2 frames per character stagger for snappier reveal
                    const startFrame = delay + currentIdx * 2;

                    const appear = spring({
                      fps,
                      frame: frame - startFrame,
                      // Damping is decreased for higher bounce, mass lowered for snappiness
                      config: { damping: 11, stiffness: 260, mass: 0.8 },
                    });

                    const y = interpolate(appear, [0, 1], [40, 0]);
                    const scale = isHighlight
                      ? interpolate(appear, [0, 1], [0.4, 1])
                      : interpolate(appear, [0, 1], [0.8, 1]);

                    return (
                      <span
                        key={j}
                        style={{
                          display: 'inline-block',
                          opacity: appear,
                          transform: `translateY(${y}px) scale(${scale})`,
                          transformOrigin: 'bottom center',
                          // Highlighted chars get a stronger glow effect
                          textShadow: isHighlight
                            ? '0 4px 16px rgba(245,157,11,0.6)'
                            : 'none',
                          // 若当前是空格，保留极小的包裹尺寸防止吃掉空格
                          minWidth: char === ' ' ? '0.3em' : 'auto',
                        }}
                      >
                        {char}
                      </span>
                    );
                  })}
                </span>
              );
            })}
          </span>
        );
      })}
    </div>
  );
};
