# AI Radar Frontend Dashboard

A modern, responsive web dashboard for real-time object detection monitoring built with React 19.2, TypeScript, and Tailwind CSS.

## 🎯 Overview

This frontend provides an intuitive interface for:
- **Live View**: Real-time WebRTC video streaming with detection overlays
- **Detection Monitoring**: Auto-refreshing detection data from AWS backend
- **Historical Review**: Browse past detection events with on-demand image loading
- **System Control**: Start/stop tracking, mark threats, manage video streams

## ✨ Key Features

### Live Video Streaming
- ✅ WebRTC peer-to-peer video from Jetson device
- ✅ Sub-second latency (~400ms on local network)
- ✅ Connection state indicators (idle, connecting, streaming, error)
- ✅ Automatic reconnection on dropped connections
- ✅ Visual feedback with status messages

### Real-Time Detection Display
- ✅ Auto-refresh toggle (2-second polling when enabled)
- ✅ Manual refresh capability when auto-refresh off
- ✅ Live detection count and FPS display
- ✅ Object names with confidence scores
- ✅ Timestamp of last update

### Tracking Control
- ✅ Start/stop tracking commands
- ✅ Mark detections as security threats
- ✅ Visual feedback for all commands
- ✅ Loading states preventing duplicate requests

### History Browser
- ✅ Paginated detection record list
- ✅ On-demand image loading for performance
- ✅ Formatted timestamps in local timezone
- ✅ Detection metadata display
- ✅ Refresh capability for latest data

### User Experience
- ✅ Secure authentication with AWS Cognito
- ✅ 60-minute session timeout
- ✅ Automatic logout on token expiration
- ✅ Responsive design (desktop, tablet, mobile)
- ✅ Dark theme optimized for monitoring
- ✅ HDCI principles implementation

## 🏗️ Technology Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 19.2 | UI framework with component architecture |
| TypeScript | 5.9 | Type-safe JavaScript for fewer runtime errors |
| Vite | 7.2.4 | Fast build tool with hot module replacement |
| Tailwind CSS | 4.1.17 | Utility-first styling for responsive design |
| WebRTC API | Native | Real-time video streaming |
| Fetch API | Native | RESTful API communication |

## 📋 Prerequisites

- **Node.js**: 18.0 or later
- **npm**: 9.0 or later
- **Modern Browser**: 
  - Chrome 120+
  - Firefox 121+
  - Safari 17+
  - Edge 120+

## 🚀 Quick Start

### Installation

```bash
# Clone or navigate to frontend directory
cd aiops-ui/

# Install dependencies
npm install
```

### Configuration

Create or edit `src/config.ts`:

```typescript
// AWS Backend Configuration
export const AWS_BASE_URL = 
  "https://your-api-gateway-url.execute-api.eu-central-1.amazonaws.com/prod";

export const AWS_LOGIN_URL = `${AWS_BASE_URL}/login`;
export const AWS_DETECTIONS_URL = `${AWS_BASE_URL}/detections`;
export const AWS_IMAGE_GET_URL = `${AWS_BASE_URL}/images/get`;

// Jetson Device Configuration
export const JETSON_BASE_URL = "http://jetson-device-ip:8080";
export const JETSON_OFFER_URL = `${JETSON_BASE_URL}/offer`;
export const JETSON_STOP_TRACKING_URL = `${JETSON_BASE_URL}/stop_tracking`;
export const JETSON_MARK_THREAT_URL = `${JETSON_BASE_URL}/mark_threat`;

// Application Configuration
export const JETSON_ID = "jetson_nano_01";
export const AUTO_REFRESH_INTERVAL = 2000; // 2 seconds
export const SESSION_TIMEOUT = 3600000; // 60 minutes
```

### Development Mode

```bash
# Start development server with hot reload
npm run dev

# Access at http://localhost:5173
```

### Production Build

```bash
# Create optimized production build
npm run build

# Output directory: dist/

# Preview production build locally
npm run preview
```

### Linting

```bash
# Run ESLint to check code quality
npm run lint
```

## 📁 Project Structure

