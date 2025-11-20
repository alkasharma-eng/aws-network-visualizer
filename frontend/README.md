# AWS Network Visualizer - React Dashboard

Production-ready React + TypeScript dashboard for visualizing and analyzing AWS network topology.

## Features

- **Interactive Network Topology** - D3.js-powered force-directed graph visualization
- **Real-time Anomaly Detection** - View and filter detected security issues
- **Multi-Region Support** - Browse topology across multiple AWS regions
- **Responsive Design** - Mobile-friendly interface with Tailwind CSS
- **Type-Safe** - Full TypeScript support

## Tech Stack

- React 18
- TypeScript 5
- Vite (build tool)
- D3.js (visualizations)
- TanStack Query (data fetching)
- Tailwind CSS (styling)
- Zustand (state management)

## Getting Started

### Prerequisites

- Node.js 18+ and npm/yarn
- API Gateway endpoint URL

### Installation

```bash
# Install dependencies
npm install

# Set up environment variables
cp .env.example .env
# Edit .env with your API endpoint

# Start development server
npm run dev
```

### Build for Production

```bash
# Build optimized production bundle
npm run build

# Preview production build
npm run preview
```

### Testing

```bash
# Run tests
npm test

# Run tests with UI
npm test:ui

# Generate coverage report
npm run test:coverage
```

## Project Structure

```
frontend/
├── src/
│   ├── api/              # API client and types
│   ├── components/       # Reusable components
│   │   ├── Layout.tsx
│   │   ├── NetworkGraph.tsx
│   │   └── ...
│   ├── pages/            # Route pages
│   │   ├── Dashboard.tsx
│   │   ├── TopologyView.tsx
│   │   └── AnomaliesView.tsx
│   ├── hooks/            # Custom React hooks
│   ├── store/            # Zustand stores
│   ├── utils/            # Utility functions
│   ├── App.tsx           # Main app component
│   └── main.tsx          # Entry point
├── public/               # Static assets
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.js
```

## Environment Variables

Create a `.env` file:

```env
VITE_API_BASE_URL=https://your-api-gateway-url.amazonaws.com/prod
```

## Deployment

### AWS S3 + CloudFront

```bash
# Build
npm run build

# Deploy to S3
aws s3 sync dist/ s3://your-bucket-name/ --delete

# Invalidate CloudFront cache
aws cloudfront create-invalidation --distribution-id YOUR_DIST_ID --paths "/*"
```

### Docker

```bash
# Build Docker image
docker build -t network-visualizer-dashboard .

# Run container
docker run -p 80:80 network-visualizer-dashboard
```

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for contribution guidelines.

## License

MIT License - see [LICENSE](../LICENSE) for details.
