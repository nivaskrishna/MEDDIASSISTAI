import React, { useState } from "react";
import Navbar from "./components/Layout/Navbar";
import Footer from "./components/Layout/Footer";
import Home from "./pages/Home";
import Analyzer from "./pages/Analyzer";
import Hospitals from "./pages/Hospitals";
import KnowledgeBase from "./pages/KnowledgeBase";
import EmergencyPanel from "./components/Contacts/EmergencyPanel";

function App() {
  const [activeTab, setActiveTab] = useState("home");
  const [initialQuery, setInitialQuery] = useState("");
  const [initialImage, setInitialImage] = useState(null);
  const [initialImagePreview, setInitialImagePreview] = useState(null);

  const renderContent = () => {
    switch (activeTab) {
      case "home":
        return (
          <Home
            setActiveTab={setActiveTab}
            setInitialQuery={setInitialQuery}
            setInitialImage={setInitialImage}
            setInitialImagePreview={setInitialImagePreview}
          />
        );
      case "analyzer":
        return (
          <Analyzer
            setActiveTab={setActiveTab}
            initialQuery={initialQuery}
            setInitialQuery={setInitialQuery}
            initialImage={initialImage}
            setInitialImage={setInitialImage}
            initialImagePreview={initialImagePreview}
            setInitialImagePreview={setInitialImagePreview}
          />
        );
      case "hospitals":
        return <Hospitals />;
      case "drugs":
        return <KnowledgeBase defaultTab="medicines" />;
      case "kb":
        return <KnowledgeBase defaultTab="firstaid" />;
      case "contacts":
        return <EmergencyPanel />;
      default:
        return <Home setActiveTab={setActiveTab} />;
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-slate-950 text-slate-100">
      <Navbar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 md:px-6 py-6 md:py-10">
        {renderContent()}
      </main>
      <Footer />
    </div>
  );
}

export default App;