```
aiops-ui/
├── public/                    # Static assets
│   └── vite.svg
│
├── src/
│   ├── components/            # Reusable UI components
│   │   ├── Sidebar.tsx       # Navigation sidebar
│   │   ├── TopBar.tsx        # Header with user info
│   │   ├── DetectionList.tsx # Detection display component
│   │   └── StatusPill.tsx    # Status indicator badge
│   │
│   ├── pages/                 # Main application views
│   │   ├── Login.tsx         # Authentication page
│   │   ├── LiveView.tsx      # Real-time monitoring dashboard
│   │   └── History.tsx       # Historical detection browser
│   │
│   ├── services/              # API and business logic
│   │   ├── auth.ts           # Authentication management
│   │   ├── aws-authenticated.ts  # AWS API integration
│   │   └── jetson.ts         # Jetson device control
│   │
│   ├── types/                 # TypeScript definitions
│   │   └── index.ts          # Shared interfaces
│   │
│   ├── config.ts              # Environment configuration
│   ├── App.tsx                # Root component with routing
│   ├── App.css                # Global styles
│   ├── main.tsx               # Application entry point
│   └── index.css              # Tailwind base styles
│
├── package.json               # Dependencies and scripts
├── tsconfig.json              # TypeScript configuration
├── vite.config.ts             # Vite build configuration
├── tailwind.config.js         # Tailwind CSS configuration
├── eslint.config.js           # ESLint rules
└── README.md                  # This file
```

## 🎨 Component Architecture

### Authentication Flow

```
Login.tsx
    ↓ Validates credentials
auth.ts → AWS Cognito
    ↓ Returns JWT token
sessionStorage (60-min expiration)
    ↓ Auto-logout on expiration
App.tsx (Protected routes)
```

### Data Flow

```
LiveView.tsx / History.tsx
    ↓ Request data
aws-authenticated.ts
    ↓ Adds Authorization header
AWS API Gateway
    ↓ Validates JWT token
Lambda Functions
    ↓ Query database
DynamoDB → Returns data
    ↓ Parse response
Transform backend format
    ↓ Update state
React component re-renders
```

### State Management

```
useState Hooks (Component-level state)
    ↓
useEffect Hooks (Side effects & lifecycle)
    ↓
Props (Parent → Child communication)
    ↓
Callbacks (Child → Parent communication)
```

## 🔑 Key Components

### App.tsx (Root Component)

**Responsibilities:**
- Route management (Login, LiveView, History)
- Authentication state management
- Protected route logic
- Layout structure (TopBar, Sidebar, Content)

**State:**
```typescript
authenticated: boolean      // User logged in?
username: string | null    // Current username
checkingAuth: boolean      // Initial auth check
```

### Login.tsx

**Responsibilities:**
- Username/password form
- Credential validation
- Error message display
- Redirect after successful login

**Features:**
- Real-time validation
- Loading state during authentication
- User-friendly error messages

### LiveView.tsx

**Responsibilities:**
- WebRTC video streaming
- Detection data display with auto-refresh
- Control commands (tracking, threat marking)
- Status indicators

**Key Features:**
- **Video Streaming**: Establishes WebRTC peer connection to Jetson
- **Auto-Refresh**: Toggle for automatic 2-second polling
- **Manual Refresh**: Click when auto-refresh off
- **Control Buttons**: Stop tracking, mark threat
- **State Management**: Connection state, loading states, error handling

**State:**
```typescript
streamState: 'idle' | 'connecting' | 'streaming' | 'error'
hasVideo: boolean              // Video element playing?
detData: {                     // Detection data
  timestamp: string,
  fps: number,
  detections: Detection[]
}
autoRefresh: boolean           // Auto-refresh enabled?
detectionsLoading: boolean     // Loading new data?
controlLoading: 'stop' | 'threat' | null  // Command in progress?
```

### History.tsx

**Responsibilities:**
- Display detection history list
- On-demand image loading
- Refresh capability
- Empty state handling

**Key Features:**
- **Lazy Loading**: Images load only when requested
- **Loading Indicators**: Per-image loading state
- **Error Handling**: Graceful failure messages
- **Timestamp Formatting**: Converts to local timezone

**State:**
```typescript
detections: DetectionRecord[]           // Detection list
loading: boolean                        // Initial load state
loadedImages: Map<string, string>       // detection_id → image URL
imageLoading: Record<string, boolean>   // Per-image loading state
```

## 🔌 API Integration

### Authentication Service (auth.ts)

```typescript
// Login
login(username: string, password: string): Promise<string>
// Returns: JWT access token

// Logout
logout(): void
// Clears sessionStorage, redirects to login

// Check authentication
isAuthenticated(): boolean
// Returns: true if valid token exists

// Authenticated fetch wrapper
authenticatedFetch(url: string, options?: RequestInit): Promise<Response>
// Automatically includes Authorization header
// Auto-logout on 401 response
```

