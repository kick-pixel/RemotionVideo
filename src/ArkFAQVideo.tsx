import React from 'react';
import { Series } from 'remotion';
import { FAQScene } from './components/FAQScene';
import { IntroScene } from './components/IntroScene';
import { OutroScene } from './components/OutroScene';
import { QAData } from './data';

export type EnhancedVideoProps = {
  theme?: {
    theme_title: string;
    theme_subtitle: string;
    audioPath: string;
    durationFrames?: number;
  };
  outro?: {
    summary_display: string;
    audioPath: string;
    durationFrames?: number;
  };
  dataWithDurations: QAData[];
};

export const ArkFAQVideo: React.FC<EnhancedVideoProps> = ({ 
  dataWithDurations, 
  theme, 
  outro 
}) => {
  const fps = 30;

  return (
    <Series>
      {/* ── 1. 片头序列 ── */}
      {theme && theme.durationFrames && (
        <Series.Sequence durationInFrames={theme.durationFrames}>
          <IntroScene 
            themeTitle={theme.theme_title} 
            themeSubject={theme.theme_subtitle} 
            audioPath={theme.audioPath}
          />
        </Series.Sequence>
      )}

      {/* ── 2. 正片问答序列 ── */}
      {dataWithDurations?.map((item, index) => {
        // Calculate the scene duration explicitly
        const qFrames = Math.ceil(item.qDur! * fps);
        const aFrames = Math.ceil(item.aDur! * fps);
        const padding = Math.ceil(fps * 0.5);
        const endPadding = Math.ceil(fps * 1.5);
        
        const sceneDuration = qFrames + padding + aFrames + endPadding;
        
        return (
          <Series.Sequence 
            key={`qa-${index}`} 
            durationInFrames={sceneDuration}
            offset={-15}
          >
            <FAQScene 
              {...item} 
              qDur={item.qDur!} 
              aDur={item.aDur!} 
            />
          </Series.Sequence>
        );
      })}

      {/* ── 3. 片尾序列 ── */}
      {outro && outro.durationFrames && (
        <Series.Sequence durationInFrames={outro.durationFrames} offset={-15}>
          <OutroScene 
            summaryDisplay={outro.summary_display} 
            audioPath={outro.audioPath} 
          />
        </Series.Sequence>
      )}
    </Series>
  );
};
