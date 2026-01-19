import React from 'react';

const Footer: React.FC = () => {
  return (
    <footer className="mt-8 text-center text-gray-500 dark:text-gray-400 text-sm animate-fade-in">
      <p>Todo List App &copy; {new Date().getFullYear()}</p>
    </footer>
  );
};

export default Footer;