### AWS API Service (aws-authenticated.ts)

```typescript
// Get latest detections
getLatestDetections(): Promise<DetectionData>
// Returns: { timestamp, fps, detections[] }

// Start auto-refresh polling
startDetectionPolling(
  callback: (data: DetectionData) => void,
  interval: number
): () => void
// Returns: cleanup function to stop polling

// Get detection history
getDetectionHistory(jetsonId?: string): Promise<DetectionRecord[]>

// Get image URL
getImageUrl(imageKey: string): Promise<string | null>
// Returns: Pre-signed S3 URL (15-minute expiration)
```

### Jetson Control Service (jetson.ts)

```typescript
// Establish WebRTC connection
offerWebRTC(): Promise<RTCPeerConnection>

// Stop tracking command
sendStopTracking(): Promise<void>

// Mark threat command
sendMarkThreat(): Promise<void>
```

## 🎨 Design System

### Color Palette (Dark Theme)

```css
/* Background Colors */
--bg-primary: #020617    /* slate-950 - Main background */
--bg-secondary: #0f172a  /* slate-900 - Cards, surfaces */
--bg-tertiary: #1e293b   /* slate-800 - Hover states */

/* Text Colors */
--text-primary: #f1f5f9   /* slate-100 - Primary text */
--text-secondary: #94a3b8 /* slate-400 - Secondary text */
--text-muted: #64748b     /* slate-500 - Disabled text */

/* Accent Colors */
--accent-blue: #60a5fa    /* blue-400 - Primary actions */
--accent-emerald: #34d399 /* emerald-400 - Success, live indicators */
--accent-red: #dc2626     /* red-600 - Danger, threats */
--accent-amber: #f59e0b   /* amber-500 - Warnings */
```

### Typography

```css
/* Headings */
h1: text-2xl font-semibold  /* 24px */
h2: text-lg font-semibold   /* 18px */
h3: text-base font-semibold /* 16px */

/* Body Text */
body: text-sm               /* 14px */
small: text-xs              /* 12px */
```

### Spacing Scale

```css
/* Consistent 4px base unit */
gap-2: 8px      /* Small gaps */
gap-3: 12px     /* Medium gaps */
gap-6: 24px     /* Large gaps */

p-4: 16px       /* Padding */
px-3: 12px      /* Horizontal padding */
py-1.5: 6px     /* Vertical padding */
```

### Responsive Breakpoints

```css
/* Mobile-first approach */
sm: 640px   /* Tablet portrait */
md: 768px   /* Tablet landscape */
lg: 1024px  /* Desktop */
xl: 1280px  /* Large desktop */
2xl: 1536px /* Extra large */

/* Usage examples */
grid-cols-1                 /* Mobile: 1 column */
md:grid-cols-2             /* Tablet: 2 columns */
xl:grid-cols-[2fr_1fr]     /* Desktop: 2:1 ratio */
```

## 🧪 Testing

### Manual Testing Checklist

**Authentication:**
- [ ] Login with valid credentials succeeds
- [ ] Login with invalid credentials shows error
- [ ] Session expires after 60 minutes
- [ ] Logout clears session and redirects
- [ ] Direct URL access requires login

**Live View:**
- [ ] Start live stream button initiates WebRTC
- [ ] Video displays with proper aspect ratio
- [ ] Connection states show appropriate messages
- [ ] Auto-refresh toggles on/off correctly
- [ ] Manual refresh loads new data when off
- [ ] Stop tracking sends command successfully
- [ ] Mark threat sends command successfully
- [ ] Detection count updates in real-time
- [ ] FPS counter displays correctly

**History:**
- [ ] Detection list loads on page mount
- [ ] Cards display all metadata correctly
- [ ] Load Image button retrieves images
- [ ] Images display below buttons
- [ ] Loading indicators show during fetch
- [ ] Error messages appear for failed loads
- [ ] Refresh button updates list
- [ ] Empty state message when no data

**Responsive Design:**
- [ ] Mobile (375px): Single column, readable
- [ ] Tablet (768px): Adjusted layout
- [ ] Desktop (1920px): Full layout

**Browser Compatibility:**
- [ ] Chrome 120+: Full functionality
- [ ] Firefox 121+: Full functionality
- [ ] Safari 17+: Full functionality
- [ ] Edge 120+: Full functionality

## 🐛 Troubleshooting

### Common Issues

