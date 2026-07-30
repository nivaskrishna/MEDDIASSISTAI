import React, { useState, useRef, useEffect } from "react";
import {
  Stethoscope,
  MapPin,
  BookOpen,
  PhoneCall,
  ShieldAlert,
  Camera,
  X,
  Send,
  Sparkles,
  Mic,
  MicOff,
  Quote,
  RefreshCw,
  Globe,
} from "lucide-react";
import { fetchGlobalStats } from "../services/diseaseApi";
import { fetchHealthQuote } from "../services/quoteApi";
import {
  startListening,
  stopListening,
  isRecognitionSupported,
} from "../services/speechService";

const Home = ({
  setActiveTab,
  setInitialQuery,
  setInitialImage,
  setInitialImagePreview,
}) => {
  const [query, setQuery] = useState("");
  const [image, setImage] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  const fileInputRef = useRef(null);

  // Global health stats (disease.sh)
  const [globalStats, setGlobalStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);

  // Health quote (quotable.io)
  const [quote, setQuote] = useState(null);
  const [quoteLoading, setQuoteLoading] = useState(true);

  // Voice input (Web Speech API)
  const [voiceActive, setVoiceActive] = useState(false);
  const [interimText, setInterimText] = useState("");
  const [voiceError, setVoiceError] = useState(null);

  useEffect(() => {
    fetchGlobalStats().then((data) => {
      setGlobalStats(data);
      setStatsLoading(false);
    });
    loadQuote();
  }, []);

  const loadQuote = async () => {
    setQuoteLoading(true);
    const q = await fetchHealthQuote();
    setQuote(q);
    setQuoteLoading(false);
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result);
      setImage(reader.result);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveImage = () => {
    setImage(null);
    setImagePreview(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() && !image) return;
    setInitialQuery(query);
    setInitialImage(image);
    setInitialImagePreview(imagePreview);
    setActiveTab("analyzer");
  };

  const handleVoiceToggle = () => {
    if (voiceActive) {
      stopListening();
      setVoiceActive(false);
      setInterimText("");
    } else {
      setVoiceError(null);
      setVoiceActive(true);
      startListening(
        (finalText) => {
          setQuery((prev) => (prev ? prev + " " + finalText : finalText));
          setVoiceActive(false);
          setInterimText("");
        },
        (interim) => setInterimText(interim),
        (err) => {
          setVoiceError(err);
          setVoiceActive(false);
          setInterimText("");
          setTimeout(() => setVoiceError(null), 4000);
        },
      );
    }
  };

  const fmt = (n) => {
    if (!n && n !== 0) return "—";
    if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
    if (n >= 1_000) return (n / 1_000).toFixed(0) + "K";
    return n.toLocaleString();
  };

  const cards = [
    {
      id: "analyzer",
      title: "AI Symptom Analyzer",
      icon: Stethoscope,
      color: "from-blue-500 to-emerald-500",
      description:
        "Describe your symptoms in natural language. Our AI will analyze conditions, suggest first aid, and specify doctor specialties.",
    },
    {
      id: "hospitals",
      title: "Find Nearby Hospitals",
      icon: MapPin,
      color: "from-emerald-500 to-teal-500",
      description:
        "Enter your pincode and search radius. Track hospitals on Leaflet Maps with distance calculations and navigation links.",
    },
    {
      id: "kb",
      title: "First Aid + Medicines",
      icon: BookOpen,
      color: "from-teal-500 to-cyan-500",
      description:
        "Search our vetted knowledge base of medical conditions, first aid instructions, drug information, and severity ratings.",
    },
    {
      id: "contacts",
      title: "Emergency Contacts",
      icon: PhoneCall,
      color: "from-rose-500 to-orange-500",
      description:
        "Immediate access to country-specific emergency numbers: National Emergency, Ambulance, Police, Fire, and Helpline panels.",
    },
  ];

  const statItems = [
    { label: "Total Cases", value: globalStats?.cases, color: "text-blue-400" },
    { label: "Active", value: globalStats?.active, color: "text-amber-400" },
    {
      label: "Recovered",
      value: globalStats?.recovered,
      color: "text-emerald-400",
    },
    {
      label: "Today's Cases",
      value: globalStats?.todayCases,
      color: "text-violet-400",
    },
  ];

  return (
    <div className="max-w-6xl mx-auto flex flex-col gap-8 sm:gap-10 py-6 px-4 md:px-8">
      {/* ── Global Health Stats Banner ───────────────────────────────── */}
      <div className="glass-card rounded-2xl border border-slate-800/60 p-4 flex flex-col sm:flex-row items-center gap-4">
        <div className="flex items-center gap-2 shrink-0">
          <Globe className="h-4 w-4 text-blue-400" />
          <span className="text-xs font-bold text-slate-400 uppercase tracking-wider">
            Global Health Tracker
          </span>
        </div>
        {statsLoading ? (
          <div className="flex gap-6 flex-1 animate-pulse">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-8 w-20 bg-slate-800 rounded-lg" />
            ))}
          </div>
        ) : globalStats ? (
          <div className="flex flex-wrap gap-6 flex-1">
            {statItems.map((s) => (
              <div key={s.label} className="flex flex-col">
                <span className={`text-sm font-extrabold ${s.color}`}>
                  {fmt(s.value)}
                </span>
                <span className="text-[10px] text-slate-500 font-medium">
                  {s.label}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <span className="text-xs text-slate-500">
            Health stats unavailable
          </span>
        )}
        <span className="text-[9px] text-slate-600 shrink-0">
          via disease.sh
        </span>
      </div>

      {/* ── Hero + Search ────────────────────────────────────────────── */}
      <div className="text-center relative">
        <div className="absolute inset-0 bg-blue-500/10 rounded-full blur-3xl w-72 h-72 mx-auto -z-10" />
        <span className="text-xs font-bold text-blue-500 bg-blue-600/15 border border-blue-500/20 px-3 py-1 rounded-full uppercase tracking-wider">
          AI Healthcare Assistant
        </span>
        <h1 className="text-3xl md:text-5xl font-extrabold text-slate-100 mt-4 tracking-tight leading-tight px-2">
          Your Intelligent Shield in <br className="hidden sm:block" />
          <span className="bg-gradient-to-r from-blue-500 via-emerald-500 to-teal-500 bg-clip-text text-transparent">
            Medical Situations
          </span>
        </h1>
        <p className="text-sm md:text-base text-slate-400 mt-4 max-w-xl mx-auto leading-relaxed">
          MediAssist AI combines generative intelligence with location-aware
          search to give you fast, reliable first aid information and connect
          you with local medical care.
        </p>

        {/* Search bar */}
        <div className="max-w-3xl mx-auto mt-8 w-full px-4">
          <form
            onSubmit={handleSubmit}
            className="glass-card p-2 sm:p-3 rounded-2xl flex flex-col sm:flex-row gap-2 sm:gap-3 border border-slate-800/80 focus-within:border-blue-500/50 focus-within:shadow-lg focus-within:shadow-blue-500/5 transition-all duration-300"
          >
            <div className="flex items-center gap-2 sm:gap-3 px-2 sm:px-0 flex-1 min-w-0">
              <div className="p-1 sm:p-2 text-blue-400 shrink-0 hidden sm:block">
                <Sparkles className="h-5 w-5 sm:h-6 sm:w-6" />
              </div>

              <input
                type="text"
                value={voiceActive ? interimText || query : query}
                onChange={(e) => !voiceActive && setQuery(e.target.value)}
                placeholder={
                  voiceActive
                    ? "🎙️ Listening… speak your symptoms"
                    : imagePreview
                      ? "Describe the symptoms shown in photo..."
                      : "Describe symptoms (e.g., severe burn, chest pain) or snap a photo..."
                }
                className={`flex-1 min-w-0 bg-transparent border-0 text-slate-100 placeholder-slate-500 text-sm sm:text-lg focus:outline-none py-2 sm:py-3 ${voiceActive ? "placeholder-violet-400" : ""}`}
                readOnly={voiceActive}
              />
            </div>

            <div className="flex items-center gap-2 sm:gap-3">
              {/* Voice input */}
              {isRecognitionSupported() && (
                <button
                  type="button"
                  id="voice-input-btn"
                  onClick={handleVoiceToggle}
                  title={
                    voiceActive
                      ? "Stop recording"
                      : "Voice input — speak your symptoms"
                  }
                  className={`flex-1 sm:flex-none flex justify-center items-center p-3 rounded-xl transition-all duration-200 shrink-0 cursor-pointer ${
                    voiceActive
                      ? "bg-violet-600 text-white animate-pulse shadow-lg shadow-violet-500/30"
                      : "bg-slate-900 sm:bg-transparent hover:bg-slate-800 text-slate-400 hover:text-violet-400"
                  }`}
                >
                  {voiceActive ? (
                    <MicOff className="h-5 w-5 sm:h-5.5 sm:w-5.5" />
                  ) : (
                    <Mic className="h-5 w-5 sm:h-5.5 sm:w-5.5" />
                  )}
                </button>
              )}

              <input
                type="file"
                ref={fileInputRef}
                onChange={handleImageChange}
                accept="image/*"
                capture="environment"
                className="hidden"
              />
              <button
                type="button"
                id="camera-btn"
                onClick={() => fileInputRef.current.click()}
                className="flex-1 sm:flex-none flex justify-center items-center p-3 bg-slate-900 sm:bg-transparent hover:bg-slate-800 text-slate-400 hover:text-slate-200 rounded-xl transition-colors cursor-pointer shrink-0"
                title="Capture photo or upload image"
              >
                <Camera className="h-5 w-5 sm:h-5.5 sm:w-5.5" />
              </button>

              <button
                type="submit"
                id="analyze-submit-btn"
                disabled={!query.trim() && !image}
                className="flex-[2] sm:flex-none bg-blue-600 hover:bg-blue-500 text-white font-bold px-4 py-3 sm:p-3 rounded-xl flex items-center justify-center transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed shrink-0"
              >
                <Send className="h-5 w-5 sm:h-5.5 sm:w-5.5" />
              </button>
            </div>

            {voiceError && (
              <div className="mx-2 mb-1 text-xs text-rose-400 bg-rose-500/10 border border-rose-500/20 rounded-lg px-3 py-2">
                {voiceError}
              </div>
            )}

            {imagePreview && (
              <div className="flex items-center gap-2 bg-slate-900/80 border border-slate-800 p-2 rounded-xl mt-1 self-start ml-2 relative">
                <img
                  src={imagePreview}
                  alt="Attached symptom preview"
                  className="h-14 w-14 object-cover rounded-lg border border-slate-700"
                />
                <div className="text-left pr-6">
                  <p className="text-xs font-semibold text-slate-200">
                    Photo Attached
                  </p>
                  <p className="text-xxs text-slate-500">Ready to analyze</p>
                </div>
                <button
                  type="button"
                  onClick={handleRemoveImage}
                  className="absolute top-1 right-1 bg-rose-600/90 hover:bg-rose-500 text-white p-0.5 rounded-full border border-slate-950 transition-colors cursor-pointer"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            )}
          </form>

          <div className="flex justify-center mt-4">
            <button
              onClick={() => setActiveTab("contacts")}
              className="text-xs text-rose-400 hover:text-rose-300 flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-rose-500/5 hover:bg-rose-500/10 border border-rose-500/10 hover:border-rose-500/20 transition-all cursor-pointer"
            >
              <PhoneCall className="h-3.5 w-3.5" /> Need immediate assistance?
              Emergency Hotline
            </button>
          </div>
        </div>

        {/* Health quote widget */}
        <div className="max-w-2xl mx-auto mt-5 px-4">
          <div className="glass-card rounded-xl border border-emerald-500/10 bg-emerald-950/10 px-5 py-4 flex items-start gap-3 text-left">
            <Quote className="h-4 w-4 text-emerald-400 shrink-0 mt-0.5" />
            {quoteLoading ? (
              <div className="flex-1 animate-pulse">
                <div className="h-4 bg-slate-800 rounded w-3/4 mb-2" />
                <div className="h-3 bg-slate-800 rounded w-1/3" />
              </div>
            ) : quote ? (
              <div className="flex-1">
                <p className="text-sm text-slate-300 italic leading-relaxed">
                  "{quote.content}"
                </p>
                <p className="text-[11px] text-emerald-400 font-bold mt-1.5">
                  — {quote.author}
                </p>
              </div>
            ) : null}
            <button
              onClick={loadQuote}
              className="p-1.5 hover:bg-emerald-500/10 rounded-lg transition-colors shrink-0 text-slate-500 hover:text-emerald-400 cursor-pointer"
              title="Next quote"
            >
              <RefreshCw
                className={`h-3.5 w-3.5 ${quoteLoading ? "animate-spin" : ""}`}
              />
            </button>
          </div>
        </div>
      </div>

      {/* ── Feature Cards ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              id={`feature-card-${card.id}`}
              onClick={() => setActiveTab(card.id)}
              className="glass-card p-6 rounded-2xl cursor-pointer transition-all duration-300 hover:border-blue-500/30 hover:shadow-lg hover:shadow-blue-500/5 group"
            >
              <div
                className={`w-12 h-12 rounded-xl bg-gradient-to-r ${card.color} p-0.5 mb-5 flex items-center justify-center shrink-0 shadow-md`}
              >
                <div className="bg-slate-100 w-full h-full rounded-xl flex items-center justify-center">
                  <Icon className="h-5 w-5 text-white" />
                </div>
              </div>
              <h3 className="text-lg font-bold text-slate-100 group-hover:text-blue-500 transition-colors">
                {card.title}
              </h3>
              <p className="text-xs text-slate-400 mt-2.5 leading-relaxed">
                {card.description}
              </p>
            </div>
          );
        })}
      </div>

      {/* ── Critical Notice ──────────────────────────────────────────── */}
      <div className="glass-card border-rose-500/20 bg-rose-500/5 p-6 rounded-2xl flex items-start gap-4">
        <ShieldAlert className="h-6 w-6 text-rose-500 shrink-0 mt-0.5 animate-pulse" />
        <div>
          <h4 className="text-sm font-bold text-slate-100 uppercase tracking-wider">
            Critical Medical Notice
          </h4>
          <p className="text-xs text-rose-300/80 leading-relaxed mt-1.5">
            This system serves solely as a supportive resource offering
            immediate first aid guidelines and hospital directories. It is{" "}
            <strong>not</strong> an alternative to direct emergency rescue
            systems or licensed practitioners. In a serious crisis, please rely
            on state emergency lines first.
          </p>
        </div>
      </div>
    </div>
  );
};

export default Home;
