/**
 * speechService.js
 * Wraps the browser's Web Speech API for:
 *   - Speech Recognition  (mic → text)
 *   - Speech Synthesis    (text → voice read-aloud)
 *
 * Browser support: Chrome ✅ Edge ✅ Safari (partial) ✅ Firefox ❌
 * No API key or backend needed — 100% free browser-native API.
 */

// ──────────────────────────────────────────────────────────────────────────────
// Feature detection
// ──────────────────────────────────────────────────────────────────────────────

/** True if the browser supports speech recognition */
export const isRecognitionSupported = () =>
  !!(window.SpeechRecognition || window.webkitSpeechRecognition);

/** True if the browser supports text-to-speech */
export const isSynthesisSupported = () => !!window.speechSynthesis;


// ──────────────────────────────────────────────────────────────────────────────
// Speech Recognition (mic → text)
// ──────────────────────────────────────────────────────────────────────────────

let _recognition = null;
let _isListening = false;

/**
 * Start listening to the microphone.
 *
 * @param {function} onResult   - Called with the final transcript string
 * @param {function} onInterim  - Called with partial (interim) transcript
 * @param {function} onError    - Called with an error message string
 * @param {string}   lang       - BCP-47 language tag, e.g. "en-US", "hi-IN"
 * @returns {void}
 */
export const startListening = (onResult, onInterim, onError, lang = 'en-US') => {
  if (!isRecognitionSupported()) {
    onError?.('Speech recognition is not supported in this browser. Please use Chrome or Edge.');
    return;
  }
  if (_isListening) {
    stopListening();
    return;
  }

  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  _recognition = new SpeechRecognition();

  _recognition.lang            = lang;
  _recognition.continuous      = false;   // Stop after a pause
  _recognition.interimResults  = true;    // Provide live partial results
  _recognition.maxAlternatives = 1;

  _recognition.onstart = () => {
    _isListening = true;
  };

  _recognition.onresult = (event) => {
    let interimText = '';
    let finalText   = '';

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript;
      if (event.results[i].isFinal) {
        finalText += transcript;
      } else {
        interimText += transcript;
      }
    }

    if (interimText) onInterim?.(interimText);
    if (finalText)   onResult?.(finalText.trim());
  };

  _recognition.onerror = (event) => {
    _isListening = false;
    const messages = {
      'no-speech':          'No speech detected. Please speak clearly and try again.',
      'audio-capture':      'Microphone not accessible. Check your browser permissions.',
      'not-allowed':        'Microphone permission denied. Please allow access in browser settings.',
      'network':            'Network error during speech recognition.',
      'aborted':            'Listening stopped.',
      'service-not-allowed':'Speech service not allowed. Try on HTTPS.',
    };
    onError?.(messages[event.error] || `Speech error: ${event.error}`);
  };

  _recognition.onend = () => {
    _isListening = false;
  };

  try {
    _recognition.start();
  } catch (err) {
    _isListening = false;
    onError?.(`Could not start microphone: ${err.message}`);
  }
};

/**
 * Stop listening. Safe to call even if not currently listening.
 */
export const stopListening = () => {
  if (_recognition) {
    try { _recognition.stop(); } catch (_) {}
    _recognition = null;
  }
  _isListening = false;
};

/** True if currently recording */
export const isListening = () => _isListening;


// ──────────────────────────────────────────────────────────────────────────────
// Speech Synthesis (text → voice)
// ──────────────────────────────────────────────────────────────────────────────

let _currentUtterance = null;

/**
 * Read aloud the given text using the browser's TTS engine.
 *
 * @param {string} text    - The text to speak
 * @param {object} options - { rate, pitch, volume, lang, voiceName }
 * @returns {void}
 */
export const speak = (text, options = {}) => {
  if (!isSynthesisSupported()) return;

  // Cancel any ongoing speech
  stopSpeaking();

  if (!text || !text.trim()) return;

  // Trim to a reasonable length to avoid extremely long reads
  const truncated = text.length > 1500 ? text.slice(0, 1500) + '…' : text;

  _currentUtterance = new SpeechSynthesisUtterance(truncated);
  _currentUtterance.rate   = options.rate   ?? 0.95;
  _currentUtterance.pitch  = options.pitch  ?? 1.0;
  _currentUtterance.volume = options.volume ?? 1.0;
  _currentUtterance.lang   = options.lang   ?? 'en-US';

  // Prefer a natural-sounding voice if available
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v =>
    v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Samantha')
  );
  if (preferred) _currentUtterance.voice = preferred;

  window.speechSynthesis.speak(_currentUtterance);
};

/**
 * Stop any ongoing TTS speech immediately.
 */
export const stopSpeaking = () => {
  if (isSynthesisSupported()) {
    window.speechSynthesis.cancel();
  }
  _currentUtterance = null;
};

/** True if TTS is currently speaking */
export const isSpeaking = () =>
  isSynthesisSupported() && window.speechSynthesis.speaking;