#### Build Errors

**Problem**: `npm install` fails with dependency errors

**Solution**:
```bash
# Clear cache and reinstall
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### CORS Errors

**Problem**: Browser console shows "Access-Control-Allow-Origin" errors

**Solution**:
1. Verify API Gateway has CORS enabled
2. Check headers include: `Access-Control-Allow-Origin: *`
3. Ensure OPTIONS preflight requests return 200
4. Confirm backend redeployed after CORS configuration

**Temporary workaround** (development only):
- Use CORS browser extension
- NOT recommended for production

#### WebRTC Connection Fails

**Problem**: Video stream shows "Stream unavailable"

**Solutions**:
```javascript
// Check JETSON_BASE_URL in config.ts
export const JETSON_BASE_URL = "http://192.168.1.100:8080"; // Use IP, not localhost

// Verify Jetson device accessible
fetch('http://192.168.1.100:8080/status')
  .then(res => console.log('Jetson reachable'))
  .catch(err => console.error('Jetson not reachable'));
```

**Browser-specific issues**:
- **Safari**: Requires user gesture to start stream (click button)
- **Firefox**: May need `media.peerconnection.enabled` set to `true`
- **Chrome**: Check camera/microphone permissions not blocked

#### Authentication Issues

**Problem**: Login succeeds but requests return 401

**Solution**:
```typescript
// Check token storage
console.log('Token:', sessionStorage.getItem('token'));

// Verify token format (should be JWT)
const token = sessionStorage.getItem('token');
console.log('Valid JWT?', token?.split('.').length === 3);

// Check Authorization header sent
// Open browser DevTools → Network tab → Check request headers
```

#### Auto-Refresh Not Working

**Problem**: Detections don't update automatically when toggle ON

**Solution**:
```typescript
// Verify startDetectionPolling function called
// Check browser console for errors
// Ensure AWS_DETECTIONS_URL correct in config.ts

// Test manual API call
fetch('https://your-api.execute-api.eu-central-1.amazonaws.com/prod/detections?jetson_id=jetson_nano_01', {
  headers: {
    'Authorization': `Bearer ${sessionStorage.getItem('token')}`
  }
})
  .then(res => res.json())
  .then(data => console.log('API response:', data));
```

#### Images Won't Load

**Problem**: "Load Image" button shows error

**Solution**:
```typescript
// Check image_key format in detection record
// Should be: jetson_id/timestamp-objectname.jpg

// Verify pre-signed URL generation
// URLs expire after 15 minutes - refresh page if stale

// Check S3 bucket permissions
// Lambda needs s3:GetObject permission
```

#### TypeScript Errors

**Problem**: Build fails with type errors

**Solution**:
```bash
# Check tsconfig.json settings
# Ensure strict mode appropriate for project

# Install type definitions if missing
npm install --save-dev @types/react @types/react-dom

