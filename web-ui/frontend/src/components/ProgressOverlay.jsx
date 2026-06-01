import { useState, useEffect } from 'react';

export default function ProgressOverlay({ isVisible, statusText }) {
  const [progress, setProgress] = useState(0);
  const [step, setStep] = useState("");
  const [status, setStatus] = useState("idle");

  useEffect(() => {
    if (!isVisible) return;
    
    // Connect to SSE
    const eventSource = new EventSource("http://localhost:8001/api/progress");
    
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setProgress(data.percent);
        setStep(data.step);
        setStatus(data.status);
      } catch(e) {
        console.error("SSE parse error", e);
      }
    };
    
    eventSource.onerror = (error) => {
      console.error("SSE error", error);
      eventSource.close();
    };

    return () => {
      eventSource.close();
    };
  }, [isVisible]);

  if (!isVisible) return null;

  return (
    <div className="progress-overlay">
      <div className="progress-modal">
        <div className="loader-spinner"></div>
        <h2>{statusText || "✨ MAGIC ARBEITET..."}</h2>
        <div className="progress-bar-container">
          <div className="progress-bar-fill" style={{ width: `${progress}%` }}></div>
        </div>
        <div className="progress-details">
          <span>{step}</span>
          <span>{progress}%</span>
        </div>
      </div>
    </div>
  );
}
