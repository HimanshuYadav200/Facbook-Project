// Voice + looping ambience + optional music: the audio every style shares.
// Beds loop, so they last the whole video (the test version stopped after 40 s).
import React from "react";
import { Audio, staticFile } from "remotion";
import { BasePlan, musicFile, sfxFile } from "./timing";

export const AudioBed: React.FC<{ plan: BasePlan }> = ({ plan }) => (
  <>
    <Audio src={staticFile("voice.wav")} />
    {(plan.beds ?? []).map((b, i) => <Audio key={i} src={sfxFile(b.sfx)} volume={b.volume} loop />)}
    {plan.music ? <Audio src={musicFile(plan.music.track)} volume={plan.music.volume} loop /> : null}
  </>
);
