import React, { useState, useEffect } from "react";
import { getConditions, searchDrug } from "../services/api";
import {
  Search,
  Loader2,
  BookOpen,
  AlertCircle,
  Heart,
  User,
  CheckCircle2,
  Pill,
  AlertTriangle,
  Info,
  ChevronDown,
  ChevronUp,
} from "lucide-react";

// ──────────────────────────────────────────────────────────────────
// Shared severity styles helper
// ──────────────────────────────────────────────────────────────────
const getSeverityStyles = (severity) => {
  switch (severity?.toLowerCase()) {
    case "low":
      return "bg-emerald-500/10 text-emerald-400 border-emerald-500/20";
    case "medium":
      return "bg-yellow-500/10  text-yellow-400  border-yellow-500/20";
    case "high":
      return "bg-orange-500/10  text-orange-400  border-orange-500/20";
    case "critical":
      return "bg-rose-500/10    text-rose-400    border-rose-500/20 animate-pulse";
    default:
      return "bg-slate-500/10   text-slate-400   border-slate-500/20";
  }
};

// ──────────────────────────────────────────────────────────────────
// First Aid Conditions Tab (unchanged logic)
// ──────────────────────────────────────────────────────────────────
const ConditionsTab = () => {
  const [conditions, setConditions] = useState([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedCondition, setSelectedCondition] = useState(null);

  const fetchConditions = async (searchTerm = "") => {
    setLoading(true);
    try {
      const data = await getConditions(searchTerm);
      setConditions(data);
      if (data.length > 0 && !selectedCondition) setSelectedCondition(data[0]);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const timer = setTimeout(() => fetchConditions(search), 300);
    return () => clearTimeout(timer);
  }, [search]);

  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full lg:h-[600px] h-auto items-stretch">
      {/* List */}
      <div className="w-full lg:w-96 flex flex-col gap-4 shrink-0 overflow-hidden">
        <div className="glass-card p-5 rounded-2xl shrink-0">
          <h2 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-blue-500" /> First Aid Knowledge
            Base
          </h2>
          <div className="relative">
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search condition (e.g. burn, fracture)..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors placeholder:text-slate-500"
            />
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          </div>
        </div>

        <div className="glass-card p-5 rounded-2xl h-[300px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3 mb-3 shrink-0">
            <h3 className="text-sm font-bold text-slate-100">
              Emergency Guide Directory
            </h3>
            {loading && (
              <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
            )}
          </div>
          <div className="flex-1 overflow-y-auto flex flex-col gap-2 pr-1">
            {conditions.length === 0 && !loading ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-10">
                <AlertCircle className="h-6 w-6 mb-2 opacity-40" />
                <p className="text-xs">No matching conditions found.</p>
              </div>
            ) : (
              conditions.map((item) => (
                <div
                  key={item.id}
                  onClick={() => setSelectedCondition(item)}
                  className={`p-3.5 rounded-xl border transition-all duration-300 cursor-pointer flex flex-col gap-1.5 ${selectedCondition?.id === item.id ? "bg-blue-950/20 border-blue-500 shadow-md shadow-blue-500/5" : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"}`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">
                      {item.condition_name}
                    </h4>
                    <span
                      className={`text-xxs px-2 py-0.5 rounded-full border shrink-0 ${getSeverityStyles(item.severity_level)}`}
                    >
                      {item.severity_level}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {item.symptoms.slice(0, 3).map((sym, i) => (
                      <span
                        key={i}
                        className="text-xxs bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded"
                      >
                        {sym}
                      </span>
                    ))}
                    {item.symptoms.length > 3 && (
                      <span className="text-xxs text-slate-500 px-1 py-0.5">
                        + {item.symptoms.length - 3} more
                      </span>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Detail */}
      <div className="flex-1 min-h-[350px] lg:min-h-0">
        {selectedCondition ? (
          <div className="glass-card p-6 rounded-2xl h-auto lg:h-full flex flex-col gap-6 lg:overflow-y-auto lg:relative">
            <div className="absolute top-0 right-0 w-32 h-32 bg-blue-500/5 rounded-full blur-3xl" />
            <div className="flex items-center justify-between border-b border-slate-800 pb-4">
              <div>
                <span className="text-xs text-slate-400 uppercase font-semibold tracking-wider">
                  Condition detail
                </span>
                <h2 className="text-2xl font-extrabold text-slate-100 mt-1">
                  {selectedCondition.condition_name}
                </h2>
              </div>
              <span
                className={`px-3 py-1 rounded-full border text-xs font-bold ${getSeverityStyles(selectedCondition.severity_level)}`}
              >
                {selectedCondition.severity_level} Severity
              </span>
            </div>
            <div>
              <h4 className="text-sm font-bold text-slate-300 mb-2">
                Key Symptoms
              </h4>
              <div className="flex flex-wrap gap-2">
                {selectedCondition.symptoms.map((sym, i) => (
                  <span
                    key={i}
                    className="text-xs font-medium bg-slate-900 border border-slate-800 text-slate-300 px-2.5 py-1.5 rounded-lg flex items-center gap-1.5"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5 text-blue-500 shrink-0" />{" "}
                    {sym}
                  </span>
                ))}
              </div>
            </div>
            <div className="flex items-start gap-3 bg-slate-900/60 p-5 rounded-xl border border-slate-800 leading-relaxed">
              <Heart className="h-5 w-5 text-rose-500 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-slate-100">
                  First Aid Guideline
                </h4>
                <p className="text-sm text-slate-300 mt-2 whitespace-pre-line leading-relaxed">
                  {selectedCondition.first_aid_instructions}
                </p>
              </div>
            </div>
            <div className="flex items-start gap-3 bg-slate-900/60 p-5 rounded-xl border border-slate-800">
              <User className="h-5 w-5 text-blue-400 shrink-0 mt-0.5" />
              <div>
                <h4 className="text-sm font-bold text-slate-100">
                  Recommended Doctor Specialty
                </h4>
                <p className="text-sm text-slate-300 mt-1.5">
                  It is recommended to seek medical follow-up with a{" "}
                  <span className="text-blue-400 font-extrabold">
                    {selectedCondition.recommended_doctor_type}
                  </span>
                  .
                </p>
              </div>
            </div>
          </div>
        ) : (
          <div className="glass-card p-6 rounded-2xl h-full flex flex-col items-center justify-center text-center py-20 border-dashed border-slate-800">
            <h3 className="text-lg font-bold text-slate-100">
              Select a Condition
            </h3>
            <p className="text-sm text-slate-400 mt-2 max-w-xs mx-auto">
              Select any medical condition from the list on the left to view
              detailed first aid instructions, symptoms, and doctor suggestions.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// Drug result card component
// ──────────────────────────────────────────────────────────────────
const DrugCard = ({ drug }) => {
  const [expanded, setExpanded] = useState(false);

  const Section = ({
    icon: Icon,
    title,
    content,
    color = "text-slate-300",
  }) => {
    if (!content || content === "Not available") return null;
    return (
      <div className="border-t border-slate-800/60 pt-3 mt-3">
        <h5 className="text-xs font-bold text-slate-400 flex items-center gap-1.5 mb-1.5">
          <Icon className={`h-3.5 w-3.5 ${color}`} /> {title}
        </h5>
        <p className={`text-xs ${color} leading-relaxed line-clamp-4`}>
          {content}
        </p>
      </div>
    );
  };

  return (
    <div className="glass-card rounded-xl border border-slate-800/60 p-4 flex flex-col gap-2">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="text-sm font-extrabold text-slate-100">
            {drug.brand_name}
          </h4>
          {drug.generic_name !== drug.brand_name &&
            drug.generic_name !== "Not available" && (
              <p className="text-xs text-slate-400 mt-0.5">
                Generic:{" "}
                <span className="text-slate-300">{drug.generic_name}</span>
              </p>
            )}
          <div className="flex flex-wrap gap-1.5 mt-2">
            {drug.route !== "Not available" && (
              <span className="text-[10px] bg-blue-500/10 text-blue-400 border border-blue-500/20 px-2 py-0.5 rounded-full font-bold">
                {drug.route}
              </span>
            )}
            {drug.product_type !== "Not available" && (
              <span className="text-[10px] bg-slate-800 text-slate-400 border border-slate-700/50 px-2 py-0.5 rounded-full">
                {drug.product_type}
              </span>
            )}
          </div>
        </div>
        <button
          onClick={() => setExpanded((p) => !p)}
          className="text-slate-500 hover:text-slate-300 transition-colors p-1 cursor-pointer shrink-0"
        >
          {expanded ? (
            <ChevronUp className="h-4 w-4" />
          ) : (
            <ChevronDown className="h-4 w-4" />
          )}
        </button>
      </div>

      {drug.indications !== "Not available" && (
        <div className="bg-slate-900/50 rounded-lg px-3 py-2">
          <p className="text-xs text-slate-300 leading-relaxed line-clamp-3">
            {drug.indications}
          </p>
        </div>
      )}

      {expanded && (
        <div className="mt-1">
          <Section
            icon={AlertTriangle}
            title="Warnings"
            content={drug.warnings}
            color="text-amber-300"
          />
          <Section
            icon={Info}
            title="Side Effects"
            content={drug.side_effects}
            color="text-slate-300"
          />
          <Section
            icon={AlertCircle}
            title="Contraindications"
            content={drug.contraindications}
            color="text-rose-300"
          />
          <Section
            icon={Pill}
            title="Dosage"
            content={drug.dosage}
            color="text-blue-300"
          />
          {drug.manufacturer !== "Not available" && (
            <p className="text-[10px] text-slate-600 mt-3 border-t border-slate-800/40 pt-2">
              Manufacturer: {drug.manufacturer}
            </p>
          )}
        </div>
      )}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// Medicines / Drug Search Tab (OpenFDA)
// ──────────────────────────────────────────────────────────────────
const MedicinesTab = () => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);
  const [error, setError] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim() || query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    setSearched(true);
    try {
      const data = await searchDrug(query.trim(), 5);
      setResults(data.results || []);
      if ((data.results || []).length === 0)
        setError(
          "No FDA-approved drug found for that name. Try a different spelling or generic name.",
        );
    } catch {
      setError("Could not reach the drug database. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const suggestions = [
    "aspirin",
    "ibuprofen",
    "paracetamol",
    "amoxicillin",
    "metformin",
    "atorvastatin",
  ];

  return (
    <div className="flex flex-col gap-6 w-full">
      {/* Search bar */}
      <div className="glass-card p-5 rounded-2xl">
        <h2 className="text-lg font-bold text-slate-100 mb-1 flex items-center gap-2">
          <Pill className="h-5 w-5 text-purple-400" /> Drug Information Lookup
        </h2>
        <p className="text-xs text-slate-400 mb-4">
          Search FDA-approved drug labels — indications, dosage, side effects,
          warnings.
        </p>
        <form onSubmit={handleSearch} className="flex gap-2">
          <div className="relative flex-1">
            <input
              type="text"
              id="drug-search-input"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter drug name (e.g. aspirin, amoxicillin)..."
              className="w-full bg-slate-900 border border-slate-800 rounded-xl pl-10 pr-4 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-purple-500 transition-colors placeholder:text-slate-500"
            />
            <Search className="absolute left-3 top-3 h-4 w-4 text-slate-500" />
          </div>
          <button
            type="submit"
            disabled={loading || query.trim().length < 2}
            className="bg-purple-600 hover:bg-purple-500 text-white px-5 py-2.5 rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2 cursor-pointer"
          >
            {loading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Search className="h-4 w-4" />
            )}
            Search
          </button>
        </form>

        {/* Quick suggestions */}
        <div className="flex flex-wrap gap-2 mt-3">
          <span className="text-[10px] text-slate-500 font-semibold uppercase tracking-wider self-center">
            Try:
          </span>
          {suggestions.map((s) => (
            <button
              key={s}
              onClick={() => {
                setQuery(s);
              }}
              className="text-[10px] text-purple-400 hover:text-purple-300 border border-purple-500/20 hover:border-purple-400/30 bg-purple-500/5 hover:bg-purple-500/10 px-2.5 py-1 rounded-full transition-all cursor-pointer"
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Results */}
      {loading && (
        <div className="flex items-center justify-center gap-3 py-16 text-slate-500">
          <Loader2 className="h-6 w-6 animate-spin text-purple-400" />
          <span className="text-sm">Searching FDA drug database…</span>
        </div>
      )}

      {error && !loading && (
        <div className="flex items-start gap-3 bg-amber-950/20 border border-amber-500/20 p-4 rounded-xl text-amber-300 text-sm">
          <AlertCircle className="h-5 w-5 shrink-0 mt-0.5" /> {error}
        </div>
      )}

      {!loading && results.length > 0 && (
        <div className="flex flex-col gap-4">
          <p className="text-xs text-slate-500 font-semibold">
            {results.length} result{results.length !== 1 ? "s" : ""} found —
            data from OpenFDA
          </p>
          {results.map((drug, i) => (
            <DrugCard key={i} drug={drug} />
          ))}
        </div>
      )}

      {!loading && !searched && (
        <div className="flex flex-col items-center justify-center py-16 text-slate-600 gap-3">
          <Pill className="h-12 w-12 opacity-20" />
          <p className="text-sm">
            Search for any medication name above to see FDA label information.
          </p>
        </div>
      )}
    </div>
  );
};

// ──────────────────────────────────────────────────────────────────
// Main KnowledgeBase page — tabs: First Aid | Medicines
// ──────────────────────────────────────────────────────────────────
const KnowledgeBase = ({ defaultTab = "firstaid" }) => {
  const [activeTab, setActiveTab] = useState(defaultTab);

  useEffect(() => {
    setActiveTab(defaultTab);
  }, [defaultTab]);

  return (
    <div className="w-full max-w-6xl mx-auto flex flex-col gap-5">
      {/* Tab switcher */}
      <div className="flex gap-1 p-1 bg-slate-900/50 border border-slate-800 rounded-xl self-start">
        <button
          id="tab-firstaid"
          onClick={() => setActiveTab("firstaid")}
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer flex items-center gap-2 ${activeTab === "firstaid" ? "bg-blue-600 text-white shadow-lg shadow-blue-500/20" : "text-slate-400 hover:text-slate-200"}`}
        >
          <Heart className="h-4 w-4" /> First Aid Guide
        </button>
        <button
          id="tab-medicines"
          onClick={() => setActiveTab("medicines")}
          className={`px-4 py-2 rounded-lg text-sm font-bold transition-all cursor-pointer flex items-center gap-2 ${activeTab === "medicines" ? "bg-purple-600 text-white shadow-lg shadow-purple-500/20" : "text-slate-400 hover:text-slate-200"}`}
        >
          <Pill className="h-4 w-4" /> Drug Lookup
        </button>
      </div>

      {activeTab === "firstaid" ? <ConditionsTab /> : <MedicinesTab />}
    </div>
  );
};

export default KnowledgeBase;
