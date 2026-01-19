import { Rocket } from 'lucide-react';

export default function Footer() {
  return (
    <footer className="border-t border-border/40 bg-background/95 py-10">
      <div className="container max-w-5xl mx-auto">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          <div>
            <div className="flex items-center gap-2 mb-4">
              <Rocket className="h-6 w-6 text-primary" />
              <span className="text-xl font-bold tracking-tight">Mira News</span>
            </div>
            <p className="text-sm text-muted-foreground mb-4">
              Unbiased, AI-powered news summaries for a clearer world view.
            </p>
            <div className="flex gap-4">
              <a href="#" className="text-muted-foreground hover:text-primary">
                Twitter
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary">
                Facebook
              </a>
              <a href="#" className="text-muted-foreground hover:text-primary">
                Instagram
              </a>
            </div>
          </div>
          <div>
            <h3 className="text-sm font-semibold mb-4">Company</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-primary">About</a></li>
              <li><a href="#" className="hover:text-primary">Careers</a></li>
              <li><a href="#" className="hover:text-primary">Press</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold mb-4">Support</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-primary">Contact Us</a></li>
              <li><a href="#" className="hover:text-primary">Help Center</a></li>
              <li><a href="#" className="hover:text-primary">FAQ</a></li>
            </ul>
          </div>
          <div>
            <h3 className="text-sm font-semibold mb-4">Legal</h3>
            <ul className="space-y-2 text-sm text-muted-foreground">
              <li><a href="#" className="hover:text-primary">Terms of Service</a></li>
              <li><a href="#" className="hover:text-primary">Privacy Policy</a></li>
              <li><a href="#" className="hover:text-primary">Cookie Policy</a></li>
            </ul>
          </div>
        </div>
        <div className="mt-10 pt-6 border-t border-border/40 text-center text-sm text-muted-foreground">
          <p>© {new Date().getFullYear()} Mira News. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}