import HeaderNav from '../components/HeaderNav';
import ArticleFeed from '../components/ArticleFeed';
import SearchBar from '../components/SearchBar';
import OfflineIndicator from '../components/OfflineIndicator';

export default function Home() {
  return (
    <main className="min-h-screen flex flex-col bg-gradient-to-b from-background to-secondary/20">
      <HeaderNav />
      <div className="container mx-auto px-4 py-8 flex-1">
        <section className="mb-8 text-center">
          <h1 className="text-4xl md:text-5xl font-bold text-primary mb-4 animate-fade-in">
            Welcome to Mira News
          </h1>
          <p className="text-lg md:text-xl text-muted-foreground mb-6">
            Unbiased, AI-driven space news delivered to you.
          </p>
          <SearchBar />
        </section>
        <OfflineIndicator />
        <ArticleFeed />
      </div>
      <footer className="py-6 text-center text-muted-foreground text-sm">
        © {new Date().getFullYear()} Mira News. All rights reserved.
      </footer>
    </main>
  );
}