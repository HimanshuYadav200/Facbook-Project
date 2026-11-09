import React from "react";
import { Composition } from "remotion";
import { StyleB, StyleBProps } from "./styleB/StyleB";
import { StyleA, StyleAProps } from "./styleA/StyleA";
import { FPS, WordsFile, loadJson } from "./common/timing";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="StyleB"
      component={StyleB}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={300}
      defaultProps={{ words: [], duration: 0, plan: { shots: [] } } as StyleBProps}
      calculateMetadata={async () => {
        const w = await loadJson<WordsFile>("styleB/words.json");
        const plan = await loadJson<StyleBProps["plan"]>("styleB/plan.json");
        return {
          durationInFrames: Math.ceil((w.duration + 0.8) * FPS),
          props: { words: w.words, duration: w.duration, plan },
        };
      }}
    />
    <Composition
      id="StyleA"
      component={StyleA}
      width={1080}
      height={1920}
      fps={FPS}
      durationInFrames={300}
      defaultProps={{ words: [], duration: 0, points: [], plan: { shots: [], endCard: { text: "", seconds: 0 } } } as StyleAProps}
      calculateMetadata={async () => {
        const w = await loadJson<WordsFile>("styleA/words.json");
        const plan = await loadJson<StyleAProps["plan"]>("styleA/plan.json");
        const data = await loadJson<{ points: StyleAProps["points"] }>("styleA/nvda.json");
        return {
          durationInFrames: Math.ceil((w.duration + 0.4 + plan.endCard.seconds) * FPS),
          props: { words: w.words, duration: w.duration, plan, points: data.points },
        };
      }}
    />
  </>
);
