export type QAData = {
  question: string;
  answer: string;
  qAudio: string;
  aAudio: string;
  character: "businessman" | "book";
  qDur?: number;
  aDur?: number;
};

export const faqData: QAData[] = [
  {
    question: "为什么任务一直是 <hl>processing</hl> 状态？",
    answer: "视频生成是一个<hl>异步过程</hl>，系统会自动轮询状态，请<hl>耐心等待</hl>。",
    qAudio: "audio/q1.mp3",
    aAudio: "audio/a1.mp3",
    character: "businessman"
  },
  {
    question: "可以<hl>取消</hl>正在生成的任务吗？",
    answer: "暂不<hl>支持取消</hl>，但可以在系统中<hl>标记为已取消</hl>。",
    qAudio: "audio/q2.mp3",
    aAudio: "audio/a2.mp3",
    character: "book"
  },
  {
    question: "如何同时使用 OpenAI 和火山引擎？",
    answer: "在创建任务时通过 <hl>provider 参数</hl>指定即可。",
    qAudio: "audio/q3.mp3",
    aAudio: "audio/a3.mp3",
    character: "businessman"
  },
  {
    question: "视频生成失败如何处理？",
    answer: "系统会自动发布<hl>失败事件</hl>，可监听此事件进行<hl>重试</hl>。",
    qAudio: "audio/q4.mp3",
    aAudio: "audio/a4.mp3",
    character: "book"
  }
];
