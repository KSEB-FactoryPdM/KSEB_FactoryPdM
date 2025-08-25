import React, { FC, ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export const Card: FC<CardProps> = ({ children, className = '' }) => (
  <div
    className={`bg-white border border-gray-200 rounded-lg shadow-[0_2px_6px_rgba(0,0,0,0.08),_0_1px_3px_rgba(0,0,0,0.04)] transform transition-transform hover:-translate-y-1 ${className}`}
  >
    {children}
  </div>
);

export const CardHeader: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div
    className={`px-6 py-4 border-b border-gray-200 bg-white text-gray-900 rounded-t-lg ${className}`}
  >
    {children}
  </div>
);

export const CardTitle: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <h3 className={`text-lg font-semibold text-gray-900 ${className}`}>{children}</h3>
);

export const CardContent: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`p-6 ${className}`}>{children}</div>
);
