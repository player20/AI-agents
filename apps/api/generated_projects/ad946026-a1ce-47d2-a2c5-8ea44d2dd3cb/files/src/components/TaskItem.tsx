import React, { useState } from 'react';
import { Check, Trash2, Edit } from 'lucide-react';
import { Task } from '../app/page';

interface TaskItemProps {
  task: Task;
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, newText: string) => void;
}

const TaskItem: React.FC<TaskItemProps> = ({
  task,
  onToggle,
  onDelete,
  onEdit,
}) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editText, setEditText] = useState(task.text);

  const handleSave = () => {
    if (editText.trim()) {
      onEdit(task.id, editText);
      setIsEditing(false);
    }
  };

  return (
    <div
      className="flex items-center justify-between p-4 bg-white dark:bg-gray-800 rounded-lg shadow-task hover:shadow-hover transition-all duration-200 animate-slide-up"
      role="listitem"
      aria-label={`Task: ${task.text}`}
    >
      {isEditing ? (
        <div className="flex-1 flex gap-2">
          <input
            type="text"
            value={editText}
            onChange={(e) => setEditText(e.target.value)}
            className="flex-1 px-3 py-2 rounded-md border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 text-gray-900 dark:text-gray-100 focus:outline-none focus:ring-2 focus:ring-primary-light dark:focus:ring-primary-dark"
            autoFocus
            aria-label="Edit task text"
          />
          <button
            onClick={handleSave}
            className="px-3 py-1 bg-primary-light dark:bg-primary-dark text-white rounded-md hover:opacity-90 transition-opacity duration-200"
            disabled={!editText.trim()}
          >
            Save
          </button>
          <button
            onClick={() => {
              setIsEditing(false);
              setEditText(task.text);
            }}
            className="px-3 py-1 bg-gray-200 dark:bg-gray-700 text-gray-800 dark:text-gray-200 rounded-md hover:opacity-90 transition-opacity duration-200"
          >
            Cancel
          </button>
        </div>
      ) : (
        <>
          <div className="flex items-center gap-3 flex-1">
            <button
              onClick={() => onToggle(task.id)}
              className={`w-6 h-6 rounded-full border flex items-center justify-center transition-colors duration-200 ${
                task.completed
                  ? 'bg-primary-light dark:bg-primary-dark border-primary-light dark:border-primary-dark text-white'
                  : 'border-gray-300 dark:border-gray-600'
              }`}
              aria-label={task.completed ? 'Mark as incomplete' : 'Mark as complete'}
            >
              {task.completed && <Check size={14} />}
            </button>
            <span
              className={`text-gray-900 dark:text-gray-100 flex-1 ${
                task.completed ? 'line-through text-gray-500 dark:text-gray-400' : ''
              }`}
            >
              {task.text}
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setIsEditing(true)}
              className="p-1 text-gray-500 dark:text-gray-400 hover:text-primary-light dark:hover:text-primary-dark transition-colors duration-200"
              aria-label="Edit task"
            >
              <Edit size={16} />
            </button>
            <button
              onClick={() => onDelete(task.id)}
              className="p-1 text-gray-500 dark:text-gray-400 hover:text-accent-light dark:hover:text-accent-dark transition-colors duration-200"
              aria-label="Delete task"
            >
              <Trash2 size={16} />
            </button>
          </div>
        </>
      )}
    </div>
  );
};

export default TaskItem;
