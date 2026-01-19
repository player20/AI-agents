import React from 'react';

const Header: React.FC = () => {
  return (
    <header className="mb-8 text-center animate-fade-in">
      <h1 className="text-4xl md:text-5xl font-bold text-transparent bg-clip-text bg-hero-gradient mb-2">
        Todo List
      </h1>
      <p className="text-lg md:text-xl text-gray-600 dark:text-gray-300">
        Keep track of your tasks effortlessly.
      </p>
    </header>
  );
};

export default Header;