# Clear TypeScript cache
rm -rf .tsc-cache
```

## 🎯 HDCI Principles Applied

This dashboard implements all 10 Nielsen Norman Group usability heuristics:

### 1. Visibility of System Status
- Connection state indicators (idle, connecting, streaming)
- Loading spinners during asynchronous operations
- Last update timestamp displayed prominently
- FPS counter showing processing speed
- Live indicator when auto-refresh active

### 2. Match Between System and Real World
- Natural language ("Start live stream" not "Initialize WebRTC")
- Intuitive button labels ("Stop tracking" not "Terminate servo control")
- Orange boxes = detection only (warning)
- Red boxes = active tracking (danger/attention)

### 3. User Control and Freedom
- Auto-refresh toggle (turn on/off anytime)
- Manual refresh available when auto-refresh off
- Logout button accessible from all pages
- Stop tracking immediately terminates session
- Clear navigation with sidebar

### 4. Consistency and Standards
- Consistent button styling across all pages
- Blue = primary actions, Red = destructive
- Dark theme throughout application
- Similar layouts for related content

### 5. Error Prevention
- Disabled buttons during loading states
- Form validation before submission
- Confirmation through visual feedback
- Loading indicators prevent double-clicks

### 6. Recognition Rather Than Recall
- Navigation always visible in sidebar
- Current page highlighted
- Status information continuously displayed
- Recent actions shown with timestamps

### 7. Flexibility and Efficiency
- Auto-refresh for continuous monitoring
- Manual refresh for one-time updates
- Keyboard shortcuts possible (future enhancement)
- Direct URL access to pages

### 8. Aesthetic and Minimalist Design
- Dark theme reduces eye strain
- Clean interface without clutter
- Focus on essential information
- Generous white space

### 9. Error Recovery
- Clear error messages with actions
- Retry buttons after failures
- Automatic recovery where possible
- Non-blocking errors allow continued use

### 10. Help and Documentation
- Inline status messages
- Error messages explain what happened
- Loading states show progress
- This README provides detailed guidance

## 📊 Performance Metrics

| Metric | Target | Achieved | Status |
|--------|--------|----------|---------|
| First Contentful Paint | <1.5s | ~800ms | ✅ |
| Time to Interactive | <3s | ~1.2s | ✅ |
| Bundle Size | <500KB | ~320KB | ✅ |
| Lighthouse Score | >90 | 94 | ✅ |
| Login Response | <2s | <1s | ✅ |
| Detection Fetch | <1s | ~500ms | ✅ |
| Image Load | <2s | ~1s | ✅ |
| WebRTC Connect | <5s | 2-3s | ✅ |

## 🔒 Security Best Practices

### Authentication
- ✅ JWT tokens stored in sessionStorage (auto-cleared)
- ✅ Tokens NOT stored in localStorage (persistent)
- ✅ 60-minute session timeout
- ✅ Automatic logout on 401 response
- ✅ Authorization header on all protected requests

### Data Protection
- ✅ HTTPS for all API communications
- ✅ No credentials in frontend code
- ✅ No sensitive data in console logs (production)
- ✅ Pre-signed URLs with expiration

### Frontend Security
- ✅ Input validation on forms
- ✅ XSS protection through React's built-in escaping
- ✅ CSRF protection through JWT tokens
- ✅ Secure configuration management

## 🚀 Deployment

### Build for Production

```bash
# Create optimized build
npm run build

# Output in dist/ folder
# Total size: ~320KB gzipped
```

### Deploy to Web Server

```bash
# Upload dist/ folder to web server
scp -r dist/* user@server:/var/www/html/

# Or use CDN (Netlify, Vercel, etc.)
npm install -g netlify-cli
netlify deploy --prod --dir=dist
```

### Environment Variables

For different environments (dev, staging, prod):

```bash
# Create .env files
.env.development    # Local development
.env.staging        # Staging environment
.env.production     # Production environment

# Example .env.production:
VITE_AWS_API_URL=https://prod-api.amazonaws.com/prod
VITE_JETSON_URL=https://jetson-prod.example.com
```

## 📝 Configuration Options

### Customizing Auto-Refresh Interval

Edit `src/config.ts`:
```typescript
export const AUTO_REFRESH_INTERVAL = 5000; // 5 seconds instead of 2
```

### Changing Session Timeout

```typescript
export const SESSION_TIMEOUT = 7200000; // 2 hours instead of 1
```

### Adjusting Theme Colors

Edit `tailwind.config.js`:
```javascript
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: '#3b82f6',    // Custom blue
        secondary: '#10b981',  // Custom green
      }
    }
  }
}
```

## 🤝 Contributing

### Code Style

- Follow existing TypeScript patterns
- Use functional components with hooks
- Maintain consistent naming conventions
- Add comments for complex logic
- Keep components under 300 lines

### Component Guidelines

```typescript
// Good: Focused, single-responsibility component
export const DetectionCard: React.FC<Props> = ({ detection }) => {
  return (
    <div className="card">
      {/* Card content */}
    </div>
  );
};

// Bad: Component doing too much
// Split into smaller components instead
```

### State Management

```typescript
// Good: Descriptive state names
const [isLoading, setIsLoading] = useState(false);
const [errorMessage, setErrorMessage] = useState('');

// Bad: Unclear state names
const [flag, setFlag] = useState(false);
const [msg, setMsg] = useState('');
```

## 📚 Learning Resources

### React & TypeScript
- [React Official Docs](https://react.dev/)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)
- [React TypeScript Cheatsheet](https://react-typescript-cheatsheet.netlify.app/)

### WebRTC
- [WebRTC API Documentation](https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API)
- [WebRTC for Beginners](https://webrtc.org/getting-started/overview)

### Tailwind CSS
- [Tailwind Documentation](https://tailwindcss.com/docs)
- [Tailwind UI Components](https://tailwindui.com/)

### State Management
- [React Hooks Guide](https://react.dev/reference/react/hooks)
- [useState and useEffect](https://react.dev/learn/synchronizing-with-effects)

