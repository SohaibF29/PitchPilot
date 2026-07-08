import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'warning';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  className = '',
  ...props
}) => {
  const baseStyle =
    'inline-flex items-center justify-center px-4 py-2 rounded-lg font-semibold text-sm transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-background disabled:opacity-50 disabled:cursor-not-allowed';

  const variants = {
    primary: 'bg-[#6366f1] hover:bg-[#4f46e5] text-white focus:ring-[#6366f1]',
    secondary: 'bg-[#8b5cf6] hover:bg-[#7c3aed] text-white focus:ring-[#8b5cf6]',
    outline:
      'bg-transparent border border-gray-300 dark:border-gray-700 hover:border-[#6366f1] text-gray-600 dark:text-gray-300 hover:text-[#6366f1] dark:hover:text-white focus:ring-gray-500',
    danger: 'bg-[#ef4444] hover:bg-[#dc2626] text-white focus:ring-[#ef4444]',
    warning: 'bg-[#f59e0b] hover:bg-[#d97706] text-white focus:ring-[#f59e0b]',
  };

  return (
    <button
      className={`${baseStyle} ${variants[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};
export default Button;
