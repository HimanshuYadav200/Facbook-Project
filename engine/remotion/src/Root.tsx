// One composition per style. Each reads the run folder given to the render as --public-dir
// (plan.json, words.json, voice.wav, data/, img/, assets/). New style = new folder in styles/ + one line in STYLES.
import React from "react";
import { Composition } from "remotion";
import { BasePlan, DataFile, FPS, WordsFile, loadJson } from "./common/timing";
import { VintageStory } from "./styles/vintage-story/VintageStory";
import { FlatFastcut } from "./styles/flat-fastcut/FlatFastcut";

const STYLES: Record<string, React.FC<any>> = {
  "vintage-story": VintageStory,
  "flat-fastcut": FlatFastcut,
};

async function loadRun(styleId: string) {
  const plan = await loadJson<BasePlan>("plan.json");
  if (plan.style !== styleId) throw new Error(`plan.json is style "${plan.style}", but composition "${styleId}" was rendered`);
  const w = await loadJson<WordsFile>("words.json");
  const data: Record<string, DataFile> = {};
  for (const [name, file] of Object.entries(plan.data ?? {})) data[name] = await loadJson<DataFile>(file);
  const seconds = w.duration + (plan.tailSeconds ?? 0.5) + (plan.endCard?.seconds ?? 0);
  return { durationInFrames: Math.ceil(seconds * FPS), props: { words: w.words, duration: w.duration, plan, data } };
}

export const RemotionRoot: React.FC = () => (
  <>
    {Object.entries(STYLES).map(([id, component]) => (
      <Composition
        key={id}
        id={id}
        component={component}
        width={1080}
        height={1920}
        fps={FPS}
        durationInFrames={FPS}
        defaultProps={{ words: [], duration: 0, plan: { version: 1, style: id, shots: [] }, data: {} }}
        calculateMetadata={() => loadRun(id)}
      />
    ))}
  </>
);
