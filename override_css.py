import re

css_override = '''
/* EDITORIAL THEME OVERRIDE */
:root {
  --bg-main: #0a0a0a;
  --bg-card: transparent;
  --bg-card-hover: rgba(255,255,255,0.03);
  --bg-card-subtle: transparent;
  --bg-input: transparent;
  --border-glass: rgba(255, 255, 255, 0.15);
  --border-focus: #ff4500;
  
  --accent-purple: #ff4500;
  --accent-purple-glow: rgba(255, 69, 0, 0.1);
  --accent-cyan: #ff4500;
  --accent-cyan-glow: rgba(255, 69, 0, 0.1);
  --accent-emerald: #10b981;
  --accent-amber: #f59e0b;
  --accent-rose: #f43f5e;
  
  --font-sans: 'Inter', sans-serif;
  
  --radius-sm: 0px;
  --radius-md: 0px;
  --radius-lg: 0px;
  --radius-full: 0px;
  
  --shadow-card: none;
  --glow-purple: none;
  --glow-cyan: none;
}
.ambient-glow { display: none !important; }
.grid-overlay { opacity: 0.1 !important; }

/* Upload Card Redesign */
.generator-card {
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
  border-radius: 0;
  padding: 40px;
}
.drop-zone {
  border: 1px dashed rgba(255, 255, 255, 0.2);
  border-radius: 0;
  background: transparent;
  transition: all 0.3s ease;
}
.drop-zone:hover, .drop-zone.drag-active {
  background: rgba(255, 69, 0, 0.05);
  border-color: #ff4500;
}
.btn-browse {
  border-radius: 0;
  background: transparent;
  border: 1px solid rgba(255, 255, 255, 0.3);
  font-family: var(--font-mono);
  text-transform: uppercase;
}
.btn-browse:hover {
  background: #ff4500;
  border-color: #ff4500;
  color: #fff;
  transform: none;
}

/* Inputs & Overrides */
.profile-fields-grid input, .profile-fields-grid textarea {
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 0;
  background: transparent;
  font-family: var(--font-sans);
  padding: 12px 0;
}
.profile-fields-grid input:focus, .profile-fields-grid textarea:focus {
  border-bottom-color: #ff4500;
  background: transparent;
  outline: none;
}
.customization-block .btn-upload-photo {
  border-radius: 0;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  font-family: var(--font-mono);
  text-transform: uppercase;
  color: #fff;
}
.theme-swatch {
  border-radius: 0;
}

/* Template Cards */
.template-card {
  border-radius: 0;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: transparent;
}
.template-card.active {
  border-color: #ff4500;
  background: rgba(255, 69, 0, 0.05);
}
.template-select-indicator {
  border-radius: 0;
}

/* Massive Generate Button */
.btn-generate-main {
  border-radius: 0;
  background: transparent;
  border: 1px solid #ff4500;
  color: #ff4500;
  font-family: 'Instrument Serif', serif;
  font-size: 2.5rem;
  padding: 24px;
  text-transform: uppercase;
  position: relative;
  overflow: hidden;
  transition: all 0.4s;
}
.btn-generate-main:not(:disabled):hover {
  background: #ff4500;
  color: #fff;
  transform: none;
  box-shadow: none;
}

/* Stepper Box Minimal */
.stepper-list {
  background: transparent;
  border: 1px solid rgba(255,255,255,0.1);
  border-radius: 0;
}
.step-indicator {
  border-radius: 0;
}
'''

with open('generator.css', 'a', encoding='utf-8') as f:
    f.write(css_override)

# Replace fonts in existing css to prevent conflicts if needed
with open('generator.css', 'r', encoding='utf-8') as f:
    content = f.read()
content = content.replace("'Plus Jakarta Sans'", "'Inter'")
content = content.replace("'Space Grotesk'", "'Instrument Serif'")
with open('generator.css', 'w', encoding='utf-8') as f:
    f.write(content)
