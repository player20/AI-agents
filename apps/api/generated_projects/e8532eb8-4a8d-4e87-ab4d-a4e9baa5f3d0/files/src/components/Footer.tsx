import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer className="text-center text-muted-foreground text-sm mt-8">
      <p>© {new Date().getFullYear()} Simple Counter App</p>
    </footer>
  );
};