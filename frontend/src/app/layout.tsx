import type { Metadata } from 'next';
import './globals.css';
import Providers from './providers';
import Sidebar from '../components/layout/Sidebar';

export const metadata: Metadata = {
  title: 'Smart Classroom Edge AI System',
  description: 'Classroom occupancy detection & Smart AC automation powered by YOLO11 Edge AI.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-[#090d16] text-gray-100 antialiased selection:bg-blue-500 selection:text-white">
        <Providers>
          <div className="min-h-screen flex">
            {/* Sidebar Navigation */}
            <Sidebar />
            
            {/* Main Content Workspace */}
            <div className="flex-1 ml-64 flex flex-col min-h-screen bg-[#090d16]">
              {children}
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
