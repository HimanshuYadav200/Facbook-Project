// Voice + looping ambience + optional music: the audio every style shares.
// Beds loop, so they last the whole video (the test version stopped after 40 s).
import React from "react";
import { Audio, interpolate, staticFile, useVideoConfig } from "remotion";
import { BasePlan, musicFile, sfxFile } from "./timing";

export const AudioBed: React.FC<{ plan: BasePlan }> = ({ plan }) => {
  const { durationInFrames, fps } = useVideoConfig();
  const music = plan.music;
  // Music fades in over 1 s and out over the last 2 s, so a long track never cuts off mid-phrase.
  const musicVolume = (f: number) => (music?.volume ?? 0) * interpolate(
    f, [0, fps, durationInFrames - 2 * fps, durationInFrames], [0, 1, 1, 0],
    { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <>
      <Audio src={staticFile("voice.wav")} />
      {(plan.beds ?? []).map((b, i) => <Audio key={i} src={sfxFile(b.sfx)} volume={b.volume} loop />)}
      {music ? <Audio src={musicFile(music.track)} volume={musicVolume} loop /> : null}
    </>
  );
};
