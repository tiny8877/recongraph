import type { Metadata } from 'next';
import './globals.css';
import Sidebar from '@/components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'ReconGraph - Bug Bounty Recon Visualizer',
  description: 'BloodHound-style recon data visualization for bug bounty hunters',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg-primary text-gray-200 font-mono">
        <Sidebar />
        <main className="ml-16 min-h-screen">
          {children}
        </main>
      </body>
    </html>
  );
}
