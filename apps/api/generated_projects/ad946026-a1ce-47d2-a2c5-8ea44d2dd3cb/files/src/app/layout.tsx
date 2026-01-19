import type { Metadata } from 'next';
import { Inter } from 'next/font/google';
import './globals.css';

const inter = Inter({ subsets: ['latin'] });

export const metadata: Metadata = {
  title: 'Todo List App',
  description: 'A simple, modern todo list application to manage your tasks efficiently.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-secondary-light dark:bg-secondary-dark transition-colors duration-300`}>
        {children}
      </body>
    </html>
  );
}
