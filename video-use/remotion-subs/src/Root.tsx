import React from "react";
import { Composition, getInputProps } from "remotion";
import { Subtitles } from "./Subtitles";

export const RemotionRoot: React.FC = () => {
  const props = getInputProps() || {};
  const fps = typeof props.fps === "number" ? props.fps : 30;

  return (
    <>
      <Composition
        id="Subtitles"
        component={Subtitles}
        durationInFrames={props.durationInFrames || 1800} // Read dynamically from props!
        fps={fps}
        width={props.width || 1080}
        height={props.height || 1920}
        defaultProps={{
          words: [],
          highlightColor: "#00FFFF",
          highlightShape: "skew"
        }}
      />
    </>
  );
};
