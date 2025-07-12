# ISEE Tutor Frontend

A React 18 TypeScript application designed for kiosk-mode operation on touchscreen devices.

## Features

- **Kiosk Mode Optimized**: Fullscreen, no browser chrome, auto-recovery
- **Touch-First Design**: Large touch targets, gesture support
- **Voice Interaction**: Real-time audio streaming and speech recognition
- **WebSocket Communication**: Live updates with the backend
- **PWA Support**: Installable, works offline
- **Responsive**: Adapts to different screen sizes

## Development

```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build
```

## Kiosk Mode Features

1. **Auto-Fullscreen**: Requests fullscreen on first interaction
2. **Cursor Hiding**: Hides cursor after 3 seconds of inactivity
3. **Context Menu Disabled**: No right-click menu
4. **Navigation Prevention**: Prevents back button and refresh
5. **Error Recovery**: Auto-reloads on critical errors
6. **Touch Optimized**: All interactions designed for touch

## Environment Variables

- `REACT_APP_API_URL`: Backend API URL (default: http://localhost:8000)
- `REACT_APP_WS_URL`: WebSocket URL (default: ws://localhost:8000)

## Project Structure

```
src/
├── components/        # React components
│   ├── HomeScreen.tsx
│   ├── VoiceInteraction.tsx
│   └── LearningDashboard.tsx
├── contexts/         # React contexts
│   ├── AppStateContext.tsx
│   ├── AudioContext.tsx
│   └── WebSocketContext.tsx
├── styles/          # Global styles
│   └── GlobalStyles.tsx
├── hooks/           # Custom React hooks
├── utils/           # Utility functions
└── types/           # TypeScript types
```

## Building for Production

```bash
# Build optimized production bundle
npm run build

# Serve locally to test
npx serve -s build
```

## Deployment

For kiosk mode deployment, see `/docs/kiosk-mode-setup.md` in the main project.

## Browser Support

- Chrome/Chromium (recommended for kiosk mode)
- Firefox
- Safari
- Edge

## PWA Installation

The app can be installed as a Progressive Web App:
1. Visit the app in Chrome
2. Click the install button in the address bar
3. Or go to Settings > Install App

## Accessibility

- Keyboard navigation support
- Screen reader compatible
- High contrast mode support
- Focus indicators for all interactive elements