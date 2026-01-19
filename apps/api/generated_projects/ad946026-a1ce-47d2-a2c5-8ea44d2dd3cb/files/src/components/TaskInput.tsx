import React, { useState } from 'react';

interface TaskInputProps {
  onAddTask: (text: string) => void;
}

const TaskInput: React.FC<TaskInputProps> = ({ onAddTask }) => {
  const [text, setText] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (text.trim()) {
      onAddTask(text);
      setText('');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full mb-6 animate-slide-up">
      <div className="flex flex-col gap-2">
        <label htmlFor="task-input" className="sr-only">
          Add a new task
        </label>
        <div className="flex flex-row gap-2">
          <input
            id="task-input"
            type="text"
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Add a new task..."
            className="flex-1 px-4 py-3 rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-light dark:focus:ring-primary-dark transition-all duration-200"
            aria-required="true"
          />
          <button
            type="submit"
            className="px-6 py-3 bg-primary-light dark:bg-primary-dark text-white rounded-lg hover:opacity-90 transition-opacity duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={!text.trim()}
            aria-label="Add task"
          >
            Add
          </button>
        </div>
      </div>
    </form>
  );
};

export default TaskInput;
