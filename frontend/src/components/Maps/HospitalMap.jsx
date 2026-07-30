import React, { useState, useEffect } from "react";
import { searchHospitals, getMyLocation } from "../../services/api";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import { Search, MapPin, Navigation, Eye, Loader2 } from "lucide-react";
import "leaflet/dist/leaflet.css";

// Fix Leaflet default marker icon path issue in React/Webpack/Vite
import markerIcon2x from "leaflet/dist/images/marker-icon-2x.png";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";

delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: markerIcon2x,
  iconUrl: markerIcon,
  shadowUrl: markerShadow,
});

// A custom icon for hospitals
const hospitalIcon = new L.Icon({
  iconUrl: "https://cdn-icons-png.flaticon.com/512/809/809957.png", // red cross hospital icon
  iconRetinaUrl: "https://cdn-icons-png.flaticon.com/512/809/809957.png",
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -32],
  shadowUrl: markerShadow,
  shadowSize: [41, 41],
  shadowAnchor: [13, 41],
});

// Component to dynamically re-center map
const RecenterMap = ({ center, zoom }) => {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.setView(center, zoom);
    }
  }, [center, zoom, map]);
  return null;
};

const HospitalMap = () => {
  const [searchQuery, setSearchQuery] = useState(""); // Default empty
  const [radius, setRadius] = useState(10);
  const [loading, setLoading] = useState(false);
  const [geolocating, setGeolocating] = useState(false);
  const [liveLocationName, setLiveLocationName] = useState("");
  // Store actual live coordinates separately so we don't need to parse display string
  const [liveCoords, setLiveCoords] = useState(null); // { lat, lon }
  const [error, setError] = useState(null);
  const [mapCenter, setMapCenter] = useState([12.9716, 77.5946]); // Bangalore Default
  const [zoomLevel, setZoomLevel] = useState(12);
  const [hospitals, setHospitals] = useState([]);
  const [selectedHospital, setSelectedHospital] = useState(null);

  const doHospitalSearch = async (lat, lon, radiusVal) => {
    setLoading(true);
    setError(null);
    setSelectedHospital(null);
    try {
      const data = await searchHospitals(null, radiusVal, lat, lon);
      setMapCenter([data.center.lat, data.center.lon]);
      setHospitals(data.hospitals);
      setZoomLevel(radiusVal > 15 ? 11 : radiusVal > 8 ? 12 : 13);
      if (data.hospitals.length === 0) {
        setError(
          `No hospitals found within ${radiusVal} km. Try increasing the radius.`,
        );
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Failed to fetch hospitals. Please check your connection.",
      );
      console.error("Hospital search error:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (e) => {
    if (e) e.preventDefault();

    // If GPS location is active, re-use stored coordinates
    if (liveCoords && (!searchQuery.trim() || searchQuery === "GPS Location")) {
      await doHospitalSearch(liveCoords.lat, liveCoords.lon, radius);
      return;
    }

    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setSelectedHospital(null);

    try {
      const data = await searchHospitals(searchQuery, radius);
      setMapCenter([data.center.lat, data.center.lon]);
      setHospitals(data.hospitals);
      setZoomLevel(radius > 15 ? 11 : radius > 8 ? 12 : 13);
      if (data.hospitals.length === 0) {
        setError(
          `No hospitals found within ${radius} km of "${searchQuery}". Try a larger radius or different location.`,
        );
      }
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Location not found. Please verify the pincode or location name.",
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUseLiveLocation = () => {
    setGeolocating(true);
    setError(null);
    setSelectedHospital(null);

    const applyLocationAndSearch = async (lat, lon, source) => {
      console.log(`Location obtained via ${source}: ${lat}, ${lon}`);
      const coords = { lat, lon };
      setLiveCoords(coords);
      setMapCenter([lat, lon]);
      setLiveLocationName(`${lat.toFixed(4)},${lon.toFixed(4)}`);
      setGeolocating(false);
      // Now search hospitals using the actual coordinates
      await doHospitalSearch(lat, lon, radius);
    };

    const fallbackToIP = async () => {
      console.log("Trying server-side geolocation...");
      try {
        // This calls our backend which does IP lookup server-side (no CORS issues)
        const loc = await getMyLocation();
        console.log("Server geolocation result:", loc);
        if (loc && loc.lat && loc.lon) {
          await applyLocationAndSearch(loc.lat, loc.lon, loc.source || "IP");
        } else {
          throw new Error("Invalid geolocation response");
        }
      } catch (err) {
        console.error("Server-side geolocation failed:", err);
        setGeolocating(false);
        setLoading(false);
        setError(
          "Could not detect your location automatically. Please type your village name or pincode in the search box above.",
        );
      }
    };

    if (!navigator.geolocation) {
      console.warn("Browser geolocation not supported, using IP fallback");
      fallbackToIP();
      return;
    }

    // Try GPS with a reasonable timeout
    navigator.geolocation.getCurrentPosition(
      async (position) => {
        const lat = position.coords.latitude;
        const lon = position.coords.longitude;
        await applyLocationAndSearch(lat, lon, "GPS");
      },
      (gpsErr) => {
        console.warn(
          `GPS failed (code ${gpsErr.code}): ${gpsErr.message} — trying IP fallback`,
        );
        fallbackToIP();
      },
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    );
  };

  // Run once on load to detect location automatically
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => {
    handleUseLiveLocation();
  }, []);

  const handleShowOnMap = (hospital) => {
    setSelectedHospital(hospital);
    setMapCenter([hospital.latitude, hospital.longitude]);
    setZoomLevel(15);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 w-full max-w-6xl mx-auto lg:h-[600px] h-auto items-stretch animate-fadeIn">
      {/* Search and List Panel */}
      <div className="w-full lg:w-96 flex flex-col gap-4 shrink-0 overflow-hidden">
        {/* Search controls */}
        <div className="glass-card p-5 rounded-2xl">
          <h2 className="text-lg font-bold text-slate-100 mb-4 flex items-center gap-2">
            <Search className="h-5 w-5 text-blue-500" />
            Hospital Search
          </h2>
          <form onSubmit={handleSearch} className="flex flex-col gap-3">
            <div>
              <label className="block text-xs text-slate-400 font-semibold mb-1 uppercase tracking-wider">
                Pincode or Location
              </label>
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => {
                  setSearchQuery(e.target.value);
                  if (liveCoords) {
                    setLiveCoords(null);
                    setLiveLocationName("");
                  }
                }}
                placeholder="e.g. 515001 or Anantapur"
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors placeholder:text-slate-500"
              />
            </div>
            <div>
              <label className="block text-xs text-slate-400 font-semibold mb-1 uppercase tracking-wider">
                Radius (KM)
              </label>
              <select
                value={radius}
                onChange={(e) => setRadius(Number(e.target.value))}
                className="w-full bg-slate-900 border border-slate-800 rounded-xl px-3.5 py-2.5 text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              >
                <option value={2}>2 KM</option>
                <option value={5}>5 KM</option>
                <option value={10}>10 KM</option>
                <option value={15}>15 KM</option>
                <option value={25}>25 KM</option>
                <option value={30}>30 KM</option>
              </select>
            </div>

            <div className="flex flex-col gap-2 pt-1 border-t border-slate-800/80">
              <div className="flex items-center justify-between">
                <label className="block text-xs text-slate-400 font-semibold uppercase tracking-wider">
                  Or Use Current Location
                </label>
                {liveLocationName && (
                  <span className="text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-bold">
                    GPS Active
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={handleUseLiveLocation}
                disabled={loading || geolocating}
                className="w-full border border-dashed border-slate-800 hover:border-blue-500/50 bg-slate-900/40 hover:bg-blue-600/5 text-slate-300 hover:text-white font-bold py-3 px-3.5 rounded-xl text-xs flex items-center justify-center gap-2 transition-all duration-300 cursor-pointer shadow-sm focus:outline-none"
              >
                {geolocating ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin text-blue-500" />{" "}
                    Detecting location...
                  </>
                ) : (
                  <>
                    <Navigation className="h-4 w-4 text-emerald-400" />
                    {liveLocationName
                      ? `GPS: ${liveLocationName}`
                      : "Detect & Search Live Location"}
                  </>
                )}
              </button>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-2.5 rounded-xl text-sm flex items-center justify-center gap-2 transition-colors disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" /> Searching...
                </>
              ) : (
                "Find Nearby Hospitals"
              )}
            </button>
          </form>

          {error && (
            <p className="text-xs text-rose-400 border border-rose-500/25 bg-rose-500/5 px-3 py-2 rounded-lg mt-3">
              {error}
            </p>
          )}
        </div>

        {/* Results List */}
        <div className="glass-card p-5 rounded-2xl h-[300px] lg:h-auto lg:flex-1 flex flex-col min-h-0">
          <div className="flex justify-between items-center border-b border-slate-800 pb-3 mb-3 shrink-0">
            <h3 className="text-sm font-bold text-slate-100">
              Results ({hospitals.length})
            </h3>
            <span className="text-xxs font-bold text-slate-400 bg-slate-900 border border-slate-800 px-2 py-0.5 rounded-full">
              Sorted by Distance
            </span>
          </div>

          <div className="flex-1 overflow-y-auto flex flex-col gap-2.5 pr-1">
            {hospitals.length === 0 ? (
              <div className="flex-1 flex flex-col items-center justify-center text-slate-500 py-10">
                <MapPin className="h-6 w-6 mb-2 opacity-40 animate-pulse" />
                <p className="text-xs">No hospitals found within {radius}km.</p>
              </div>
            ) : (
              hospitals.map((hospital, idx) => (
                <div
                  key={idx}
                  onClick={() => handleShowOnMap(hospital)}
                  className={`p-3.5 rounded-xl border transition-all duration-300 cursor-pointer flex flex-col gap-1.5 ${
                    selectedHospital?.name === hospital.name
                      ? "bg-blue-600/10 border-blue-500 shadow-md shadow-blue-500/5"
                      : "bg-slate-900/40 border-slate-800/80 hover:border-slate-700"
                  }`}
                >
                  <div className="flex items-start justify-between gap-2">
                    <h4 className="text-sm font-semibold text-slate-200 line-clamp-1">
                      {hospital.name}
                    </h4>
                    <span className="text-xxs font-bold text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full shrink-0">
                      {hospital.distance_km} KM
                    </span>
                  </div>
                  <p className="text-xxs text-slate-400 line-clamp-1">
                    {hospital.address}
                  </p>
                  <div className="flex justify-end mt-1">
                    <button className="text-xxs font-semibold text-blue-400 hover:text-blue-300 flex items-center gap-1.5 transition-colors">
                      <Eye className="h-3 w-3" /> Show on Map
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Map display */}
      <div className="flex-1 h-[350px] lg:h-auto lg:flex-1 rounded-2xl overflow-hidden border border-slate-800/60 relative">
        <MapContainer
          center={mapCenter}
          zoom={zoomLevel}
          className="w-full h-full z-10"
        >
          <TileLayer
            attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
          />
          <RecenterMap center={mapCenter} zoom={zoomLevel} />

          {/* User coordinates center marker */}
          <Marker position={mapCenter}>
            <Popup>
              <div className="text-center font-bold text-xs p-1 text-slate-200">
                Search Center
              </div>
            </Popup>
          </Marker>

          {/* Hospital markers */}
          {hospitals.map((hospital, idx) => (
            <Marker
              key={idx}
              position={[hospital.latitude, hospital.longitude]}
              icon={hospitalIcon}
            >
              <Popup>
                <div className="p-1 flex flex-col gap-1 text-slate-200">
                  <h4 className="text-xs font-bold text-blue-400">
                    {hospital.name}
                  </h4>
                  <p className="text-xxs text-slate-300">{hospital.address}</p>
                  <span className="text-xxs font-bold text-emerald-400">
                    Distance: {hospital.distance_km} KM
                  </span>
                  <a
                    href={`https://www.google.com/maps/dir/?api=1&destination=${hospital.latitude},${hospital.longitude}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xxs font-bold bg-blue-600 hover:bg-blue-500 text-white py-1 px-2 rounded mt-1 text-center flex items-center justify-center gap-1 transition-colors"
                  >
                    <Navigation className="h-3 w-3" /> Directions
                  </a>
                </div>
              </Popup>
            </Marker>
          ))}
        </MapContainer>
      </div>
    </div>
  );
};

export default HospitalMap;
