import React from 'react';
import { Img, staticFile, useCurrentFrame } from 'remotion';

export const Character: React.FC<{ type: 'question' | 'answer' }> = ({ type }) => {
  const frame = useCurrentFrame();
  
  const imgSrc =
    type === 'question'
      ? staticFile('images/question.png')
      : staticFile('images/answer.png');

  // 生动微小的人物律动效果:
  // Wobble: 左右很轻微的偏转角度 (-0.8 ~ 0.8 度)
  const wobble = Math.sin(frame / 20) * 0.8;
  // Bounce: 上下微弱的呼吸浮动 (-4 ~ 4 px)
  const bounce = Math.cos(frame / 20) * 4;

  return (
    <div
      style={{
        position: 'relative',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        // Drop shadow 保持在最外层以免和 transform 冲突
        filter: 'drop-shadow(0px 16px 32px rgba(0,0,0,0.18))',
      }}
    >
      <div
        style={{
          transform: `translateY(${bounce}px) rotate(${wobble}deg)`,
          transformOrigin: 'bottom center', // 锚点定在底部（例如屁股或脚）
        }}
      >
        <Img
          src={imgSrc}
          style={{
            width: 680,
            height: 680,
            objectFit: 'contain',
          }}
        />
      </div>
    </div>
  );
};
