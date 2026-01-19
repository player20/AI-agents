import { Moon, Sun } from 'lucide-react';

interface ThemeSwitcherProps {
  theme: 'light' | 'dark';
  toggleTheme: () => void;
}

export function ThemeSwitcher({ theme, toggleTheme }: ThemeSwitcherProps) {
  return (
    <button
      onClick={toggleTheme}
      className="p-3 rounded-full bg-secondary hover:bg-secondary/80 focus:ring-2 focus:ring-secondary/50 focus:outline-none transition-all duration-200"
      aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
    >
      {theme === 'light' ? (
        <Moon className="w-5 h-5 text-secondary-foreground" />
      ) : (
        <Sun className="w-5 h-5 text-secondary-foreground" />
      )}
    </button>
  );
}