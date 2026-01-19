import { Search } from 'lucide-react';

export default function SearchBar() {
  return (
    <div className="relative max-w-xl mx-auto">
      <input
        type="search"
        placeholder="Search space news..."
        className="w-full py-3 px-4 bg-input border border-border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary/50 text-foreground placeholder-muted-foreground"
        aria-label="Search news articles"
      />
      <Search className="absolute right-3 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
    </div>
  );
}