#!/bin/bash

echo "🔥 Installing Tailwind..."
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p

echo "📝 Configuring Tailwind..."
cat > tailwind.config.js << 'EOF'
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          DEFAULT: "#FC4C02",
          light: "#FF6A2A",
          dark: "#DD4200"
        }
      },
      fontFamily: {
        sans: ["Inter", "sans-serif"],
      }
    },
  },
  plugins: [],
};
EOF

echo "🎨 Updating src/index.css..."
cat > src/index.css << 'EOF'
@tailwind base;
@tailwind components;
@tailwind utilities;
EOF

echo "📦 Installing Inter font..."
npm install @fontsource/inter

echo "⚙️ Installing ShadCN (new version)..."
npm install -D shadcn

echo "✨ Initializing ShadCN..."
npx shadcn init -y

echo "🔧 Configuring tsconfig paths..."
cat > tsconfig.json << 'EOF'
{
  "compilerOptions": {
    "target": "ESNext",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ESNext"],
    "allowJs": false,
    "skipLibCheck": true,
    "esModuleInterop": false,
    "allowSyntheticDefaultImports": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "module": "ESNext",
    "moduleResolution": "Node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
}
EOF

echo "🛠 Updating vite.config.ts to support @ alias..."
cat > vite.config.ts << 'EOF'
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
EOF

echo "📁 Creating clean folder structure..."
mkdir -p src/pages
mkdir -p src/components/layout
mkdir -p src/components/charts
mkdir -p src/components/ui
mkdir -p src/api
mkdir -p src/hooks

echo "🎉 Setup complete! Run the dev server:"
echo "=> npm run dev"
