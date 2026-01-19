import Link from 'next/link';
import { Moon, Sun } from 'lucide-react';
import { useState } from 'react';

export default function HeaderNav() {
  const [darkMode, setDarkMode] = useState(true);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark', !darkMode);
  };

  return (
    <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-md border-b border-border px-4 py-4">
      <nav className="container mx-auto flex items-center justify-between">
        <div className="text-2xl font-bold text-primary">
          <Link href="/" aria-label="Mira News Home">
            Mira News
          </Link>
        </div>
        <div className="flex items-center gap-6">
          <Link
            href="/latest"
            className="text-foreground hover:text-primary transition-colors"
          >
            Latest
          </Link>
          <Link
            href="/space"
            className="text-foreground hover:text-primary transition-colors"
          >
            Space
          </Link>
          <Link
            href="/tech"
            className="text-foreground hover:text-primary transition-colors"
          >
            Tech
          </Link>
          <button
            onClick={toggleDarkMode}
            className="p-2 rounded-md bg-secondary hover:bg-secondary/80 transition-colors"
            aria-label="Toggle dark mode"
          >
            {darkMode ? (
              <Sun className="h-5 w-5 text-muted-foreground" />
            ) : (
              <Moon className="h-5 w-5 text-muted-foreground" />
            )}
          </button>
        </div>
      </nav>
    </header>
  );
}