# ISEE Tutor Frontend Preview

## Home Screen
- **Background**: Purple gradient (Alexa-like)
- **Title**: "Welcome to ISEE Tutor" 
- **3 Mode Selection Cards**:
  - 📚 Tutor Mode - ISEE test preparation
  - 🤗 Friend Mode - Chat & learn
  - ✨ Smart Mode - Adaptive switching
- **Start Learning Button**: Large, centered

## Voice Interaction Screen
- **Minimal Interface**: Focus on voice
- **Large Microphone Button**: Pulses when listening
- **Visual Feedback**: Audio level indicator
- **Transcript Display**: Shows conversation
- **Mode Indicator**: Top-right corner

## Learning Dashboard
- **Statistics Cards**:
  - Questions Answered
  - Accuracy Rate
  - Study Streak
  - Total Study Time
- **Progress Bars**: For each subject
- **Clean, Touch-Friendly Design**

## Kiosk Features Implemented:
✅ Auto-fullscreen request
✅ Cursor hiding after 3 seconds
✅ Right-click disabled
✅ Back button prevention
✅ Auto-recovery on errors
✅ PWA installable
✅ Touch-optimized UI
✅ No browser chrome in fullscreen

## To Test the Frontend:

1. **Quick Test** (if API already running):
   ```bash
   cd /home/tutor/iseetutor/frontend
   npm start
   ```

2. **Full Environment**:
   ```bash
   ./start_frontend_dev.sh
   ```

3. **Production Build**:
   ```bash
   cd frontend
   npm run build
   npx serve -s build
   ```

The app is designed to work exactly like Alexa/Google Home devices - boots directly to the app with no desktop visible.