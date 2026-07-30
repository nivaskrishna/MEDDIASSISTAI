import React, { useState } from "react";
import {
  Activity,
  Stethoscope,
  MapPin,
  BookOpen,
  PhoneCall,
  Pill,
  Menu,
  X,
} from "lucide-react";

const Navbar = ({ activeTab, setActiveTab }) => {
  const [menuOpen, setMenuOpen] = useState(false);

  const navItems = [
    { id: "home", label: "Dashboard", icon: Activity },
    { id: "analyzer", label: "AI Analyzer", icon: Stethoscope },
    { id: "hospitals", label: "Find Hospitals", icon: MapPin },
    { id: "drugs", label: "Drug Info", icon: Pill },
    { id: "kb", label: "First Aid DB", icon: BookOpen },
    { id: "contacts", label: "Emergency", icon: PhoneCall },
  ];

  return (
    <nav className="glass sticky top-0 z-50 px-3 sm:px-6 py-3 sm:py-4 border-b border-slate-800">
      <div className="flex items-center justify-between w-full">
        <div
          className="flex items-center gap-2 sm:gap-3 cursor-pointer shrink-0"
          onClick={() => {
            setActiveTab("home");
            setMenuOpen(false);
          }}
        >
          <div className="bg-blue-600/25 p-1.5 sm:p-2 rounded-xl border border-blue-500/30 shrink-0">
            <Stethoscope className="h-5 w-5 sm:h-6 sm:w-6 text-blue-500" />
          </div>
          <div className="min-w-0">
            <span className="text-lg sm:text-xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-emerald-500 bg-clip-text text-transparent block truncate">
              MediAssist AI
            </span>
            <span className="hidden sm:block text-xxs text-slate-400 font-medium tracking-wider uppercase">
              24/7 Smart Health Shield
            </span>
          </div>
        </div>

        {/* Desktop Menu */}
        <div className="hidden md:flex items-center gap-1 bg-slate-900/60 p-1.5 rounded-xl border border-slate-800">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-300 ${
                  isActive
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className="h-4 w-4" />
                {item.label}
              </button>
            );
          })}
        </div>

        {/* Mobile Menu Hamburger Toggle */}
        <div className="flex md:hidden items-center">
          <button
            onClick={() => setMenuOpen(!menuOpen)}
            className="p-2 rounded-lg text-slate-400 hover:bg-slate-900 hover:text-slate-200 transition-colors cursor-pointer"
            aria-label="Toggle Menu"
          >
            {menuOpen ? <X className="h-5.5 w-5.5" /> : <Menu className="h-5.5 w-5.5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu Dropdown Panel */}
      {menuOpen && (
        <div className="md:hidden mt-3 p-2 bg-slate-900/95 border border-slate-800 rounded-xl flex flex-col gap-1 animate-fadeIn shadow-lg">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => {
                  setActiveTab(item.id);
                  setMenuOpen(false);
                }}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-all duration-200 ${
                  isActive
                    ? "bg-blue-600 text-white shadow-md shadow-blue-500/10"
                    : "text-slate-400 hover:text-slate-200 hover:bg-slate-800/50"
                }`}
              >
                <Icon className="h-4.5 w-4.5 shrink-0" />
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </nav>
  );
};

export default Navbar;
