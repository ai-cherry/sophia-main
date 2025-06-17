import React from 'react';
import { cn } from '@/lib/utils';

const Input = React.forwardRef(({
  className,
  type,
  label,
  error,
  icon: Icon,
  ...props
}, ref) => {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-300 mb-2">
          {label}
        </label>
      )}
      <div className="relative">
        {Icon && (
          <div className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <Icon className="w-5 h-5" />
          </div>
        )}
        <input
          type={type}
          className={cn(
            "w-full bg-slate-800 border border-slate-600 rounded-lg",
            "px-4 py-3 text-white placeholder-gray-400",
            "focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20",
            "transition-all duration-200",
            Icon && "pl-12",
            error && "border-red-500 focus:border-red-500 focus:ring-red-500/20",
            className
          )}
          ref={ref}
          {...props}
        />
      </div>
      {error && (
        <p className="mt-2 text-sm text-red-400">{error}</p>
      )}
    </div>
  );
});

Input.displayName = 'Input';

export default Input; 