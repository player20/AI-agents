import { Sun, Moon, Menu } from 'lucide-react';
import { useState } from 'react';

export function Header() {
  const [darkMode, setDarkMode] = useState(false);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
    document.documentElement.classList.toggle('dark', !darkMode);
  };

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-2">
          <span className="text-xl font-bold tracking-tight">TestApp</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <a href="#features" className="transition-colors hover:text-foreground/80">Features</a>
          <a href="#about" className="transition-colors hover:text-foreground/80">About</a>
          <a href="#contact" className="transition-colors hover:text-foreground/80">Contact</a>
        </nav>
        <div className="flex items-center gap-4">
          <button
            onClick={toggleDarkMode}
            className="rounded-full p-2 transition-colors hover:bg-muted"
            aria-label="Toggle dark mode"
          >
            {darkMode ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
          <button className="md:hidden p-2 rounded-md hover:bg-muted" aria-label="Open menu">
            <Menu className="h-5 w-5" />
          </button>
        </div>
      </div>
    </header>
  );
}