import React from 'react';
import { Sequence, Audio, staticFile, useVideoConfig, AbsoluteFill, useCurrentFrame, interpolate, spring } from 'remotion';
import { AnimatedText } from './AnimatedText';
import { Character } from './Character';
import { DynamicVisual } from './DynamicVisual';

// --- Scene-in animation for the text block ---
const SlideInLeft: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame: frame - delay,
    config: { damping: 18, stiffness: 120 },
  });

  const x = interpolate(progress, [0, 1], [80, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{ transform: `translateX(${x}px)`, opacity }}>
      {children}
    </div>
  );
};

const SlideInRight: React.FC<{ children: React.ReactNode; delay?: number }> = ({ children, delay = 0 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame: frame - delay,
    config: { damping: 18, stiffness: 120 },
  });

  const x = interpolate(progress, [0, 1], [-80, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{ transform: `translateX(${x}px)`, opacity }}>
      {children}
    </div>
  );
};

// --- Character entrance animation ---
const CharacterEntrance: React.FC<{ children: React.ReactNode; fromBottom?: boolean }> = ({ children, fromBottom = true }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  const progress = spring({
    fps,
    frame,
    config: { damping: 16, stiffness: 100 },
  });

  const y = interpolate(progress, [0, 1], [fromBottom ? 60 : -60, 0]);
  const opacity = interpolate(progress, [0, 1], [0, 1]);

  return (
    <div style={{ transform: `translateY(${y}px)`, opacity }}>
      {children}
    </div>
  );
};

export const FAQScene: React.FC<{
  question: string;
  answer: string;
  qAudio: string;
  aAudio: string;
  character: 'businessman' | 'book' | 'fox' | 'bunny';
  qDur: number;
  aDur: number;
  visual_type?: string;
  visual_labels?: string[];
}> = ({ question, answer, qAudio, aAudio, qDur, aDur, visual_type = 'flow', visual_labels = [] }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();

  // 跨场淡入交叉渐变（配合 ArkFAQVideo 里的 offset={-15}）
  const sceneOpacity = spring({
    fps,
    frame,
    config: { damping: 20, stiffness: 200 },
  });

  const qAudioFrames = Math.ceil(qDur * fps);
  const aAudioFrames = Math.ceil(aDur * fps);
  const padding = Math.ceil(fps * 0.5);   // 0.5s pause between Q and A
  const endPadding = Math.ceil(fps * 1.5); // 1.5s hold after A finishes

  const qSeqDuration = qAudioFrames + padding;
  const aStartOffset = qAudioFrames + padding;

  return (
    <AbsoluteFill
      style={{
        background: '#f5efe0',
        overflow: 'hidden',
        opacity: sceneOpacity,
      }}
    >
      {/* ── Diagonal crosshatch texture (matches reference images) ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: [
            'repeating-linear-gradient(45deg, transparent, transparent 36px, rgba(0,0,0,0.032) 36px, rgba(0,0,0,0.032) 37px)',
            'repeating-linear-gradient(135deg, transparent, transparent 36px, rgba(0,0,0,0.032) 36px, rgba(0,0,0,0.032) 37px)',
          ].join(', '),
        }}
      />

      {/* ── Subtle edge vignette ── */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse at center, transparent 50%, rgba(0,0,0,0.07) 120%)',
        }}
      />

      {/* ══════════════════════════════════════════════
          QUESTION PHASE
          Character: bottom-left | Text: right side
      ══════════════════════════════════════════════ */}
      <Sequence durationInFrames={qSeqDuration}>
        <AbsoluteFill>
          {/* Character – bottom-left, slightly off-screen */}
          <div className="absolute bottom-0 left-[-40px]">
            <CharacterEntrance fromBottom>
              <Character type="question" />
            </CharacterEntrance>
          </div>

          {/* Text block – right side, vertically centered */}
          <div
            className="absolute flex flex-col justify-center"
            style={{
              right: 100,
              top: '50%',
              transform: 'translateY(-50%)',
              width: '46%',
            }}
          >
            <SlideInRight delay={4}>
              {/* Label */}
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#c8b89a',
                  letterSpacing: '0.15em',
                  marginBottom: 28,
                  fontFamily: 'sans-serif',
                  textTransform: 'uppercase',
                }}
              >
                Q &amp;
              </div>

              <AnimatedText text={question} delay={8} align="left" />
            </SlideInRight>
          </div>

          <Audio src={staticFile(qAudio)} />
        </AbsoluteFill>
      </Sequence>

      {/* ══════════════════════════════════════════════
          ANSWER PHASE
          Character: top-right | Text: left side
      ══════════════════════════════════════════════ */}
      <Sequence from={aStartOffset} durationInFrames={aAudioFrames + endPadding}>
        <AbsoluteFill>
          {/* Character – top-right, slightly off-screen */}
          <div className="absolute top-0 right-[-30px]">
            <CharacterEntrance fromBottom={false}>
              <Character type="answer" />
            </CharacterEntrance>
          </div>

          {/* Text block – left side, vertically centered */}
          <div
            className="absolute flex flex-col justify-center"
            style={{
              left: 100,
              top: '50%',
              transform: 'translateY(-50%)',
              width: '46%',
            }}
          >
            <SlideInLeft delay={4}>
              {/* Label */}
              <div
                style={{
                  fontSize: 36,
                  fontWeight: 900,
                  color: '#c8b89a',
                  letterSpacing: '0.15em',
                  marginBottom: 28,
                  fontFamily: 'sans-serif',
                  textTransform: 'uppercase',
                }}
              >
                A &amp;
              </div>

              <AnimatedText text={answer} delay={8} align="left" />
            </SlideInLeft>
          </div>

          <DynamicVisual type={visual_type} labels={visual_labels} />

          <Audio src={staticFile(aAudio)} />
        </AbsoluteFill>
      </Sequence>
    </AbsoluteFill>
  );
};
