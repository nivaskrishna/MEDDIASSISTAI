import React, { useState, useEffect } from "react";
import { getEmergencyContacts } from "../../services/api";
import {
  Phone,
  PhoneCall,
  ShieldAlert,
  HeartHandshake,
  Loader2,
  Search,
  Siren,
  Flame,
  Stethoscope,
  Baby,
  Zap,
  HelpCircle,
} from "lucide-react";

// ─── Category config ─────────────────────────────────────────────────────────
const CATEGORY_META = {
  critical: {
    label: "All-in-One Emergency",
    color: "rose",
    icon: Siren,
    bg: "bg-rose-500/10",
    border: "border-rose-500/30",
    badge: "bg-rose-500/15 text-rose-800 border-rose-500/30",
    btn: "bg-rose-600 hover:bg-rose-500",
  },
  medical: {
    label: "Medical",
    color: "blue",
    icon: Stethoscope,
    bg: "bg-blue-500/10",
    border: "border-blue-500/30",
    badge: "bg-blue-500/15 text-blue-800 border-blue-500/30",
    btn: "bg-blue-600 hover:bg-blue-500",
  },
  police: {
    label: "Police & Security",
    color: "indigo",
    icon: ShieldAlert,
    bg: "bg-indigo-500/10",
    border: "border-indigo-500/30",
    badge: "bg-indigo-500/15 text-indigo-800 border-indigo-500/30",
    btn: "bg-indigo-600 hover:bg-indigo-500",
  },
  fire: {
    label: "Fire & Rescue",
    color: "orange",
    icon: Flame,
    bg: "bg-orange-500/10",
    border: "border-orange-500/30",
    badge: "bg-orange-500/15 text-orange-800 border-orange-500/30",
    btn: "bg-orange-600 hover:bg-orange-500",
  },
  disaster: {
    label: "Disaster / Accident",
    color: "amber",
    icon: Zap,
    bg: "bg-amber-500/10",
    border: "border-amber-500/30",
    badge: "bg-amber-500/15 text-amber-800 border-amber-500/30",
    btn: "bg-amber-600 hover:bg-amber-500",
  },
  women: {
    label: "Women & Child",
    color: "pink",
    icon: Baby,
    bg: "bg-pink-500/10",
    border: "border-pink-500/30",
    badge: "bg-pink-500/15 text-pink-800 border-pink-500/30",
    btn: "bg-pink-600 hover:bg-pink-500",
  },
  other: {
    label: "Other Helplines",
    color: "slate",
    icon: HelpCircle,
    bg: "bg-slate-700/10",
    border: "border-slate-700/30",
    badge: "bg-slate-700/15 text-slate-300 border-slate-700/30",
    btn: "bg-slate-600 hover:bg-slate-500",
  },
};

const CATEGORY_ORDER = [
  "critical",
  "medical",
  "police",
  "fire",
  "disaster",
  "women",
  "other",
];

// ─── Single contact card ──────────────────────────────────────────────────────
const ContactCard = ({ contact }) => {
  const meta = CATEGORY_META[contact.category] || CATEGORY_META.other;
  const Icon = meta.icon;
  return (
    <div
      className={`glass-card p-4 rounded-2xl flex items-center justify-between gap-4 border ${meta.border} ${meta.bg} hover:scale-[1.02] transition-all duration-200 group`}
    >
      <div className="flex items-center gap-3 min-w-0">
        <div
          className={`shrink-0 p-2 rounded-xl ${meta.bg} border ${meta.border}`}
        >
          <Icon className="h-4 w-4 text-current opacity-70" />
        </div>
        <div className="min-w-0">
          <p className="text-[11px] text-slate-400 font-bold uppercase tracking-wider truncate">
            {contact.name}
          </p>
          <p className="text-2xl font-extrabold text-slate-100 leading-tight">
            {contact.number}
          </p>
          <p className="text-[10px] text-slate-500 leading-snug mt-0.5 line-clamp-2">
            {contact.description}
          </p>
        </div>
      </div>
      <a
        href={`tel:${contact.number}`}
        className={`shrink-0 ${meta.btn} text-white p-3 rounded-xl transition-all duration-200 group-hover:scale-110 shadow-lg`}
        title={`Call ${contact.name}: ${contact.number}`}
      >
        <PhoneCall className="h-4 w-4" />
      </a>
    </div>
  );
};

