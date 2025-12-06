#!/bin/bash

# -----------------------------
# Setup Frontend Environment
# React + Vite + TypeScript
# TailwindCSS + ShadCN UI
# Recharts + Project Layout
# -----------------------------

echo "🚀 Creating Vite + React + TypeScript project..."
npm create vite@latest frontend --template react-ts --yes

cd frontend

echo "📦 Installing dependencies..."
npm install

echo "📦 Installing TailwindCSS..."
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

echo "🛠 Configuring Tailwind..."
# Update tailwind.config.js content paths
sed -i '' 's/content: \[\]/content: ["\.\/index.html", ".\/src\/*\*\/\*.{js,ts,jsx,tsx}"]/' tailwind.config.js

# Replace CSS file with Tailwind imports
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

echo "📦 Installing ShadCN UI..."
npm install shadcn-ui@latest --save-dev
npx shadcn-ui init

echo "📦 Installing base ShadCN components..."
npx shadcn-ui add button card input tabs table

echo "📊 Installing Recharts..."
npm install recharts

echo "🧭 Creating basic folder layout..."
mkdir -p src/components/{charts,layout,ui}
mkdir -p src/pages
mkdir -p src/api
mkdir -p src/hooks

echo "🧱 Creating starter layout..."

# App Layout
cat > src/components/layout/Layout.tsx << 'EOF'
import { PropsWithChildren } from "react";

export default function Layout({ children }: PropsWithChildren) {
  return (
    <div className="min-h-screen bg-gray-100 text-gray-900 dark:bg-gray-900 dark:text-gray-100 flex">
      <aside className="w-64 bg-white dark:bg-gray-800 shadow-lg p-4">
        <h1 className="text-xl font-bold mb-4">Strava Pro</h1>
        <nav className="space-y-2">
          <a className="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" href="/">Dashboard</a>
          <a className="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" href="/activities">Activities</a>
          <a className="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" href="/prediction">Predictions</a>
          <a className="block p-2 rounded hover:bg-gray-200 dark:hover:bg-gray-700" href="/training">Training Blocks</a>
        </nav>
      </aside>
      <main className="flex-1 p-6">
        {children}
      </main>
    </div>
  );
}
EOF

# Pages
cat > src/pages/Dashboard.tsx << 'EOF'
export default function Dashboard() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Dashboard</h2>
      <p>Welcome to your Strava Pro coaching dashboard.</p>
    </div>
  );
}
EOF

cat > src/pages/Activities.tsx << 'EOF'
export default function Activities() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Activities</h2>
      <p>Activity list will go here.</p>
    </div>
  );
}
EOF

cat > src/pages/Prediction.tsx << 'EOF'
export default function Prediction() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Race Prediction</h2>
      <p>Future race prediction tools will live here.</p>
    </div>
  );
}
EOF

cat > src/pages/TrainingBlocks.tsx << 'EOF'
export default function TrainingBlocks() {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-4">Training Blocks</h2>
      <p>Training planning UI will go here.</p>
    </div>
  );
}
EOF

# App.tsx
cat > src/App.tsx << 'EOF'
import { BrowserRouter, Routes, Route } from "react-router-dom";

import Layout from "./components/layout/Layout";
import Dashboard from "./pages/Dashboard";
import Activities from "./pages/Activities";
import Prediction from "./pages/Prediction";
import TrainingBlocks from "./pages/TrainingBlocks";

function App() {
  return (
    <BrowserRouter>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/activities" element={<Activities />} />
          <Route path="/prediction" element={<Prediction />} />
          <Route path="/training" element={<TrainingBlocks />} />
        </Routes>
      </Layout>
    </BrowserRouter>
  );
}

export default App;
EOF

echo "📦 Installing React Router..."
npm install react-router-dom

echo "🎉 Frontend environment is ready!"
echo "Run it with:"
echo "  cd frontend"
echo "  npm run dev"
