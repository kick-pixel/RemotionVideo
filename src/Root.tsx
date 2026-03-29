import "./index.css";
import { Composition, CalculateMetadataFunction, staticFile } from "remotion";
import { ArkFAQVideo, EnhancedVideoProps } from "./ArkFAQVideo";
import { faqData } from "./data";
import { Input, ALL_FORMATS, UrlSource } from "mediabunny";

export const getAudioDuration = async (src: string) => {
  const input = new Input({
    formats: ALL_FORMATS,
    source: new UrlSource(src, {
      getRetryDelay: () => null,
    }),
  });
  const durationInSeconds = await input.computeDuration();
  return durationInSeconds;
};

type RootProps = EnhancedVideoProps;

// render_props.json 的完整结构（包含预计算的 totalFrames）
type FullRenderProps = EnhancedVideoProps & { totalFrames?: number };

const calculateMetadata: CalculateMetadataFunction<RootProps> = async ({ props }) => {
  const fps = 30;

  // ── 直接 fetch render_props.json，获取预计算好的所有数据 ────────────────
  let fullProps: FullRenderProps | null = null;
  try {
    const resp = await fetch(staticFile("data/render_props.json"));
    if (resp.ok) {
      fullProps = (await resp.json()) as FullRenderProps;
    }
  } catch {
    // fetch 失败则回退到 props 注入
  }

  // 使用完整的数据（含 theme / outro / totalFrames）
  const theme = fullProps?.theme ?? props.theme;
  const outro = fullProps?.outro ?? props.outro;
  const qaData =
    (fullProps?.dataWithDurations?.length ?? 0) > 0
      ? fullProps!.dataWithDurations
      : (props.dataWithDurations?.length ?? 0) > 0
      ? props.dataWithDurations
      : faqData;

  // ── 若 gen_audio.py 已预计算 totalFrames，直接使用；否则逐项计算 ────────
  let totalFrames = fullProps?.totalFrames ?? 0;

  if (!totalFrames) {
    // 片头
    if (theme?.durationFrames) totalFrames += theme.durationFrames;
    // QA
    for (const item of qaData) {
      let qDur = item.qDur;
      let aDur = item.aDur;
      if (!qDur) qDur = await getAudioDuration(staticFile(item.qAudio));
      if (!aDur) aDur = await getAudioDuration(staticFile(item.aAudio));
      totalFrames +=
        Math.ceil(qDur * fps) + Math.ceil(fps * 0.5) +
        Math.ceil(aDur * fps) + Math.ceil(fps * 1.5);
    }
    // 片尾
    if (outro?.durationFrames) totalFrames += outro.durationFrames;
  }

  // ── 补充 QA 的 qDur/aDur（若没有则动态读取） ───────────────────────────
  const dataWithDurations = await Promise.all(
    qaData.map(async (item) => {
      let qDur = item.qDur;
      let aDur = item.aDur;
      if (!qDur) qDur = await getAudioDuration(staticFile(item.qAudio));
      if (!aDur) aDur = await getAudioDuration(staticFile(item.aAudio));
      return { ...item, qDur, aDur };
    })
  );

  return {
    durationInFrames: Math.max(30, totalFrames),
    fps,
    width: 1920,
    height: 1080,
    props: {
      theme,
      outro,
      dataWithDurations,
    },
  };
};

export const RemotionRoot: React.FC = () => {
  return (
    <>
      <Composition
        id="ArkFAQ"
        component={ArkFAQVideo}
        defaultProps={{
          dataWithDurations: [],
          theme: undefined,
          outro: undefined,
        }}
        calculateMetadata={calculateMetadata}
        durationInFrames={300}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
