'use client';

import { useState } from 'react';
import { Header } from '@/components/Header';
import { Hero } from '@/components/Hero';
import { Features } from '@/components/Features';
import { Footer } from '@/components/Footer';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';

export default function Home() {
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  const toggleTheme = () => {
    setTheme((prev) => (prev === 'light' ? 'dark' : 'light'));
    document.documentElement.classList.toggle('dark', theme === 'light');
  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between">
      <Header theme={theme} />
      <Hero />
      <Features />
      <ThemeSwitcher theme={theme} toggleTheme={toggleTheme} />
      <Footer />
    </main>
  );
}