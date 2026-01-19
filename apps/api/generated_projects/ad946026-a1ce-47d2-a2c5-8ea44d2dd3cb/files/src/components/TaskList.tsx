import React from 'react';
import TaskItem from './TaskItem';
import { Task } from '../app/page';

interface TaskListProps {
  tasks: Task[];
  onToggle: (id: string) => void;
  onDelete: (id: string) => void;
  onEdit: (id: string, newText: string) => void;
}

const TaskList: React.FC<TaskListProps> = ({
  tasks,
  onToggle,
  onDelete,
  onEdit,
}) => {
  if (tasks.length === 0) {
    return (
      <div className="text-center py-10 text-gray-500 dark:text-gray-400 animate-fade-in">
        <p>No tasks yet. Add one above!</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-3 max-h-[50vh] overflow-y-auto pr-1 animate-fade-in">
      {tasks.map((task) => (
        <TaskItem
          key={task.id}
          task={task}
          onToggle={onToggle}
          onDelete={onDelete}
          onEdit={onEdit}
        />
      ))}
    </div>
  );
};

export default TaskList;
