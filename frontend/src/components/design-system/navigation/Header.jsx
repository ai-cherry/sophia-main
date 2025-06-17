import React from 'react';
import { cn } from '@/lib/utils';
import { Bell, Search, Settings, User, Menu } from 'lucide-react';
import Button from '../buttons/Button';

const Header = ({ 
  title = "Sophia AI",
  user,
  onMenuClick,
  showSearch = true,
  className 
}) => {
  return (
    <header className={cn(
      "fixed top-0 left-0 right-0 z-50",
      "glass-effect border-b border-slate-700",
      "h-20 px-6",
      className
    )}>
      <div className="max-w-7xl mx-auto h-full flex items-center justify-between">
        {/* Left section */}
        <div className="flex items-center space-x-4">
          <button
            onClick={onMenuClick}
            className="lg:hidden p-2 rounded-md hover:bg-slate-700 transition-colors"
          >
            <Menu className="w-5 h-5 text-gray-400" />
          </button>
          
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-gradient-to-r from-purple-600 to-blue-600 rounded-lg flex items-center justify-center">
              <span className="text-white font-bold text-lg">S</span>
            </div>
            <div>
              <h1 className="text-xl font-bold text-white">{title}</h1>
              <p className="text-xs text-gray-400">Pay Ready Business Intelligence</p>
            </div>
          </div>
        </div>

        {/* Center section - Search */}
        {showSearch && (
          <div className="hidden md:flex flex-1 max-w-xl mx-6">
            <div className="relative w-full">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search dashboards, metrics, insights..."
                className="w-full bg-slate-800 border border-slate-600 rounded-lg pl-10 pr-4 py-2.5 text-sm text-white placeholder-gray-400 focus:border-purple-500 focus:ring-2 focus:ring-purple-500/20 transition-all duration-200"
              />
            </div>
          </div>
        )}

        {/* Right section */}
        <div className="flex items-center space-x-3">
          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="relative"
          >
            <Bell className="w-5 h-5" />
            <span className="absolute top-0 right-0 w-2 h-2 bg-red-500 rounded-full"></span>
          </Button>

          {/* Settings */}
          <Button
            variant="ghost"
            size="icon"
          >
            <Settings className="w-5 h-5" />
          </Button>

          {/* User menu */}
          <div className="flex items-center space-x-3 pl-3 border-l border-slate-700">
            <div className="text-right hidden sm:block">
              <p className="text-sm font-medium text-white">{user?.name || 'Admin User'}</p>
              <p className="text-xs text-gray-400">{user?.role || 'Administrator'}</p>
            </div>
            <button className="w-10 h-10 bg-purple-600 rounded-lg flex items-center justify-center hover:bg-purple-700 transition-colors">
              <User className="w-5 h-5 text-white" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header; 