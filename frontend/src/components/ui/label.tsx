import React, { FC, LabelHTMLAttributes } from 'react';

export const Label: FC<LabelHTMLAttributes<HTMLLabelElement>> = ({
  className = '',
  children,
  ...props
}) => (
  <label className={`block text-sm font-medium ${className}`} {...props}>
    {children}
  </label>
);
