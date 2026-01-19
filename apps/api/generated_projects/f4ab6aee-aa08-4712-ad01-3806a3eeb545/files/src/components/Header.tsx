import { Globe } from 'lucide-react';

interface HeaderProps {
  theme: 'light' | 'dark';
}

export function Header({ theme }: HeaderProps) {
  return (
    <header className="w-full py-6 px-4 md:px-8 flex items-center justify-between bg-card shadow-md transition-all duration-300">
      <div className="flex items-center gap-2">
        <Globe className="w-6 h-6 text-primary" aria-label="Globe icon" />
        <h1 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-secondary-foreground">HelloWorldApp</h1>
      </div>
    </header>
  );
}