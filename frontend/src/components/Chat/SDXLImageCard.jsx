/**
 * SDXLImageCard.jsx
 *
 * A self-contained card component that lets users generate a Stable Diffusion XL
 * image from a text prompt.  It is rendered inside AnalyzerChat after a successful
 * analysis result – the first-aid condition is pre-filled as the prompt.
 *
 * Props
 * -----
 * defaultPrompt  {string}  – Pre-filled text (e.g. the condition name + first aid step)
 */

import React, { useState } from "react";
import { generateSDXLImage } from "../../services/api";
import {
  Sparkles,
  Loader2,
  AlertTriangle,
  Download,
  RefreshCw,
  Image,
} from "lucide-react";

const QUALITY_SUFFIX =
  "high quality, highly detailed, professional digital art, sharp focus, cinematic lighting";

const SDXLImageCard = ({ defaultPrompt = "" }) => {
  const [prompt, setPrompt] = useState(defaultPrompt);
  const [imageUrl, setImageUrl] = useState(null);
  const [promptUsed, setPromptUsed] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleGenerate = async () => {
    if (!prompt.trim()) return;
    setLoading(true);
    setError(null);
    setImageUrl(null);

    try {
      const data = await generateSDXLImage(prompt.trim());
      setImageUrl(data.image_url);
      setPromptUsed(data.prompt_used);
    } catch (err) {
      const msg =
        err?.response?.data?.detail ||
        err?.message ||
        "Image generation failed. Please try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = () => {
    if (!imageUrl) return;
    const link = document.createElement("a");
    link.href = imageUrl;
    link.download = "mediassist-sdxl.jpg";
    link.click();
  };

  return (
    <div className="glass-card p-5 rounded-xl border border-slate-800 bg-slate-900/40 flex flex-col gap-4 text-left">
      {/* Header */}
      <h3 className="text-sm font-extrabold text-slate-200 uppercase tracking-widest flex items-center gap-2 border-b border-slate-800/60 pb-3">
        <Image className="h-4 w-4 text-violet-400" />
        AI Image Studio
        <span className="ml-auto text-[9px] font-bold text-violet-400/70 bg-violet-500/10 border border-violet-500/20 px-2 py-0.5 rounded-full uppercase tracking-wider">
          SDXL
        </span>
      </h3>

      {/* Prompt input */}
      <div className="flex flex-col gap-2">
        <label className="text-[10px] font-extrabold text-slate-400 uppercase tracking-wider">
          Image Prompt
        </label>
        <textarea
          id="sdxl-prompt-input"
          rows={3}
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the first aid scene to visualise…"
          className="w-full bg-slate-950/60 border border-slate-800 rounded-lg px-3 py-2 text-xs text-slate-200 placeholder-slate-600 resize-none focus:outline-none focus:border-violet-500/60 transition-colors"
        />
        <p className="text-[9px] text-slate-600 leading-relaxed">
          Quality modifiers auto-appended:{" "}
          <span className="text-slate-500 italic">{QUALITY_SUFFIX}</span>
        </p>
      </div>

      {/* Generate button */}
      <button
        id="sdxl-generate-btn"
        onClick={handleGenerate}
        disabled={loading || !prompt.trim()}
        className="flex items-center justify-center gap-2 w-full px-4 py-2.5 bg-violet-600 hover:bg-violet-500 disabled:opacity-40 disabled:cursor-not-allowed rounded-lg text-white text-xs font-extrabold uppercase tracking-wider transition-all duration-200"
      >
        {loading ? (
          <>
            <Loader2 className="h-3.5 w-3.5 animate-spin" />
            Generating with SDXL…
          </>
        ) : (
          <>
            <Sparkles className="h-3.5 w-3.5" />
            Generate Image
          </>
        )}
      </button>

      {/* Loading state */}
      {loading && (
        <div className="flex flex-col items-center gap-3 py-6 text-center">
          <div className="relative">
            <div className="w-14 h-14 rounded-full border-2 border-violet-500/20 border-t-violet-500 animate-spin" />
            <Sparkles className="h-5 w-5 text-violet-400 absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2" />
          </div>
          <p className="text-xs text-slate-400 font-semibold">
            Stable Diffusion XL is rendering your image…
          </p>
          <p className="text-[10px] text-slate-600">
            This may take up to 60 seconds on first run
          </p>
        </div>
      )}

      {/* Error state */}
      {error && !loading && (
        <div className="flex items-start gap-3 bg-red-950/30 border border-red-500/20 rounded-lg p-4">
          <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-bold text-red-400 mb-1">
              Generation Failed
            </p>
            <p className="text-[11px] text-slate-400 leading-relaxed">
              {error}
            </p>
            {error.includes("HUGGINGFACE_API_KEY") && (
              <p className="text-[10px] text-slate-500 mt-2">
                Add your key to{" "}
                <code className="text-violet-400">backend/.env</code>:{" "}
                <code className="text-violet-400">
                  HUGGINGFACE_API_KEY=hf_…
                </code>
              </p>
            )}
          </div>
          <button
            onClick={handleGenerate}
            className="shrink-0 p-1.5 text-slate-400 hover:text-white transition-colors"
            title="Retry"
          >
            <RefreshCw className="h-3.5 w-3.5" />
          </button>
        </div>
      )}

      {/* Generated image */}
      {imageUrl && !loading && (
        <div className="flex flex-col gap-3">
          <div className="relative rounded-xl overflow-hidden border border-slate-800 group">
            <img
              id="sdxl-generated-image"
              src={imageUrl}
              alt="SDXL generated first aid illustration"
              className="w-full object-cover rounded-xl transition-transform duration-500 group-hover:scale-105"
            />
            {/* Overlay actions */}
            <div className="absolute inset-0 bg-gradient-to-t from-slate-950/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex items-end justify-between p-4">
              <p className="text-[10px] text-slate-300 font-semibold truncate max-w-[75%]">
                {promptUsed}
              </p>
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-3 py-1.5 bg-white/10 hover:bg-white/20 backdrop-blur-sm border border-white/20 rounded-lg text-white text-[10px] font-bold uppercase tracking-wider transition-all"
              >
                <Download className="h-3 w-3" />
                Save
              </button>
            </div>
          </div>

          {/* Prompt used */}
          <div className="bg-slate-950/40 border border-slate-800/60 rounded-lg p-3">
            <p className="text-[9px] font-extrabold text-slate-500 uppercase tracking-wider mb-1">
              Full prompt sent to SDXL
            </p>
            <p className="text-[10px] text-slate-400 leading-relaxed italic">
              "{promptUsed}"
            </p>
          </div>

          {/* Re-generate button */}
          <button
            onClick={handleGenerate}
            className="flex items-center justify-center gap-2 w-full px-4 py-2 border border-slate-700 hover:border-violet-500/50 rounded-lg text-slate-400 hover:text-violet-400 text-xs font-bold uppercase tracking-wider transition-all duration-200"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Regenerate
          </button>
        </div>
      )}
    </div>
  );
};

export default SDXLImageCard;
