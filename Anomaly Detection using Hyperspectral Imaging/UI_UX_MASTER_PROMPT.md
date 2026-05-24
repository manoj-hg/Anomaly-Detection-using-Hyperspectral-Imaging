# Master Prompt for AI-Powered Geospatial Anomaly Detection UI/UX Enhancement

## Project Overview
This is an AI-powered geospatial anomaly detection platform for camouflaged object detection using spectral data. The system uses Vision Transformer (ViT), Isolation Forest, Autoencoder, and Ensemble Stacking models to detect anomalies in satellite imagery with domain-specific applications for Defense, Agriculture, and Geological Surveying.

## Current Design System

### Color Palette (Spectral Cyberpunk Theme)
- **Background:** #0A0A12 (deep dark blue-black)
- **Accent Cyan:** #00F2FF (primary accent)
- **Accent Magenta:** #BC13FE (secondary accent)
- **Accent Lime:** #39FF14 (success/highlight)
- **Gradients:** 
  - Primary: linear-gradient(135deg, #00F2FF 0%, #BC13FE 100%)
  - Secondary: linear-gradient(135deg, #BC13FE 0%, #39FF14 100%)
  - Success: linear-gradient(135deg, #39FF14 0%, #00F2FF 100%)

### Typography
- **Headings:** 'Orbitron' (futuristic, uppercase, letter-spacing)
- **Body/Data:** 'JetBrains Mono' (monospace for technical data)
- **Font Sizes:** 
  - Headers: 0.9rem - 1.2rem
  - Body: 0.8rem - 1rem
  - Data/Metrics: Monospace, 500 weight

### Current UI Structure
- **Hero Section:** Large landing with stats and radar visualization
- **Navigation:** Horizontal nav bar with 6 pages (Dashboard, Detection, Analysis, Defense, Agriculture, Geological)
- **Frame-based Layout:** Grid system with bordered frames for different content areas
- **Pages:**
  - Dashboard: Overview with charts and metrics
  - Detection: Main detection interface with parameters and results
  - Analysis: Spectral analysis tools
  - Defense: Domain-specific defense detection
  - Agriculture: Crop health and field analysis
  - Geological: Mineral deposit surveying

### Current Design Issues
- Frames can feel congested with too many borders
- Background grid animation may be distracting
- Navigation buttons could be more modern
- Need smoother transitions between pages
- Maps need better integration
- Overall spacing could be improved
- Need more micro-interactions and animations

## UI/UX Enhancement Goals

### 1. Modern Design System
- Implement a cleaner, more minimalist approach
- Use glassmorphism effects with proper blur and transparency
- Add subtle gradients instead of harsh borders
- Improve whitespace and breathing room
- Create a more cohesive visual hierarchy

### 2. Enhanced Animations
- Smooth page transitions with fade/slide effects
- Micro-interactions on buttons and interactive elements
- Loading states with animated indicators
- Chart animations on data updates
- Map zoom/pan animations
- Hover effects with smooth transitions
- Particle effects for hero section
- Progress bar animations
- Toast notification animations

### 3. Improved Navigation
- More intuitive navigation design
- Active state indicators
- Smooth scroll to sections
- Mobile-responsive navigation
- Breadcrumb navigation for deep pages

### 4. Better Data Visualization
- Animated charts with smooth transitions
- Interactive data points
- Tooltips and hover states
- Color-coded data categories
- Responsive chart sizing
- Real-time data update animations

### 5. Map Integration
- Seamless map integration with UI
- Custom map markers with animations
- Smooth zoom and pan
- Layer toggle animations
- Map control styling to match theme

### 6. Form & Input Design
- Modern input field styling
- Floating labels
- Validation states with animations
- Focus states with glow effects
- Smooth form transitions

### 7. Responsive Design
- Mobile-first approach
- Responsive grid layouts
- Touch-friendly interactions
- Adaptive typography
- Mobile navigation patterns

### 8. Accessibility
- Proper color contrast ratios
- Keyboard navigation support
- Screen reader compatibility
- Focus indicators
- ARIA labels

## Specific Animation Requirements

### Page Transitions
- Fade in/out with 0.3s ease
- Slide up effect for new content
- Staggered animation for grid items
- Smooth opacity transitions

### Button Interactions
- Hover: Scale 1.05, shadow increase
- Click: Scale 0.95, ripple effect
- Active: Glow effect with cyan accent
- Loading: Spinner or progress indicator

### Chart Animations
- Initial load: Grow from bottom
- Data update: Smooth transition
- Hover: Highlight with tooltip
- Legend: Fade in on load

### Map Animations
- Initial load: Fade in with zoom
- Marker drop: Bounce effect
- Layer toggle: Fade in/out
- Zoom: Smooth transition

### Loading States
- Skeleton screens for content
- Progress bars with animation
- Spinner with gradient
- Pulse effect for waiting states

### Micro-interactions
- Card hover: Lift and shadow
- Input focus: Border glow
- Checkbox: Custom animation
- Toggle: Smooth slide
- Dropdown: Fade and slide

## Design Principles to Follow

1. **Minimalism:** Remove unnecessary elements, focus on content
2. **Consistency:** Unified design language across all pages
3. **Performance:** Smooth 60fps animations
4. **Accessibility:** WCAG AA compliance
5. **Responsiveness:** Works on all screen sizes
6. **User-Centric:** Intuitive and easy to use
7. **Visual Hierarchy:** Clear information architecture
8. **Feedback:** Immediate response to user actions

## Technical Requirements

- Use CSS Grid and Flexbox for layouts
- CSS custom properties for theming
- CSS transitions and keyframe animations
- JavaScript for complex interactions
- Intersection Observer for scroll animations
- RequestAnimationFrame for smooth animations
- CSS transforms for performance
- Backdrop-filter for glassmorphism

## Color Scheme Refinement

### Primary Colors
- Background: #0A0A12 → #0D0D1A (slightly lighter)
- Card Background: rgba(20, 20, 30, 0.6) → rgba(25, 25, 40, 0.7)
- Border: rgba(0, 242, 255, 0.15) → rgba(0, 242, 255, 0.2)

### Accent Colors
- Primary: #00F2FF (keep)
- Secondary: #BC13FE (keep)
- Success: #39FF14 (keep)
- Warning: #FFA500 (add)
- Error: #FF4444 (add)

### Text Colors
- Primary: #E0E0E0 (keep)
- Secondary: #A0A0A0 (add)
- Muted: #606060 (add)

## Typography Refinement

### Font Weights
- Light: 300 (subtext)
- Regular: 400 (body)
- Medium: 500 (emphasis)
- Semibold: 600 (headings)
- Bold: 700 (titles)

### Line Heights
- Body: 1.6
- Headings: 1.2
- Data: 1.4

### Letter Spacing
- Headings: 1px (reduced from 2px)
- Body: 0.5px
- Data: 0px

## Spacing System

### Base Unit: 8px
- XS: 4px
- SM: 8px
- MD: 16px
- LG: 24px
- XL: 32px
- XXL: 48px

### Component Spacing
- Button padding: 12px 24px
- Card padding: 24px
- Section gap: 32px
- Grid gap: 24px

## Border Radius System

- Small: 4px (badges, tags)
- Medium: 8px (buttons, inputs)
- Large: 12px (cards, frames)
- XL: 16px (modals, panels)
- Full: 9999px (pills, avatars)

## Shadow System

- XS: 0 2px 4px rgba(0, 0, 0, 0.1)
- SM: 0 4px 8px rgba(0, 0, 0, 0.15)
- MD: 0 8px 16px rgba(0, 0, 0, 0.2)
- LG: 0 16px 32px rgba(0, 0, 0, 0.25)
- XL: 0 24px 48px rgba(0, 0, 0, 0.3)
- Glow: 0 0 20px rgba(0, 242, 255, 0.3)

## Deliverables

1. **Updated CSS file** with all enhancements
2. **New animation library** for reusable animations
3. **Component library** for consistent UI elements
4. **Responsive design** for all screen sizes
5. **Accessibility improvements**
6. **Performance optimizations**
7. **Documentation** for design system

## Testing Requirements

- Cross-browser compatibility (Chrome, Firefox, Safari, Edge)
- Mobile testing (iOS, Android)
- Performance testing (Lighthouse score > 90)
- Accessibility testing (WCAG AA)
- User testing for intuitiveness

## Success Metrics

- Improved user engagement
- Reduced bounce rate
- Faster page load times
- Better accessibility scores
- Positive user feedback
- Increased feature adoption

---

**Note:** The current CSS file is at `frontend/styles_advanced.css` and the HTML is at `frontend/index_advanced.html`. The project uses a dark spectral cyberpunk theme that should be maintained while making it more modern, clean, and user-friendly.
