import { useState } from 'react';

export default function TranscriptEditor({ transcript, onSave, onCancel }) {
  const [editedTranscript, setEditedTranscript] = useState(transcript);
  const [editingIndex, setEditingIndex] = useState(null);
  const [editValue, setEditValue] = useState("");

  const handleWordClick = (index, wordObj) => {
    if (wordObj.type !== 'word') return;
    setEditingIndex(index);
    setEditValue(wordObj.text);
  };

  const handleWordSave = () => {
    if (editingIndex === null) return;
    const newWords = [...editedTranscript.words];
    newWords[editingIndex] = {
      ...newWords[editingIndex],
      text: editValue
    };
    setEditedTranscript({ ...editedTranscript, words: newWords });
    setEditingIndex(null);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      handleWordSave();
    } else if (e.key === 'Escape') {
      setEditingIndex(null);
    }
  };

  return (
    <div className="transcript-editor card">
      <h2>Transkript überprüfen & korrigieren</h2>
      <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '15px'}}>
        Klicke auf ein falsch geschriebenes Wort, um es zu korrigieren. Die Zeitstempel für den Schnitt bleiben dabei erhalten!
      </p>

      <div className="transcript-text-container">
        {editedTranscript?.words?.map((word, index) => {
          if (word.type !== 'word') return null;
          
          if (editingIndex === index) {
            return (
              <span key={index} className="word-editor">
                <input
                  autoFocus
                  type="text"
                  value={editValue}
                  onChange={(e) => setEditValue(e.target.value)}
                  onBlur={handleWordSave}
                  onKeyDown={handleKeyDown}
                />
              </span>
            );
          }

          return (
            <span 
              key={index} 
              className="transcript-word"
              onClick={() => handleWordClick(index, word)}
            >
              {word.text}{' '}
            </span>
          );
        })}
      </div>

      <div className="editor-actions">
        <button className="magic-button secondary" onClick={onCancel}>Abbrechen</button>
        <button className="magic-button" onClick={() => onSave(editedTranscript)}>Weiter: KI-Schnitt & Rendern ✨</button>
      </div>
    </div>
  );
}
