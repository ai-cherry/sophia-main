import React from 'react';
import { cn } from '@/lib/utils';

const GlassCard = ({ 
  children, 
  className,
  hover = true,
  gradient = false,
  padding = 'default',
  ...props 
}) => {
  const paddingSizes = {
    none: '',
    small: 'p-4',
    default: 'p-6',
    large: 'p-8',
  };

  if (gradient) {
    return (
      <div className={cn("gradient-border", className)} {...props}>
        <div className="gradient-border-content">
          {children}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn(
        "glass-effect rounded-lg",
        paddingSizes[padding],
        hover && "hover:border-slate-600 hover:shadow-lg transition-all duration-300",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
};

export default GlassCard; 