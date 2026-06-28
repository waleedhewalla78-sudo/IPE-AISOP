import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: { '@': path.resolve(__dirname, './src') },
    },
    build: {
        rollupOptions: {
            output: {
                manualChunks: function (id) {
                    if (!id.includes('node_modules'))
                        return;
                    if (id.includes('recharts') || id.includes('d3-'))
                        return 'charts';
                    if (id.includes('react-dom') ||
                        id.includes('react-router') ||
                        id.includes('node_modules/react/') ||
                        id.includes('node_modules\\react\\')) {
                        return 'react-vendor';
                    }
                    if (id.includes('@reduxjs') || id.includes('react-redux'))
                        return 'redux';
                },
            },
        },
        chunkSizeWarningLimit: 500,
    },
    server: {
        port: 8082,
        strictPort: true,
        proxy: {
            '/api': { target: 'http://localhost:8000', changeOrigin: true },
        },
    },
});
