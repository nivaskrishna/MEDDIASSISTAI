import React from "react";
import { Activity, ShieldCheck } from "lucide-react";

const Footer = () => {
  return (
    <footer className="border-t border-slate-800 bg-slate-950/80 backdrop-blur-md py-8 px-6 mt-auto">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
        <div className="flex items-center gap-2.5">
          <Activity className="h-5 w-5 text-blue-500" />
          <span className="text-sm font-semibold text-slate-400">
            © {new Date().getFullYear()} MediAssist AI. All rights reserved.
          </span>
        </div>

        <div className="flex items-center gap-2 text-xs text-slate-500 bg-slate-900/40 px-3 py-1.5 rounded-full border border-slate-800">
          <ShieldCheck className="h-4 w-4 text-emerald-500" />
          <span>Information verified against WHO & Mayo Clinic guidelines</span>
        </div>

        <div className="flex gap-6 text-sm text-slate-400 font-medium">
          <a href="#" className="hover:text-blue-400 transition-colors">
            Privacy Policy
          </a>
          <a href="#" className="hover:text-blue-400 transition-colors">
            Terms of Use
          </a>
          <a href="#" className="hover:text-blue-400 transition-colors">
            Contact Support
          </a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
