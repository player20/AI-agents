import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="text-center">
      <h1 className="text-4xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
        Simple Counter
      </h1>
      <p className="text-muted-foreground mt-2 max-w-lg">
        A minimal counter app with memory to track your counts across sessions.
      </p>
    </header>
  );
};