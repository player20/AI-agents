import { Rocket } from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 max-w-5xl items-center justify-between">
        <div className="flex items-center gap-2">
          <Rocket className="h-6 w-6 text-primary" />
          <span className="text-xl font-bold tracking-tight">Mira News</span>
        </div>
        <nav className="hidden md:flex items-center gap-6 text-sm font-medium">
          <a href="#" className="transition-colors hover:text-foreground/80">
            Home
          </a>
          <a href="#" className="transition-colors hover:text-foreground/80">
            Global
          </a>
          <a href="#" className="transition-colors hover:text-foreground/80">
            Local
          </a>
          <a href="#" className="transition-colors hover:text-foreground/80">
            Topics
          </a>
        </nav>
        <Button
          variant="outline"
          className="rounded-full transition-all duration-300 hover:scale-105"
        >
          Subscribe
        </Button>
      </div>
    </header>
  );
}