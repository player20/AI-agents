import { Counter } from '@/components/Counter';
import { ThemeSwitcher } from '@/components/ThemeSwitcher';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center p-4 md:p-6 bg-gradient-to-br from-primary/20 to-secondary/20 dark:from-primary/10 dark:to-secondary/10 transition-colors duration-500">
      <div className="max-w-2xl w-full flex flex-col items-center justify-center gap-8 animate-in">
        <Header />
        <Counter initialCount={0} step={1} />
        <ThemeSwitcher />
        <Footer />
      </div>
    </main>
  );
}