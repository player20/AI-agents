'use client';

import { useState, useEffect } from 'react';
import { Moon, Sun } from 'lucide-react';
import Header from '../components/Header';
import TaskInput from '../components/TaskInput';
import TaskList from '../components/TaskList';
import Footer from '../components/Footer';

export interface Task {
  id: string;
  text: string;
  completed: boolean;
  createdAt: string;
}

export default function Home() {
  const [tasks, setTasks] = useState<Task[]>(() => {
    if (typeof window !== 'undefined') {
      const savedTasks = localStorage.getItem('tasks');
      return savedTasks ? JSON.parse(savedTasks) : [];
    }
    return [];
  });
  const [darkMode, setDarkMode] = useState<boolean>(() => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('darkMode') === 'true';
    }
    return false;
  });

  useEffect(() => {
    localStorage.setItem('tasks', JSON.stringify(tasks));
  }, [tasks]);

  useEffect(() => {
    localStorage.setItem('darkMode', darkMode.toString());
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  const toggleDarkMode = () => setDarkMode(!darkMode);

  const addTask = (text: string) => {
    if (text.trim()) {
      setTasks([
        {
          id: crypto.randomUUID(),
          text,
          completed: false,
          createdAt: new Date().toISOString(),
        },
        ...tasks,
      ]);
    }
  };

  const toggleTask = (id: string) => {
    setTasks(
      tasks.map((task) =>
        task.id === id ? { ...task, completed: !task.completed } : task
      )
    );
  };

  const deleteTask = (id: string) => {
    setTasks(tasks.filter((task) => task.id !== id));
  };

  const editTask = (id: string, newText: string) => {
    setTasks(
      tasks.map((task) => (task.id === id ? { ...task, text: newText } : task))
    );
  };

  return (
    <div className="min-h-screen flex flex-col bg-secondary-light dark:bg-secondary-dark transition-colors duration-300">
      <div className="absolute top-0 right-0 p-6 z-50">
        <button
          onClick={toggleDarkMode}
          aria-label="Toggle dark mode"
          className="p-2 rounded-full bg-gray-100 dark:bg-gray-800 text-gray-800 dark:text-gray-200 shadow-md hover:shadow-hover transition-all duration-200"
        >
          {darkMode ? <Sun size={20} /> : <Moon size={20} />}
        </button>
      </div>
      <div className="flex-grow flex flex-col items-center justify-center px-4 py-8 max-w-2xl mx-auto w-full">
        <Header />
        <TaskInput onAddTask={addTask} />
        <TaskList tasks={tasks} onToggle={toggleTask} onDelete={deleteTask} onEdit={editTask} />
        <Footer />
      </div>
    </div>
  );
}