// ─── Main EmergencyPanel ──────────────────────────────────────────────────────
const EmergencyPanel = () => {
  const [contacts, setContacts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [activeFilter, setActiveFilter] = useState("all");

  useEffect(() => {
    (async () => {
      try {
        setContacts(await getEmergencyContacts());
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

  // Filter by search text + active category button
  const filtered = contacts.filter((c) => {
    const q = search.toLowerCase();
    const matchSearch =
      !q ||
      c.name.toLowerCase().includes(q) ||
      c.number.includes(q) ||
      c.description.toLowerCase().includes(q);
    const matchCat = activeFilter === "all" || c.category === activeFilter;
    return matchSearch && matchCat;
  });

  // Group by category in order
  const grouped = CATEGORY_ORDER.reduce((acc, cat) => {
    const items = filtered.filter((c) => (c.category || "other") === cat);
    if (items.length) acc[cat] = items;
    return acc;
  }, {});

  // Unique categories present
  const presentCats = CATEGORY_ORDER.filter((cat) =>
    contacts.some((c) => (c.category || "other") === cat),
  );

  return (
    <div className="w-full max-w-5xl mx-auto flex flex-col gap-6">
      {/* Alert Header */}
      <div className="bg-rose-500/10 border border-rose-500/20 p-5 rounded-2xl flex items-start gap-4">
        <div className="bg-rose-500/25 p-2 rounded-xl text-rose-400 shrink-0 mt-0.5 animate-pulse">
          <ShieldAlert className="h-6 w-6" />
        </div>
        <div>
          <h2 className="text-lg font-bold text-slate-100">
            India Emergency Helpline Numbers
          </h2>
          <p className="text-sm text-slate-300 mt-1 leading-relaxed">
            All official helpline numbers — active 24/7. Tap any card to dial
            directly from your device.
          </p>
        </div>
      </div>

      {/* Search bar */}
      <div className="relative">
        <Search className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-500" />
        <input
          type="text"
          placeholder="Search by name, number, or service…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-slate-900/60 border border-slate-800 rounded-xl pl-10 pr-4 py-3 text-sm text-slate-200 focus:outline-none focus:border-blue-500/60 transition-colors placeholder:text-slate-600"
        />
      </div>

      {/* Category filter pills */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveFilter("all")}
          className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-all cursor-pointer ${
            activeFilter === "all"
              ? "bg-slate-200 border-slate-200 text-white"
              : "bg-transparent border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-300"
          }`}
        >
          All ({contacts.length})
        </button>
        {presentCats.map((cat) => {
          const meta = CATEGORY_META[cat];
          const count = contacts.filter(
            (c) => (c.category || "other") === cat,
          ).length;
          return (
            <button
              key={cat}
              onClick={() => setActiveFilter(cat)}
              className={`text-xs font-bold px-3 py-1.5 rounded-full border transition-all cursor-pointer ${
                activeFilter === cat
                  ? `${meta.badge} scale-105`
                  : "bg-transparent border-slate-700 text-slate-400 hover:border-slate-500 hover:text-slate-300"
              }`}
            >
              {meta.label} ({count})
            </button>
          );
        })}
      </div>

      {/* Cards */}
      {loading ? (
        <div className="flex justify-center items-center py-20">
          <Loader2 className="h-8 w-8 text-blue-500 animate-spin" />
        </div>
      ) : Object.keys(grouped).length === 0 ? (
        <div className="text-center py-12 text-slate-500 text-sm">
          No results for "<span className="text-slate-100">{search}</span>"
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {Object.entries(grouped).map(([cat, items]) => {
            const meta = CATEGORY_META[cat] || CATEGORY_META.other;
            const Icon = meta.icon;
            return (
              <div key={cat}>
                {/* Section heading */}
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className={`inline-flex items-center gap-1.5 text-[10px] font-extrabold uppercase tracking-widest px-2.5 py-1 rounded-full border ${meta.badge}`}
                  >
                    <Icon className="h-3 w-3" />
                    {meta.label}
                  </span>
                  <div className="flex-1 h-px bg-slate-800" />
                  <span className="text-[10px] text-slate-600 font-semibold">
                    {items.length} numbers
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                  {items.map((c, i) => (
                    <ContactCard key={i} contact={c} />
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Guidelines */}
      <div className="glass-card p-6 rounded-2xl flex items-start gap-4">
        <HeartHandshake className="h-6 w-6 text-emerald-500 shrink-0 mt-0.5" />
        <div>
          <h3 className="text-sm font-bold text-slate-100">
            Guidelines When Calling Emergency Services
          </h3>
          <ul className="text-xs text-slate-400 mt-2 list-disc list-inside flex flex-col gap-1.5 leading-relaxed">
            <li>State your name, phone number, and location clearly.</li>
            <li>
              Briefly explain the situation (medical, fire, hazard, accident).
            </li>
            <li>
              State how many people require help and details on their
              conditions.
            </li>
            <li>Follow any first aid instructions given by the operator.</li>
            <li>Do not hang up until the operator tells you to do so.</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default EmergencyPanel;
