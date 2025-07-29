/**
 * Sound effects manager for achievement celebrations
 */

import { useCallback } from 'react';

// Sound effect URLs (you can replace with actual sound files)
const SOUNDS = {
  achievement: 'data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE',
  confetti: 'data:audio/wav;base64,UklGRjAGAABXQVZFZm10IBAAAAABAAEAiBUAAIgVAAABAAgAZGF0YQwGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBTGH0fPTgjMGHm7A7+OZURE',
  levelUp: 'data:audio/wav;base64,UklGRgoEAABXQVZFZm10IBAAAAABAAEAiBUAAIgVAAABAAgAZGF0YeYDAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+Dyvv',
  star: 'data:audio/wav;base64,UklGRrQFAABXQVZFZm10IBAAAAABAAEAiBUAAIgVAAABAAgAZGF0YZAFAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBQ',
};

class SoundEffectsManager {
  private sounds: Map<string, HTMLAudioElement> = new Map();
  private enabled: boolean = true;
  private volume: number = 0.5;

  constructor() {
    this.loadSounds();
    this.loadSettings();
  }

  private loadSounds() {
    Object.entries(SOUNDS).forEach(([name, url]) => {
      const audio = new Audio(url);
      audio.volume = this.volume;
      this.sounds.set(name, audio);
    });
  }

  private loadSettings() {
    const savedEnabled = localStorage.getItem('soundEffectsEnabled');
    const savedVolume = localStorage.getItem('soundEffectsVolume');
    
    if (savedEnabled !== null) {
      this.enabled = savedEnabled === 'true';
    }
    
    if (savedVolume !== null) {
      this.volume = parseFloat(savedVolume);
      this.updateVolume();
    }
  }

  play(soundName: keyof typeof SOUNDS) {
    if (!this.enabled) return;

    const sound = this.sounds.get(soundName);
    if (sound) {
      // Clone the audio to allow multiple simultaneous plays
      const audioClone = sound.cloneNode() as HTMLAudioElement;
      audioClone.volume = this.volume;
      audioClone.play().catch(err => {
        console.warn('Failed to play sound:', err);
      });
    }
  }

  setEnabled(enabled: boolean) {
    this.enabled = enabled;
    localStorage.setItem('soundEffectsEnabled', enabled.toString());
  }

  setVolume(volume: number) {
    this.volume = Math.max(0, Math.min(1, volume));
    localStorage.setItem('soundEffectsVolume', this.volume.toString());
    this.updateVolume();
  }

  private updateVolume() {
    this.sounds.forEach(sound => {
      sound.volume = this.volume;
    });
  }

  getEnabled() {
    return this.enabled;
  }

  getVolume() {
    return this.volume;
  }

  // Play a sequence of sounds
  playSequence(sounds: Array<{ sound: keyof typeof SOUNDS; delay: number }>) {
    if (!this.enabled) return;

    sounds.forEach(({ sound, delay }) => {
      setTimeout(() => this.play(sound), delay);
    });
  }

  // Play a random celebration sound
  playRandomCelebration() {
    const celebrationSounds: Array<keyof typeof SOUNDS> = ['achievement', 'confetti', 'levelUp', 'star'];
    const randomSound = celebrationSounds[Math.floor(Math.random() * celebrationSounds.length)];
    this.play(randomSound);
  }
}

// Create singleton instance
export const soundEffects = new SoundEffectsManager();

// React hook for sound effects
export const useSoundEffects = () => {
  const playSound = useCallback((sound: keyof typeof SOUNDS) => {
    soundEffects.play(sound);
  }, []);

  const playSequence = useCallback((sounds: Array<{ sound: keyof typeof SOUNDS; delay: number }>) => {
    soundEffects.playSequence(sounds);
  }, []);

  const playRandomCelebration = useCallback(() => {
    soundEffects.playRandomCelebration();
  }, []);

  return {
    playSound,
    playSequence,
    playRandomCelebration,
    setEnabled: soundEffects.setEnabled.bind(soundEffects),
    setVolume: soundEffects.setVolume.bind(soundEffects),
    getEnabled: soundEffects.getEnabled.bind(soundEffects),
    getVolume: soundEffects.getVolume.bind(soundEffects),
  };
};