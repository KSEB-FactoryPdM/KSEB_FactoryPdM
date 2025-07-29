import React, { FC, ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

export const Card: FC<CardProps> = ({ children, className = '' }) => (
  <div className={`bg-white rounded-lg shadow ${className}`}>{children}</div>
);

export const CardHeader: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`px-6 py-4 border-b ${className}`}>{children}</div>
);

export const CardTitle: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <h3 className={`text-xl font-semibold ${className}`}>{children}</h3>
);

export const CardContent: FC<{ children: ReactNode; className?: string }> = ({
  children,
  className = '',
}) => (
  <div className={`p-6 ${className}`}>{children}</div>
);
