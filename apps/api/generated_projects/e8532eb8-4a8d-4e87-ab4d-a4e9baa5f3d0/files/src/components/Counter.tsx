import React, { useState, useEffect } from 'react';

import { Button } from './Button';
import { Plus, Minus, RotateCcw } from 'lucide-react';

interface CounterProps {
  initialCount: number;
  step: number;
}

export const Counter: React.FC<CounterProps> = ({ initialCount, step }) => {
  const [count, setCount] = useState<number>(() => {
    const savedCount = localStorage.getItem('counterValue');
    return savedCount ? parseInt(savedCount, 10) : initialCount;
  });

  useEffect(() => {
    localStorage.setItem('counterValue', count.toString());
  }, [count]);

  const handleIncrement = () => setCount((prev) => prev + step);
  const handleDecrement = () => setCount((prev) => prev - step);
  const handleReset = () => setCount(initialCount);

  return (
    <div className="flex flex-col items-center gap-6 p-8 bg-card/50 backdrop-blur-sm rounded-lg shadow-xl dark:bg-card/30 transition-all duration-300 w-full max-w-md border border-border/50">
      <div className="text-center">
        <p className="text-5xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent animate-pulse">
          {count}
        </p>
        <p className="text-muted-foreground text-sm mt-2">Counter Value</p>
      </div>
      <div className="flex gap-4 justify-center">
        <Button
          variant="outline"
          size="icon"
          onClick={handleDecrement}
          aria-label="Decrement counter"
          className="hover:scale-105 transition-transform border-border/50"
        >
          <Minus className="h-5 w-5" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={handleIncrement}
          aria-label="Increment counter"
          className="hover:scale-105 transition-transform border-border/50"
        >
          <Plus className="h-5 w-5" />
        </Button>
        <Button
          variant="outline"
          size="icon"
          onClick={handleReset}
          aria-label="Reset counter"
          className="hover:scale-105 transition-transform border-border/50"
        >
          <RotateCcw className="h-5 w-5" />
        </Button>
      </div>
    </div>
  );
};