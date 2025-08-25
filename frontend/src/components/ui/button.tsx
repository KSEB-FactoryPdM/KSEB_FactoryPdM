import React, { FC, ButtonHTMLAttributes } from 'react';

export const Button: FC<ButtonHTMLAttributes<HTMLButtonElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <button
    className={`bg-blue-500 text-white py-2 px-4 rounded hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-accent ${className}`}
    {...props}
  >
    {children}
  </button>
);
