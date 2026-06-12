import React from 'react';

export default function StyleSelector({ 
  selectedStyle,
  onStyleChange,
  highlightColor, 
  onColorChange, 
  highlightShape, 
  onShapeChange,
  fontFamily,
  onFontFamilyChange,
  fontWeight,
  onFontWeightChange,
  textCase,
  onTextCaseChange,
  fontSize,
  onFontSizeChange,
  yPosition,
  onYPositionChange,
  pillRadius,
  onPillRadiusChange,
  popInAnimation,
  onPopInAnimationChange,
  keepPunctuation,
  onKeepPunctuationChange,
  shapePadding,
  onShapePaddingChange
}) {
  return (
    <div className="style-selector card" style={{marginTop: '20px', borderLeft: '6px solid #3333CC'}}>
      <h2 style={{color: '#3333CC', marginBottom: '10px'}}>4. Untertitel-Design (Style & Position)</h2>
      <p style={{fontSize: '0.9rem', color: '#666', marginBottom: '20px'}}>
        Wähle den Animations-Modus und passe Schriftgröße und vertikale Position an.
      </p>

      {/* Mode Selection */}
      <div style={{marginBottom: '20px', background: '#f9f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #e4e4e7'}}>
        <h4 style={{marginTop: 0, marginBottom: '10px', color: '#333'}}>Animations-Modus</h4>
        <select 
          value={selectedStyle}
          onChange={(e) => onStyleChange(e.target.value)}
          style={{width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', fontSize: '15px', outline: 'none', cursor: 'pointer'}}
        >
          <option value="tiktok_dynamic">Dynamisch (KARAOKE - Wort für Wort)</option>
          <option value="translated_dmax">Standard (Klassischer Textblock)</option>
        </select>
      </div>

      <div className="style-settings" style={{display: 'flex', gap: '20px', alignItems: 'flex-start', flexWrap: 'wrap'}}>
        
        {/* Colors & Shapes (Only relevant if dynamic) */}
        <div style={{flex: '1 1 200px', background: '#f9f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #e4e4e7', opacity: selectedStyle === "tiktok_dynamic" ? 1 : 0.5}}>
          <h4 style={{marginTop: 0, marginBottom: '15px', color: '#333'}}>Highlight-Design (Nur Dynamisch)</h4>
          
          <div className="setting-group" style={{display: 'flex', flexDirection: 'column', gap: '5px', marginBottom: '15px'}}>
            <label htmlFor="highlight-color" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Highlight-Farbe</label>
            <div style={{display: 'flex', alignItems: 'center', gap: '10px'}}>
              <input 
                type="color" 
                id="highlight-color" 
                value={highlightColor} 
                onChange={(e) => onColorChange(e.target.value)} 
                disabled={selectedStyle !== "tiktok_dynamic"}
                style={{
                  width: '40px', height: '40px', padding: '0', border: 'none', 
                  borderRadius: '8px', cursor: 'pointer', background: 'transparent'
                }}
              />
              <span style={{fontFamily: 'monospace', fontSize: '14px', background: '#fff', padding: '4px 8px', borderRadius: '4px', border: '1px solid #ddd'}}>{highlightColor}</span>
            </div>
          </div>

          <div className="setting-group" style={{display: 'flex', flexDirection: 'column', gap: '5px'}}>
            <label htmlFor="highlight-shape" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Highlight-Form</label>
            <select 
              id="highlight-shape"
              value={highlightShape}
              onChange={(e) => onShapeChange(e.target.value)}
              disabled={selectedStyle !== "tiktok_dynamic"}
              style={{padding: '8px 12px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', fontSize: '14px', outline: 'none', cursor: 'pointer'}}
            >
              <option value="text">Text-Farbe (Klassisch)</option>
              <option value="outline">Dicke Outline (Glow)</option>
              <option value="box">Opaque Box (Eckig)</option>
              <option value="skew">Skewed Box (Schräg)</option>
              <option value="rounded">Pill Box (Abgerundet)</option>
            </select>
            
            {highlightShape === "rounded" && (
              <div style={{marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '5px'}}>
                <label htmlFor="pill-radius" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Ecken-Radius: {pillRadius}px</label>
                <input 
                  type="range" 
                  id="pill-radius" 
                  min="0" max="40" step="1"
                  value={pillRadius} 
                  onChange={(e) => onPillRadiusChange(Number(e.target.value))}
                  style={{cursor: 'pointer'}}
                />
              </div>
            )}

            {["box", "skew", "rounded"].includes(highlightShape) && (
              <div style={{marginTop: '10px', display: 'flex', flexDirection: 'column', gap: '5px'}}>
                <label htmlFor="shape-padding" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Shape-Größe (Padding): {shapePadding}px</label>
                <input 
                  type="range" 
                  id="shape-padding" 
                  min="0" max="40" step="1"
                  value={shapePadding} 
                  onChange={(e) => onShapePaddingChange(Number(e.target.value))}
                  style={{cursor: 'pointer'}}
                />
              </div>
            )}
            
            <div style={{marginTop: '15px', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <input 
                type="checkbox" 
                id="pop-in-animation" 
                checked={popInAnimation}
                onChange={(e) => onPopInAnimationChange(e.target.checked)}
                disabled={selectedStyle !== "tiktok_dynamic"}
                style={{cursor: 'pointer', width: '16px', height: '16px'}}
              />
              <label htmlFor="pop-in-animation" style={{fontWeight: 'bold', fontSize: '13px', color: '#333', cursor: 'pointer', opacity: selectedStyle !== "tiktok_dynamic" ? 0.5 : 1}}>
                Pop-In Animation
              </label>
            </div>

            <div style={{marginTop: '10px', display: 'flex', alignItems: 'center', gap: '8px'}}>
              <input 
                type="checkbox" 
                id="keep-punctuation" 
                checked={keepPunctuation}
                onChange={(e) => onKeepPunctuationChange(e.target.checked)}
                disabled={selectedStyle !== "tiktok_dynamic"}
                style={{cursor: 'pointer', width: '16px', height: '16px'}}
              />
              <label htmlFor="keep-punctuation" style={{fontWeight: 'bold', fontSize: '13px', color: '#333', cursor: 'pointer', opacity: selectedStyle !== "tiktok_dynamic" ? 0.5 : 1}}>
                Satzzeichen beibehalten
              </label>
            </div>
          </div>
        </div>

        {/* Font Settings */}
        <div style={{flex: '1 1 200px', background: '#f9f9fa', padding: '15px', borderRadius: '8px', border: '1px solid #e4e4e7'}}>
          <h4 style={{marginTop: 0, marginBottom: '15px', color: '#333'}}>Typografie & Position</h4>

          <div className="setting-group" style={{display: 'flex', flexDirection: 'column', gap: '5px', marginBottom: '15px'}}>
            <label htmlFor="font-family" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Schrift-Familie</label>
            <select 
              id="font-family"
              value={fontFamily}
              onChange={(e) => onFontFamilyChange(e.target.value)}
              style={{padding: '8px 12px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', fontSize: '14px', outline: 'none', cursor: 'pointer'}}
            >
              <option value="'GT America', Helvetica, Arial, sans-serif">GT America (Pixelschickeria)</option>
              <option value="'Proxima Nova', sans-serif">Proxima Nova (Modern/Clean)</option>
              <option value="'Impact', sans-serif">Impact (Meme Style)</option>
              <option value="'Arial Black', sans-serif">Arial Black (Wuchtig)</option>
              <option value="'Roboto', sans-serif">Roboto (Modern)</option>
              <option value="'Anton', sans-serif">Anton (Schmal & Laut)</option>
            </select>
          </div>

          <div style={{display: 'flex', gap: '15px', marginBottom: '15px'}}>
            <div className="setting-group" style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '5px'}}>
              <label htmlFor="font-weight" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Dicke</label>
              <select 
                id="font-weight"
                value={fontWeight}
                onChange={(e) => onFontWeightChange(e.target.value)}
                style={{padding: '8px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', fontSize: '14px', outline: 'none', cursor: 'pointer'}}
              >
                <option value="bold">Fett (Bold)</option>
                <option value="normal">Normal</option>
                <option value="100">Dünn (Thin)</option>
              </select>
            </div>

            <div className="setting-group" style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '5px'}}>
              <label htmlFor="text-case" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Buchstaben</label>
              <select 
                id="text-case"
                value={textCase}
                onChange={(e) => onTextCaseChange(e.target.value)}
                style={{padding: '8px', borderRadius: '4px', border: '1px solid #ccc', background: '#fff', fontSize: '14px', outline: 'none', cursor: 'pointer'}}
              >
                <option value="uppercase">ALLES GROSS</option>
                <option value="none">Original</option>
                <option value="lowercase">alles klein</option>
              </select>
            </div>
          </div>
          
          {/* New Size & Position Controls */}
          <div style={{display: 'flex', gap: '15px'}}>
            <div className="setting-group" style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '5px'}}>
              <label htmlFor="font-size" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Größe: {fontSize}</label>
              <input 
                type="range" 
                id="font-size" 
                min="10" max="60" step="1"
                value={fontSize} 
                onChange={(e) => onFontSizeChange(Number(e.target.value))}
                style={{cursor: 'pointer'}}
              />
            </div>

            <div className="setting-group" style={{flex: 1, display: 'flex', flexDirection: 'column', gap: '5px'}}>
              <label htmlFor="y-position" style={{fontWeight: 'bold', fontSize: '12px', color: '#888'}}>Y-Achse: {yPosition}%</label>
              <input 
                type="range" 
                id="y-position" 
                min="5" max="50" step="1"
                value={yPosition} 
                onChange={(e) => onYPositionChange(Number(e.target.value))}
                style={{cursor: 'pointer'}}
              />
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
