import React from 'react';
import { TrendingUp, TrendingDown } from 'lucide-react';
import { cn } from '@/lib/utils';

const MetricCard = ({
  title,
  value,
  change,
  trend = 'up',
  icon: Icon,
  className,
  loading = false,
  onClick,
}) => {
  return (
    <div
      className={cn(
        "group bg-slate-800 rounded-lg p-6 border border-slate-700",
        "hover:border-slate-600 hover:shadow-lg hover:scale-[1.02]",
        "transition-all duration-300",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
    >
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-sm font-medium text-gray-400">{title}</h3>
        {Icon && (
          <div className="text-purple-400 group-hover:text-purple-300 transition-colors duration-200">
            <Icon className="w-5 h-5" />
          </div>
        )}
      </div>
      
      {loading ? (
        <div className="space-y-2">
          <div className="h-8 bg-slate-700 rounded animate-pulse" />
          <div className="h-4 w-24 bg-slate-700 rounded animate-pulse" />
        </div>
      ) : (
        <>
          <div className="text-3xl font-bold text-white mb-2">{value}</div>
          {change && (
            <div className="flex items-center space-x-1">
              {trend === 'up' ? (
                <TrendingUp className="w-4 h-4 text-green-400" />
              ) : (
                <TrendingDown className="w-4 h-4 text-red-400" />
              )}
              <span
                className={cn(
                  "text-sm",
                  trend === 'up' ? "text-green-400" : "text-red-400"
                )}
              >
                {change}
              </span>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default MetricCard; 