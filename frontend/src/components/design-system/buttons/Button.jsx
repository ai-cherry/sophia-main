import React from 'react';
import { cn } from '@/lib/utils';
import { Loader2 } from 'lucide-react';

const Button = React.forwardRef(({
  className,
  variant = 'primary',
  size = 'default',
  loading = false,
  children,
  disabled,
  icon: Icon,
  iconPosition = 'left',
  ...props
}, ref) => {
  const variants = {
    primary: "bg-purple-600 hover:bg-purple-700 text-white hover:shadow-glow hover:scale-[1.02]",
    secondary: "border-2 border-purple-500 text-purple-400 hover:bg-purple-500 hover:text-white",
    ghost: "text-purple-400 hover:text-purple-300 hover:bg-purple-900/30",
    destructive: "bg-red-600 hover:bg-red-700 text-white",
    outline: "border border-slate-600 text-gray-300 hover:bg-slate-700 hover:border-slate-500",
  };

  const sizes = {
    small: "px-3 py-1.5 text-sm rounded",
    default: "px-6 py-3 rounded-lg",
    large: "px-8 py-4 text-lg rounded-lg",
    icon: "p-2 rounded-md",
  };

  const isDisabled = disabled || loading;

  return (
    <button
      ref={ref}
      className={cn(
        "font-medium transition-all duration-200",
        "inline-flex items-center justify-center",
        "focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 focus:ring-offset-slate-900",
        variants[variant],
        sizes[size],
        isDisabled && "opacity-50 cursor-not-allowed",
        className
      )}
      disabled={isDisabled}
      {...props}
    >
      {loading && (
        <Loader2 className={cn(
          "animate-spin",
          size === 'small' ? "w-3 h-3" : "w-4 h-4",
          iconPosition === 'left' ? "mr-2" : "ml-2"
        )} />
      )}
      
      {!loading && Icon && iconPosition === 'left' && (
        <Icon className={cn(
          size === 'small' ? "w-3 h-3" : "w-4 h-4",
          "mr-2"
        )} />
      )}
      
      {children}
      
      {!loading && Icon && iconPosition === 'right' && (
        <Icon className={cn(
          size === 'small' ? "w-3 h-3" : "w-4 h-4",
          "ml-2"
        )} />
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button; 