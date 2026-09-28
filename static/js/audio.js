// Speech Engine for KabaadSetu
// Handles Vernacular Text-to-Speech in Marathi, Hindi, Telugu, and English

const AudioEngine = {
  synth: window.speechSynthesis,
  isAudioEnabled: true,
  currentUtterance: null,

  speak(text, langCode = 'mr') {
    if (!this.isAudioEnabled || !this.synth) return;

    // Cancel any previous ongoing speech
    this.synth.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Select appropriate BCP 47 language code
    const langMap = {
      'mr': 'mr-IN',
      'hi': 'hi-IN',
      'te': 'te-IN',
      'en': 'en-IN'
    };
    
    utterance.lang = langMap[langCode] || 'hi-IN';
    utterance.rate = 0.9; // Slightly slower for low-literacy clarity
    utterance.pitch = 1.0;

    // Find available voices in browser
    const voices = this.synth.getVoices();
    const voice = voices.find(v => v.lang === utterance.lang || v.lang.startsWith(langCode));
    if (voice) {
      utterance.voice = voice;
    }

    this.currentUtterance = utterance;
    this.synth.speak(utterance);
  },

  stop() {
    if (this.synth) {
      this.synth.cancel();
    }
  },

  toggleAudio() {
    this.isAudioEnabled = !this.isAudioEnabled;
    if (!this.isAudioEnabled) {
      this.stop();
    }
    return this.isAudioEnabled;
  }
};

// Pre-load voices if supported
if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
  window.speechSynthesis.onvoiceschanged = () => {
    window.speechSynthesis.getVoices();
  };
}
