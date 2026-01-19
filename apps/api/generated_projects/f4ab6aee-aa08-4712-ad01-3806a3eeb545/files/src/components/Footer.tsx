export function Footer() {
  return (
    <footer className="py-6 px-4 md:px-8 bg-card text-center text-muted-foreground w-full border-t border-border">
      <p>© {new Date().getFullYear()} HelloWorldApp. All rights reserved.</p>
    </footer>
  );
}