import React, { useMemo } from "react";
import { AbsoluteFill, useCurrentFrame, useVideoConfig, spring } from "remotion";

export const Subtitles: React.FC<{
  words: { start: number; end: number; text: string; yPositionOverride?: number }[];
  highlightColor: string;
  highlightShape: string;
  fontFamily?: string;
  fontWeight?: string;
  textCase?: string;
  fontSize?: number;
  yPosition?: number;
  pillRadius?: number;
  popInAnimation?: boolean;
  keepPunctuation?: boolean;
  shapePadding?: number;
}> = ({ words, highlightColor, highlightShape, fontFamily = "'GT America', Helvetica, Arial, sans-serif", fontWeight = "bold", textCase = "uppercase", fontSize = 20, yPosition = 15, pillRadius = 20, popInAnimation = true, keepPunctuation = false, shapePadding = 10 }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const currentTime = frame / fps;

  // Chunk words into groups (e.g., 2-3 words per screen)
  const chunks = useMemo(() => {
    const result = [];
    let currentChunk = [];
    
    for (let i = 0; i < words.length; i++) {
      const word = words[i];
      currentChunk.push(word);
      
      const textLength = currentChunk.map(w => w.text).join(" ").length;
      const endsInPunct = /[.,;!?]$/.test(word.text);
      
      if (currentChunk.length >= 3 || textLength > 20 || endsInPunct) {
        result.push(currentChunk);
        currentChunk = [];
      }
    }
    if (currentChunk.length > 0) result.push(currentChunk);
    return result;
  }, [words]);

  // Find the active chunk based on time
  // Search backwards to find the most recent chunk that has started.
  // This prevents previous chunks with lingering (+0.5s) from blocking new chunks!
  let activeChunk = null;
  for (let i = chunks.length - 1; i >= 0; i--) {
    const chunk = chunks[i];
    if (chunk.length === 0) continue;
    
    const start = chunk[0].start;
    if (currentTime >= start) {
      const end = chunk[chunk.length - 1].end;
      // Keep text on screen slightly longer if there's a pause, 
      // but ONLY if a newer chunk hasn't started yet!
      if (currentTime <= end + 0.5) {
        activeChunk = chunk;
      }
      break;
    }
  }

  if (!activeChunk) {
    return <AbsoluteFill style={{ backgroundColor: "transparent" }} />;
  }

  // Find which specific word in the chunk is active
  // The active word is the last word whose start time is <= currentTime
  let activeWordIndex = -1;
  for (let i = activeChunk.length - 1; i >= 0; i--) {
    if (currentTime >= activeChunk[i].start) {
      activeWordIndex = i;
      break;
    }
  }
  
  // If we are slightly before the first word, highlight the first word
  if (activeWordIndex === -1) {
    activeWordIndex = 0;
  }

  const currentYPosition = activeChunk && activeChunk[0].yPositionOverride !== undefined 
    ? activeChunk[0].yPositionOverride 
    : yPosition;

  return (
    <AbsoluteFill
      style={{
        backgroundColor: "transparent",
        justifyContent: "flex-end",
        alignItems: "center",
        paddingBottom: `${currentYPosition}%`, // Dynamic Lower third
      }}
    >
      <div
        style={{
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "center",
          gap: "15px",
          width: "80%",
          textAlign: "center",
        }}
      >
        {activeChunk.map((word, i) => {
          const isActive = i === activeWordIndex;
          
          let bgScale = 1;
          let textActiveScale = 1.1;

          if (isActive && popInAnimation) {
            bgScale = spring({
              fps,
              frame: frame - (word.start * fps),
              config: { damping: 14, stiffness: 200, mass: 0.5 },
            });
            textActiveScale = 1 + (bgScale * 0.1);
          } else if (isActive && !popInAnimation) {
            textActiveScale = 1.1;
          }

          let wordStyle: React.CSSProperties = {
            fontFamily: fontFamily,
            fontSize: `${fontSize * 3.5}px`,
            fontWeight: fontWeight as any,
            color: "white",
            textTransform: (textCase === "none" ? "none" : textCase) as any,
            textShadow: "4px 4px 0px rgba(0,0,0,0.8)",
            transition: popInAnimation ? "none" : "all 0.1s ease-out",
            position: "relative",
            zIndex: isActive ? 10 : 1,
            transform: isActive ? `scale(${textActiveScale})` : "scale(1)",
          };

          if (isActive) {
            if (highlightShape === "text") {
              wordStyle.color = highlightColor;
            } else if (highlightShape === "outline") {
              wordStyle.color = "white";
              wordStyle.WebkitTextStroke = `3px ${highlightColor}`;
              wordStyle.textShadow = `0 0 20px ${highlightColor}, 4px 4px 0px rgba(0,0,0,0.8)`;
            } else if (highlightShape === "box") {
              wordStyle.color = "black";
              wordStyle.textShadow = "none";
              return (
                <div key={i} style={{ position: "relative", display: "inline-block" }}>
                  <div
                    style={{
                      position: "absolute",
                      top: `-${shapePadding * 0.6}px`,
                      left: `-${shapePadding}px`,
                      right: `-${shapePadding}px`,
                      bottom: `-${shapePadding * 0.6}px`,
                      backgroundColor: highlightColor,
                      zIndex: -1,
                      borderRadius: "8px",
                      transform: `scale(${bgScale})`,
                      transformOrigin: "center center"
                    }}
                  />
                  <span style={{ ...wordStyle, position: "relative", zIndex: 1 }}>
                    {keepPunctuation ? word.text : word.text.replace(/[.,;!?]/g, "")}
                  </span>
                </div>
              );
            } else if (highlightShape === "skew") {
              wordStyle.color = "black";
              wordStyle.textShadow = "none";
              return (
                <div key={i} style={{ position: "relative", display: "inline-block" }}>
                  <div
                    style={{
                      position: "absolute",
                      top: `-${shapePadding * 0.6}px`,
                      left: `-${shapePadding}px`,
                      right: `-${shapePadding}px`,
                      bottom: `-${shapePadding * 0.6}px`,
                      backgroundColor: highlightColor,
                      transform: `skew(-15deg) scale(${bgScale})`,
                      zIndex: -1,
                      borderRadius: "5px",
                      boxShadow: "4px 4px 0px rgba(0,0,0,0.5)",
                      transformOrigin: "center center"
                    }}
                  />
                  <span style={{ ...wordStyle, position: "relative", zIndex: 1 }}>
                    {keepPunctuation ? word.text : word.text.replace(/[.,;!?]/g, "")}
                  </span>
                </div>
              );
            } else if (highlightShape === "rounded") {
              return (
                <div key={i} style={{ position: "relative", display: "inline-block" }}>
                  <div
                    style={{
                      position: "absolute",
                      top: `-${shapePadding * 0.6}px`,
                      left: `-${shapePadding}px`,
                      right: `-${shapePadding}px`,
                      bottom: `-${shapePadding * 0.6}px`,
                      backgroundColor: highlightColor,
                      zIndex: -1,
                      borderRadius: `${pillRadius}px`,
                      boxShadow: "4px 4px 0px rgba(0,0,0,0.5)",
                      transform: `scale(${bgScale})`,
                      transformOrigin: "center center"
                    }}
                  />
                  <span style={{ ...wordStyle, position: "relative", zIndex: 1 }}>
                    {keepPunctuation ? word.text : word.text.replace(/[.,;!?]/g, "")}
                  </span>
                </div>
              );
            }
          }

          return (
            <span key={i} style={wordStyle}>
              {keepPunctuation ? word.text : word.text.replace(/[.,;!?]/g, "")}
            </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};
