import { Global, css } from '@emotion/react';

const GlobalStyles = () => (
  <Global
    styles={css`
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
        -webkit-tap-highlight-color: transparent;
        -webkit-touch-callout: none;
        -webkit-user-select: none;
        -khtml-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
      }

      html, body {
        width: 100%;
        height: 100%;
        overflow: hidden;
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
          'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
          sans-serif;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
      }

      body {
        margin: 0;
        padding: 0;
        overscroll-behavior: none;
      }

      #root {
        width: 100%;
        height: 100%;
      }

      /* Disable pull-to-refresh on mobile */
      body {
        overscroll-behavior-y: contain;
      }

      /* Hide scrollbars */
      ::-webkit-scrollbar {
        display: none;
      }

      * {
        -ms-overflow-style: none;
        scrollbar-width: none;
      }

      /* Prevent text selection */
      * {
        -webkit-user-select: none;
        -moz-user-select: none;
        -ms-user-select: none;
        user-select: none;
      }

      /* Allow text selection only in input fields */
      input, textarea {
        -webkit-user-select: text;
        -moz-user-select: text;
        -ms-user-select: text;
        user-select: text;
      }

      /* Prevent zooming on mobile */
      input, select, textarea {
        font-size: 16px;
      }

      /* Disable browser chrome on standalone mode */
      @media all and (display-mode: standalone) {
        body {
          padding: env(safe-area-inset-top) env(safe-area-inset-right) 
                  env(safe-area-inset-bottom) env(safe-area-inset-left);
        }
      }

      /* Animation performance */
      * {
        -webkit-transform: translateZ(0);
        -webkit-backface-visibility: hidden;
        -webkit-perspective: 1000;
      }

      /* Focus styles for accessibility */
      :focus {
        outline: 2px solid #667eea;
        outline-offset: 2px;
      }

      button:focus,
      a:focus {
        outline: 3px solid #667eea;
        outline-offset: 2px;
      }

      /* Loading animation */
      @keyframes pulse {
        0% {
          opacity: 1;
        }
        50% {
          opacity: 0.5;
        }
        100% {
          opacity: 1;
        }
      }

      .loading {
        animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
      }
    `}
  />
);

export default GlobalStyles;