import { Rocket } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 dark:bg-background/80">
      <div className="container flex items-center justify-between h-16 px-4 mx-auto">
        <div className="flex items-center gap-2">
          <Rocket className="w-6 h-6 text-primary" />
          <span className="text-xl font-bold tracking-tight text-foreground">
            Mira News
          </span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-muted-foreground">
          <a href="#" className="transition-colors hover:text-foreground">
            Home
          </a>
          <a href="#" className="transition-colors hover:text-foreground">
            Global
          </a>
          <a href="#" className="transition-colors hover:text-foreground">
            Local
          </a>
          <a href="#" className="transition-colors hover:text-foreground">
            Topics
          </a>
        </nav>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" className="rounded-lg transition-all duration-300 hover:scale-105">
            Login
          </Button>
          <Button size="sm" className="rounded-lg shadow-md transition-all duration-300 hover:scale-105">
            Sign Up
          </Button>
        </div>
      </div>
    </header>
  );
}